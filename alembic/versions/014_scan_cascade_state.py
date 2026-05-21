"""Add cascade_state to scans table

Revision ID: 014
Revises: 013
Create Date: 2026-05-21

Tracks post-scrape cascade pipeline progress (PASS A / PASS B / similarity recompute).
The existing `scans.status` field only reflects scraper completion — the cascade
that builds findings → graph → score → fingerprint → similarity continues for
5-8 minutes after status='completed'.

Values: null (legacy), 'gathering', 'computing', 'similarity', 'done', 'failed'.
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "scans",
        sa.Column("cascade_state", sa.String(20), nullable=True, server_default=None),
    )
    op.create_index(
        "idx_scans_status_cascade",
        "scans",
        ["status", "cascade_state"],
    )
    op.execute(
        "UPDATE scans SET cascade_state = 'done' "
        "WHERE status = 'completed' AND cascade_state IS NULL"
    )


def downgrade():
    op.drop_index("idx_scans_status_cascade", table_name="scans")
    op.drop_column("scans", "cascade_state")
