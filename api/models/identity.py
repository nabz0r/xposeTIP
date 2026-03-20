import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, UUIDMixin


class Identity(UUIDMixin, Base):
    __tablename__ = "identities"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(String(500))
    platform: Mapped[str | None] = mapped_column(String(100))
    source_module: Mapped[str | None] = mapped_column(String(50))
    source_finding: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("findings.id"))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    target = relationship("Target", back_populates="identities")

    __table_args__ = (
        Index("uq_identity", "workspace_id", "target_id", "type", "value", unique=True),
    )


class IdentityLink(UUIDMixin, Base):
    __tablename__ = "identity_links"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"))
    dest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"))
    link_type: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_module: Mapped[str | None] = mapped_column(String(50))
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    source = relationship("Identity", foreign_keys=[source_id])
    dest = relationship("Identity", foreign_keys=[dest_id])

    __table_args__ = (
        Index("uq_identity_link", "workspace_id", "source_id", "dest_id", "link_type", unique=True),
    )
