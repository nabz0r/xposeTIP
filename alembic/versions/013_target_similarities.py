"""Add target_similarities table for S131 similarity engine.

Stores pairwise fingerprint cosine similarity (>= 0.7) between workspace targets.
Both directions (A->B and B->A) stored as separate rows for simpler indexed queries.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "013"
down_revision = "012"


def upgrade():
    op.create_table(
        "target_similarities",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("target_a_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_b_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("axis_diffs", JSONB, nullable=False),
        sa.Column("first_detected", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_computed", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("target_a_id != target_b_id", name="no_self_similarity"),
        sa.CheckConstraint("similarity >= 0.0 AND similarity <= 1.0", name="valid_similarity"),
    )
    op.create_index(
        "idx_target_similarities_pair",
        "target_similarities",
        ["workspace_id", "target_a_id", "target_b_id"],
        unique=True,
    )
    op.create_index(
        "idx_target_similarities_lookup",
        "target_similarities",
        ["workspace_id", "target_a_id", sa.text("similarity DESC")],
    )


def downgrade():
    op.drop_index("idx_target_similarities_lookup", table_name="target_similarities")
    op.drop_index("idx_target_similarities_pair", table_name="target_similarities")
    op.drop_table("target_similarities")
