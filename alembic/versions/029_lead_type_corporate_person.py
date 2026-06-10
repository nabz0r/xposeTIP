"""S264-0f — allow 'corporate_person' (+ 'organization') lead_type on discovery_leads.

The AR-0 corporate-person lead_type (S264-0 B) was never added to the
`valid_lead_type` CHECK constraint (created in migration 009), so every autonomous
AR-0 lead INSERT failed with CheckViolation → the discovery transaction rolled back
→ no corporate_person lead ever persisted. This is the root reason autonomous
resolution never surfaced (validation had used extract_all / injected findings,
never a real discovery_lead insert). Extend the allowed set.

Revision ID: 029
Revises: 028
"""
from alembic import op

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None

_OLD = "lead_type IN ('email', 'username', 'url', 'name', 'document', 'mention')"
_NEW = ("lead_type IN ('email', 'username', 'url', 'name', 'document', 'mention', "
        "'corporate_person', 'organization')")


def upgrade():
    op.drop_constraint("valid_lead_type", "discovery_leads", type_="check")
    op.create_check_constraint("valid_lead_type", "discovery_leads", _NEW)


def downgrade():
    # NOTE: will fail if any 'corporate_person'/'organization' rows exist — delete
    # them first if downgrading. Reverses to the pre-S264-0f allowed set.
    op.drop_constraint("valid_lead_type", "discovery_leads", type_="check")
    op.create_check_constraint("valid_lead_type", "discovery_leads", _OLD)
