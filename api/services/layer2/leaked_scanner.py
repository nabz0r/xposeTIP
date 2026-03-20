"""Leaked Domains scanner — xposedornot.com free breach check."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class LeakedScanner(BaseScanner):
    MODULE_ID = "leaked_domains"
    LAYER = 2
    CATEGORY = "breach"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        async with httpx.AsyncClient(timeout=20) as client:
            # XposedOrNot API
            try:
                resp = await client.get(
                    f"https://api.xposedornot.com/v1/check-email/{email}",
                    headers={"User-Agent": "xpose-tip"},
                )
                if resp.status_code == 404:
                    # Not found = not exposed
                    return []
                if resp.status_code == 429:
                    logger.warning("XposedOrNot rate limited")
                    return []
                if resp.status_code != 200:
                    logger.info("XposedOrNot returned %d for %s", resp.status_code, email)
                    return []

                data = resp.json()
            except Exception:
                logger.exception("XposedOrNot request failed for %s", email)
                return []

        # Parse response
        breaches_details = data.get("breaches_details") or data.get("ExposedBreaches", {})
        if isinstance(breaches_details, str):
            # Sometimes returns a string like "Not found"
            return []

        breaches = []
        if isinstance(breaches_details, dict):
            breaches = breaches_details.get("breaches_details", [])
            if not breaches:
                breaches = breaches_details.get("breaches", [])
        elif isinstance(breaches_details, list):
            breaches = breaches_details

        if not breaches:
            # Try alternate response format
            exposed = data.get("ExposedBreaches", {})
            if isinstance(exposed, dict):
                breaches = exposed.get("breaches_details", [])

        if not breaches:
            return []

        # Summary finding
        breach_names = []
        total_data_classes = set()
        for breach in breaches:
            name = breach.get("breach") or breach.get("name") or breach.get("domain", "Unknown")
            breach_names.append(name)
            data_classes = breach.get("data_classes") or breach.get("xposed_data") or ""
            if isinstance(data_classes, str):
                for dc in data_classes.split(","):
                    dc = dc.strip()
                    if dc:
                        total_data_classes.add(dc)
            elif isinstance(data_classes, list):
                total_data_classes.update(data_classes)

        severity = "medium"
        if len(breaches) >= 5:
            severity = "high"
        if len(breaches) >= 10:
            severity = "critical"
        if any(dc.lower() in ("passwords", "password", "hashed passwords") for dc in total_data_classes):
            severity = "high" if severity == "medium" else severity

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="breach",
            severity=severity,
            title=f"Found in {len(breaches)} breach databases",
            description=(
                f"Email found in {len(breaches)} breaches via XposedOrNot: "
                f"{', '.join(breach_names[:10])}"
                + (f" and {len(breach_names) - 10} more" if len(breach_names) > 10 else "")
                + f". Exposed data types: {', '.join(list(total_data_classes)[:15])}"
            ),
            data={
                "breach_count": len(breaches),
                "breach_names": breach_names,
                "data_classes": list(total_data_classes),
                "source": "xposedornot",
                "raw": breaches[:20],
            },
            indicator_value=email,
            indicator_type="email",
            verified=True,
        ))

        # Individual breach findings (top 10)
        for breach in breaches[:10]:
            name = breach.get("breach") or breach.get("name") or breach.get("domain", "Unknown")
            date = breach.get("xposed_date") or breach.get("date") or breach.get("added_date", "")
            data_classes = breach.get("data_classes") or breach.get("xposed_data") or ""
            records = breach.get("xposed_records") or breach.get("records") or ""
            industry = breach.get("industry", "")

            if isinstance(data_classes, str):
                data_classes_list = [dc.strip() for dc in data_classes.split(",") if dc.strip()]
            else:
                data_classes_list = data_classes if isinstance(data_classes, list) else []

            b_severity = "medium"
            if any(dc.lower() in ("passwords", "password", "hashed passwords", "credit cards", "ssn") for dc in data_classes_list):
                b_severity = "high"

            desc = f"Breach: {name}"
            if date:
                desc += f" (date: {date})"
            if records:
                desc += f". {records} records exposed"
            if data_classes_list:
                desc += f". Data: {', '.join(data_classes_list[:8])}"

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="breach",
                severity=b_severity,
                title=f"Breach: {name}",
                description=desc,
                data={
                    "breach_name": name,
                    "date": date,
                    "records": records,
                    "data_classes": data_classes_list,
                    "industry": industry,
                    "source": "xposedornot",
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        logger.info("Leaked Domains scan for %s: %d findings (%d breaches)", email, len(results), len(breaches))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.xposedornot.com/v1/check-email/test@example.com",
                    headers={"User-Agent": "xpose-tip"},
                )
                return resp.status_code in (200, 404)
        except Exception:
            return False
