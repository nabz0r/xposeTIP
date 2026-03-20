"""Epieos scanner — Google ID, name, photo discovery from email."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class EpieosScanner(BaseScanner):
    MODULE_ID = "epieos"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        async with httpx.AsyncClient(timeout=15) as client:
            # Epieos Google endpoint
            try:
                resp = await client.get(
                    f"https://api.epieos.com/v1/google?email={email}",
                    headers={"User-Agent": "xpose-tip"},
                )
                if resp.status_code == 429:
                    logger.warning("Epieos rate limited for %s", email)
                    return []
                if resp.status_code != 200:
                    logger.info("Epieos returned %d for %s", resp.status_code, email)
                    return []

                data = resp.json()
            except Exception:
                logger.exception("Epieos request failed for %s", email)
                return []

        # Check if we got useful data
        google_id = data.get("id") or data.get("google_id")
        name = data.get("name") or data.get("full_name")
        photo_url = data.get("photo") or data.get("picture") or data.get("avatar_url")
        last_edit = data.get("last_edit") or data.get("last_updated")

        if not google_id and not name and not photo_url:
            # Try alternate response structure
            account = data.get("account") or data.get("data") or {}
            if isinstance(account, dict):
                google_id = account.get("id") or account.get("google_id")
                name = account.get("name") or account.get("full_name")
                photo_url = account.get("photo") or account.get("picture")
                last_edit = account.get("last_edit")

        if not google_id and not name and not photo_url:
            return []

        # Main Google profile finding
        desc_parts = []
        if google_id:
            desc_parts.append(f"Google ID: {google_id}")
        if name:
            desc_parts.append(f"Name: {name}")
        if last_edit:
            desc_parts.append(f"Profile last edited: {last_edit}")

        finding_data = {
            "google_id": google_id,
            "name": name,
            "photo_url": photo_url,
            "last_edit": last_edit,
            "source": "epieos",
            "raw": data,
        }

        title = "Google account discovered"
        if name:
            title = f"Google account: {name}"

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="medium",
            title=title,
            description=". ".join(desc_parts) if desc_parts else "Google account linked to this email",
            data=finding_data,
            url=f"https://maps.google.com/maps/contrib/{google_id}" if google_id else None,
            indicator_value=email,
            indicator_type="email",
            verified=True,
        ))

        # Photo finding (separate — useful for profile aggregation)
        if photo_url:
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="info",
                title="Google profile photo found",
                description=f"Public profile photo discovered for this Google account" + (f" ({name})" if name else ""),
                data={"photo_url": photo_url, "google_id": google_id, "source": "epieos"},
                url=photo_url,
                indicator_value=photo_url,
                indicator_type="social_url",
                verified=True,
            ))

        logger.info("Epieos scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.epieos.com/v1/google?email=test@gmail.com",
                    headers={"User-Agent": "xpose-tip"},
                )
                return resp.status_code in (200, 404, 429)
        except Exception:
            return False
