"""Risk Assessor — final synthesis generating human-readable risk assessment.

Produces an overall risk level, remediation priorities, and actionable steps.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

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

        results.append({
            "title": f"Risk Assessment: {risk_level}",
            "description": summary,
            "category": "intelligence",
            "severity": "info",
            "data": {
                "analyzer": "risk_assessor",
                "risk_level": risk_level,
                "summary": summary,
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

        # Weak email security
        if "dmarc" in title_lower or "spf" in title_lower or "email security" in title_lower:
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

        return None
