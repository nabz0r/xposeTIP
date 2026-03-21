import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base, TimestampMixin, UUIDMixin


class Scraper(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scrapers"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Request config
    url_template: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10), default="GET")
    headers: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    cookies: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    body_template: Mapped[str | None] = mapped_column(Text)

    # Input mapping
    input_type: Mapped[str] = mapped_column(String(50))
    input_transform: Mapped[str | None] = mapped_column(String(200))

    # Extraction rules (editable regex/jsonpath patterns)
    extraction_rules: Mapped[list] = mapped_column(JSONB, default=list)

    # Output mapping
    finding_title_template: Mapped[str | None] = mapped_column(String(500))
    finding_category: Mapped[str | None] = mapped_column(String(50))
    finding_severity: Mapped[str | None] = mapped_column(String(20))
    identity_type: Mapped[str | None] = mapped_column(String(50))

    # Rate limiting
    rate_limit_requests: Mapped[int] = mapped_column(Integer, default=1)
    rate_limit_window: Mapped[int] = mapped_column(Integer, default=2)

    # Validation
    success_indicator: Mapped[str | None] = mapped_column(String(200))
    not_found_indicators: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Auth
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Test status
    last_tested: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_test_status: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    # Workspace scope
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "url_template": self.url_template,
            "method": self.method,
            "headers": self.headers,
            "cookies": self.cookies,
            "body_template": self.body_template,
            "input_type": self.input_type,
            "input_transform": self.input_transform,
            "extraction_rules": self.extraction_rules,
            "finding_title_template": self.finding_title_template,
            "finding_category": self.finding_category,
            "finding_severity": self.finding_severity,
            "identity_type": self.identity_type,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window": self.rate_limit_window,
            "success_indicator": self.success_indicator,
            "not_found_indicators": self.not_found_indicators,
            "requires_auth": self.requires_auth,
            "last_tested": self.last_tested.isoformat() if self.last_tested else None,
            "last_test_status": self.last_test_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
