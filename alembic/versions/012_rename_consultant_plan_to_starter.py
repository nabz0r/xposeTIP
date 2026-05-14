"""Rename consultant plan to starter

Revision ID: 012
Revises: 011
Create Date: 2026-05-14

S116a: Rename SaaS plan 'consultant' to 'starter' for 4-tier alignment
(Free / Starter / Team / Enterprise). Role 'consultant' is unaffected —
this is a workspaces.plan data migration only.
"""
from alembic import op


# revision identifiers, used by Alembic
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE workspaces SET plan = 'starter' WHERE plan = 'consultant'")


def downgrade() -> None:
    op.execute("UPDATE workspaces SET plan = 'consultant' WHERE plan = 'starter'")
