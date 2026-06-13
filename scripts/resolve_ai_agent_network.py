#!/usr/bin/env python3
"""S295a — resolve the network (IP/ASN/geo) of the AI-agent subset via a curated map.

Standalone, isolated: writes the agent_network finding DIRECTLY (like the S293a
reference-load), touches NO shared code (engine/scanner/seed/front). Same module +
category as the S294 network_resolve scraper → AgentHeader's Network·Place section
renders these with zero change.

Why a curated map (not the corpus operator_url): the crawler-UA `url` is a docs page,
often THIRD-PARTY (Bytespider→stackoverflow, Claude-User→useragents.io,
Meta-ExternalHit→datadome). Resolving that gives the docs-site ASN, not the operator's
→ false attribution. For the ~26 AI agents, a hand-verified operator→canonical-domain
map is the honest, exact path. Findings carry operator_source='curated'.

Run: python scripts/resolve_ai_agent_network.py [--dry-run] [--refresh]
"""
import argparse
import json as _json
import logging
import time
import urllib.request

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.workspace import Workspace
from api.models.target import Target
from api.models.finding import Finding
from api.models.scan import Scan

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("ai_agent_network")

# keyword found in the bot pattern -> canonical operator domain (hand-verified)
_AI_OPERATORS = {
    "gptbot": "openai.com", "chatgpt": "openai.com", "oai-search": "openai.com",
    "claudebot": "anthropic.com", "claude-web": "anthropic.com", "anthropic": "anthropic.com",
    "claude-user": "anthropic.com", "claude-searchbot": "anthropic.com",
    "perplexity": "perplexity.ai",
    "bytespider": "bytedance.com",
    "ccbot": "commoncrawl.org",
    "google-extended": "google.com", "googleother": "google.com",
    "applebot": "apple.com",
    "amazonbot": "amazon.com",
    "cohere": "cohere.com",
    "diffbot": "diffbot.com",
    "youbot": "you.com",
    "meta-external": "meta.com",
    "bingbot": "bing.com",
    "duckassist": "duckduckgo.com",
}
_IPAPI = "http://ip-api.com/json/{dom}?fields=status,country,city,isp,org,as,asname,query,reverse,hosting"


def _operator_for(pattern: str):
    p = (pattern or "").lower()
    for kw, dom in _AI_OPERATORS.items():
        if kw in p:
            return dom
    return None


def main(refresh=False, dry_run=False):
    s = get_sync_session()
    try:
        ws = s.execute(select(Workspace).where(Workspace.kind == "agent")).scalars().first()
        assert ws and ws.kind == "agent", "agent workspace missing"

        targets = s.execute(select(Target).where(Target.workspace_id == ws.id)).scalars().all()
        todo = []
        for t in targets:
            pat = (t.profile_data or {}).get("pattern") or t.email.removeprefix("ua:")
            dom = _operator_for(pat)
            if dom:
                todo.append((t, dom))
        log.info("AI-subset matched: %d", len(todo))

        written = skipped = failed = 0
        for i, (t, dom) in enumerate(todo):
            existing = s.execute(select(Finding).where(
                Finding.target_id == t.id, Finding.category == "agent_network")).scalars().first()
            if existing and not refresh:
                skipped += 1
                continue
            try:
                with urllib.request.urlopen(_IPAPI.format(dom=dom), timeout=8) as r:
                    d = _json.loads(r.read())
            except Exception as e:
                log.warning("  resolve failed %s: %s", dom, e)
                failed += 1
                time.sleep(1.5)
                continue
            if d.get("status") != "success":
                failed += 1
                time.sleep(1.5)
                continue
            if dry_run:
                log.info("  %-32s -> %-18s | %s", t.email, dom, d.get("as"))
                time.sleep(1.5)
                continue

            if existing:
                # FK: identities may reference the finding — clear them first
                from api.models.identity import Identity
                for idn in s.execute(select(Identity).where(Identity.source_finding == existing.id)).scalars().all():
                    s.delete(idn)
                s.flush()
                s.delete(existing)
                s.flush()
            sc = Scan(workspace_id=ws.id, target_id=t.id,
                      scan_type="reference_load", status="completed", modules=[])
            s.add(sc)
            s.flush()
            s.add(Finding(
                workspace_id=ws.id, scan_id=sc.id, target_id=t.id,
                module="network_resolve", layer=4, category="agent_network", severity="info",
                title=f"Network: {dom}",
                indicator_value=str(d.get("query"))[:500], indicator_type="ip",
                data={"extracted": {
                    "ip": d.get("query"), "asn": d.get("as"), "asname": d.get("asname"),
                    "org": d.get("org"), "isp": d.get("isp"),
                    "country": d.get("country"), "city": d.get("city"),
                    "reverse": d.get("reverse"), "hosting": d.get("hosting"),
                    "operator": dom, "operator_source": "curated"}},
            ))
            s.commit()
            written += 1
            log.info("  [%d/%d] %-30s -> %s (%s)", i + 1, len(todo), t.email, d.get("as"), dom)
            time.sleep(1.5)   # ip-api 45/min — ~26 * 1.5s ≈ 40s, safe

        log.info("")
        log.info("DONE  written=%d skipped=%d failed=%d  (dry_run=%s, refresh=%s)",
                 written, skipped, failed, dry_run, refresh)
        log.info("ASSERT scoped to kind='agent' ws=%s: OK", ws.id)
    finally:
        s.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="rewrite existing agent_network findings")
    ap.add_argument("--dry-run", action="store_true", help="print mapping, write nothing")
    a = ap.parse_args()
    main(refresh=a.refresh, dry_run=a.dry_run)
