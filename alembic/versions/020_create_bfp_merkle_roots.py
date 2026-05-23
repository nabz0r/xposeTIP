"""Create bfp_merkle_roots table (BFP Phase 1 trust log — Merkle anchor).

S169 — workspace-level append-only snapshots of the Merkle root computed over
bfp_claims.claim_hash. Latest root per workspace = MAX(computed_at). No UNIQUE
on workspace_id: history of roots is intentional.

Tree algorithm: RFC 6962 binary Merkle tree, SHA-3-256, 0x00/0x01 domain
separation, odd-leaf promotion (NOT duplication — CVE-2012-2459). Canonical
leaf order: bfp_claims ORDER BY emitted_at ASC, claim_hash ASC.

Revision ID: 020
Revises: 019
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bfp_merkle_roots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("root_hash", sa.Text, nullable=False),
        sa.Column("num_leaves", sa.Integer, nullable=False),
        sa.Column("root_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_bfp_merkle_roots_workspace", "bfp_merkle_roots", ["workspace_id"])
    op.create_index("idx_bfp_merkle_roots_workspace_computed", "bfp_merkle_roots", ["workspace_id", "computed_at"])


def downgrade():
    op.drop_index("idx_bfp_merkle_roots_workspace_computed", table_name="bfp_merkle_roots")
    op.drop_index("idx_bfp_merkle_roots_workspace", table_name="bfp_merkle_roots")
    op.drop_table("bfp_merkle_roots")
