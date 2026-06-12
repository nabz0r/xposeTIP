"""S288 — Article context fetch + named-press corroboration signal.

Best-effort, stateless. From media_mention findings, fetch the best name-matched
articles, recompute the name-match on the FULL text, and extract lightweight context
(author meta, og:image, image alt, a short snippet). Feeds ONE governed entropy axis
(press_corroboration) — NOT identity resolution (no primary_name/company write; R7 is
S289).

The signal (one sentence): being named in identifiable press with a strong name-match
is real identifying corroboration — not the article COUNT (that's the BFP
public_exposure axis), but the QUALITY of nominative corroboration.

Guards:
- §0 trap: we do NOT extract an employer/affiliation from captions (confident false
  positives, the ekatarina neighbourhood). Raw context only; bits are GATED by the
  name-match floor — below it the article is not a reliable corroboration → 0 credit
  (governor 3, never guess).
- Copyright: store only a short snippet (<=200 chars) around the mention, never the
  full article text. The fetched text is transient (used for the match, then dropped).
- Best-effort: any fetch failure (403/timeout/no text) is skipped, never raised — a
  dead article must never crash profile aggregation (same discipline as S286 avatars).
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

MAX_ARTICLES = 5          # hard cap — fetch only the best-matched few
FETCH_WORKERS = 3         # bound concurrency (PageFetcher is sync/requests)
SNIPPET_CHARS = 200       # copyright: short window around the mention only


def _name_match_floor() -> float:
    """Single source of the strong-match floor — the press_corroboration prior."""
    try:
        from api.services.layer4.entropy_engine import load_priors
        return float((load_priors().get("press_corroboration") or {}).get("name_match_floor", 0.80))
    except Exception:
        return 0.80


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _select_articles(findings, primary_name, max_n: int = MAX_ARTICLES) -> list:
    """Pick up to N best name-matched media_mention article URLs, pre-ranked on the
    title+snippet we ALREADY have (no fetch yet) so network is spent on the most
    promising. Hard cap = max_n."""
    from api.services.layer4.public_exposure_enricher import compute_name_match_confidence
    scored = []
    for f in (findings or []):
        if (getattr(f, "indicator_type", "") or "") != "media_mention":
            continue
        url = getattr(f, "url", None)
        if not url:
            continue
        title = getattr(f, "title", "") or ""
        desc = getattr(f, "description", "") or ""
        pre = compute_name_match_confidence(f"{title} {desc}", primary_name)
        scored.append((pre, url))
    scored.sort(key=lambda x: -x[0])
    seen, out = set(), []
    for _, url in scored:
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= max_n:
            break
    return out


def _extract_og_context(html: str) -> dict:
    """Local og:image / image-alt / author extraction (no coupling to the shared
    discovery meta_tag_extractor). The image ALT is the 'real info' signal."""
    out = {"author": None, "og_image": None, "image_alt": None}
    if not html:
        return out
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        def _meta(prop=None, name=None):
            t = soup.find("meta", property=prop) if prop else soup.find("meta", attrs={"name": name})
            c = (t.get("content") if t else None) or ""
            return c.strip() or None

        out["author"] = (_meta(name="author") or _meta(prop="article:author")
                         or _meta(prop="og:author") or _meta(name="twitter:creator"))
        out["og_image"] = _meta(prop="og:image")
        alt = _meta(prop="og:image:alt")
        if not alt:
            for img in soup.find_all("img"):
                a = (img.get("alt") or "").strip()
                if len(a) >= 10:          # significant alt only (skip "logo"/"icon")
                    alt = a
                    break
        out["image_alt"] = alt or None
    except Exception:
        pass
    return out


def _snippet_around(text: str, name: str, max_chars: int = SNIPPET_CHARS) -> str:
    """A <=max_chars window around the first name mention. Copyright-bounded — never
    the full article."""
    if not text or not name:
        return ""
    tl = text.lower()
    idx = -1
    for tok in [name] + name.split():
        i = tl.find(tok.lower())
        if i >= 0:
            idx = i
            break
    if idx < 0:
        return text[:max_chars].strip()
    start = max(0, idx - max_chars // 2)
    return text[start:start + max_chars].strip()


def fetch_article_contexts(findings, primary_name) -> dict:
    """Fetch the selected articles, recompute name-match on the FULL text, extract
    context. Best-effort: any failure is skipped, never raised. Returns hashes/counts
    + short snippets only — never a full article."""
    report = {"computed": True, "fetched": 0, "skipped_fetch_fail": 0,
              "strong_matches": 0, "best_match_confidence": 0.0, "contexts": []}
    if not (primary_name or "").strip():
        return report                      # no name → nothing to corroborate
    selected = _select_articles(findings, primary_name)
    if not selected:
        return report
    floor = _name_match_floor()

    from api.discovery.page_fetcher import PageFetcher
    from api.services.layer4.public_exposure_enricher import compute_name_match_confidence
    fetcher = PageFetcher()

    def _one(url):
        try:
            return url, fetcher.fetch(url)
        except Exception:
            return url, None

    try:
        with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
            results = list(ex.map(_one, selected))
    except Exception as e:
        logger.debug("article fetch pool failed: %s", e)
        return {"computed": False}

    best = 0.0
    for url, page in results:
        text = (page or {}).get("text") if page else None
        if not text:
            report["skipped_fetch_fail"] += 1
            continue
        report["fetched"] += 1
        conf = compute_name_match_confidence(text, primary_name)   # FULL-text match
        best = max(best, conf)
        if conf >= floor:
            report["strong_matches"] += 1
        ctx = _extract_og_context((page or {}).get("html"))
        report["contexts"].append({
            "url": url,
            "source_domain": _domain(url),
            "match_confidence": round(conf, 2),
            "author": ctx["author"],
            "og_image": ctx["og_image"],
            "image_alt": ctx["image_alt"],
            "snippet": _snippet_around(text, primary_name),   # <=200 chars, transient text dropped
        })
    report["best_match_confidence"] = round(best, 2)
    return report
