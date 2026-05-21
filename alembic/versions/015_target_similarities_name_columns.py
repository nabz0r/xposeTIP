"""S146 — Add name_similarity and cosine_similarity columns to target_similarities.

The existing `similarity` column becomes the canonical combined score
(cosine × name_similarity). `cosine_similarity` preserves the raw cosine for
inspection. `name_similarity` exposes the name-match component. Both new
columns are nullable: NULL on legacy rows pre-recompute, NULL on rows where
neither target has a resolvable name.

Revision ID: 015
Revises: 014
"""
from alembic import op
import sqlalchemy as sa


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "target_similarities",
        sa.Column("name_similarity", sa.Float(), nullable=True),
    )
    op.add_column(
        "target_similarities",
        sa.Column("cosine_similarity", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("target_similarities", "cosine_similarity")
    op.drop_column("target_similarities", "name_similarity")
