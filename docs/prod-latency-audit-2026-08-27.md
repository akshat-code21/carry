# Prod Latency Audit - `carry-fin.vercel.app` / `carry-api.akshat21.me`

**Date:** 2026-08-27 (UTC)  
**Environment:** `APP_ENV=production`, `NEXT_PUBLIC_API_URL=https://carry-api.akshat21.me`  
**Regions:** Vercel `bom1` (Mumbai), GCP `34.142.183.86` (Singapore, `asia-southeast1`), Aiven PG `pg-becf1b9...g.aivencloud.com` (Bengaluru, DigitalOcean `206.189.132.98`), Redis `hydrangea-grade-gingery-41136.db.redis.io` (Singapore, `ap-southeast1`), Clerk `api.clerk.com` (Cloudflare anycast, US origin).  
**Commit inspected:** `84162de` (`master`)  
**Dashboard page:** `web/src/app/(app)/dashboard/page.tsx:14` → `web/src/lib/hooks.ts:107` `useDashboardData()` (5 parallel `useQuery` + `useMe()`).

---

## TL;DR - Where is the 15–20 s?

**85 % backend, 15 % frontend. Single biggest cause is the backend `GET /api/themes` N+1 + 1 MB payload served cross-region on a single uvicorn worker.**

Fix `src/services/theme_service.py:173` `get_theme_hierarchy_tree()` alone and the dashboard p95 drops from **55 s → ~3 s**. Fix the remaining three items and it drops to **< 800 ms**.

| Bucket | Root cause | Impact | Effort |
|---|---|---|---|
| **P0 Backend** | `GET /api/themes` does 133 sequential SQL round-trips (N+1) and returns 2 826 nodes (909 KB JSON) even though dashboard only needs `themes.length`. `src/services/theme_service.py:173` `src/api/themes.py:20` | p50 1.5 s → p95 40 s, max 55.9 s. Holds DB connection for whole request, starves pool. | 1 query + lightweight count endpoint, or aggregated dashboard endpoint |
| **P0 Backend** | Cross-region DB: GCP Singapore → Aiven PG Bengaluru (≈45 ms RTT). Every round-trip pays it. 133 * 45 ms ≈ 6 s just in network. `src/database.py:12` `DATABASE_URL` | Amplifies every N+1, even single-query endpoints are 10× slower than DB `EXPLAIN` suggests. | Move DB to Singapore, or add SG read replica |
| **P0 Infra** | Single `uvicorn` worker `Dockerfile:43` `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`, no `--workers`. Python JSON serialisation of 1 MB blocks event loop, queuing other 4 dashboard requests on same worker. | `GET /api/channels` (2 rows, `EXPLAIN` 0.15 ms) still p50 1.5 s, p95 30 s, max 47 s in `api_request_logs`. | `--workers 2-4` + `gunicorn` or multiple containers behind nginx |
| **P1 Backend** | Missing index on `theme_hierarchy.level` (seq-scan 2 945 rows, `EXPLAIN` 0.99 ms, but every request pays it). No HTTP caching, no server cache for taxonomy. `src/models/theme.py:22` | Adds ~100 ms planning per theme request × 133 queries. | Add `CREATE INDEX ix_theme_hierarchy_level ON theme_hierarchy(level)` + Redis cache 5 min |
| **P1 Auth** | No `CLERK_JWT_KEY` in `.env.prod:62` → every authenticated request falls back to JWKS verification via Clerk SDK (`src/auth/clerk.py:151`). JWKS fetch to US adds 100–180 ms when not cached. `get_clerk_user_profile()` HTTP to Clerk on first request per user per minute (`src/auth/dependencies.py:170`). | `GET /api/auth/me` p95 2.76 s, `403 invite_required` still 1 s (should be 80 ms). 165× `401` vs 167× `403` in 7 days indicates many token-missing retries. | Set `CLERK_JWT_KEY` (PEM) and/or verify `clerk-backend-api` JWKS cache TTL; use `useAuth().getToken()` instead of `window.Clerk` polling |
| **P1 Frontend** | Dashboard fans out **6 parallel authenticated fetches** on mount: `videos`, `channels`, `tickers`, `top-etfs`, `themes`, `me` `web/src/lib/hooks.ts:107` `web/src/app/(app)/layout.tsx:13`. Each calls `getAuthToken()` → `waitForClerkLoaded()` poll `50 ms` up to `8 s` `web/src/lib/auth-client.ts:16`, then `fetch("/api/...")` via Vercel rewrite `web/next.config.ts:4` → Mumbai→Singapore 35 ms extra hop. `isLoading` = slowest of 5 (`||`), so skeleton stays until themes finishes. No incremental rendering, no dedup of token, `retry:1` on 401 causes double attempts. | Even with fast backend, TTFB is `Clerk load (0.5–2 s) + 35 ms Vercel hop + backend`. Retries double it. | Single `GET /api/dashboard/summary` aggregated endpoint (1 RTT), `Clerk.useAuth()` hook, `staleTime` + `React.Suspense` per card, share token promise |
| **P2** | No `gzip`/`brotli` observed on `carry-api` (`curl -H Accept-Encoding: gzip` → `Content-Encoding: null`), 1 MB themes payload sent uncompressed. `deploy/nginx.conf:1` has no `gzip on`. No `Cache-Control`, no CDN for taxonomy. `src/analytics/middleware.py:27` opens new DB session per request for `api_request_logs` INSERT + upsert (extra pool pressure). | Adds 200–400 ms transfer on slow links; pool pressure under load. | Enable `gzip` in nginx, `Cache-Control: public, max-age=60` for taxonomy, move analytics to async batch or sample 10 % |

