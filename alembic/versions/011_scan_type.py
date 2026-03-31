"""Add scan_type column to scans table for Phase A.5 rescan tagging."""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"


def upgrade():
    op.add_column("scans", sa.Column("scan_type", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("scans", "scan_type")
