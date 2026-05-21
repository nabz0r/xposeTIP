"""TargetSimilarity model — pairwise behavioral + name similarity between workspace targets.

Both directions (A->B and B->A) stored as separate rows. axis_diffs is from
target_a_id perspective (axes_a - axes_b), so the B->A row stores reversed signs.

Columns post-S146:
- similarity: combined score = cosine_similarity × name_similarity (when name_similarity
  is not NULL), else equal to cosine_similarity. This is the canonical "are these the
  same person?" score, gated by STORAGE_THRESHOLD.
- cosine_similarity: raw fingerprint cosine (NULL for legacy rows pre-S146 recompute).
- name_similarity: name-string Jaccard match (NULL when either target has no
  resolvable name, or for legacy rows).
"""
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, Float, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base, UUIDMixin


class TargetSimilarity(UUIDMixin, Base):
    __tablename__ = "target_similarities"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    target_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    target_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    similarity: Mapped[float] = mapped_column(Float)
    cosine_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    name_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    axis_diffs: Mapped[dict] = mapped_column(JSONB)
    first_detected: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    last_computed: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    __table_args__ = (
        CheckConstraint("target_a_id != target_b_id", name="no_self_similarity"),
        CheckConstraint("similarity >= 0.0 AND similarity <= 1.0", name="valid_similarity"),
        Index("idx_target_similarities_pair", "workspace_id", "target_a_id", "target_b_id", unique=True),
        Index("idx_target_similarities_lookup", "workspace_id", "target_a_id", text("similarity DESC")),
    )
