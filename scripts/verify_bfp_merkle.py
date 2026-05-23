#!/usr/bin/env python3
"""
Independent verification of stored BFP Merkle roots. S169.

For each workspace that has a stored root, re-derive the Merkle root from raw
bfp_claims.claim_hash values (via the same canonical algorithm) and assert
equality with the most recent stored root.

This is the property that makes the trust log meaningful:
    any tampering with past claim_hash, emitted_at, or claim order
    will break this verification.

Exit codes:
    0 — all workspaces match
    1 — at least one workspace mismatched (count or root)

Usage:
    docker compose exec api python scripts/verify_bfp_merkle.py
"""
import sys

from sqlalchemy import select

from api.models.bfp_claim import BfpClaim
from api.models.bfp_merkle_root import BfpMerkleRoot
from api.services.bfp.merkle_builder import _hash_leaf, compute_merkle_root
from api.tasks.utils import get_sync_session


def main():
    session = get_sync_session()
    try:
        workspace_ids = [
            row[0]
            for row in session.execute(select(BfpMerkleRoot.workspace_id).distinct()).all()
        ]

        n_ok = 0
        n_mismatch = 0
        for wsid in workspace_ids:
            latest = session.execute(
                select(BfpMerkleRoot)
                .where(BfpMerkleRoot.workspace_id == wsid)
                .order_by(BfpMerkleRoot.computed_at.desc())
                .limit(1)
            ).scalar_one()

            claims = session.execute(
                select(BfpClaim)
                .where(BfpClaim.workspace_id == wsid)
                .order_by(BfpClaim.emitted_at.asc(), BfpClaim.claim_hash.asc())
            ).scalars().all()

            if len(claims) != latest.num_leaves:
                print(
                    f"  {wsid}: COUNT MISMATCH stored={latest.num_leaves} current={len(claims)}",
                    file=sys.stderr,
                )
                n_mismatch += 1
                continue

            if not claims:
                continue

            recomputed = compute_merkle_root([_hash_leaf(c.claim_hash) for c in claims]).hex()
            if recomputed == latest.root_hash:
                n_ok += 1
                print(
                    f"  {wsid}: OK   {latest.num_leaves:5d} leaves  root={latest.root_hash[:16]}…",
                    file=sys.stderr,
                )
            else:
                n_mismatch += 1
                print(
                    f"  {wsid}: FAIL stored={latest.root_hash[:16]}…  "
                    f"recomputed={recomputed[:16]}…",
                    file=sys.stderr,
                )

        total = n_ok + n_mismatch
        print(f"\nVerified: {n_ok}/{total} workspaces match", file=sys.stderr)
        sys.exit(0 if n_mismatch == 0 else 1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
