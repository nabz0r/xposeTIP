"""S230 — Relabel name-shaped username findings to indicator_type='name'.

Background: S229 surfaced 237 findings (4.8% of validator-PASS bucket) where
indicator_value matches a 'Firstname Lastname' shape but indicator_type was
written as 'username'. Root cause traced to api/services/layer1/
name_scraper_scanner.py:125 emitting `indicator_type=scraper.input_type`
when name_scraper_engine dispatches a name to a scraper whose input_type
is 'username' (the technical URL-slug input shape). Writer fix shipped
alongside this migration (same sprint, T3).

This migration relabels historical rows. Per-row filter uses
api.services.layer4.username_validator.is_looks_like_full_name() — the
classifier itself is the trust signal, NOT a module allow-list (would
miss long-tail emitters and would over-relabel mixed-bucket modules
like gitlab_profile where ~25% of rows ARE legit handle slugs).

Pattern: S215 migration 027 (scope-drift relabel — values are valid name
data, just mistagged). No DELETE.

Revision ID: 028
Revises: 027
Create Date: 2026-05-25
"""
import logging

import sqlalchemy as sa
from alembic import op

from api.services.layer4.username_validator import is_looks_like_full_name

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# S229 baseline: 237 rows matching looks_like_full_name across all modules.
# Cap at 500 (>100% headroom) to allow drift between S229 audit and migration run.
_MAX_EXPECTED_RELABELS = 500


def upgrade() -> None:
    conn = op.get_bind()

    # Fetch all candidate rows. Filter applied in Python — looks_like_full_name
    # regex isn't expressible cleanly in plain Postgres regex (Unicode range
    # + token-level case check).
    candidates = conn.execute(
        sa.text(
            "SELECT id, indicator_value, module FROM findings "
            "WHERE indicator_type = 'username' AND indicator_value IS NOT NULL"
        )
    ).fetchall()

    relabel_ids = []
    per_module = {}
    for row in candidates:
        if is_looks_like_full_name(row.indicator_value):
            relabel_ids.append(row.id)
            per_module[row.module] = per_module.get(row.module, 0) + 1

    total = len(relabel_ids)
    for module, n in sorted(per_module.items(), key=lambda x: -x[1]):
        logger.info("S230 migration 028: %s has %d looks_like_full_name rows queued", module, n)
    logger.info("S230 migration 028: total relabel candidates = %d", total)

    if total == 0:
        logger.info("S230 migration 028: nothing to relabel, exiting cleanly")
        return

    if total > _MAX_EXPECTED_RELABELS:
        raise RuntimeError(
            f"S230 migration 028: relabel count {total} exceeds safety cap "
            f"of {_MAX_EXPECTED_RELABELS}. S229 baseline was 237. Inspect drift "
            f"before running — possible new emitter or classifier regression."
        )

    # Chunked UPDATE (psycopg2 has IN-list ceiling; chunks of 500 are well under it).
    CHUNK = 500
    total_updated = 0
    for i in range(0, len(relabel_ids), CHUNK):
        chunk = relabel_ids[i:i + CHUNK]
        result = conn.execute(
            sa.text(
                "UPDATE findings SET indicator_type = 'name' "
                "WHERE id = ANY(:ids)"
            ),
            {"ids": chunk},
        )
        total_updated += result.rowcount

    logger.info(
        "S230 migration 028: relabeled %d rows from indicator_type='username' to 'name'",
        total_updated,
    )

    if total_updated != total:
        logger.warning(
            "S230 migration 028: rowcount mismatch — expected %d, updated %d",
            total, total_updated,
        )


def downgrade() -> None:
    """Reverse the relabel — reverts to bug state for testing only."""
    logger.warning(
        "S230 migration 028 DOWNGRADE: no-op. Cannot reliably distinguish migrated "
        "rows from legitimate name-class findings. Restore from backup if needed."
    )
