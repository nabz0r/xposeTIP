"""BFP public + future protocol endpoints.

Currently exposes a single PUBLIC, unauthenticated aggregate-stats endpoint
consumed by `/bfp` marketing page (BFPStatus.jsx). Aggregates COUNT(*) across
ALL workspaces — no PII, no per-workspace data, no claim contents. Numbers
exposed are already public via SPRINT_LOG.md and BFP_SPEC_v0 non-normative
notes.

DESIGN — public endpoint isolation:
- No `Depends(get_current_user)` / `require_role` / `get_current_workspace`.
- 300s in-memory TTL cache: a single shared dict per worker process. Per-
  worker means up to N workers can hold slightly different snapshots
  (≤300s drift). Acceptable for displayed counts.
- All queries are COUNT(*) on indexed or small tables — fast, no JOINs.
- Future auth-gated BFP routes (subject portal, claim emission API) MUST
  add their own `Depends(...)` per route — do NOT lift auth to router level
  or this public endpoint breaks.
"""
import time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.bfp_claim import BfpClaim
from api.models.bfp_merkle_root import BfpMerkleRoot
from api.models.target import Target

router = APIRouter()

_CACHE: dict = {"data": None, "ts": 0.0}
_TTL_SECONDS = 300.0


@router.get("/stats")
async def bfp_public_stats(db: AsyncSession = Depends(get_db)):
    """Platform-wide BFP substrate aggregate counts. PUBLIC — no auth.

    Returns:
        {
            "behavioral_hashes_computed": int,
            "trust_claims_logged": int,
            "merkle_roots_committed": int
        }

    Cached 300s per worker. No PII, no per-workspace data.
    """
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["ts"]) < _TTL_SECONDS:
        return _CACHE["data"]

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
    }
    _CACHE["data"] = data
    _CACHE["ts"] = now
    return data
