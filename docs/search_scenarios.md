# Search Engine — Scenario ↔ Output Matrix

> Debug / reference for `GET /api/search`, `/api/search/answer`, `/api/search/coverage`.
> Last verified against `src/services/query_router.py`, `src/api/search.py`, `src/services/search_service.py`, `src/services/search_answer_service.py`, `src/services/search_coverage_service.py`, `web/src/app/(app)/search/page.tsx`, `web/src/lib/hooks.ts`.
> Commit: `859d8f4` + sanitization / sentiment / cache-bust fixes (Aug 24 2026).

---

## 1. How the engine is wired (1 diagram)

```
query ──► QueryRouter.classify() ──► intent ──► SearchService
                                   │                      ├─► search_stocks_for_query()  [sector_discovery]
                                   │                      ├─► search_ticker_narrative()  [ticker_narrative|sentiment_check]
                                   │                      └─► hybrid_search()            [every intent → segments/predictions/groups]
                                   └─► instrument_type (stocks|etfs) + ticker_hint/sector_hint
                                                          │
                                ┌─────────────────────────┴─────────────────────────┐
                                │ SearchResponse                                   │
                                │ { segments, groups, predictions, stocks,         │
                                │   videos, channels, total, has_more,            │
                                │   query_intent, instrument_type }                │
                                └──────────────────────────────────────────────────┘
                                                        │
                          results.groups ──► answerSegmentIds (12 ids) ──► GET /api/search/answer
                                                               └───────► GET /api/search/coverage
```

**Cache keys**

| Layer | Key | TTL | Bust |
|---|---|---|---|
| `QueryRouter` | in-memory `heuristic_classify()` (no cache) else LLM `gpt-5.4-nano` (`max_completion_tokens=100`) | none — `T:0.0` | heuristic bypass |
| `SearchService.hybrid_search` | no cache — live `tsvector` + `pgvector` + RRF(`k=60`) + `max_per_video=4` | 0 | — |
| `SearchAnswerService` | `sha256(normalize(query))` + `source_segment_ids` set (added Aug 24) | 24h `CACHE_TTL` | set-mismatch or legacy fallback `don't mention` |
| `SearchCoverageService` | `hash(query)+window_days` | 6h | — |
| Frontend `useSearch` | `["search",q,type,sort,limit]` `keepPreviousData` | — | `q|type|sort` key reset `page.tsx:346` |
| Frontend `useSearchAnswer` | `["searchAnswer",q, joinedIds]` `staleTime 10m` | 10m | gated on `!isPlaceholderData && !isFetching` |

> **Known race (fixed Aug 24):** `keepPreviousData` kept NVDA `groups` while MSFT query fetching → `answerSegmentIds` were NVDA ids + `q=MSFT` → poisoned answer `The provided clips don't mention MSFT…` cached under MSFT hash. Fixed by `page.tsx:440` gating + `search_answer_service.py:249` set-mismatch bust. Purge stale: `DELETE FROM search_answers WHERE query_text ILIKE '%MSFT%'`.

---

## 2. Intent Taxonomy (QueryRouter)

`ROUTER_SYSTEM_PROMPT` `query_router.py:21` + heuristics `query_router.py:241`.

| Intent | Heuristic signal (`_heuristic_classify`) | LLM examples | `sector_hint` | `ticker_hint` | `instrument_type` |
|---|---|---|---|---|---|
| `sector_discovery` | `best/top + semiconductor/ai/tech/energy/defense/biotech… + stocks/etfs/picks/plays` or bare sector `semiconductors` | `Best AI stocks?`, `Nuclear stocks?`, `Top energy plays`, `Which ETF for clean energy?` | `semiconductor`, `ai`, `clean energy` | `null` | `stocks` unless query has `etf/sector fund/index fund` → `etfs`, also `Channel.channel_type` overrides (`institutional→etfs`, `individual→stocks`) |
| `ticker_narrative` | `narrative|outlook|what are people saying|stock analysis|bull case for` + ticker name (`Nvidia→NVDA`) | `Outlook on Nvidia?`, `Apple stock analysis`, `SMH outlook` | `null` | `NVDA,TSLA,AAPL,MSFT,AMZN,GOOGL,META,AMD,INTC,PLTR,NFLX,SMH,QQQ…` or any `[A-Z]{2,5}` | `stocks` (or `etfs` if ticker is ETF) |
| `sentiment_check` | `sentiment|bullish|bearish|bull case|bear case|overbought|oversold` + ticker | `What is the sentiment on NVDA?`, `Is TSLA bullish?`, `is NVDA overbought?` | `null` | same map | `stocks` |
| `entity_lookup` | *(no heuristic — LLM only)* | `What did Cathie Wood say about Tesla?`, `Nvidia earnings call`, `Anthropic's IPO?` | `null` | `NVDA…` if identifiable | `stocks` |
| `factual_search` | fallback | `inflation discussion`, `Fed rate decision`, `when was Bitcoin discussed?` | `null` | `null` unless `ticker` param | `stocks` |

