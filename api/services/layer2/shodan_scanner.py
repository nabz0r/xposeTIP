"""Shodan scanner — domain DNS, IP ports, services, technologies."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class ShodanScanner(BaseScanner):
    MODULE_ID = "shodan"
    LAYER = 2
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.info("Shodan scan skipped — no API key")
            return []

        domain = email.split("@")[-1] if "@" in email else email
        results = []

        async with httpx.AsyncClient(timeout=20) as client:
            # Domain DNS lookup
            try:
                resp = await client.get(
                    f"https://api.shodan.io/dns/domain/{domain}",
                    params={"key": api_key},
                )
                if resp.status_code == 401:
                    logger.warning("Shodan API key invalid")
                    return []
                if resp.status_code != 200:
                    return []

                data = resp.json()
                subdomains = data.get("subdomains", [])
                records = data.get("data", [])

                # Collect unique IPs from A records
                ips = set()
                for record in records:
                    if record.get("type") == "A":
                        ips.add(record.get("value", ""))

                if subdomains:
                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="metadata",
                        severity="low",
                        title=f"Shodan: {len(subdomains)} subdomains for {domain}",
                        description=f"Subdomains: {', '.join(subdomains[:15])}{'...' if len(subdomains) > 15 else ''}",
                        data={
                            "domain": domain,
                            "subdomains": subdomains[:50],
                            "total_subdomains": len(subdomains),
                            "dns_records": len(records),
                        },
                        indicator_value=domain,
                        indicator_type="domain",
                        verified=True,
                    ))

            except Exception:
                logger.exception("Shodan domain lookup failed for %s", domain)
                ips = set()

            # Host lookup for each discovered IP (max 3)
            for ip in list(ips)[:3]:
                if not ip:
                    continue
                try:
                    resp = await client.get(
                        f"https://api.shodan.io/shodan/host/{ip}",
                        params={"key": api_key},
                    )
                    if resp.status_code != 200:
                        continue

                    host = resp.json()
                    ports = host.get("ports", [])
                    os_name = host.get("os")
                    org = host.get("org", "")
                    isp = host.get("isp", "")
                    vulns = host.get("vulns", [])

                    severity = "info"
                    if vulns:
                        severity = "high"
                    elif len(ports) > 10:
                        severity = "medium"
                    elif len(ports) > 5:
                        severity = "low"

                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="metadata",
                        severity=severity,
                        title=f"Shodan: {ip} — {len(ports)} open ports",
                        description=(
                            f"IP {ip} ({org or isp}): ports {', '.join(str(p) for p in ports[:20])}"
                            f"{f'. OS: {os_name}' if os_name else ''}"
                            f"{f'. {len(vulns)} vulnerabilities detected' if vulns else ''}"
                        ),
                        data={
                            "ip": ip,
                            "ports": ports,
                            "os": os_name,
                            "org": org,
                            "isp": isp,
                            "vulns": vulns[:20] if vulns else [],
                            "city": host.get("city"),
                            "country_code": host.get("country_code"),
                            "hostnames": host.get("hostnames", []),
                        },
                        indicator_value=ip,
                        indicator_type="ip",
                        verified=True,
                    ))

                except Exception:
                    logger.debug("Shodan host lookup failed for %s", ip)

        logger.info("Shodan scan for %s: %d findings", domain, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
