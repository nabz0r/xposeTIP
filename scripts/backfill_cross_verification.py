#!/usr/bin/env python3
"""
S168 — Backfill cross_verification_count + cross_verification_sources on findings.

Iterates all targets (optionally filtered by --workspace or --target), groups
findings by indicator_value within each target, computes peers per finding,
and updates the new columns. Idempotent — re-running produces the same DB state.

Usage:
    docker compose exec api python scripts/backfill_cross_verification.py
    docker compose exec api python scripts/backfill_cross_verification.py --workspace friends
    docker compose exec api python scripts/backfill_cross_verification.py --dry-run
    docker compose exec api python scripts/backfill_cross_verification.py --target <uuid>
"""
import argparse
import sys
import uuid as _uuid
from collections import defaultdict

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.finding import Finding
from api.models.target import Target
from api.models.workspace import Workspace


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=None, help="Filter by workspace slug")
    p.add_argument("--target", default=None, help="Single target UUID to backfill")
    p.add_argument("--dry-run", action="store_true", help="Compute but do not write")
    return p.parse_args()


def recompute_target(session, target_id, dry_run: bool = False) -> tuple[int, int]:
    """Recompute cross-verification for all findings of one target.

    Returns (n_findings_seen, n_findings_updated). An update counts only when
    the new column values differ from the existing ones — idempotent re-runs
    report 0 updates.
    """
    findings = session.execute(
        select(Finding).where(Finding.target_id == target_id)
    ).scalars().all()

    by_indicator: dict[str, list] = defaultdict(list)
    for f in findings:
        if f.indicator_value:
            by_indicator[f.indicator_value].append(f)

    n_updated = 0
    for indicator_value, group in by_indicator.items():
        all_modules = sorted({f.module for f in group})
        for f in group:
            peers = [m for m in all_modules if m != f.module]
            new_count = len(peers)
            current_sources = list(f.cross_verification_sources or [])
            if f.cross_verification_count != new_count or current_sources != peers:
                if not dry_run:
                    f.cross_verification_count = new_count
                    f.cross_verification_sources = peers
                n_updated += 1

    return len(findings), n_updated


def main() -> None:
    args = parse_args()
    session = get_sync_session()
    try:
        if args.target:
            target_ids = [_uuid.UUID(args.target)]
        else:
            q = select(Target.id)
            if args.workspace:
                ws = session.execute(
                    select(Workspace).where(Workspace.slug == args.workspace)
                ).scalar_one_or_none()
                if ws is None:
                    print(f"ERROR: workspace slug '{args.workspace}' not found", file=sys.stderr)
                    sys.exit(2)
                q = q.where(Target.workspace_id == ws.id)
            target_ids = [row[0] for row in session.execute(q).all()]

        total_seen = 0
        total_updated = 0
        for tid in target_ids:
            seen, updated = recompute_target(session, tid, dry_run=args.dry_run)
            total_seen += seen
            total_updated += updated

        if not args.dry_run:
            session.commit()

        print(
            f"Targets processed: {len(target_ids)}  findings seen: {total_seen}  "
            f"updates: {total_updated}",
            file=sys.stderr,
        )
        if args.dry_run:
            print("(dry-run — no writes)", file=sys.stderr)
    finally:
        session.close()


if __name__ == "__main__":
    main()
