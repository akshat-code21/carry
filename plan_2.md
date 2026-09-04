# Financial Media Accountability Engine
## Implementation Plan - Prototype (Seed Channel: Prof G Markets)

*A build plan for a 3-day prototype sprint. Scope, stack, and scoring depth reflect decisions confirmed during scoping (Section 0).*

---

## 0. Confirmed Scope

Three decisions anchor this plan:

1. **Backfill scope - full history, not a sample.** "3 days" is the *build* timeline, not a data-window limit. As of research for this plan (mid-July 2026), Prof G Markets has **~370 published episodes**, releasing several times a week, averaging ~48 minutes each. That's the real corpus to design around - a few hundred videos, not a handful.
2. **Stack - Python + Postgres + TypeScript/Next.js.** A deliberate two-runtime split: Python owns ingestion, extraction, and resolution (the "brain"); Next.js owns the search UI and browsing experience (the "face"); Postgres is the single shared source of truth both sides read and write.
3. **Scoring rigor - broad.** The system should grade not just hard ticker/price-target calls but also macro and directional commentary ("the Fed will cut," "the market's due for a correction"). Section 5.6 is the core design response to this: a **tiered resolution engine**. "Broad" and "defensible" pull in different directions, and reconciling them - rather than glossing over it - is the single most important design decision in this document.

### Assumptions (flag anything that's wrong)
- One developer or a small team is building this, not a large engineering org.
- You can obtain (same-day, free) an Anthropic API key, a YouTube Data API key, and a FRED API key.
- Prototype hosting budget is minimal - tens of dollars a month, not enterprise infrastructure.
- The goal of the prototype is to prove the pipeline and the product experience, not to serve production traffic. Auth, multi-tenancy, and abuse-handling are explicitly deferred (Section 12).
- Greenfield build - no existing codebase to integrate with.

---

## 1. What We're Building

A search and accountability layer over financial YouTube commentary. The system ingests a channel, transcribes every episode, extracts the concrete calls and predictions being made (who said it, about what, in which direction, by when), and - as time passes - checks each one against what actually happened in the market or economy. Users get a search interface over the result: "what has X said about Y," filterable by person, ticker, claim type, and outcome, plus a natural-language "ask" mode that answers questions with citations back to specific claims and the exact video timestamp they came from.

The prototype is a single channel, fully self-contained, built to validate the pipeline end-to-end before any multi-user/multi-channel product work begins.

---

## 2. The Seed Channel, Grounded

A few facts worth designing around, gathered while scoping this plan:

- **~370 episodes** as of mid-July 2026, averaging **~48 minutes**, released several times a week (marketing copy says "daily" - treat that as aspirational, not literal).
- Co-hosted by **Scott Galloway and Ed Elson**, but a large share of episodes bring on a named outside expert (e.g., a hedge fund founder, an equity analyst, an economist), each making their own calls - a lot of the highest-value, most specific claims in the archive will be **guest** claims, not host claims.
- The host chair itself isn't fixed - at least one episode has had a guest host filling in for Scott. Don't hardcode "speaker is always Galloway or Elson."
- There's a **dedicated year-ahead predictions episode** (stock pick, tech pick, AI forecast for the year) - direct validation that the "claim → outcome" format this product is built around is exactly the kind of content this show already produces on purpose.
- Show notes reliably name guests and their affiliation ("X is the founder and CEO of Y") - a strong, cheap signal for participant resolution (Section 5.3). This is a property of a well-produced Vox Media show; don't assume it generalizes to every channel a user adds later (Section 11).

---

## 3. Architecture Overview

```
[1] Video Discovery & Backfill          (yt-dlp / YouTube Data API)
        │
        ▼
[2] Transcript Acquisition               (youtube-transcript-api → yt-dlp+Whisper fallback)
        │
        ▼
[3] Participant Resolution                (title/description parsing + person dedup)
        │
        ▼
[4] Claim Extraction                      (Claude Sonnet 5, chunked, schema-constrained, Batch API)
        │
        ▼
[5] Entity / Ticker Resolution
        │
        ▼
[6] Claim Resolution Engine (tiered)  ◀──── Market Data Cache (yfinance/Finnhub)
        │                              ◀──── Econ Indicator Cache (FRED)
        ▼
[7] Postgres + pgvector                  (system of record + embeddings)
        │
        ▼
[8] Search / RAG API                      (FastAPI: hybrid search + /ask endpoint)
        │
        ▼
[9] Next.js Frontend                      (search, claim cards, person/channel/video pages)
```

