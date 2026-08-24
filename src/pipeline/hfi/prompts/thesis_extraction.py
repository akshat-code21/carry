THESIS_EXTRACTION_PROMPT = """\
You are an expert investment analyst. Extract the core investment thesis for each company discussed in the text below.

For each company with a meaningful discussion, return a thesis object. Focus on:
- WHY the investor likes or dislikes the position
- Specific catalysts mentioned
- Risks acknowledged
- Time horizon signals ("near-term", "over the next few years", etc.)
- Position sizing language ("core holding", "small position", "trimming")

Return a JSON array of thesis objects:
{{
  "company": "Full company name",
  "ticker": "TICKER or null",
  "thesis_summary": "2-3 sentence summary of the investor's view",
  "bullish_points": ["point 1", "point 2"],
  "bearish_points": ["concern 1", "concern 2"],
  "catalysts": ["catalyst 1", "catalyst 2"],
  "risks": ["risk 1", "risk 2"],
  "conviction_score": 7
}}

conviction_score is 0-10:
- 8-10: "highest conviction", "core holding", "very significant position", "extremely confident"
- 5-7: "like", "good risk/reward", "reasonable position", "watching"
- 1-4: "speculative", "small position", "uncertain", "hedging"
- 0: mentioned briefly with no clear view

Only include companies with at least 2-3 sentences of substantive discussion.
Return [] if no companies have sufficient discussion.

TEXT:
{full_text}

Respond with ONLY the JSON array, no other text.
"""
