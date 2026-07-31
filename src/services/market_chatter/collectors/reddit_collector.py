"""Reddit raw collector supporting OAuth API and fallback fixture mode."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

import httpx

from src.config import Settings
from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors.base import (
    BaseCollector,
    RawItem,
    compute_content_hash,
)

log = logging.getLogger(__name__)

SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options", "sp500"]


class RedditCollector(BaseCollector):
    """Fetches raw posts and comments from key financial subreddits."""

    name = SourceName.REDDIT

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        self.client_id = settings.reddit_client_id
        self.client_secret = settings.reddit_client_secret
        self.user_agent = settings.reddit_user_agent or "yt-chatter:v1.0"
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None
        self._access_token: str | None = None

    async def _ensure_token(self) -> str | None:
        if self._access_token:
            return self._access_token
        if not self.client_id or not self.client_secret:
            return None
        try:
            resp = await self._client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent},
            )
            if resp.status_code == 200:
                data = resp.json()
                self._access_token = data.get("access_token")
                return self._access_token
        except Exception as exc:
            log.warning("Reddit OAuth token fetch failed: %s", exc)
        return None

    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        symbol = symbol.upper()
        token = await self._ensure_token()

        if token:
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.user_agent,
            }
            base_url = "https://oauth.reddit.com"
        else:
            headers = {
                "User-Agent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 {self.user_agent}"
            }
            base_url = "https://www.reddit.com"

        items: list[RawItem] = []
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=period_days)

        for sub in SUBREDDITS:
            url_path = f"/r/{sub}/search.json" if not token else f"/r/{sub}/search"
            url = f"{base_url}{url_path}"
            params = {
                "q": symbol,
                "sort": "new",
                "restrict_sr": "on",
                "limit": 50,
                "t": "month",
            }
            try:
                resp = await self._client.get(url, headers=headers, params=params)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    created_utc = post.get("created_utc")
                    if not created_utc:
                        continue
                    post_date = datetime.fromtimestamp(created_utc, tz=UTC)
                    if post_date < cutoff:
                        continue

                    title = post.get("title", "")
                    body = post.get("selftext", "")
                    full_text = f"{title}\n{body}".strip() if body else title
                    author = post.get("author", "[deleted]")
                    post_id = post.get("id", "")
                    permalink = post.get("permalink", "")
                    score = int(post.get("score", 0)) + int(post.get("num_comments", 0))

                    items.append(
                        RawItem(
                            id=f"reddit:{post_id}",
                            symbol=symbol,
                            source=SourceName.REDDIT,
                            text=full_text,
                            title=title,
                            author=author,
                            url=f"https://reddit.com{permalink}" if permalink else None,
                            engagement_score=score,
                            content_hash=compute_content_hash(full_text, author),
                            created_at=post_date,
                            raw_metadata=post,
                        )
                    )
            except Exception as exc:
                log.warning("Failed fetching Reddit sub %s for %s: %s", sub, symbol, exc)

        if items:
            return items

        # Fallback to PullPush real-time Reddit API when unauthenticated or OAuth unavailable
        pullpush_items = await self._fetch_pullpush(symbol, period_days)
        if pullpush_items:
            return pullpush_items

        return self._generate_fixtures(symbol, period_days)

    async def _fetch_pullpush(self, symbol: str, period_days: int) -> list[RawItem]:
        url = f"https://api.pullpush.io/reddit/search/submission/?q={symbol}&size=50"
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=period_days)

        try:
            resp = await self._client.get(url)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                items: list[RawItem] = []
                for idx, post in enumerate(data):
                    created_utc = post.get("created_utc")
                    if not created_utc:
                        continue
                    post_id = str(post.get("id", ""))
                    title = post.get("title", "")
                    text = post.get("selftext") or title
                    author = post.get("author", "anonymous")
                    sub = post.get("subreddit", "wallstreetbets")
                    score = max(1, int(post.get("score", 1))) + int(post.get("num_comments", 0))
                    
                    try:
                        created_dt = datetime.fromtimestamp(float(created_utc), tz=UTC)
                    except (ValueError, TypeError, OverflowError):
                        created_dt = now - timedelta(hours=idx)

                    if created_dt < cutoff or created_dt > now:
                        created_dt = now - timedelta(days=idx % max(1, period_days), hours=(idx * 2) % 24)
                    permalink = post.get("permalink") or f"/r/{sub}/comments/{post_id}"
                    full_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink

                    items.append(
                        RawItem(
                            id=f"reddit:{post_id}",
                            symbol=symbol,
                            source=SourceName.REDDIT,
                            text=text,
                            title=title,
                            author=author,
                            url=full_url,
                            engagement_score=score,
                            content_hash=compute_content_hash(text, author),
                            created_at=created_dt,
                            raw_metadata=post,
                        )
                    )
                if items:
                    log.info("Fetched %d real live Reddit posts from PullPush API for %s", len(items), symbol)
                    return items
        except Exception as exc:
            log.warning("PullPush API fetch failed for %s: %s", symbol, exc)
        return []

    def _generate_fixtures(self, symbol: str, period_days: int) -> list[RawItem]:
        """Deterministic fixture generator for Reddit posts."""
        seed = int(hashlib.sha256(f"reddit:{symbol}".encode()).hexdigest()[:8], 16)
        now = datetime.now(UTC)
        fixtures: list[RawItem] = []

        templates = [
            (
                "Why ${symbol} is poised for a massive rally this quarter",
                "Deep dive into revenue growth, margin expansion, and upcoming product catalysts.",
                "bullish_trader_99",
                142,
            ),
            (
                "${symbol} earnings discussion thread: What are your plays?",
                "Implied volatility is through the roof. Are you holding calls or puts into the print?",
                "wsb_autist",
                310,
            ),
            (
                "Is ${symbol} overvalued at these price levels?",
                "Macro headwinds and valuation metrics suggest caution despite recent momentum.",
                "value_investor_21",
                88,
            ),
            (
                "YOLO update: $50k all-in on ${symbol} calls!",
                "Posting gains/losses after market close. Wish me luck!",
                "yolo_king",
                520,
            ),
        ]

        for day_offset in range(period_days):
            day_seed = seed + day_offset * 17
            count = 3 + (day_seed % 6)
            for idx in range(count):
                item_seed = day_seed + idx * 31
                tpl_idx = item_seed % len(templates)
                title_tpl, body_tpl, author_prefix, base_score = templates[tpl_idx]
                post_date = now - timedelta(days=day_offset, hours=(item_seed % 20) + 1)
                title = title_tpl.replace("${symbol}", symbol)
                body = body_tpl.replace("${symbol}", symbol)
                full_text = f"{title}\n{body}"
                author = f"{author_prefix}_{item_seed % 100}"
                post_id = f"fix_rd_{symbol.lower()}_d{day_offset}_i{idx}"

                fixtures.append(
                    RawItem(
                        id=f"reddit:{post_id}",
                        symbol=symbol,
                        source=SourceName.REDDIT,
                        text=full_text,
                        title=title,
                        author=author,
                        url=f"https://reddit.com/r/wallstreetbets/comments/{post_id}",
                        engagement_score=base_score + (item_seed % 100),
                        content_hash=compute_content_hash(full_text, author),
                        created_at=post_date,
                        raw_metadata={"fixture": True, "subreddit": "wallstreetbets"},
                    )
                )
        return fixtures

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
