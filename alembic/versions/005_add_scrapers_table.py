"""add scrapers table

Revision ID: 005
Revises: 004
Create Date: 2026-03-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scrapers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200)),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(50)),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("url_template", sa.String(500), nullable=False),
        sa.Column("method", sa.String(10), server_default="GET"),
        sa.Column("headers", JSONB, server_default="{}"),
        sa.Column("cookies", JSONB, server_default="{}"),
        sa.Column("body_template", sa.Text()),
        sa.Column("input_type", sa.String(50), nullable=False),
        sa.Column("input_transform", sa.String(200)),
        sa.Column("extraction_rules", JSONB, server_default="[]", nullable=False),
        sa.Column("finding_title_template", sa.String(500)),
        sa.Column("finding_category", sa.String(50)),
        sa.Column("finding_severity", sa.String(20)),
        sa.Column("identity_type", sa.String(50)),
        sa.Column("rate_limit_requests", sa.Integer(), server_default="1"),
        sa.Column("rate_limit_window", sa.Integer(), server_default="2"),
        sa.Column("success_indicator", sa.String(200)),
        sa.Column("not_found_indicators", JSONB, server_default="[]"),
        sa.Column("requires_auth", sa.Boolean(), server_default="false"),
        sa.Column("auth_config", JSONB, server_default="{}"),
        sa.Column("last_tested", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_test_status", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_table("scrapers")
