#!/usr/bin/env python3
"""S291 — agent discovery bootstrap (one-to-many). Creates the agent corpus.

This is the A1 of the agent layer: it does NOT enrich (that's the agent scrapers,
which run per-target via the dynamic engine). It fetches/curates two sources and
creates agent TARGETS that the scrapers then enrich:

  - WBA (Web Bot Auth): operators that publish a signed key directory at
    /.well-known/http-message-signatures-directory → 1 target/operator
    (email = operator host, profile_data={operator, source:'wba'}). The
    wba_directory scraper fetches each operator's directory.
  - JA4: a curated slice of well-known TLS runtime signatures → 1 target/signature
    (email = 'ja4:<hash>', profile_data={ja4, source:'ja4db'}). The ja4_lookup
    scraper resolves each to its software (when ja4db is reachable).

Discipline (mirrors the S290 harvest contract):
  - Idempotent: SELECT-before-INSERT on target.email. Re-run → skipped>0, stable.
  - Scoped: ALL writes assert workspace.kind=='agent' first. Never touches human orgs.
  - --reset: DELETE scoped to THIS agent workspace only, gated on count>0.
  - Resilient: each source in try/except → skip+log, never crash (S286 pattern).
  - --no-scan: skip enqueuing scans (default: enqueue modules=['scraper_engine']
    per new target so the agent scrapers run — and ONLY them, not the 26 humans).

Run: python scripts/discover_agents_wba.py [--reset] [--no-scan]
"""
import argparse
import logging
import sys
import uuid

import requests
from sqlalchemy import func, select

from api.tasks.utils import get_sync_session
from api.models.workspace import Workspace
from api.models.user import UserWorkspace
from api.models.target import Target
from api.models.scan import Scan
from api.models.finding import Finding

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("agent_discovery")

AGENT_WS_SLUG = "agent-corpus"
AGENT_WS_NAME = "Agent Corpus"

# WBA operators — the 3 directories confirmed live (200 + signed keys) as of 2026-06.
# The ecosystem is young; this set grows as WBA adoption does. Dead hosts removed
# (they only created empty 0-finding targets).
_WBA_SEED = [
    "agent.bot.goog",                                          # Google — 4 keys
    "http-message-signatures-example.research.cloudflare.com", # Cloudflare — purpose=rag
    "chatgpt.com",                                             # OpenAI — purpose=ai
]
# Optional live registry (best-effort merge; failure → seed stands).
_WBA_REGISTRY_URL = (
    "https://raw.githubusercontent.com/cloudflareresearch/web-bot-auth/main/registry.json"
)

# crawler-user-agents — 1498 known bots loaded as REFERENCE data (agent_known).
# Unlike WBA (discovered live via the signed directory), this is a known list: the
# discovery writes one finding per entry directly — nothing to scrape per-target.
_CRAWLER_UA_URL = (
    "https://raw.githubusercontent.com/monperrus/crawler-user-agents/master/crawler-user-agents.json"
)


def _get_or_create_agent_ws(s):
    ws = s.execute(select(Workspace).where(Workspace.slug == AGENT_WS_SLUG)).scalar_one_or_none()
    if ws is None:
        # owner = the user that owns the most workspaces (the operator), for visibility
        owner_id = s.execute(
            select(Workspace.owner_id).where(Workspace.owner_id.isnot(None))
            .group_by(Workspace.owner_id).order_by(func.count().desc()).limit(1)
        ).scalar_one_or_none()
        ws = Workspace(name=AGENT_WS_NAME, slug=AGENT_WS_SLUG, owner_id=owner_id, kind="agent")
        s.add(ws)
        s.flush()
        if owner_id:
            s.add(UserWorkspace(user_id=owner_id, workspace_id=ws.id, role="superadmin"))
        s.commit()
        log.info("created agent workspace %s (kind=agent)", ws.id)
    # HARD ASSERT before any further write — never touch a human org.
    assert ws.kind == "agent", f"FATAL: workspace {ws.id} kind={ws.kind!r} != 'agent'"
    return ws