**Ticker extraction** `_extract_ticker_heuristic()` `query_router.py:430` — `nvidia→NVDA`, `tesla→TSLA`, else first `[A-Z]{2,5}` not in `WHAT|WHEN|...|SENTIMENT`.

**Debug:** `uv run python -c "from src.services.query_router import QueryRouter; print(QueryRouter._heuristic_classify('What is the sentiment on NVDA?'))"` → `sentiment_check/NVDA`. Logs `Query '...' classified as: ...` `query_router.py:156`. Failure → `WARNING fallback to factual_search` `query_router.py:164` (previously broken by `max_tokens` → `max_completion_tokens` fix).

---

## 3. Output Matrix — `GET /api/search`

`src/api/search.py:37` `SearchResponse` `schemas/__init__.py:280`.

| # | Scenario (example query) | Classified intent → handler | `stocks` (Top Stocks / Stocks Mentioned) | `groups` / `segments` (Related Segments) | `predictions` | `query_intent` / `instrument_type` | UI visible |
|---|---|---|---|---|---|---|---|
| **A1** | `Best semiconductor stocks?` `Best AI stocks?` `Top energy plays` | `sector_discovery` → `search_stocks_for_query(sector_hint)` `search_service.py:884` | **Yes** `10` items `StockDiscoveryResult` `composite_score` `theme_relevance` `mention_count` `avg_sentiment` `bullish_pct` `themes` `sample_predictions` `is_etf=false` — uses `ThemeHierarchy` + `ThemeTickerMapping` + `SpeakerTickerAggregation` + `Prediction` | Yes `groups` from `hybrid_search` (keyword+semantic) | keyword `predictions` (ranked, dedup) may be empty | `sector_discovery` / `stocks` (or `etfs` if `ETF` wording or institutional channel) | `Top Stocks (1…10)` grid `page.tsx:546` + `Related Segments` + `AI-Powered Discovery` badge |
| **A2** | `Best semiconductor ETFs?` `Which ETF for clean energy?` `Top ETFs to buy` | `sector_discovery` + `instrument_type=etfs` → `_build_etf_discovery_results()` `search_service.py:773` | **Yes** ETF list `is_etf=true` `mention_count=0` `themes` = matched themes, `composite_score=1.0 - i*0.02` | Same as A1 | Same | `sector_discovery` / `etfs` | `Top ETFs` header `page.tsx:523` |
| **B1** | `Outlook on Nvidia?` `What are people saying about Tesla?` `nvidia outlook` | `ticker_narrative` → `search_ticker_narrative(ticker)` `search_service.py:480` | **Yes** single-element `[{ticker, composite_score, mention_count, avg_sentiment, bullish_pct, bearish_pct, themes: [236…], is_etf}]` — `mention_count` from `speaker_ticker_aggregation` (e.g. `NVDA 29`, `MSFT 20`, `BRK.B 40`), `avg_sentiment -1..+1`, `bullish_pct` from `Prediction.direction` only (often `0` when `predictions.ticker IS NULL` — known data quirk: 374/378 predictions have `ticker=NULL`) | Yes `hybrid_search(query, ticker=ticker_hint)` — `limit 20` groups `hit_count` truthful `keyword_match_counts` + `best_rank` RRF | Same (filtered by `ticker` param) | `ticker_narrative` / `stocks` | `Top Stocks (1)` card `#1 $NVDA Neutral 40 mentions 0 predictions` + `Related Segments` + `SUMMARY` (if ≥3 segments) |
| **B2** | `What is the sentiment on NVDA?` `Is TSLA bullish?` `is NVDA overbought?` | `sentiment_check` → **same as B1** (fixed `search.py:88` `in (ticker_narrative,sentiment_check)`) | **Yes** same single-element (note `avg_sentiment` → `Neutral|Bullish|Bearish` threshold `>0.2` / `<-0.2` `page.tsx:565`) — previously **empty** (`No explicit stocks`) due to `max_tokens` bug + missing handler | Yes | Yes | `sentiment_check` / `stocks` | Same as B1; rail badge `Bullish|Bearish|Neutral` `page.tsx:977` + `% bull` if `>0` |
| **C1** | `What did Cathie Wood say about Tesla?` `Anthropic's IPO in 2027` `Nvidia earnings call` | `entity_lookup` (LLM) — *no* `stocks` | **No** `stocks=[]` | **Yes** `groups` (fused RRF) — best for clip retrieval | Yes dedup | `entity_lookup` / `stocks` | No Top Stocks grid; `Related Segments` only + `SUMMARY` (llm may cite) |
| **C2** | `inflation discussion` `Fed rate decision` `AI bubble comparison` | `factual_search` (LLM or fallback) | **No** | **Yes** `groups` | Yes | `factual_search` / `stocks` | Same as C1 |
| **D** | `sdfqweqwe qweqwe` (nonsense) or no video match | `factual_search` | `[]` | `[]` / `has_more=false` | `[]` `total=0` `zero_results=true` analytics | `factual_search` | `No transcript segments found` `page.tsx:903` + `Try a broader keyword…` |
| **E** | `BRK.B` (dot ticker) `What is sentiment on BRK.B?` | `sentiment_check` → `NVDA`-like but theme overflow case | **Yes** `BRK.B 40 mentions` (screenshot) with `236 themes` → UI bug was truncation (`Billionaire / capital gains tax and revenu`) fixed `page.tsx:619` `h-auto !whitespace-normal break-words max-w-full` | Yes | — | `sentiment_check` | Card wraps badges with tooltip `title`, no mid-word cut |

