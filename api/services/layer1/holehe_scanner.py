import asyncio
import httpx

from api.services.base import BaseScanner, ScanResult

MAJOR_SITES = {"google", "facebook", "twitter", "instagram", "linkedin", "github", "microsoft", "apple", "amazon", "spotify"}


class HoleheScanner(BaseScanner):
    MODULE_ID = "holehe"
    LAYER = 1
    CATEGORY = "social"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        try:
            from holehe.modules import import_submodules
            from holehe.core import is_email

            if not is_email(email):
                return []

            modules = import_submodules("holehe.modules")
            client = httpx.AsyncClient(timeout=10)
            out = []

            try:
                for module_name, module in modules.items():
                    for func_name in dir(module):
                        func = getattr(module, func_name)
                        if callable(func) and hasattr(func, '__name__') and not func_name.startswith('_'):
                            try:
                                await func(email, client, out)
                                await asyncio.sleep(1)  # Rate limit: 1 req/sec
                            except Exception:
                                continue
            finally:
                await client.aclose()

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
        except ImportError:
            pass  # holehe not installed
        except Exception:
            pass

        return results

    async def health_check(self) -> bool:
        try:
            from holehe.modules import import_submodules
            return True
        except Exception:
            return False
