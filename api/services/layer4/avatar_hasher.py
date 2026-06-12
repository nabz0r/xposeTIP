"""S286 — Perceptual avatar hashing (pHash) for cross-platform reuse detection.

Pure, stateless infra. For each real-photo avatar in profile['avatars'], download
the image, compute a 64-bit perceptual hash, and detect the same image reused
across platforms. ZERO entropy/BFP wiring (that's S287).

RGPD/CNPD framing — WE STORE THE PERCEPTUAL HASH, NEVER THE IMAGE. A pHash is an
image signature, NOT biometric data (art. 9 GDPR): no face analysis, no facial
template. That is what makes avatar-reuse defensible where face recognition is not.

Decision 0 (the false-positive trap): hash ONLY avatars with score_fn(url) >= 2
(real/unknown photos). Default avatars / identicons (score <= 1) are shared by
millions — two accounts with the Gravatar identicon are NOT the same person reusing
their picture. Same logic as the S283 free-mail GeoIP exclusion.
"""
import asyncio
import io
import logging

import httpx

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024   # avatars are small; a big file is a trap/error
HAMMING_THRESHOLD = 10              # of 64 bits — tolerates platform recompression,
                                    # rejects genuinely distinct images
MAX_AVATARS = 10                    # beyond this the reuse signal saturates
FETCH_CONCURRENCY = 5
FETCH_TIMEOUT = 8.0


async def _fetch_image_bytes(url: str, timeout: float = FETCH_TIMEOUT) -> bytes | None:
    """Download avatar bytes. Returns None on ANY failure — never raises. Caps size
    (streamed) so a hostile/huge file can't be pulled. A dead avatar is normal →
    debug log, never error."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    return None
                cl = resp.headers.get("content-length")
                if cl and cl.isdigit() and int(cl) > MAX_IMAGE_BYTES:
                    return None
                buf = bytearray()
                async for chunk in resp.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > MAX_IMAGE_BYTES:
                        return None
                return bytes(buf)
    except Exception as e:
        logger.debug("avatar fetch failed %s: %s", str(url)[:60], e)
        return None


def _compute_phash(img_bytes: bytes) -> str | None:
    """Perceptual hash (64-bit, DCT-based) as a 16-hex-char string. None if the
    bytes are not a valid image. Robust to the resize/recompression platforms apply."""
    try:
        from PIL import Image
        import imagehash
        img = Image.open(io.BytesIO(img_bytes))
        return str(imagehash.phash(img))
    except Exception:
        return None


def _hamming(h1: str, h2: str) -> int:
    """Hamming distance between two pHash hex strings (via imagehash)."""
    import imagehash
    return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)


def _cluster_by_similarity(hashed: list) -> list:
    """Greedy single-link cluster of [(phash, source)] by Hamming <= threshold.
    Returns list of clusters, each a list of (phash, source)."""
    clusters = []   # each: list of (phash, source)
    for phash, source in hashed:
        placed = False
        for c in clusters:
            if any(_hamming(phash, ph) <= HAMMING_THRESHOLD for ph, _ in c):
                c.append((phash, source))
                placed = True
                break
        if not placed:
            clusters.append([(phash, source)])
    return clusters


async def compute_avatar_reuse(avatars: list, score_fn) -> dict:
    """avatars = profile['avatars'] = [{url, source}]. score_fn = _score_avatar.
    Hashes ONLY avatars with score_fn(url) >= 2 (decision 0). Returns a reuse report
    of HASHES + COUNTERS — never any image bytes."""
    report = {"computed": True, "hashed_count": 0, "skipped_default": 0,
              "skipped_fetch_fail": 0, "clusters": [], "max_reuse": 0,
              "distinct_images": 0}
    if not avatars:
        return report

    # decision 0: keep only real-photo avatars; defaults/identicons (score < 2) out.
    candidates = []
    seen_urls = set()
    for a in avatars:
        url = (a.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        if score_fn(url) >= 2:
            candidates.append((url, a.get("source") or "unknown"))
        else:
            report["skipped_default"] += 1
    candidates = candidates[:MAX_AVATARS]

    sem = asyncio.Semaphore(FETCH_CONCURRENCY)

    async def _hash_one(url, source):
        async with sem:
            raw = await _fetch_image_bytes(url)
        if raw is None:
            return ("fail", source)
        ph = _compute_phash(raw)        # raw leaves scope here — never stored
        if ph is None:
            return ("fail", source)
        return (ph, source)

    results = await asyncio.gather(*[_hash_one(u, s) for u, s in candidates])

    hashed = []
    for ph, source in results:
        if ph == "fail":
            report["skipped_fetch_fail"] += 1
        else:
            hashed.append((ph, source))
    report["hashed_count"] = len(hashed)

    clusters = _cluster_by_similarity(hashed)
    report["distinct_images"] = len(clusters)

    reuse = []
    for c in clusters:
        sources = sorted({src for _, src in c})
        if len(sources) >= 2:   # cross-platform reuse = same image, >=2 distinct sources
            reuse.append({"phash": c[0][0], "sources": sources, "size": len(sources)})
    reuse.sort(key=lambda r: -r["size"])
    report["clusters"] = reuse
    report["max_reuse"] = reuse[0]["size"] if reuse else 0
    return report


def compute_avatar_reuse_sync(avatars: list, score_fn) -> dict:
    """Sync entry point for sync callers (aggregate_profile). Bridges to the async
    implementation via asyncio.run; falls back to {computed: False} on any failure
    so avatar hashing can NEVER crash profile aggregation."""
    try:
        return asyncio.run(compute_avatar_reuse(avatars, score_fn))
    except Exception as e:
        logger.debug("avatar reuse failed: %s", e)
        return {"computed": False}
