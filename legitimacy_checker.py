import os
import re
from datetime import datetime
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

def extract_and_validate_domain(domain_input: str) -> str | None:
    """
    Extracts the clean host domain from a URL or raw string, and validates that
    it is a valid FQDN (Fully Qualified Domain Name). Rejects IP addresses and invalid formats.
    """
    if not domain_input or domain_input.lower() in ("none", "unknown", "n/a"):
        return None

    candidate = domain_input.strip()
    if "://" in candidate:
        try:
            candidate = urlparse(candidate).netloc
        except Exception:
            return None

    # Strip port, path, and auth if present
    candidate = candidate.split("/")[0].split(":")[0].strip().lower()

    # Reject localhost, IPs, and check against FQDN regex
    if candidate in ("localhost", "127.0.0.1") or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", candidate):
        return None

    if DOMAIN_REGEX.match(candidate):
        return candidate
    return None

def sanitize_company_name(name: str) -> str:
    """Strips quotes and search operators to avoid query injection."""
    if not name:
        return ""
    cleaned = re.sub(r'["\'\(\)\[\]\{\}\\\^\~\*\?:]', ' ', name)
    cleaned = re.sub(r'\b(site|inurl|intitle|filetype|AND|OR|NOT)\b', ' ', cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split()).strip()

def check_domain_age(domain: str) -> dict:
    """
    Looks up how old a domain is using WHOIS data.
    Validates domain syntax and handles missing API keys gracefully.
    """
    valid_domain = extract_and_validate_domain(domain)
    if not valid_domain:
        return {
            "domain": domain,
            "created_date": None,
            "age_days": None,
            "error": "Invalid or missing domain format"
        }

    whois_api_key = os.environ.get("WHOIS_API_KEY")
    if not whois_api_key:
        return {
            "domain": valid_domain,
            "created_date": None,
            "age_days": None,
            "error": "WHOIS_API_KEY is not configured"
        }

    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    params = {
        "apiKey": whois_api_key,
        "domainName": valid_domain,
        "outputFormat": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "domain": valid_domain,
            "created_date": None,
            "age_days": None,
            "error": f"WHOIS lookup failed: {e}"
        }

    whois_record = data.get("WhoisRecord", {})
    created_date_str = whois_record.get("createdDate") or whois_record.get("registryData", {}).get("createdDate")

    if not created_date_str:
        return {
            "domain": valid_domain,
            "created_date": None,
            "age_days": None,
            "error": "No creation date found in WHOIS data"
        }

    try:
        created_date = datetime.fromisoformat(created_date_str.replace("Z", "+00:00"))
        age_days = (datetime.now(created_date.tzinfo) - created_date).days
    except Exception as e:
        return {
            "domain": valid_domain,
            "created_date": created_date_str,
            "age_days": None,
            "error": f"Could not parse date: {e}"
        }

    return {
        "domain": valid_domain,
        "created_date": created_date_str,
        "age_days": age_days,
        "error": None
    }


def check_company_existence(company_name: str) -> dict:
    """
    Searches for signs the company is a real, registered entity.
    Sanitizes search query and handles missing API key.
    """
    clean_name = sanitize_company_name(company_name)
    if not clean_name or clean_name.lower() == "unknown":
        return {
            "company_name": company_name,
            "has_linkedin_page": False,
            "search_results_count": 0,
            "top_results": [],
            "error": "No valid company name provided"
        }

    serper_api_key = os.environ.get("SERPER_API_KEY")
    if not serper_api_key:
        return {
            "company_name": clean_name,
            "has_linkedin_page": False,
            "search_results_count": 0,
            "top_results": [],
            "error": "SERPER_API_KEY is not configured"
        }

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": f'"{clean_name}" (linkedin.com OR "registered company" OR "Pvt Ltd" OR "Ltd" OR incorporated)'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {
            "company_name": clean_name,
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
        "company_name": clean_name,
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