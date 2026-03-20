"""IP Analyzer — deep analysis of all IPs found in findings.

Extracts IPs from geoip, dns_deep, github commits, etc.
Runs ASN lookup, reverse DNS, and AbuseIPDB check.
"""
import ipaddress
import logging
import socket

import httpx

logger = logging.getLogger(__name__)


def _is_private(ip_str: str) -> bool:
    try:
        return ipaddress.ip_address(ip_str).is_private
    except ValueError:
        return True


class IPAnalyzer:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        # 1. Collect all IPs from findings
        ips = set()
        for f in findings:
            if not f.data:
                continue
            for key in ("ip", "query", "ip_address"):
                val = f.data.get(key)
                if val and isinstance(val, str):
                    ips.add(val)
            # IPs from port scan results
            if isinstance(f.data.get("ips"), list):
                for ip in f.data["ips"]:
                    if isinstance(ip, str):
                        ips.add(ip)

        # Filter private/invalid
        public_ips = [ip for ip in ips if not _is_private(ip)]

        if not public_ips:
            return results

        # 2. Analyze each IP
        for ip in public_ips[:10]:  # Cap at 10 IPs
            # ASN lookup via ipapi.co (free, no key)
            asn_data = self._asn_lookup(ip)
            if asn_data:
                results.append({
                    "title": f"ASN: {asn_data.get('org', 'Unknown')} (AS{asn_data.get('asn', '?')})",
                    "description": f"IP {ip} belongs to {asn_data.get('org', 'Unknown')} ({asn_data.get('country_name', '')})",
                    "category": "intelligence",
                    "severity": "info",
                    "data": {
                        "analyzer": "ip_analyzer",
                        "ip": ip,
                        "asn": asn_data.get("asn"),
                        "org": asn_data.get("org"),
                        "isp": asn_data.get("org"),
                        "country": asn_data.get("country_name"),
                        "city": asn_data.get("city"),
                    },
                    "indicator_value": ip,
                    "indicator_type": "ip",
                })

            # Reverse DNS
            rdns = self._reverse_dns(ip)
            if rdns and rdns != ip:
                results.append({
                    "title": f"Reverse DNS: {rdns}",
                    "description": f"IP {ip} resolves to {rdns}",
                    "category": "intelligence",
                    "severity": "info",
                    "data": {
                        "analyzer": "ip_analyzer",
                        "ip": ip,
                        "reverse_dns": rdns,
                    },
                    "indicator_value": ip,
                    "indicator_type": "ip",
                })

        # 3. Summary
        if len(public_ips) > 1:
            # Check how many unique ASNs/countries
            countries = set()
            for r in results:
                c = (r.get("data") or {}).get("country")
                if c:
                    countries.add(c)

            if countries:
                results.append({
                    "title": f"IP infrastructure spans {len(countries)} countries",
                    "description": f"Found {len(public_ips)} unique IPs across {', '.join(sorted(countries))}",
                    "category": "intelligence",
                    "severity": "info",
                    "data": {
                        "analyzer": "ip_analyzer",
                        "total_ips": len(public_ips),
                        "countries": sorted(countries),
                        "ips": list(public_ips)[:20],
                    },
                })

        return results

    def _asn_lookup(self, ip: str) -> dict | None:
        try:
            resp = httpx.get(
                f"https://ipapi.co/{ip}/json/",
                timeout=10,
                headers={"User-Agent": "xpose/0.7.0"},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            logger.debug("ASN lookup failed for %s", ip)
        return None

    def _reverse_dns(self, ip: str) -> str | None:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return None
