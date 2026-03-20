"""Hunter.io domain scanner — email discovery, domain search."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class HunterScanner(BaseScanner):
    MODULE_ID = "hunter"
    LAYER = 2
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.info("Hunter.io scan skipped — no API key")
            return []

        domain = email.split("@")[-1] if "@" in email else email
        results = []

        async with httpx.AsyncClient(timeout=20) as client:
            # Domain search — find all emails at this domain
            try:
                resp = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "api_key": api_key, "limit": 20},
                )
                if resp.status_code == 401:
                    logger.warning("Hunter.io API key invalid")
                    return []
                if resp.status_code != 200:
                    return []

                data = resp.json().get("data", {})
                domain_name = data.get("domain", domain)
                org = data.get("organization", "")
                emails_found = data.get("emails", [])
                total = data.get("total", 0)
                pattern = data.get("pattern")

                if total > 0:
                    # Summary finding
                    other_emails = [e.get("value", "") for e in emails_found if e.get("value") != email]
                    results.append(ScanResult(
                        module=self.MODULE_ID,
                        layer=self.LAYER,
                        category="metadata",
                        severity="medium" if total > 5 else "low",
                        title=f"Hunter.io: {total} emails found at {domain_name}",
                        description=(
                            f"Organization: {org or 'Unknown'}. "
                            f"Email pattern: {pattern or 'Unknown'}. "
                            f"Total discoverable emails: {total}"
                        ),
                        data={
                            "domain": domain_name,
                            "organization": org,
                            "total_emails": total,
                            "pattern": pattern,
                            "sample_emails": [e.get("value") for e in emails_found[:10]],
                        },
                        indicator_value=domain,
                        indicator_type="domain",
                        verified=True,
                    ))

                    # Individual email findings (other people at the org)
                    for entry in emails_found[:10]:
                        found_email = entry.get("value", "")
                        if not found_email or found_email == email:
                            continue
                        first_name = entry.get("first_name", "")
                        last_name = entry.get("last_name", "")
                        position = entry.get("position", "")
                        confidence = entry.get("confidence", 0)
                        sources_count = len(entry.get("sources", []))

                        name = f"{first_name} {last_name}".strip()
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="metadata",
                            severity="info",
                            title=f"Colleague: {name or found_email}" + (f" ({position})" if position else ""),
                            description=(
                                f"Email: {found_email}. "
                                f"{f'Position: {position}. ' if position else ''}"
                                f"Confidence: {confidence}%. Found in {sources_count} sources."
                            ),
                            data={
                                "email": found_email,
                                "first_name": first_name,
                                "last_name": last_name,
                                "position": position,
                                "confidence": confidence,
                                "sources_count": sources_count,
                            },
                            indicator_value=found_email,
                            indicator_type="email",
                        ))

            except Exception:
                logger.exception("Hunter.io domain search failed for %s", domain)

            # Email verification for the target email
            try:
                resp = await client.get(
                    "https://api.hunter.io/v2/email-verifier",
                    params={"email": email, "api_key": api_key},
                )
                if resp.status_code == 200:
                    vdata = resp.json().get("data", {})
                    status = vdata.get("status", "unknown")
                    score = vdata.get("score", 0)
                    if status in ("valid", "accept_all"):
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="metadata",
                            severity="info",
                            title=f"Hunter.io email verification: {status}",
                            description=f"Email {email} status: {status}, score: {score}/100",
                            data={
                                "email": email,
                                "status": status,
                                "score": score,
                                "disposable": vdata.get("disposable"),
                                "webmail": vdata.get("webmail"),
                                "mx_records": vdata.get("mx_records"),
                            },
                            indicator_value=email,
                            indicator_type="email",
                        ))
            except Exception:
                logger.debug("Hunter.io email verification failed for %s", email)

        logger.info("Hunter.io scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
