from scrapling.fetchers import Fetcher


def fetch_jd(url: str) -> str:
    """
    Fetches and returns job description text from a URL.
    Uses a regular (non-stealth) Scrapling Fetcher — JD pages are generally open.
    Returns plain text truncated to 8000 chars, or an error string.
    """
    try:
        fetcher = Fetcher(auto_match=False)
        page = fetcher.get(url)

        # Try progressively broader selectors
        for selector in ("main", "article", "[class*='description']", "body"):
            element = page.find(selector)
            if element:
                text = element.get_all_text(
                    ignore_tags=("script", "style", "nav", "footer", "header")
                )
                if text and len(text.strip()) > 200:
                    return text.strip()[:8000]

        # Final fallback: full page text
        text = page.get_all_text(ignore_tags=("script", "style", "nav", "footer", "header"))
        return text.strip()[:8000] if text else f"ERROR: No content extracted from {url}"

    except Exception as e:
        return f"ERROR: Could not fetch JD from {url}: {str(e)}"
