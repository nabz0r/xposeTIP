"""Base SaaS Connector framework.

All SaaS connectors (Google, Microsoft, etc.) inherit from BaseConnector.
They use OAuth2 tokens stored in the accounts table to audit user data.
Each connector produces ScanResult findings like regular scanners.
"""
import logging
import uuid
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.account import Account
from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class BaseConnector(BaseScanner):
    """Base class for SaaS account connectors.

    Unlike regular scanners that take an email and query external APIs,
    connectors use stored OAuth tokens to audit the user's own accounts.
    """

    PROVIDER: str = ""  # "google", "microsoft", etc.
    REQUIRED_SCOPES: list[str] = []

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        """Main scan entry point. Loads tokens from account record."""
        account_id = kwargs.get("account_id")
        access_token = kwargs.get("access_token")

        if not access_token:
            logger.info("No access token for %s connector, skipping", self.PROVIDER)
            return []

        return await self.audit(email, access_token, **kwargs)

    @abstractmethod
    async def audit(self, email: str, access_token: str, **kwargs) -> list[ScanResult]:
        """Perform the actual audit using the OAuth access token."""
        raise NotImplementedError

    @abstractmethod
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Generate OAuth authorization URL."""
        raise NotImplementedError

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens.

        Returns: {"access_token": ..., "refresh_token": ..., "expires_in": ..., "scopes": [...]}
        """
        raise NotImplementedError

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token.

        Returns: {"access_token": ..., "expires_in": ...}
        """
        raise NotImplementedError

    def check_scopes(self, granted_scopes: list[str]) -> list[str]:
        """Check which required scopes are missing."""
        return [s for s in self.REQUIRED_SCOPES if s not in granted_scopes]
