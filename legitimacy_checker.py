import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()


WHOIS_API_KEY = os.environ.get("WHOIS_API_KEY")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

def check_domain_age(domain: str) -> dict:
    """
    Looks up how old a domain is using WHOIS data.
    """
    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    params = {
        "apiKey": WHOIS_API_KEY,
        "domainName": domain,
        "outputFormat": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "domain": domain,
            "created_date": None,
            "age_days": None,
            "error": f"WHOIS lookup failed: {e}"
        }

    whois_record = data.get("WhoisRecord", {})
    created_date_str = whois_record.get("createdDate") or whois_record.get("registryData", {}).get("createdDate")

    if not created_date_str:
        return {
            "domain": domain,
            "created_date": None,
            "age_days": None,
            "error": "No creation date found in WHOIS data"
        }

    try:
        created_date = datetime.fromisoformat(created_date_str.replace("Z", "+00:00"))
        age_days = (datetime.now(created_date.tzinfo) - created_date).days
    except Exception as e:
        return {
            "domain": domain,
            "created_date": created_date_str,
            "age_days": None,
            "error": f"Could not parse date: {e}"
        }

    return {
        "domain": domain,
        "created_date": created_date_str,
        "age_days": age_days,
        "error": None
    }


def check_company_existence(company_name: str) -> dict:
    """
    STAND-IN for OpenCorporates (which requires application/approval we don't
    have yet). Uses a general web search to look for signs the company is a
    real, registered entity - official filings, business directories, a
    LinkedIn company page.

    This is a WEAKER signal than an actual government registry lookup:
    - A positive result (found LinkedIn/directory listings) is reasonably
      reassuring.
    - A negative result (nothing found) is NOT strong evidence of fraud -
      it could just mean poor search visibility, a very new company, or
      weak search coverage for smaller/regional businesses.

    Returns:
    {
        "company_name": "...",
        "has_linkedin_page": True/False,
        "search_results_count": 3,
        "top_results": [...],
        "error": None or error message
    }
    """
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": f'"{company_name}" (linkedin.com OR "registered company" OR "Pvt Ltd" OR "Ltd" OR incorporated)'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "company_name": company_name,
            "has_linkedin_page": False,
            "search_results_count": 0,
            "top_results": [],
            "error": f"Search failed: {e}"
        }

    raw_results = data.get("organic", [])[:5]

    has_linkedin_page = any("linkedin.com" in r.get("link", "") for r in raw_results)

    top_results = [
        {"title": r.get("title", ""), "url": r.get("link", "")}
        for r in raw_results
    ]

    return {
        "company_name": company_name,
        "has_linkedin_page": has_linkedin_page,
        "search_results_count": len(raw_results),
        "top_results": top_results,
        "error": None
    }


if __name__ == "__main__":
    print("Domain age check:")
    print(check_domain_age("wyreflow.com"))
    print()
    print("Company existence check:")
    print(check_company_existence("Wyreflow Technologies"))