import re
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()


WHOIS_API_KEY = os.environ.get("WHOIS_API_KEY")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

# Each label 1-63 chars of a-z/0-9/hyphen (not starting/ending with hyphen), at least one dot
DOMAIN_RE = re.compile(
    r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$"
)


def clean_company_name(name: str) -> str:
    """
    Makes an LLM-extracted company name safe to put inside a search query.
    Keeps letters, digits, spaces and a few harmless punctuation marks; drops
    quotes, colons, parentheses, newlines and anything else that could break
    out of the quoted phrase and act as a search operator.
    """
    name = re.sub(r"[^\w\s&.,'\-]", " ", str(name or ""))
    name = re.sub(r"\s+", " ", name).strip()
    return name[:80]


def clean_domain(domain: str):
    """
    Normalizes an LLM-extracted domain (strips scheme, path, port, 'www.') and
    validates it. Returns the cleaned domain, or None if it isn't a valid one.
    """
    d = str(domain or "").strip().lower()
    d = re.sub(r"^[a-z][a-z0-9+.-]*://", "", d)
    d = re.split(r"[/?#]", d)[0]
    d = d.split(":")[0]
    if d.startswith("www."):
        d = d[4:]
    if len(d) > 253 or not DOMAIN_RE.match(d):
        return None
    return d


def check_domain_age(domain: str) -> dict:
    """
    Looks up how old a domain is using WHOIS data.
    """
    original = str(domain or "")[:100]
    domain = clean_domain(domain)
    if domain is None:
        return {
            "domain": original,
            "created_date": None,
            "age_days": None,
            "error": "Invalid domain"
        }

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
        # Don't include str(e): requests errors contain the full URL, which
        # here includes the API key in the query string.
        return {
            "domain": domain,
            "created_date": None,
            "age_days": None,
            "error": f"WHOIS lookup failed ({type(e).__name__})"
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
            "error": f"Could not parse date ({type(e).__name__})"
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
    company_name = clean_company_name(company_name)
    if not company_name:
        return {
            "company_name": "",
            "has_linkedin_page": False,
            "search_results_count": 0,
            "top_results": [],
            "error": "Invalid company name"
        }

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
            "error": f"Search failed ({type(e).__name__})"
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