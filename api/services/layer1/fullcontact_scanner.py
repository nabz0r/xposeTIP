"""FullContact scanner — person enrichment from email (requires API key)."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class FullContactScanner(BaseScanner):
    MODULE_ID = "fullcontact"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key", "")
        if not api_key:
            logger.info("FullContact: no API key, skipping")
            return []

        results = []

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    "https://api.fullcontact.com/v3/person.enrich",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"email": email},
                )
                if resp.status_code == 401:
                    logger.warning("FullContact: invalid API key")
                    return []
                if resp.status_code == 404:
                    logger.info("FullContact: no data for %s", email)
                    return []
                if resp.status_code == 429:
                    logger.warning("FullContact: rate limited")
                    return []
                if resp.status_code != 200:
                    logger.info("FullContact returned %d for %s", resp.status_code, email)
                    return []

                data = resp.json()
            except Exception:
                logger.exception("FullContact request failed for %s", email)
                return []

        full_name = data.get("fullName", "")
        age_range = data.get("ageRange", "")
        gender = data.get("gender", "")
        location = data.get("location", "")
        title = data.get("title", "")
        organization = data.get("organization", "")
        bio = data.get("bio", "")
        avatar = data.get("avatar", "")
        website = data.get("website", "")
        twitter = data.get("twitter", "")
        linkedin = data.get("linkedin", "")
        details = data.get("details", {})
        social_profiles = data.get("socialProfiles", data.get("social_profiles", []))

        # Main profile finding
        desc_parts = []
        if full_name:
            desc_parts.append(f"Name: {full_name}")
        if title and organization:
            desc_parts.append(f"Role: {title} at {organization}")
        elif organization:
            desc_parts.append(f"Organization: {organization}")
        if location:
            desc_parts.append(f"Location: {location}")
        if age_range:
            desc_parts.append(f"Age range: {age_range}")
        if gender:
            desc_parts.append(f"Gender: {gender}")

        finding_data = {
            "full_name": full_name,
            "age_range": age_range,
            "gender": gender,
            "location": location,
            "title": title,
            "organization": organization,
            "bio": bio,
            "avatar": avatar,
            "website": website,
            "source": "fullcontact",
            "raw": data,
        }

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="medium",
            title=f"FullContact profile: {full_name}" if full_name else "FullContact profile found",
            description=". ".join(desc_parts) if desc_parts else "Person enrichment data found for this email",
            data=finding_data,
            url=website or None,
            indicator_value=email,
            indicator_type="email",
            verified=True,
        ))

        # Social profiles
        if isinstance(social_profiles, list):
            for profile in social_profiles:
                network = profile.get("type") or profile.get("network") or "unknown"
                url = profile.get("url", "")
                username = profile.get("username", "")
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity="low",
                    title=f"Social profile: {network}",
                    description=f"FullContact identified a {network} profile" + (f" ({username})" if username else ""),
                    data={"network": network, "url": url, "username": username, "source": "fullcontact"},
                    url=url or None,
                    indicator_value=url or username or None,
                    indicator_type="social_url" if url else "username",
                    verified=False,
                ))

        # Twitter/LinkedIn shortcuts
        if twitter and not any(p.get("type") == "twitter" for p in (social_profiles or [])):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="social_account",
                severity="low",
                title="Social profile: Twitter/X",
                description=f"FullContact identified a Twitter/X profile: {twitter}",
                data={"network": "twitter", "handle": twitter, "source": "fullcontact"},
                url=f"https://x.com/{twitter}" if not twitter.startswith("http") else twitter,
                indicator_value=twitter,
                indicator_type="username",
                verified=False,
            ))

        if linkedin and not any(p.get("type") == "linkedin" for p in (social_profiles or [])):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="social_account",
                severity="low",
                title="Social profile: LinkedIn",
                description=f"FullContact identified a LinkedIn profile",
                data={"network": "linkedin", "url": linkedin, "source": "fullcontact"},
                url=linkedin,
                indicator_value=linkedin,
                indicator_type="social_url",
                verified=False,
            ))

        logger.info("FullContact scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        api_key = kwargs.get("api_key", "")
        if not api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.fullcontact.com/v3/person.enrich",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"email": "test@example.com"},
                )
                return resp.status_code in (200, 404)
        except Exception:
            return False
