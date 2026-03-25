"""Remediation engine — generates prioritized actions from profile data."""


def generate_remediation(profile: dict) -> list[tuple[str, str, str]]:
    """Return list of (priority, action, detail) tuples.

    priority: 'high', 'medium', 'low'
    """
    actions: list[tuple[str, str, str]] = []

    email_security = profile.get("email_security") or {}
    breach_summary = profile.get("breach_summary") or {}
    social_profiles = profile.get("social_profiles") or []
    usernames = profile.get("usernames") or []
    fingerprint = profile.get("fingerprint") or {}
    timeline_events = fingerprint.get("timeline_events") or []

    # --- HIGH PRIORITY ---

    # Email security gaps
    if email_security and not email_security.get("dkim"):
        actions.append((
            "high",
            "Enable DKIM on email domain",
            "Improves email authentication and prevents spoofing",
        ))
    if email_security and not email_security.get("dmarc"):
        actions.append((
            "high",
            "Enable DMARC on email domain",
            "Prevents unauthorized use of your email domain",
        ))

    # Breaches
    breach_count = breach_summary.get("count", 0)
    if breach_count > 0:
        breach_names = [
            e.get("label", "Unknown")
            for e in timeline_events
            if e.get("type") == "breach"
        ]
        if breach_names:
            names_str = ", ".join(breach_names[:5])
            if len(breach_names) > 5:
                names_str += f" (+{len(breach_names) - 5} more)"
            actions.append((
                "high",
                f"Review and change passwords for {len(breach_names)} breached services",
                f"Affected: {names_str}",
            ))
        else:
            actions.append((
                "high",
                f"Review {breach_count} breach exposures",
                "Change passwords on all affected services",
            ))

    if breach_summary.get("credentials_leaked"):
        actions.append((
            "high",
            "Credential leak detected — immediate password rotation required",
            "At least one breach includes plaintext or hashed credentials",
        ))

    # 2FA on high-value platforms
    high_value = {"github", "gitlab", "reddit", "steam", "twitter", "google", "facebook"}
    hv_accounts = [
        p for p in social_profiles
        if (p.get("platform") or "").lower() in high_value
    ]
    if hv_accounts:
        platforms = ", ".join(p.get("platform", "") for p in hv_accounts[:5])
        actions.append((
            "high",
            f"Enable 2FA on {len(hv_accounts)} high-value platforms",
            f"Platforms: {platforms}",
        ))

    # --- MEDIUM PRIORITY ---

    # Username reuse
    username_values = [u.get("value", "").lower() for u in usernames]
    platform_usernames: dict[str, list[str]] = {}
    for sp in social_profiles:
        uname = (sp.get("username") or "").lower()
        if uname:
            platform_usernames.setdefault(uname, []).append(sp.get("platform", ""))
    reused = {u: ps for u, ps in platform_usernames.items() if len(ps) >= 2}
    if reused:
        top_reused = list(reused.keys())[:3]
        actions.append((
            "medium",
            f"Reduce username reuse ({len(reused)} shared usernames)",
            f"Most reused: {', '.join(top_reused)}",
        ))

    # Low-value account cleanup
    low_value = {"roblox", "myanimelist", "mixcloud", "soundcloud", "duolingo", "lichess"}
    lv_accounts = [
        p for p in social_profiles
        if (p.get("platform") or "").lower() in low_value
    ]
    if lv_accounts:
        platforms = ", ".join(p.get("platform", "") for p in lv_accounts[:5])
        actions.append((
            "medium",
            f"Audit {len(lv_accounts)} low-value accounts for deletion",
            f"Consider removing: {platforms}",
        ))

    # Public exposure
    axes = fingerprint.get("axes") or {}
    if axes.get("public_exposure", 0) >= 0.5:
        actions.append((
            "medium",
            "High public exposure detected",
            "Review publicly visible personal information and limit unnecessary disclosures",
        ))

    # --- LOW PRIORITY ---

    actions.append((
        "low",
        "Set up breach monitoring alerts for this email",
        "Get notified when new breaches expose this identity",
    ))

    if len(social_profiles) > 20:
        actions.append((
            "low",
            f"Review {len(social_profiles)} active accounts",
            "Large digital footprint increases attack surface",
        ))

    return actions
