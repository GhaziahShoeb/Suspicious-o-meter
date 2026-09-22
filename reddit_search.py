import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def sanitize_search_term(term: str) -> str:
    """Strips query operators, quotes, and punctuation to prevent Google/Serper search injection."""
    if not term:
        return ""
    # Remove operators and special characters that could hijack search semantics
    cleaned = re.sub(r'["\'\(\)\[\]\{\}\\\^\~\*\?:]', ' ', term)
    cleaned = re.sub(r'\b(site|inurl|intitle|filetype|AND|OR|NOT)\b', ' ', cleaned, flags=re.IGNORECASE)
    # Collapse multiple whitespaces
    return " ".join(cleaned.split()).strip()

def search_reddit_evidence(company_or_term: str, max_results: int = 5) -> list[dict]:
    """
    Searches Reddit (via Google, through Serper) for posts mentioning the given
    company name or search term. Returns a clean list of results.
    """
    serper_api_key = os.environ.get("SERPER_API_KEY")
    if not serper_api_key:
        return []

    clean_term = sanitize_search_term(company_or_term)
    if not clean_term:
        return []

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "q": f"site:reddit.com {clean_term}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        raw_results = data.get("organic", [])[:max_results]

        clean_results = []
        for r in raw_results:
            clean_results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
                "source": "reddit"
            })
        return clean_results
    except Exception:
        # Graceful degradation if external API is unreachable or returns error
        return []

if __name__ == "__main__":
    results = search_reddit_evidence("Unlox Academy scam")
    for r in results:
        print(r["title"])
        print(r["url"])
        print(r["snippet"])
        print("---")