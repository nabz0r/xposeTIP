from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from api.models.base import Base


class NameBlacklist(Base):
    __tablename__ = "name_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern: Mapped[str] = mapped_column(String(500), unique=True)
    type: Mapped[str] = mapped_column(String(20), default="exact")  # exact, contains, regex
    reason: Mapped[str | None] = mapped_column(String(200))
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
