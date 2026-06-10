"""Search clients for Discovery Engine.

Pluggable backends behind a common `.search(query, num_results) -> [{url,title,
snippet,position}]` interface:
  - SearchClient        : Google via SerpAPI (paid key).
  - DuckDuckGoSearchClient : free, no key — DuckDuckGo HTML endpoint (S264-0).
  - MockSearchClient    : empty results (last resort).

`get_search_client()` prefers SerpAPI when keyed, else the free DDG backend, else
Mock. Set DISCOVERY_SEARCH_BACKEND={serpapi|duckduckgo|mock} to force one.
"""
import logging
import os
import re
import time
import urllib.parse

logger = logging.getLogger(__name__)

SERPAPI_KEY_ENV = "SERPAPI_KEY"
SEARCH_BACKEND_ENV = "DISCOVERY_SEARCH_BACKEND"


class SearchError(Exception):
    pass


class SearchConfigError(SearchError):
    pass


class SearchClient:
    """Execute Google searches via SerpAPI."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get(SERPAPI_KEY_ENV)
        if not self.api_key:
            raise SearchConfigError(
                "SERPAPI_KEY not configured. Set SERPAPI_KEY environment variable "
                "or pass api_key to SearchClient."
            )
        self._last_request = 0

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        """Execute a search query. Returns list of {url, title, snippet, position}."""
        try:
            from serpapi import GoogleSearch
        except ImportError:
            raise SearchError("serpapi package not installed: pip install google-search-results")

        # Rate limit: 1 req/sec
        elapsed = time.time() - self._last_request
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

        try:
            search = GoogleSearch({
                "q": query,
                "num": str(num_results),
                "engine": "google",
                "api_key": self.api_key,
            })
            raw = search.get_dict()
            self._last_request = time.time()

            results = []
            for r in raw.get("organic_results", []):
                if not r.get("link"):
                    continue
                results.append({
                    "url": r["link"],
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "position": r.get("position", 0),
                })

            logger.info("SerpAPI: %d results for '%s'", len(results), query[:80])
            return results

        except Exception as e:
            logger.warning("SerpAPI search failed for '%s': %s", query[:80], e)
            raise SearchError(f"Search failed: {e}")


class DuckDuckGoSearchClient:
    """Free, no-key search via the DuckDuckGo HTML endpoint (S264-0).

    Honest caveats: HTML scraping is fragile (rate-limit / markup drift). Returns
    DIRECT result URLs (DDG's `result__a` hrefs are no longer `uddg=`-wrapped as of
    2024). `site:` operators pass through, which is what AR-0 relies on. Pluggable
    behind the same interface so a SearXNG swap stays cheap (deferred — infra).
    """

    ENDPOINTS = ("https://html.duckduckgo.com/html/", "https://lite.duckduckgo.com/lite/")
    _UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    # DDG result anchors: <a ... class="result__a" href="https://...">title</a>
    _A_RE = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
    _SNIP_RE = re.compile(r'class="result__snippet"[^>]*>(.*?)</a>', re.S)
    # lite endpoint: plain <a class="result-link" href="...">  (no result__a)
    _LITE_A_RE = re.compile(r'<a[^>]+class="result-link"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
    _TAG_RE = re.compile(r"<[^>]+>")
    _MAX_RETRIES = 3

    def __init__(self):
        self._last_request = 0

    @classmethod
    def _clean(cls, html_fragment: str) -> str:
        return urllib.parse.unquote(
            cls._TAG_RE.sub("", html_fragment or "")
        ).replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"').strip()

    @classmethod
    def _unwrap(cls, href: str) -> str:
        # Legacy DDG redirect form (defensive): /l/?uddg=<encoded>
        if "uddg=" in href:
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                return urllib.parse.unquote(m.group(1))
        if href.startswith("//"):
            return "https:" + href
        return href

    @classmethod
    def _is_challenge(cls, html: str) -> bool:
        low = (html or "").lower()
        # 202/challenge page: canonical→duckduckgo.com, no result anchors, anomaly text.
        return any(w in low for w in ("anomaly detected", "anomaly", "are you a robot",
                                      "captcha", "challenge")) and "result__a" not in low

    def _parse(self, html: str, num_results: int) -> list[dict]:
        anchors = self._A_RE.findall(html)
        snippets = [self._clean(s) for s in self._SNIP_RE.findall(html)]
        if not anchors:
            anchors = [(h, t) for (h, t) in self._LITE_A_RE.findall(html)]
        results = []
        for i, (href, title_html) in enumerate(anchors[:num_results]):
            url = self._unwrap(href)
            if not url.startswith("http"):
                continue
            results.append({
                "url": url,
                "title": self._clean(title_html),
                "snippet": snippets[i] if i < len(snippets) else "",
                "position": i + 1,
            })
        return results

    def _search_ddgs(self, query: str, num_results: int) -> list[dict] | None:
        """Primary path: the `ddgs` lib. Handles vqd tokens + backend rotation, so it
        survives the burst rate-wall that 202s the raw HTML endpoint. Returns None if
        the lib is absent or errors → caller falls back to raw-HTML scraping."""
        try:
            from ddgs import DDGS
        except ImportError:
            return None
        try:
            rows = list(DDGS().text(query, max_results=num_results)) or []
        except Exception as e:
            logger.warning("ddgs lib failed for '%s': %s", query[:80], e)
            return None
        results = []
        for i, row in enumerate(rows[:num_results]):
            url = row.get("href") or row.get("url") or ""
            if not url.startswith("http"):
                continue
            results.append({
                "url": url,
                "title": (row.get("title") or "").strip(),
                "snippet": (row.get("body") or row.get("snippet") or "").strip(),
                "position": i + 1,
            })
        logger.info("DuckDuckGo(ddgs): %d results for '%s'", len(results), query[:80])
        return results

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        """Free DDG search. Primary: the `ddgs` lib (robust). Fallback: raw HTML
        endpoint with retry/backoff across html + lite (DDG soft-throttles bursts
        with HTTP 202 + a challenge page). Either way returns [] when walled —
        the caller degrades gracefully and this never raises."""
        import requests

        via_lib = self._search_ddgs(query, num_results)
        if via_lib:
            return via_lib

        for attempt in range(self._MAX_RETRIES):
            endpoint = self.ENDPOINTS[attempt % len(self.ENDPOINTS)]
            elapsed = time.time() - self._last_request
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            try:
                resp = requests.post(
                    endpoint, data={"q": query},
                    headers={"User-Agent": self._UA, "Accept": "text/html"}, timeout=15,
                )
                self._last_request = time.time()
                html = resp.text or ""
                if resp.status_code == 200 and not self._is_challenge(html):
                    results = self._parse(html, num_results)
                    if results:
                        logger.info("DuckDuckGo: %d results for '%s' (%s)",
                                    len(results), query[:80], endpoint)
                        return results
                logger.warning("DuckDuckGo: HTTP %d / challenge=%s for '%s' (attempt %d/%d, %s)",
                               resp.status_code, self._is_challenge(html), query[:80],
                               attempt + 1, self._MAX_RETRIES, endpoint)
            except Exception as e:
                logger.warning("DuckDuckGo: error for '%s' (attempt %d): %s",
                               query[:80], attempt + 1, e)
            time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
        logger.warning("DuckDuckGo: exhausted retries (bot-walled) for '%s'", query[:80])
        return []


class MockSearchClient:
    """Returns empty results. For testing pipeline without API key."""

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        logger.debug("MockSearch: '%s' → 0 results (no API key)", query[:80])
        return []


def get_search_client():
    """Get configured search client.

    S264-0 decision (Nabil): free, no-key by default — "No SerpAPI, ever" unless a
    human explicitly opts in. So the free DuckDuckGo backend is the DEFAULT even
    when a stray SERPAPI_KEY is present; SerpAPI is used ONLY when forced via
    DISCOVERY_SEARCH_BACKEND=serpapi (kept as an escape hatch, never auto-selected).
    """
    forced = (os.environ.get(SEARCH_BACKEND_ENV) or "").strip().lower()
    if forced == "serpapi":
        return SearchClient()
    if forced == "mock":
        return MockSearchClient()
    # default (incl. forced == "duckduckgo" or unset): free, no key.
    return DuckDuckGoSearchClient()
