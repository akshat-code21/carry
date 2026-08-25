ENTITY_EXTRACTION_PROMPT = """\
You are an expert investment analyst extracting structured information from investor communications.

Analyze the following text excerpt and extract:
1. Companies mentioned (with their ticker symbols if identifiable)
2. Investment themes or macro topics discussed
3. Key people mentioned
4. The sentiment expressed toward each company (bullish/bearish/neutral/mixed)
5. Conviction level (high/medium/low) based on language strength

High conviction indicators: "core holding", "significant position", "adding aggressively", "highest conviction", "very confident"
Medium conviction: "like", "interesting", "watching closely", "reasonable position"
Low conviction: "small position", "speculative", "hedging", "monitoring"

Return a JSON array of entities. Each entity must match exactly:
{{
  "entity_type": "company|ticker|person|theme|macro_theme",
  "entity_name": "Full name or description",
  "ticker_symbol": "TICKER or null",
  "sentiment": "bullish|bearish|neutral|mixed",
  "conviction_level": "high|medium|low|unknown",
  "context_snippet": "1-2 sentence direct quote or paraphrase supporting this extraction"
}}

Rules:
- Only include ticker symbols that follow the format [A-Z]{{1,5}} (e.g. AAPL, GOOGL, BRK.A)
- If unsure about a ticker, set ticker_symbol to null
- For themes and macro topics, set ticker_symbol to null
- Return an empty array [] if no relevant entities found

TEXT:
{chunk_text}

Respond with ONLY the JSON array, no other text.
"""
