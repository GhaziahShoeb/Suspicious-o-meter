# Suspicious-o-meter

A browser extension + backend that automatically scans job postings and emails for scam red flags. It combines LLM-based text analysis, real-world evidence from Reddit/web search, and company legitimacy checks (domain age, online presence) into a single suspicion score — rather than relying on any one signal alone.

**Live backend:** https://suspicious-o-meter.onrender.com

## The problem

Job and internship scams increasingly avoid obvious giveaway language ("wire us money," "send gift cards") in favor of plausible, well-written postings — fake training programs, unverifiable partnership claims, artificial urgency. A simple keyword filter cannot catch these; a single LLM call reading only the posting text can miss them too, since some scams have no textual red flags at all and are only identifiable through external evidence (e.g. public reports elsewhere).

## Architecture

```
Browser extension (content script)
   → extracts posting/email text from the page
   → sends to backend /scan endpoint

Backend (FastAPI)
   → runs 4 independent signals in sequence:
       1. Keyword filter        (fast, free, catches only the most blatant cases)
       2. LLM analysis (Groq)   (structured prompt: role/task/constraints/output format)
       3. Reddit/web evidence   (via Serper search API, relevance-filtered)
       4. Legitimacy checks     (WHOIS domain age + online presence)
   → combines all 4 into one weighted suspicion score (0-100)
   → caches the result in Redis (keyed by content hash, 24h expiry)
   → returns score + verdict + per-signal breakdown

Extension UI
   → toolbar badge (color-coded score)
   → floating on-page banner
   → popup with LLM / Reddit / Legitimacy tabs
```

## Tech stack

- **Backend:** Python, FastAPI, deployed on Render
- **LLM:** Groq (`openai/gpt-oss-20b`)
- **Evidence search:** Serper (Google Search API) — used for Reddit evidence retrieval, pivoted from Reddit's own API after their new approval requirement made direct access impractical within the project timeline
- **Legitimacy checks:** WHOIS API (domain age) + Serper-based company existence check (OpenCorporates application submitted but pending approval, so this is a documented interim substitute)
- **Caching:** Redis (Upstash)
- **Rate limiting:** slowapi (10 requests/minute per IP)
- **Error monitoring:** Sentry
- **Extension:** Manifest V3, vanilla JS content script + popup
- **Testing:** pytest (endpoint tests + isolated scoring-logic tests)

## Ensemble scoring

Each signal contributes points toward the total suspicion score:

| Signal | Max points |
|---|---|
| LLM verdict | 30 (SCAM=30, SUSPICIOUS=15, LEGIT=0) |
| Keyword filter | 15 |
| Reddit/web evidence | 40 |
| Legitimacy checks | 15 |

**0-19 → LEGIT · 20-49 → SUSPICIOUS · 50-100 → SCAM**

Reddit evidence is weighted highest because it represents real-world corroboration rather than a text-only guess — during development, this signal caught a scam (a fake internship listing) that both the LLM and keyword filter scored as completely clean.

## Known limitations

- **No single signal is reliable alone.** A rule-based keyword filter, tested against real scam samples, achieved 100% precision but 0% recall — it caught none of the real scams, because modern scam language avoids obvious trigger words. This is the empirical justification for the ensemble approach.
- **Some scams are undetectable by this system.** A posting with no textual red flags and no public online trace (no Reddit reports, a plausible legitimacy footprint) will score as LEGIT. This was confirmed directly during testing with a fabricated-company sample.
- **Reddit evidence scoring uses keyword presence, not sentiment.** The system can distinguish irrelevant results from relevant ones (via company-name matching), but cannot yet distinguish "this company is a scam" from "this company was impersonated by scammers" or "this company is legit, scammers copied their name" — all of which can trigger similar keyword matches. A more accurate approach would require a dedicated sentiment/stance classification step.
- **Company-name and domain extraction from LLM output is not fully reliable**, especially on long, messy real-webpage text (vs. curated test samples). Incorrect extraction can lead to searching the wrong entity.
- **LLM verdicts are not fully deterministic** — the same posting can occasionally receive different verdicts across runs.
- **Reddit's official API now requires an approval process** that wasn't feasible within the project timeline; evidence retrieval uses a general search API with a Reddit filter as a substitute.
- **OpenCorporates access is pending approval**; company legitimacy currently relies on a search-based proxy rather than an authoritative company registry.
- **Render's free tier spins down after inactivity**, so the first request after a period of idleness can take 50+ seconds.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your own API keys
uvicorn main:app --reload
```

Load the extension via `chrome://extensions` → Developer mode → Load unpacked → select the `extension/` folder.

## Testing

```bash
pytest test_main.py -v            # endpoint-level tests
pytest test_verdict_engine.py -v  # scoring logic tests (no API calls, fast)
```