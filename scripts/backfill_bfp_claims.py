#!/usr/bin/env python3
"""
S167 — Backfill bfp_claims from existing findings.

Emission rule: cross_verification_count >= 1 AND indicator_type/indicator_value present.
For each qualifying (target_id, claim_type, claim_value) tuple, emits ONE claim
sourced from the EARLIEST qualifying finding.

Idempotent via UNIQUE (target_id, claim_type, claim_value) — re-running yields
0 inserts (ON CONFLICT DO NOTHING in the emitter).

Usage:
    docker compose exec api python scripts/backfill_bfp_claims.py
    docker compose exec api python scripts/backfill_bfp_claims.py --workspace friends
    docker compose exec api python scripts/backfill_bfp_claims.py --dry-run
"""
import argparse
import sys

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.finding import Finding
from api.models.target import Target
from api.models.workspace import Workspace
from api.services.bfp.claim_emitter import emit_claim_for_finding


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=None, help="Filter by workspace slug")
    p.add_argument("--dry-run", action="store_true", help="Count but do not write")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    session = get_sync_session()
    try:
        q = (
            select(Finding)
            .where(
                Finding.cross_verification_count >= 1,
                Finding.indicator_value.isnot(None),
                Finding.indicator_type.isnot(None),
            )
            .order_by(
                Finding.target_id,
                Finding.indicator_type,
                Finding.indicator_value,
                Finding.created_at,
            )
        )
        if args.workspace:
            ws = session.execute(
                select(Workspace).where(Workspace.slug == args.workspace)
            ).scalar_one_or_none()
            if ws is None:
                print(f"ERROR: workspace slug '{args.workspace}' not found", file=sys.stderr)
                sys.exit(2)
            q = q.join(Target, Finding.target_id == Target.id).where(Target.workspace_id == ws.id)

        findings = session.execute(q).scalars().all()

        n_seen = 0
        n_inserted = 0
        seen_tuples: set = set()

        for f in findings:
            n_seen += 1
            tup = (f.target_id, f.indicator_type, f.indicator_value)
            if tup in seen_tuples:
                continue  # earlier finding already emitted in this run
            seen_tuples.add(tup)

            if args.dry_run:
                continue

            if emit_claim_for_finding(f, session):
                n_inserted += 1

        if not args.dry_run:
            session.commit()

        print(
            f"Findings seen: {n_seen}  unique tuples: {len(seen_tuples)}  "
            f"claims inserted: {n_inserted}",
            file=sys.stderr,
        )
        if args.dry_run:
            print("(dry-run — no writes)", file=sys.stderr)
    finally:
        session.close()


if __name__ == "__main__":
    main()
