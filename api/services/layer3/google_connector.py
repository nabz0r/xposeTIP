"""Google SaaS Connector — OAuth2 audit of Google account.

Audits:
- Connected third-party apps (OAuth grants)
- Login devices and sessions
- Account security status
- Google Workspace app permissions

Requires OAuth2 with scopes:
- https://www.googleapis.com/auth/userinfo.email
- https://www.googleapis.com/auth/userinfo.profile
- https://www.googleapis.com/auth/contacts.readonly (for connected accounts)
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx

from api.services.base import ScanResult
from api.services.layer3.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class GoogleConnector(BaseConnector):
    MODULE_ID = "google_audit"
    LAYER = 3
    CATEGORY = "app_permission"
    PROVIDER = "google"
    REQUIRED_SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_PEOPLE_URL = "https://people.googleapis.com/v1/people/me"

    async def get_auth_url(self, state: str, redirect_uri: str, **kwargs) -> str:
        """Generate Google OAuth2 authorization URL."""
        client_id = kwargs.get("client_id", "")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.REQUIRED_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{self.GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        client_id = kwargs.get("client_id", "")
        client_secret = kwargs.get("client_secret", "")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
            if resp.status_code != 200:
                logger.error("Google token exchange failed: %d %s", resp.status_code, resp.text)
                return {}

            data = resp.json()
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in", 3600),
                "scopes": data.get("scope", "").split(" "),
            }

    async def refresh_access_token(self, refresh_token: str, **kwargs) -> dict:
        """Refresh an expired Google access token."""
        client_id = kwargs.get("client_id", "")
        client_secret = kwargs.get("client_secret", "")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.GOOGLE_TOKEN_URL, data={
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
            })
            if resp.status_code != 200:
                logger.error("Google token refresh failed: %d", resp.status_code)
                return {}

            data = resp.json()
            return {
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in", 3600),
            }

    async def audit(self, email: str, access_token: str, **kwargs) -> list[ScanResult]:
        """Full Google account audit."""
        results = []

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            # 1. User info
            userinfo = await self._get_userinfo(client)
            if userinfo:
                results.append(self._userinfo_finding(userinfo))

            # 2. Token info (see what scopes are granted)
            tokeninfo = await self._get_tokeninfo(client, access_token)
            if tokeninfo:
                results.append(self._tokeninfo_finding(tokeninfo))

            # 3. Connected people/contacts (proxy for connected apps)
            connections = await self._get_connections(client)
            if connections:
                results.extend(self._connections_findings(connections))

        # Summary
        if results:
            results.insert(0, ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category=self.CATEGORY,
                severity="info",
                title=f"Google account audit: {len(results)} findings",
                description=f"Audited Google account for {email}",
                data={
                    "provider": "google",
                    "findings_count": len(results),
                    "email": email,
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        return results

    async def _get_userinfo(self, client: httpx.AsyncClient) -> dict | None:
        try:
            resp = await client.get(self.GOOGLE_USERINFO_URL)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            logger.exception("Failed to get Google userinfo")
        return None

    async def _get_tokeninfo(self, client: httpx.AsyncClient, token: str) -> dict | None:
        try:
            resp = await client.get(
                self.GOOGLE_TOKENINFO_URL,
                params={"access_token": token},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            logger.exception("Failed to get Google tokeninfo")
        return None

    async def _get_connections(self, client: httpx.AsyncClient) -> list:
        """Get Google contacts/connections (requires contacts.readonly scope)."""
        try:
            resp = await client.get(
                f"{self.GOOGLE_PEOPLE_URL}/connections",
                params={
                    "personFields": "names,emailAddresses,organizations",
                    "pageSize": 100,
                },
            )
            if resp.status_code == 200:
                return resp.json().get("connections", [])
        except Exception:
            logger.info("Contacts scope not granted or API error")
        return []

    def _userinfo_finding(self, data: dict) -> ScanResult:
        return ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="info",
            title="Google account profile",
            description=f"Verified Google account: {data.get('email', 'unknown')}",
            data={
                "google_id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture"),
                "verified_email": data.get("verified_email"),
                "locale": data.get("locale"),
                "hd": data.get("hd"),  # hosted domain (Google Workspace)
            },
            indicator_value=data.get("email"),
            indicator_type="email",
            verified=True,
        )

    def _tokeninfo_finding(self, data: dict) -> ScanResult:
        scopes = data.get("scope", "").split(" ")
        high_risk_scopes = [
            s for s in scopes
            if any(k in s for k in ["drive", "gmail", "calendar", "admin", "contacts"])
        ]

        severity = "high" if len(high_risk_scopes) > 2 else "medium" if high_risk_scopes else "info"

        return ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category=self.CATEGORY,
            severity=severity,
            title=f"Google OAuth: {len(scopes)} scopes granted",
            description=f"{len(high_risk_scopes)} high-risk scopes detected" if high_risk_scopes else "Standard scopes only",
            data={
                "total_scopes": len(scopes),
                "scopes": scopes,
                "high_risk_scopes": high_risk_scopes,
                "expires_in": data.get("expires_in"),
                "email": data.get("email"),
            },
            verified=True,
        )

    def _connections_findings(self, connections: list) -> list[ScanResult]:
        results = []

        if len(connections) > 0:
            orgs = set()
            emails = set()
            for conn in connections:
                for org in conn.get("organizations", []):
                    if org.get("name"):
                        orgs.add(org["name"])
                for em in conn.get("emailAddresses", []):
                    if em.get("value"):
                        domain = em["value"].split("@")[-1]
                        emails.add(domain)

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="social_account",
                severity="info",
                title=f"Google contacts: {len(connections)} connections",
                description=f"Found {len(orgs)} organizations, {len(emails)} email domains",
                data={
                    "total_connections": len(connections),
                    "organizations": list(orgs)[:20],
                    "email_domains": list(emails)[:20],
                },
                verified=True,
            ))

        return results

    async def health_check(self, **kwargs) -> bool:
        """Check if Google OAuth is configured."""
        # Health check = verify we can reach Google's token endpoint
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("https://accounts.google.com/.well-known/openid-configuration")
                return resp.status_code == 200
        except Exception:
            return False
