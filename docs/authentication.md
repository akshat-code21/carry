# Authentication & Usage Analytics

This app uses [Clerk](https://clerk.com) for authentication (email+password,
Google OAuth, magic link) with an **invite-only signup gate**, and tracks all
usage metrics in its own Postgres database.

```
Browser ──(short-lived session JWT, ~60s, auto-refreshed)──► FastAPI
                                                              │ clerk-backend-api
                                                              │ verifies RS256 locally
                                                              ▼
                                                    users / invites tables
                                                    usage_events / api_request_logs
                                                    llm_usage_logs / daily rollups
```

---

## 1. One-time Clerk setup

1. Create an application at <https://dashboard.clerk.com>.
2. In **Configure → Sign-in options**, enable:
   - Email address (+ password)
   - Google OAuth (Clerk's shared dev credentials work immediately; add your
     own Google Cloud OAuth client before production)
   - Email verification code / magic link
3. Collect keys from **API Keys**:

| Key | Where it goes | Notes |
|---|---|---|
| Publishable key (`pk_test_…`) | `web/.env.local` → `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | frontend |
| Secret key (`sk_test_…`) | `.env` → `CLERK_SECRET_KEY` | backend |
| JWT public key (PEM) | `.env` → `CLERK_JWT_KEY` | **optional** — enables networkless verification, but goes stale whenever Clerk rotates its signing key (e.g. after editing the session token template). The backend auto-falls back to JWKS on signature failure; if you see `CLERK_JWT_KEY failed to verify` warnings, just delete this variable. |
| — | `.env` → `CLERK_AUTHORIZED_PARTIES` | comma-separated frontend origins; set real origins in prod (CSRF protection) |

> **Gotcha:** editing *Configure → Sessions → Customize session token* rotates
> Clerk's signing keys. A previously-pasted `CLERK_JWT_KEY` will then fail with
> `token_invalid_signature` on fresh tokens. Delete `CLERK_JWT_KEY` (JWKS
> mode is rotation-safe) or re-copy the new PEM.

4. Frontend env (`web/.env.local`, see `web/.env.example`):
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
   NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
   ```

## 2. How access works

1. User signs in/up through Clerk (`/sign-in`, `/sign-up`) — any enabled method.
2. The Next.js proxy (`web/src/proxy.ts`) protects all pages except `/`,
   `/sign-in/**`, `/sign-up/**`.
3. Every API call attaches `Authorization: Bearer <session token>`
   (see `web/src/lib/api.ts`). FastAPI verifies it via
   `src/auth/clerk.py` and JIT-provisions a row in our `users` table.
4. New accounts start as **regular users** with `status=pending_invite`
   (unless listed in `ADMIN_CLERK_USER_IDS`, or the app runs in development).
   The UI shows the **invite gate** until they redeem a code.
5. Invites grant regular-user access only — they can never promote anyone.
   Admins are promoted manually via Clerk public metadata (see below).

### Making someone an admin (via Clerk Dashboard)

Admin status is owned by Clerk and synced into the app automatically — no
session-token template or backend restart needed:

1. Open <https://dashboard.clerk.com> → **Users** → click the person.
2. Scroll to **Metadata** → **Public metadata** → Edit, and set:
   ```json
   { "role": "admin" }
   ```
3. Save. Within ~60s (throttled re-sync) the app picks it up: they see
   **Usage** + **Admin** in the sidebar and can trigger pipelines.
   To demote, remove `"role"` from their public metadata.

*Optional optimisation:* adding a customised session token
(**Configure → Sessions → Customize session token** →
`{"role": "{{user.public_metadata.role}}"}`) puts the role directly into the
JWT, avoiding a per-minute Backend API lookup. Note that editing the session
token rotates Clerk's signing keys — if you use a static `CLERK_JWT_KEY`,
delete it afterwards (the backend auto-falls back to JWKS).

Bootstrap alternative (no dashboard): add the person's Clerk user id to
`ADMIN_CLERK_USER_IDS` in `.env`, or run
`make promote-admin email=you@example.com`.

### Troubleshooting

| Log line | Meaning | Fix |
|---|---|---|
| `jwk_kid_mismatch` + `Rejected token header: kid=ins_XXX` | token signed by a **different Clerk instance**. The Clerk Python SDK silently falls back to the browser's `__session` cookie when no `Authorization` header is present — a cookie left over from a previously-used instance fails verification. The backend now **requires the Bearer header** (cookie fallback disabled), so this only appears for genuinely stale browser sessions. | sign out, clear the `__session` / `__client` cookies for the app origin (or use an incognito window), sign in again; ensure `web/.env.local` publishable key and backend `CLERK_SECRET_KEY` belong to the same instance |
| `CLERK_JWT_KEY failed to verify … falling back to JWKS` | static PEM is stale after a key rotation | delete `CLERK_JWT_KEY` from `.env` and restart |
| `Session token carries no 'role' claim; syncing via Backend API` | info only — role still syncs via public metadata every ~60s | nothing to do (add the session-token template only if you want to skip the API lookup) |
| 503 `clerk_unavailable` | transient Clerk API failure during first-time provisioning | retry the request |

**Two Clerk accounts with the same email** (e.g. one from password provisioning,
one from a later Google sign-in) are linked to a single app account
automatically — usage history stays continuous regardless of sign-in method.
Optionally delete the unused one in Clerk Dashboard → Users.




### Creating invites

```bash
make invite                                   # random single-use code
make invite email=friend@example.com          # bound to one email
make invite max_uses=5                        # multi-use code for a cohort
PYTHONPATH=. uv run python scripts/create_invite.py --expires-in-days 30
```

