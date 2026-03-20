import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin, UUIDMixin


class Workspace(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    settings: Mapped[dict | None] = mapped_column(JSONB, default={})

    owner = relationship("User", back_populates="owned_workspaces", foreign_keys=[owner_id])
    user_workspaces = relationship("UserWorkspace", back_populates="workspace", cascade="all, delete-orphan")
    targets = relationship("Target", back_populates="workspace", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="workspace", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="workspace", cascade="all, delete-orphan")
