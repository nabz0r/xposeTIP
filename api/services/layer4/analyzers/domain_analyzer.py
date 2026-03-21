"""Domain Analyzer — deep analysis of all domains found in findings.

Runs subdomain discovery via crt.sh, security headers check,
and technology detection.
"""
import logging
import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Import managed domains set from risk_assessor
from api.services.layer4.analyzers.risk_assessor import MANAGED_DOMAINS


class DomainAnalyzer:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        # 1. Collect all domains
        domains = set()
        for f in findings:
            if not f.data:
                continue
            # Domain from data fields
            for key in ("domain", "ns_provider"):
                val = f.data.get(key)
                if val and isinstance(val, str) and "." in val:
                    domains.add(val.lower().strip())
            # Domain from indicator value (email → domain)
            if f.indicator_type == "email" and f.indicator_value and "@" in f.indicator_value:
                domains.add(f.indicator_value.split("@")[1].lower())

        if not domains:
            return results

        for domain in list(domains)[:5]:  # Cap at 5 domains
            # Skip deep analysis for managed/SaaS domains
            if domain.lower() in MANAGED_DOMAINS:
                results.append({
                    "title": f"Managed domain: {domain}",
                    "description": f"{domain} is a managed SaaS email provider. DNS configuration is controlled by the provider — no user action possible.",
                    "category": "intelligence",
                    "severity": "info",
                    "data": {
                        "analyzer": "domain_analyzer",
                        "domain": domain,
                        "managed": True,
                        "provider": domain.split(".")[-2] if "." in domain else domain,
                    },
                    "indicator_value": domain,
                    "indicator_type": "domain",
                })
                continue

            # Subdomain discovery via crt.sh
            subdomains = self._crt_sh_subdomains(domain)
            if subdomains:
                results.append({
                    "title": f"{len(subdomains)} subdomains discovered for {domain}",
                    "description": f"Certificate Transparency logs reveal {len(subdomains)} subdomains: {', '.join(list(subdomains)[:5])}{'...' if len(subdomains) > 5 else ''}",
                    "category": "intelligence",
                    "severity": "low",
                    "data": {
                        "analyzer": "domain_analyzer",
                        "domain": domain,
                        "subdomains": sorted(subdomains)[:30],
                        "total_subdomains": len(subdomains),
                        "source": "crt.sh",
                    },
                    "indicator_value": domain,
                    "indicator_type": "domain",
                })

            # Security headers check
            headers_result = self._check_security_headers(domain)
            if headers_result:
                missing = [h for h, v in headers_result.items() if not v and h != "domain"]
                if missing:
                    severity = "medium" if len(missing) >= 3 else "low"
                    results.append({
                        "title": f"Missing security headers on {domain}",
                        "description": f"Missing: {', '.join(missing)}. These headers protect against XSS, clickjacking, and MIME-type attacks.",
                        "category": "intelligence",
                        "severity": severity,
                        "data": {
                            "analyzer": "domain_analyzer",
                            "domain": domain,
                            "headers": headers_result,
                            "missing_count": len(missing),
                            "missing_headers": missing,
                        },
                        "indicator_value": domain,
                        "indicator_type": "domain",
                    })

            # Technology detection
            tech = self._detect_technology(domain)
            if tech:
                results.append({
                    "title": f"Technology stack detected on {domain}",
                    "description": f"Server: {tech.get('server', 'Unknown')}. Technologies: {', '.join(tech.get('technologies', []))}",
                    "category": "intelligence",
                    "severity": "info",
                    "data": {
                        "analyzer": "domain_analyzer",
                        "domain": domain,
                        **tech,
                    },
                    "indicator_value": domain,
                    "indicator_type": "domain",
                })

            # SSL certificate check
            ssl_info = self._check_ssl(domain)
            if ssl_info:
                if ssl_info.get("days_until_expiry") is not None:
                    days = ssl_info["days_until_expiry"]
                    if days < 0:
                        severity = "critical"
                        desc = f"SSL certificate for {domain} EXPIRED {abs(days)} days ago!"
                    elif days < 15:
                        severity = "high"
                        desc = f"SSL certificate for {domain} expires in {days} days"
                    elif days < 30:
                        severity = "medium"
                        desc = f"SSL certificate for {domain} expires in {days} days"
                    else:
                        severity = "info"
                        desc = f"SSL certificate for {domain} valid for {days} days"

                    results.append({
                        "title": f"SSL: {domain} — {ssl_info.get('issuer', 'Unknown CA')}",
                        "description": desc,
                        "category": "intelligence",
                        "severity": severity,
                        "data": {
                            "analyzer": "domain_analyzer",
                            "domain": domain,
                            **ssl_info,
                        },
                        "indicator_value": domain,
                        "indicator_type": "domain",
                    })

        return results

    def _crt_sh_subdomains(self, domain: str) -> set:
        try:
            resp = httpx.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                timeout=15,
                headers={"User-Agent": "xpose/0.7.0"},
            )
            if resp.status_code != 200:
                return set()

            entries = resp.json()
            subdomains = set()
            for entry in entries:
                name = entry.get("name_value", "")
                for line in name.split("\n"):
                    sub = line.strip().lower()
                    if sub.endswith(f".{domain}") and "*" not in sub:
                        subdomains.add(sub)
            return subdomains
        except Exception:
            logger.debug("crt.sh lookup failed for %s", domain)
            return set()

    def _check_security_headers(self, domain: str) -> dict | None:
        try:
            resp = httpx.get(
                f"https://{domain}",
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "xpose/0.7.0"},
            )
            headers = resp.headers
            return {
                "domain": domain,
                "Strict-Transport-Security": bool(headers.get("strict-transport-security")),
                "Content-Security-Policy": bool(headers.get("content-security-policy")),
                "X-Frame-Options": bool(headers.get("x-frame-options")),
                "X-Content-Type-Options": bool(headers.get("x-content-type-options")),
                "Referrer-Policy": bool(headers.get("referrer-policy")),
                "Permissions-Policy": bool(headers.get("permissions-policy")),
            }
        except Exception:
            logger.debug("Security headers check failed for %s", domain)
            return None

    def _detect_technology(self, domain: str) -> dict | None:
        try:
            resp = httpx.get(
                f"https://{domain}",
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "xpose/0.7.0"},
            )
            headers = resp.headers
            technologies = []
            server = headers.get("server", "")

            if server:
                technologies.append(server)
            powered_by = headers.get("x-powered-by", "")
            if powered_by:
                technologies.append(powered_by)

            # Detect CDN/WAF
            if headers.get("cf-ray"):
                technologies.append("Cloudflare")
            elif headers.get("x-amz-cf-id"):
                technologies.append("AWS CloudFront")
            elif "akamai" in server.lower():
                technologies.append("Akamai")

            if not technologies:
                return None

            return {
                "server": server or "Unknown",
                "technologies": technologies,
                "powered_by": powered_by or None,
            }
        except Exception:
            return None

    def _check_ssl(self, domain: str) -> dict | None:
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(5)
                s.connect((domain, 443))
                cert = s.getpeercert()

            not_after = cert.get("notAfter", "")
            if not_after:
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days = (expiry - datetime.now(timezone.utc)).days
            else:
                days = None

            issuer_parts = cert.get("issuer", ())
            issuer = ""
            for rdn in issuer_parts:
                for attr, val in rdn:
                    if attr == "organizationName":
                        issuer = val

            subject_parts = cert.get("subject", ())
            cn = ""
            for rdn in subject_parts:
                for attr, val in rdn:
                    if attr == "commonName":
                        cn = val

            san = [v for _, v in cert.get("subjectAltName", ())]

            return {
                "issuer": issuer,
                "common_name": cn,
                "san": san[:10],
                "not_after": not_after,
                "days_until_expiry": days,
            }
        except Exception:
            logger.debug("SSL check failed for %s", domain)
            return None
