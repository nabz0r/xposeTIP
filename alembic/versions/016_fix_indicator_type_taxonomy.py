"""S159 — Fix indicator_type taxonomy for misconfigured scrapers.

Audit (Q1+Q2+Q3 DB samples) confirmed 15 scrapers were writing
`indicator_type='username'` despite producing domains or emails. Root
cause: ZERO scrapers in seed_scrapers.py had an explicit identity_type;
all fell back to "username" via scraper_scanner.py.

This migration:
  1. Relabels existing findings to the correct indicator_type
  2. Deletes findings with empty indicator_value (writer noise)
  3. Tags intelligence-module synthesized name candidates with
     data.platform='name_synthesis' so they're filterable

Forward-only safe. The DELETE step is destructive; downgrade restores
the relabels but cannot restore deleted empty rows.

Revision ID: 016
Revises: 015
"""
from alembic import op
import sqlalchemy as sa


revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


DOMAIN_MODULES = [
    "crtsh_subdomains",
    "dns_dmarc_check",
    "dns_txt_saas",
    "hackertarget_hosts",
    "wayback_count",
    "disposable_email_check",
]

EMAIL_MODULES = [
    "emailrep_breaches",
    "google_groups_search",
    "google_scholar_search",
    "intelx_public",
    "leakcheck_public",
    "mailcheck_email",
    "webmii_search",
    "disify_email",
    "github_email_search",
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Relabel domain-producing modules
    conn.execute(
        sa.text(
            "UPDATE findings SET indicator_type = 'domain' "
            "WHERE indicator_type = 'username' AND module = ANY(:mods)"
        ),
        {"mods": DOMAIN_MODULES},
    )

    # 2. Relabel email-producing modules
    conn.execute(
        sa.text(
            "UPDATE findings SET indicator_type = 'email' "
            "WHERE indicator_type = 'username' AND module = ANY(:mods)"
        ),
        {"mods": EMAIL_MODULES},
    )

    # 3. Delete empty-indicator_value rows from the 15 mislabeled modules.
    # These were writer noise (scraper ran, returned nothing usable).
    all_mods = DOMAIN_MODULES + EMAIL_MODULES
    conn.execute(
        sa.text(
            "DELETE FROM findings "
            "WHERE module = ANY(:mods) "
            "AND (indicator_value IS NULL OR TRIM(indicator_value) = '')"
        ),
        {"mods": all_mods},
    )

    # 4. Tag intelligence-module synthesized name candidates so they're filterable.
    # Per Q1 sample: 1684 rows from `intelligence` module have NULL platform,
    # they're synthesized username candidates from name-derivation (Pass 1.5 / behavioral profiler).
    conn.execute(
        sa.text(
            "UPDATE findings "
            "SET data = jsonb_set(COALESCE(data, '{}'::jsonb), '{platform}', '\"name_synthesis\"'::jsonb) "
            "WHERE indicator_type = 'username' "
            "AND module = 'intelligence' "
            "AND (data->>'platform' IS NULL OR data->>'platform' = '')"
        )
    )


def downgrade() -> None:
    """Restore indicator_type labels and remove platform tag.

    Note: deleted empty-value rows cannot be restored. The DELETE in
    upgrade() is destructive.
    """
    conn = op.get_bind()

    all_mods = DOMAIN_MODULES + EMAIL_MODULES
    conn.execute(
        sa.text(
            "UPDATE findings SET indicator_type = 'username' "
            "WHERE module = ANY(:mods)"
        ),
        {"mods": all_mods},
    )

    conn.execute(
        sa.text(
            "UPDATE findings "
            "SET data = data - 'platform' "
            "WHERE module = 'intelligence' "
            "AND data->>'platform' = 'name_synthesis'"
        )
    )
