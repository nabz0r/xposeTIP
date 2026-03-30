"""GeoConsistencyAnalyzer — Cross-correlate all geographic signals.

Sources (by decreasing reliability):
  1. Operator ground truth (country_code)       weight: 1.0
  2. Self-reported location (scraper profiles)   weight: 0.8
  3. Timezone inference (activity timestamps)    weight: 0.5
  4. Nationalize (name-based prediction)         weight: 0.3
  5. Language hints (Duolingo from_language)      weight: 0.3
  6. GeoIP (mail server IP location)             weight: 0.1
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_LANG_COUNTRY_HINTS = {
    "fr": ["FR", "BE", "CH", "LU", "CA"],
    "de": ["DE", "AT", "CH", "LU"],
    "es": ["ES", "MX", "AR", "CO"],
    "pt": ["BR", "PT"],
    "it": ["IT", "CH"],
    "nl": ["NL", "BE"],
    "ja": ["JP"],
    "ko": ["KR"],
    "zh": ["CN", "TW", "HK", "SG"],
    "ru": ["RU", "UA", "BY", "KZ"],
    "ar": ["EG", "SA", "AE", "MA", "DZ", "TN", "IQ", "JO", "LB"],
    "tr": ["TR"],
    "pl": ["PL"],
    "sv": ["SE"],
    "da": ["DK"],
    "no": ["NO"],
    "fi": ["FI"],
    "cs": ["CZ"],
    "ro": ["RO"],
    "hu": ["HU"],
    "el": ["GR", "CY"],
    "uk": ["UA"],
    "he": ["IL"],
    "hi": ["IN"],
    "bn": ["BD", "IN"],
    "th": ["TH"],
    "vi": ["VN"],
    "id": ["ID"],
    "ms": ["MY"],
    "tl": ["PH"],
}

_COUNTRY_NAME_TO_CODE = {
    "united states": "US", "united kingdom": "GB", "france": "FR",
    "germany": "DE", "spain": "ES", "italy": "IT", "netherlands": "NL",
    "belgium": "BE", "luxembourg": "LU", "switzerland": "CH",
    "austria": "AT", "sweden": "SE", "norway": "NO", "denmark": "DK",
    "finland": "FI", "ireland": "IE", "portugal": "PT", "poland": "PL",
    "czech republic": "CZ", "czechia": "CZ", "romania": "RO",
    "hungary": "HU", "greece": "GR", "turkey": "TR", "ukraine": "UA",
    "russia": "RU", "canada": "CA", "mexico": "MX", "brazil": "BR",
    "argentina": "AR", "colombia": "CO", "chile": "CL", "peru": "PE",
    "india": "IN", "china": "CN", "japan": "JP", "south korea": "KR",
    "australia": "AU", "new zealand": "NZ", "singapore": "SG",
    "malaysia": "MY", "indonesia": "ID", "philippines": "PH",
    "thailand": "TH", "vietnam": "VN", "pakistan": "PK",
    "bangladesh": "BD", "sri lanka": "LK", "nepal": "NP",
    "saudi arabia": "SA", "united arab emirates": "AE",
    "israel": "IL", "egypt": "EG", "south africa": "ZA",
    "nigeria": "NG", "kenya": "KE", "morocco": "MA", "tunisia": "TN",
    "algeria": "DZ", "ghana": "GH", "hong kong": "HK", "taiwan": "TW",
    "qatar": "QA", "kuwait": "KW", "bahrain": "BH", "oman": "OM",
    "jordan": "JO", "lebanon": "LB", "iraq": "IQ", "iran": "IR",
    "croatia": "HR", "serbia": "RS", "bulgaria": "BG",
    "slovakia": "SK", "slovenia": "SI", "estonia": "EE",
    "latvia": "LV", "lithuania": "LT", "iceland": "IS",
    "albania": "AL", "north macedonia": "MK", "montenegro": "ME",
    "bosnia and herzegovina": "BA", "moldova": "MD", "belarus": "BY",
    "georgia": "GE", "armenia": "AM", "azerbaijan": "AZ",
    "kazakhstan": "KZ", "uzbekistan": "UZ",
    "cambodia": "KH", "myanmar": "MM", "laos": "LA",
    "cuba": "CU", "venezuela": "VE", "ecuador": "EC",
    "uruguay": "UY", "paraguay": "PY", "bolivia": "BO",
    "costa rica": "CR", "panama": "PA", "dominican republic": "DO",
    "jamaica": "JM", "puerto rico": "PR",
    "cameroon": "CM", "ethiopia": "ET", "tanzania": "TZ",
    "uganda": "UG", "senegal": "SN", "angola": "AO",
    "zimbabwe": "ZW", "sudan": "SD", "ivory coast": "CI",
    "fiji": "FJ",
}

_US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee",
    "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming",
}

_SOURCE_WEIGHTS = {
    "ground_truth": 1.0,
    "self_reported": 0.8,
    "timezone": 0.5,
    "nationalize": 0.3,
    "language": 0.3,
    "geoip": 0.1,
}


def analyze_geo_consistency(profile: dict, findings: list, country_code: str = None) -> dict:
    """Cross-correlate all geographic signals and score consistency."""
    signals = []

    # Signal 1: Operator ground truth
    if country_code and isinstance(country_code, str) and len(country_code.strip()) == 2:
        cc = country_code.strip().upper()
        signals.append({
            "source": "Operator ground truth", "type": "ground_truth",
            "country_code": cc, "weight": _SOURCE_WEIGHTS["ground_truth"],
            "raw_value": cc,
        })

    # Signal 2: Self-reported locations
    seen_loc = set()
    for loc_entry in profile.get("user_locations", []):
        country_name = (loc_entry.get("country") or "").strip().lower()
        if not country_name:
            continue
        cc = _resolve_country_code(country_name)
        if cc and cc not in seen_loc:
            seen_loc.add(cc)
            signals.append({
                "source": loc_entry.get("source", "scraper"), "type": "self_reported",
                "country_code": cc, "weight": _SOURCE_WEIGHTS["self_reported"],
                "raw_value": loc_entry.get("value", country_name),
            })

    profile_loc = (profile.get("location") or "").strip().lower()
    if profile_loc:
        cc = _resolve_country_code(profile_loc)
        if cc and cc not in seen_loc:
            seen_loc.add(cc)
            signals.append({
                "source": "profile.location", "type": "self_reported",
                "country_code": cc, "weight": _SOURCE_WEIGHTS["self_reported"],
                "raw_value": profile.get("location"),
            })

    # Signal 3: Timezone inference
    tz = profile.get("timezone")
    if isinstance(tz, dict) and tz.get("confidence", 0) >= 0.3:
        for hint_cc in tz.get("country_hints", [])[:5]:
            signals.append({
                "source": f"Timezone UTC{tz['utc_offset']:+d}", "type": "timezone",
                "country_code": hint_cc.upper(),
                "weight": _SOURCE_WEIGHTS["timezone"] * tz["confidence"],
                "raw_value": f"UTC{tz['utc_offset']:+d}",
            })

    # Signal 4: Nationalize
    est = profile.get("identity_estimation", {})
    for nat in est.get("nationalities", [])[:3]:
        cc = (nat.get("country_code") or "").upper()
        prob = float(nat.get("probability", 0))
        if cc and prob >= 0.05:
            signals.append({
                "source": f"Nationalize ({prob:.0%})", "type": "nationalize",
                "country_code": cc, "weight": _SOURCE_WEIGHTS["nationalize"] * prob,
                "raw_value": f"{cc} ({prob:.0%})",
            })

    # Signal 5: Language hints
    for f in findings:
        data = f.data if isinstance(f.data, dict) else {}
        if (data.get("scraper") or "") != "duolingo_profile":
            continue
        extracted = data.get("extracted", {})
        if not isinstance(extracted, dict):
            continue
        from_lang = (extracted.get("from_language") or "").lower().strip()
        if from_lang and from_lang in _LANG_COUNTRY_HINTS:
            hints = _LANG_COUNTRY_HINTS[from_lang][:3]
            for hint_cc in hints:
                signals.append({
                    "source": f"Duolingo UI ({from_lang})", "type": "language",
                    "country_code": hint_cc,
                    "weight": _SOURCE_WEIGHTS["language"] / len(hints),
                    "raw_value": from_lang,
                })

    # Signal 6: GeoIP
    for f in findings:
        source = getattr(f, "module", "") or ""
        if source not in ("geoip", "maxmind_geo"):
            continue
        data = f.data if isinstance(f.data, dict) else {}
        country = (data.get("country") or data.get("countryCode") or "").strip()
        if country and len(country) >= 2:
            cc = _resolve_country_code(country.lower())
            if cc:
                signals.append({
                    "source": "GeoIP (mail server)", "type": "geoip",
                    "country_code": cc, "weight": _SOURCE_WEIGHTS["geoip"],
                    "raw_value": country,
                })

    # Voting
    if not signals:
        return {
            "primary_country": None, "primary_country_name": None,
            "confidence": 0.0, "consistency_score": 0.0,
            "signals": [], "country_votes": {}, "anomalies": [],
            "verdict": "No geographic signals available",
        }

    country_votes = defaultdict(float)
    country_sources = defaultdict(set)

    for sig in signals:
        cc = sig["country_code"]
        country_votes[cc] += sig["weight"]
        country_sources[cc].add(sig["type"])

    ranked = sorted(country_votes.items(), key=lambda x: -x[1])
    primary_cc = ranked[0][0]
    primary_score = ranked[0][1]
    total_weight = sum(v for _, v in ranked)

    # Consistency score
    concentration = primary_score / total_weight if total_weight > 0 else 0.0
    type_diversity_bonus = min(0.2, len(country_sources[primary_cc]) * 0.05)
    consistency_score = min(1.0, concentration + type_diversity_bonus)

    # Confidence
    has_ground_truth = "ground_truth" in country_sources[primary_cc]
    has_self_reported = "self_reported" in country_sources[primary_cc]

    confidence = consistency_score * 0.6
    if has_ground_truth:
        confidence += 0.3
    elif has_self_reported:
        confidence += 0.15
    confidence = min(1.0, confidence + min(0.15, len(signals) * 0.02))

    # Anomaly detection
    anomalies = []
    for sig in signals:
        if sig["country_code"] == primary_cc:
            continue
        if sig["type"] in ("ground_truth", "self_reported") and sig["weight"] >= 0.5:
            anomalies.append({
                "signal": sig["source"], "expected": primary_cc,
                "actual": sig["country_code"],
                "description": f"{sig['source']} says {sig['country_code']} but primary is {primary_cc}",
            })

    # Verdict
    n_countries = len(ranked)
    source_types = country_sources[primary_cc]
    if n_countries == 1:
        verdict = f"All signals point to {primary_cc}"
    elif consistency_score >= 0.8:
        verdict = f"Strong consensus on {primary_cc} ({len(source_types)} signal types agree)"
    elif consistency_score >= 0.5:
        runner_up = ranked[1][0] if len(ranked) > 1 else "?"
        verdict = f"Primary: {primary_cc}, secondary: {runner_up}"
    elif n_countries >= 3:
        top3 = ", ".join(cc for cc, _ in ranked[:3])
        verdict = f"Multi-jurisdictional: {top3}"
    else:
        verdict = f"Conflicting: {ranked[0][0]} vs {ranked[1][0] if len(ranked) > 1 else '?'}"

    if anomalies:
        verdict += f" ({len(anomalies)} anomal{'y' if len(anomalies) == 1 else 'ies'})"

    _CODE_TO_NAME = {v: k.title() for k, v in _COUNTRY_NAME_TO_CODE.items()}
    primary_name = _CODE_TO_NAME.get(primary_cc, primary_cc)

    return {
        "primary_country": primary_cc,
        "primary_country_name": primary_name,
        "confidence": round(confidence, 2),
        "consistency_score": round(consistency_score, 2),
        "signals": signals,
        "country_votes": dict(sorted(country_votes.items(), key=lambda x: -x[1])),
        "anomalies": anomalies,
        "verdict": verdict,
    }


def _resolve_country_code(value: str) -> str | None:
    """Resolve a country name, code, or alias to ISO alpha-2."""
    val = value.lower().strip()
    if len(val) == 2 and val.isalpha():
        return val.upper()
    if val in _COUNTRY_NAME_TO_CODE:
        return _COUNTRY_NAME_TO_CODE[val]

    try:
        from api.services.layer4.profile_aggregator import CITY_COORDS
        for city_key, city_data in CITY_COORDS.items():
            if city_key in val:
                country_name = city_data.get("country", "").lower()
                if country_name in _COUNTRY_NAME_TO_CODE:
                    return _COUNTRY_NAME_TO_CODE[country_name]
    except ImportError:
        pass

    if val in _US_STATES:
        return "US"

    return None
