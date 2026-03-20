import asyncio
import logging
import os

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

HIBP_BASE = "https://haveibeenpwned.com/api/v3"
PASSWORD_DATA_CLASSES = {"Passwords", "Password hints", "Plaintext Passwords"}
FINANCIAL_DATA_CLASSES = {
    "Credit cards", "Bank account numbers", "Credit card CVV",
    "Credit status information", "Financial investments", "Financial transactions",
    "Partial credit card data", "Payment histories", "Payment methods",
}
PII_DATA_CLASSES = {
    "Social security numbers", "Government issued IDs", "Passport numbers",
    "National IDs", "Tax file numbers", "Driver's licenses",
    "Physical addresses", "Dates of birth",
}
HEALTH_DATA_CLASSES = {
    "Health insurance information", "Medical conditions",
    "Medical records", "Medical treatments",
}


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
                        data_classes = set(breach.get("DataClasses", []))
                        pwned_count = breach.get("PwnedCount", 0)
                        is_verified = breach.get("IsVerified", False)
                        is_sensitive = breach.get("IsSensitive", False)

                        # Severity based on exposed data types
                        has_passwords = bool(data_classes & PASSWORD_DATA_CLASSES)
                        has_financial = bool(data_classes & FINANCIAL_DATA_CLASSES)
                        has_pii = bool(data_classes & PII_DATA_CLASSES)
                        has_health = bool(data_classes & HEALTH_DATA_CLASSES)

                        if has_passwords and (has_financial or has_pii):
                            severity = "critical"
                        elif has_passwords or has_financial or has_pii or has_health:
                            severity = "high"
                        elif is_sensitive:
                            severity = "high"
                        elif len(data_classes) >= 3:
                            severity = "medium"
                        else:
                            severity = "low"

                        # Rich description
                        desc_parts = [f"Breach date: {date}"]
                        if pwned_count:
                            desc_parts.append(f"{pwned_count:,} accounts affected")
                        if data_classes:
                            desc_parts.append(f"Exposed: {', '.join(sorted(data_classes))}")
                        if is_sensitive:
                            desc_parts.append("⚠ Sensitive breach")
                        description = ". ".join(desc_parts)

                        # Enrich data payload
                        breach["_severity_reason"] = {
                            "has_passwords": has_passwords,
                            "has_financial": has_financial,
                            "has_pii": has_pii,
                            "has_health": has_health,
                            "data_class_count": len(data_classes),
                        }

                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="breach",
                            severity=severity,
                            title=f"Found in {name} breach ({date})",
                            description=description,
                            data=breach,
                            url=f"https://haveibeenpwned.com/PwnedWebsites#{name}",
                            indicator_value=email,
                            indicator_type="email",
                            verified=is_verified,
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
