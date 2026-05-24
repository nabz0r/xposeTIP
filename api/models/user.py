import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    auth_provider: Mapped[str] = mapped_column(String(20), default="local")
    auth_provider_id: Mapped[str | None] = mapped_column(String(255))
    mfa_secret: Mapped[str | None] = mapped_column(Text)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # S195 Bug 5 fix: persist user's most recent workspace selection so
    # /auth/refresh and /auth/login don't silently revert to the first-
    # inserted membership. Updated by /switch-workspace; read by /login
    # and /refresh. NULL = fallback to current `.limit(1)` behavior.
    # ondelete=SET NULL handled at DB level via migration 025.
    last_active_workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )

    owned_workspaces = relationship("Workspace", back_populates="owner", foreign_keys="Workspace.owner_id")
    user_workspaces = relationship("UserWorkspace", back_populates="user", cascade="all, delete-orphan")


class UserWorkspace(Base):
    __tablename__ = "user_workspaces"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    user = relationship("User", back_populates="user_workspaces")
    workspace = relationship("Workspace", back_populates="user_workspaces")
