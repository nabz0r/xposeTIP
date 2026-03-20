import asyncio
import logging
import os

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

HIBP_BASE = "https://haveibeenpwned.com/api/v3"
PASSWORD_DATA_CLASSES = {"Passwords", "Password hints", "Plaintext Passwords"}


class HIBPScanner(BaseScanner):
    MODULE_ID = "hibp"
    LAYER = 1
    CATEGORY = "breach"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key") or os.environ.get("HIBP_API_KEY", "")
        if not api_key:
            logger.warning("HIBP_API_KEY not set — returning info finding")
            return [ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="info",
                title="HIBP API key not configured",
                description="Configure your HaveIBeenPwned API key in Settings to enable breach checking",
                data={"reason": "missing_api_key"},
                indicator_value=email,
                indicator_type="email",
            )]

        results = []
        headers = {
            "hibp-api-key": api_key,
            "user-agent": "xpose-tip",
        }

        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            # --- Breaches ---
            try:
                resp = await client.get(
                    f"{HIBP_BASE}/breachedaccount/{email}",
                    params={"truncateResponse": "false"},
                )
                if resp.status_code == 200:
                    breaches = resp.json()
                    for breach in breaches:
                        name = breach.get("Name", "Unknown")
                        date = breach.get("BreachDate", "unknown date")
                        desc = breach.get("Description", "")[:500]
                        data_classes = set(breach.get("DataClasses", []))
                        has_passwords = bool(data_classes & PASSWORD_DATA_CLASSES)
                        severity = "high" if has_passwords else "medium"

                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="breach",
                            severity=severity,
                            title=f"Found in {name} breach ({date})",
                            description=f"{name}: {desc}",
                            data=breach,
                            url=f"https://haveibeenpwned.com/PwnedWebsites#{name}",
                            indicator_value=email,
                            indicator_type="email",
                            verified=breach.get("IsVerified", False),
                        ))
                    logger.info("HIBP found %d breaches for %s", len(breaches), email)
                elif resp.status_code == 404:
                    logger.info("HIBP: no breaches found for %s", email)
                else:
                    logger.warning("HIBP breaches API returned %d for %s", resp.status_code, email)
            except Exception:
                logger.exception("HIBP breach check failed for %s", email)

            # Rate limit between calls
            await asyncio.sleep(1.6)

            # --- Pastes ---
            try:
                resp = await client.get(f"{HIBP_BASE}/pasteaccount/{email}")
                if resp.status_code == 200:
                    pastes = resp.json()
                    for paste in pastes:
                        source = paste.get("Source", "Unknown")
                        date = paste.get("Date", "unknown date")
                        if date and "T" in str(date):
                            date = str(date).split("T")[0]

                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="paste",
                            severity="medium",
                            title=f"Email found in paste: {source} ({date})",
                            description=f"Email appeared in a paste on {source} with {paste.get('EmailCount', '?')} emails",
                            data=paste,
                            indicator_value=email,
                            indicator_type="email",
                            verified=True,
                        ))
                    logger.info("HIBP found %d pastes for %s", len(pastes), email)
                elif resp.status_code == 404:
                    logger.info("HIBP: no pastes found for %s", email)
                else:
                    logger.warning("HIBP pastes API returned %d for %s", resp.status_code, email)
            except Exception:
                logger.exception("HIBP paste check failed for %s", email)

        return results

    async def health_check(self, **kwargs) -> bool:
        api_key = kwargs.get("api_key") or os.environ.get("HIBP_API_KEY", "")
        return bool(api_key)
