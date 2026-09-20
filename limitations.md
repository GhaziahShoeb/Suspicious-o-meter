**Known limitation: Reddit evidence scoring uses keyword presence, not sentiment**

- The scoring only checks whether words like "scam," "fraud," or "warning" appear anywhere near a mention of the company — it doesn't judge what the sentence is actually saying
- This means it can't distinguish between:
  - The company itself being reported as fraudulent
  - The company being impersonated by scammers (a different problem entirely)
  - A neutral or even positive mention that happens to contain the word "scam" nearby (e.g. "X is legit, scammers copied their name")
- Result: LSEG (a real company) scored SUSPICIOUS (47) partly because of a Reddit post explicitly saying *"lseg.com is legit... scammers copied from them"* — the word "scammers" triggered a positive score even though the sentence was vouching for the company
- **Root cause:** keyword co-occurrence is a weak proxy for meaning; a phrase can contain "scam" without claiming the company is a scam
- **A real fix would require:** sentiment/stance classification (likely another LLM call) to judge whether each Reddit result is actually accusing the company of fraud, warning about impersonation, or something unrelated — rather than just checking for word presence
- **Tradeoff accepted for this project's timeline:** documented as a known gap rather than solved, given the added complexity and cost of a second LLM-based judgment step