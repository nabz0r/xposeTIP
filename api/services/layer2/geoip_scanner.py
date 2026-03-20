import asyncio
import logging
import socket

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"


class GeoIPScanner(BaseScanner):
    MODULE_ID = "geoip"
    LAYER = 2
    CATEGORY = "geolocation"
    SUPPORTED_REGIONS = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        domain = email.split("@")[1].lower() if "@" in email else ""
        if not domain:
            return []

        ips = set()
        # MX records
        try:
            addrs = socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
            for addr in addrs:
                ips.add(addr[4][0])
        except Exception:
            pass
        # A records
        try:
            addrs = socket.getaddrinfo(domain, None, socket.AF_INET)
            for addr in addrs:
                ips.add(addr[4][0])
        except Exception:
            pass

        if not ips:
            logger.info("No IPs resolved for domain %s", domain)
            return []

        results = []
        async with httpx.AsyncClient(timeout=10) as client:
            for ip in ips:
                try:
                    resp = await client.get(IP_API_URL.format(ip=ip))
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    if data.get("status") != "success":
                        continue

                    country = data.get("country", "Unknown")
                    city = data.get("city", "Unknown")
                    country_code = data.get("countryCode", "")

                    geo_data = {
                        "ip": ip,
                        "country": country,
                        "country_code": country_code,
                        "city": city,
                        "region": data.get("regionName", ""),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "timezone": data.get("timezone", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "as": data.get("as", ""),
                        "domain": domain,
                    }

                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="geolocation",
                        severity="info",
                        title=f"Mail server in {city}, {country}",
                        description=f"IP {ip} for domain {domain} geolocated to {city}, {country} ({data.get('isp', '')})",
                        data=geo_data,
                        indicator_value=ip,
                        indicator_type="ip",
                        verified=True,
                    ))
                except Exception:
                    logger.debug("GeoIP lookup failed for IP %s", ip)

                await asyncio.sleep(1.5)  # 45 req/min rate limit

        logger.info("GeoIP scan for %s: %d findings", domain, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://ip-api.com/json/8.8.8.8?fields=status")
                return resp.status_code == 200
        except Exception:
            return False
