import asyncio
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

MAJOR_SITES = {"google", "facebook", "twitter", "instagram", "linkedin", "github", "microsoft", "apple", "amazon", "spotify"}


class HoleheScanner(BaseScanner):
    MODULE_ID = "holehe"
    LAYER = 1
    CATEGORY = "social"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        try:
            from holehe.core import import_submodules, get_functions, is_email
        except ImportError:
            logger.error("holehe package not installed")
            return []

        if not is_email(email):
            logger.warning("Invalid email format: %s", email)
            return []

        try:
            modules = import_submodules("holehe.modules")
            funcs = get_functions(modules)
            logger.info("Loaded %d holehe modules for %s", len(funcs), email)
        except Exception:
            logger.exception("Failed to load holehe modules")
            return []

        out = []
        async with httpx.AsyncClient(timeout=15) as client:
            for func in funcs:
                try:
                    await func(email, client, out)
                    await asyncio.sleep(1)  # Rate limit: 1 req/sec
                except Exception:
                    logger.warning("holehe module %s failed", func.__name__, exc_info=True)

        for entry in out:
            if entry.get("exists") is True:
                site_name = entry.get("name", "unknown").lower()
                severity = "medium" if site_name in MAJOR_SITES else "low"
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity=severity,
                    title=f"Account found on {entry.get('name', 'Unknown')}",
                    description=f"Email {email} is registered on {entry.get('name', 'Unknown')}",
                    data=entry,
                    url=entry.get("emailrecovery") or entry.get("url"),
                    indicator_value=email,
                    indicator_type="email",
                    verified=True,
                ))
            elif entry.get("rateLimit") is True:
                logger.debug("Rate-limited on %s", entry.get("name", "unknown"))

        logger.info("holehe scan complete for %s: %d accounts found out of %d checks", email, len(results), len(out))
        return results

    async def health_check(self) -> bool:
        try:
            from holehe.core import import_submodules, get_functions
            modules = import_submodules("holehe.modules")
            funcs = get_functions(modules)
            return len(funcs) > 0
        except Exception:
            logger.exception("holehe health check failed")
            return False
