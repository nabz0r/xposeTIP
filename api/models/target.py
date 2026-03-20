import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin, UUIDMixin


class Target(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "targets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    country_code: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    exposure_score: Mapped[int | None] = mapped_column(Integer)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    first_scanned: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_scanned: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    tags: Mapped[list | None] = mapped_column(ARRAY(Text))
    notes: Mapped[str | None] = mapped_column(Text)
    profile_data: Mapped[dict | None] = mapped_column(JSONB)
    fingerprint_history: Mapped[list | None] = mapped_column(JSONB, default=list)

    workspace = relationship("Workspace", back_populates="targets")
    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="target", cascade="all, delete-orphan")
    identities = relationship("Identity", back_populates="target", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_targets_workspace", "workspace_id"),
        Index("idx_targets_score", exposure_score.desc()),
        {"schema": None},
    )
