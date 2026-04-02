"""
Tool 4: serper_search.py
Searches the web via Serper API to find relevant URLs.
Used to find interview experiences and salary data pages
before deep scraping with Scrapling.
"""

import os
import requests
from typing import Any
from datetime import datetime, timedelta


SERPER_API_URL = "https://google.serper.dev/search"


def _is_too_old(date_str: str, years: int = 3) -> bool:
    """
    Check if a result date is older than `years` years.
    Returns True if the result should be dropped.
    """
    if not date_str:
        return False  # No date = keep it, can't tell

    cutoff = datetime.now() - timedelta(days=years * 365)

    # Serper returns dates like "Jan 15, 2024" or "2 days ago" etc.
    try:
        # Try parsing absolute date
        parsed = datetime.strptime(date_str, "%b %d, %Y")
        return parsed < cutoff
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed < cutoff
    except ValueError:
        pass

    # Relative dates like "2 days ago", "3 months ago" are always recent
    if "ago" in date_str.lower():
        return False

    return False  # When in doubt, keep it


def serper_search(query: str, num_results: int = 10) -> dict[str, Any]:
    """
    Search the web using Serper API and return structured results.

    Args:
        query: Search query string.
        num_results: Number of results to return (max 10).

    Returns:
        {
            "query": the search query used,
            "results": list of {url, title, snippet, date},
            "filtered_count": how many were dropped for being too old,
            "error": None or error message
        }
    """
    api_key = os.getenv("SERPER_API_KEY", "")

    if not api_key:
        return {
            "query": query,
            "results": [],
            "filtered_count": 0,
            "error": "SERPER_API_KEY not set in environment variables",
        }

    try:
        response = requests.post(
            SERPER_API_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "num": num_results,
            },
            timeout=10,
        )

        if response.status_code != 200:
            return {
                "query": query,
                "results": [],
                "filtered_count": 0,
                "error": f"Serper API error: {response.status_code} — {response.text}",
            }

        data = response.json()
        raw_results = data.get("organic", [])

        results = []
        filtered_count = 0

        for item in raw_results:
            date_str = item.get("date", "")

            # Drop results older than 3 years
            if _is_too_old(date_str, years=3):
                filtered_count += 1
                continue

            results.append({
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "date": date_str,
            })

        return {
            "query": query,
            "results": results,
            "filtered_count": filtered_count,
            "error": None,
        }

    except requests.exceptions.Timeout:
        return {
            "query": query,
            "results": [],
            "filtered_count": 0,
            "error": "Serper API request timed out",
        }
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "filtered_count": 0,
            "error": f"Serper search failed: {str(e)}",
        }


def build_interview_queries(company: str, role: str) -> list[str]:
    """
    Build a list of search queries for interview experience data.

    Args:
        company: Company name.
        role: Job role/title.

    Returns:
        List of search query strings.
    """
    year = datetime.now().year
    return [
        f"{company} {role} interview experience {year}",
        f"{company} {role} interview process {year}",
        f"{company} {role} interview questions {year}",
        f"{company} {role} interview rounds site:glassdoor.com",
        f"{company} {role} interview experience site:reddit.com",
        f"{company} {role} interview experience site:leetcode.com",
    ]


def build_salary_queries(company: str, role: str) -> list[str]:
    main_company = company.split()[0]
    year = datetime.now().year
    return [
        f"{company} {role} salary India {year} site:ambitionbox.com",
        f"{company} {role} salary India {year} site:glassdoor.co.in",
        f"{company} {role} salary India {year} site:naukri.com",
        f"{company} {role} compensation {year} site:levels.fyi",
        f"{company} {role} CTC India {year}",
        f"{company} {role} salary India linkedin",
    ]