Or via the **Admin page** (`/admin`) in the app (admins only).
Recovery/bootstrap: `make promote-admin email=you@example.com`.

### Onboarding specific users with pre-made credentials (pilot flow)

For sending the MVP to a known list of people, pre-provision their accounts —
they get ready credentials and skip the invite screen entirely:

1. Create `users.csv` — the optional third column is a **custom password you
   choose** (min 8 chars); leave it off to auto-generate:
   ```csv
   Akshat,akshat@example.com,MySecretPass123
   Jane,jane@example.com
   ```
2. Run:
   ```bash
   make provision-users csv=users.csv out=credentials.csv \
        login-url=https://your-app.vercel.app/sign-in
   ```
3. This **creates verified Clerk accounts** with your chosen (or generated)
   passwords, activates them app-side, and writes `credentials.csv` for you
   to send. If a Clerk user already exists, a provided password **resets**
   it — so you can re-send updated credentials anytime.
4. Each person can either sign in with the emailed password (**preferred**)
   or click **Continue with Google** with the *same* email — the backend
   detects the shared verified email and links both identities into one
   account automatically (`account_linked` event, no duplicate usage stats).
5. Everyone arrives as a regular user. To make one an admin, use the
   Clerk-dashboard steps above.

> Passwords are shown once at generation; Clerk stores only hashes.
> Re-running the script is idempotent — existing Clerk users are reused and
> no new password is generated.


Or via the **Admin page** (`/admin`) in the app (admins only).
Recovery/bootstrap: `make promote-admin email=you@example.com`.

### Going live with external users (production checklist)

1. **Clerk production instance** — create one in the dashboard (dev instances
   are for local testing only). `npx clerk@latest env pull --instance prod`
   or copy keys manually; update `.env` + `web/.env.local`.
2. **Google OAuth** — Configure → SSO Connections → add Google. Dev instances
   share Clerk's dev credentials; production requires your own Google Cloud
   OAuth client (authorized redirect URI shown by Clerk).
3. **Email provider** — production Clerk instances require your own SMTP
   provider (Resend/SES/Postmark) under Configure → Communication.
   Not needed for password logins, but required if anyone uses magic link
   or email verification.
4. **Authorized parties** — set `CLERK_AUTHORIZED_PARTIES` to your real
   frontend origin(s), e.g. `https://carry-fin.vercel.app`.
5. Provision pilot users per the section above, then watch adoption in
   `/admin` (DAU/WAU, searches, feature adoption).

### Authorization model

| Endpoint group | Access |
|---|---|
| `/api/health`, `/`, docs | public |
| `/api/websub/callback` | public (HMAC signature verified instead) |
| Read/browse endpoints (search, videos, tickers, themes, channels, activity, market-chatter) | authenticated active user |
| Usage dashboard (`GET /api/usage/me`), `/usage`, `/admin` pages | **admin only** (hidden in sidebar for regular users) |
| Client event ingest (`POST /api/usage/events`) | all authenticated users (invisible background telemetry) |
| Pipeline triggers (`/api/pipeline/*`), `/api/websub/simulate` | **admin only** |
| `/api/admin/*` (invites, platform metrics, users) | **admin only** |

---

## 3. Usage analytics

All metrics live in the app's Postgres. Raw rows are pruned after
`ANALYTICS_RETENTION_DAYS` (default 180) by a Celery Beat task; daily rollups
are kept forever.

### What is tracked and why

| Signal | Table(s) | Why |
|---|---|---|
| Every API request (method, route template, status, latency, user) | `api_request_logs` | usage counts, error rates, latency monitoring, DAU/WAU/MAU, abuse detection |
| Searches (query, intent, type, result count, zero-result flag, duration) | `usage_events` + rollups | core feature engagement + search-quality signal |
| Entity views (video/channel/theme/ticker detail) | `usage_events` + rollups | which content drives interest |
| Page views per route | `usage_events` (client-sent) | feature adoption funnel |
| Expensive ops (backfill, ingest, process, embeddings, chatter refresh, websub simulate) | `usage_events` + rollups | quota/money attribution to users |
| LLM/embedding calls (provider, model, tokens, duration) incl. failures | `llm_usage_logs` | real cost attribution per user/feature/day |
| Auth lifecycle (signed up, invite redeemed, first-seen/last-seen) | `users`, `usage_events`, `platform_daily_usage.new_users` | invite-conversion + retention analysis |
| Daily per-user counters | `daily_user_usage` | O(days×users) dashboards without raw scans |
| Daily platform counters + exact DAU | `platform_daily_usage` | admin overview |

Deliberately **not** tracked: keystrokes/mouse telemetry, static assets,
health checks, system/Celery pipeline traffic (`source=system`), PII beyond
the Clerk profile (email/name/avatar).

### Endpoints

- `GET /api/usage/me?days=30` — personal dashboard data
- `POST /api/usage/events` — client event ingest (batched)
- `GET /api/admin/metrics/overview?days=30` — platform snapshot
- `POST/GET/DELETE /api/admin/invites` — invite management

### UI

- `/usage` — personal stats, daily activity chart, top queries, recent events
- `/admin` — invites CRUD + platform metrics (visible to admins only)

### Maintenance (Celery Beat)

| Task | Schedule | Purpose |
|---|---|---|
| `analytics.aggregate_platform_daily` | daily 01:00 UTC | exact previous-day platform stats |
| `analytics.retention_cleanup` | daily 03:30 UTC | prune raw rows past retention |

### Env flags

```env
ANALYTICS_ENABLED=true        # master kill-switch
ANALYTICS_RETENTION_DAYS=180  # raw-row retention
ADMIN_CLERK_USER_IDS=         # extra bootstrap admins (comma-separated)
```
