"""BFP Merkle root model — workspace-level trust anchor (S169).

A row records a snapshot of the Merkle root computed over all bfp_claims in a
workspace at a given point in time. Append-only — each rebuild creates a new
row, never overwrites or deletes.

The latest root for a workspace = the row with MAX(computed_at). No UNIQUE on
workspace_id: history of root evolution is intentional, so an external auditor
can show "the root at time T was X, at time T' it became Y, and the new claims
between them justify the transition".

Hard tamper-evidence guarantee (the property the BFP public page commits to):
any modification to a past bfp_claims row will change the workspace's
recomputed root_hash. The scripts/verify_bfp_merkle.py helper proves this by
re-deriving the root from raw claim_hash values and asserting equality with
the most recently stored root.

Algorithm version stored in root_version (currently 1 — RFC 6962 binary +
SHA-3-256 + 0x00/0x01 domain separation + (emitted_at, claim_hash) ordering).
Future algorithm changes bump the version; old roots remain interpretable in
their original version.
"""
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class BfpMerkleRoot(UUIDMixin, Base):
    __tablename__ = "bfp_merkle_roots"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    root_hash: Mapped[str] = mapped_column(Text, nullable=False)
    num_leaves: Mapped[int] = mapped_column(Integer, nullable=False)
    root_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    computed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    workspace = relationship("Workspace")

    __table_args__ = (
        Index("idx_bfp_merkle_roots_workspace", "workspace_id"),
        Index("idx_bfp_merkle_roots_workspace_computed", "workspace_id", "computed_at"),
    )
