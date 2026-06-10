"""S257 — Reclean historic legal_record findings produced by the pre-S256
matcher (bodacc_search + uk_gazette_search).

Two tracks because the scrapers stored asymmetric data:

  Track A — uk_gazette_search: surgical / offline.
    Recompute name_match_confidence against the row's stored `title` +
    `description` columns (Gazette matched on those fields). Score 0.0
    -> purge. Score >= 0.82 -> keep. Both columns blank -> keep
    (cannot evaluate; never delete blind).

  Track B — bodacc_search: re-fetch live.
    Bodacc matched on 9 fields but only stored `data.commercant`; a true
    officer match (matched via `personnes`) only has the *company name*
    in `commercant`, so recomputing against stored data would
    false-delete real records. Instead, call search_bodacc(primary_name)
    directly with the S256-fixed matcher, purge the target's old bodacc
    legal_records, re-insert the fresh hits. SCOPED to legal_record
    only -- never re-runs the full enrich_public_exposure() because the
    PASS2 persister still lacks cross-scan dedup (S256 Defect 2 backlog)
    and would double every media/sanctions/corporate row.

Two-step atomic delete (identities.source_finding has no ON DELETE
CASCADE -> identity rows first, then findings, in one transaction).

Dry-run by default. Mutations only with --commit (and only if there's
anything to change). Idempotent: a second pass should produce zero deltas.

Usage:
  docker compose exec api python scripts/reclean_legal_records.py
  docker compose exec api python scripts/reclean_legal_records.py --target guillaume.a.perrin@gmail.com
  docker compose exec api python scripts/reclean_legal_records.py --module bodacc_search --commit
"""
import argparse
import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from api.scrapers._name_match import name_match_confidence
from api.scrapers.bodacc_search import search_bodacc
from api.models.finding import Finding
from api.models.scan import Scan
from api.models.target import Target
from api.services.layer4.public_exposure_enricher import _sanitize_for_json
from api.tasks.utils import get_sync_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reclean_legal_records")

GAZETTE = "uk_gazette_search"
BODACC = "bodacc_search"


def _candidate_names(target: Target) -> list[str]:
    """Build the name set we evaluate against. The scraper used
    `primary_name` from profile_data at scan time, so that's the
    primary signal. We also accept the operator-asserted name (if set)
    so we don't false-delete records the operator confirmed."""
    out = []
    profile = target.profile_data or {}
    if profile.get("primary_name"):
        out.append(str(profile["primary_name"]).strip())
    op = " ".join(
        x for x in (target.user_first_name, target.user_last_name) if x
    ).strip()
    if op:
        out.append(op)
    # Dedupe while preserving order
    seen, dedup = set(), []
    for n in out:
        k = n.lower()
        if n and k not in seen:
            dedup.append(n)
            seen.add(k)
    return dedup


def _two_step_delete(session, finding_ids: list[uuid.UUID]) -> int:
    """identities.source_finding has no ON DELETE CASCADE.
    Delete identity rows referencing these findings first (identity_edges
    cascade via identities.id), then the findings themselves. One
    transaction per call site."""
    if not finding_ids:
        return 0
    session.execute(
        text("DELETE FROM identities WHERE source_finding = ANY(:ids)"),
        {"ids": finding_ids},
    )
    res = session.execute(
        text("DELETE FROM findings WHERE id = ANY(:ids)"),
        {"ids": finding_ids},
    )
    return res.rowcount or 0


# ─── Track A — UK Gazette ────────────────────────────────────────────────


def classify_gazette(rows: list[Finding], name_by_target: dict[uuid.UUID, list[str]]):
    """Return (purge_ids, keep_count, unclassifiable_kept).
    Unclassifiable = both title and description blank → kept (we never
    delete blind)."""
    purge_ids = []
    keep = 0
    unclassifiable = 0
    for f in rows:
        names = name_by_target.get(f.target_id) or []
        title = (f.title or "").strip()
        desc = (f.description or "").strip()
        if not title and not desc:
            unclassifiable += 1
            keep += 1
            continue
        best = 0.0
        for nm in names:
            score = name_match_confidence([title, desc], nm)
            if score > best:
                best = score
        if best == 0.0:
            purge_ids.append(f.id)
        else:
            keep += 1
    return purge_ids, keep, unclassifiable


