"""S246 — GPG public-key scanner.

Looks the input email up on keys.openpgp.org (no auth, free). When a key is
present, emits:
  1. One `public_key` finding carrying the V4 fingerprint + linked emails
  2. One `email` finding per UID email that is NOT the input email — feeds
     the existing cascade so newly discovered emails get re-scanned

No `pgpy` dep (fragile on modern Python). Dearmor + base64 + a hand-rolled
V4 packet parser; fingerprint is best-effort, the `public_key` finding is
still emitted (without fingerprint) if packet parsing fails.

BFP impact: none directly. category="identity" sits outside the fingerprint
axes. The cascaded email findings widen the social/account footprint at
recompute → fingerprint enriches indirectly through the existing path.
"""
import base64
import hashlib
import logging
import re
import struct
from urllib.parse import quote

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(rb"[\w.+-]+@[\w-]+\.[\w.-]+")
_ARMOR_BEGIN = "-----BEGIN PGP PUBLIC KEY BLOCK-----"
_ARMOR_END = "-----END PGP PUBLIC KEY BLOCK-----"


_ARMOR_HEADER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*:")


def _dearmor(armored: str) -> bytes | None:
    """Strip armor headers + CRC checksum, base64-decode to raw packet bytes.

    Robust to leading blank line(s) before the headers (keys.openpgp.org
    inserts an extra newline right after the BEGIN marker) and to keys
    that omit the armor-header block entirely.
    """
    try:
        start = armored.index(_ARMOR_BEGIN) + len(_ARMOR_BEGIN)
        end = armored.index(_ARMOR_END, start)
    except ValueError:
        return None
    b64_lines = []
    for raw in armored[start:end].splitlines():
        line = raw.strip()
        if not line:
            continue
        if _ARMOR_HEADER_RE.match(line):  # Comment: / Version: / etc.
            continue
        if line.startswith("="):  # CRC-24 checksum line — not part of the data
            continue
        b64_lines.append(line)
    if not b64_lines:
        return None
    try:
        return base64.b64decode("".join(b64_lines))
    except Exception:
        return None


def _first_packet_body(data: bytes) -> bytes | None:
    """Return the body of the first PGP packet IF it is a Public-Key packet (tag 6).

    Handles both old- and new-format packet headers. Best-effort; returns None on
    anything unexpected so the caller can degrade gracefully.
    """
    if not data or not (data[0] & 0x80):
        return None
    ctb = data[0]
    new_format = bool(ctb & 0x40)
    i = 1
    if new_format:
        tag = ctb & 0x3F
        if i >= len(data):
            return None
        l0 = data[i]; i += 1
        if l0 < 192:
            length = l0
        elif l0 < 224:
            if i >= len(data):
                return None
            length = ((l0 - 192) << 8) + data[i] + 192; i += 1
        elif l0 == 0xFF:
            if i + 4 > len(data):
                return None
            length = struct.unpack(">I", data[i:i + 4])[0]; i += 4
        else:
            return None  # partial body lengths unsupported (keys never use them here)
    else:
        tag = (ctb & 0x3C) >> 2
        ltype = ctb & 0x03
        nbytes = {0: 1, 1: 2, 2: 4}.get(ltype)
        if nbytes is None or i + nbytes > len(data):
            return None
        length = int.from_bytes(data[i:i + nbytes], "big"); i += nbytes
    if tag != 6:
        return None
    return data[i:i + length]


def _v4_fingerprint(data: bytes) -> str | None:
    """V4 key fingerprint = SHA1(0x99 || len(body, 2 bytes BE) || body), uppercase hex."""
    try:
        body = _first_packet_body(data)
        if not body or body[0] != 4:  # version byte must be 4
            return None
        prefix = b"\x99" + struct.pack(">H", len(body))
        return hashlib.sha1(prefix + body).hexdigest().upper()
    except Exception:
        return None


class GpgKeysScanner(BaseScanner):
    MODULE_ID = "gpg_keys"
    LAYER = 1
    CATEGORY = "identity"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        if not email or "@" not in email:
            return []  # keyserver lookup is email-only; skip username-only inputs

        url = f"https://keys.openpgp.org/vks/v1/by-email/{quote(email)}"
        armored = None
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers={"User-Agent": "xpose-tip"})
                if resp.status_code == 200 and _ARMOR_BEGIN in resp.text:
                    armored = resp.text
            except Exception:
                logger.debug("openpgp.org lookup failed for %s", email)

        if not armored:
            return []

        raw = _dearmor(armored)
        fingerprint = _v4_fingerprint(raw) if raw else None

        # Linked emails from cleartext UID packets
        linked = []
        if raw:
            for m in _EMAIL_RE.findall(raw):
                try:
                    em = m.decode("utf-8", "ignore").strip().lower()
                except Exception:
                    continue
                if em and em not in linked:
                    linked.append(em)

        results: list[ScanResult] = []

        # (1) The key itself — identity signal (NOT a risk → severity info)
        fp_disp = " ".join(fingerprint[i:i + 4] for i in range(0, len(fingerprint), 4)) if fingerprint else None
        other = [e for e in linked if e != email.lower()]
        desc = []
        if fingerprint:
            desc.append(f"Fingerprint {fp_disp}")
        if other:
            desc.append(f"{len(other)} linked email(s)")
        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="identity",
            severity="info",
            title="GPG public key (keys.openpgp.org)",
            description=". ".join(desc) if desc else "Published GPG public key found for this email",
            data={
                "source": "keys.openpgp.org",
                "fingerprint": fingerprint,
                "fingerprint_display": fp_disp,
                "linked_emails": other,
                "key_type": "GPG",
                "armored_len": len(armored),
            },
            url=url,
            indicator_value=fingerprint or f"gpg:{email.lower()}",
            indicator_type="public_key",
            verified=True,
        ))

        # (2) Linked emails (≠ input) → email Identity rows → existing cascade re-scans them
        for em in other:
            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="identity",
                severity="info",
                title=f"Email linked via GPG key: {em}",
                description="Discovered in a GPG public-key UID",
                data={"source": "keys.openpgp.org", "via_fingerprint": fingerprint},
                indicator_value=em,
                indicator_type="email",
                verified=True,
            ))

        return results
