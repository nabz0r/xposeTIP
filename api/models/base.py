import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TZDateTime = TIMESTAMP(timezone=True)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(TZDateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(TZDateTime, default=func.now(), onupdate=func.now())


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
