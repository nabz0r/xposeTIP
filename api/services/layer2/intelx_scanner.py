"""Intelligence X scanner — darkweb, paste, breach, document search."""
import asyncio
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

INTELX_BASE = "https://2.intelx.io"


class IntelXScanner(BaseScanner):
    MODULE_ID = "intelx"
    LAYER = 2
    CATEGORY = "breach"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.info("IntelX scan skipped — no API key")
            return []

        results = []
        headers = {"x-key": api_key, "User-Agent": "xpose-tip"}

        async with httpx.AsyncClient(timeout=30) as client:
            # Start search
            try:
                resp = await client.post(
                    f"{INTELX_BASE}/intelligent/search",
                    headers=headers,
                    json={
                        "term": email,
                        "maxresults": 20,
                        "media": 0,
                        "timeout": 10,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("IntelX search failed: %d", resp.status_code)
                    return []

                search_data = resp.json()
                search_id = search_data.get("id")
                if not search_id:
                    return []

            except Exception:
                logger.exception("IntelX search initiation failed for %s", email)
                return []

            # Wait briefly for results
            await asyncio.sleep(3)

            # Fetch results
            try:
                resp = await client.get(
                    f"{INTELX_BASE}/intelligent/search/result",
                    headers=headers,
                    params={"id": search_id, "limit": 20},
                )
                if resp.status_code != 200:
                    return []

                result_data = resp.json()
                records = result_data.get("records", [])

            except Exception:
                logger.exception("IntelX result fetch failed for %s", email)
                return []

            # Media type mapping
            media_types = {
                0: "paste/text",
                1: "paste site",
                2: "darkweb",
                3: "document",
                4: "social media",
                5: "forum",
                24: "data leak",
            }

            source_severity = {
                "darkweb": "high",
                "data leak": "critical",
                "paste site": "medium",
                "paste/text": "medium",
                "document": "low",
                "social media": "low",
                "forum": "low",
            }

            for record in records:
                name = record.get("name", "Unknown source")
                media = record.get("media", 0)
                source_type = media_types.get(media, "unknown")
                date = record.get("date", "")
                bucket = record.get("bucket", "")
                system_id = record.get("systemid", "")

                severity = source_severity.get(source_type, "medium")

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="breach",
                    severity=severity,
                    title=f"IntelX: {name[:100]}",
                    description=f"Email found in {source_type}: {name[:200]}. Date: {date[:10] if date else 'Unknown'}",
                    data={
                        "source_name": name,
                        "source_type": source_type,
                        "media_type": media,
                        "date": date,
                        "bucket": bucket,
                        "system_id": system_id,
                    },
                    indicator_value=email,
                    indicator_type="email",
                    verified=True,
                ))

        logger.info("IntelX scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