**Sorting / filtering** (post-retrieval, client- or server-side):

| Control | Backend | Frontend |
|---|---|---|
| `type=keyword|semantic|hybrid` `search.py:41` | `hybrid` → both retrievers pool `100`, RRF; `keyword`/`semantic` single list | `Search type` toggle `page.tsx:469` |
| `sort=relevance|recent` | `hybrid_search: sort` → `_apply_group_sort` `search_service.py:297` (`recent` sorts `groups` by `published_at desc`) | `Sort Relevance|Newest` `page.tsx:623` |
| `PERIOD All|7d|30d|90d` | not sent to backend — frontend filters `visibleGroups` `page.tsx:413` by `published_at >= cutoff` | `Period` buttons `page.tsx:645` |
| `Channel` facet | `channel_id` param → `Video.channel_id` filter in `_keyword_search_segments`, `_semantic_search_segments`, `_keyword_match_counts` | `Channel` select `page.tsx:665` |
| `limit` / `Load more` | `limit` (default 20) → `pool_size min(limit*4,100)`; `has_more` ` _compute_has_more` `search_service.py:303` | `resultLimit` `+20` `page.tsx:913` hidden while filters active |

---

## 4. Secondary endpoints

### 4a. `GET /api/search/answer` → `SearchAnswerResponse` `schemas/__init__.py:314`

