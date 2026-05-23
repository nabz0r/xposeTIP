"""BFP claim model — append-only trust substrate (S167).

A BfpClaim is the atomic unit of the BFP protocol's trust layer: a
content-addressable, append-only record asserting that a particular fact
(claim_type, claim_value) about a subject (target_id) is corroborated by
N independent modules at emission time E, with hash H.

Lifecycle:
- INSERT only via api/services/bfp/claim_emitter.py
- NO UPDATE in application code (convention-enforced at MVP)
- NO DELETE in application code (convention-enforced at MVP)
- Deduplication: UNIQUE (target_id, claim_type, claim_value)
  via INSERT ... ON CONFLICT DO NOTHING

Future:
- merkle_position + parent_hash filled by S169 Merkle root builder
- subject_signature + operator_signature filled in Phase 3 (PQC)
- supersession chain via separate mechanism if evidence evolves
"""
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class BfpClaim(UUIDMixin, Base):
    __tablename__ = "bfp_claims"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    source_finding_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("findings.id", ondelete="SET NULL"), nullable=True
    )
    source_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scans.id", ondelete="SET NULL"), nullable=True
    )

    claim_type: Mapped[str] = mapped_column(String(50))
    claim_value: Mapped[str] = mapped_column(String(500))

    cross_verification_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    cross_verification_sources: Mapped[list] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )
    verified_at_emission: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    claim_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Reserved for S169 (Merkle log)
    merkle_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reserved for Phase 3 (PQC signatures)
    subject_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    emitted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    target = relationship("Target")
    source_finding = relationship("Finding")
    source_scan = relationship("Scan")

    __table_args__ = (
        UniqueConstraint("target_id", "claim_type", "claim_value", name="uq_bfp_claims_target_type_value"),
        Index("idx_bfp_claims_target", "target_id"),
        Index("idx_bfp_claims_target_type", "target_id", "claim_type"),
        Index("idx_bfp_claims_claim_hash", "claim_hash"),
        Index("idx_bfp_claims_emitted_at", "emitted_at"),
    )
