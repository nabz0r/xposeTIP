"""Add user_first_name and user_last_name to targets."""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"


def upgrade():
    op.add_column("targets", sa.Column("user_first_name", sa.String(100), nullable=True))
    op.add_column("targets", sa.Column("user_last_name", sa.String(100), nullable=True))


def downgrade():
    op.drop_column("targets", "user_last_name")
    op.drop_column("targets", "user_first_name")
