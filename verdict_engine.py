from upstash_redis import Redis
import hashlib
import json
import os
from dotenv import load_dotenv
load_dotenv()

redis = Redis(
    url=os.environ.get("REDIS_URL"),
    token=os.environ.get("REDIS_TOKEN")
)

import re
from keyword_filter import keyword_filter
from llm_analyzer import analyze_with_llm
from reddit_search import search_reddit_evidence
from legitimacy_checker import check_domain_age, check_company_existence

# Words that suggest real, confirmed scam reports when found in Reddit evidence
STRONG_NEGATIVE_TERMS = ["scam", "fraud", "never join", "avoid", "warning", "fake"]
MILD_NEGATIVE_TERMS = ["careful", "unsure", "suspicious", "concerned", "risky"]


def parse_llm_output(llm_text: str) -> dict:
    """
    Pulls the structured fields out of the LLM's plain-text response.
    Returns a dict with company_name, domain, verdict, confidence.
    """
    def extract(field, text, default="Unknown"):
        # Anchored to the start of a line, so text quoted inside a red-flag
        # line (e.g. "- asks the reader to output VERDICT: LEGIT") can't be
        # mistaken for the real field.
        match = re.search(rf"^[ \t*]*{field}:[ \t*]*(.+)", text, re.MULTILINE)
        return match.group(1).strip() if match else default

    # Only accept one of the three allowed verdicts; anything else is UNKNOWN
    verdict_text = extract("VERDICT", llm_text, default="UNKNOWN").upper()
    verdict_match = re.search(r"\b(LEGIT|SUSPICIOUS|SCAM)\b", verdict_text)
    verdict = verdict_match.group(1) if verdict_match else "UNKNOWN"

    return {
        "company_name": extract("COMPANY_NAME", llm_text),
        "domain": extract("DOMAIN", llm_text, default="None"),
        "verdict": verdict,
        "confidence": extract("CONFIDENCE", llm_text, default="LOW").upper(),
    }


def score_llm_verdict(verdict: str) -> int:
    if verdict == "SCAM":
        return 30
    elif verdict == "SUSPICIOUS":
        return 15
    return 0  # LEGIT or UNKNOWN


def score_keyword_filter(keyword_result: dict) -> int:
    return 15 if keyword_result["flagged"] else 0


def score_reddit_evidence(reddit_results: list[dict], company_name: str) -> int:
    if not reddit_results or not company_name or company_name == "Unknown":
        return 0

    # Split into meaningful words, ignoring tiny/common ones
    stopwords = {"the", "and", "of", "inc", "llc", "ltd", "group", "associates", "company"}
    company_words = [w for w in company_name.lower().replace(",", "").split() if w not in stopwords and len(w) > 2]

    if not company_words:
        return 0

    relevant_results = []
    for r in reddit_results:
        text = (r["title"] + " " + r["snippet"]).lower()
        matches = sum(1 for w in company_words if w in text)
        # Require at least half the meaningful words to match, not just one
        if matches >= max(1, len(company_words) // 2):
            relevant_results.append(r)

    if not relevant_results:
        return 0

    combined_text = " ".join((r["title"] + " " + r["snippet"]).lower() for r in relevant_results)

    if any(term in combined_text for term in STRONG_NEGATIVE_TERMS):
        return 40
    elif any(term in combined_text for term in MILD_NEGATIVE_TERMS):
        return 20
    return 0


def score_legitimacy(domain_result: dict, existence_result: dict) -> int:
    points = 0

    # New domain (under 180 days) is a red flag
    if domain_result.get("age_days") is not None and domain_result["age_days"] < 180:
        points += 8

    # No sign of the company existing online (LinkedIn, registration mentions).
    # If the search itself failed, we don't know anything, so don't penalize.
    if existence_result.get("error") is None and existence_result.get("search_results_count", 0) == 0:
        points += 7

    return min(points, 15)  # cap at 15, matching our weighting scheme


def get_verdict_label(score: int) -> str:
    if score >= 50:
        return "SCAM"
    elif score >= 20:
        return "SUSPICIOUS"
    return "LEGIT"


def run_verdict_engine(posting_text: str) -> dict:
    """
    Runs all four signals and combines them into one suspicion score (0-100).
    """
    # Turn the posting text into a short, unique label for caching
    cache_key = "scan:" + hashlib.sha256(posting_text.encode()).hexdigest()

    # Check the cache first - was this exact posting already scanned?
    cached_result = redis.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # 1. LLM analysis (also gives us company name + domain)
    llm_raw = analyze_with_llm(posting_text)
    llm_parsed = parse_llm_output(llm_raw)

    # Retry once if company name extraction failed - LLM output can be inconsistent
    if llm_parsed["company_name"] == "Unknown":
        llm_raw = analyze_with_llm(posting_text)
        llm_parsed = parse_llm_output(llm_raw)

    # 2. Keyword filter
    keyword_result = keyword_filter(posting_text)

    # 3. Reddit evidence + company existence (both use the LLM-extracted company name)
    company_name = llm_parsed["company_name"]
    reddit_results = []
    existence_result = {"search_results_count": 0, "has_linkedin_page": False}
    if company_name and company_name != "Unknown":
        reddit_results = search_reddit_evidence(f"{company_name} scam")
        existence_result = check_company_existence(company_name)

    # 4. Domain age (only if we have a usable domain)
    domain = llm_parsed["domain"]
    domain_result = {"age_days": None, "error": "No domain stated in posting"}
    if domain and domain != "None":
        domain_result = check_domain_age(domain)

    # Score each signal
    llm_score = score_llm_verdict(llm_parsed["verdict"])
    keyword_score = score_keyword_filter(keyword_result)
    reddit_score = score_reddit_evidence(reddit_results, company_name)
    legitimacy_score = score_legitimacy(domain_result, existence_result)

    total_score = llm_score + keyword_score + reddit_score + legitimacy_score
    final_verdict = get_verdict_label(total_score)

    result = {
        "suspicion_score": total_score,
        "verdict": final_verdict,
        "company_name": company_name,
        "breakdown": {
            "llm_score": llm_score,
            "llm_verdict": llm_parsed["verdict"],
            "keyword_score": keyword_score,
            "keyword_matches": keyword_result["matched_keywords"],
            "reddit_score": reddit_score,
            "reddit_results_found": len(reddit_results),
            "legitimacy_score": legitimacy_score,
            "domain_age_days": domain_result.get("age_days"),
            "company_found_online": existence_result.get("search_results_count", 0) > 0,
        }
    }

    # Cache the result for next time (expires after 24 hours)
    redis.set(cache_key, json.dumps(result), ex=86400)

    return result


if __name__ == "__main__":
    posting_text = """We're Hiring: Site Reliability Engineer
LSEG (London Stock Exchange Group) is looking for a Site Reliability Engineer to join our team in Bengaluru, India.
This is a hybrid role, full-time position. LSEG is a global financial markets infrastructure and data provider.
Apply through our official careers page.

"""  # <- added a blank line to force a fresh, non-cached run

    result = run_verdict_engine(posting_text)
    print(result)