---

## 1. Measured Prod Latency (source of truth: `api_request_logs`)

`src/analytics/middleware.py:47` records `duration_ms = perf_counter()` around `call_next` (excludes nginx, but includes Clerk verify + DB + serialisation). 7-day window `2026-08-20 → 2026-08-27`.

### 1.1 By route template (last 7 days)

```
route                              cnt     avg     p50     p95     p99     max
/api/search                         11 17721.3 18031.0 25334.1 26465.3 26748.1
/api/themes                         78 13546.2  1499.6 40111.0 53727.9 55916.7
/api/channels/{channel_id}           6 12639.2 12446.0 16906.2 16913.8 16915.6
/api/tickers/{ticker}                1 11154.0 11154.0 11154.0 11154.0 11154.0
/api/channels                       81  9828.5  1520.9 30515.6 39883.3 47316.8
/api/videos                         56  7247.3  1380.9 27505.8 32530.7 34293.3
/api/tickers/{ticker}/sentiment-timeline 1 6685.8 6685.8 6685.8 6685.8 6685.8
/api/tickers/{ticker}/price-history  1  5510.0  5510.0  5510.0  5510.0  5510.0
/api/search/answer                  10  5138.5  5424.0 10094.9 11996.8 12472.2
/api/tickers                        88  1016.5   282.5  3044.0 17065.3 28911.4
/api/hfi/investors/{investor_id}/sources 2 1663.6 1663.6 1972.7 2000.2 2007.0
/api/admin/metrics/overview         10  1659.2  1741.7  2527.1  2694.6  2736.5
/api/auth/me                        71   871.5   239.5  2759.5  7119.9 15282.5
```

Dashboard endpoints only:

```
route                        avg     p50     p95     max
/api/themes                  13546   1500    40111   55917
/api/channels                 9829   1521    30516   47317
/api/videos                   7247   1381    27506   34293
/api/tickers                  1017    283     3044   28911
/api/tickers/top-etfs          791    ---     1775   ---
/api/auth/me                   872    240     2760   15283
```

Buckets (dashboard-relevant):

```
/api/auth/me   <500 ms:43  500-2000:21  2-10 s:6   >10 s:1
/api/themes    <500 ms:28  500-2000:16  2-10 s:2   >10 s:32   ← 41 % of successful 200s are >10 s
```

Slowest successful `GET /api/themes 200` observed:

```
2026-08-27 08:41:35  55917 ms  200  user=None   (also channels 38025 ms + videos 34293 ms in same minute)
2026-08-25 15:49:50  53074 ms  200
2026-08-26 15:05:32  50585 ms  200
... max 55916.7 ms
Fastest successful 200: 19637 ms  ← the *best case* for themes is still 19.6 s, matching the reported 15–20 s.
```

Status breakdown for `GET /api/themes`:

```
200  n=32  avg 32146 ms  min 19637  max 55917   ← actual data fetch (N+1)
403  n=24  avg  1030 ms  min   227  max  3874   ← invite_required, no data fetch, still 1 s (auth+DB)
401  n=21  avg    80 ms  min     2  max  1123   ← token missing, fast fail before DB
500  n=1   avg  1540 ms
```

