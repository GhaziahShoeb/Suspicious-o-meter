(venv) ghaziah@Ghaziahs-MacBook-Air Suspicious-o-meter % python test_prompt_all.py

============================================================
POSTING 1 — expected: SCAM
============================================================
RED FLAGS:
- The message imposes a strict enrollment deadline of 11:00 AM tomorrow without providing any instructions, contact details, or verification of the program’s legitimacy, creating undue urgency.

VERDICT: SUSPICIOUS

CONFIDENCE: MEDIUM

REASONING: The urgent deadline coupled with the absence of details or verification suggests a manipulative approach typical of dubious recruitment schemes, though the message does not contain clear financial or personal‑information requests that would indicate a definitive scam.

============================================================
POSTING 2 — expected: LEGIT
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: MEDIUM

REASONING: The message contains a standard job description, a LinkedIn link, and a request to submit a resume via email, with no indications of payment, urgency, or other scam patterns.

============================================================
POSTING 3 — expected: AMBIGUOUS
============================================================
RED FLAGS:
None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The message contains only standard internship details, a legitimate Google Form link, and no requests for money or other fraudulent behaviors, indicating a likely legitimate opportunity.

============================================================
POSTING 4 — expected: LEGIT
============================================================
RED FLAGS:
None found

VERDICT: LEGIT

CONFIDENCE: MEDIUM

REASONING: The message contains standard job posting details and a request for applicants to email a contact address; no patterns of fraud or deceptive requests are present, though the authenticity of the company and contact information cannot be verified from this text alone.

============================================================
POSTING 5 — expected: SCAM
============================================================
RED FLAGS:
- None found

VERDICT: SUSPICIOUS

CONFIDENCE: LOW

REASONING: The message is extremely brief, lacking any contact details, job description, or next‑step instructions, so there is insufficient context to determine legitimacy; additional information such as official contact email, program details, or a verifiable company website would be needed.

============================================================
POSTING 6 — expected: LEGIT
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The message only advertises a generic entry‑level IT role and requests resumes via email, with no requests for money, urgent deadlines, or other typical scam indicators.

============================================================
POSTING 7 — expected: AMBIGUOUS
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The posting provides specific job details, a stipend range, and clear responsibilities without any requests for money, urgency cues, or vague language that would indicate manipulation or deception.

============================================================
POSTING 8 — expected: SCAM
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The message contains only standard job posting details (role, responsibilities, stipend, application deadline) without any request for money, vague terms, urgency, or other typical scam patterns.

============================================================
POSTING 9 — expected: SCAM (text alone won't reveal this - confirmed via external report)
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The message provides a clear company background, role description, and qualifications without any payment requests, urgent language, or vague promises, showing no indicators of manipulation or deception.

============================================================
POSTING 10 — expected: LEGIT
============================================================
RED FLAGS:
- None found

VERDICT: LEGIT

CONFIDENCE: HIGH

REASONING: The message consists solely of a straightforward internship posting with no requests for payment, personal data, or other deceptive content.
(venv) ghaziah@Ghaziahs-MacBook-Air Suspicious-o-meter % 

#	Expected	Got	Verdict
1	SCAM	SUSPICIOUS	close ✅
2	LEGIT	LEGIT	✅
3	AMBIGUOUS	LEGIT	ok
4	LEGIT	LEGIT	✅
5	SCAM	SUSPICIOUS(LOW)	better, still miss
6	LEGIT	LEGIT	✅
7	AMBIGUOUS	LEGIT	ok
8	SCAM	LEGIT	❌ miss
9	SCAM(external)	LEGIT	✅ expected
10	LEGIT	LEGIT	✅

#	Expected	v1 result	v2 result
1	SCAM	Suspicious ✅	SUSPICIOUS ✅
2	LEGIT	❌ false positive	LEGIT ✅
3	AMBIGUOUS	Suspicious (ok)	LEGIT (ok)
4	LEGIT	❌ false positive	LEGIT ✅
5	SCAM	Scam ✅	SUSPICIOUS(LOW) — close
6	LEGIT	❌ EMPTY	LEGIT ✅
7	AMBIGUOUS	Suspicious (ok)	LEGIT (ok)
8	SCAM	❌ EMPTY	LEGIT ❌ (still a miss)
9	SCAM(ext)	❌ EMPTY	LEGIT ✅ (expected, text-only limit)
10	LEGIT	❌ cut off	LEGIT ✅]

Step 4: Full comparison table
Posting	Expected	Keyword filter	LLM (v2 prompt)
1	SCAM	❌ missed (not flagged)	✅ SUSPICIOUS (close)
2	LEGIT	✅ correct (not flagged)	❌ SUSPICIOUS (false positive)
3	AMBIGUOUS	✅ not flagged	✅ LEGIT (defensible)
4	LEGIT	✅ correct	✅ LEGIT
5	SCAM	❌ missed	✅ SUSPICIOUS (close)
6	LEGIT	✅ correct	❌ SUSPICIOUS (false positive)
7	AMBIGUOUS	✅ not flagged	✅ LEGIT (defensible)
8	SCAM	❌ missed	❌ LEGIT (worst miss, both approaches)
9	SCAM (text-invisible)	❌ missed (expected)	❌ LEGIT (expected — structural gap)
10	LEGIT	✅ correct	❌ SUSPICIOUS (false positive)