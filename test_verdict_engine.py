from verdict_engine import (
    score_llm_verdict,
    score_keyword_filter,
    score_reddit_evidence,
    score_legitimacy,
    get_verdict_label,
    parse_llm_output,
)


# ---- score_llm_verdict ----
def test_score_llm_verdict_scam():
    assert score_llm_verdict("SCAM") == 30

def test_score_llm_verdict_suspicious():
    assert score_llm_verdict("SUSPICIOUS") == 15

def test_score_llm_verdict_legit():
    assert score_llm_verdict("LEGIT") == 0

def test_score_llm_verdict_unknown():
    assert score_llm_verdict("UNKNOWN") == 0


# ---- score_keyword_filter ----
def test_score_keyword_filter_flagged():
    assert score_keyword_filter({"flagged": True, "matched_keywords": ["wire transfer"]}) == 15

def test_score_keyword_filter_not_flagged():
    assert score_keyword_filter({"flagged": False, "matched_keywords": []}) == 0


# ---- score_reddit_evidence (this is the function with the real bug history) ----
def test_score_reddit_evidence_no_results():
    assert score_reddit_evidence([], "Acme Corp") == 0

def test_score_reddit_evidence_unknown_company():
    results = [{"title": "some scam", "snippet": "totally a scam"}]
    assert score_reddit_evidence(results, "Unknown") == 0

def test_score_reddit_evidence_irrelevant_results_dont_count():
    # This is the exact false-positive pattern found during real testing (Day 12):
    # results mentioning generic/unrelated companies should NOT count as evidence.
    results = [
        {"title": "Some totally unrelated scam", "snippet": "JP Morgan investment scam warning"},
        {"title": "Coinbase scam", "snippet": "crypto scam via Coinbase"},
    ]
    assert score_reddit_evidence(results, "A Neumann & Associates, LLC") == 0

def test_score_reddit_evidence_relevant_strong_negative():
    results = [
        {"title": "Acme Corp is a total scam", "snippet": "avoid Acme Corp, never join"}
    ]
    assert score_reddit_evidence(results, "Acme Corp") == 40

def test_score_reddit_evidence_relevant_mild_negative():
    results = [
        {"title": "Is Acme Corp legit?", "snippet": "feeling a bit unsure about Acme Corp"}
    ]
    assert score_reddit_evidence(results, "Acme Corp") == 20


# ---- score_legitimacy ----
def test_score_legitimacy_new_domain_and_not_found():
    domain_result = {"age_days": 30}
    existence_result = {"search_results_count": 0}
    assert score_legitimacy(domain_result, existence_result) == 15

def test_score_legitimacy_old_domain_and_found():
    domain_result = {"age_days": 5000}
    existence_result = {"search_results_count": 3}
    assert score_legitimacy(domain_result, existence_result) == 0

def test_score_legitimacy_unknown_domain_age():
    domain_result = {"age_days": None}
    existence_result = {"search_results_count": 2}
    assert score_legitimacy(domain_result, existence_result) == 0


# ---- get_verdict_label ----
def test_get_verdict_label_scam():
    assert get_verdict_label(50) == "SCAM"
    assert get_verdict_label(100) == "SCAM"

def test_get_verdict_label_suspicious():
    assert get_verdict_label(20) == "SUSPICIOUS"
    assert get_verdict_label(49) == "SUSPICIOUS"

def test_get_verdict_label_legit():
    assert get_verdict_label(0) == "LEGIT"
    assert get_verdict_label(19) == "LEGIT"


# ---- parse_llm_output ----
def test_parse_llm_output_full_response():
    llm_text = """COMPANY_NAME: Acme Corp

DOMAIN: acme.com

RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: Looks fine."""
    result = parse_llm_output(llm_text)
    assert result["company_name"] == "Acme Corp"
    assert result["domain"] == "acme.com"
    assert result["verdict"] == "LEGIT"
    assert result["confidence"] == "HIGH"

def test_parse_llm_output_missing_fields_defaults():
    llm_text = "Some malformed response with no structure"
    result = parse_llm_output(llm_text)
    assert result["company_name"] == "Unknown"
    assert result["verdict"] == "UNKNOWN"