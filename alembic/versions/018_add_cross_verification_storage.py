"""Add cross-verification storage to findings.

S168 — formalizes the cross-verification trust signal from read-time
computation (api/routers/findings.py:54-68 + 154-167) into persisted,
queryable columns.

This is the BFP trust layer's seed signal — `bfp_claims` (S167) will
reference `cross_verification_count` directly instead of recomputing
from the indicator_value join at every read.

Revision ID: 018
Revises: 017
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "findings",
        sa.Column(
            "cross_verification_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "findings",
        sa.Column(
            "cross_verification_sources",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_index(
        "idx_findings_cross_verification_count",
        "findings",
        ["cross_verification_count"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_findings_cross_verification_count", table_name="findings")
    op.drop_column("findings", "cross_verification_sources")
    op.drop_column("findings", "cross_verification_count")
