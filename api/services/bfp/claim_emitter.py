"""BFP claim emission — the only writer to bfp_claims table (S167).

Emission rule (LOCKED): a claim is emitted exactly when a finding has
cross_verification_count >= 1 AND non-null indicator_type/indicator_value.
Cross-verification is the strongest available trust signal — emitting on
`verified` alone would emit weaker claims.

Idempotent via UNIQUE (target_id, claim_type, claim_value) — repeated
emission of the same canonical tuple is silently swallowed by ON CONFLICT DO NOTHING.

Future evidence evolution (when N or sources change for a tuple already
emitted) is intentionally NOT handled here — the UNIQUE constraint blocks
re-insert. Supersession chains will live in a separate mechanism (post-S167).
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.models.bfp_claim import BfpClaim
from api.models.finding import Finding


CLAIM_HASH_VERSION = 1


def compute_claim_hash(
    target_id: str,
    claim_type: str,
    claim_value: str,
    cross_verification_count: int,
    cross_verification_sources: list[str],
    verified_at_emission: bool,
    emitted_at_iso: str,
) -> str:
    """SHA-3-256 of canonical JSON encoding of claim content.

    Sort keys + sort sources list + compact separators = deterministic.
    claim_hash_version baked in so schema changes are detectable.
    """
    canonical = json.dumps(
        {
            "target_id": target_id,
            "claim_type": claim_type,
            "claim_value": claim_value,
            "cross_verification_count": cross_verification_count,
            "cross_verification_sources": sorted(cross_verification_sources),
            "verified_at_emission": verified_at_emission,
            "emitted_at": emitted_at_iso,
            "claim_hash_version": CLAIM_HASH_VERSION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


def emit_claim_for_finding(finding: Finding, session) -> bool:
    """Emit a BFP claim for the given finding if it qualifies.

    Returns True if a new claim row was inserted, False if skipped
    (either ineligible or already emitted via UNIQUE conflict).
    """
    if not finding.indicator_value or not finding.indicator_type:
        return False
    if (finding.cross_verification_count or 0) < 1:
        return False

    emitted_at = datetime.now(timezone.utc)
    sources = list(finding.cross_verification_sources or [])
    claim_hash = compute_claim_hash(
        target_id=str(finding.target_id),
        claim_type=finding.indicator_type,
        claim_value=finding.indicator_value,
        cross_verification_count=finding.cross_verification_count,
        cross_verification_sources=sources,
        verified_at_emission=bool(finding.verified),
        emitted_at_iso=emitted_at.isoformat(),
    )

    stmt = (
        pg_insert(BfpClaim)
        .values(
            workspace_id=finding.workspace_id,
            target_id=finding.target_id,
            source_finding_id=finding.id,
            source_scan_id=finding.scan_id,
            claim_type=finding.indicator_type,
            claim_value=finding.indicator_value,
            cross_verification_count=finding.cross_verification_count,
            cross_verification_sources=sources,
            verified_at_emission=bool(finding.verified),
            claim_hash=claim_hash,
            emitted_at=emitted_at,
        )
        .on_conflict_do_nothing(
            index_elements=["target_id", "claim_type", "claim_value"],
        )
    )
    result = session.execute(stmt)
    return (result.rowcount or 0) > 0


def emit_claims_for_findings(findings: Iterable[Finding], session) -> int:
    """Batch helper. Returns count of newly inserted claims."""
    return sum(1 for f in findings if emit_claim_for_finding(f, session))
