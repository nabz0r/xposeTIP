import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class DiscoverySession(UUIDMixin, Base):
    """Phase C discovery run — tracks queries, pages, and leads found."""
    __tablename__ = "discovery_sessions"

    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))

    # Budget config
    max_queries: Mapped[int] = mapped_column(Integer, default=20)
    max_pages: Mapped[int] = mapped_column(Integer, default=50)
    max_depth: Mapped[int] = mapped_column(Integer, default=2)
    budget_seconds: Mapped[int] = mapped_column(Integer, default=60)

    # Results
    queries_executed: Mapped[int] = mapped_column(Integer, default=0)
    pages_fetched: Mapped[int] = mapped_column(Integer, default=0)
    leads_found: Mapped[int] = mapped_column(Integer, default=0)

    # State
    status: Mapped[str] = mapped_column(String(20), default="running")
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    # Profile snapshot at launch time
    profile_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    target = relationship("Target")
    leads = relationship("DiscoveryLead", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'error')",
            name="valid_session_status",
        ),
        Index("idx_discovery_sessions_target", "target_id"),
    )


class DiscoveryLead(UUIDMixin, Base):
    """A lead extracted from a fetched web page during Phase C discovery."""
    __tablename__ = "discovery_leads"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("discovery_sessions.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))

    # What was found
    lead_type: Mapped[str] = mapped_column(String(20))
    lead_value: Mapped[str] = mapped_column(Text)

    # Where it was found
    source_url: Mapped[str] = mapped_column(Text)
    source_title: Mapped[str | None] = mapped_column(Text)
    source_snippet: Mapped[str | None] = mapped_column(Text)

    # How it was found
    discovery_chain: Mapped[dict] = mapped_column(JSONB, default=[])
    depth: Mapped[int] = mapped_column(Integer, default=0)

    # Scoring
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    extractor_type: Mapped[str | None] = mapped_column(String(30))

    # Operator workflow
    status: Mapped[str] = mapped_column(String(20), default="new")
    ingested_as: Mapped[str | None] = mapped_column(String(20))
    linked_target_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("targets.id"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    session = relationship("DiscoverySession", back_populates="leads")
    target = relationship("Target", foreign_keys=[target_id])

    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'ingested', 'confirmed', 'dismissed')",
            name="valid_lead_status",
        ),
        CheckConstraint(
            "lead_type IN ('email', 'username', 'url', 'name', 'document', 'mention')",
            name="valid_lead_type",
        ),
        CheckConstraint(
            "ingested_as IS NULL OR ingested_as IN ('enriched', 'new_target')",
            name="valid_ingested_as",
        ),
        Index("idx_discovery_leads_target", "target_id"),
        Index("idx_discovery_leads_session", "session_id"),
        Index("idx_discovery_leads_status", "target_id", "status"),
    )


class TargetLink(UUIDMixin, Base):
    """Cross-target relationship discovered during Phase C."""
    __tablename__ = "target_links"

    source_target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    linked_target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))

    link_type: Mapped[str] = mapped_column(String(30), default="discovered_from")
    discovery_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("discovery_leads.id", ondelete="SET NULL")
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    source_target = relationship("Target", foreign_keys=[source_target_id])
    linked_target = relationship("Target", foreign_keys=[linked_target_id])

    __table_args__ = (
        CheckConstraint(
            "source_target_id != linked_target_id",
            name="no_self_link",
        ),
        Index("idx_target_links_source", "source_target_id"),
        Index("idx_target_links_linked", "linked_target_id"),
    )