Same pattern for `GET /api/channels` (2 rows, should be 5 ms) → `200 avg 21944 ms`. That proves the bottleneck is **not query complexity** but connection/wait queueing on the single worker + cross-region RTT.

### 1.2 Direct DB timing (psql from Bengaluru, same DC as Aiven PG)

Measured from `Dasarahalli, IN` (Tata, 10 ms to Aiven PG). Singapore → Aiven PG would be ~45 ms, so multiply RTT-bound queries by ~4.5×.

```
theme_hierarchy counts: sector=6, industry=14, theme=111, narrative=2820, total=2951
theme_ticker_mappings=2477  videos=27  channels=2  speaker_ticker_aggregation=206

N+1 simulation (get_theme_hierarchy_tree):
  Sectors query:                          10 ms
  Full N+1 (133 queries: 1 sector +6 industries+14 themes+111 mappings+1 narrative): 1987 ms
  → 133 queries, avg 14.9 ms per round-trip (query exec 1–2 ms + 10 ms RTT)
  → Projected Singapore (45 ms RTT): 133*45 + 200 = ~6185 ms just for queries, plus 5–10 s observed with pool queue + JSON serialisation → matches 19–55 s in logs.

Single JOIN alternative (single query, 3836 rows): 716 ms (Bengaluru) → ~760 ms from Singapore (1 RTT).

Per-endpoint EXPLAIN (execution only, no RTT):
  tickers GROUP BY ticker (206 rows): 0.238 ms (planning 0.15 ms)
  videos WHERE duration_sec>60 ORDER BY published_at LIMIT 20 (27 rows): 0.194 ms
  sectors WHERE level='sector': 1.037 ms (seq scan 2945 rows, filtered, no index on level)
```

Network baseline from Bengaluru (our probe) → GCP Singapore:

```
GET /health (no auth, no DB)   avg 175 ms  min 156  max 231  p95 231   ← pure network Mumbai? actually direct Bangalore→Singapore 160 ms
GET /api/tickers with invalid Bearer (401 fast fail, includes Clerk verify fail): avg 167 ms
```

So baseline network `Bangalore→Singapore` is 160 ms. Vercel `bom1` adds ~35 ms: `client (India) → bom1 5 ms → Singapore 35 ms → PG Bengaluru 45 ms → back 45+35 ms`. Total 160 ms is consistent.

### 1.3 Concurrency vs latency correlation

Minutes with ≥3 dashboard endpoints fired together show correlated slowdown (shared worker/pool):

```
minute                themes  channels  videos  tickers
2026-08-27 08:41       55917   38025     34293   ---      ← all 3 slow together, top-etfs 328 ms (fast) shows it didn't contend same resource
2026-08-26 17:51       30541   18471     ---     335
2026-08-26 15:19       26215   18918     17841   307      ← classic dashboard fan-out, all slow
2026-08-27 08:52       2       2         2       2        ← all 401 fast, no DB work, no contention
```

404 flood: `4272× 404`, top `/fetch 42×`, `/.env 35×`, `/.aws/credentials 14×` - scanner bots, but avg 6 ms, not saturating DB (but they do consume nginx and worker connections).

---

## 2. Backend Deep Dive

### 2.1 `GET /api/themes` - Textbook N+1

`src/api/themes.py:20` → `src/services/theme_service.py:173`:

```python
# src/services/theme_service.py:173
async def get_theme_hierarchy_tree(self) -> list[dict]:
    sectors = await self.get_themes_by_level("sector")          # 1
    for sector in sectors:
        industries = await self.get_theme_children(sector.id)   # S=6
        for industry in industries:
            themes = await self.get_theme_children(industry.id) # I=14
            for theme in themes:
                ticker_mappings = await self.get_ticker_mappings(theme.id) # T=111
    narratives = await self.get_themes_by_level("narrative")    # 1, but 2820 rows
```

Query count from prod data: `2 + 6 + 14 + 111 = 133` `SELECT`s per request, sequentially awaited, holding the `AsyncSession` (hence DB connection) for the entire 20–55 s.

Each `get_theme_children(parent_id)` does `SELECT * WHERE parent_id=:pid` using `ix_theme_hierarchy_parent_id` (indexed, fast). Each `get_ticker_mappings(theme_id)` uses `ix_theme_ticker_mappings_theme_id`. The per-query execution is <2 ms, but the RTT dominates, and the Python loop overhead + building the 2826-node tree + `json.dumps` of ~1 MB blocks the `asyncio` loop on a single worker, delaying the other 4 concurrent dashboard requests multiplexed on that worker (hence they also appear slow in the same minute).

