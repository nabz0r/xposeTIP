import logging
import re

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class GoogleScanner(BaseScanner):
    MODULE_ID = "google_profile"
    LAYER = 1
    CATEGORY = "metadata"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        domain = email.split("@")[1].lower() if "@" in email else ""

        # Detect Gmail/Google Workspace
        is_gmail = domain in ("gmail.com", "googlemail.com")
        is_google_workspace = False
        if not is_gmail and domain:
            try:
                import socket
                addrs = socket.getaddrinfo(f"_dmarc.{domain}", None)
                # Check MX for Google
                import subprocess
                mx_check = subprocess.run(
                    ["python3", "-c", f"import socket; print(socket.getaddrinfo('aspmx.l.google.com', 25))"],
                    capture_output=True, timeout=5
                )
                # Simpler: just check MX records for google
                mx_resp = subprocess.run(
                    ["python3", "-c",
                     f"import dns.resolver; answers = dns.resolver.resolve('{domain}', 'MX'); print([str(r.exchange) for r in answers])"],
                    capture_output=True, timeout=5, text=True
                )
                if "google" in mx_resp.stdout.lower():
                    is_google_workspace = True
            except Exception:
                pass

        if is_gmail or is_google_workspace:
            svc_type = "Gmail" if is_gmail else "Google Workspace"
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="metadata",
                severity="info",
                title=f"Email uses Google services ({svc_type})",
                description=f"{email} is a {svc_type} address. Google profile, Drive, YouTube, Maps contributions may be linked.",
                data={"email": email, "google_service": svc_type, "domain": domain},
                indicator_value=email,
                indicator_type="email",
                verified=True,
            ))

        # YouTube search
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    "https://www.youtube.com/results",
                    params={"search_query": f'"{email}"'},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    # Count video results (rough estimate from page content)
                    video_count = len(re.findall(r'"videoId":', resp.text))
                    if video_count > 0:
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="metadata",
                            severity="low",
                            title=f"YouTube references found ({video_count} results)",
                            description=f"YouTube search for this email returned approximately {video_count} results",
                            data={"email": email, "youtube_results": video_count},
                            url=f"https://www.youtube.com/results?search_query=%22{email}%22",
                            indicator_value=email,
                            indicator_type="email",
                        ))
            except Exception:
                logger.debug("YouTube search failed for %s", email)

        logger.info("Google scanner for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        return True
