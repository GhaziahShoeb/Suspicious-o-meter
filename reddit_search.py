import os
import re
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")


def clean_search_term(term: str) -> str:
    """
    Makes an LLM-extracted company name / search term safe to use in an
    unquoted search query. Removes quotes, colons, parentheses, newlines and
    leading/trailing hyphens so the term can't act as a search operator
    (e.g. "-scam", "site:other.com") and skew the results.
    """
    term = re.sub(r"[^\w\s&.,'\-]", " ", str(term or ""))
    # Keep hyphens only when they sit between letters/digits (e.g. Coca-Cola)
    term = re.sub(r"(?<!\w)-+|-+(?!\w)", " ", term)
    term = re.sub(r"\s+", " ", term).strip()
    return term[:100]


def _is_reddit_url(link: str) -> bool:
    """Only accept https links that really point at reddit.com."""
    try:
        parsed = urlparse(link)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "reddit.com" or host.endswith(".reddit.com"))


def search_reddit_evidence(company_or_term: str, max_results: int = 5) -> list[dict]:
    """
    Searches Reddit (via Google, through Serper) for posts mentioning the given
    company name or search term. Returns a clean list of results.
    """
    company_or_term = clean_search_term(company_or_term)
    if not company_or_term:
        return []

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": f"site:reddit.com {company_or_term}"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    raw_results = data.get("organic", [])[:max_results]

    clean_results = []
    for r in raw_results:
        link = r.get("link", "")
        if not _is_reddit_url(link):
            continue
        clean_results.append({
            "title": r.get("title", ""),
            "url": link,
            "snippet": r.get("snippet", ""),
            "source": "reddit"
        })

    return clean_results


if __name__ == "__main__":
    results = search_reddit_evidence("Unlox Academy scam")
    for r in results:
        print(r["title"])
        print(r["url"])
        print(r["snippet"])
        print("---")