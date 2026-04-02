import json
import re

import requests


_PLATFORM_PATTERNS = [
    ("github", r"github\.com"),
    ("linkedin", r"linkedin\.com"),
    ("leetcode", r"leetcode\.com"),
    ("kaggle", r"kaggle\.com"),
    ("codeforces", r"codeforces\.com"),
    ("codechef", r"codechef\.com"),
    ("hackerrank", r"hackerrank\.com"),
    ("devpost", r"devpost\.com"),
    ("portfolio", r"(vercel\.app|netlify\.app|github\.io|pages\.dev)"),
]


def _detect_platform(url: str) -> str:
    for platform, pattern in _PLATFORM_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return "other"


def _check_leetcode(url: str) -> tuple[str, str, str]:
    """Returns (status, note, action_required) for a LeetCode profile URL."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return "dead", f"HTTP {resp.status_code}", "Verify LeetCode profile URL"

        text = resp.text
        # Look for solved count patterns in the page
        solved_match = re.search(r'"solvedProblem[s]?["\s:]+(\d+)', text)
        total_solved = int(solved_match.group(1)) if solved_match else None

        if total_solved is not None and total_solved < 100:
            return (
                "warning",
                f"Low activity ({total_solved} problems solved)",
                "Solve 50+ medium/hard problems before listing LeetCode on resume",
            )
        return "live", "", ""
    except requests.RequestException as e:
        return "warning", f"Timeout or error: {str(e)[:80]}", ""


def validate_links(links_json: str) -> str:
    """
    Validates HTTP status of all resume links.

    Input: JSON array of URL strings (e.g., '["https://github.com/foo", ...]')
    Returns a JSON string with keys:
      - "links": list of {url, platform, status, note, action_required}
      - "action_items": list of strings for the candidate to act on
    """
    try:
        links: list[str] = json.loads(links_json)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"links": [], "action_items": [], "error": "Invalid input JSON"})

    results = []
    action_items = []

    for url in links:
        platform = _detect_platform(url)
        note = ""
        action_required = ""

        if platform == "leetcode":
            status, note, action_required = _check_leetcode(url)
        else:
            try:
                resp = requests.head(
                    url,
                    allow_redirects=True,
                    timeout=8,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                code = resp.status_code
                if code == 200:
                    status = "live"
                elif code in (403, 404, 410):
                    status = "dead"
                    action_required = f"Fix or remove dead link (HTTP {code})"
                else:
                    status = "warning"
                    note = f"HTTP {code}"
            except requests.exceptions.Timeout:
                status = "warning"
                note = "Request timed out"
            except requests.RequestException as e:
                status = "warning"
                note = str(e)[:80]

        result = {
            "url": url,
            "platform": platform,
            "status": status,
            "note": note,
            "action_required": action_required,
        }
        results.append(result)

        if action_required:
            action_items.append(f"[{platform.upper()}] {action_required}: {url}")

    return json.dumps({"links": results, "action_items": action_items})