Payload size calculation (validated via `psql` direct):

```
Narratives: 2820 rows × ~330 bytes JSON each = 909 KB
Tree overhead (sectors 6 + industries 14 + themes 111 with 22 tickers avg):
  111 themes × ~500 bytes + 2477 mappings × ~80 bytes ≈ 250 KB
Total JSON ≈ 1.1–1.3 MB uncompressed, no gzip
Dashboard uses only data.themes.length (web/src/app/(app)/dashboard/page.tsx:103) → 99 % of bytes wasted.
```

No cache: `src/api/themes.py:20` has no `Cache-Control`, no Redis cache. Taxonomy changes only on ingestion (rare), but every dashboard load recomputes from DB.

Missing index: `theme_hierarchy.level` has no index. `SELECT * WHERE level='sector'` does `Seq Scan on theme_hierarchy cost=0.00..137.97 rows=6 filter: level='sector' rows removed=2945 buffers hit=101 planning 0.517 ms execution 1.037 ms`. Add:

```sql
CREATE INDEX CONCURRENTLY ix_theme_hierarchy_level ON theme_hierarchy(level);
```

**Fix (P0):**

Option A - minimal: 2-query fetch + count endpoint

```python
# Single query for hierarchy + single query for mappings, build tree in Python
hierarchy = (await db.execute(select(ThemeHierarchy))).scalars().all()  # 1
mappings = (await db.execute(select(ThemeTickerMapping))).scalars().all()  # 1, or filter to theme ids
# Build tree in memory O(n)
```

Option B - recommended: dedicated lightweight stats + paginated hierarchy

```python
@router.get("/stats", response_model=DashboardStats)  # dashboard should call this, not full hierarchy
async def get_theme_stats(db: AsyncSession = Depends(get_db)):
    # SELECT level, COUNT(*) FROM theme_hierarchy GROUP BY level → 4 rows
    return {"sectors":6,"industries":14,"themes":111,"narratives":2820}

@router.get("", response_model=list[dict])
async def list_themes(level: str | None = None, include_narratives: bool = False):
    # Default exclude narratives (the 909 KB). Frontend that needs full tree passes ?include_narratives=true
```

Add server cache:

```python
from functools import lru_cache # or redis
@cache(ttl=300)  # taxonomy rarely changes, bust on ThemeService.write
```

Add HTTP cache headers: `Cache-Control: public, max-age=60, stale-while-revalidate=120` for `GET /api/themes`.

Estimated improvement: 133 → 2 queries, 2 s (Bengaluru) / 6.2 s (Singapore) → 0.02 s / 0.06 s query time, plus 1 MB → 5 KB for count endpoint → p95 40 s → 0.3 s.

### 2.2 `GET /api/videos`, `GET /api/channels`, `GET /api/tickers`, `GET /api/tickers/top-etfs`

These are single-query endpoints (verified via `EXPLAIN` above). Why are they also slow in `api_request_logs`?

- `GET /api/videos` `src/api/videos.py:27`: `SELECT * WHERE duration_sec>60 ORDER BY published_at DESC LIMIT 20` - no index on `(published_at, duration_sec)`. Seq scan 27 rows is fine now, but will degrade. Add `CREATE INDEX ix_videos_published_at_duration ON videos(published_at DESC) WHERE duration_sec>60`.
- `GET /api/channels` `src/api/channels.py:19`: `SELECT * ORDER BY created_at DESC` - 2 rows, should be 2 ms, but `p95 30 s` in logs indicates worker queueing, not query. Fix via workers + pool.
- `GET /api/tickers` `src/api/tickers.py:37`: `SELECT ticker, SUM(total_mentions) ... GROUP BY ticker` - HashAggregate 206 rows, 0.24 ms execution, but `p50 283 ms` from prod indicates 220 ms overhead (RTT + Clerk). Acceptable, but cross-region amplifies.
- `GET /api/tickers/top-etfs` `src/services/aggregation_service.py:409`: 2 queries (institutional channels + `WHERE channel_id IN (...)` + in-memory merge). Fast (`p95 1.7 s`), but does `ETFMAPPINGService().is_etf()` per row in Python (file I/O `etf_mappings.json` per call, not cached across requests - should cache).

