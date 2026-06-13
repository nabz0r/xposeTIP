"""S304a — freshness foundation: scrapers.ttl_seconds + findings.valid_until.

Both columns NULLABLE (NULL is meaningful: scraper ttl_seconds NULL → use category
default; finding valid_until NULL → unstamped, backfilled by scripts/backfill_valid_until.py).
NO NOT NULL / NO CHECK on existing rows (AR-0 lesson: a CHECK silently rolled back inserts).
Index on findings.valid_until for the S304d `valid_until < now()` smart-rescan query.
Descriptive only — does not touch confidence.

Revision ID: 031
Revises: 030
"""
from alembic import op
import sqlalchemy as sa

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("scrapers", sa.Column("ttl_seconds", sa.Integer(), nullable=True))
    op.add_column("findings", sa.Column("valid_until", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_findings_valid_until", "findings", ["valid_until"])


def downgrade():
    op.drop_index("idx_findings_valid_until", table_name="findings")
    op.drop_column("findings", "valid_until")
    op.drop_column("scrapers", "ttl_seconds")
