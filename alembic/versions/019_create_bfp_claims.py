"""Create bfp_claims table (BFP Phase 1 trust log).

S167 — append-only content-addressable claim log. Populated by
api/services/bfp/claim_emitter.py from findings with
cross_verification_count >= 1 (the S168-formalized signal).

Reserved columns merkle_position / parent_hash filled by S169.
Reserved columns subject_signature / operator_signature filled by Phase 3.

Append-only enforcement at MVP = convention only (UPDATE/DELETE not used
in app code). Hard enforcement (triggers/REVOKE) deferred to a future
hardening sprint when threat model justifies it. UNIQUE constraint already
blocks the most common "accidental mutation via re-insert" pattern.

Revision ID: 019
Revises: 018
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bfp_claims",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_finding_id", UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_scan_id", UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="SET NULL"), nullable=True),

        sa.Column("claim_type", sa.String(50), nullable=False),
        sa.Column("claim_value", sa.String(500), nullable=False),

        sa.Column("cross_verification_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cross_verification_sources", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("verified_at_emission", sa.Boolean, nullable=False, server_default="false"),

        sa.Column("claim_hash", sa.Text, nullable=False),

        # Reserved for S169 (Merkle)
        sa.Column("merkle_position", sa.Integer, nullable=True),
        sa.Column("parent_hash", sa.Text, nullable=True),

        # Reserved for Phase 3 (PQC signatures)
        sa.Column("subject_signature", sa.Text, nullable=True),
        sa.Column("operator_signature", sa.Text, nullable=True),

        sa.Column("emitted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.UniqueConstraint("target_id", "claim_type", "claim_value", name="uq_bfp_claims_target_type_value"),
    )
    op.create_index("idx_bfp_claims_target", "bfp_claims", ["target_id"])
    op.create_index("idx_bfp_claims_target_type", "bfp_claims", ["target_id", "claim_type"])
    op.create_index("idx_bfp_claims_claim_hash", "bfp_claims", ["claim_hash"])
    op.create_index("idx_bfp_claims_emitted_at", "bfp_claims", ["emitted_at"])


def downgrade():
    op.drop_index("idx_bfp_claims_emitted_at", table_name="bfp_claims")
    op.drop_index("idx_bfp_claims_claim_hash", table_name="bfp_claims")
    op.drop_index("idx_bfp_claims_target_type", table_name="bfp_claims")
    op.drop_index("idx_bfp_claims_target", table_name="bfp_claims")
    op.drop_table("bfp_claims")
