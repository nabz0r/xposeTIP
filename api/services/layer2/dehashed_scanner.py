"""Dehashed breach scanner — credential search with hashed passwords, IPs, usernames."""
import logging
from base64 import b64encode

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class DehashedScanner(BaseScanner):
    MODULE_ID = "dehashed"
    LAYER = 2
    CATEGORY = "breach"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.info("Dehashed scan skipped — no API key")
            return []

        # Dehashed uses Basic auth: email:api_key
        # The api_key should be in format "email:key" or just "key"
        # We'll use the target email as username for auth if not provided
        if ":" in api_key:
            auth_str = api_key
        else:
            auth_str = f"user@example.com:{api_key}"

        auth_b64 = b64encode(auth_str.encode()).decode()
        results = []
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "User-Agent": "xpose-tip",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.get(
                    "https://api.dehashed.com/search",
                    headers=headers,
                    params={"query": f"email:{email}", "size": 50},
                )
                if resp.status_code == 401:
                    logger.warning("Dehashed API key invalid")
                    return []
                if resp.status_code == 429:
                    logger.warning("Dehashed rate limited")
                    return []
                if resp.status_code != 200:
                    return []

                data = resp.json()
                entries = data.get("entries", [])
                total = data.get("total", 0)

                if not entries:
                    return []

                # Summary finding
                has_passwords = any(e.get("hashed_password") or e.get("password") for e in entries)
                has_phones = any(e.get("phone") for e in entries)
                has_names = any(e.get("name") for e in entries)
                has_ips = any(e.get("ip_address") for e in entries)

                databases = list(set(e.get("database_name", "Unknown") for e in entries if e.get("database_name")))

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="breach",
                    severity="critical" if has_passwords else "high",
                    title=f"Dehashed: {total} breach entries found",
                    description=(
                        f"Found in {len(databases)} databases: {', '.join(databases[:5])}. "
                        f"{'Passwords exposed! ' if has_passwords else ''}"
                        f"{'Phone numbers found. ' if has_phones else ''}"
                        f"{'IP addresses found. ' if has_ips else ''}"
                    ),
                    data={
                        "total_entries": total,
                        "databases": databases,
                        "has_passwords": has_passwords,
                        "has_phones": has_phones,
                        "has_names": has_names,
                        "has_ips": has_ips,
                    },
                    indicator_value=email,
                    indicator_type="email",
                    verified=True,
                ))

                # Per-database findings
                by_db = {}
                for entry in entries:
                    db = entry.get("database_name", "Unknown")
                    if db not in by_db:
                        by_db[db] = []
                    by_db[db].append(entry)

                for db_name, db_entries in list(by_db.items())[:10]:
                    entry = db_entries[0]
                    has_pw = any(e.get("hashed_password") or e.get("password") for e in db_entries)
                    username = entry.get("username", "")
                    name = entry.get("name", "")
                    ip = entry.get("ip_address", "")
                    phone = entry.get("phone", "")

                    detail_parts = []
                    if username:
                        detail_parts.append(f"username={username}")
                    if name:
                        detail_parts.append(f"name={name}")
                    if has_pw:
                        detail_parts.append("has_password=true")
                    if ip:
                        detail_parts.append(f"ip={ip}")
                    if phone:
                        detail_parts.append(f"phone={phone}")

                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="breach",
                        severity="critical" if has_pw else "high",
                        title=f"Breach: {db_name}",
                        description=f"Found in {db_name}: {', '.join(detail_parts) if detail_parts else 'email match'}",
                        data={
                            "database_name": db_name,
                            "entries_count": len(db_entries),
                            "username": username,
                            "name": name,
                            "has_password": has_pw,
                            "ip_address": ip,
                            "phone": phone,
                        },
                        url=f"https://dehashed.com/search?query={email}",
                        indicator_value=email,
                        indicator_type="email",
                        verified=True,
                    ))

            except Exception:
                logger.exception("Dehashed search failed for %s", email)

        logger.info("Dehashed scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
