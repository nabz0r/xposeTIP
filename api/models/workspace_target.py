"""Many-to-many association: share targets across workspaces.

The primary ownership remains via targets.workspace_id (the "home" workspace).
This table allows targets to be *shared* into additional workspaces for
cross-workspace visibility (e.g. consultants sharing targets across clients).
"""
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


class WorkspaceTarget(Base):
    __tablename__ = "workspace_targets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), primary_key=True
    )
    added_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20), default="viewer")  # viewer|editor
    added_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
