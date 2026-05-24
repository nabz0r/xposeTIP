"""BFP public + future protocol endpoints.

Currently exposes two PUBLIC, unauthenticated endpoints consumed by `/bfp`
marketing page:
- GET /stats           (S171) — aggregate counts across all workspaces
- GET /recent_anchors  (S173) — N most recent Merkle root snapshots,
                                no workspace_id field exposed

Both endpoints have independent in-memory TTL caches (per worker process).
No PII, no per-workspace identifiers, no claim contents. Numbers exposed
are already public via SPRINT_LOG.md and BFP_SPEC_v0 non-normative notes.

DESIGN — public endpoint isolation:
- No `Depends(get_current_user)` / `require_role` / `get_current_workspace`.
- In-memory TTL cache shields DB from public-traffic spikes.
- Future auth-gated BFP routes MUST add their own `Depends(...)` per route.
  Do NOT lift auth to router level or these public endpoints break.
"""
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.bfp_claim import BfpClaim
from api.models.bfp_merkle_root import BfpMerkleRoot
from api.models.target import Target

router = APIRouter()

# /stats cache (S171)
_STATS_CACHE: dict = {"data": None, "ts": 0.0}
_STATS_TTL_SECONDS = 300.0

# Platform inventory (S189) — constants that change per release, sourced from
# seed_scrapers.py + seed_modules.py + fingerprint_engine.py. Bumping these
# alongside the version field is the contract that keeps the public /bfp page
# in sync with the deployed code.
_PLATFORM_INVENTORY = {
    "scrapers_count": 174,
    "scrapers_active": 149,
    "scrapers_disabled": 25,
    "scanners_count": 27,
    "analyzers_count": 9,
    "axes_count": 11,
    "version": "v1.6.21",
}

# /recent_anchors cache (S173) — single cache slot always holding the top 100,
# slice for the requested limit. Avoids per-limit cache fragmentation.
_RECENT_CACHE: dict = {"data": None, "ts": 0.0}
_RECENT_TTL_SECONDS = 60.0
_RECENT_CACHE_SIZE = 100  # always cache 100 rows, slice for requested limit


@router.get("/stats")
async def bfp_public_stats(db: AsyncSession = Depends(get_db)):
    """Platform-wide BFP substrate aggregate counts + platform inventory. PUBLIC — no auth.

    Returns live BFP substrate counts (DB-queried) merged with platform inventory
    constants (release-pinned): scrapers/scanners/analyzers/axes/version.

    Cached 300s per worker. No PII, no per-workspace data.
    """
    now = time.time()
    if _STATS_CACHE["data"] is not None and (now - _STATS_CACHE["ts"]) < _STATS_TTL_SECONDS:
        return _STATS_CACHE["data"]

    behavioral_hashes = await db.scalar(
        select(func.count())
        .select_from(Target)
        .where(Target.bfp_behavioral_hash_v1.isnot(None))
    )
    trust_claims = await db.scalar(select(func.count()).select_from(BfpClaim))
    merkle_roots = await db.scalar(select(func.count()).select_from(BfpMerkleRoot))

    data = {
        "behavioral_hashes_computed": int(behavioral_hashes or 0),
        "trust_claims_logged": int(trust_claims or 0),
        "merkle_roots_committed": int(merkle_roots or 0),
        **_PLATFORM_INVENTORY,
    }
    _STATS_CACHE["data"] = data
    _STATS_CACHE["ts"] = now
    return data


@router.get("/recent_anchors")
async def bfp_recent_anchors(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """N most recent Merkle root snapshots across all workspaces. PUBLIC — no auth.

    Returns:
        {
            "anchors": [
                {
                    "root_hash": str (64 hex chars, SHA3-256),
                    "num_leaves": int,
                    "computed_at": str (ISO 8601 UTC)
                },
                ...
            ]
        }

    Ordered by computed_at DESC (newest first). No workspace_id field exposed —
    deliberate omission for privacy and visual cleanliness on the public page.

    Cached 60s per worker. Cache always holds the top 100 rows; the response
    slices to `limit`. Hit rate is effectively 100% under the widget's 60s
    polling cadence.
    """
    now = time.time()
    if _RECENT_CACHE["data"] is None or (now - _RECENT_CACHE["ts"]) >= _RECENT_TTL_SECONDS:
        result = await db.execute(
            select(
                BfpMerkleRoot.root_hash,
                BfpMerkleRoot.num_leaves,
                BfpMerkleRoot.computed_at,
            )
            .order_by(BfpMerkleRoot.computed_at.desc())
            .limit(_RECENT_CACHE_SIZE)
        )
        _RECENT_CACHE["data"] = [
            {
                "root_hash": row.root_hash,
                "num_leaves": row.num_leaves,
                "computed_at": row.computed_at.isoformat(),
            }
            for row in result.all()
        ]
        _RECENT_CACHE["ts"] = now

    return {"anchors": _RECENT_CACHE["data"][:limit]}
