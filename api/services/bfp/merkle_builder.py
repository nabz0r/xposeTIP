"""BFP Merkle root builder (S169).

RFC 6962-style binary Merkle tree over bfp_claims.claim_hash, per workspace.

Algorithm v1:
    leaf_hash     = SHA-3-256(0x00 || raw_claim_hash_bytes)
    internal_hash = SHA-3-256(0x01 || left || right)
    odd leaf      → promoted unchanged to the next level (NOT duplicated,
                    which is the CVE-2012-2459 antipattern that lets an
                    attacker forge inclusion proofs against an alternate tree)
    leaf order    = bfp_claims ORDER BY emitted_at ASC, claim_hash ASC
                    (deterministic; claim_hash tiebreaker handles same-µs
                    emissions; append-friendly for incremental rebuilds)

Trust property this enables:
    Any modification to a past bfp_claims row changes its claim_hash, which
    changes the leaf hash, which changes the root. An external party holding
    a previous root can detect tampering simply by re-running this builder.
    This is the Certificate-Transparency-style guarantee the BFP page commits
    to. Inclusion-proof generation (sibling paths) is deferred — needed when
    a third-party verifier wants to assert "claim X is in root R" without
    refetching the whole log.

Side effects:
    - Updates bfp_claims.merkle_position (0-indexed, dense per workspace)
    - Inserts a new bfp_merkle_roots row (history is append-only)

This module is the SOLE writer to merkle_position and bfp_merkle_roots.
"""
import hashlib

from sqlalchemy import select

from api.models.bfp_claim import BfpClaim
from api.models.bfp_merkle_root import BfpMerkleRoot

MERKLE_ROOT_VERSION = 1
LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def _hash_leaf(claim_hash_hex: str) -> bytes:
    """RFC 6962 leaf hash over the raw bytes of claim_hash."""
    return hashlib.sha3_256(LEAF_PREFIX + bytes.fromhex(claim_hash_hex)).digest()


def _hash_node(left: bytes, right: bytes) -> bytes:
    """RFC 6962 internal node hash."""
    return hashlib.sha3_256(NODE_PREFIX + left + right).digest()


def compute_merkle_root(leaf_hashes: list[bytes]) -> bytes:
    """Compute the Merkle root from pre-hashed leaves.

    Odd leaves at any level promote unchanged. Returns 32-byte root.
    Raises ValueError on empty input — callers must check len() first.
    """
    if not leaf_hashes:
        raise ValueError("compute_merkle_root requires at least one leaf")

    current_level = leaf_hashes[:]
    while len(current_level) > 1:
        next_level: list[bytes] = []
        i = 0
        while i + 1 < len(current_level):
            next_level.append(_hash_node(current_level[i], current_level[i + 1]))
            i += 2
        if i < len(current_level):
            # Unpaired leaf — promote unchanged (do NOT hash it with itself).
            next_level.append(current_level[i])
        current_level = next_level
    return current_level[0]


def rebuild_workspace_merkle(workspace_id, session) -> dict:
    """Rebuild the Merkle tree for a single workspace.

    Side effects (caller commits):
        - Updates merkle_position on every bfp_claims row for this workspace
          (only rows where the position actually changes are touched)
        - Inserts one new bfp_merkle_roots row (empty workspace → no row)

    Returns: {workspace_id, num_leaves, root_hash, updated_positions}
             root_hash is None when the workspace has zero claims.
    """
    claims = session.execute(
        select(BfpClaim)
        .where(BfpClaim.workspace_id == workspace_id)
        .order_by(BfpClaim.emitted_at.asc(), BfpClaim.claim_hash.asc())
    ).scalars().all()

    if not claims:
        return {
            "workspace_id": workspace_id,
            "num_leaves": 0,
            "root_hash": None,
            "updated_positions": 0,
        }

    updated_positions = 0
    leaf_hashes: list[bytes] = []
    for idx, c in enumerate(claims):
        if c.merkle_position != idx:
            c.merkle_position = idx
            updated_positions += 1
        leaf_hashes.append(_hash_leaf(c.claim_hash))

    root_hex = compute_merkle_root(leaf_hashes).hex()

    session.add(BfpMerkleRoot(
        workspace_id=workspace_id,
        root_hash=root_hex,
        num_leaves=len(claims),
        root_version=MERKLE_ROOT_VERSION,
    ))

    return {
        "workspace_id": workspace_id,
        "num_leaves": len(claims),
        "root_hash": root_hex,
        "updated_positions": updated_positions,
    }


def rebuild_all_workspaces(session) -> list[dict]:
    """Rebuild every workspace that has at least one claim.

    Returns one summary dict per workspace processed.
    """
    workspace_ids = [
        row[0]
        for row in session.execute(select(BfpClaim.workspace_id).distinct()).all()
    ]
    return [rebuild_workspace_merkle(wsid, session) for wsid in workspace_ids]
