"""Add bfp_behavioral_hash_v1 column to targets

Behavioral clustering hash (Phase 1 of BFP roadmap).
v1 uses MinHash over SHA-3-compatible permutations of 3 invariant axes:
public_exposure, geo_spread, data_leaked (identified by S165 invariance diag).

IMPORTANT: This is a clustering primitive, not a uniqueness identifier.
Per S165 entropy analysis (~6.68 bits with K=3), uniqueness arises from
composition with subject binding signature + future network-layer signals.
See docs/BFP_SPEC_v0.md.

Revision ID: 017
Revises: 016
"""
from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "targets",
        sa.Column("bfp_behavioral_hash_v1", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_targets_bfp_behavioral_hash_v1",
        "targets",
        ["bfp_behavioral_hash_v1"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_targets_bfp_behavioral_hash_v1", table_name="targets")
    op.drop_column("targets", "bfp_behavioral_hash_v1")
