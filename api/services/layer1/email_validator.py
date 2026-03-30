import asyncio
import re
import socket

from api.services.base import BaseScanner, ScanResult

DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "10minutemail.com", "yopmail.com", "trashmail.com", "sharklasers.com",
    "guerrillamailblock.com", "grr.la", "dispostable.com",
}

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class EmailValidatorScanner(BaseScanner):
    MODULE_ID = "email_validator"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        domain = email.split("@")[1].lower() if "@" in email else ""

        # Format check
        is_valid = bool(EMAIL_RE.match(email))
        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="info",
            title="Email format validation",
            description=f"Email format is {'valid' if is_valid else 'invalid'}",
            data={"email": email, "format_valid": is_valid},
            indicator_value=email,
            indicator_type="email",
            verified=is_valid,
        ))

        if not is_valid:
            return results

        # MX record check (real MX lookup via dnspython)
        has_mx = False
        mx_records = []
        try:
            import dns.resolver
            loop = asyncio.get_event_loop()

            def _resolve_mx():
                try:
                    answers = dns.resolver.resolve(domain, 'MX')
                    return [(str(r.exchange).rstrip('.'), r.preference) for r in answers]
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    return []
                except Exception:
                    return []

            mx_result = await loop.run_in_executor(None, _resolve_mx)
            if mx_result:
                has_mx = True
                mx_records = [f"{host} (priority {pref})" for host, pref in sorted(mx_result, key=lambda x: x[1])[:5]]
        except Exception:
            pass

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="info",
            title=f"DNS records for {domain}",
            description=f"Domain {domain} {'has' if has_mx else 'has no'} DNS records",
            data={"domain": domain, "has_dns": has_mx, "records": mx_records},
            indicator_value=domain,
            indicator_type="domain",
            verified=has_mx,
        ))

        # Disposable check
        if domain in DISPOSABLE_DOMAINS:
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="medium",
                title="Disposable email provider detected",
                description=f"{domain} is a known disposable email provider",
                data={"domain": domain, "disposable": True},
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        return results

    async def health_check(self) -> bool:
        return True
