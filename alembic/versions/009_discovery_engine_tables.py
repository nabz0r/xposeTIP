"""Add discovery_sessions, discovery_leads, and target_links tables for Phase C Discovery Engine."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "009"
down_revision = "008"


def upgrade():
    # discovery_sessions
    op.create_table(
        "discovery_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("target_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("max_queries", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("budget_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("queries_executed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("triggered_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("profile_snapshot", JSONB),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'error')",
            name="valid_session_status",
        ),
    )
    op.create_index("idx_discovery_sessions_target", "discovery_sessions", ["target_id"])

    # discovery_leads
    op.create_table(
        "discovery_leads",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("lead_type", sa.String(20), nullable=False),
        sa.Column("lead_value", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_title", sa.Text()),
        sa.Column("source_snippet", sa.Text()),
        sa.Column("discovery_chain", JSONB, nullable=False, server_default="[]"),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("extractor_type", sa.String(30)),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("ingested_as", sa.String(20)),
        sa.Column("linked_target_id", sa.Uuid(), sa.ForeignKey("targets.id")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "status IN ('new', 'ingested', 'confirmed', 'dismissed')",
            name="valid_lead_status",
        ),
        sa.CheckConstraint(
            "lead_type IN ('email', 'username', 'url', 'name', 'document', 'mention')",
            name="valid_lead_type",
        ),
        sa.CheckConstraint(
            "ingested_as IS NULL OR ingested_as IN ('enriched', 'new_target')",
            name="valid_ingested_as",
        ),
    )
    op.create_index("idx_discovery_leads_target", "discovery_leads", ["target_id"])
    op.create_index("idx_discovery_leads_session", "discovery_leads", ["session_id"])
    op.create_index("idx_discovery_leads_status", "discovery_leads", ["target_id", "status"])

    # target_links
    op.create_table(
        "target_links",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_target_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_target_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("link_type", sa.String(30), nullable=False, server_default="discovered_from"),
        sa.Column("discovery_lead_id", sa.Uuid(), sa.ForeignKey("discovery_leads.id", ondelete="SET NULL")),
        sa.Column("confidence", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "source_target_id != linked_target_id",
            name="no_self_link",
        ),
    )
    op.create_index("idx_target_links_source", "target_links", ["source_target_id"])
    op.create_index("idx_target_links_linked", "target_links", ["linked_target_id"])


def downgrade():
    op.drop_table("target_links")
    op.drop_table("discovery_leads")
    op.drop_table("discovery_sessions")
