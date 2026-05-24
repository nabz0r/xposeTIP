"""S194 — Delete junk username findings (form labels + connection_quality).

Background: prior to S192, the username validator (`is_valid_username()` in
api/services/layer4/username_validator.py) had a narrow `_TITLE_PATTERNS`
tuple that missed form-label values (`Sign Up`, `Log In`, `404 Not Found`,
etc.) scraped from "not found" / auth pages where the scraper saw a
200 OK and extracted the page <title> or a heading.

S192 (commit 6e52016) extended `_TITLE_PATTERNS` with 14 form-label patterns,
closing the validator gap for new writes. This migration cleans up
pre-existing rows in the `findings` table that match the new patterns.

Filter is conservatively narrower than the validator:
- INCLUDED: multi-word patterns ("sign up", "log in", "404 not found", etc.)
  + exact-match `connection_quality` (JSON key from S179-era Threads scraper bug)
- EXCLUDED: "register" and "not available" single-word/phrase patterns
  that substring-match legit handles (`registered_dev`, `not_available_now`)
  with non-zero risk of deleting valid usernames.

FK cascade handling: `identities.source_finding` references `findings.id`
WITHOUT ON DELETE CASCADE, so we must delete the dependent identity rows
first. `identity_links` cascade-deletes automatically (its source_id/dest_id
FKs DO have ON DELETE CASCADE on identities). All cleanup happens in a
single alembic transaction so failure mid-way rolls back atomically.

Backfill is one-shot: downgrade is a no-op + warning log because deleted
junk rows are not recoverable.

Revision ID: 024
Revises: 023
Create Date: 2026-05-24
"""

import logging
from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# Safety cap — abort if the filter would delete more than this many rows
# (combined findings + identities). Same magnitude as S179 migration 022.
_MAX_EXPECTED_DELETIONS = 500


# Filter mirrors a CONSERVATIVE subset of S192 _TITLE_PATTERNS in
# api/services/layer4/username_validator.py. Excludes "register" and
# "not available" patterns that risk substring-matching legit usernames.
# See spec S194 decision #3 for rationale.
_FILTER_SQL = """
    indicator_type = 'username' AND (
        LOWER(indicator_value) LIKE '%sign up%'
        OR LOWER(indicator_value) LIKE '%sign in%'
        OR LOWER(indicator_value) LIKE '%log in%'
        OR LOWER(indicator_value) LIKE '%log out%'
        OR LOWER(indicator_value) LIKE '%create account%'
        OR LOWER(indicator_value) LIKE '%forgot password%'
        OR LOWER(indicator_value) LIKE '%404 not found%'
        OR LOWER(indicator_value) LIKE '%page not found%'
        OR LOWER(indicator_value) LIKE '%user not found%'
        OR LOWER(indicator_value) LIKE '%profile not found%'
        OR LOWER(indicator_value) LIKE '%click here%'
        OR LOWER(indicator_value) LIKE '%learn more%'
        OR LOWER(indicator_value) LIKE '%get started%'
        OR LOWER(indicator_value) = 'connection_quality'
    )
"""


def upgrade() -> None:
    conn = op.get_bind()

    # Sanity-count both tables before delete (combined cap check).
    pre_findings = conn.execute(
        sa.text(f"SELECT COUNT(*) FROM findings WHERE {_FILTER_SQL}")
    ).scalar()
    pre_identities = conn.execute(
        sa.text(
            f"SELECT COUNT(*) FROM identities "
            f"WHERE source_finding IN (SELECT id FROM findings WHERE {_FILTER_SQL})"
        )
    ).scalar()
    combined = (pre_findings or 0) + (pre_identities or 0)

    logger.info(
        "S194 migration 024: %d junk findings + %d dependent identities = %d total rows",
        pre_findings, pre_identities, combined,
    )

    if combined > _MAX_EXPECTED_DELETIONS:
        raise RuntimeError(
            f"S194 migration 024: combined count {combined} "
            f"(findings={pre_findings} + identities={pre_identities}) "
            f"exceeds safety cap of {_MAX_EXPECTED_DELETIONS}. "
            f"Inspect filter before running. See pre-flight count "
            f"in docs/qa/S194_preflight_count.txt."
        )

    # Step 1: delete dependent identities first.
    # `identity_links` rows referencing these identities cascade-delete via
    # the ON DELETE CASCADE on identity_links.source_id / dest_id FKs.
    id_result = conn.execute(
        sa.text(
            f"DELETE FROM identities "
            f"WHERE source_finding IN (SELECT id FROM findings WHERE {_FILTER_SQL})"
        )
    )
    logger.info("S194 migration 024: deleted %d dependent identities", id_result.rowcount)

    # Step 2: delete the junk findings now that the FK references are gone.
    fnd_result = conn.execute(
        sa.text(f"DELETE FROM findings WHERE {_FILTER_SQL}")
    )
    logger.info("S194 migration 024: deleted %d junk username findings", fnd_result.rowcount)


def downgrade() -> None:
    """No-op — deleted junk rows are not recoverable.

    The deleted rows were form-label values (Sign Up, Log In, 404 Not Found,
    etc.) and the `connection_quality` JSON-key value, all incorrectly
    stored as `indicator_type='username'` due to scraper page-title
    extraction on auth/not-found pages. None carry recoverable semantic
    information. Same applies to the dependent identity rows whose
    `source_finding` pointed at these junk findings — they were the
    downstream pollution from the same extraction bug.
    """
    logger.warning(
        "S194 migration 024 downgrade is a no-op — junk findings + dependent "
        "identities previously deleted cannot be restored."
    )
