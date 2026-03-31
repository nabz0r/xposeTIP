"""SerpAPI search client for Discovery Engine.

Wrapper around Google Search via SerpAPI. Swappable: replace this
class for Searx/Bing/other backend.
"""
import logging
import os
import time

logger = logging.getLogger(__name__)

SERPAPI_KEY_ENV = "SERPAPI_KEY"


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


class MockSearchClient:
    """Returns empty results. For testing pipeline without API key."""

    def search(self, query: str, num_results: int = 10) -> list[dict]:
        logger.debug("MockSearch: '%s' → 0 results (no API key)", query[:80])
        return []


def get_search_client() -> SearchClient | MockSearchClient:
    """Get configured search client. Falls back to mock if no API key."""
    api_key = os.environ.get(SERPAPI_KEY_ENV)
    if api_key:
        return SearchClient(api_key)
    logger.warning("SERPAPI_KEY not set — using MockSearchClient (no real searches)")
    return MockSearchClient()
