"""S195 — Add User.last_active_workspace_id to persist workspace selection.

Background: prior to S195, /auth/refresh and /auth/login both resolve
workspace via `select(UserWorkspace).limit(1)` which is nondeterministic
order but in practice returns first-inserted membership. User-visible
symptom: every JWT refresh silently reverts active workspace, regardless
of /switch-workspace calls.

This migration adds a nullable column `last_active_workspace_id` on the
users table, with FK to workspaces.id and ON DELETE SET NULL.

Backward compatibility: column defaults to NULL for all existing rows.
/login and /refresh fall back to current .limit(1) behavior when NULL,
so no behavior change for users who haven't yet exercised /switch-workspace
post-deploy.

Revision ID: 025
Revises: 024
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "last_active_workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "last_active_workspace_id")
