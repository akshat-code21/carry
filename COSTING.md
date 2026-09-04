# 💰 Platform Costing — YT Chatter / Carry

**Last updated:** 2026-08-29
**Scope:** Every service, API, and infrastructure component used in production (`carry-fin.vercel.app` + `carry-api.akshat21.me`), with current vendor pricing, free-tier limits, per-unit cost math, and monthly scenarios.

> Prices are USD list prices verified on 2026-08-29 (Anthropic, Clerk, Aiven, Vercel from vendor pages; OpenAI from documented list prices — `gpt-5.4-nano` pricing is estimated from OpenAI's nano-tier history; Cloud SQL from GCP list rates — verify in the GCP Pricing Calculator). Always re-check vendor pricing pages before committing to a plan.

---

## 1. Architecture → Cost Map

| Layer | Component | Provider | Cost Type |
|---|---|---|---|
| Frontend | Next.js 16 hosting | Vercel | Fixed tier (free/flat) |
| Auth | Clerk (invite-only, JWT) | Clerk | Per-MRU (free ≤ 50k) |
| API | FastAPI + Uvicorn (4 workers) | GCP VM `asia-southeast1` | Fixed hourly |
| Workers | Celery worker + Celery beat | Same GCP VM (Docker) | Included in VM |
| Reverse proxy | Nginx + Let's Encrypt | Same GCP VM | Free |
| Database | PostgreSQL 16 + pgvector | GCP Cloud SQL (8 vCPU / 64 GB) | Fixed hourly |
| Cache / Broker | Redis 7 (Celery broker + cache) | Aiven (Singapore) | Fixed tier |
| Domain | `akshat21.me` | — | **Free** |
| LLM (all workloads) | `gpt-5.4-nano` — extraction, query routing, search answers, HFI pipeline | OpenAI | Per token |
| LLM (channel classification) | `gpt-4o-mini` | OpenAI | Per token |
| Embeddings | `text-embedding-3-small` (384-dim) | OpenAI | Per token |
| YouTube metadata | YouTube Data API v3 | Google | Free quota |
| Transcripts (primary) | `youtube-transcript-api` | Open source | Free |
| Transcripts (fallback) | Supadata.ai API | Supadata | Freemium |
| Transcripts (last resort) | `yt-dlp` + faster-whisper (local ASR) | Open source | VM compute only |
| New-video detection | WebSub (PubSubHubbub) + RSS poll | Google (free hub) | Free |
| Market prices | `yfinance` | Unofficial Yahoo | Free (ToS risk) |
| Macro data | FRED API | St. Louis Fed | Free |
| Social sentiment | Reddit API (OAuth), X via `twikit`, GDELT | Reddit / self-scraped | Free tier |
| Social sentiment (opt-in) | Adanos gateway | Adanos | Tiered (currently **unused**, provider = `native_raw`) |
| Sentiment NLP | FinBERT (ONNX, local inference) | Open source | VM compute only |

---

## 2. Fixed Infrastructure Costs

### 2.1 Compute — GCP VM (Singapore, `asia-southeast1`)

Runs the entire backend as Docker containers: `api` (uvicorn, 4 workers), `worker` (Celery, concurrency 2), `beat`, plus nginx. Also runs Whisper + FinBERT ONNX inference when transcripts need local ASR.

✅ **Confirmed current instance: `e2-medium` (~$25–27/mo on-demand in `asia-southeast1`, incl. ~$1–2/mo disk/egress).** A good fit for Whisper fallback + 4 workers. Reference alternatives:

| Instance | vCPU (shared) | RAM | ~$/month | Notes |
|---|---|---|---|---|
| `e2-small` | 0.5 | 2 GB | ~$13 | Too tight with 4 uvicorn workers + Celery + Whisper |
| **`e2-medium` (current)** | **1** | **4 GB** | **~$25–27** | Comfortable for current pipeline |
| `e2-standard-2` | 2 | 8 GB | ~$55 | Only needed if Whisper moves to `small.en`/`medium.en` |

**Estimate: ~$25–27/mo.**

### 2.2 Database — GCP Cloud SQL for PostgreSQL (8 vCPU / 64 GB)

✅ **Confirmed current setup:** production PostgreSQL (16 + pgvector) runs on a **GCP Cloud SQL custom instance — 8 vCPU / 64 GB RAM**. This is the **single largest line item** on the platform bill.

| Component | Rate (approx. list, `asia-southeast1`) | Monthly |
|---|---|---|
| Compute — 8 vCPU | ~$0.05–0.06 / vCPU-hr | ~$290–350 |
| Memory — 64 GB | ~$0.006–0.008 / GB-hr | ~$320–400 |
| SSD storage (10–50 GB) | ~$0.20 / GB-mo | ~$2–10 |
| **Total (8 vCPU / 64 GB)** | | **≈ $600–750 / mo** |

⚠️ Verify the exact figure in the [GCP Pricing Calculator](https://cloud.google.com/products/calculator) — rates differ slightly by edition (Enterprise vs Enterprise Plus) and drop ~25–35% with 1-year committed-use discounts.

🚨 **This instance is heavily oversized.** The database holds ~569 MB of data and the 7-day audit window showed only a few hundred requests. A **2 vCPU / 8 GB** custom instance (~$120–150/mo) — or even 1 vCPU / 4 GB (~$60–75/mo) — would comfortably handle current and growth-stage traffic. Downsizing is a **~$450–600/mo saving**, by far the biggest cost lever on the platform.

### 2.3 Redis — Aiven (Singapore)

Used as Celery broker, result backend, and search-answer cache. Light footprint.

- **Free/dev tier: $0** (current instance appears to be free tier)
- Paid Hobbyist-class: **~$12–15/mo** when you need persistence/HA guarantees

**Estimate: $0 → $12–15/mo at scale.**


### 2.4 Frontend — Vercel

| Plan | $/month | Edge requests | Data transfer |
|---|---|---|---|
| Hobby | **$0** | 1M/mo | 100 GB/mo |
| Pro | $20 (incl. $20 usage credit) | 10M/mo | 1 TB/mo |

At invite-only beta traffic you are comfortably inside Hobby. Upgrade triggers: custom team workflows, >1M requests, or spend management needs.

**Estimate: $0 now → $20/mo when commercializing.**

### 2.5 Domain — **Free**

- Domain: **$0**
- TLS (Let's Encrypt via Certbot): free

### 2.6 Infra subtotal

| State | Monthly |
|---|---|
| **Today (beta: e2-medium + Cloud SQL 8/64 + free tiers)** | **~$630–780** |
| Post-fixes (downsized Cloud SQL 2/8, same VM) | **~$150–180** |
| Production-ready (downsized Cloud SQL HA, paid Redis, Vercel Pro, e2-medium) | ~$330–360 |

---

## 3. Variable Costs — LLMs (OpenAI only)

✅ **Verified in code + env: zero Anthropic usage.** No `ANTHROPIC_API_KEY` is set, so `AnthropicLLMService` (present in `llm_service.py`) is never selected. Every LLM call goes through OpenAI:

| Workload | Model | Where |
|---|---|---|
| Claim/prediction/theme extraction, investor reports | `gpt-5.4-nano` (`OPENAI_MODEL=gpt-5.4-nano`) | `llm_service.py` |
| Query routing + search answer synthesis | `gpt-5.4-nano` (hardcoded `ANSWER_MODEL`) | `query_router.py`, `search_answer_service.py` |
| HFI entity/thesis extraction, ticker resolution | `gpt-5.4-nano` (hardcoded) | `src/pipeline/hfi/nodes/*`, `hfi/portfolio_service.py` |
| Channel-type classification | `gpt-4o-mini` (hardcoded) | `pipeline/ingestion.py` |
| Embeddings (384-dim) | `text-embedding-3-small` | `embedding_service.py` |

### 3.1 `gpt-5.4-nano` — the only chat model in production

Nano-class pricing (OpenAI's nano tier has historically been ~**$0.05–0.15 / MTok input, $0.40–0.60 / MTok output** — verify on the OpenAI pricing page; this model postdates the last verified page fetch):

**Per-video estimate** (~45-min video ≈ ~12k transcript tokens; ~14k input, ~4k output):

| Component | Tokens | Cost (at ~$0.10 in / $0.50 out per MTok) |
|---|---|---|
| Input (transcript + prompts) | ~14k | ~$0.0014 |
| Output (structured JSON: claims, themes, tickers) | ~4k | ~$0.0020 |
| **Total per video** | | **~$0.003–0.01** |

Per search (router + answer synthesis): **~$0.001–0.005**.

### 3.2 `gpt-4o-mini` — channel classification

List pricing $0.15/$0.60 per MTok; a few short calls per channel → **<$0.01 per channel**. Negligible.

### 3.3 OpenAI — `text-embedding-3-small`

List pricing: **$0.02 / MTok** (384-dim configured). Negligible.

- ~12k tokens per video → **$0.00024/video**
- 1,000 videos/month → **~$0.25/mo**

### 3.4 LLM cost scenarios

| Scenario | Videos/mo | Searches/mo | **LLM total/mo** |
|---|---|---|---|
| Beta (current) | 100 | 500 | **~$1–5** |
| Growth | 1,000 | 5,000 | **~$5–20** |
| Scale | 5,000 | 25,000 | **~$25–100** |

🔑 **The cost structure has flipped: infrastructure now dominates.** On nano-class models, LLM spend is nearly noise — Cloud SQL alone is ~95% of the current bill. LLM optimizations (caching, batching) are no longer worth engineering time; database right-sizing is.

---

## 4. Data Acquisition Costs

### 4.1 YouTube Data API v3 — **Free**
10,000 quota units/day. `channels.list`/`videos.list` = 1 unit, `search.list` = 100 units. Ingesting 50 videos/channel via `playlistItems` costs ~50–60 units → you can discover and fetch metadata for **hundreds of videos/day** within the free quota.

### 4.2 Transcripts — layered fallback chain
1. `youtube-transcript-api` — free, scrapes captions (most videos)
2. **Supadata.ai** (paid fallback) — freemium; free tier ~150 requests/mo, paid plans start ~**$10/mo** (verify — pricing page unreachable at time of writing). Only hit when captions are blocked/unavailable.
3. `yt-dlp` + faster-whisper (local ASR) — **$0 license, VM compute only**: ~0.1–0.3 CPU-minutes per audio-minute on `tiny.en`. A 45-min video ≈ 5–15 min of VM time ≈ **$0.02–0.10** of e2 instance time.

### 4.3 WebSub / PubSubHubbub — **Free**
Google's free hub. Only cost is that your API must be publicly reachable (already true).

### 4.4 Market data
- `yfinance` — **free** (unofficial; ToS/rate-limit risk → not for commercial redistribution of raw data)
- `fredapi` (FRED) — **free** API key
- ⚠️ If you ever need licensed market data for a commercial product: Polygon.io ($29–199/mo) or Twelve Data ($29+/mo) — **not currently used**.

### 4.5 Social sentiment
- **Reddit API (OAuth)** — free tier (100 queries/min) — sufficient for hourly ingest of 3 subreddits
- **X/Twitter via `twikit`** — free (account scraping) — ⚠️ ToS risk, account-ban risk; official X API v2 is $200+/mo (Basic) if you need legitimacy
- **GDELT** — free
- **Adanos** — configured but **inactive** (`SENTIMENT_PROVIDER=native_raw`, `ADANOS_PLAN=free` → $0 today). Paid tiers exist with a configured monthly budget cap of **$225** — only enable when the native pipeline can't keep up.

**Data acquisition subtotal today: $0/mo** (Supadata only if captions fail often → $0–10).

---

## 5. Auth — Clerk

Verified pricing (billed by **Monthly Retained Users**, MRU — a user counts only if they return ≥24h after signup):

| Plan | $/month | MRU included |
|---|---|---|
| Hobby | **$0** | 50,000 |
| Pro | $25/mo ($20/mo annual) | 50k, then $0.02/MRU |
| Business | $250/mo | + SOC2, priority support |

You're on **live keys** but invite-only → thousands of users cost **$0**. Even 10,000 retained users stays free. Pro becomes relevant for: custom session lifetime, MFA, remove branding, more log retention.

**Estimate: $0 now → $25/mo at commercial launch.**

---

## 6. Total Platform Cost — Summary

### Current state (invite-only beta)

| Item | $/month |
|---|---|
| GCP VM `e2-medium` (backend + workers + ASR) | ~$25–27 |
| GCP Cloud SQL PostgreSQL (8 vCPU / 64 GB) | ~$600–750 |
| Aiven Redis (Free tier) | $0 |
| Vercel (Hobby) | $0 |
| Domain | $0 |
| Clerk (Hobby, <50k MRU) | $0 |
| YouTube API / WebSub / FRED / yfinance / Reddit / FinBERT | $0 |
| Supadata (fallback, occasional) | $0–10 |
| LLMs (OpenAI: gpt-5.4-nano + gpt-4o-mini + embeddings) | ~$1–5 |
| **TOTAL** | **≈ $625–790 / month** |

### At growth (1,000 videos/mo, ~5k searches/mo)

| Item | $/month |
|---|---|
| GCP VM `e2-medium` | ~$27 |
| GCP Cloud SQL PostgreSQL (8 vCPU / 64 GB) | ~$600–750 |
| Aiven Redis (paid) | ~$12–15 |
| Vercel Pro | $20 |
| Clerk Pro | $25 |
| LLMs (OpenAI) | ~$5–20 |
| Adanos (if enabled) | up to $225 (budget-capped) |
| **TOTAL** | **≈ $690–855 / month** |

### Cost per unit (unit economics at growth scale)

| Unit | Cost |
|---|---|
| Ingest + fully analyze 1 video (LLM only) | **<$0.01** |
| Serve 1 user search (LLM only) | **~$0.001–0.005** |
| Infra per video at 1,000 videos/mo (VM + Cloud SQL) | **~$0.65–0.80** |
| 1 monthly retained user (10 searches + browsing) | **~$0.70–0.90** |

→ COGS is **infrastructure-bound, not AI-bound**. Down-sizing Cloud SQL from 8 vCPU/64 GB to 2 vCPU/8 GB drops per-user infra cost by ~75% and is worth more than every LLM optimization combined.

---

## 7. Recommendations (biggest savings first)

1. **Downsize Cloud SQL** — 8 vCPU / 64 GB is massively oversized for a ~569 MB database. Move to **2 vCPU / 8 GB (~$120–150/mo)**: saves **~$450–600/mo**, and coincidentally fixes the connection-pool sizing from the latency audit. If the instance was sized for pgvector scans, note that 384-dim vectors are tiny — RAM pressure should be minimal.
2. **If you must keep the big instance**: buy a **1-year committed-use discount** (~25–35% off) instead of paying on-demand.
3. **Keep the current GPT model lineup** — `gpt-5.4-nano` for all chat workloads is already near-optimal cost-wise; `gpt-4o-mini` for classification is fine. No changes needed.
4. **Keep `tiny.en` Whisper** — moving to `small.en` costs VM size, not license, but doubles-to-quadruples compute. `tiny.en` is ~$0.05/video of e2 time — fine.
5. **Stay on `native_raw`** sentiment (Reddit+GDELT free) as long as possible; Adanos professional ($225 budget) is a scale-time decision, not a now decision.
6. **Use Cloud SQL private IP** — the DB is now on GCP alongside the VM; switch from public IP to private IP (free) to cut latency and egress charges.
7. **Watch Vercel/Hobby limits** — 1M edge requests/mo is plenty now; the `/api` rewrite proxy means every page load generates multiple edge requests.

---

## 8. Security note (found during this audit)

`web/.env.prod` contains a **live Clerk secret key** (`sk_live_...`). The file is gitignored (not committed — verified), but treat it as sensitive: never paste it into chats/issues, and rotate it from the Clerk dashboard if it has ever been shared.