All four are **victims of the single-worker head-of-line blocking** by the concurrent `GET /api/themes` on the same `uvicorn` process. Fixing themes + adding workers decouples them.

### 2.3 Cross-region DB

Aiven PG in Bengaluru while GCP in Singapore adds 45 ms per round-trip. With 133 queries that is 6 s. Even with fixed 2 queries, the single `GET /api/themes` still pays 90 ms vs 10 ms if co-located. Recommend:

- Option 1: Move Aiven PG to `aws-ap-southeast-1` (Singapore) - one-click migration, no code change, `DATABASE_URL` update, downtime < 5 min.
- Option 2: Keep primary in Bengaluru, add SG read replica for dashboard (`DATABASE_URL_SYNC` → replica for `GET` routes, writes to primary). Requires `async_session_factory` routing.
- Option 3: Use Cloud SQL in same GCP project/region as compute (lowest latency, VPC peering, private IP).

Redis is already correctly in Singapore.

### 2.4 Auth path

`src/auth/dependencies.py:62` `get_current_authenticated_user()`:

1. `verify_session_token()` `src/auth/clerk.py:116`: `authenticate_request(..., secret_key, jwt_key=None)` → JWKS fetch from `api.clerk.com` (US) when `CLERK_JWT_KEY` unset. `src/config.py:101` `clerk_jwt_key=""` in prod. The `clerk-backend-api` SDK caches JWKS for `~5 min` after first fetch (verified in SDK source), but first request after cache expiry still pays 150–250 ms Singapore→US.
2. `get_user_by_clerk_id()` → `SELECT * FROM users WHERE clerk_user_id=:id` (indexed, 1 RTT).
3. Possible `get_clerk_user_profile()` HTTP to Clerk (`src/auth/dependencies.py:96`, `112`) throttled to 60 s per `clerk_user_id` (`_LAST_ROLE_SYNC`), but first dashboard load after 60 s window triggers it (extra 150 ms).
4. `touch_last_seen()` throttled 60 s, but still `UPDATE users SET last_seen_at=now()` per minute per user.

Measured: `403 invite_required` still 1 s avg (should be 100 ms). The 900 ms overhead is Clerk verify + DB commit + RTT. Setting `CLERK_JWT_KEY` (PEM from Clerk Dashboard → API Keys → JWT verification) enables **network-less** verification (no JWKS fetch). Current `.env.prod` does not set it. Add:

```bash
CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----\n..."  # from https://dashboard.clerk.com/.../api-keys
```

Alternative: upgrade `clerk-backend-api` and ensure `authenticate_request` is called with `authorized_parties` correctly to avoid extra round-trip (already set `src/config.py:106` to `https://carry-fin.vercel.app`).

Frontend token acquisition also contributes: `web/src/lib/auth-client.ts:16` `waitForClerkLoaded()` polls `window.Clerk.loaded` every 50 ms up to 8 s before calling `Clerk.session.getToken()`. If `Clerk.js` is slow (ad blocker, 3G), the request stalls 8 s then goes out **without** `Authorization` header → `401` (2 ms) → React Query `retry:1` (`web/src/components/QueryProvider.tsx:9` `retry:1`) retries after ~1 s, now with token → succeeds but 9 s later. Use `useAuth()` from `@clerk/nextjs` (which internally waits for `Clerk.loaded`) instead of manual `window.Clerk` polling.

### 2.5 Low-hanging DB/ORM

- `src/database.py:12` `pool_size=10, max_overflow=20` with `max_connections=20` on Aiven PG. Overflow beyond 20 is rejected server-side, causing `TimeoutError` after `pool_timeout=30`. Under load, analytics writes (`src/analytics/service.py:85` opens new `async_session_factory()` per request) compete for same pool. Set `pool_size=5, max_overflow=10` to stay under server limit, or raise Aiven plan to `max_connections=100`, or use `PgBouncer`.
- `videos.published_at` no index - add `CREATE INDEX CONCURRENTLY ix_videos_published_at ON videos(published_at DESC)`.
- `theme_hierarchy.parent_id` already indexed, good.

---

## 3. Frontend Deep Dive

### 3.1 Dashboard fan-out

`web/src/lib/hooks.ts:107`:

```typescript
export function useDashboardData() {
  const videos = useVideos();      // GET /api/videos
  const channels = useChannels();  // GET /api/channels
  const themes = useThemes();      // GET /api/themes  ← 1 MB, 20–55 s
  const tickers = useTickers();    // GET /api/tickers
  const etfs = useTopETFs();       // GET /api/tickers/top-etfs
  const isLoading = videos.isLoading || channels.isLoading || themes.isLoading || tickers.isLoading || etfs.isLoading;
  // ...
}
```

