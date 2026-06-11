"""HudsonRock Cavalier infostealer intelligence (S269).

Free, key-less OSINT-tools endpoints (cavalier.hudsonrock.com/api/json/v2/osint-tools).
Checks whether an email or domain appears in infostealer-compromised machine logs
(30M+ machines). API-based — not bare-HTTP scraping — so immune to the 2026
Cloudflare/SPA degradation that killed Holehe/Maigret.

SCOPING (HARD RULE) — EXPOSURE METADATA ONLY. The platform must NEVER ingest or store
cleartext credentials. Doing so would make xposeTIP a credential honeypot (security
liability + RGPD nightmare + makes us a breach target). The live response literally
contains `top_passwords` / `top_logins` (cleartext creds) plus `ip` / `malware_path`
(PII) — these are HARD-DROPPED at parse time and an allow-list (_SAFE_*) governs what
may enter `data`. We store WHETHER and HOW MUCH someone is exposed, never WHAT leaked.

Real per-stealer shape (sampled live, S269): antiviruses[], computer_name,
date_compromised, operating_system, total_corporate_services, total_user_services,
+ the forbidden ip/malware_path/top_logins/top_passwords. No stealer_family/date_uploaded.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools"
REQUEST_TIMEOUT = 15
THROTTLE_S = 10                          # observed-safe rate (1 req / 10s)
REDIS_DISABLE_KEY = "hudsonrock:disabled"
REDIS_DISABLE_TTL = 3600

# Allow-list — the ONLY per-stealer fields permitted into `data` (everything else,
# incl. top_passwords/top_logins/ip/malware_path, is dropped by omission).
_SAFE_STEALER_FIELDS = {
    "date_compromised", "operating_system", "computer_name", "antiviruses",
    "total_corporate_services", "total_user_services",
}
# Defensive denylist — fields we explicitly refuse even if upstream renames/nests them.
_CRED_FIELDS = {
    "top_passwords", "top_logins", "passwords", "password", "logins", "login",
    "credentials", "cookies", "cookie", "token", "tokens", "cleartext",
    "ip", "malware_path", "url", "urls",
}


def _redis():
    from api.config import settings
    import redis
    return redis.from_url(settings.REDIS_URL)


def _is_disabled() -> bool:
    try:
        return _redis().exists(REDIS_DISABLE_KEY) > 0
    except Exception:
        return False


def _disable():
    try:
        _redis().setex(REDIS_DISABLE_KEY, REDIS_DISABLE_TTL, "blocked")
        logger.warning("HudsonRock disabled for %ds after upstream error", REDIS_DISABLE_TTL)
    except Exception:
        pass


def _safe_stealer(stealer: dict) -> dict:
    """Allow-list ONLY — exposure metadata, never a credential or PII field."""
    if not isinstance(stealer, dict):
        return {}
    out = {}
    for k, v in stealer.items():
        if k in _CRED_FIELDS or k not in _SAFE_STEALER_FIELDS:
            continue  # hard-drop: creds/PII and anything not explicitly allow-listed
        out[k] = v
    return out


def search_hudsonrock(email: str | None = None, domain: str | None = None) -> list[dict]:
    if _is_disabled() or (not email and not domain):
        return []
    if email:
        seed, ind_type = email, "infostealer_exposure"
        url, params = f"{BASE}/search-by-email", {"email": email}
    else:
        seed, ind_type = domain, "infostealer_exposure"
        url, params = f"{BASE}/search-by-domain", {"domain": domain}
    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        time.sleep(THROTTLE_S)
        if r.status_code == 429:
            _disable()
            return []
        if r.status_code != 200:
            logger.warning("hudsonrock HTTP %d for %s", r.status_code, str(seed)[:60])
            return []
        body = r.json() or {}
    except Exception as e:
        logger.warning("hudsonrock failed for %s: %s", str(seed)[:60], e)
        _disable()
        return []

    stealers = body.get("stealers", []) or []
    if not stealers:
        return []  # not compromised → honest empty (false-negative safe)

    safe = [_safe_stealer(s) for s in stealers]
    dates = [s.get("date_compromised") for s in safe if s.get("date_compromised")]
    oses = sorted({s.get("operating_system") for s in safe if s.get("operating_system")})
    # counts of EXPOSED SERVICES (how many sites) — NOT the credentials of those sites.
    corp_services = sum(int(s.get("total_corporate_services") or 0) for s in safe)
    user_services = sum(int(s.get("total_user_services") or 0) for s in safe)

    data = {
        "compromised": True,
        "log_count": len(stealers),                       # number of infected machines/logs
        "exposed_corporate_services": corp_services,      # COUNT only
        "exposed_user_services": user_services,           # COUNT only
        "operating_systems": oses,
        "first_compromised": min(dates) if dates else None,
        "last_compromised": max(dates) if dates else None,
        "source": "hudsonrock_cavalier",
        "summary": str(body.get("message") or "")[:300],
        # NO cleartext credentials, NO ip, NO malware_path — ever.
    }

    return [{
        "module": "hudsonrock_search",
        "category": "breach",                              # exposure, breach-class finding
        "indicator_type": ind_type,
        "indicator_value": seed,
        "title": f"Infostealer exposure: {seed} ({len(stealers)} log{'s' if len(stealers) != 1 else ''})",
        "description": (
            f"Found in {len(stealers)} infostealer-compromised machine log(s); "
            f"{corp_services} corporate + {user_services} user services exposed. "
            f"Credentials NOT stored (exposure metadata only)."
        )[:1000],
        "data": data,
        "confidence": 0.95,                                # high-fidelity forensic source
        "severity": "high",
        "source": "hudsonrock",
    }]
