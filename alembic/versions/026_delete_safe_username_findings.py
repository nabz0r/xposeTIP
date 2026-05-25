"""S214 — Delete safe-bucket junk username findings.

Background: S213 R&D audit identified 2,820 findings with indicator_type='username'
that are simultaneously (a) rejected by the current `is_valid_username()` validator
and (b) carry zero trust signal (verified=False AND cross_verification_count=0).

This migration deletes that bucket only. The remaining ~120 validator-fail rows
that carry a trust signal (cross_verified >= 1 OR verified=True) are intentionally
preserved for manual triage — they may be legitimate handles incorrectly flagged
by the validator, or junk that nevertheless corroborated across modules.

Scope drift bugs (wayback_domain/rdap_domain emitting username, telegram_profile
page-title extraction) are addressed in separate sprints (S215+). This sprint
cleans historic pollution only.

FK cascade: `identities.source_finding` -> `findings.id` has no ON DELETE CASCADE,
so dependent identity rows must be deleted first. `identity_links` cascade
auto-deletes via its own FKs. All operations in a single alembic transaction.

Revision ID: 026
Revises: 025
Create Date: 2026-05-25
"""
import logging

import sqlalchemy as sa
from alembic import op

from api.services.layer4.username_validator import is_valid_username

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# Safety cap. S213 audit measured 2,820. Cap at 3,500 to allow modest
# corpus growth between audit-run and migration-run without blowing up
# on unexpected DB state.
_MAX_EXPECTED_DELETIONS = 3500

# Trust-bucket SQL filter. Validator-fail check is applied per-row in
# Python after this filter narrows the candidate set.
_TRUST_FILTER_SQL = """
    indicator_type = 'username'
    AND verified = FALSE
    AND cross_verification_count = 0
"""


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: pull candidate (id, indicator_value) tuples matching the
    # trust-bucket SQL filter. This narrows the universe to the same
    # bucket S213 measured — validator-fail check is applied next.
    candidates = conn.execute(
        sa.text(
            f"SELECT id, indicator_value FROM findings "
            f"WHERE {_TRUST_FILTER_SQL}"
        )
    ).fetchall()
    logger.info(
        "S214 migration 026: %d candidate findings in trust bucket "
        "(unverified + cross_verified=0 + indicator_type='username')",
        len(candidates),
    )

    # Step 2: filter to validator-fail rows in Python using the same
    # is_valid_username() implementation that produced S213 numbers.
    junk_ids = [
        row.id for row in candidates
        if not is_valid_username(row.indicator_value or "")
    ]
    logger.info(
        "S214 migration 026: %d candidates fail current validator -> targeted for deletion",
        len(junk_ids),
    )

    if not junk_ids:
        logger.info("S214 migration 026: nothing to delete, exiting cleanly")
        return

    if len(junk_ids) > _MAX_EXPECTED_DELETIONS:
        raise RuntimeError(
            f"S214 migration 026: validator-fail count {len(junk_ids)} "
            f"exceeds safety cap of {_MAX_EXPECTED_DELETIONS}. "
            f"S213 audit baseline was 2,820. Inspect corpus drift before running. "
            f"Re-run scripts/audit_username_findings.py for fresh evidence."
        )

    # Step 3: dependent identities first. `identity_links` cascade-deletes
    # via its own FK constraints.
    id_result = conn.execute(
        sa.text(
            "DELETE FROM identities WHERE source_finding = ANY(:ids)"
        ),
        {"ids": junk_ids},
    )
    logger.info(
        "S214 migration 026: deleted %d dependent identity rows",
        id_result.rowcount,
    )

    # Step 4: the junk findings themselves.
    fnd_result = conn.execute(
        sa.text("DELETE FROM findings WHERE id = ANY(:ids)"),
        {"ids": junk_ids},
    )
    logger.info(
        "S214 migration 026: deleted %d junk username findings",
        fnd_result.rowcount,
    )


def downgrade() -> None:
    """No-op — deleted junk rows are not recoverable.

    The deleted rows were validator-fail values (FQDN-shaped strings,
    page-title fragments, multi-word page bleeds, paren-pattern titles,
    empty strings) with zero corroborating trust signal at deletion time.
    None carry recoverable semantic information. Dependent identity rows
    whose `source_finding` pointed at these junk findings were downstream
    pollution from the same extraction bugs and are equally non-recoverable.
    """
    logger.warning(
        "S214 migration 026 downgrade is a no-op — junk findings + dependent "
        "identities previously deleted cannot be restored."
    )
