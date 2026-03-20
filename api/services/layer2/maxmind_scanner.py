import logging
import os
import socket

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

MAXMIND_DB_PATH = os.environ.get("MAXMIND_DB_PATH", "data/maxmind/GeoLite2-City.mmdb")


class MaxmindScanner(BaseScanner):
    MODULE_ID = "maxmind_geo"
    LAYER = 2
    CATEGORY = "geolocation"
    SUPPORTED_REGIONS = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        try:
            import geoip2.database
        except ImportError:
            logger.warning("geoip2 not installed — skipping GeoIP lookup")
            return []

        if not os.path.exists(MAXMIND_DB_PATH):
            logger.warning("MaxMind DB not found at %s — skipping GeoIP lookup", MAXMIND_DB_PATH)
            return []

        domain = email.split("@")[1].lower() if "@" in email else ""
        if not domain:
            return []

        results = []

        # Resolve MX / A records to get IPs
        ips = set()
        try:
            # Try MX-style: resolve the domain
            addrs = socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
            for addr in addrs:
                ips.add(addr[4][0])
        except Exception:
            pass

        try:
            addrs = socket.getaddrinfo(domain, None, socket.AF_INET)
            for addr in addrs:
                ips.add(addr[4][0])
        except Exception:
            pass

        if not ips:
            logger.info("No IPs resolved for domain %s", domain)
            return []

        try:
            reader = geoip2.database.Reader(MAXMIND_DB_PATH)
        except Exception:
            logger.exception("Failed to open MaxMind DB")
            return []

        try:
            for ip in ips:
                try:
                    resp = reader.city(ip)
                    country = resp.country.name or "Unknown"
                    city = resp.city.name or "Unknown"
                    lat = resp.location.latitude
                    lon = resp.location.longitude

                    geo_data = {
                        "ip": ip,
                        "country": country,
                        "country_code": resp.country.iso_code,
                        "city": city,
                        "latitude": lat,
                        "longitude": lon,
                        "domain": domain,
                    }

                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="geolocation",
                        severity="info",
                        title=f"Mail server located in {country}, {city}",
                        description=f"IP {ip} for domain {domain} geolocated to {city}, {country}",
                        data=geo_data,
                        indicator_value=ip,
                        indicator_type="ip",
                        verified=True,
                    ))
                except Exception:
                    logger.debug("GeoIP lookup failed for IP %s", ip)
        finally:
            reader.close()

        logger.info("MaxMind scan complete for %s: %d findings", domain, len(results))
        return results

    async def health_check(self) -> bool:
        try:
            import geoip2.database
            return os.path.exists(MAXMIND_DB_PATH)
        except ImportError:
            return False