# ─── Track B — BODACC live refetch ───────────────────────────────────────


def refetch_bodacc_for_target(
    session, target: Target, old_rows: list[Finding], dry_run: bool
) -> dict:
    """Per-target: call search_bodacc with the S256-fixed matcher, purge
    old bodacc legal_records, re-insert fresh hits. Returns counts."""
    names = _candidate_names(target)
    fresh_rows: list[dict] = []
    if names:
        # search_bodacc takes a single name string; use the primary_name
        # (first candidate). The S256 matcher is what enforces correctness.
        try:
            fresh_rows = search_bodacc(names[0]) or []
        except Exception:
            logger.exception("search_bodacc failed for target=%s name=%r", target.id, names[0])
            fresh_rows = []
    # Idempotency: compare the fresh result set against what's already
    # stored. If they coincide (same indicator_value + url tuples), this
    # target is already clean — skip both the purge and the re-insert.
    def _key(iv, url):
        return ((iv or "").strip().lower(), (url or "").strip().lower())

    fresh_keys = {
        _key(
            fd.get("indicator_value")
            or (fd.get("data") or {}).get("commercant")
            or fd.get("url")
            or fd.get("title"),
            fd.get("url"),
        )
        for fd in fresh_rows
    }
    old_keys = {_key(r.indicator_value, r.url) for r in old_rows}
    no_change = fresh_keys == old_keys and len(old_keys) == len(old_rows)

    counts = {
        "target_id": target.id,
        "email": target.email,
        "old": len(old_rows),
        "fresh": len(fresh_rows),
        "no_change": no_change,
    }
    if dry_run or no_change:
        if dry_run and no_change:
            counts["note"] = "idempotent skip"
        return counts

    # Purge old (two-step)
    if old_rows:
        _two_step_delete(session, [r.id for r in old_rows])

    # Re-insert fresh — scoped strictly to legal_record (the only kind
    # this script touches). Mirrors enricher L741-757 Finding construction.
    # findings.scan_id is NOT NULL; reuse the target's most recent scan
    # (the same scan whose enrichment we're correcting). If the target
    # somehow has no scans, skip insert + report — purge still wins.
    latest_scan_id = session.execute(
        select(Scan.id)
        .where(Scan.target_id == target.id)
        .order_by(Scan.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if not latest_scan_id and fresh_rows:
        counts["skipped_no_scan"] = True
        return counts
    inserted = 0
    for fd in fresh_rows:
        try:
            scraper_name = (fd.get("data") or {}).get("scraper", "bodacc_search")
            ind_type = "legal_record"
            category = "formal_records"  # S145 dedicated category
            finding = Finding(
                workspace_id=target.workspace_id,
                scan_id=latest_scan_id,
                target_id=target.id,
                module=scraper_name[:50],
                layer=4,
                category=category,
                severity=fd.get("severity", "info"),
                title=fd.get("title", f"BODACC: {names[0] if names else ''}")[:255],
                description=(fd.get("description") or "")[:1000] or None,
                data=_sanitize_for_json(fd.get("data", {})),
                url=fd.get("url"),
                indicator_value=str(
                    fd.get("indicator_value") or fd.get("url") or fd.get("title", "")
                )[:500],
                indicator_type=ind_type,
                verified=False,
                confidence=round(fd.get("confidence", 0.60), 3),
            )
            session.add(finding)
            inserted += 1
        except Exception:
            logger.exception(
                "Failed to construct backfill finding for target=%s", target.id
            )
    counts["inserted"] = inserted
    return counts


# ─── Driver ──────────────────────────────────────────────────────────────


def _resolve_target_filter(session, target_arg: str | None):
    """Return a sqlalchemy clause restricting to a single target, or None."""
    if not target_arg:
        return None
    try:
        uid = uuid.UUID(target_arg)
        return Finding.target_id == uid
    except ValueError:
        # treat as email
        t = session.execute(
            select(Target).where(Target.email == target_arg)
        ).scalar_one_or_none()
        if not t:
            logger.error("No target with email=%r", target_arg)
            sys.exit(2)
        return Finding.target_id == t.id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="UUID or email; restrict to one target")
    parser.add_argument(
        "--module",
        choices=[GAZETTE, BODACC],
        help="restrict to one scraper (default: both tracks)",
    )
    parser.add_argument(
        "--commit", action="store_true",
        help="apply changes (default: dry-run only)"
    )
    args = parser.parse_args()
    dry = not args.commit

    session = get_sync_session()
    try:
        target_clause = _resolve_target_filter(session, args.target)

        # Pre-load all affected legal_record rows + targets.
        q = (
            select(Finding)
            .where(Finding.indicator_type == "legal_record")
            .where(Finding.module.in_([GAZETTE, BODACC]))
        )
        if target_clause is not None:
            q = q.where(target_clause)
        if args.module:
            q = q.where(Finding.module == args.module)
        all_rows = session.execute(q).scalars().all()

        # Pre-load Target rows once for candidate-name resolution.
        target_ids = {r.target_id for r in all_rows}
        targets = {
            t.id: t
            for t in session.execute(
                select(Target).where(Target.id.in_(target_ids))
            ).scalars().all()
        }
        name_by_target = {tid: _candidate_names(t) for tid, t in targets.items()}

        gazette_rows = [r for r in all_rows if r.module == GAZETTE]
        bodacc_rows = [r for r in all_rows if r.module == BODACC]

        # ─── Track A ─────────────────────────────────────────────────
        gazette_summary = {"total": len(gazette_rows), "purge": 0, "keep": 0, "blind_kept": 0}
        gazette_purge_ids = []
        if not args.module or args.module == GAZETTE:
            purge_ids, keep, unclassifiable = classify_gazette(
                gazette_rows, name_by_target
            )
            gazette_purge_ids = purge_ids
            gazette_summary.update(
                purge=len(purge_ids), keep=keep, blind_kept=unclassifiable
            )

        # ─── Track B ─────────────────────────────────────────────────
        bodacc_by_target: dict[uuid.UUID, list[Finding]] = {}
        for r in bodacc_rows:
            bodacc_by_target.setdefault(r.target_id, []).append(r)

        bodacc_summary = {
            "targets": 0,
            "old": 0,
            "fresh": 0,
            "inserted": 0,
            "details": [],
        }
        if (not args.module or args.module == BODACC) and bodacc_by_target:
            bodacc_summary["targets"] = len(bodacc_by_target)
            bodacc_summary["unchanged"] = 0
            for tid, old_rows in bodacc_by_target.items():
                t = targets.get(tid)
                if not t:
                    continue
                counts = refetch_bodacc_for_target(session, t, old_rows, dry_run=dry)
                # Idempotent skip: don't count this target's rows as
                # "to purge/insert" — they're already correct.
                if counts.get("no_change"):
                    bodacc_summary["unchanged"] += 1
                    continue
                bodacc_summary["old"] += counts["old"]
                bodacc_summary["fresh"] += counts["fresh"]
                bodacc_summary["inserted"] += counts.get("inserted", 0)
                bodacc_summary["details"].append(counts)

        # ─── Reporting + differential gate ───────────────────────────
        gz_change = gazette_summary["purge"]
        bd_change = bodacc_summary["old"] + bodacc_summary["fresh"]
        total_change = gz_change + bd_change

        print()
        print(f"== {'DRY RUN' if dry else 'APPLYING'} ==")
        print(
            f"Gazette: {gazette_summary['total']} legal_records -> "
            f"{gazette_summary['purge']} purge / {gazette_summary['keep']} keep "
            f"/ {gazette_summary['blind_kept']} unclassifiable(kept)"
        )
        print(
            f"BODACC : {bodacc_summary['targets']} targets ({bodacc_summary.get('unchanged', 0)} already clean) -> "
            f"{bodacc_summary['old']} purge, {bodacc_summary['fresh']} fresh re-inserts"
        )
        for c in sorted(bodacc_summary["details"], key=lambda d: -d["old"])[:20]:
            print(
                f"  {c['email']}: {c['old']} old -> {c['fresh']} fresh "
                f"(purge {c['old']}, insert {c['fresh']})"
            )

        if dry:
            print()
            print("Re-run with --commit to apply.")
            return

        if total_change == 0:
            print()
            print("Nothing to change. Aborting commit.")
            return

        # Track A — apply gazette purge in one txn
        if gazette_purge_ids:
            _two_step_delete(session, gazette_purge_ids)
        # Track B inserts already added via session.add inside the loop
        session.commit()
        print()
        print("Committed.")
    except Exception:
        session.rollback()
        logger.exception("aborted")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