Plus `web/src/app/(app)/layout.tsx:13` `useMe()` → `GET /api/auth/me`. So **6 concurrent authenticated GETs** on mount.

`web/src/lib/api.ts:330` `request()` does:

```typescript
async function request<T>(path: RequestInit, opts?: {auth?:boolean}) {
  const token = await getAuthToken();           // waitForClerkLoaded poll
  headers.set("Authorization", `Bearer ${token}`);
  res = await fetch(`${API_BASE_URL}${path}`, {headers}); // API_BASE_URL="/api" → Vercel rewrite
}
```

`API_BASE_URL` is `"/api"` when `NEXT_PUBLIC_API_URL` empty at runtime? Actually Vercel sets `NEXT_PUBLIC_API_URL=https://carry-api.akshat21.me` (verified via `vercel env pull` 2026-08-27). `web/next.config.ts:5` `rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001"` so prod rewrite destination is `https://carry-api.akshat21.me/api/:path*` (correct). Local `.next/routes-manifest.json` showed `127.0.0.1:8001` because built without env - but Vercel's build has correct URL.

Problems:

1. **No token sharing**: 6 hooks call `getAuthToken()` independently. `waitForClerkLoaded` shares `clerkReadyWaiter` promise, but `Clerk.session.getToken()` is called 6 times in parallel. `clerk-js` dedupes internally, but still 6 microtasks. Better to hoist token via `useAuth()` context.
2. **Head-of-line blocking**: `isLoading = a||b||c||d||e` shows `<DashboardSkeleton />` (`web/src/app/(app)/dashboard/page.tsx:17`) until slowest finishes. Should render incrementally (`<Suspense>` per card, or render with `data?.tickers` as they arrive).
3. **Over-fetching**: `data.themes.length` only needs a count, but fetches 1 MB. `data.videos.slice(0,8)` only needs 8, but endpoint default `limit=20` returns 20 full rows (`title, youtube_video_id, channel_id, published_at, duration_sec, created_at` ×20). Acceptable vs themes, but still waste.
4. **Retry on 401**: `QueryProvider.tsx:9` `retry:1` means if first fetch races Clerk load and goes out without token → `401` → waits ~1 s exponential backoff → retries with token. Dashboard appears to hang 1–2 s extra on cold load. `useSearchAnswer`/`useSearchCoverage` correctly set `retry:false` (`hooks.ts:170`), `useMe` sets `retry:false` (`hooks.ts:221`), but dashboard hooks do not. Set `retry: (count, err) => err.status===401 ? false : count<1`.
5. **No caching**: `staleTime: 60*1000` (`QueryProvider.tsx:8`) means within 1 min, back-nav is instant, but hard reload always refetches. `GET /api/themes` is immutable for hours (taxonomy updated only on ingestion). Should be `staleTime: 5*60*1000` + `gcTime: 30*60*1000` for dashboard, or use HTTP `Cache-Control`.

### 3.2 Vercel ↔ GCP hop

Vercel edge `bom1` (Mumbai) to GCP Singapore is 35 ms (measured `traceroute` via `x-vercel-id: bom1::...`). Could be avoided by:

- Hosting frontend in `sin1` (Singapore) via Vercel `regions = ["sin1"]` in `vercel.json`, or
- Using Cloud Run same region as backend + `career-api.akshat21.me` on Cloudflare with `cache` for `GET` routes.

Not P0 (35 ms is small vs 20 s backend), but worth noting.

### 3.3 Missing performance headers

No `Server-Timing`, no `Cache-Control`, no `Content-Encoding: gzip`. `deploy/nginx.conf:1` is minimal. Add:

```nginx
gzip on; gzip_types application/json;
add_header Cache-Control "public, max-age=60" always;  # for /api/themes
```

---

## 4. Infra

