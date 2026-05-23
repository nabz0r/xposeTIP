"""S179 — Delete junk username rows from identities table.

Background: prior to S179, two username validators
(`is_valid_username()` central + `_is_valid_extracted_username()` local
to graph_builder) both missed two patterns: (1) FQDN single-dot values
like `gmail.com`, `lessentiel.lu`; (2) the specific JSON key
`connection_quality` from a Threads scraper bug. Plus a paren-containing
replit-style title `HBrandon (Brandon Herrera)`. This led to ~290 junk
rows accumulating in the `identities` table.

S179 T1+T2 close the validator gaps for future writes. This migration
cleans up the existing pollution. The DELETE filter is per-platform
narrowed to avoid false positives (Steam handles, GitLab handles,
chesscom display names, etc. that look domain-shaped or 2-worded but
are real usernames on platforms that allow such formats).

Backfill is one-shot: downgrade is a no-op + warning log because
deleted junk is not recoverable.

Revision ID: 022
Revises: 021
Create Date: 2026-05-23
"""

import logging
from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# Safety cap — abort if the filter would delete more than this many
# rows. Protects against runaway delete on unexpected DB state.
_MAX_EXPECTED_DELETIONS = 500


_FILTER_SQL = """
    type = 'username' AND (
        -- Category A: HTML page-title fragments
        value LIKE '%% on about.me'
        OR value LIKE '%%''s collection | Bandcamp'
        OR value LIKE '%%&#39;s collection | Bandcamp'
        OR value LIKE '%% | Linktree'
        OR (platform = 'linkedin' AND value LIKE '%% - %%')
        OR (platform = 'replit'   AND value LIKE '%% (%% %%)')
        OR value = 'Telegram – a new era of messaging'
        OR value = 'connection_quality'
        -- Category B: domains tagged type='username' (per offending scraper)
        OR (platform IN ('dns_dmarc_check', 'dns_txt_saas',
                         'crtsh_subdomains', 'disposable_email_check',
                         'hackertarget_hosts', 'rdap_domain',
                         'wayback_count', 'wayback_domain')
            AND value ~ '^[a-z0-9.-]+\\.(com|org|net|lu|fr|de|uk|io|co|app|gov|edu|info|biz|me|us|ca|au|nl|be|ch|it|es)$')
        -- Edge case
        OR value = '1800 INFORMATION'
    )
"""


def upgrade() -> None:
    conn = op.get_bind()

    # Sanity-count before delete
    pre_count = conn.execute(
        sa.text(f"SELECT COUNT(*) FROM identities WHERE {_FILTER_SQL}")
    ).scalar()
    logger.info("S179 migration 022: %d junk username rows match filter", pre_count)

    if pre_count > _MAX_EXPECTED_DELETIONS:
        raise RuntimeError(
            f"S179 migration 022: filter matched {pre_count} rows, "
            f"exceeds safety cap of {_MAX_EXPECTED_DELETIONS}. "
            f"Inspect filter before running."
        )

    result = conn.execute(
        sa.text(f"DELETE FROM identities WHERE {_FILTER_SQL}")
    )
    logger.info("S179 migration 022: deleted %d junk username rows", result.rowcount)


def downgrade() -> None:
    """No-op — deleted junk rows are not recoverable.

    The deleted rows were page titles, JSON keys, and FQDN values
    mistakenly stored as `type='username'`. None of them carry
    semantic information worth restoring.
    """
    logger.warning(
        "S179 migration 022 downgrade is a no-op — junk username rows "
        "previously deleted from identities table cannot be restored."
    )
