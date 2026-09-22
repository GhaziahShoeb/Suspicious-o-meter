import hashlib
import json
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

from keyword_filter import keyword_filter
from llm_analyzer import analyze_with_llm
from reddit_search import search_reddit_evidence
from legitimacy_checker import check_domain_age, check_company_existence

# Resilient Caching Layer with In-Memory TTL Fallback
_in_memory_cache: dict[str, tuple[float, str]] = {}
_redis_client = None
_redis_initialized = False

def get_cache_backend():
    """Lazily and safely gets the Upstash Redis client or falls back to in-memory."""
    global _redis_client, _redis_initialized
    if not _redis_initialized:
        _redis_initialized = True
        redis_url = os.environ.get("REDIS_URL")
        redis_token = os.environ.get("REDIS_TOKEN")
        if redis_url and redis_token:
            try:
                from upstash_redis import Redis
                _redis_client = Redis(url=redis_url, token=redis_token)
            except Exception:
                _redis_client = None
        else:
            _redis_client = None
    return _redis_client

def get_cached_verdict(cache_key: str) -> dict | None:
    redis = get_cache_backend()
    if redis:
        try:
            val = redis.get(cache_key)
            if val:
                return json.loads(val)
        except Exception:
            pass  # Fall back to in-memory cache on connection issue

    entry = _in_memory_cache.get(cache_key)
    if entry:
        expires_at, data = entry
        if time.time() < expires_at:
            return json.loads(data)
        else:
            del _in_memory_cache[cache_key]
    return None

def set_cached_verdict(cache_key: str, result: dict, ttl_seconds: int = 86400):
    val_str = json.dumps(result)
    redis = get_cache_backend()
    if redis:
        try:
            redis.set(cache_key, val_str, ex=ttl_seconds)
            return
        except Exception:
            pass  # Fall back to in-memory cache

    # In-memory storage with expiry
    _in_memory_cache[cache_key] = (time.time() + ttl_seconds, val_str)

# Words that suggest real, confirmed scam reports when found in Reddit evidence
STRONG_NEGATIVE_TERMS = ["scam", "fraud", "never join", "avoid", "warning", "fake"]
MILD_NEGATIVE_TERMS = ["careful", "unsure", "suspicious", "concerned", "risky"]


def parse_llm_output(llm_text: str) -> dict:
    """
    Pulls structured fields out of the LLM's plain-text response.
    Validates fields to prevent malformed values from propagating.
    """
    def extract(field, text, default="Unknown"):
        match = re.search(rf"{field}:\s*(.+)", text, re.IGNORECASE)
        if match:
            # Strip tags and excess whitespace
            val = re.sub(r"[<>]", "", match.group(1)).strip()
            return val if val else default
        return default

    verdict_raw = extract("VERDICT", llm_text, default="UNKNOWN").upper()
    verdict = verdict_raw if verdict_raw in ("LEGIT", "SUSPICIOUS", "SCAM") else "UNKNOWN"

    confidence_raw = extract("CONFIDENCE", llm_text, default="LOW").upper()
    confidence = confidence_raw if confidence_raw in ("LOW", "MEDIUM", "HIGH") else "LOW"

    return {
        "company_name": extract("COMPANY_NAME", llm_text, default="Unknown"),
        "domain": extract("DOMAIN", llm_text, default="None"),
        "verdict": verdict,
        "confidence": confidence,
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
    if not reddit_results or not company_name or company_name.lower() == "unknown":
        return 0

    # Split into meaningful words, ignoring tiny/common ones
    stopwords = {"the", "and", "of", "inc", "llc", "ltd", "group", "associates", "company"}
    company_words = [w for w in company_name.lower().replace(",", "").split() if w not in stopwords and len(w) > 2]

    if not company_words:
        return 0

    relevant_results = []
    for r in reddit_results:
        text = (r.get("title", "") + " " + r.get("snippet", "")).lower()
        matches = sum(1 for w in company_words if w in text)
        # Require at least half the meaningful words to match, not just one
        if matches >= max(1, len(company_words) // 2):
            relevant_results.append(r)

    if not relevant_results:
        return 0

    combined_text = " ".join((r.get("title", "") + " " + r.get("snippet", "")).lower() for r in relevant_results)

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

    # No sign of the company existing online (LinkedIn, registration mentions)
    if existence_result.get("search_results_count", 0) == 0:
        points += 7

    return min(points, 15)  # cap at 15, matching our weighting scheme


def get_verdict_label(score: int) -> str:
    if score >= 50:
        return "SCAM"
    elif score >= 20:
        return "SUSPICIOUS"
    return "LEGIT"


def normalize_posting_text(text: str) -> str:
    """Normalizes whitespace to prevent simple cache-busting by trailing spaces/newlines."""
    return " ".join(text.split()).strip()


def run_verdict_engine(posting_text: str) -> dict:
    """
    Runs all four signals and combines them into one suspicion score (0-100).
    Normalizes text for robust caching.
    """
    normalized_text = normalize_posting_text(posting_text)
    cache_key = "scan:" + hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    # Check cache first
    cached_result = get_cached_verdict(cache_key)
    if cached_result:
        return cached_result

    # 1. LLM analysis (also gives us company name + domain)
    llm_raw = analyze_with_llm(posting_text)
    llm_parsed = parse_llm_output(llm_raw)

    # Retry once if company name extraction failed - LLM output can be inconsistent
    if llm_parsed["company_name"] == "Unknown":
        llm_raw = analyze_with_llm(posting_text)
        llm_parsed = parse_llm_output(llm_raw)

    # 2. Keyword filter
    keyword_result = keyword_filter(posting_text)

    # 3. Reddit evidence (search ONCE per scan)
    company_name = llm_parsed["company_name"]
    reddit_results = []
    if company_name and company_name.lower() != "unknown":
        reddit_results = search_reddit_evidence(f"{company_name} scam")

    # 4. Legitimacy checks
    domain = llm_parsed["domain"]
    domain_result = {"age_days": None, "error": "No domain stated in posting"}
    if domain and domain.lower() != "none":
        domain_result = check_domain_age(domain)

    # Call company existence check properly
    existence_result = {"search_results_count": 0, "has_linkedin_page": False}
    if company_name and company_name.lower() != "unknown":
        existence_result = check_company_existence(company_name)

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

    # Cache result (expires after 24 hours)
    set_cached_verdict(cache_key, result, ttl_seconds=86400)

    return result


if __name__ == "__main__":
    sample_text = """We're Hiring: Site Reliability Engineer
LSEG (London Stock Exchange Group) is looking for a Site Reliability Engineer to join our team in Bengaluru, India.
This is a hybrid role, full-time position. LSEG is a global financial markets infrastructure and data provider.
Apply through our official careers page."""
    result = run_verdict_engine(sample_text)
    print(result)