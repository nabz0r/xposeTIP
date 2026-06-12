"""S290 — kind discriminator (human|agent) on workspaces + scrapers.

server_default 'human' backfills every existing workspace AND scraper at the DB
level. Zero data migration. Makes the engine type-aware; behaviour is unchanged
until agent rows exist (S291). All existing targets (via their workspaces) and
all scrapers become 'human' automatically.

Revision ID: 030
Revises: 029
"""
from alembic import op
import sqlalchemy as sa

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade():
    for tbl in ("workspaces", "scrapers"):
        op.add_column(tbl, sa.Column("kind", sa.String(10), nullable=False,
                                     server_default="human"))
        op.create_check_constraint(f"{tbl}_kind_valid", tbl, "kind IN ('human','agent')")


def downgrade():
    for tbl in ("workspaces", "scrapers"):
        op.drop_constraint(f"{tbl}_kind_valid", tbl, type_="check")
        op.drop_column(tbl, "kind")
