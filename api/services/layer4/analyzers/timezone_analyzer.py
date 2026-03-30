"""TimezoneAnalyzer — Infer probable timezone from activity timestamps.

Principle: humans sleep. The 4-6 hour window with the LEAST activity
reveals the UTC offset. If the quiet window is 01:00-06:00 UTC,
the user is likely in UTC+0 to UTC+2. If it's 17:00-22:00 UTC,
they're likely in UTC+8 to UTC+10 (sleeping at 01:00-06:00 local).
"""
import logging
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)

_OFFSET_TO_REGIONS = {
    -12: ["Baker Island"],
    -11: ["American Samoa", "Niue"],
    -10: ["Hawaii", "Cook Islands"],
    -9: ["Alaska"],
    -8: ["US Pacific", "Tijuana"],
    -7: ["US Mountain", "Arizona"],
    -6: ["US Central", "Mexico City"],
    -5: ["US Eastern", "Colombia", "Peru"],
    -4: ["Atlantic", "Venezuela", "Bolivia", "Chile"],
    -3: ["Argentina", "Brazil (East)", "Uruguay"],
    -2: ["Mid-Atlantic"],
    -1: ["Azores", "Cape Verde"],
    0: ["UK", "Portugal", "Iceland", "Ghana", "Morocco"],
    1: ["Western Europe", "France", "Germany", "Spain", "Italy", "Netherlands", "Belgium", "Luxembourg"],
    2: ["Eastern Europe", "Finland", "Romania", "Greece", "Turkey", "Egypt", "South Africa", "Israel"],
    3: ["Moscow", "Saudi Arabia", "Iraq", "Kenya", "Qatar"],
    4: ["UAE", "Oman", "Georgia", "Azerbaijan"],
    5: ["Pakistan", "Uzbekistan", "Maldives"],
    6: ["Bangladesh", "Kazakhstan", "Kyrgyzstan"],
    7: ["Thailand", "Vietnam", "Indonesia (West)", "Cambodia"],
    8: ["China", "Singapore", "Malaysia", "Philippines", "Taiwan", "Hong Kong"],
    9: ["Japan", "South Korea"],
    10: ["Australia (East)", "Papua New Guinea"],
    11: ["Solomon Islands", "New Caledonia"],
    12: ["New Zealand", "Fiji"],
    13: ["Tonga", "Samoa"],
    14: ["Line Islands"],
}

_OFFSET_COUNTRY_HINTS = {
    -8: ["US"], -7: ["US"], -6: ["US", "MX"], -5: ["US", "CO", "PE"],
    -3: ["AR", "BR"], 0: ["GB", "PT", "IS"],
    1: ["FR", "DE", "ES", "IT", "NL", "BE", "LU", "AT", "CH", "SE", "NO", "DK", "PL", "CZ"],
    2: ["FI", "RO", "GR", "TR", "EG", "ZA", "IL", "UA"],
    3: ["RU", "SA", "KE"], 4: ["AE", "OM", "GE"],
    5: ["PK", "UZ"], 6: ["BD", "KZ"],
    7: ["TH", "VN", "ID"], 8: ["CN", "SG", "MY", "PH", "TW", "HK"],
    9: ["JP", "KR"], 10: ["AU"], 12: ["NZ"],
}

_TS_FIELDS = [
    "created_at", "createdAt", "created", "joined", "last_seen",
    "last_activity", "last_online", "member_since", "joined_date",
    "seenAt", "updated_at", "created_time",
]

_SKIP_MODULES = {"geoip", "maxmind_geo", "dns_deep", "whois_lookup",
                 "domain_analyzer", "crt_sh", "dns_resolver", "email_dns"}


def analyze_timezone(findings: list) -> dict | None:
    """Analyze activity timestamps from findings to infer timezone."""
    hours_utc = []

    for f in findings:
        data = f.data if isinstance(f.data, dict) else {}
        source = getattr(f, "module", "") or ""
        if source in _SKIP_MODULES:
            continue

        sources = [data]
        if isinstance(data.get("extracted"), dict):
            sources.append(data["extracted"])

        for d in sources:
            for field in _TS_FIELDS:
                val = d.get(field)
                if val is None:
                    continue
                hour = _extract_hour_utc(val)
                if hour is not None:
                    hours_utc.append(hour)

    if len(hours_utc) < 5:
        return None

    # Build hourly distribution
    hour_counts = Counter(hours_utc)
    distribution = {h: hour_counts.get(h, 0) for h in range(24)}
    total = sum(distribution.values())

    # Find best UTC offset by maximizing daytime activity ratio
    best_offset = 0
    best_score = -1

    for offset in range(-12, 15):
        local_counts = {}
        for utc_hour, count in distribution.items():
            local_hour = (utc_hour + offset) % 24
            local_counts[local_hour] = local_counts.get(local_hour, 0) + count

        daytime_activity = sum(local_counts.get(h, 0) for h in range(8, 24))
        score = daytime_activity / total if total > 0 else 0

        if score > best_score:
            best_score = score
            best_offset = offset

    # Find sleep window (quietest 5h block in UTC)
    sleep_start = 0
    min_sleep_activity = float("inf")
    for start in range(24):
        window_sum = sum(distribution.get((start + i) % 24, 0) for i in range(5))
        if window_sum < min_sleep_activity:
            min_sleep_activity = window_sum
            sleep_start = start
    sleep_end = (sleep_start + 5) % 24

    # Compute confidence
    if total > 0:
        sleep_ratio = min_sleep_activity / total
        confidence = max(0.0, min(1.0, 1.0 - (sleep_ratio * 4)))
    else:
        confidence = 0.0

    sample_bonus = min(0.2, len(hours_utc) / 100)
    confidence = min(1.0, confidence + sample_bonus)

    if best_score < 0.6:
        confidence *= 0.5

    regions = _OFFSET_TO_REGIONS.get(best_offset, [f"UTC{best_offset:+d}"])
    country_hints = _OFFSET_COUNTRY_HINTS.get(best_offset, [])

    return {
        "utc_offset": best_offset,
        "confidence": round(confidence, 2),
        "regions": regions,
        "country_hints": country_hints,
        "hourly_distribution": distribution,
        "sleep_window": (sleep_start, sleep_end),
        "sample_count": len(hours_utc),
        "daytime_score": round(best_score, 3),
    }


def _extract_hour_utc(value) -> int | None:
    """Extract UTC hour from various timestamp formats."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            if value > 1e12:
                dt = datetime.utcfromtimestamp(value / 1000)
            elif value > 1e8:
                dt = datetime.utcfromtimestamp(value)
            else:
                return None
            return dt.hour
        except (OSError, ValueError):
            return None

    if not isinstance(value, str):
        return None

    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(value[:30], fmt)
            return dt.hour
        except (ValueError, IndexError):
            continue

    return None
