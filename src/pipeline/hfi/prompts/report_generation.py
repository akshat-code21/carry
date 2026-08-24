INVESTOR_REPORT_PROMPT = """\
You are a senior investment analyst generating a structured intelligence report.

Investor: {investor_name}
Period: {period_start} to {period_end}
Sources analyzed: {source_count}
New content items: {content_count}

EXTRACTED ENTITIES AND MENTIONS:
{entities_json}

INVESTMENT THESES:
{theses_json}

PORTFOLIO CHANGES (13F):
{portfolio_changes_json}

PREVIOUS REPORT SUMMARY (for continuity):
{previous_summary}

Generate a comprehensive intelligence report in the EXACT markdown format below.
Be specific, cite actual companies and tickers, and use the extracted data above.
Do not invent information not present in the extracted data.

---

# Intelligence Report: {investor_name}
**Generated:** {generated_at}
**Period:** {period_start} — {period_end}
**Sources analyzed:** {source_count} | **New content items:** {content_count}

---

## Executive Summary
[2-3 sentence AI-generated summary of the most important developments this period]

---

## Key Observations
[Bulleted list of 3-7 most significant findings. Be specific — mention companies, tickers, themes.]

---

## Companies Discussed
| Company | Ticker | Sentiment | Conviction | Context |
|---------|--------|-----------|------------|---------|
[One row per company. Use 🟢 for bullish, 🔴 for bearish, 🟡 for neutral/mixed]

---

## Bullish Signals
[For each bullish company/theme: investor's thesis, catalysts mentioned, key supporting quote]

---

## Bearish Signals
[For each bearish company/theme: investor's concerns, risks cited, supporting context]

---

## Conviction Indicators
[Language analysis: identify positions described as "core", "significant", "adding", "trimming"]
- **Strong Conviction:** [companies with highest-conviction language]
- **Monitoring:** [companies mentioned with lower conviction]

---

## Portfolio Changes (from latest 13F)
**Filing Period:** {filing_period}
**New Positions:** [list or "None"]
**Increased:** [list or "None"]
**Decreased:** [list or "None"]
**Closed:** [list or "None"]

---

## Source Links
{source_links}
"""
