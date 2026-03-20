import json
import logging
import os
import subprocess
import tempfile
import uuid

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class SherlockScanner(BaseScanner):
    MODULE_ID = "sherlock"
    LAYER = 1
    CATEGORY = "social"
    SUPPORTED_REGIONS = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        # Extract username from email
        username = email.split("@")[0].lower() if "@" in email else email
        if not username:
            return []

        output_path = os.path.join(tempfile.gettempdir(), f"sherlock_{uuid.uuid4().hex}.json")

        try:
            proc = subprocess.run(
                ["sherlock", username, "--print-found", "--json", output_path, "--timeout", "10"],
                capture_output=True,
                text=True,
                timeout=90,
            )
            logger.info("Sherlock exited with code %d for username '%s'", proc.returncode, username)

            if not os.path.exists(output_path):
                logger.warning("Sherlock output file not found: %s", output_path)
                return []

            with open(output_path) as f:
                data = json.load(f)

            for site_name, info in data.items():
                url_user = info.get("url_user", "")
                if info.get("status", "").lower() not in ("claimed",):
                    continue

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity="low",
                    title=f"Username '{username}' found on {site_name}",
                    description=f"Profile exists at {url_user}",
                    data={"site": site_name, "url": url_user, "username": username, **info},
                    url=url_user,
                    indicator_value=username,
                    indicator_type="username",
                    verified=False,
                ))

            logger.info("Sherlock found %d profiles for '%s'", len(results), username)

        except FileNotFoundError:
            logger.warning("Sherlock CLI not installed — skipping username enumeration")
        except subprocess.TimeoutExpired:
            logger.warning("Sherlock timed out for '%s'", username)
        except Exception:
            logger.exception("Sherlock scan failed for '%s'", username)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

        return results

    async def health_check(self) -> bool:
        try:
            proc = subprocess.run(["sherlock", "--version"], capture_output=True, timeout=5)
            return proc.returncode == 0
        except Exception:
            return False
