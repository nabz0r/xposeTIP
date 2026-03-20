"""DNS Deep scanner — SPF, DMARC, DKIM, MX, NS analysis for email domain."""
import logging
import re

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


def _query_dns(domain: str, rdtype: str) -> list[str]:
    """Query DNS records. Returns list of record strings."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, rdtype)
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


class DNSDeepScanner(BaseScanner):
    MODULE_ID = "dns_deep"
    LAYER = 2
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        domain = email.split("@")[-1] if "@" in email else email
        results = []

        # Gather DNS records
        mx_records = _query_dns(domain, "MX")
        txt_records = _query_dns(domain, "TXT")
        ns_records = _query_dns(domain, "NS")
        a_records = _query_dns(domain, "A")

        # Parse SPF
        spf_record = None
        for txt in txt_records:
            clean = txt.strip('"')
            if clean.startswith("v=spf1"):
                spf_record = clean
                break

        # Parse DMARC
        dmarc_records = _query_dns(f"_dmarc.{domain}", "TXT")
        dmarc_record = None
        for txt in dmarc_records:
            clean = txt.strip('"')
            if clean.startswith("v=DMARC1"):
                dmarc_record = clean
                break

        # Parse DKIM (common selectors)
        dkim_found = False
        dkim_selectors_tried = ["default", "google", "selector1", "selector2", "k1", "mail", "dkim"]
        dkim_selector = None
        for selector in dkim_selectors_tried:
            dkim_recs = _query_dns(f"{selector}._domainkey.{domain}", "TXT")
            if dkim_recs:
                dkim_found = True
                dkim_selector = selector
                break

        if not mx_records and not txt_records and not ns_records:
            return []

        # --- 1. MX Records ---
        if mx_records:
            mx_providers = []
            provider = "unknown"
            for mx in mx_records:
                mx_lower = mx.lower()
                if "google" in mx_lower or "gmail" in mx_lower:
                    provider = "Google Workspace"
                elif "outlook" in mx_lower or "microsoft" in mx_lower:
                    provider = "Microsoft 365"
                elif "protonmail" in mx_lower or "proton" in mx_lower:
                    provider = "ProtonMail"
                elif "zoho" in mx_lower:
                    provider = "Zoho"
                elif "yahoo" in mx_lower:
                    provider = "Yahoo"
                elif "mimecast" in mx_lower:
                    provider = "Mimecast"
                elif "barracuda" in mx_lower:
                    provider = "Barracuda"
                mx_providers.append(mx.strip().rstrip("."))

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="info",
                title=f"Email provider: {provider}",
                description=f"MX records for {domain}: {', '.join(mx_providers[:5])}. Detected provider: {provider}",
                data={
                    "mx_records": mx_providers,
                    "provider": provider,
                    "domain": domain,
                    "source": "dns_deep",
                },
                indicator_value=domain,
                indicator_type="domain",
                verified=True,
            ))

        # --- 2. SPF Analysis ---
        spf_severity = "info"
        spf_issues = []
        if not spf_record:
            spf_severity = "medium"
            spf_issues.append("No SPF record found — domain is vulnerable to email spoofing")
        else:
            if "+all" in spf_record:
                spf_severity = "high"
                spf_issues.append("SPF uses +all (permits all senders — extremely weak)")
            elif "~all" in spf_record:
                spf_severity = "low"
                spf_issues.append("SPF uses ~all (soft fail — allows spoofed emails through)")
            elif "?all" in spf_record:
                spf_severity = "medium"
                spf_issues.append("SPF uses ?all (neutral — no spoofing protection)")
            elif "-all" in spf_record:
                spf_issues.append("SPF uses -all (hard fail — good protection)")
            # Count DNS lookups (max 10)
            lookups = len(re.findall(r'(include:|a:|mx:|redirect=)', spf_record))
            if lookups > 8:
                spf_issues.append(f"SPF has {lookups} DNS lookups (max 10 — risk of permerror)")

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity=spf_severity,
            title=f"SPF: {'configured' if spf_record else 'MISSING'}",
            description=". ".join(spf_issues) if spf_issues else f"SPF record: {spf_record}",
            data={
                "spf_record": spf_record,
                "spf_issues": spf_issues,
                "domain": domain,
                "source": "dns_deep",
            },
            indicator_value=domain,
            indicator_type="domain",
            verified=True,
        ))

        # --- 3. DMARC Analysis ---
        dmarc_severity = "info"
        dmarc_issues = []
        if not dmarc_record:
            dmarc_severity = "medium"
            dmarc_issues.append("No DMARC record — domain has no policy for handling spoofed emails")
        else:
            policy_match = re.search(r'p=(\w+)', dmarc_record)
            policy = policy_match.group(1) if policy_match else "none"
            if policy == "none":
                dmarc_severity = "low"
                dmarc_issues.append("DMARC policy is 'none' — monitoring only, no enforcement")
            elif policy == "quarantine":
                dmarc_issues.append("DMARC policy is 'quarantine' — spoofed emails sent to spam")
            elif policy == "reject":
                dmarc_issues.append("DMARC policy is 'reject' — spoofed emails blocked (strong)")
            # Check for rua (reporting)
            if "rua=" in dmarc_record:
                dmarc_issues.append("DMARC aggregate reporting enabled")
            else:
                dmarc_issues.append("No DMARC aggregate reporting configured")

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity=dmarc_severity,
            title=f"DMARC: {'configured' if dmarc_record else 'MISSING'}",
            description=". ".join(dmarc_issues) if dmarc_issues else f"DMARC record: {dmarc_record}",
            data={
                "dmarc_record": dmarc_record,
                "dmarc_issues": dmarc_issues,
                "domain": domain,
                "source": "dns_deep",
            },
            indicator_value=domain,
            indicator_type="domain",
            verified=True,
        ))

        # --- 4. DKIM ---
        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="info" if dkim_found else "low",
            title=f"DKIM: {'found' if dkim_found else 'not detected'}",
            description=(
                f"DKIM record found with selector '{dkim_selector}'" if dkim_found
                else f"No DKIM record found for common selectors ({', '.join(dkim_selectors_tried)})"
            ),
            data={
                "dkim_found": dkim_found,
                "dkim_selector": dkim_selector,
                "selectors_tried": dkim_selectors_tried,
                "domain": domain,
                "source": "dns_deep",
            },
            indicator_value=domain,
            indicator_type="domain",
            verified=True,
        ))

        # --- 5. NS Records ---
        if ns_records:
            ns_clean = [ns.strip().rstrip(".") for ns in ns_records]
            ns_provider = "unknown"
            for ns in ns_clean:
                ns_lower = ns.lower()
                if "cloudflare" in ns_lower:
                    ns_provider = "Cloudflare"
                elif "aws" in ns_lower or "awsdns" in ns_lower:
                    ns_provider = "AWS Route53"
                elif "google" in ns_lower:
                    ns_provider = "Google Cloud DNS"
                elif "azure" in ns_lower:
                    ns_provider = "Azure DNS"
                elif "ns1." in ns_lower:
                    ns_provider = "NS1"
                elif "domaincontrol" in ns_lower:
                    ns_provider = "GoDaddy"
                elif "registrar" in ns_lower:
                    ns_provider = "Domain registrar"

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="info",
                title=f"DNS provider: {ns_provider}",
                description=f"Nameservers for {domain}: {', '.join(ns_clean)}",
                data={
                    "ns_records": ns_clean,
                    "ns_provider": ns_provider,
                    "domain": domain,
                    "source": "dns_deep",
                },
                indicator_value=domain,
                indicator_type="domain",
                verified=True,
            ))

        # --- 6. Security summary ---
        security_score = 0
        if spf_record and "-all" in spf_record:
            security_score += 1
        if dmarc_record:
            policy_match = re.search(r'p=(\w+)', dmarc_record)
            policy = policy_match.group(1) if policy_match else "none"
            if policy == "reject":
                security_score += 2
            elif policy == "quarantine":
                security_score += 1
        if dkim_found:
            security_score += 1

        sec_level = "weak"
        sec_severity = "medium"
        if security_score >= 4:
            sec_level = "strong"
            sec_severity = "info"
        elif security_score >= 2:
            sec_level = "moderate"
            sec_severity = "low"

        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity=sec_severity,
            title=f"Domain email security: {sec_level}",
            description=(
                f"Email security assessment for {domain}: {sec_level} ({security_score}/4). "
                f"SPF: {'yes' if spf_record else 'NO'}, "
                f"DMARC: {'yes' if dmarc_record else 'NO'}, "
                f"DKIM: {'yes' if dkim_found else 'not detected'}"
            ),
            data={
                "security_score": security_score,
                "security_level": sec_level,
                "has_spf": bool(spf_record),
                "has_dmarc": bool(dmarc_record),
                "has_dkim": dkim_found,
                "domain": domain,
                "source": "dns_deep",
            },
            indicator_value=domain,
            indicator_type="domain",
            verified=True,
        ))

        logger.info("DNS Deep scan for %s: %d findings", domain, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            import dns.resolver
            dns.resolver.resolve("google.com", "MX")
            return True
        except Exception:
            return False
