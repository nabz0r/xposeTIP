"""Risk Assessor — final synthesis generating human-readable risk assessment.

Produces an overall risk level, remediation priorities, and actionable steps.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# SaaS/managed email domains — user cannot fix DNS for these
MANAGED_DOMAINS = {
    # Google
    "gmail.com", "googlemail.com", "google.com",
    # Microsoft
    "outlook.com", "hotmail.com", "live.com", "msn.com", "outlook.fr",
    "outlook.de", "outlook.co.uk", "outlook.es", "outlook.it",
    # Yahoo
    "yahoo.com", "yahoo.fr", "yahoo.co.uk", "yahoo.de", "yahoo.it",
    "yahoo.es", "yahoo.co.jp", "ymail.com", "rocketmail.com",
    # Apple
    "icloud.com", "me.com", "mac.com",
    # ProtonMail
    "protonmail.com", "proton.me", "pm.me", "protonmail.ch",
    # Tutanota
    "tutanota.com", "tutanota.de", "tuta.io",
    # Zoho
    "zoho.com", "zohomail.com",
    # FastMail
    "fastmail.com", "fastmail.fm",
    # AOL
    "aol.com", "aim.com",
    # GMX / Mail.com
    "gmx.com", "gmx.de", "gmx.fr", "gmx.net", "mail.com",
    # French ISPs
    "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr", "laposte.net",
    "bbox.fr", "numericable.fr",
    # German ISPs
    "t-online.de", "web.de",
    # Other
    "yandex.com", "yandex.ru", "mail.ru", "inbox.lv",
    "hey.com", "pm.me", "posteo.de", "mailbox.org",
}

REMEDIATION_LINKS = {
    "spotify": "https://www.spotify.com/account/security/",
    "amazon": "https://www.amazon.com/gp/css/account/info/view.html",
    "github": "https://github.com/settings/security",
    "reddit": "https://www.reddit.com/prefs/update/",
    "steam": "https://store.steampowered.com/account/",
    "keybase": "https://keybase.io/account",
    "google": "https://myaccount.google.com/security",
    "facebook": "https://www.facebook.com/settings?tab=security",
    "twitter": "https://twitter.com/settings/security",
    "linkedin": "https://www.linkedin.com/psettings/sign-in-and-security",
    "instagram": "https://www.instagram.com/accounts/privacy_and_security/",
    "tiktok": "https://www.tiktok.com/setting",
    "pinterest": "https://www.pinterest.com/settings/security/",
    "youtube": "https://myaccount.google.com/security",
    "discord": "https://discord.com/channels/@me",
    "gitlab": "https://gitlab.com/-/profile/account",
    "medium": "https://medium.com/me/settings/security",
    "tumblr": "https://www.tumblr.com/settings/account",
}


class RiskAssessor:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        # Count by severity
        critical = len([f for f in findings if f.severity == "critical"])
        high = len([f for f in findings if f.severity == "high"])
        medium = len([f for f in findings if f.severity == "medium"])
        low = len([f for f in findings if f.severity == "low"])
        info = len([f for f in findings if f.severity == "info"])

        # Generate risk level
        if critical > 0 or high > 3:
            risk_level = "CRITICAL"
            summary = "This identity has critical exposure requiring immediate action."
        elif high > 0 or medium > 5:
            risk_level = "HIGH"
            summary = "This identity has significant exposure that should be addressed."
        elif medium > 0:
            risk_level = "MODERATE"
            summary = "This identity has moderate exposure with room for improvement."
        else:
            risk_level = "LOW"
            summary = "This identity has minimal exposure."

        # Generate remediation priorities
        remediations = self._generate_remediations(findings)

        # Generate executive summary narrative
        executive_summary = self._generate_executive_summary(
            findings, risk_level, critical, high, medium, low, info, remediations,
        )

        results.append({
            "title": f"Risk Assessment: {risk_level}",
            "description": summary,
            "category": "intelligence",
            "severity": "info",
            "data": {
                "analyzer": "risk_assessor",
                "risk_level": risk_level,
                "summary": summary,
                "executive_summary": executive_summary,
                "stats": {
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "info": info,
                    "total": len(findings),
                },
                "remediations": remediations,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "verified": True,
        })

        return results

    def _generate_remediations(self, findings: list) -> list:
        """Generate prioritized remediation actions from findings."""
        remediations = []
        seen_actions = set()

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            findings,
            key=lambda x: severity_order.get(x.severity, 5),
        )

        for f in sorted_findings:
            if f.severity not in ("critical", "high", "medium"):
                continue

            remediation = self._get_remediation(f)
            if remediation:
                action_key = remediation["action"]
                if action_key not in seen_actions:
                    seen_actions.add(action_key)
                    remediations.append(remediation)

        return remediations[:10]

    def _get_remediation(self, finding) -> dict | None:
        """Map finding to actionable remediation."""
        data = finding.data or {}
        title_lower = (finding.title or "").lower()
        category = finding.category or ""

        # Breach with passwords → change password
        if category == "breach" and finding.severity in ("critical", "high"):
            data_classes = data.get("DataClasses") or data.get("data_classes") or []
            has_password = any("password" in dc.lower() for dc in data_classes)
            if has_password:
                return {
                    "action": "Change leaked passwords",
                    "priority": "critical",
                    "finding": finding.title,
                    "steps": [
                        "Change password immediately on the affected service",
                        "Change password on any other service using the same password",
                        "Enable 2FA/MFA on all accounts",
                        "Use a password manager for unique passwords",
                        "Check for unauthorized access to the account",
                    ],
                }
            return {
                "action": f"Review breach exposure: {finding.title}",
                "priority": "high",
                "finding": finding.title,
                "steps": [
                    "Check if credentials were exposed",
                    "Change password as a precaution",
                    "Enable 2FA/MFA",
                    "Monitor for suspicious activity",
                ],
            }

        # Social account → secure it
        if category == "social_account":
            platform = (
                data.get("platform")
                or data.get("network")
                or data.get("service")
                or ""
            ).lower()
            link = REMEDIATION_LINKS.get(platform)
            steps = [
                "Enable 2FA/MFA",
                "Review connected apps and revoke unused ones",
                "Check privacy settings",
                "Remove account if unused",
            ]
            if link:
                steps.insert(0, f"Go to security settings: {link}")

            return {
                "action": f"Secure {platform or 'account'}: {finding.title}",
                "priority": "medium",
                "finding": finding.title,
                "link": link,
                "steps": steps,
            }

        # Weak email security — skip if managed domain
        if "dmarc" in title_lower or "spf" in title_lower or "email security" in title_lower:
            domain = data.get("domain", "")
            if domain.lower() in MANAGED_DOMAINS:
                return None  # SaaS domain — user cannot fix DNS
            if finding.severity in ("critical", "high", "medium"):
                return {
                    "action": "Strengthen email domain security",
                    "priority": "high",
                    "finding": finding.title,
                    "steps": [
                        "Add DMARC record with p=reject policy",
                        "Configure SPF with strict -all",
                        "Add DKIM signing for outbound email",
                        "Monitor DMARC reports for spoofing attempts",
                    ],
                }

        # Missing security headers
        if "security headers" in title_lower:
            return {
                "action": f"Add security headers to {data.get('domain', 'domain')}",
                "priority": "medium",
                "finding": finding.title,
                "steps": [
                    "Add Strict-Transport-Security header",
                    "Add Content-Security-Policy header",
                    "Add X-Frame-Options: DENY",
                    "Add X-Content-Type-Options: nosniff",
                    "Add Referrer-Policy: strict-origin-when-cross-origin",
                ],
            }

        # Username reuse
        if "reuse" in title_lower or "proliferation" in title_lower:
            return {
                "action": "Reduce username reuse across platforms",
                "priority": "medium",
                "finding": finding.title,
                "steps": [
                    "Use different usernames on different platforms",
                    "Delete unused accounts to reduce attack surface",
                    "Use email aliases for different services",
                    "Enable 2FA on all accounts with the same username",
                ],
            }

        return None  # no remediation for this finding type

    def _generate_executive_summary(
        self, findings, risk_level, critical, high, medium, low, info, remediations,
    ) -> str:
        """Generate a dynamic narrative executive summary from findings."""
        total = len(findings)
        parts = []

        # Opening
        parts.append(f"This identity has {total} data points across the open internet.")

        # Breach summary
        breaches = [f for f in findings if f.category == "breach"]
        if breaches:
            breach_names = []
            has_passwords = False
            for b in breaches:
                breach_names.append(b.title.replace("Breach: ", "").replace("Data breach: ", ""))
                data_classes = (b.data or {}).get("DataClasses") or (b.data or {}).get("data_classes") or []
                if any("password" in dc.lower() for dc in data_classes):
                    has_passwords = True
            parts.append(
                f"Found in {len(breaches)} data breach{'es' if len(breaches) > 1 else ''}"
                f" ({', '.join(breach_names[:3])}{'...' if len(breach_names) > 3 else ''})."
                + (" Credentials (passwords) were exposed." if has_passwords else "")
            )

        # Social footprint
        socials = [f for f in findings if f.category == "social_account"]
        if socials:
            platforms = []
            for s in socials:
                p = (s.data or {}).get("platform") or (s.data or {}).get("network") or (s.data or {}).get("service") or ""
                if p:
                    platforms.append(p.capitalize())
            if platforms:
                parts.append(
                    f"Active on {len(socials)} platform{'s' if len(socials) > 1 else ''}"
                    f" ({', '.join(platforms[:5])}{'...' if len(platforms) > 5 else ''})."
                )

        # Email domain
        email_domains = set()
        for f in findings:
            if f.indicator_type == "email" and f.indicator_value and "@" in f.indicator_value:
                domain = f.indicator_value.split("@")[1].lower()
                email_domains.add(domain)
        managed = [d for d in email_domains if d in MANAGED_DOMAINS]
        custom = [d for d in email_domains if d not in MANAGED_DOMAINS]
        if managed:
            parts.append(f"Email hosted on managed provider ({', '.join(managed)}) — DNS is provider-controlled.")
        if custom:
            parts.append(f"Custom domain{'s' if len(custom) > 1 else ''} detected: {', '.join(custom)}.")

        # Geolocation
        geo_findings = [f for f in findings if f.category == "geolocation" and f.module not in ("geoip", "maxmind_geo")]
        if geo_findings:
            locations = set()
            for g in geo_findings:
                loc = (g.data or {}).get("city") or (g.data or {}).get("country")
                if loc:
                    locations.add(loc)
            if locations:
                parts.append(f"Geolocation signals from: {', '.join(list(locations)[:3])}.")

        # Risk closing
        if critical > 0:
            parts.append(f"{critical} critical finding{'s' if critical > 1 else ''} require{'s' if critical == 1 else ''} immediate attention.")
        elif high > 0:
            parts.append(f"{high} high-severity finding{'s' if high > 1 else ''} should be addressed promptly.")
        elif medium > 0:
            parts.append(f"{medium} medium-severity finding{'s' if medium > 1 else ''} identified for review.")
        else:
            parts.append("No high-severity issues detected.")

        if remediations:
            parts.append(f"{len(remediations)} remediation action{'s' if len(remediations) > 1 else ''} recommended.")

        return " ".join(parts)