def _wba_operators():
    ops = list(_WBA_SEED)
    try:
        r = requests.get(_WBA_REGISTRY_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            entries = data if isinstance(data, list) else data.get("operators", [])
            for e in entries:
                host = (e.get("directory") or e.get("host") or "").replace("https://", "").split("/")[0] \
                    if isinstance(e, dict) else str(e)
                if host and host not in ops:
                    ops.append(host)
    except Exception as e:
        log.info("  wba registry fetch skipped (%s) — using seed", e)
    return ops


def _upsert_target(s, ws, email, profile_data):
    """SELECT-before-INSERT on email (idempotent). Returns (target, created)."""
    t = s.execute(
        select(Target).where(Target.workspace_id == ws.id, Target.email == email)
    ).scalar_one_or_none()
    if t:
        return t, False
    t = Target(workspace_id=ws.id, email=email, status="harvested", profile_data=profile_data)
    s.add(t)
    s.flush()
    return t, True


def _enqueue_scan(s, ws, target):
    from api.tasks.scan_orchestrator import launch_scan
    scan = Scan(workspace_id=ws.id, target_id=target.id,
                modules=["scraper_engine"], module_progress={"scraper_engine": "queued"})
    s.add(scan)
    s.commit()
    task = launch_scan.delay(str(scan.id))
    scan.celery_task_id = task.id
    s.commit()


def _ref_scan(s, ws, target_id):
    """One completed reference-load scan per crawler-UA target (findings need a
    scan_id). Nothing is dispatched — the data is loaded, not scraped."""
    sc = Scan(workspace_id=ws.id, target_id=target_id,
              scan_type="reference_load", status="completed", modules=[])
    s.add(sc)
    s.flush()
    return sc.id


def _write_ua_finding(s, ws, target, scan_id, entry):
    f = Finding(
        workspace_id=ws.id, scan_id=scan_id, target_id=target.id,
        module="crawler_ua_corpus", layer=1,
        category="agent_known", severity="info",
        title=(entry.get("description") or f"Known agent: {entry['pattern']}")[:255],
        indicator_value=entry["pattern"][:500], indicator_type="ua_pattern",
        data={"pattern": entry["pattern"], "url": entry.get("url"),
              "instances": entry.get("instances", []),
              "description": entry.get("description"),
              "tags": entry.get("tags", []), "source": "crawler-ua"},
    )
    s.add(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete this agent workspace's targets first")
    ap.add_argument("--no-scan", action="store_true", help="do not enqueue scans (WBA only)")
    ap.add_argument("--no-crawler-ua", action="store_true", help="skip the 1498-bot reference corpus")
    args = ap.parse_args()

    s = get_sync_session()
    try:
        ws = _get_or_create_agent_ws(s)

        if args.reset:
            n = s.execute(
                select(func.count()).select_from(Target).where(Target.workspace_id == ws.id)
            ).scalar() or 0
            if n > 0:                                  # differential gate — no-op on empty
                s.execute(Target.__table__.delete().where(Target.workspace_id == ws.id))
                s.commit()
                log.info("--reset: deleted %d agent targets (scoped to ws %s)", n, ws.id)
            else:
                log.info("--reset: no agent targets to delete (no-op)")

        counts = {"wba_ops": 0, "wba_new": 0, "wba_skip": 0,
                  "ua_total": 0, "ua_new": 0, "ua_skip": 0,
                  "scans": 0, "source_fail": 0}
        new_targets = []   # WBA only — these get a live scraper scan

        # --- source 1: WBA ---
        try:
            ops = _wba_operators()
            counts["wba_ops"] = len(ops)
            for host in ops:
                t, created = _upsert_target(s, ws, host, {"operator": host, "source": "wba"})
                if created:
                    counts["wba_new"] += 1
                    new_targets.append(t.id)
                else:
                    counts["wba_skip"] += 1
            s.commit()
        except Exception as e:
            counts["source_fail"] += 1
            log.warning("  wba source failed: %s", e)
            s.rollback()

        # --- source 2: crawler-UA known-bot reference corpus (reference-load) ---
        if not args.no_crawler_ua:
            try:
                import urllib.request
                import json as _json
                with urllib.request.urlopen(_CRAWLER_UA_URL, timeout=30) as r:
                    corpus = _json.loads(r.read())
                counts["ua_total"] = len(corpus)
                # preload existing emails ONCE — idempotence at 1.5k scale
                existing = {e for (e,) in s.execute(
                    select(Target.email).where(Target.workspace_id == ws.id)
                ).all()}
                for i, entry in enumerate(corpus):
                    pat = entry.get("pattern")
                    if not pat:
                        continue
                    email = f"ua:{pat}"[:255]
                    if email in existing:
                        counts["ua_skip"] += 1
                        continue
                    t = Target(workspace_id=ws.id, email=email, status="harvested",
                               profile_data={"pattern": pat, "operator_url": entry.get("url"),
                                             "tags": entry.get("tags", []), "source": "crawler-ua"})
                    s.add(t)
                    s.flush()
                    _write_ua_finding(s, ws, t, _ref_scan(s, ws, t.id), entry)
                    existing.add(email)
                    counts["ua_new"] += 1
                    if (i + 1) % 200 == 0:
                        s.commit()
                        log.info("  crawler-UA %d/%d", i + 1, len(corpus))
                s.commit()
            except Exception as e:
                counts["source_fail"] += 1
                log.warning("  crawler-UA source failed (seed stands): %s", e)
                s.rollback()

        # --- enqueue scraper scans for WBA targets ONLY (crawler-UA = reference,
        #     already has its finding + reference_load scan; nothing to scrape) ---
        if not args.no_scan and new_targets:
            for tid in new_targets:
                try:
                    t = s.execute(select(Target).where(Target.id == tid)).scalar_one()
                    _enqueue_scan(s, ws, t)
                    counts["scans"] += 1
                except Exception as e:
                    log.warning("  scan enqueue failed for %s: %s", tid, e)

        log.info("")
        log.info("DISCOVERY workspace=%s kind=%s", ws.id, ws.kind)
        log.info("  wba:        operators=%d targets_new=%d skipped=%d",
                 counts["wba_ops"], counts["wba_new"], counts["wba_skip"])
        log.info("  crawler-ua: total=%d targets_new=%d skipped=%d",
                 counts["ua_total"], counts["ua_new"], counts["ua_skip"])
        log.info("  scans_enqueued=%d (WBA only)  source_fail=%d", counts["scans"], counts["source_fail"])
        log.info("ASSERT all writes scoped to kind='agent': OK")
    finally:
        s.close()


if __name__ == "__main__":
    main()
