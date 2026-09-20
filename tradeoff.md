Here's the tradeoff, in plain terms.

## Before the fix
Your Reddit-matching was **loose** — it counted a result as relevant if even one word overlapped with the company name.

- **Good side:** it caught more real evidence, even if worded a bit differently
- **Bad side:** it also caught garbage — completely unrelated posts that just happened to share a generic word, like "Associates" or "LSE" — causing real companies to get wrongly flagged (false positives)

## After the fix
Your Reddit-matching is now **strict** — it only counts a result if the entire company name appears as an exact phrase.

- **Good side:** it correctly threw out the garbage — unrelated scams about totally different companies no longer count
- **Bad side:** it can also throw out *real, relevant* evidence if the wording doesn't match exactly — like that LSEG result that genuinely was about a scam using LSEG's name, but got missed because the exact search phrase didn't match

## The simple version

You made your system **more careful about not crying wolf** (fewer false positives, good) — but in doing so, it's now also a bit **more likely to miss things that are worded slightly differently** (more false negatives, not as good).

You can't fully avoid both problems at once with a simple rule like this — being stricter always trades away some recall to gain precision, and being looser does the opposite. This is a real, normal tradeoff in building any detection system, not a mistake you made.

**Limitation:** Reddit scoring counts keyword presence ("scam," "fraud"), not meaning — so it can't tell "LSEG is a scam" from "scammers impersonated LSEG" or "LSEG is legit, scammers copied them." A real fix needs sentiment analysis (another LLM call), not just keyword matching.

**Tradeoff:** loosening the match to catch more real evidence (better recall) also let in these misleading keyword-only matches (worse precision) — you can't fix one without risking the other with this simple approach.