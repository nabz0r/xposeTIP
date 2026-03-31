"""Page fetcher for Discovery Engine.

Downloads web pages and extracts clean text via trafilatura.
Handles HTML pages and PDF documents.
"""
import logging
from io import BytesIO

import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; xposeTIP Discovery/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
}

_SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".webm",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dmg", ".msi", ".deb", ".rpm",
    ".woff", ".woff2", ".ttf", ".eot",
}


class PageFetcher:
    """Fetch web pages and extract content."""

    def __init__(self, timeout: int = 10, max_size_mb: int = 5):
        self.timeout = timeout
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def fetch(self, url: str) -> dict | None:
        """Fetch a URL and extract content. Returns dict or None on failure."""
        try:
            # Skip obvious non-HTML
            lower_url = url.lower()
            if any(lower_url.endswith(ext) for ext in _SKIP_EXTENSIONS):
                return None

            resp = requests.get(
                url, timeout=self.timeout, headers=_HEADERS,
                stream=True, allow_redirects=True,
            )

            if resp.status_code in (401, 403, 404, 410, 429, 451):
                return None
            if resp.status_code >= 400:
                return None

            # Check content length
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_size_bytes:
                logger.debug("PageFetcher: skipping %s (too large: %s)", url, content_length)
                return None

            content_type = (resp.headers.get("Content-Type") or "").lower()

            # PDF handling
            if "application/pdf" in content_type or lower_url.endswith(".pdf"):
                return self._extract_pdf(url, resp.content)

            # Only process HTML
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None

            html = resp.text
            if not html or len(html) < 100:
                return None

            # Extract clean text via trafilatura
            text = ""
            title = ""
            try:
                import trafilatura
                text = trafilatura.extract(
                    html, include_links=True, include_tables=True,
                ) or ""
                metadata = trafilatura.extract_metadata(html)
                if metadata:
                    title = metadata.title or ""
            except ImportError:
                logger.debug("trafilatura not installed — using raw HTML")
                text = html
            except Exception:
                text = html

            # Fallback title from HTML
            if not title:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html[:5000], "html.parser")
                    tag = soup.find("title")
                    if tag:
                        title = tag.get_text(strip=True)[:200]
                except Exception:
                    pass

            return {
                "url": url,
                "title": title,
                "text": text,
                "html": html,
                "content_type": content_type,
            }

        except requests.exceptions.Timeout:
            logger.debug("PageFetcher: timeout for %s", url)
            return None
        except requests.exceptions.RequestException as e:
            logger.debug("PageFetcher: error for %s: %s", url, e)
            return None
        except Exception as e:
            logger.debug("PageFetcher: unexpected error for %s: %s", url, e)
            return None

    def _extract_pdf(self, url: str, content: bytes) -> dict | None:
        """Extract text from PDF content."""
        if len(content) > self.max_size_bytes:
            return None
        try:
            import pdfplumber
            pdf = pdfplumber.open(BytesIO(content))
            pages_text = []
            for page in pdf.pages[:20]:  # Max 20 pages
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            pdf.close()

            text = "\n\n".join(pages_text)
            if not text.strip():
                return None

            return {
                "url": url,
                "title": url.rsplit("/", 1)[-1],
                "text": text,
                "html": "",
                "content_type": "application/pdf",
            }
        except ImportError:
            logger.debug("pdfplumber not installed — skipping PDF %s", url)
            return None
        except Exception as e:
            logger.debug("PageFetcher: PDF extraction failed for %s: %s", url, e)
            return None
