"""S215 — Relabel scope-drift username findings to domain.

Background: 4 domain-input scrapers (wayback_domain, rdap_domain,
alienvault_otx_domain, securitytrails_ping) shipped without
`identity_type` set in scripts/seed_scrapers.py. Pre-S159 they wrote
indicator_type='username' (hardcoded fallback). S159 fixed the runtime
fallback (now `identity_type or input_type`) but migration 016's
DOMAIN_MODULES list missed these 4 modules — their historic rows
remained mistagged.

S214 left these as the 100% validator-fail residue (correctly — they're
FQDN values, validator rejects them as usernames, but they ARE valid
domain findings). This migration completes the S159/016 fix by
relabeling those rows to indicator_type='domain', their actual semantic
type.

No DELETE in this migration — the values are real domain data, just
mislabeled. Companion seed fix in scripts/seed_scrapers.py prevents
future occurrences (T1).

Revision ID: 027
Revises: 026
Create Date: 2026-05-25
"""
import logging

import sqlalchemy as sa
from alembic import op

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# Same modules whose seed-level identity_type was missing.
# securitytrails_ping is enabled=False but included for completeness in
# case historic rows exist from a past enabled=True period.
_SCOPE_DRIFT_MODULES = (
    "wayback_domain",
    "rdap_domain",
    "alienvault_otx_domain",
    "securitytrails_ping",
)

# S213 baseline (post-S214): 77 rows (46 rdap_domain + 31 wayback_domain).
# Cap at 200 to allow modest drift and the 2 unseen modules' contribution.
_MAX_EXPECTED_RELABELS = 200


def upgrade() -> None:
    conn = op.get_bind()

    # Pre-count per module for the log + safety cap.
    per_module = conn.execute(
        sa.text(
            "SELECT module, COUNT(*) AS n FROM findings "
            "WHERE indicator_type = 'username' "
            "AND module = ANY(:mods) "
            "GROUP BY module ORDER BY module"
        ),
        {"mods": list(_SCOPE_DRIFT_MODULES)},
    ).fetchall()

    total = sum(r.n for r in per_module)
    for r in per_module:
        logger.info("S215 migration 027: %s has %d username rows queued for relabel", r.module, r.n)
    logger.info("S215 migration 027: total relabel candidates = %d", total)

    if total == 0:
        logger.info("S215 migration 027: nothing to relabel, exiting cleanly")
        return

    if total > _MAX_EXPECTED_RELABELS:
        raise RuntimeError(
            f"S215 migration 027: relabel count {total} exceeds safety cap "
            f"of {_MAX_EXPECTED_RELABELS}. S213 baseline was 77 (post-S214). "
            f"Inspect drift before running."
        )

    result = conn.execute(
        sa.text(
            "UPDATE findings SET indicator_type = 'domain' "
            "WHERE indicator_type = 'username' AND module = ANY(:mods)"
        ),
        {"mods": list(_SCOPE_DRIFT_MODULES)},
    )
    logger.info(
        "S215 migration 027: relabeled %d rows from indicator_type='username' to 'domain'",
        result.rowcount,
    )


def downgrade() -> None:
    """Reverse the relabel."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "UPDATE findings SET indicator_type = 'username' "
            "WHERE indicator_type = 'domain' AND module = ANY(:mods)"
        ),
        {"mods": list(_SCOPE_DRIFT_MODULES)},
    )
    logger.warning(
        "S215 migration 027 DOWNGRADE: reverted %d rows back to indicator_type='username'. "
        "Note: this restores the bug. Only useful for testing.",
        result.rowcount,
    )
