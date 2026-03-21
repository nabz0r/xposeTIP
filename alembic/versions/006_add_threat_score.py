"""Add threat_score column to targets."""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"


def upgrade():
    op.add_column("targets", sa.Column("threat_score", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("targets", "threat_score")
