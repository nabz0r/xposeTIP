import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class Finding(UUIDMixin, Base):
    __tablename__ = "findings"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    module: Mapped[str] = mapped_column(String(50))
    layer: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSONB)
    url: Mapped[str | None] = mapped_column(String(1024))
    indicator_value: Mapped[str | None] = mapped_column(String(500))
    indicator_type: Mapped[str | None] = mapped_column(String(30))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    first_seen: Mapped[datetime] = mapped_column(default=func.now())
    last_seen: Mapped[datetime] = mapped_column(default=func.now())
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    workspace = relationship("Workspace", back_populates="findings")
    scan = relationship("Scan", back_populates="findings")
    target = relationship("Target", back_populates="findings")

    __table_args__ = (
        Index("idx_findings_workspace", "workspace_id"),
        Index("idx_findings_target", "target_id"),
        Index("idx_findings_module", "module"),
        Index("idx_findings_severity", "severity"),
        Index("idx_findings_category", "category"),
        Index("idx_findings_indicator", "indicator_value"),
    )