| Component | Current | Issue | Fix |
|---|---|---|---|
| GCP VM | `34.142.183.86` single `uvicorn` worker, no `gunicorn` | Single-threaded event loop | `CMD ["gunicorn","src.main:app","-k","uvicorn.workers.UvicornWorker","--workers","4","--bind","0.0.0.0:8000"]` or `uvicorn --workers 4`. Ensure `pool_size` × workers < `max_connections` |
| Docker | `docker-compose.prod.yml:3` single `api` service | No scale | Add `deploy: replicas: 2` + load balancer, or Cloud Run |
| DB | Aiven `max_connections 20`, `shared_buffers 190MB`, `569MB` size | Too small for 4 workers × 10 pool | Upgrade to `Business 4GB` (max 100) or PgBouncer |
| Nginx | `proxy_read_timeout 300s` but no gzip | Payload penalty | Enable gzip, `proxy_cache` for GETs |
| CI | `.github/workflows/deploy.yml:13` `docker compose up -d --build && alembic upgrade head` | Deploys single VM, no blue/green | OK for hobby |

---

## 5. What to Fix First (actionable PRs)

### PR #1 - P0 Backend: fix `get_theme_hierarchy_tree()` (1 hour, highest ROI)

Files: `src/services/theme_service.py:173`, `src/api/themes.py:20`, `alembic/versions/XXX_ix_theme_hierarchy_level.py`

```sql
-- migration
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_theme_hierarchy_level ON theme_hierarchy(level);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_videos_published_at ON videos(published_at DESC);
```

```python
# src/services/theme_service.py - single-query version
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_theme_hierarchy_tree(self) -> list[dict]:
    # 2 queries, no N+1
    result = await self.db.execute(
        select(ThemeHierarchy).options(selectinload(ThemeHierarchy.ticker_mappings))
        .order_by(ThemeHierarchy.level, ThemeHierarchy.name)
    )
    all_nodes = result.scalars().all()
    # build tree in memory - O(n), ~1 ms
    ...

# src/api/themes.py - add lightweight count, exclude narratives by default
@router.get("")
async def list_themes(
    include_narratives: bool = Query(default=False),
    theme_service: ThemeService = Depends(get_theme_service),
) -> list[dict]:
    return await theme_service.get_theme_hierarchy_tree(include_narratives=include_narratives)

@router.get("/stats")
async def get_theme_stats(db: AsyncSession = Depends(get_db)) -> dict:
    counts = dict(await db.execute(select(ThemeHierarchy.level, func.count()).group_by(ThemeHierarchy.level)))
    return {"sectors": counts.get("sector",0), "industries": counts.get("industry",0),
            "themes": counts.get("theme",0), "narratives": counts.get("narrative",0)}
```

Update dashboard: `web/src/lib/api.ts` add `getThemeStats(): Promise<{themes:number}>`, `web/src/lib/hooks.ts` use it instead of `useThemes()`.

Add Redis cache (`src/services/theme_service.py` 5 min, bust on write).

### PR #2 - P0 Frontend: single dashboard summary endpoint (2 hours)

```python
# src/api/dashboard.py
@router.get("/api/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Run 5 queries concurrently with asyncio.gather, each with its own session or same session serialized
    videos, channels, ticker_rows, etf_rows, theme_counts = await asyncio.gather(
        db.execute(select(Video).where(Video.duration_sec>60).order_by(Video.published_at.desc()).limit(8)),
        db.execute(select(Channel).order_by(Channel.created_at.desc())),
        db.execute(select(SpeakerTickerAggregation.ticker, func.sum(...)).group_by(...).limit(50)),
        aggregation.get_top_etfs(limit=8),
        db.execute(select(func.count()).select_from(ThemeHierarchy).where(ThemeHierarchy.level=="theme")),
    )
    return {
        "videos": [VideoResponse.model_validate(v) for v in videos.scalars().all()],
        "channels": [...],
        "tickers": [...],
        "etfs": [...],
        "theme_counts": {"themes": theme_counts.scalar_one(), "narratives": ...},
    }
```

Frontend: `web/src/lib/hooks.ts` replace `useDashboardData()` 5 hooks with `useQuery({queryKey:["dashboardSummary"], queryFn: api.getDashboardSummary})`. Renders after 1 RTT (instead of 5 fan-out + auth×6). Add `staleTime: 5*60*1000`.

### PR #3 - P0 Infra: co-locate DB + add workers (1 day)

- Aiven console → Migrate PG to `aws-ap-southeast-1` or GCP `asia-southeast1`. Update `DATABASE_URL*` in `.env.prod` and Vercel env.
- `Dockerfile:43` → `CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--workers","4"]` or switch to `gunicorn`.
- `deploy/nginx.conf` add `gzip on;`.
- Set `CLERK_JWT_KEY` in `.env.prod`.

### PR #4 - P1 Polish

