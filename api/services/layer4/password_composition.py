"""Password composition extractor (S270) — L1 entropy signal, extract-and-drop.

Takes a cleartext password ONLY in transit (from the HudsonRock parse), derives
coarse identifying-attribute CANDIDATES from its *shape*, and a salted reuse-hash for
cross-account linking. The cleartext is NEVER returned, logged, or persisted — this
module has no logging of the input and never puts the raw value in its output.

Honesty: candidates are COARSE / low-veracity (a 4-digit token may be a year or
random; a capitalised token may be a name or any word). They feed entropy as coarse
bits and resolution as low-confidence candidates — and are GATED from any
authoritative cascade (S191 lesson: a wrong name must not reach SEC EDGAR /
Companies House). Every candidate carries source + veracity="coarse" so consumers
down-weight it.
"""
import datetime
import hashlib
import re

_YEAR_LO = 1940
_YEAR_HI = datetime.date.today().year

# minimal stop-set so we don't emit "Password", "Admin", "Welcome" as a name
_COMMON = {
    "password", "admin", "welcome", "login", "qwerty", "letmein", "monkey",
    "dragon", "master", "root", "secret", "summer", "winter", "spring",
}

# host-name device words to strip before recovering a name from computer_name
_HOST_STRIP = re.compile(r"^(desktop|laptop|pc|win|user|admin|home)[-_]?|[-_]?(pc|laptop|desktop)$", re.I)
_DEVICE_WORDS = {
    "macbook", "imac", "windows", "linux", "pc", "laptop", "desktop",
    # S273b — manufacturer brands + model lines that leak as fake names from
    # hostnames (DELL-7420 → "Dell"). Non-exhaustive by design: the hostname path
    # stays a coarse/gated signal; this just kills the obvious "calling someone Dell".
    "dell", "hp", "lenovo", "asus", "acer", "msi", "samsung", "lg", "sony",
    "toshiba", "fujitsu", "huawei", "microsoft", "apple", "gigabyte", "razer",
    "compaq", "medion", "packard", "bell",
    "latitude", "inspiron", "vostro", "precision", "optiplex", "alienware", "xps",
    "thinkpad", "ideapad", "thinkcentre", "legion", "yoga",
    "pavilion", "elitebook", "probook", "spectre", "envy", "omen",
    "zenbook", "vivobook", "rog", "tuf",
    "surface", "workstation", "server",
}


def extract_composition(password: str, salt: str) -> dict:
    """Return {candidates: [...], reuse_hash: str}. The cleartext is NEVER emitted —
    only derived shape candidates + a salted hash leave this function."""
    out = {"candidates": [], "reuse_hash": None}
    if not password or len(password) < 4:
        return out

    # 1) salted reuse-hash (cross-account linking only) — never the cleartext.
    out["reuse_hash"] = hashlib.sha256((str(salt) + password).encode("utf-8")).hexdigest()

    # 2) candidate year — one 4-digit token in a plausible DOB/anniversary range.
    for tok in re.findall(r"(?<!\d)(\d{4})(?!\d)", password):
        y = int(tok)
        if _YEAR_LO <= y <= _YEAR_HI:
            out["candidates"].append({
                "attribute": "candidate_year", "value": y,
                "veracity": "coarse", "source": "password_composition",
                "note": "4-digit token in plausible DOB/anniversary range",
            })
            break  # one is enough; avoid noise

    # 3) candidate name — one capitalised, non-dictionary alpha token (>=3 chars).
    for tok in re.findall(r"[A-Z][a-z]{2,}", password):
        if tok.lower() in _COMMON:
            continue
        out["candidates"].append({
            "attribute": "candidate_name", "value": tok,
            "veracity": "coarse", "source": "password_composition",
            "note": "capitalised non-dictionary token — pet/person/place candidate",
        })
        break

    return out


def extract_hostname_name(computer_name: str | None) -> list[dict]:
    """Recover the name signal from a stealer-log host name (DESKTOP-NABIL,
    Johns-MacBook) as a COARSE candidate_name; the raw host name is then dropped by
    the S269b allow-list. Catches all-caps tokens the password regex misses.
    Returns [] on no signal."""
    if not computer_name or len(computer_name) < 3:
        return []
    base = _HOST_STRIP.sub("", computer_name.strip())
    base = re.sub(r"[-_]?(macbook|imac|pc|laptop|desktop)s?$", "", base, flags=re.I)
    for tok in re.findall(r"[A-Za-z]{3,}", base):
        if tok.lower() in _COMMON or tok.lower() in _DEVICE_WORDS:
            continue
        return [{
            "attribute": "candidate_name", "value": tok.capitalize(),
            "veracity": "coarse", "source": "hostname_composition",
            "note": "name token recovered from stealer-log host name",
        }]
    return []
