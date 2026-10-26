# Prediction Markets Integration — Kalshi & Polymarket

> **Goal**: Integrate prediction-market odds (Kalshi + Polymarket) into the analysis
> engine as a new signal source, alongside YouTube commentary, FinBERT/LLM sentiment,
> Reddit, X, StockTwits, and news.
>
> **Scope (approved)**: Full integration — market text flows through the existing
> chatter pipeline as source cards, **and** structured odds feed directly into the
> composite OCS score (Phases 1–2 below). Phases 3–4 (LLM market-matching, prediction
> grading vs market baseline) are follow-up work, described but not in scope.
>
> **Status**: Approved plan — implementation pending.

---

## Table of Contents

1. [Design Rationale](#1-design-rationale)
2. [Current Architecture Touchpoints](#2-current-architecture-touchpoints)
3. [API Research (verified)](#3-api-research-verified)
4. [Target Architecture](#4-target-architecture)
5. [Phase 1 — Clients, Collectors, Persistence](#5-phase-1--clients-collectors-persistence)
6. [Phase 2 — LangGraph Node & Scoring Integration](#6-phase-2--langgraph-node--scoring-integration)
7. [Phase 3–4 Preview (out of scope)](#7-phase-34-preview-out-of-scope)
8. [Testing Plan](#8-testing-plan)
9. [Risks & Mitigations](#9-risks--mitigations)
10. [Implementation Checklist](#10-implementation-checklist)

---

## 1. Design Rationale

Prediction markets are **fundamentally different** from every other source in the
engine: they produce *structured event probabilities* — e.g.
"P(NVDA closes above $200 on Friday) = 0.62" — not chatter text. Two consequences
drive the whole design:

### 1.1 Dual-feed design (text + odds)

- **Text feed**: a market's question and description can flow through the existing
  `RawItem → FinBERT/LLM` pipeline like any Reddit post or news headline, so
  prediction markets appear as ordinary **source cards** in TickerFlow responses.
- **Odds feed**: the actual probability/spread/volume must **bypass** sentiment NLP
  and reach the scoring agent directly as numbers. Running "62% chance" through
  FinBERT would be meaningless. Hence a dedicated odds snapshot store plus a new
  LangGraph node.

### 1.2 Sparse but high-value coverage

Per-ticker markets are sparse (mostly index/rates/macro/threshold markets, not every
S&P 100 name), but they encode *real-money consensus* — the only source in the
engine where participants are financially incentivized to be right. The engine must
degrade gracefully per symbol (mirroring the existing `found=False` snapshot
pattern), and the scoring formula must fall back to today's OCS when no odds exist.

### 1.3 The divergence signal (differentiator)

Because chatter measures *what retail says* and prediction markets measure *what
the crowd bets*, the gap between RISS and market-implied probability is itself a
signal ("retail 81% bullish, markets price only 55% odds → divergence"). Phase 2
adds this as a first-class driver card.

---

## 2. Current Architecture Touchpoints

Everything below already exists; the integration plugs into these exact seams.

| Component | Location | Role today |
|---|---|---|
| Collector interface | `src/services/market_chatter/collectors/base.py` | `BaseCollector.collect(symbol, period_days) -> list[RawItem]`; `compute_content_hash` dedup |
| Collectors | `src/services/market_chatter/collectors/` | Reddit, StockTwits, News, Twitter; each has a deterministic fixture fallback when the real API is unavailable |
| Ingestion orchestrator | `src/services/market_chatter/raw_ingestion_service.py` | `RawIngestionService.collectors` list instantiated in `__init__`; runs collectors concurrently, dedupes, persists to `raw_content` |
| Source taxonomy | `src/schemas/market_chatter.py` | `SourceName` (REDDIT/X/NEWS), `SOURCE_WEIGHTS` (0.45/0.30/0.25), `ProviderSnapshot`, `SourceCard`, `SignalSummary.source_count` (`le=3`), `MCPlatformBreakdown` |
| Vendor aggregation | `src/services/market_chatter/collection_service.py` | `CollectionService` — per-source snapshots, quota, Redis `JsonCache`, source cards, signal |
| Social bridge | `src/services/social_context_service.py` | Surfaces TickerFlow data on ticker pages / search cards |
| LangGraph pipeline | `src/pipeline/graph.py` | `validation → cleaner → (finbert ∥ llm) → scoring` |
| State contract | `src/schemas/agent_pipeline.py` | `PipelineGraphState` with `Annotated` reducers (`operator.add` / `operator.or_`); `TickerScoreOutput` (riss/sms/ocs), `ScoreDriverCard` |
| Scoring agent | `src/pipeline/agents/agent_scoring.py` | OCS = 0.70·RISS + 0.30·SMS, trend bands, driver cards |
| Config | `src/config.py` | pydantic-settings; provider keys, TTLs, feature flags |
| Migrations | `alembic/versions/` | 12 revisions; newest pattern is auto-generated hash revisions (e.g. `f8a92b113478_add_raw_content_table.py`) |

**Knock-on constraint discovered**: the source set is hard-coded in several places —
`SOURCE_WEIGHTS`, the `le=3` bound on `SignalSummary.source_count`, and the three
named integer fields in `MCPlatformBreakdown`. Adding two sources means touching all
of them (detailed in Phase 1).

## 3. API Research (verified)

Verified against live vendor docs on 2026-09-20. Re-verify at implementation time.

### 3.1 Kalshi

- **Base URL**: `https://api.elections.kalshi.com/trade-api/v2` (docs also reference
  `https://external-api.kalshi.com/trade-api/v2` — make the base URL a config value
  so it can be switched without code changes).
- **Market discovery**: `GET /markets` with query params:
  - `series_ticker` / `event_ticker` — filter by series or event
  - `status=open` — only tradeable markets
  - `min_close_ts` / `max_close_ts` — Unix timestamp window (horizon filter)
  - `limit` (≤1000) + cursor pagination
- **Market schema (relevant fields)**: `ticker`, `event_ticker`, `title`,
  `yes_sub_title`, `rules_primary`, `status`, `yes_bid_dollars`, `yes_ask_dollars`,
  `no_bid_dollars`, `no_ask_dollars`, `last_price_dollars`, `volume_fp`,
  `volume_24h_fp`, `open_interest_fp`, `liquidity_dollars`, `close_time`,
  `expiration_time`, `strike_type`, `floor_strike`, `cap_strike`.
- **Probability**: prices are quoted in **cents** (the `_dollars` fields carry
  e.g. `"0.56"`) — probability = yes price directly. Use the **midpoint of yes
  bid/ask** as implied probability; spread = ask − bid.
- **Auth**: market-data reads are free; newer API versions may require a (free)
  account API key, and trade endpoints use RSA request signing. **Decision**: make
  the API key optional in config and degrade to unauthenticated reads with fixture
  fallback — mirroring the existing Reddit OAuth-or-PullPush pattern in
  `reddit_collector.py`. Do **not** implement RSA signing in Phase 1 (read-only).
- **Relevant series (verify tickers at impl time)**: Fed funds decision series,
  CPI series, S&P/Nasdaq daily-close threshold series, per-stock "close above $X"
  markets. Build a curated `series_ticker` map rather than scanning the full
  market list per request.
- **Rate limits**: tiered per-account; market data is the most generous tier. A
  10–15 min cache TTL keeps usage comfortably inside limits for the S&P 100 universe.

### 3.2 Polymarket

- **Two public read APIs, both unauthenticated**:
  - **Gamma API** (`https://gamma-api.polymarket.com`) — market/event discovery:
    `GET /markets`, `GET /events` (filters: `closed=false`, `end_date_min`, tag),
    `GET /public-search?q=...` for keyword search. Market fields: `question`,
    `description`, `slug`, `conditionId`, `outcomes`, `outcomePrices` (decimals
    0–1), `volume24hr`, `liquidityNum`, `endDate`, `closed`.
  - **CLOB API** (`https://clob.polymarket.com`) — prices/orderbooks by token id:
    `GET /midpoint?token_id=...`, `GET /prices`, `GET /book`. Use for fresh
    midpoints on markets discovered via Gamma.
- **Probability**: outcome prices are decimals 0–1 — mid-price ≈ implied
  probability directly.
- **Auth**: not needed for any read path used here. (Auth/private-key flows exist
  only for trading — explicitly out of scope.)
- **Rate limits**: modest; enforce a per-client concurrency cap + Redis cache TTL.

### 3.3 Coverage reality check

For a given equity symbol expect 0–3 relevant markets per venue on a typical day
(earnings-window threshold markets, index thresholds, macro events). The collector
must be cheap for symbols with no coverage (one search call per venue returning
empty is fine) and the UI must treat empty odds as normal, not an error state.

## 4. Target Architecture

```
                         ┌──────────────────────────────┐
 Kalshi API v2 ─────────►│ KalshiClient  ┐               │
 Gamma/CLOB APIs ───────►│ PolymarketClient ─► normalizer │
                         └──────────────────┬───────────┘
                                            │ list[MarketOddsSnapshot]
                 ┌──────────────────────────┼──────────────────────────┐
                 ▼ (text as RawItem)        ▼ (structured odds)        │
   BaseCollector pair → RawIngestionService   PredictionMarketService  │
   ("kalshi"/"polymarket" sources)            → market_odds_snapshots  │
                 │                            (Redis cache 10–15 min)  │
                 ▼                                                     │
   raw_content → LangGraph: validation → cleaner ─┬─► finbert ─┐       │
                                                  ├─► llm ─────┤       │
                                                  └─► market_odds ──► scoring
                                                                      │
                                              OCS' = 0.60·RISS + 0.25·SMS + 0.15·PMI
                                              + "Chatter vs Market" divergence card
```

### 4.1 New package: `src/services/prediction_market/`

- `schemas.py` — `MarketOddsSnapshot` (Pydantic): the single normalized shape both
  venues are mapped onto.
- `kalshi_client.py` — thin `httpx` wrapper around `GET /markets` (+ series map).
- `polymarket_client.py` — Gamma discovery + CLOB midpoint fetch.
- `normalizer.py` — venue payload → `MarketOddsSnapshot` mapping (pure functions,
  unit-testable without network).
- `service.py` — `PredictionMarketService`: per-symbol orchestration, Redis caching
  (reuse the `JsonCache` pattern from `src/services/market_chatter/cache.py`),
  snapshot persistence, graceful empty-coverage handling.

### 4.2 Normalized schema: `MarketOddsSnapshot`

| Field | Type | Notes |
|---|---|---|
| `venue` | `Literal["kalshi", "polymarket"]` | |
| `market_id` | `str` | Kalshi `ticker` / Polymarket `conditionId` |
| `question` | `str` | Kalshi `title`+`yes_sub_title` / Polymarket `question` |
| `description` | `str \| None` | `rules_primary` / `description` |
| `url` | `str` | deep link to the market page |
| `implied_prob` | `float` | yes midpoint, `[0,1]` |
| `bid` / `ask` | `float \| None` | yes-side best bid/ask, `[0,1]` |
| `spread` | `float \| None` | `ask − bid` |
| `volume_24h` | `float \| None` | |
| `liquidity` | `float \| None` | |
| `close_time` | `datetime \| None` | market resolution time |
| `direction` | `Literal["up", "macro", "other"]` | see §6.2 — only `up` feeds PMI |
| `strike` | `float \| None` | threshold for "close above $X" markets |
| `fetched_at` | `datetime` | |
| `raw_payload` | `dict` | untouched venue payload (debugging/audit) |

### 4.3 Ticker→market matching strategy (Phase 1: deterministic)

In priority order, per venue:

1. **Curated series map** (Kalshi): a small config/constant mapping symbols or
   macro themes → `series_ticker` values (e.g. Fed/CPI series keyed by theme, not
   per-symbol). Cheapest and most reliable.
2. **Keyword search**: search `"{TICKER}"`, company name (reuse the company-name
   resolution already available in `CollectionService`/`universe.py`), and simple
   aliases, filtered to `status=open` / `closed=false` and a close-time horizon of
   `period_days`.
3. **Exclude false positives** with a denylist of question patterns
   ("Who will win…", non-financial events). Direction classification (`up` vs
   `other`) in Phase 1 is keyword-based: threshold/close-above markets → `up`;
   everything else → `macro`/`other` (visible as info, excluded from PMI).

LLM-assisted matching of extracted themes → markets is Phase 3 (out of scope), but
the `PredictionMarketService` API is designed so the LLM matcher can later supply
candidate market ids per symbol without changing call sites.

## 5. Phase 1 — Clients, Collectors, Persistence

### 5.1 Config additions — `src/config.py` (+ `.env.example`)

```
# ── Prediction Markets ──────────────────────────────────────────────
prediction_markets_enabled: bool = True
kalshi_api_key: str = ""                        # optional (free account key)
kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
polymarket_gamma_base_url: str = "https://gamma-api.polymarket.com"
polymarket_clob_base_url: str = "https://clob.polymarket.com"
prediction_market_cache_ttl_seconds: int = 900  # 15 min (prices move intraday)
prediction_market_max_markets_per_symbol: int = 5
```

Note the TTL: unlike the 24h social-sentiment TTLs (`source_ttl_seconds`), odds
change intraday, so these need their own, much shorter TTL. Also add the two new
keys to `.env.example` with comments.

### 5.2 Source taxonomy — `src/schemas/market_chatter.py`

- Add `KALSHI = "kalshi"` and `POLYMARKET = "polymarket"` to `SourceName`.
- Rebalance `SOURCE_WEIGHTS` (proposal — tune after observing real data):

  | Source | Old | New |
  |---|---|---|
  | reddit | 0.45 | 0.35 |
  | x | 0.30 | 0.20 |
  | news | 0.25 | 0.20 |
  | kalshi | — | 0.15 |
  | polymarket | — | 0.10 |

- Raise `SignalSummary.source_count` bound: `ge=0, le=3` → `le=5`.
- Extend `MCPlatformBreakdown` with `kalshi_markets: int` and
  `polymarket_markets: int` (or, better, refactor to `by_source: dict[str, int]`
  to stop hard-coding per-source fields — check `dashboard_service.py` usages
  when implementing).
- `SourceCard` gains optional `implied_prob: float | None` and
  `volume_24h: float | None` so prediction-market cards can display odds.

### 5.3 Collectors — `src/services/market_chatter/collectors/`

New files `kalshi_collector.py` and `polymarket_collector.py`, each conforming to
`BaseCollector` (same `__init__(settings, client=None)` + `collect()` + `close()`
shape as `RedditCollector`):

- `KalshiCollector(name=SourceName.KALSHI)`:
  - `collect()` resolves candidate markets via the series map + keyword search,
    then emits **one `RawItem` per market**: `text = question` (optionally +
    truncated `rules_primary`), `title = question`, `url` = market deep link,
    `engagement_score` = log-scaled 24h volume (keeps engagement weighting in the
    scoring agent meaningful), `author = "Kalshi market"`.
  - `raw_metadata` carries the full `MarketOddsSnapshot` dict so downstream
    stages never need to re-fetch.
  - No credentials → fixture fallback (deterministic generator seeded by
    `sha256("kalshi:{symbol}")`, same pattern as the other collectors), so tests
    and offline dev never hit the network.
- `PolymarketCollector(name=SourceName.POLYMARKET)`: same shape; Gamma search →
  CLOB midpoints; fixture fallback likewise.
- Register both in `collectors/__init__.py` and append to the
  `RawIngestionService.collectors` list (they then run concurrently with the other
  four collectors automatically; dedup via `content_hash` on question text works
  as-is).
- Re-fetch cadence: `RawContent` dedup means a market whose question text is
  unchanged won't be re-inserted — good (no LLM spend on unchanged markets). Fresh
  *odds* come from the snapshot store, not from raw text, so staleness of the text
  feed is acceptable.

### 5.4 Persistence — new model + migration

- **Model**: `src/models/market_odds.py` — `MarketOddsSnapshotRecord` mapped to
  table `market_odds_snapshots` (same style as `SourceSnapshot` in
  `src/models/source_snapshot.py`):

  Columns: `id` (int pk), `symbol` (String(16), indexed), `venue` (String(16),
  indexed), `market_id` (String(128)), `question` (Text), `url` (String(512)
  nullable), `implied_prob` (Float), `bid`/`ask`/`spread` (Float nullable),
  `volume_24h`/`liquidity` (Float nullable), `close_time` (DateTime(timezone=True)
  nullable), `direction` (String(16)), `fetched_at` (DateTime(timezone=True),
  indexed), `raw_payload` (JSON).

  Write model: **append-only snapshots**; consumers query the latest row per
  (`symbol`, `venue`, `market_id`). Add a `(symbol, venue, fetched_at)` composite
  index. Optional dedup guard: skip insert when the latest row for a market has
  the same `implied_prob` rounded to 3dp within the TTL — prevents table bloat.

- **Migration**: new alembic revision `009_add_market_odds_snapshots.py`
  (resolve the actual `down_revision` against `alembic heads` at implementation
  time — the versions tree currently mixes `00N` and hash revisions). Follow the
  `e4e38ec36752_add_tickerflow_tables.py` style (`sa.Table` + indexes +
  `UniqueConstraint` where applicable).

- **Daily rollup**: write one `TickerDailyMetric` row per venue per day
  (`source='kalshi'/'polymarket'`, `sentiment_score = implied_prob − 0.5` scaled
  to [−1,1], `mentions = market count`) so the existing chart pipeline in
  `collection_service.py` renders odds alongside chatter without frontend changes.

### 5.5 Service — `src/services/prediction_market/service.py`

`PredictionMarketService(settings, session_factory=None, cache=None)`:

- `async get_odds(symbol, period_days=7) -> list[MarketOddsSnapshot]`
  - checks Redis cache (`JsonCache`, key `pm_odds:{symbol}:{period_days}`,
    TTL from config) → on miss runs both clients concurrently
    (`asyncio.gather`, exceptions logged-and-swallowed per venue like
    `RawIngestionService`), normalizes, persists snapshots, caches, returns.
- `async close()` — closes owned httpx clients.
- Wired into `src/api/deps.py` alongside the other singletons
  (`app.state.tickerflow_service` pattern) so API endpoints and the LangGraph
  node share one instance/cache.

## 6. Phase 2 — LangGraph Node & Scoring Integration

### 6.1 New node: `agent_market_odds`

- **File**: `src/pipeline/agents/agent_market_odds.py` (async node, same shape as
  `agent_finbert_node`).
- **Graph wiring** (`src/pipeline/graph.py`): register node `"market_odds"` and
  run it **parallel** to finbert/llm:

  ```
  cleaner → finbert ──────► scoring
  cleaner → llm ──────────► scoring
  cleaner → market_odds ──► scoring
  ```

  LangGraph's fan-out from `cleaner` already works for the current pair; add the
  third edge identically (`builder.add_edge("cleaner", "market_odds")`).

- **Behavior**: calls `PredictionMarketService.get_odds(symbol)` (service injected
  via a module-level lazy singleton like `_get_finbert_service()`, overridable in
  tests), and writes into state:

  ```python
  # PipelineGraphState addition (src/schemas/agent_pipeline.py)
  market_odds: Annotated[dict[str, list[dict[str, Any]]], operator.or_]
  # key: venue ("kalshi"/"polymarket") → list of MarketOddsSnapshot dicts
  ```

- **Failure mode**: on service error or empty coverage, returns
  `{"market_odds": {}}` — the scoring agent must treat that as "no signal",
  never as zero probability. Flag `prediction_markets_enabled=False` short-circuits
  the node entirely.

### 6.2 Scoring changes — `agent_scoring.py` + schemas

**PMI (Prediction-Market Implied score, 0–100):**

1. From `state["market_odds"]`, keep only `direction == "up"` snapshots (threshold
   / "close above $X" style markets). `macro`/`other` markets are *displayed* but
   excluded from PMI — a 70% odds on "Fed cuts rates" is not bullish-or-bearish
   for `$NVDA` without a mapping, which is Phase 3 territory.
2. Weight each market's `implied_prob` by min(volume_24h, liquidity) so a
   thin $500 market can't outweigh a $5M one.
3. `pmi_score = round(weighted_mean(implied_prob) * 100, 1)`.

**New OCS blend** (`TickerScoreOutput` gains `pmi_score: float | None`):

```
if pmi exists:  OCS' = 0.60·RISS + 0.25·SMS + 0.15·PMI
else:           OCS  = 0.70·RISS + 0.30·SMS     (unchanged, current behavior)
```

Weights are a starting point — document them as "OCS v0.2" in the docstring, and
keep the fallback branch exactly equivalent to today's formula so symbols without
markets are unaffected. Keep the `0.0–100.0` rounding and trend bands
(≥65 rising / ≤40 falling) as-is.

**Divergence driver card** (in addition to existing cards):

- Compute `gap = riss_score − pmi_score`.
- If `|gap| ≥ 15` points, append a `ScoreDriverCard`:
  - `gap > 0` → *"Retail is more bullish than prediction markets"* (driver_type
    `neutral`, impact 0 — it's informational, not directional): summary cites both
    numbers, e.g. "Chatter RISS 81 vs market-implied 55 — crowd positioning lags
    social sentiment."
  - `gap < 0` → mirrored wording.
- Add `source_links` pointing at the market URLs so the claim is auditable —
  consistent with the citation-first product principle used elsewhere.

**`MCPlatformBreakdown` / response surface**: include per-venue market counts and
top-of-book probabilities in the ticker response (via the `SourceCard` fields from
§5.2), so the existing TickerFlow UI renders odds without new endpoints.

### 6.3 Celery refresh task

Add `prediction_markets.refresh` to `src/tasks/pipeline_tasks.py` — same pattern as
`tickerflow_watchlist_collect_task`: iterate `pilot_symbols`, call
`PredictionMarketService.get_odds`, log counts. Schedule via Celery Beat every
15 min during market hours (cheap: one search call per venue per symbol, cached).

## 7. Phase 3–4 Preview (out of scope)

Recorded so future work doesn't need re-planning. Both build on the
`PredictionMarketService` seams above without changing Phase 1–2 call sites.

- **Phase 3 — LLM market matching & surfacing**:
  - Use the existing LLM service to match extracted predictions/catalyst themes
    (transcripts + social) to live market questions; a guest's "Fed will cut in
    September" claim shows the Kalshi odds *at time of claim*.
  - New public endpoint `GET /api/v1/prediction-markets/{symbol}` returning
    snapshots + divergence summary; `MarketOddsPanel` component in `web/` on the
    ticker page.
- **Phase 4 — Prediction grading vs market baseline**:
  - Grade `src/models/prediction.py` entries against market-implied probability
    *at the time of the call* — separating skilled calls from lucky ones
    ("market gave it 12% — that call was genuine alpha"). Extends
    `performance_service.py`, which currently grades only against yfinance
    1d/1w/1m returns.

---

## 8. Testing Plan

Follow the existing patterns: fixture fallbacks make collector tests network-free;
`Settings(_env_file=None)` in tests (see `tests/market_chatter/test_collectors.py`).

### 8.1 New tests

| File | Coverage |
|---|---|
| `tests/market_chatter/test_prediction_market_clients.py` | `normalizer.py` mapping for both venues (real captured payloads as fixtures): cents→prob for Kalshi, decimals for Polymarket, `direction` classification, spread math |
| `tests/market_chatter/test_prediction_market_collectors.py` | `KalshiCollector` / `PolymarketCollector` fixture mode: unique ids/hashes, `RawItem` shape, `raw_metadata` odds present; empty-coverage symbol returns `[]` (not an exception) |
| `tests/test_agent_market_odds.py` | Node writes `market_odds` into state; service error → `{}`; disabled flag → `{}` |
| `tests/test_agent_scoring.py` (extend) | PMI weighting math; OCS v0.2 blend vs fallback equality when no odds; divergence card emitted at gap ≥15 and absent at gap <15; `macro` markets excluded from PMI |
| `tests/test_langgraph_pipeline.py` (extend) | Full-graph run with fixture odds — asserts `final_score.pmi_score` present and the parallel branch merge works (the `operator.or_` reducer on a dict-of-lists needs an explicit test) |
| Migration smoke | `alembic upgrade head` against a scratch Postgres in CI or locally before merge |

### 8.2 Existing tests that must be re-checked

- Anything asserting `SOURCE_WEIGHTS` sums (0.45+0.30+0.25) — must be updated for
  the new weights.
- `SignalSummary` validation tests (`source_count` bound).
- `MCDashboardResponse` / platform-breakdown tests in
  `tests/market_chatter/test_services.py`.

### 8.3 Live validation (manual, before merge)

- Fetch odds for `NVDA`, `SPX`, `AAPL` from both venues; eyeball implied
  probabilities against the public websites.
- Run the pipeline for one symbol end-to-end with `prediction_markets_enabled`
  on/off and diff `final_score` to confirm the fallback path is byte-identical.

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Kalshi API/auth changes (endpoints have moved hosts before; newer versions may require keys or RSA signing for reads) | Collector breaks | Base URL + key in config; unauthenticated read attempt first, fixture fallback; RSA signing isolated inside `KalshiClient` only, added only if reads start 401-ing |
| Polymarket rate limits | Collection stalls | 15-min Redis TTL, per-client concurrency cap, gather-and-swallow per venue |
| Sparse per-ticker coverage | PMI missing for most symbols | Explicit fallback OCS branch (unchanged formula); UI treats empty as normal; focus first on pilot symbols + macro themes |
| Semantics: probability ≠ sentiment | Corrupting OCS | Only `direction=="up"` markets feed PMI; macro/other display-only; divergence cards are `neutral`/informational |
| Thin/illiquid markets skew PMI | Bad signal | Volume+liquidity weighting; `max_markets_per_symbol` cap; min-volume threshold as config knob if needed |
| Score discontinuity when odds appear/disappear mid-trend | Jumpy OCS | Documented weights versioning (OCS v0.1 → v0.2); snapshot store enables retroactive evaluation |
| Regulatory availability (venue access varies by jurisdiction) | Display concern only | Read-only public market data; keep odds cards labeled as market-implied probabilities, not advice (existing footer disclaimer pattern) |

## 10. Implementation Checklist

### Phase 1
- [ ] `src/config.py`: prediction-market settings (+ `.env.example`)
- [ ] `src/schemas/market_chatter.py`: `SourceName` entries, `SOURCE_WEIGHTS`,
      `SignalSummary.source_count` bound, `SourceCard` odds fields,
      `MCPlatformBreakdown` (+ check `dashboard_service.py` and web types in
      `web/src/lib/api.ts`)
- [ ] `src/services/prediction_market/schemas.py` — `MarketOddsSnapshot`
- [ ] `src/services/prediction_market/kalshi_client.py`
- [ ] `src/services/prediction_market/polymarket_client.py`
- [ ] `src/services/prediction_market/normalizer.py`
- [ ] `src/services/prediction_market/service.py` (+ Redis cache, snapshot persist)
- [ ] `src/services/market_chatter/collectors/kalshi_collector.py` (+ fixtures)
- [ ] `src/services/market_chatter/collectors/polymarket_collector.py` (+ fixtures)
- [ ] Register collectors in `collectors/__init__.py` + `raw_ingestion_service.py`
- [ ] `src/models/market_odds.py` + alembic revision for `market_odds_snapshots`
- [ ] Daily rollup into `TickerDailyMetric`
- [ ] Wire `PredictionMarketService` singleton in `src/api/deps.py`

### Phase 2
- [ ] `src/pipeline/agents/agent_market_odds.py` + export in `agents/__init__.py`
- [ ] `src/pipeline/graph.py`: register node + third parallel edge
- [ ] `src/schemas/agent_pipeline.py`: `market_odds` state key, `pmi_score` on
      `TickerScoreOutput`
- [ ] `src/pipeline/agents/agent_scoring.py`: PMI, OCS v0.2 blend + fallback,
      divergence driver card
- [ ] `src/tasks/pipeline_tasks.py`: `prediction_markets.refresh` Celery task
- [ ] Tests (§8.1) + fix affected existing tests (§8.2)
- [ ] Live validation run (§8.3)






