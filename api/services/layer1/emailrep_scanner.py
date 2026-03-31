"""EmailRep.io scanner — free email reputation, breach status, social profiles, security."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class EmailRepScanner(BaseScanner):
    MODULE_ID = "emailrep"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        headers = {"User-Agent": "xpose-tip", "Accept": "application/json"}
        api_key = kwargs.get("api_key")
        if api_key:
            headers["Key"] = api_key

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"https://emailrep.io/{email}",
                    headers=headers,
                )
                if resp.status_code == 429:
                    logger.warning("EmailRep rate limited for %s", email)
                    return []
                if resp.status_code != 200:
                    logger.info("EmailRep returned %d for %s", resp.status_code, email)
                    return []

                data = resp.json()
            except Exception:
                logger.exception("EmailRep request failed for %s", email)
                return []

        reputation = data.get("reputation", "none")
        suspicious = data.get("suspicious", False)
        details = data.get("details", {})

        # --- 1. Reputation finding (always) ---
        rep_severity = "info"
        if reputation == "high":
            rep_severity = "info"
        elif reputation == "medium":
            rep_severity = "low"
        elif reputation == "low":
            rep_severity = "medium"
        elif reputation == "none":
            rep_severity = "medium"

        if suspicious:
            rep_severity = "high"

        rep_desc_parts = [
            f"Reputation: {reputation}",
            f"Suspicious: {'Yes' if suspicious else 'No'}",
        ]
        if details.get("first_seen"):
            rep_desc_parts.append(f"First seen: {details['first_seen']}")
        if details.get("last_seen"):
            rep_desc_parts.append(f"Last seen: {details['last_seen']}")
        if details.get("days_since_domain_creation") is not None:
            rep_desc_parts.append(f"Domain age: {details['days_since_domain_creation']} days")

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity=rep_severity,
            title=f"Email reputation: {reputation}" + (" (suspicious)" if suspicious else ""),
            description=". ".join(rep_desc_parts),
            data={
                "reputation": reputation,
                "suspicious": suspicious,
                "references": data.get("references", 0),
                "first_seen": details.get("first_seen"),
                "last_seen": details.get("last_seen"),
                "domain_age_days": details.get("days_since_domain_creation"),
                "free_provider": details.get("free_provider", False),
                "deliverable": details.get("deliverable", False),
                "accept_all": details.get("accept_all", False),
                "spam": details.get("spam", False),
            },
            indicator_value=email,
            indicator_type="email",
            verified=True,
        ))

        # --- 2. Credentials leaked ---
        if details.get("credentials_leaked"):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="breach",
                severity="critical",
                title="Credentials found in leak databases",
                description=(
                    "EmailRep reports that credentials (email + password) for this address "
                    "have been found in one or more data breaches or paste sites."
                ),
                data={
                    "credentials_leaked": True,
                    "credentials_leaked_recent": details.get("credentials_leaked_recent", False),
                    "source": "emailrep",
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # --- 3. Data breach ---
        if details.get("data_breach"):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="breach",
                severity="high",
                title="Email found in data breaches",
                description=(
                    "This email address appears in known data breach databases. "
                    f"Credentials leaked recently: {'Yes' if details.get('credentials_leaked_recent') else 'No'}."
                ),
                data={
                    "data_breach": True,
                    "credentials_leaked": details.get("credentials_leaked", False),
                    "credentials_leaked_recent": details.get("credentials_leaked_recent", False),
                    "source": "emailrep",
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # --- 4. Social/online profiles ---
        profiles = details.get("profiles", [])
        for profile in profiles:
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="social_account",
                severity="low",
                title=f"Profile detected: {profile}",
                description=f"EmailRep detected a {profile} profile associated with this email address.",
                data={"platform": profile, "source": "emailrep"},
                indicator_value=email,
                indicator_type="email",
                verified=False,
            ))

        # --- 5. Email security (SPF/DMARC/DKIM) ---
        spf = details.get("spf_strict", False)
        dmarc = details.get("dmarc_enforced", False)
        dkim = details.get("valid_mx", False)
        if not spf or not dmarc:
            security_issues = []
            if not spf:
                security_issues.append("SPF not strict")
            if not dmarc:
                security_issues.append("DMARC not enforced")
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="low",
                title="Email domain security gaps",
                description=(
                    f"Domain security issues detected: {', '.join(security_issues)}. "
                    f"SPF strict: {'Yes' if spf else 'No'}, "
                    f"DMARC enforced: {'Yes' if dmarc else 'No'}, "
                    f"Valid MX: {'Yes' if dkim else 'No'}."
                ),
                data={
                    "spf_strict": spf,
                    "dmarc_enforced": dmarc,
                    "valid_mx": dkim,
                    "source": "emailrep",
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # --- 6. Disposable email ---
        if details.get("disposable"):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="medium",
                title="Disposable email address detected",
                description="This email address belongs to a disposable/temporary email provider.",
                data={"disposable": True, "source": "emailrep"},
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # --- 7. Spam flag ---
        if details.get("spam"):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="low",
                title="Email flagged as spam source",
                description="This email address has been flagged in spam databases.",
                data={"spam": True, "source": "emailrep"},
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # --- 8. Malicious activity ---
        if details.get("malicious_activity") or details.get("malicious_activity_recent"):
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="high",
                title="Malicious activity associated with email",
                description=(
                    "This email address has been associated with malicious activity. "
                    f"Recent: {'Yes' if details.get('malicious_activity_recent') else 'No'}."
                ),
                data={
                    "malicious_activity": details.get("malicious_activity", False),
                    "malicious_activity_recent": details.get("malicious_activity_recent", False),
                    "source": "emailrep",
                },
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        logger.info("EmailRep scan for %s: %d findings (rep=%s)", email, len(results), reputation)
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://emailrep.io/test@example.com",
                    headers={"User-Agent": "xpose-tip", "Accept": "application/json"},
                )
                return resp.status_code == 200
        except Exception:
            return False