| Input | Behavior | Success Output | Fallback Output | UI |
|---|---|---|---|---|
| `q` + `segment_ids` (12 ids from `groups.flatMap`) `search.py:199` / `hooks.ts:162` `["searchAnswer",q,joined]` `staleTime 10m` | `get_or_create()` `search_answer_service.py:221` 1) lock `hash_query(q)` 2) `_read_cache` (24h TTL) + **source_segment_ids set-mismatch bust** `service:249` + sanitization 3) `_resolve_segments(ids)` else `hybrid_search` 4) if `<3` segments → `available:false` 5) `_synthesize` (8s timeout `gpt-5.4-nano` `response_format json_object` `T0.2`) 6) `parse_llm_response()` + `sanitize_citation_text()` (`[uuid]`→`[1]`) `service:98` 7) `map_citations()` + cache `source_segment_ids` | `{query, summary:"Excerpts suggest… ([1],[2])", key_points:["Near-term… ([1])"×4], citations:[{segment_id,video_id,start_sec,text(240),video_title,channel_title,youtube_video_id}]` order = LLM order, `available:true, cached:false|true}` | `available:false` (no citations) when `<3` segments, LLM timeout, `None` parse, or genuinely no info. **Special fallback**: summary=`The provided clips don't mention MSFT specifically…` + `key_points:[]` + `citations:[]` `available:true` (not cached as negative `unavailable`? Actually `unavailable` is `available:false` only for `<3`; fallback with 1-sentence is still `available:true` but empty citations) | `SearchAnswerCard` `page.tsx:91` — `SUMMARY` `summary` + bullets + `[1][2]…` buttons `onCitationClick` → modal. `cached` badge `page.tsx:105` (`cached` chip). Sanitization `page.tsx:62` also runs client-side for legacy cache. Gated `showAnswerSkeleton` only when `results` fresh (`!isPlaceholderData|||!isFetching`) — fixes NVDA→MSFT poison. |

**Sanitization:** `_CITATION_BRACKET_RE` `^\[uuid\]` → `[index]` else `""`, `_RAW_UUID_RE` strip, `()`, `[]`, `, )`, double-space cleanup. Applied in `parse_llm_response` and `_read_cache` + frontend `sanitizeCitations()`. Test: `NVDA` summary `([28442ada-…],[42be41ce-…])` → `([1],[2])`.

**Debug**

* Logs `search/answer: synthesis timed out 8s` / `synthesis failed` `service:392`.
* Check cache `SELECT query_text, answer_json->>'summary', query_hash FROM search_answers;` Purge `DELETE FROM search_answers WHERE query_hash=hash_query('What is the sentiment on MSFT ?');` or `WHERE query_text ILIKE '%MSFT%'`.
* Force fresh synthesis via different `segment_ids` set (bust) or wait 24h.

### 4b. `GET /api/search/coverage` → `SearchCoverageResponse` `schemas/__init__.py:326`

| Window `window_days` default `14` `search.py:224` | Counts videos discussing query (FinBERT per-video best snippet → `positive/neutral/negative` + `weekly_volume` 2 buckets + `wow_delta_pct`) `search_coverage_service.py` | `SearchCoverageResponse {total_videos, positive, neutral, negative, weekly_volume:[{week_start,count}], wow_delta_pct, window_days}` | `Coverage` card `page.tsx:162` stacked `positive/neutral/negative` bar + `Weekly volume` bars + `▲▼ WoW%` |
|---|---|---|---|

**Frontend gate:** `answerSegmentIds` as above, `useSearchCoverage` `hooks.ts:175` `enabled segmentIds.length>0`, `CoverageSnapshotCard` shown when `total_videos>0`.

---

## 5. Predicates Cheat-Sheet (copy-paste for curl)

