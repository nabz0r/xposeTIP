"""Add name_blacklist table."""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"


def upgrade():
    op.create_table(
        "name_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pattern", sa.String(500), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False, server_default="exact"),
        sa.Column("reason", sa.String(200)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("name_blacklist")
