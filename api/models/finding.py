import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import TIMESTAMP, Boolean, Float, ForeignKey, Index, Integer, String, Text, event, func
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
    # S168 — cross-verification trust signal, formalized from read-time computation.
    # "claim X about subject Y is corroborated by N independent modules". Foundation
    # signal for the BFP trust layer; bfp_claims (S167) will reference these directly.
    cross_verification_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    cross_verification_sources: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    first_seen: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    last_seen: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    # S304a — last_seen + resolved TTL (freshness.py); NULL = unstamped (pre-S304a / backfill pending)
    valid_until: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

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
        Index("idx_findings_cross_verification_count", "cross_verification_count"),
    )


# S304a-2 — leak-proof valid_until net. 6 paths create Finding via ORM add(); only 2
# (persist_scanner_results override-aware + analysis_pipeline) stamped explicitly. This
# before_insert listener fills valid_until ONLY IF still NULL, so every ORM-inserted
# finding (current + future paths) gets at least the category-default TTL. Override-aware
# paths set valid_until before insert → this no-ops for them (per-scraper TTL preserved).
# Category-default only here (the per-scraper override path is persist_scanner_results).
@event.listens_for(Finding, "before_insert")
def _stamp_valid_until(mapper, connection, target):
    if target.valid_until is None:
        from api.services.freshness import resolve_ttl
        base = target.last_seen or datetime.now(timezone.utc)
        target.valid_until = base + timedelta(seconds=resolve_ttl(target.category))
