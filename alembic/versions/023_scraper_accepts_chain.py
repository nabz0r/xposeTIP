"""S185 — Add scrapers.accepts_chain column for crypto chain-shape dispatch gate.

Background: A1.5 stores wallet chain ("btc" | "eth") alongside address in
profile_data.crypto_wallets[]. A1.6 dispatcher was sending every wallet to
every enabled crypto scraper regardless of chain, causing false-positive
findings (e.g. ensideas_resolve emitting a finding for Satoshi BTC because
the API echoes input in the `name` field when no ENS resolves) and wasted
API requests (BTC to EVM scrapers, ETH to BTC scrapers, etc.).

Adds `accepts_chain: ARRAY(Text)` nullable column. NULL = no gate
(multi-chain scrapers like chainabuse_check). Populated = whitelist of
accepted chain values. A1.6 skips mismatched pairs at dispatch with
attempt_log status "skipped_chain_mismatch" (observability preserved).

No data backfill in this migration — seed file (re-run by operator) sets
the field on 13 of 15 crypto_wallet entries via standard upsert.

Revision ID: 023
Revises: 022
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scrapers",
        sa.Column("accepts_chain", postgresql.ARRAY(sa.Text), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scrapers", "accepts_chain")
