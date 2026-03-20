"""Add profile_data JSONB column to targets

Revision ID: 002
Revises: 001
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("targets", sa.Column("profile_data", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("targets", "profile_data")
