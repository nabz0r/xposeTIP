"""VirusTotal domain scanner — domain reputation, DNS, subdomains, malware."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

VT_BASE = "https://www.virustotal.com/api/v3"


class VirusTotalScanner(BaseScanner):
    MODULE_ID = "virustotal"
    LAYER = 2
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.info("VirusTotal scan skipped — no API key")
            return []

        domain = email.split("@")[-1] if "@" in email else email
        results = []
        headers = {"x-apikey": api_key, "User-Agent": "xpose-tip"}

        async with httpx.AsyncClient(timeout=20) as client:
            # Domain report
            try:
                resp = await client.get(f"{VT_BASE}/domains/{domain}", headers=headers)
                if resp.status_code == 429:
                    logger.warning("VirusTotal rate limited")
                    return []
                if resp.status_code != 200:
                    return []

                data = resp.json().get("data", {})
                attrs = data.get("attributes", {})

                # Reputation
                reputation = attrs.get("reputation", 0)
                last_analysis = attrs.get("last_analysis_stats", {})
                malicious = last_analysis.get("malicious", 0)
                suspicious = last_analysis.get("suspicious", 0)
                harmless = last_analysis.get("harmless", 0)
                undetected = last_analysis.get("undetected", 0)

                severity = "info"
                if malicious > 0:
                    severity = "critical" if malicious >= 3 else "high"
                elif suspicious > 0:
                    severity = "medium"

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="metadata",
                    severity=severity,
                    title=f"Domain reputation: {domain}",
                    description=(
                        f"VirusTotal analysis: {malicious} malicious, {suspicious} suspicious, "
                        f"{harmless} harmless, {undetected} undetected. Reputation: {reputation}"
                    ),
                    data={
                        "domain": domain,
                        "reputation": reputation,
                        "malicious": malicious,
                        "suspicious": suspicious,
                        "harmless": harmless,
                        "undetected": undetected,
                        "categories": attrs.get("categories", {}),
                        "registrar": attrs.get("registrar"),
                        "creation_date": attrs.get("creation_date"),
                        "last_analysis_date": attrs.get("last_analysis_date"),
                    },
                    url=f"https://www.virustotal.com/gui/domain/{domain}",
                    indicator_value=domain,
                    indicator_type="domain",
                    verified=True,
                ))

                # SSL certificate info
                last_https_cert = attrs.get("last_https_certificate", {})
                if last_https_cert:
                    subject = last_https_cert.get("subject", {})
                    issuer = last_https_cert.get("issuer", {})
                    validity = last_https_cert.get("validity", {})
                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="metadata",
                        severity="info",
                        title=f"SSL certificate for {domain}",
                        description=(
                            f"Subject: {subject.get('CN', 'N/A')}, "
                            f"Issuer: {issuer.get('O', 'N/A')}, "
                            f"Valid until: {validity.get('not_after', 'N/A')}"
                        ),
                        data={
                            "subject": subject,
                            "issuer": issuer,
                            "validity": validity,
                            "serial_number": last_https_cert.get("serial_number"),
                        },
                        indicator_value=domain,
                        indicator_type="domain",
                    ))

            except Exception:
                logger.exception("VirusTotal domain lookup failed for %s", domain)

            # Subdomains
            try:
                resp = await client.get(
                    f"{VT_BASE}/domains/{domain}/subdomains",
                    headers=headers,
                    params={"limit": 20},
                )
                if resp.status_code == 200:
                    subs = resp.json().get("data", [])
                    subdomain_list = [s.get("id", "") for s in subs if s.get("id")]
                    if subdomain_list:
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="metadata",
                            severity="low",
                            title=f"{len(subdomain_list)} subdomains discovered for {domain}",
                            description=f"Subdomains: {', '.join(subdomain_list[:10])}{'...' if len(subdomain_list) > 10 else ''}",
                            data={"subdomains": subdomain_list, "total": len(subdomain_list)},
                            indicator_value=domain,
                            indicator_type="domain",
                            verified=True,
                        ))
            except Exception:
                logger.debug("VirusTotal subdomains lookup failed for %s", domain)

        logger.info("VirusTotal scan for %s: %d findings", domain, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True  # Requires API key, can't check without it
