## Rule-based vs LLM-based classification (Day 4 finding)

Before committing to an LLM as the primary detection signal, I built a simple rule-based keyword filter as a baseline, using a curated list of known scam-recruiting phrases (upfront fee language, money-transfer requests, guaranteed-outcome claims, suspicious interview channels).

**Result:** the keyword filter had 100% precision (zero false positives across 10 real test samples) but 0% recall on the 3 scam-labeled samples — it caught none of them.

**Why:** modern recruiting scams have moved past obvious giveaway phrases like "wire transfer" or "send gift cards." The scam samples in my test set used plausible, soft language instead — an unverifiable partnership claim, an artificially tight deadline, a vague "training program" — none of which map to any fixed keyword. The individual words used are mundane on their own (e.g. "training," "fee," "materials"); only the *combination and context* make them suspicious, which a substring-matching filter structurally cannot detect.

**Conclusion:** this empirically justified using an LLM as the primary red-flag detector rather than a cheaper rule-based approach, since context-dependent reasoning is required to catch the scam patterns actually present in real postings. The keyword filter still has value as a fast, free, zero-cost pre-check for the most blatant/obvious cases, but cannot serve as the primary signal.

The LLM approach (structured v2 prompt with role/task/constraints/output-format/one-shot example) performed better on recall (correctly flagged 2 of 3 scams as at least SUSPICIOUS) but introduced false positives on 3 legitimate postings, and — notably — missed the same hardest scam sample (a plausible-sounding "email & chat process intern" posting) that the keyword filter also missed. This is direct evidence for why the project uses an ensemble of independent signals (LLM analysis + Reddit evidence + company legitimacy checks) rather than relying on any single classifier: no single approach reliably catches sophisticated scams without either missing real threats or over-flagging legitimate postings.
