import asyncio
import logging
import re

from api.services.base import BaseScanner, ScanResult
from api.services.scraper_engine import ScraperEngine

logger = logging.getLogger(__name__)


class ScraperScanner(BaseScanner):
    """
    Meta-scanner that executes all enabled scraper definitions from DB.
    Replaces individual scanner files for simple scraping tasks.
    """

    MODULE_ID = "scraper_engine"
    LAYER = 1
    CATEGORY = "social"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        # Import here to avoid circular deps
        from api.tasks.utils import get_sync_session
        from api.models.scraper import Scraper
        from sqlalchemy import select

        session = get_sync_session()
        try:
            scrapers = session.execute(
                select(Scraper).where(
                    Scraper.enabled == True,
                    Scraper.input_type.in_(["email", "username", "domain", "first_name"]),
                )
            ).scalars().all()

            if not scrapers:
                return results

            engine = ScraperEngine()
            username = email.split("@")[0]
            domain = email.split("@")[-1] if "@" in email else email
            cleaned_prefix = re.sub(r"\d+", "", username)
            name_parts = re.split(r"[._]", cleaned_prefix)
            first_name = name_parts[0].lower() if name_parts else username
            inputs = {"email": email, "username": username, "domain": domain, "first_name": first_name}

            # Write scraper progress to Redis
            scan_id = kwargs.get("scan_id")
            redis_client = None
            if scan_id:
                try:
                    import redis as r
                    from api.config import settings
                    import json as _json
                    redis_client = r.from_url(settings.REDIS_URL)
                except Exception:
                    pass

            total_scrapers = len(scrapers)
            for idx, scraper in enumerate(scrapers):
                input_value = inputs.get(scraper.input_type, email)

                # Update Redis progress
                if redis_client and scan_id:
                    try:
                        redis_client.setex(
                            f"scan:{scan_id}:scraper_progress",
                            300,
                            _json.dumps({"current": idx + 1, "total": total_scrapers, "current_name": scraper.display_name or scraper.name}),
                        )
                    except Exception:
                        pass

                try:
                    result = await engine.execute(scraper.to_dict(), input_value)
                except Exception:
                    logger.debug("Scraper %s failed", scraper.name)
                    continue

                if not result.get("found"):
                    continue

                extracted = result.get("extracted", {})

                # Build finding title from template
                try:
                    title = (scraper.finding_title_template or "{service}: profile found").format(
                        service=scraper.display_name or scraper.name,
                        **{k: v for k, v in extracted.items() if v is not None},
                    )
                except (KeyError, IndexError):
                    title = f"{scraper.display_name or scraper.name}: profile found"

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category=scraper.finding_category or "social_account",
                    severity=scraper.finding_severity or "low",
                    title=title,
                    description=f"Data extracted from {scraper.display_name or scraper.name}",
                    url=result.get("url"),
                    data={
                        "scraper": scraper.name,
                        "platform": scraper.name.replace("_profile", "").replace("_scraper", ""),
                        "extracted": extracted,
                        "status_code": result.get("status_code"),
                    },
                    indicator_value=extracted.get("display_name") or extracted.get("username"),
                    indicator_type=scraper.identity_type or "username",
                ))

                # Wait between scrapers to respect rate limits
                await asyncio.sleep(scraper.rate_limit_window / max(scraper.rate_limit_requests, 1))

            await engine.close()

        except Exception:
            logger.exception("ScraperScanner failed")
        finally:
            session.close()

        return results

    async def health_check(self) -> bool:
        return True
