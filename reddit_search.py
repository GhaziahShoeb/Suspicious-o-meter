import os
import requests
from dotenv import load_dotenv
load_dotenv()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")


def search_reddit_evidence(company_or_term: str, max_results: int = 5) -> list[dict]:
    """
    Searches Reddit (via Google, through Serper) for posts mentioning the given
    company name or search term. Returns a clean list of results.
    """
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
        clean_results.append({
            "title": r.get("title", ""),
            "url": r.get("link", ""),
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