```bash
# 1) Raw search — sector discovery (expects stocks)
curl -s "http://localhost:8000/api/search?q=Best%20AI%20stocks%3F&type=hybrid&limit=10" -H "Authorization: Bearer $TOKEN" | jq '{intent: .query_intent, stocks: [.stocks[]|.ticker], groups: (.groups|length)}'

# 2) Ticker narrative / sentiment (expects single stock with sentiment)
curl -s "http://localhost:8000/api/search?q=What%20is%20the%20sentiment%20on%20NVDA%3F&type=hybrid&limit=5" -H "Authorization: Bearer $TOKEN" | jq '{intent, stocks:[.stocks[]|{t:.ticker,s:.avg_sentiment,b:.bullish_pct}], total}'

# 3) Answer + coverage (use real ids from previous groups)
IDS=$(curl -s "http://localhost:8000/api/search?q=MSFT&type=hybrid&limit=12" -H "Authorization: Bearer $TOKEN" | jq -r '[.groups[].top_segments[].id, .groups[].remaining_segments[].id]|flatten|join(",")')
curl -s "http://localhost:8000/api/search/answer?q=What%20is%20the%20sentiment%20on%20MSFT%20%3F&segment_ids=$IDS" -H "Authorization: Bearer $TOKEN" | jq '{cached, available, summary, citations: [.citations[]|.segment_id]}'
curl -s "http://localhost:8000/api/search/coverage?q=MSFT&segment_ids=$IDS" -H "Authorization: Bearer $TOKEN" | jq .

# 4) ETF vs stock routing
curl -s "http://localhost:8000/api/search?q=Best%20semiconductor%20ETFs%3F" -H "Authorization: Bearer $TOKEN" | jq .instrument_type # etfs

# 5) DB checks
psql $DATABASE_URL_SYNC -c "SELECT ticker, total_mentions, avg_sentiment FROM speaker_ticker_aggregation WHERE ticker IN ('NVDA','MSFT','BRK.B') ORDER BY total_mentions DESC;"
psql $DATABASE_URL_SYNC -c "SELECT ticker, COUNT(*) FROM predictions GROUP BY ticker ORDER BY COUNT(*) DESC LIMIT 5;" # expect many NULL
psql $DATABASE_URL_SYNC -c "SELECT COUNT(*) FROM transcript_segments WHERE text ILIKE '%microsoft%';"
psql $DATABASE_URL_SYNC -c "SELECT query_text, answer_json->>'summary' FROM search_answers LIMIT 5;"
psql $DATABASE_URL_SYNC -c "DELETE FROM search_answers WHERE query_text ILIKE '%MSFT%';"

# 6) Router heuristic offline
uv run python -c "from src.services.query_router import QueryRouter; print(QueryRouter._heuristic_classify('What is the sentiment on NVDA?'))"
uv run python -c "from src.services.query_router import QueryRouter; print(QueryRouter._heuristic_classify('Best semiconductor ETFs?'))"
```

---

## 6. Common Failures & How to Spot Them

| Symptom (UI) | Root cause | Log / DB | Fix |
|---|---|---|---|
| `SUMMARY` shows raw `[28442ada-dea1-4b3b-8859-…]` | Frontend missed `sanitizeCitations` or backend `parse_llm_response` not sanitized | `summary` contains UUID regex `\b[0-9a-f]{8}-` | Already fixed `service:88` + `page.tsx:62`; purge old cache |
| `The provided clips don't mention MSFT` but `Related Segments` shows `Microsoft.` (10) | **Stale answerSegmentIds** (NVDA→MSFT race) poisoned cache under MSFT hash | `search_answers` row for MSFT has `summary~"don't mention MSFT"` + `citations:[]` while `groups` for MSFT has `Microsoft` | `page.tsx:440` gating + `service:249` set-mismatch bust + manual `DELETE` (done for MSFT) |
| `No explicit stocks found` for `What is the sentiment on NVDA?` | `sentiment_check` not handled or `max_tokens` → `factual_search` fallback | `query_router: WARNING fallback` `server.md:670` `query_intent=factual_search` `stocks=[]` | `search.py:88` now handles `sentiment_check` + `query_router.py:128` `max_completion_tokens` + heuristic `query_router.py:359` |
| `Top Stocks` card `$BRK.B` themes cut off `Billionaire / capital gains tax and revenu` | Badge `whitespace-nowrap h-5 w-fit shrink-0` overflow `page.tsx:621` + `badge.tsx:8` | Visual only | `page.tsx:619` `h-auto !whitespace-normal break-words max-w-full min-w-0` + `Card min-w-0 overflow-hidden` |
| `No transcript segments found` | `tsvector` + `pgvector` both miss; `total=0` `has_more=false` | `Keyword match counting …` warning `search_service.py:337` | Broaden query, try `type=semantic` |
| `Search` stays in `cached` forever with stale excerpts | Cache TTL 24h, `source_segment_ids` matches but new videos added | `search_answers.created_at` older than new `videos.published_at` | Wait TTL or `DELETE FROM search_answers WHERE query_hash=...` or trigger bust by changing `segment_ids` set |
| `current transaction is aborted` `InFailedSQLTransactionError` `server.md:18` | `search_answers` table missing (pre-migration) or prior `SELECT … IN (…)` failed, transaction not rolled back | `relation "search_answers" does not exist` | Run `alembic upgrade head` (`007_add_search_answers`) ; service now does `_safe_rollback()` `service:414` |
| `Top Stocks` shows `Neutral 0% bull` for NVDA/MSFT despite bullish summary | `bullish_pct` derived only from `Prediction.direction` `search_service.py:546`; 374/378 predictions have `ticker=NULL` so per-ticker count is `0` even though `speaker_ticker_aggregation` has `29|20` mentions with `avg_sentiment ~0.03` (neutral threshold `>0.2`) | `SELECT direction, COUNT(*) FROM predictions WHERE ticker='NVDA'` → `0` | Data pipeline fix (ticker extraction) or adjust UI to show `avg_sentiment`-based label not just `bullish_pct`; currently shows `Neutral` correctly per data |
| `++51 more` theme badge | 236 themes for NVDA example `search_service.py` test (`themes` huge) | `stock.themes.length >3` `page.tsx:630` | Intended; wrapping fixed |