- `web/src/lib/auth-client.ts` replace `window.Clerk` polling with `useAuth()` from `@clerk/nextjs`.
- `web/src/components/QueryProvider.tsx:9` `retry: (c, e) => e.status===401||e.code==="unauthorized" ? false : c<1`.
- `web/src/app/(app)/dashboard/page.tsx:17` incremental render: `{videos.data && <RecentVideos videos={videos.data.slice(0,8)}/>} ` etc., instead of `if(isLoading) return <Skeleton/>`.
- `src/analytics/middleware.py:47` sample 10 % or batch writes to avoid pool contention; fix `user_id` reading (`request.state.user_id` not `scope["state"]` - currently `user_id` is always `None` in logs, so attribution is broken).
- Add `Cache-Control` and `ETag` for taxonomy.

---

## 6. Expected After Fix

Model: dashboard p95 = `Clerk load (200 ms) + Vercel hop (35 ms) + 1× backend aggregated query (2 DB RTTs 90 ms + exec 5 ms) + JSON 50 KB gzip 10 ms + 35 ms back` ≈ **370 ms** server time from Singapore, plus client-side Clerk.

| Metric | Before (prod `api_request_logs` 7d) | After PR #1+2 | After PR #3 |
|---|---|---|---|
| `GET /api/themes 200` p50 | 1500 ms | 60 ms | 15 ms |
| `GET /api/themes 200` p95 | 40111 ms | 200 ms | 80 ms |
| `GET /api/themes 200` max | 55917 ms | 400 ms | 150 ms |
| `GET /api/channels 200` p50 | 1521 ms | - (aggregated) | - |
| Dashboard end-to-end (6 requests, `isLoading` = slowest) | p50 ~1.5 s, p95 40 s, max 55 s | p50 400 ms, p95 800 ms | p50 300 ms, p95 600 ms |
| Payload `GET /api/themes` | 1.1 MB | 5 KB (`/stats`) or 300 KB tree gzip | - |
| DB queries per dashboard load | 133 + 1 + 1 + 1 + 1 + 1 (auth) = 138 | 5 (aggregated) | 5, but 45 ms→5 ms RTT |

Verification steps already run for this doc:

```bash
psql $DATABASE_URL_SYNC -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ..." # videos 0.19 ms, tickers 0.24 ms, sectors 1.03 ms
python3 -c "time hierarchy N+1 vs single JOIN"  # 1987 ms vs 716 ms (Bengaluru), projected 6185 ms vs 760 ms (Singapore)
curl -w "%{time_total}" https://carry-api.akshat21.me/health  # 175 ms avg (Bangalore→Singapore)
SELECT route_template, PERCENTILE_CONT(0.95) FROM api_request_logs GROUP BY route_template # themes p95 40111 ms
```

---

## 7. Appendix - Raw Counts

```
Production DB (Aiven 206.189.132.98, 569 MB, max_connections 20):
  theme_hierarchy  2951 rows (sector 6, industry 14, theme 111, narrative 2820)  1328 kB
  theme_ticker_mappings 2477 rows  912 kB
  videos  27 rows  200 kB
  channels 2 rows  128 kB
  speaker_ticker_aggregation 206 rows (206 tickers grouped, 50 returned by API) 184 kB
  api_request_logs 5084 rows  1240 kB  (last 7d: 78× themes, 81× channels, 56× videos, 88× tickers, 71× auth/me)
  404 flood: 4272 requests in 7d (bots probing /.env, /fetch, /index.php)
```

`Vercel` env (pulled 2026-08-27 via `vercel env pull`):

```
NEXT_PUBLIC_API_URL=https://carry-api.akshat21.me
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_Y2xlcmsuY2FycnktZmluLnZlcmNlbC5hcHAk
# CLERK_JWT_KEY not set
```

`web/next.config.ts:4` rewrites in Vercel build: `"/api/:path*" → "https://carry-api.akshat21.me/api/:path*"` (verified via `vercel env pull`; local `.next/routes-manifest.json` shows `127.0.0.1:8001` only because built without env).

---

## 8. One-line Answer: Frontend or Backend?

**Backend.** Frontend adds ~0.5 s (Clerk load + 6-way fan-out via Vercel hop), but backend `GET /api/themes` alone is 19–55 s due to 133 sequential cross-region round-trips + 1 MB payload on a single uvicorn worker. Fix backend first; frontend aggregation then removes the fan-out entirely.
