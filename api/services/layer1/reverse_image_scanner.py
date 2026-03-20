"""Reverse Image Search scanner — PimEyes API integration.

Searches for face matches across the web using a profile photo URL.
Requires PIMEYES_API_KEY. Falls back to TinEye free reverse image search.
"""
import hashlib
import logging
from typing import Optional

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class ReverseImageScanner(BaseScanner):
    MODULE_ID = "reverse_image"
    LAYER = 1
    CATEGORY = "metadata"
    SUPPORTED_REGIONS = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        api_key = kwargs.get("api_key")
        photo_url = kwargs.get("photo_url")

        if not photo_url:
            # Try to get photo URL from existing findings (gravatar, github, etc.)
            photo_url = kwargs.get("avatar_url")

        if not photo_url:
            logger.info("No photo URL provided for reverse image search")
            return results

        # PimEyes API (if key available)
        if api_key:
            pimeyes_results = await self._search_pimeyes(photo_url, api_key)
            results.extend(pimeyes_results)

        # TinEye reverse search (free, no API key)
        tineye_results = await self._search_tineye(photo_url)
        results.extend(tineye_results)

        # Summary finding
        if results:
            results.insert(0, ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category=self.CATEGORY,
                severity="medium" if len(results) > 3 else "low",
                title=f"Reverse image: {len(results)} matches found",
                description=f"Profile photo appears on {len(results)} locations across the web",
                data={
                    "photo_url": photo_url,
                    "total_matches": len(results),
                    "sources": ["pimeyes"] if api_key else [] + ["tineye"],
                },
                indicator_value=photo_url,
                indicator_type="photo_url",
                verified=True,
            ))

        return results

    async def _search_pimeyes(self, photo_url: str, api_key: str) -> list[ScanResult]:
        """Search PimEyes API for face matches."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # PimEyes search endpoint
                resp = await client.post(
                    "https://pimeyes.com/api/search/new",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "image": photo_url,
                        "search_type": "SEARCH_BY_FACE",
                    },
                )
                if resp.status_code != 200:
                    logger.warning("PimEyes API returned %d", resp.status_code)
                    return results

                data = resp.json()
                search_id = data.get("search_id")
                if not search_id:
                    return results

                # Fetch results
                resp2 = await client.get(
                    f"https://pimeyes.com/api/search/results/{search_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp2.status_code != 200:
                    return results

                matches = resp2.json().get("results", [])
                for match in matches[:20]:  # Cap at 20 results
                    site_url = match.get("url", "")
                    thumbnail = match.get("thumbnail_url", "")
                    score = match.get("score", 0)

                    severity = "high" if score > 0.9 else "medium" if score > 0.7 else "low"

                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category=self.CATEGORY,
                        severity=severity,
                        title=f"Face match on {self._extract_domain(site_url)}",
                        description=f"Profile photo matched with {score:.0%} confidence",
                        data={
                            "source": "pimeyes",
                            "match_url": site_url,
                            "thumbnail_url": thumbnail,
                            "confidence_score": score,
                            "domain": self._extract_domain(site_url),
                        },
                        url=site_url,
                        indicator_value=site_url,
                        indicator_type="url",
                        verified=score > 0.85,
                    ))

        except httpx.TimeoutException:
            logger.warning("PimEyes API timeout")
        except Exception:
            logger.exception("PimEyes search failed")

        return results

    async def _search_tineye(self, photo_url: str) -> list[ScanResult]:
        """Search TinEye for reverse image matches (free)."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    "https://tineye.com/api/v1/result_json/",
                    params={"url": photo_url, "sort": "score", "order": "desc"},
                    headers={"User-Agent": "xpose/0.6.0"},
                )
                if resp.status_code != 200:
                    logger.info("TinEye returned %d (may need different approach)", resp.status_code)
                    return results

                data = resp.json()
                matches = data.get("matches", [])

                for match in matches[:10]:
                    domain = match.get("domain", "unknown")
                    backlinks = match.get("backlinks", [])

                    for bl in backlinks[:3]:
                        url = bl.get("url", "")
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category=self.CATEGORY,
                            severity="low",
                            title=f"Image found on {domain}",
                            description=f"Profile photo indexed on {domain}",
                            data={
                                "source": "tineye",
                                "domain": domain,
                                "backlink_url": url,
                                "crawl_date": bl.get("crawl_date", ""),
                            },
                            url=url,
                            indicator_value=url,
                            indicator_type="url",
                            verified=False,
                        ))

        except httpx.TimeoutException:
            logger.info("TinEye timeout")
        except Exception:
            logger.exception("TinEye search failed")

        return results

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc or url
        except Exception:
            return url

    async def health_check(self, **kwargs) -> bool:
        api_key = kwargs.get("api_key")
        if not api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://pimeyes.com/api/search/status",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False
