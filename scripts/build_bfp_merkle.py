#!/usr/bin/env python3
"""
Build (or rebuild) Merkle roots over bfp_claims, per workspace. S169.

Idempotent — each invocation appends a fresh bfp_merkle_roots row even when
the underlying claims didn't change. The root_hash will be identical to the
previous row in that case, which is the intended signal of stability.

Usage:
    docker compose exec api python scripts/build_bfp_merkle.py
    docker compose exec api python scripts/build_bfp_merkle.py --workspace friends
    docker compose exec api python scripts/build_bfp_merkle.py --dry-run
"""
import argparse
import sys

from sqlalchemy import select

from api.models import Workspace
from api.services.bfp.merkle_builder import (
    rebuild_all_workspaces,
    rebuild_workspace_merkle,
)
from api.tasks.utils import get_sync_session


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default=None, help="Workspace slug to rebuild (default: all with claims)")
    p.add_argument("--dry-run", action="store_true", help="Compute but rollback the transaction")
    return p.parse_args()


def main():
    args = parse_args()
    session = get_sync_session()
    try:
        if args.workspace:
            ws = session.execute(
                select(Workspace).where(Workspace.slug == args.workspace)
            ).scalar_one_or_none()
            if not ws:
                print(f"Workspace not found: {args.workspace}", file=sys.stderr)
                sys.exit(1)
            results = [rebuild_workspace_merkle(ws.id, session)]
        else:
            results = rebuild_all_workspaces(session)

        if args.dry_run:
            session.rollback()
        else:
            session.commit()

        total_leaves = sum(r["num_leaves"] for r in results)
        print(f"Workspaces processed: {len(results)}  total claims: {total_leaves}", file=sys.stderr)
        for r in results:
            if r["root_hash"]:
                print(
                    f"  {r['workspace_id']}: {r['num_leaves']:5d} leaves → {r['root_hash'][:16]}…  "
                    f"(positions updated: {r['updated_positions']})",
                    file=sys.stderr,
                )
            else:
                print(f"  {r['workspace_id']}:     0 leaves (no root written)", file=sys.stderr)

        if args.dry_run:
            print("(dry-run — rolled back)", file=sys.stderr)
    finally:
        session.close()


if __name__ == "__main__":
    main()
