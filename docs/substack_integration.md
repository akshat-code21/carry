# Substack Integration Plan - Feasibility, Legality, and Implementation

> **Goal:** Add Substack newsletters as a first-class content source alongside YouTube, Reddit, Twitter/X, and News.

**Status:** Feasibility confirmed ✅ · Implementable at near-zero API cost · Dated 2026-08-29

---

## 1. Is there an official API?

**No. Substack has no official public developer API for reading content.** What actually exists (all verified live at research time):

| Access method | Status | What you get | Cost |
|---|---|---|---|
| **RSS feed** - `https://{pub}.substack.com/feed` (works on custom domains too) | ✅ Public, intended for syndication | Title, link, pubDate, full body for **free** posts; **truncated preview + paywall stub** for paid posts | Free |
| **Unofficial JSON API** - `/api/v1/archive`, `/api/v1/posts/{slug}`, `/api/v1/publication` (same endpoints substack.com's own web app calls) | ⚠️ Unofficial, no auth needed for public content | Everything RSS gives **plus**: reactions, restacks, subtitle, cover image, pagination back through the entire archive | Free |
| **Unofficial Python client** - [`substack_api` (NHagar)](https://github.com/NHagar/substack_api), 222★, actively maintained | ⚠️ Wraps the above; can access *your own* paid subscriptions with your own `substack.sid` cookie | Full text of paywalled posts **only if you're a paying subscriber** | Free |
| **Email ingestion** - subscribe and parse your own inbox | ✅ Fully legitimate | Full text of whatever tier you subscribe to | Subscription price |

### Live verification highlights

- ✅ `https://www.readtrung.com/feed` → valid RSS with full metadata; `/api/v1/archive?sort=new&limit=1&offset=0` → rich JSON (reactions, restacks, canonical URLs confirmed in the response).
- ⚠️ **Michael Burry's *Cassandra Unchained*** (`cassandraunchained.substack.com`) returned **HTTP 404 - "publication flagged as Potential Violation of Substack's content guidelines"** from the research environment. It is also a **paid** publication, so even via RSS/unofficial API you would only get previews without a paid subscription.

### Target publications

| Publication | Notes |
|---|---|
| ETF Investments | Exact subdomain needs discovery (one-time) |
| Brevarthan Research | Exact subdomain needs discovery |
| Aurelion Research | Exact subdomain needs discovery |
| TJ Terwillinger | Exact subdomain needs discovery |
| Michael Burry - Cassandra Unchained | ⚠️ Currently flagged on Substack + paid-only → only usable via email/own-subscription path |
| Multibagger Ideas | Exact subdomain needs discovery |

**Feasibility verdict: YES - high feasibility, near-zero monetary cost**, with one honest caveat: **paywalled full text cannot be legitimately obtained without being a paid subscriber.** Free posts + previews + your own paid subscriptions = fully workable.

---

## 2. Legal & ethics - "doesn't a workaround exploit their API costs, and is it legal?"

The answer has three layers:

### 2a. RSS - nothing is being exploited
Substack *deliberately publishes* RSS for syndication. There is no per-call billing to circumvent; Substack's only "cost" is bandwidth, and polling ~6 publications once every 15–60 min is a few thousand requests/month - trivial. This is the same model as the existing `NewsCollector` (Google News RSS). **Legality: clean.**

### 2b. Unofficial JSON API - not illegal, but a ToS gray zone
The endpoints are public, unauthenticated, and identical to what every browser visiting a Substack page executes. No hacking, no auth bypass, no CFAA-type issue - it is a *civil contract* matter, not criminal. Risks:
- IP throttling/blocks
- Endpoints changing without notice
- ToS violation exposure

Note: the codebase **already accepts this tradeoff** - `twikit` (unofficial X scraping) and `curl_cffi` (browser impersonation) are used in the Twitter collector. Substack's gray zone is considerably *safer* than the current X approach.

### 2c. What we do differently - the differentiator AND the strongest legal position
Substack sells raw text; nobody pays them for analysis. We do not republish - we **transform**:

- **Ticker mapping** - RSS has no symbol concept; the existing theme-ticker engine makes a Burry post queryable as `$NVDA` alongside his YouTube/Reddit/X counterparts (cross-source correlation Substack does not offer at all).
- **Prediction extraction + accuracy tracking** - via the existing LLM pipeline (`src/pipeline/analysis.py`) and `performance_service.py` (yfinance 1d/1w/1m returns).
- **FinBERT scoring, hybrid search, embeddings** - reused as-is.
- **Link-out + short snippet** display (Google News model) rather than full-text republication - keeps the product on the right side of copyright, since facts/ideas are not copyrightable while verbatim full-text republication of paywalled content would be.

**The real risk is not legality - it is breakage.** Mitigation: RSS as the primary stable channel, JSON API behind a feature flag as optional enrichment, email path for paywalled full text.

---

## 3. Implementation Plan (mapped to the codebase)

Your architecture has **two natural integration points**, and Substack slots into both cleanly. Articles are the *easiest* content class you have - no Whisper, no transcripts, and `html2text` is already a dependency.

### Step 0 - Publication discovery (small script, ~1 hr)
- Resolve exact subdomains for the six target publications.
- Re-check Burry's flagged status; `substack_api` even handles handle-rename redirects.
- Store as seed config.

### Step 1 - Schema changes (Alembic migration)
- Add `"substack"` to `SourceName` enum in `src/schemas/market_chatter.py`.
- Add `"substack"` to `HfiSourceTypeEnum` in `src/models/hfi_source.py` (the enum already has `rss`, `twitter`, `youtube` - Substack is a peer, not a hack).

### Step 2 - `SubstackAdapter` in HFI ingestion (primary path)
- New `src/services/hfi/ingestion/substack_adapter.py` implementing `BaseAdapter` (only `sec_adapter.py` exists today - this fills the pattern).
- RSS-first parsing (reuse the `xml.etree` pattern from `news_collector.py`), body → markdown via `html2text`, dedup via existing `content_hasher.py`, paywall-preview flagging, conditional-GET caching (ETag/Last-Modified stored in `HfiSource.config` JSONB - column already exists).
- Fits the investor model perfectly: these newsletters are *investor sources* - the HFI investor/sources UI (`web/src/app/(app)/investors/[id]/page.tsx`) already lets users add sources by URL.

### Step 3 - Optional `SubstackEnricher` (feature-flagged)
- `/api/v1/archive` paginated backfill (RSS only returns ~10 recent items - this unlocks history) + reactions/restacks as engagement signals.
- Gated behind an `ENABLE_SUBSTACK_JSON_API` config flag, token-bucket rate limiting, graceful degradation if endpoints break (mirrors the `social_context_service.py` "graceful degradation" pattern).

### Step 4 - `SubstackCollector` for Market Chatter
- `src/services/market_chatter/collectors/substack_collector.py` implementing `BaseCollector.collect(symbol, period_days)` so Substack chatter shows up in TickerFlow alongside Reddit/X/StockTwits/News.

### Step 5 - Orchestration & UI
- Celery beat schedule entry (poll per-source; `HfiSource.check_frequency_hours` already handles cadence).
- Activity-feed events via existing `activity_service.py`.

### Step 6 - Tests & validation
- Feed fixtures for the adapter/collector (no live calls in CI), run `make test`.

**Cost: $0 in API fees.**

---

## 4. Risk summary

| Path | Risk level | Notes |
|---|---|---|
| RSS feed | Low | Intended for syndication; primary channel |
| Unofficial JSON API | Medium-low | ToS gray zone; gate behind feature flag + rate limit |
| Email parsing | Legal but operationally fiddly | Only for pubs you legitimately subscribe to |
| Paid-cookie access | Only for your own subscriptions | Do not use other users' cookies (ToS violation + CFAA-ish exposure) |

---

## 5. Open questions / follow-ups

- [ ] Confirm exact subdomains for all six publications (Burry's is currently blocked/flagged).
- [ ] Decide priority: HFI-adapter path (investor-centric) vs. Market-Chatter collector path (ticker-centric) first.
- [ ] Decide whether the unofficial JSON enrichment should ship in phase 1 (flag-gated) or phase 2.
- [ ] Legal sign-off on ToS exposure for the unofficial JSON endpoints (existing X/twikit precedent applies).