Stages 1–6 are Python batch/worker jobs. Stage 7 is the shared boundary. Stages 8–9 are the served application. This split is exactly what the confirmed stack choice implies, and it means the pipeline can keep running (new videos, ongoing resolution) with zero coupling to whatever the frontend is doing.

---

## 4. Data Model

Illustrative Postgres schema - the shape matters more than exact types; adjust as you build.

```sql
CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector, for semantic search

CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_channel_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    handle TEXT,
    added_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL,
    aliases TEXT[],                    -- {'Scott', 'Prof G', 'Scott Galloway'}
    affiliation TEXT,                  -- 'Founder & CEO, Galaxy Digital'
    is_recurring_host BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES channels(id),
    youtube_video_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    duration_seconds INT,
    transcript_status TEXT DEFAULT 'pending',   -- pending | fetched | asr_fallback | failed
    transcript_raw JSONB,                       -- [{start,end,text}, ...] - INTERNAL ONLY, never served whole
    processed_status TEXT DEFAULT 'pending',    -- pending | extracted | failed
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE video_participants (
    video_id UUID REFERENCES videos(id),
    person_id UUID REFERENCES persons(id),
    role TEXT NOT NULL,                -- host | co_host | guest | guest_host
    PRIMARY KEY (video_id, person_id)
);

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    speaker_id UUID REFERENCES persons(id),
    ts_start_seconds INT NOT NULL,
    ts_end_seconds INT,
    raw_quote TEXT,                    -- short excerpt only, never a long passage
    paraphrase TEXT NOT NULL,
    claim_type TEXT NOT NULL,          -- price_target | directional_call | macro_prediction | event_prediction | general_take
    entities TEXT[],                   -- {'NVDA'} or {'FEDFUNDS'}
    direction TEXT,                    -- bullish | bearish | neutral | specific
    magnitude NUMERIC,                 -- e.g. 150.00, or 20 (percent)
    magnitude_unit TEXT,               -- usd_price | percent | null
    timeframe_text TEXT,               -- as spoken: 'by Q3 2026'
    resolves_by DATE,                  -- normalized resolution date
    confidence_language TEXT,          -- hedged | moderate | confident
    resolution_tier INT,               -- 1 = price data, 2 = econ data, 3 = LLM judge
    resolution_status TEXT DEFAULT 'pending', -- pending | correct | incorrect | mixed | too_vague | expired_unresolved
    resolution_evidence JSONB,         -- price series snapshot / FRED datapoint / judge reasoning
    resolved_at TIMESTAMPTZ,
    embedding VECTOR(1024),            -- over `paraphrase`, for semantic search
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE market_data_cache (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume BIGINT,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE econ_indicator_cache (
    series_id TEXT NOT NULL,           -- FRED series id: 'FEDFUNDS', 'CPIAUCSL', 'UNRATE'...
    date DATE NOT NULL,
    value NUMERIC,
    PRIMARY KEY (series_id, date)
);
```

`claims` is the center of gravity - everything the frontend renders and everything search queries against comes from this one table plus its two caches.

---

## 5. Pipeline, Stage by Stage

### 5.1 Discovery & Backfill
Resolve the `@ProfGMarkets` handle to a `channel_id` and uploads-playlist ID once (YouTube Data API `channels.list`, 1 quota unit). Then enumerate all ~370 videos cheaply with `yt-dlp --flat-playlist -j` (no API quota consumed) or `playlistItems.list` (~1 unit per 50 videos - trivially inside the free 10,000-units/day quota either way). Insert a stub row per video into `videos` with `transcript_status = 'pending'`.

### 5.2 Transcript Acquisition
Primary path: **`youtube-transcript-api`** (Python, free, no auth, still the most widely used and actively maintained option for this in 2026). It fetches YouTube's existing caption file - this is a text download, not real-time audio processing, so backfilling all 370 videos this way is fast (expect well under an hour with polite rate-limiting, not an overnight job).

