import hashlib
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class GravatarScanner(BaseScanner):
    MODULE_ID = "gravatar"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
        results = []

        async with httpx.AsyncClient(timeout=10) as client:
            # Check profile JSON
            profile_data = None
            try:
                resp = await client.get(f"https://en.gravatar.com/{email_hash}.json")
                if resp.status_code == 200:
                    profile_data = resp.json()
            except Exception:
                logger.debug("Gravatar profile fetch failed for %s", email)

            # Check avatar
            avatar_url = None
            try:
                resp = await client.head(
                    f"https://www.gravatar.com/avatar/{email_hash}?s=200&d=404"
                )
                if resp.status_code == 200:
                    avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s=200"
            except Exception:
                pass

            if not profile_data and not avatar_url:
                return []

            # Parse profile
            entry = {}
            if profile_data and profile_data.get("entry"):
                entry = profile_data["entry"][0]

            display_name = entry.get("displayName", "")
            username = entry.get("preferredUsername", "")
            about = entry.get("aboutMe", "")
            location = entry.get("currentLocation", "")
            photos = entry.get("photos", [])
            urls = entry.get("urls", [])
            accounts = entry.get("accounts", [])

            if not avatar_url and photos:
                avatar_url = photos[0].get("value")

            finding_data = {
                "email_hash": email_hash,
                "display_name": display_name,
                "username": username,
                "about": about,
                "location": location,
                "avatar_url": avatar_url,
                "urls": urls,
                "accounts": [{"service": a.get("shortname", ""), "url": a.get("url", ""), "username": a.get("username", "")} for a in accounts],
                "raw_profile": entry,
            }

            # Main profile finding
            title_parts = ["Gravatar profile found"]
            if display_name:
                title_parts = [f"Gravatar profile: {display_name}"]
            desc_parts = []
            if display_name:
                desc_parts.append(f"Name: {display_name}")
            if location:
                desc_parts.append(f"Location: {location}")
            if about:
                desc_parts.append(f"Bio: {about[:200]}")
            if accounts:
                desc_parts.append(f"{len(accounts)} linked accounts")

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="medium",
                title=title_parts[0],
                description=". ".join(desc_parts) if desc_parts else "Gravatar profile exists for this email",
                data=finding_data,
                url=f"https://gravatar.com/{email_hash}",
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

            # Linked accounts as separate findings
            for acct in accounts:
                service = acct.get("shortname", acct.get("domain", "unknown"))
                acct_url = acct.get("url", "")
                acct_username = acct.get("username", "")
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity="low",
                    title=f"Linked account: {service}",
                    description=f"Gravatar profile links to {service}" + (f" as {acct_username}" if acct_username else ""),
                    data={"service": service, "url": acct_url, "username": acct_username, "source": "gravatar"},
                    url=acct_url or None,
                    indicator_value=acct_url or acct_username or None,
                    indicator_type="social_url" if acct_url else "username",
                    verified=True,
                ))

        logger.info("Gravatar scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
