"""Extract secondary identifiers (phone numbers, crypto wallets) from findings.

Runs as step A1.5 in finalize_scan. Stores results in target.profile_data
for downstream enrichment by secondary_identifier_enricher (step A1.6).
"""
import re
import logging

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{6,15}')

PHONE_SKIP_MODULES = {
    "dns_deep", "whois_lookup", "geoip", "maxmind_geo",
    "virustotal", "shodan", "leaked_domains", "domain_analyzer",
    "crt_sh", "rdap_domain",
}

BTC_REGEX = re.compile(
    r'\b(1[a-km-zA-HJ-NP-Z1-9]{25,34}'
    r'|3[a-km-zA-HJ-NP-Z1-9]{25,34}'
    r'|bc1[a-zA-HJ-NP-Z0-9]{25,90})\b'
)
ETH_REGEX = re.compile(r'\b(0x[a-fA-F0-9]{40})\b')


def extract_secondary_identifiers(target, findings, session):
    """Extract phone numbers and crypto wallets from existing findings."""
    phones = _extract_phones(findings)
    wallets = _extract_wallets(findings)

    pd = dict(target.profile_data or {})
    changed = False

    if phones:
        pd["phones"] = phones
        changed = True
        logger.info("A1.5: Extracted %d phone(s) for target %s", len(phones), target.id)
    if wallets:
        pd["crypto_wallets"] = wallets
        changed = True
        logger.info("A1.5: Extracted %d wallet(s) for target %s", len(wallets), target.id)

    if changed:
        target.profile_data = pd
        session.commit()


def _extract_phones(findings):
    """Extract and validate phone numbers from finding data."""
    try:
        import phonenumbers
    except ImportError:
        logger.debug("A1.5: phonenumbers lib not installed, skipping phone extraction")
        return []

    raw_phones = set()
    for f in findings:
        if f.module in PHONE_SKIP_MODULES:
            continue
        # Search in finding data JSONB + description
        text_parts = []
        if f.data and isinstance(f.data, dict):
            text_parts.append(str(f.data))
        if f.description:
            text_parts.append(f.description)
        text = " ".join(text_parts)

        for match in PHONE_REGEX.findall(text):
            raw_phones.add(match.strip())

    valid_phones = []
    for raw in raw_phones:
        try:
            parsed = phonenumbers.parse(raw, None)
            if not phonenumbers.is_valid_number(parsed):
                continue
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            if len(e164.replace("+", "")) < 7:
                continue
            valid_phones.append(e164)
        except Exception:
            continue

    return list(set(valid_phones))[:10]


def _extract_wallets(findings):
    """Extract BTC and ETH wallet addresses from finding data."""
    wallets = []
    seen = set()

    for f in findings:
        text_parts = []
        if f.data and isinstance(f.data, dict):
            text_parts.append(str(f.data))
        if f.description:
            text_parts.append(f.description)
        text = " ".join(text_parts)

        for addr in BTC_REGEX.findall(text):
            if addr not in seen:
                seen.add(addr)
                wallets.append({"chain": "btc", "address": addr})

        for addr in ETH_REGEX.findall(text):
            addr_lower = addr.lower()
            if addr_lower not in seen:
                seen.add(addr_lower)
                wallets.append({"chain": "eth", "address": addr_lower})

    return wallets[:10]