Two practical gotchas worth designing around from day one, not discovering mid-backfill:
- **No official transcript API exists.** The YouTube Data API's captions endpoint only works via OAuth for videos *you* own - it can't be used to fetch a third-party channel's captions. Unofficial libraries are the only route for arbitrary public channels.
- **Cloud IPs get blocked faster than residential ones.** If you run the backfill from a cloud VM and hit request-blocked errors, that's expected - add delay + exponential backoff, or run the one-time backfill from a local/dev machine.

Fallback (for the small fraction of videos with no captions at all): download audio with `yt-dlp`, transcribe via Whisper (or `faster-whisper` locally). This is slower and should be the exception, not the default path - budget for it but don't design the primary pipeline around it.

Store the transcript with per-segment timestamps in `transcript_raw`. This field is internal only - never rendered to end users (see Section 7's display rule).

### 5.3 Participant Resolution
Parse each video's title and description for named guests and their stated affiliation - Vox Media's show notes are reliable here ("X is the founder and CEO of Y"). A cheap regex/heuristic pass, backed by a small LLM call (Haiku-tier is enough) for the harder cases, populates `persons` (with fuzzy-match dedup, since recurring guests should map to one person record, not a new one per appearance) and `video_participants`. Do not hardcode host = Galloway + Elson - check for the guest-host case explicitly.

In-transcript, per-claim speaker attribution is handled as part of extraction (5.4), not as a separate diarization step: the extraction call receives the resolved participant list for that episode and infers who's speaking from context (names addressed directly, self-references matched to known bios). This is a pragmatic v1 choice - good enough to ship, not perfect. If manual spot-checks show attribution is too noisy, real audio diarization (e.g., `pyannote-audio`, aligned back to transcript timestamps) is the natural v2 upgrade - flagged here so it isn't a surprise later.

### 5.4 Claim Extraction
Chunk each transcript into ~5–8 minute windows with a small overlap (~30s) so claims spanning a chunk boundary aren't lost. For each chunk, call **Claude Sonnet 5** with:
- A **cached system prompt**: the claim schema, extraction rubric, and a couple of few-shot examples (see Appendix A) - identical across all ~2,200 chunk calls, which is exactly what prompt caching is for (up to 90% off the repeated portion after the first call).
- **User content**: the chunk's transcript with timestamps, plus the episode's resolved participant list and their affiliations.
- **Structured JSON output** matching the `claims` schema, with an explicit instruction to skip generic banter and to leave `magnitude`/`timeframe_text` null rather than invent one.

Run the whole backfill through the **Message Batches API**, not the synchronous endpoint - this isn't time-sensitive, batching gets a flat 50% discount on top of caching, and it comfortably fits a multi-day build (see Section 9 for the cost math and Section 10 for why you should submit this batch as early as possible given batch jobs can take up to 24 hours to fully complete).

A light per-video merge/dedupe pass afterward catches claims extracted twice from overlapping chunk boundaries.

### 5.5 Entity / Ticker Resolution
Maintain a small `ticker_lookup` table (company-name variants → ticker), seeded from a public listed-company symbol file. Ask the extraction model to propose a ticker directly when it's confident (it usually will be - "Nvidia" → `NVDA`), falling back to the lookup table, then to a small manual "needs review" queue for anything genuinely ambiguous. Expect this queue to be short.

### 5.6 Claim Resolution Engine (Tiered) - the core response to "broad" scoring
This is where the credibility-vs-coverage tension from the scoping discussion gets resolved concretely, via three tiers sharing one schema:

**Tier 1 - Quantitative price/ticker claims.** Claims with a ticker, a direction or target, and a timeframe. Once `resolves_by` has passed (a daily cron checks), pull the ticker's close price near that date from `market_data_cache`, plus a benchmark index (e.g., SPY) for relative context, and apply a deterministic rule: hit the target within tolerance → `correct`; right direction, missed the number → `mixed`; wrong direction → `incorrect`. Fully automated, no LLM call needed at resolution time.

**Tier 2 - Macro/economic claims with an identifiable data series.** Fed-rate calls, CPI/inflation calls, unemployment, GDP - recurring themes on a show like this. Maintain a small curated map from common claim patterns to FRED series IDs (`FEDFUNDS`, `CPIAUCSL`, `UNRATE`, `GDP`, …), pull the series for the resolution window, and check the claim against what actually happened. Mostly automatable; the map needs occasional manual upkeep as new claim patterns show up.

**Tier 3 - Vaguer directional/sentiment calls.** "The market's due for a correction." "AI is in a bubble." No ticker, no clean series to check. At resolution time (a default window if the speaker gave none - e.g. 6 months, re-checked periodically up to an 18–24 month cutoff), run an **LLM-as-judge** pass: feed the original claim plus the intervening period's index performance and a few relevant headlines, and ask for a verdict from a fixed rubric - `directionally_correct | directionally_incorrect | mixed | too_soon | unfalsifiable_as_stated` - with a one-line justification stored in `resolution_evidence`. Use Sonnet 5 by default; escalate genuinely hard cases to Opus 4.8 or a human reviewer if spot-checks show inconsistency.

**Critical UI rule:** Tier 1/2 outcomes are labeled "data-verified"; Tier 3 outcomes are labeled "AI-assessed judgment," visibly distinct. This is what lets the product deliver on "broad" without quietly overstating how objective a "the market's due for a correction - WRONG ❌" badge actually is. All three tiers write into the same `resolution_status`/`resolution_evidence`/`resolution_tier` columns, so the frontend renders one consistent claim card type regardless of tier.

### 5.7 Ongoing Ingestion (New Videos)
Prototype-grade: a scheduled job every 1–4 hours polls the channel's RSS feed (`https://www.youtube.com/feeds/videos.xml?channel_id=...`) for video IDs not yet in `videos` - free, no quota. Stronger option worth adding once the polling version is stable: subscribe to the channel's feed topic via **PubSubHubbub/WebSub**, which pushes a near-real-time callback on new uploads and removes polling entirely - a small additional effort on top of an already-working pipeline. Either way, a new video re-enters the pipeline at Stage 2 automatically; claims whose timeframe hasn't elapsed simply stay `pending` until it does.

---

## 6. Search & Serving Layer

FastAPI, backed directly by Postgres:

- **Hybrid search**: Postgres full-text search (`tsvector`/GIN) over `paraphrase`/`raw_quote` for keyword queries, combined with `pgvector` cosine similarity over `embedding` for natural-language queries. A simple reciprocal-rank-fusion merge of the two result sets covers both "NVDA earnings" and "who thinks AI spending is overdone" style queries well.
- **Filters**: person, ticker/entity, claim type, date range, resolution status (correct/incorrect/pending/AI-assessed), channel.
- **`/ask` endpoint (RAG)**: embed the user's question, retrieve the top-k matching claims, feed them plus the question to Claude to synthesize a direct answer that cites specific claims - each citation links to that claim's video timestamp. This is the actual "search engine" experience the product is named for: "What has Scott Galloway said about Nvidia, and was he right?" → a synthesized answer plus the underlying claim cards.

---

## 7. Frontend (Next.js + TypeScript)

- `/search` - query box + filter sidebar, results as claim cards.
- `/claim/[id]` - full detail: paraphrase, short quote, resolution evidence, embedded video seeked to the exact timestamp.
- `/person/[id]` - track-record profile: accuracy breakdown by claim type and tier, full claim list.
- `/channel/[id]` - channel overview, episode list.
- `/video/[id]` - embedded player + every extracted claim for that episode, each clickable to seek.

**Firm display rule**: never render a full transcript in the UI. Always short quote + paraphrase + a deep link that jumps to the moment in the actual video (YouTube iframe API `seekTo()`, or a plain `&t=Xs` link). This is safer on the copyright front than displaying raw transcripts wholesale, and it's honestly a better product - it sends people to the source instead of trying to replace it.

---

## 8. Tech Stack Summary

| Layer | Choice | Why |
|---|---|---|
| Backend / pipeline | Python (FastAPI + async workers) | Best ecosystem for LLM orchestration, scraping, and data libraries |
| Frontend | Next.js + TypeScript | Confirmed preference; fast to build, easy to deploy |
| Database | Postgres + pgvector | One database for structured data *and* vector search - no separate vector DB needed at this scale |
| LLM | Claude Sonnet 5 (Batch API + prompt caching); Opus 4.8 for escalation | Matches Anthropic's own model-selection guidance (Haiku for simple, Sonnet for most production work, Opus for hard reasoning); batching + caching make the backfill cheap |
| Transcript source | `youtube-transcript-api`, with `yt-dlp` + Whisper as fallback | Free, actively maintained; wrap behind an interface so it's swappable later (Section 11) |
| Video discovery | `yt-dlp` (backfill) + RSS/PubSubHubbub (ongoing) | No API quota burned |
| Stock/ETF price data | `yfinance` (backfill) + Finnhub free tier (ongoing) | Free and sufficient at this volume - note Polygon.io no longer has a free tier and IEX Cloud shut down in 2024, so don't reach for either |
| Macro/econ data | FRED API | Official, free, ~120 req/min with a (free) key, 800,000+ series |
| Deployment | Small managed Postgres + a small app host (Render/Fly/Railway-class) for the API; Vercel-class host for Next.js | Cheap and simple; revisit before multi-user scale |

---

## 9. Cost & Time Estimate

**LLM (extraction):** ~370 videos × ~6 chunks ≈ 2,200 extraction calls. Roughly 5–6M input tokens and 2–2.5M output tokens total. At Sonnet 5's batch rate (~$1/$5 per million tokens during the current introductory pricing period), that's roughly **$15–20** for the extraction pass alone; with a buffer for the merge pass, ticker resolution, and the initial Tier 3 judge calls, budget **$25–50 total** for the entire backfill's LLM spend. This is genuinely a non-issue at this scale.

**Market/econ data:** $0 - `yfinance`, Finnhub's free tier, and FRED all comfortably cover a few hundred unique tickers plus a handful of macro series at prototype volume.

**Hosting:** Roughly $20–50/month for a small Postgres instance and a small compute host, or $0 if you run Postgres locally for the duration of the prototype.

**Time:** See the day-by-day plan below - the real constraint isn't cost, it's sequencing around the Batch API's up-to-24-hour turnaround window.

---

## 10. 3-Day Build Plan

**Day 1 - Ingest**
- Repo, Postgres schema, FastAPI skeleton.
- Discovery: enumerate all ~370 videos (fast).
- Transcript backfill for all videos (fast - this is a text download, not audio processing; budget the rest of the day for the fallback path on whatever fraction lacks captions).
- Participant-resolution heuristic built and run against titles/descriptions.
- Draft the extraction prompt and hand-check it against 5–10 sample videos *before* committing to the full run.

**Day 2 - Extract & resolve (Tier 1/2)**
- Once the prompt checks out on samples, submit the **full Batch API extraction job as early in the day as possible** - batches can take up to 24 hours, so this should not be a Day-3 task.
- While it runs: build entity/ticker resolution, the Tier 1 (price) resolution engine, backfill `market_data_cache` for every ticker that shows up, and wire up the FRED integration for Tier 2.
- If more than one person is building this, frontend scaffolding (search page shell, claim card component, against mock data) can start in parallel here rather than waiting for Day 3.

**Day 3 - Serve & ship**
- Load the completed batch results into `claims`; run Tier 1/2 resolution across everything now in the database.
- Build and run the Tier 3 LLM-judge pass on the qualitative subset.
- Build the search API (hybrid search + `/ask`) and the frontend pages.
- Spot-check a random sample of claims against the source video for extraction quality, smoke-test end to end, polish, deploy.

---

## 11. Risks & Open Design Decisions

1. **Claim extraction will be noisy at first.** Hedged, argumentative, conversational speech doesn't turn into clean structured claims on the first try. Plan for the Day-1 sample-check step above, and consider a standing practice of spot-checking a random N claims per week even after backfill.
2. **Tier 3 defensibility.** The AI-assessed / data-verified labeling split in Section 5.6 is the mitigation - don't let it get lost or merged visually in the frontend, since it's carrying real credibility weight.
3. **Speaker attribution is a heuristic, not ground truth.** LLM-inferred from context, not audio diarization. Fine for v1; flag it if guest-heavy episodes start showing visibly wrong attributions.
4. **Two unofficial dependencies: `youtube-transcript-api` and `yfinance`.** Both are scraping-based, both are fine at one-channel scale, and both are exactly the kind of dependency that should sit behind a clean interface (`TranscriptSource`, `MarketDataSource`) from day one - so that swapping in a managed provider (several now exist for transcripts; Finnhub/Twelve Data paid tiers or a licensed vendor for market data) later is a config change, not a rewrite.
5. **The metadata-parsing heuristic (5.3) is validated for *this* channel specifically** - Vox Media writes detailed, consistent show notes. A lower-budget or single-host channel a user adds later may not, so don't treat participant resolution as "solved" going into the multi-channel phase.
6. **Not legal advice, but worth a real lawyer's look before any public launch:** publishing accuracy scorecards attached to named real people sits adjacent to both copyright (mitigated by the no-full-transcript display rule) and accuracy/defamation-adjacent concerns (mitigated by always linking to source, keeping paraphrases faithful, and the data-verified/AI-assessed distinction). None of this blocks a personal prototype; it matters once other people's names are attached to public "was he right" scores at any scale.

---

## 12. Path to Multi-Channel / Multi-User (Post-Prototype, Not Part of the 3-Day Build)

- **Auth & ownership**: user accounts, per-user channel subscriptions/ownership.
- **Ingestion becomes a real queue**, not a one-off script - many channels' new videos will arrive continuously (Celery/RQ or a cloud task queue).
- **Swap the unofficial dependencies** flagged in Risk #4 for managed/paid providers as volume grows - the interface boundary from day one is what makes this cheap later.
- **Participant resolution needs to get more robust** for channels with less reliable show notes than this one (Risk #5).
- **Rate-limiting and abuse controls** once arbitrary users can point the pipeline at arbitrary channels - cost control matters once you're not the only one triggering backfills.
- **Cross-channel person dedup**: the same guest can appear on multiple channels a user adds. `persons` is already channel-agnostic in the schema above specifically so this doesn't require a redesign later.

---

## 13. Immediate Next Steps

1. Register API keys: Anthropic, YouTube Data API v3, FRED.
2. Stand up Postgres locally (or a small managed instance) with the pgvector extension enabled, and run the Section 4 schema.
3. Resolve `@ProfGMarkets` to its `channel_id`, and enumerate all videos via `yt-dlp --flat-playlist -j`.
4. Pull transcripts for 5–10 videos and hand-write/test the extraction prompt (Appendix A) against them before touching the other ~360.
5. Once that checks out, proceed through the pipeline in the order laid out in Section 10.

---

## Appendix A: Example Extraction Prompt (Illustrative)

```
SYSTEM (cached across all ~2,200 chunk calls):

You are extracting checkable, concrete claims and predictions from a segment
of a financial-news podcast transcript.

Known participants in this episode:
- Scott Galloway (co-host, NYU Stern professor)
- Ed Elson (co-host)
- Mike Novogratz (guest - Founder & CEO, Galaxy Digital)

For EACH concrete, checkable claim or prediction made - skip generic banter,
throat-clearing, or unfalsifiable philosophizing - output one JSON object with:

- speaker: best-guess name from the participant list, based on context
- ts_start / ts_end: approximate timestamp range in the transcript
- raw_quote: a short verbatim excerpt (<25 words)
- paraphrase: a one-sentence plain-English restatement
- claim_type: one of [price_target, directional_call, macro_prediction,
  event_prediction, general_take]
- entities: tickers/companies/macro indicators mentioned
- direction: one of [bullish, bearish, neutral, specific_target]
- magnitude: a number if a specific target/percentage was stated, else null
- timeframe_text: the timeframe as stated ("by end of the year"), else null
- confidence_language: one of [hedged, moderate, confident]

Never invent a magnitude or timeframe the speaker didn't state - leave it
null. Vague claims are still worth extracting; they're handled by the
qualitative-judgment resolution tier downstream, not discarded here.

Return only a JSON array. No prose.
```