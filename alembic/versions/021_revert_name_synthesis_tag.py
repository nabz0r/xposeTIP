"""S178 — Revert name_synthesis platform tag on intelligence findings.

Migration 016 (S159) tagged 1,684 intelligence-module username findings
with `data.platform='name_synthesis'` to make them filterable. The
frontend (UsernameTab) then filtered them out entirely via its
PLATFORM_COLORS allow-list, hiding legitimate analyzer correlation
output. S178 fixes the frontend to handle intelligence-module findings
on a dedicated path (no platform-scalar dependency); this migration
removes the now-misleading sentinel from the data column so future
contributors don't pattern-match on a fake platform name.

Revision ID: 021
Revises: 020
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop the data.platform key when its value is 'name_synthesis' on
    intelligence-module username findings.
    """
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE findings "
            "SET data = data - 'platform' "
            "WHERE module = 'intelligence' "
            "AND indicator_type = 'username' "
            "AND data->>'platform' = 'name_synthesis'"
        )
    )


def downgrade() -> None:
    """Restore the name_synthesis tag on intelligence-module username
    findings that currently have no platform key. Idempotent."""
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE findings "
            "SET data = jsonb_set(COALESCE(data, '{}'::jsonb), "
            "                     '{platform}', '\"name_synthesis\"'::jsonb) "
            "WHERE module = 'intelligence' "
            "AND indicator_type = 'username' "
            "AND (data->>'platform' IS NULL OR data->>'platform' = '')"
        )
    )