---

## 7. Minimal QA Checklist (run before merge)

```
# Backend
uv run pytest tests/test_search_answer.py tests/test_search_grouping.py tests/test_search_coverage.py tests/test_query_instrument_type.py -q  # 50 passed
uv run python -c "from src.services.search_answer_service import parse_llm_response; ..." # UUID sanitization
uv run python -c "from src.services.query_router import QueryRouter; assert QueryRouter._heuristic_classify('What is the sentiment on NVDA?').intent=='sentiment_check'"

# Manual UI (hard refresh, not keepPreviousData)
1. Search `Best AI stocks?` → Top Stocks grid 10, `Related Segments`, `SUMMARY` with [1][2] not UUID.
2. Search `What is the sentiment on NVDA?` → Stocks Mentioned shows `NVDA 29 mentions Neutral` + summary positive despite tough week.
3. Immediately change query input to `What is the sentiment on MSFT ?` + Search → summary shows MSFT sentiment (not `don't mention MSFT`), citations [1]… match Microsoft clips (55% match).
4. Check `BRK.B` card → 3 theme badges wrap, `title` hover shows full `Billionaire / ...`, no `revenu` cut.
5. Switch `Keyword|Semantic|Hybrid` + `Relevance|Newest` + `PERIOD` + `Channel` → visibleGroups filters correctly.
6. Load more → `has_more` → groups grow.
7. Empty query `sdfqwe` → `No transcript segments found`.
8. Check Network: `/api/search/answer?q=MSFT&segment_ids=...` response `cached:false` first, `cached:true` second but `source_segment_ids` matches; changing `segment_ids` order busts.
```

---

## 8. File Map

```
src/api/search.py:37                      # router: classify → search_stocks_for_query | search_ticker_narrative | hybrid_search
src/services/query_router.py:21,241       # classify, heuristics, _extract_ticker_heuristic, detect_instrument_type
src/services/search_service.py:36,480,773 # hybrid_search (RRF, diversity, groups, has_more) + search_ticker_narrative/search_stocks_for_query
src/services/search_answer_service.py:44,88,98,127,221,336 # build_user_prompt, sanitize, parse, get_or_create (cache+ bust), _resolve_segments, _synthesize
src/services/search_coverage_service.py   # coverage (FinBERT)
src/schemas/__init__.py:199,314,326       # SearchRequest/Response, SearchAnswerResponse, SearchCoverageResponse, StockDiscoveryResult
web/src/app/(app)/search/page.tsx:91,162,337,440 # SearchAnswerCard, CoverageSnapshotCard, useSearch gating, answerSegmentIds
web/src/lib/hooks.ts:148,162              # useSearch (keepPreviousData), useSearchAnswer (joined ids, staleTime 10m)
web/src/lib/api.ts:380                    # api.search/Answer/Coverage
src/models/search_answer.py               # search_answers (query_hash PK, answer_json)
tests/test_search_answer.py, test_search_grouping.py, test_search_coverage.py, test_query_instrument_type.py
```

---

*Generated Aug 24 2026 for feature branch `feature/ph_2`. Keep this file as living debug doc — add new intents / edge cases here before touching `query_router` or `search_answer_service`.*
