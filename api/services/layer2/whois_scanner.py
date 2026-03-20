import logging

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class WhoisScanner(BaseScanner):
    MODULE_ID = "whois_lookup"
    LAYER = 2
    CATEGORY = "domain_registration"
    SUPPORTED_REGIONS = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        try:
            import whois
        except ImportError:
            logger.warning("python-whois not installed — skipping WHOIS lookup")
            return []

        results = []
        domain = email.split("@")[1].lower() if "@" in email else ""
        if not domain:
            return []

        try:
            w = whois.whois(domain)
        except Exception:
            logger.warning("WHOIS lookup failed for domain %s", domain)
            return []

        whois_data = {}
        for key in ("domain_name", "registrar", "creation_date", "expiration_date",
                     "name_servers", "status", "emails", "registrant",
                     "registrant_email", "admin_email", "tech_email", "org", "country"):
            val = getattr(w, key, None)
            if val is not None:
                whois_data[key] = str(val) if not isinstance(val, (list, dict)) else val

        # Always create an info finding with WHOIS data
        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="domain_registration",
            severity="info",
            title=f"WHOIS data for {domain}",
            description=f"Registrar: {w.registrar or 'unknown'}, created: {w.creation_date or 'unknown'}",
            data=whois_data,
            indicator_value=domain,
            indicator_type="domain",
            verified=True,
        ))

        # Check if target email is the domain registrant
        whois_emails = []
        for field in ("registrant_email", "admin_email", "tech_email", "emails"):
            val = getattr(w, field, None)
            if isinstance(val, list):
                whois_emails.extend([e.lower() for e in val if isinstance(e, str)])
            elif isinstance(val, str):
                whois_emails.append(val.lower())

        email_lower = email.lower()
        if email_lower in whois_emails:
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="domain_registration",
                severity="medium",
                title=f"Domain {domain} registered with this email",
                description=f"Email {email} appears as a registrant contact for {domain}",
                data=whois_data,
                url=f"https://who.is/whois/{domain}",
                indicator_value=domain,
                indicator_type="domain",
                verified=True,
            ))

        logger.info("WHOIS scan complete for %s: %d findings", domain, len(results))
        return results

    async def health_check(self) -> bool:
        try:
            import whois
            return True
        except ImportError:
            return False
