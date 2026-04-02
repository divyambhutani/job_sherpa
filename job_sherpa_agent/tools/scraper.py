import re

from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher


_STEALTH_DOMAINS = {"glassdoor.com", "ambitionbox.com","https://leetcode.com/discuss/topic/compensation/", "indeed.com", "instahyre.com"}
_DYNAMIC_DOMAINS = {"levels.fyi", "wellfound.com", "weworkremotely.com", "remotejobs.io", "jobright.ai"}
_MAX_CONTENT_LENGTH = 6000


def _get_domain(url: str) -> str:
    match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
    return match.group(1).lower() if match else ""


def _extract_text(page: object) -> str:
    """Try progressively broader selectors to get main content."""
    for selector in ("article", "main", "[class*='content']", "body"):
        element = page.find(selector)
        if element:
            text = element.get_all_text(
                ignore_tags=("script", "style", "nav",
                             "footer", "header", "aside")
            )
            if text and len(text.strip()) > 300:
                return text.strip()[:_MAX_CONTENT_LENGTH]

    text = page.get_all_text(ignore_tags=(
        "script", "style", "nav", "footer", "header"))
    return (text or "").strip()[:_MAX_CONTENT_LENGTH]


def scrape_content(url: str) -> str:
    """
    Scrapes full text content from a URL, routing to the appropriate fetcher:
      - StealthyFetcher: Glassdoor, AmbitionBox (Cloudflare-protected)
      - DynamicFetcher: Levels.fyi (JS-rendered)
      - Fetcher: Reddit, Medium, and all other open sites

    Returns extracted text truncated to 6000 chars, or a SCRAPE_FAILED error string.
    """
    domain = _get_domain(url)

    try:
        if any(sd in domain for sd in _STEALTH_DOMAINS):
            page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            return _extract_text(page)

        if any(dd in domain for dd in _DYNAMIC_DOMAINS):
            # Try regular first (faster), fall back to DynamicFetcher
            try:
                fetcher = Fetcher(auto_match=False)
                page = fetcher.get(url)
                text = _extract_text(page)
                if len(text) > 300:
                    return text
            except Exception:
                pass
            page = DynamicFetcher.fetch(url, network_idle=True)
            return _extract_text(page)

        # Default: regular Fetcher
        fetcher = Fetcher(auto_match=False)
        page = fetcher.get(url)
        return _extract_text(page)

    except Exception as e:
        return f"SCRAPE_FAILED: {url}: {str(e)}"
