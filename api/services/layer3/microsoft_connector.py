"""Microsoft SaaS Connector — OAuth2 audit of Microsoft account.

Placeholder for Phase 2. Will audit:
- Connected third-party apps
- Azure AD app registrations
- Sign-in activity
- Device list
- OneDrive sharing settings

Requires OAuth2 with Microsoft Graph API scopes.
"""
import logging
from urllib.parse import urlencode

import httpx

from api.services.base import ScanResult
from api.services.layer3.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class MicrosoftConnector(BaseConnector):
    MODULE_ID = "microsoft_audit"
    LAYER = 3
    CATEGORY = "app_permission"
    PROVIDER = "microsoft"
    REQUIRED_SCOPES = [
        "User.Read",
        "Application.Read.All",
    ]

    MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    MS_GRAPH_URL = "https://graph.microsoft.com/v1.0"

    async def get_auth_url(self, state: str, redirect_uri: str, **kwargs) -> str:
        client_id = kwargs.get("client_id", "")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.REQUIRED_SCOPES),
            "state": state,
        }
        return f"{self.MS_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        client_id = kwargs.get("client_id", "")
        client_secret = kwargs.get("client_secret", "")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.MS_TOKEN_URL, data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
            if resp.status_code != 200:
                logger.error("Microsoft token exchange failed: %d", resp.status_code)
                return {}

            data = resp.json()
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in", 3600),
                "scopes": data.get("scope", "").split(" "),
            }

    async def refresh_access_token(self, refresh_token: str, **kwargs) -> dict:
        client_id = kwargs.get("client_id", "")
        client_secret = kwargs.get("client_secret", "")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.MS_TOKEN_URL, data={
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
            })
            if resp.status_code != 200:
                return {}

            data = resp.json()
            return {
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in", 3600),
            }

    async def audit(self, email: str, access_token: str, **kwargs) -> list[ScanResult]:
        """Microsoft account audit — placeholder implementation."""
        results = []
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            # 1. User profile
            profile = await self._get_profile(client)
            if profile:
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="metadata",
                    severity="info",
                    title="Microsoft account profile",
                    description=f"Verified Microsoft account: {profile.get('mail', profile.get('userPrincipalName', 'unknown'))}",
                    data={
                        "display_name": profile.get("displayName"),
                        "mail": profile.get("mail"),
                        "upn": profile.get("userPrincipalName"),
                        "job_title": profile.get("jobTitle"),
                        "office_location": profile.get("officeLocation"),
                        "mobile_phone": profile.get("mobilePhone"),
                    },
                    indicator_value=profile.get("mail") or profile.get("userPrincipalName"),
                    indicator_type="email",
                    verified=True,
                ))

            # 2. OAuth app permissions (if scope allows)
            apps = await self._get_oauth_apps(client)
            if apps:
                for app in apps[:15]:
                    app_name = app.get("appDisplayName", "Unknown")
                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category=self.CATEGORY,
                        severity="medium",
                        title=f"Microsoft OAuth app: {app_name}",
                        description=f"Third-party app '{app_name}' has access to your Microsoft account",
                        data={
                            "app_id": app.get("appId"),
                            "app_name": app_name,
                            "consent_type": app.get("consentType"),
                            "principal_id": app.get("principalId"),
                        },
                        verified=True,
                    ))

        if results:
            results.insert(0, ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category=self.CATEGORY,
                severity="info",
                title=f"Microsoft account audit: {len(results)} findings",
                description=f"Audited Microsoft account for {email}",
                data={"provider": "microsoft", "findings_count": len(results)},
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        return results

    async def _get_profile(self, client: httpx.AsyncClient) -> dict | None:
        try:
            resp = await client.get(f"{self.MS_GRAPH_URL}/me")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            logger.exception("Failed to get Microsoft profile")
        return None

    async def _get_oauth_apps(self, client: httpx.AsyncClient) -> list:
        try:
            resp = await client.get(f"{self.MS_GRAPH_URL}/me/oauth2PermissionGrants")
            if resp.status_code == 200:
                return resp.json().get("value", [])
        except Exception:
            logger.info("OAuth apps scope not granted")
        return []

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration")
                return resp.status_code == 200
        except Exception:
            return False
