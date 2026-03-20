from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    layer: Mapped[int] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_config: Mapped[dict | None] = mapped_column(JSONB)
    rate_limit: Mapped[dict | None] = mapped_column(JSONB)
    supported_regions: Mapped[dict | None] = mapped_column(JSONB)
    version: Mapped[str | None] = mapped_column(String(20))
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_health: Mapped[datetime | None] = mapped_column()
