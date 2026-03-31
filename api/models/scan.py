import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class Scan(UUIDMixin, Base):
    __tablename__ = "scans"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    layer: Mapped[int] = mapped_column(Integer, default=1)
    modules: Mapped[dict | None] = mapped_column(JSONB)
    module_progress: Mapped[dict | None] = mapped_column(JSONB, default={})
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    new_findings: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    scan_type: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    workspace = relationship("Workspace", back_populates="scans")
    target = relationship("Target", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_scans_workspace", "workspace_id"),
        Index("idx_scans_target", "target_id"),
    )
