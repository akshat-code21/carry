"""YouTube WebSub (PubSubHubbub) client — free Google hub push notifications."""

from __future__ import annotations

import hashlib
import hmac
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Atom / YouTube feed namespaces
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


@dataclass(frozen=True)
class WebSubEntry:
    """Parsed video entry from a WebSub Atom notification or RSS feed."""

    youtube_video_id: str
    youtube_channel_id: str
    title: str
    published_at: str | None = None
    is_short: bool = False


class WebSubService:
    """Subscribe/renew YouTube channel feeds and parse push notifications.

    Hub: https://pubsubhubbub.appspot.com/ (free, Google-operated)
    Topic: https://www.youtube.com/xml/feeds/videos.xml?channel_id=UC...
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def callback_url(self) -> str:
        base = self.settings.public_base_url.rstrip("/")
        return f"{base}/api/websub/callback"

    @staticmethod
    def topic_url(youtube_channel_id: str) -> str:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={youtube_channel_id}"

    @staticmethod
    def build_atom_notification(
        *,
        youtube_channel_id: str,
        youtube_video_id: str,
        title: str,
        published_at: str | None = None,
    ) -> str:
        """Build a YouTube-style Atom push body for local dry-runs (no real upload)."""
        published = published_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        # Escape minimal XML special chars in title
        safe_title = (
            title.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns="http://www.w3.org/2005/Atom">
  <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
  <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id={youtube_channel_id}"/>
  <title>YouTube video feed</title>
  <updated>{published}</updated>
  <entry>
    <id>yt:video:{youtube_video_id}</id>
    <yt:videoId>{youtube_video_id}</yt:videoId>
    <yt:channelId>{youtube_channel_id}</yt:channelId>
    <title>{safe_title}</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v={youtube_video_id}"/>
    <author>
      <name>Simulate</name>
      <uri>https://www.youtube.com/channel/{youtube_channel_id}</uri>
    </author>
    <published>{published}</published>
    <updated>{published}</updated>
  </entry>
</feed>
"""

    def verify_signature(self, body: bytes, signature_header: str | None) -> bool:
        """Verify X-Hub-Signature (sha1=...) when websub_secret is configured.

        If no secret is configured, verification is skipped (returns True) so
        local dev without a secret still works. Production should set a secret.
        """
        secret = self.settings.websub_secret
        if not secret:
            logger.warning("WEBSUB_SECRET is empty — skipping signature verification")
            return True

        if not signature_header:
            logger.warning("Missing X-Hub-Signature header")
            return False

        # Format: sha1=<hex>
        try:
            algo, provided = signature_header.split("=", 1)
        except ValueError:
            logger.warning("Malformed X-Hub-Signature: %s", signature_header)
            return False

        if algo.lower() != "sha1":
            logger.warning("Unsupported hub signature algorithm: %s", algo)
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha1,
        ).hexdigest()
        return hmac.compare_digest(expected, provided)

    @staticmethod
    def parse_atom_notification(body: bytes | str) -> list[WebSubEntry]:
        """Parse YouTube Atom/RSS push body into video entries."""
        if isinstance(body, bytes):
            text = body.decode("utf-8", errors="replace")
        else:
            text = body

        text = text.strip()
        if not text:
            return []

        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            logger.error("Failed to parse WebSub Atom body: %s", e)
            return []

        # Handle both namespaced and default Atom roots
        entries: list[WebSubEntry] = []

        # Find entry elements regardless of default namespace quirks
        atom_entries = root.findall("atom:entry", _ATOM_NS)
        if not atom_entries:
            # Fallback: any tag ending with 'entry'
            atom_entries = [el for el in root.iter() if el.tag.endswith("entry")]

        for entry in atom_entries:
            video_id = _child_text(
                entry, "videoId", ns_uri="http://www.youtube.com/xml/schemas/2015"
            )
            channel_id = _child_text(
                entry, "channelId", ns_uri="http://www.youtube.com/xml/schemas/2015"
            )
            title = _child_text(entry, "title") or ""
            published = _child_text(entry, "published")

            # Some feeds put video id in <id>tag:youtube.com,2008:video:VIDEO_ID</id>
            if not video_id:
                raw_id = _child_text(entry, "id") or ""
                if "video:" in raw_id:
                    video_id = raw_id.rsplit("video:", 1)[-1].strip()

            if not video_id:
                logger.debug("Skipping Atom entry without video id (title=%s)", title)
                continue

            if not channel_id:
                # Try yt:channelId already handled; also link rel
                channel_id = ""

            is_short = False
            for el in entry.iter():
                if el.tag.endswith("link") or el.tag == "link":
                    href = el.attrib.get("href", "")
                    if "/shorts/" in href:
                        is_short = True
                        break

            entries.append(
                WebSubEntry(
                    youtube_video_id=video_id,
                    youtube_channel_id=channel_id,
                    title=title or video_id,
                    published_at=published,
                    is_short=is_short,
                )
            )

        return entries

    async def subscribe(self, youtube_channel_id: str) -> datetime:
        """Subscribe (or renew) a channel topic. Returns approximate lease expiry."""
        if not self.settings.websub_enabled:
            raise RuntimeError(
                "PUBLIC_BASE_URL is not set — cannot subscribe to WebSub. "
                "Set it to your ngrok/public HTTPS URL."
            )

        lease_seconds = self.settings.websub_lease_seconds
        data = {
            "hub.mode": "subscribe",
            "hub.topic": self.topic_url(youtube_channel_id),
            "hub.callback": self.callback_url,
            "hub.verify": "async",
            "hub.lease_seconds": str(lease_seconds),
        }
        if self.settings.websub_secret:
            data["hub.secret"] = self.settings.websub_secret

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.settings.websub_hub_url, data=data)

        # Hub returns 202/204 on accepted async verify, sometimes 204
        if response.status_code not in (200, 202, 204):
            raise RuntimeError(
                f"WebSub subscribe failed for {youtube_channel_id}: "
                f"HTTP {response.status_code} {response.text[:300]}"
            )

        logger.info(
            "WebSub subscribe accepted for channel %s (callback=%s)",
            youtube_channel_id,
            self.callback_url,
        )
        # Lease starts after verification; use requested lease as upper bound estimate
        return datetime.now(UTC) + timedelta(seconds=lease_seconds)

    async def unsubscribe(self, youtube_channel_id: str) -> None:
        """Unsubscribe a channel topic (best-effort)."""
        if not self.settings.websub_enabled:
            return

        data = {
            "hub.mode": "unsubscribe",
            "hub.topic": self.topic_url(youtube_channel_id),
            "hub.callback": self.callback_url,
            "hub.verify": "async",
        }
        if self.settings.websub_secret:
            data["hub.secret"] = self.settings.websub_secret

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.settings.websub_hub_url, data=data)

        if response.status_code not in (200, 202, 204):
            logger.warning(
                "WebSub unsubscribe failed for %s: HTTP %s %s",
                youtube_channel_id,
                response.status_code,
                response.text[:200],
            )
        else:
            logger.info("WebSub unsubscribe accepted for %s", youtube_channel_id)

    async def fetch_rss_feed(self, youtube_channel_id: str) -> list[WebSubEntry]:
        url = self.topic_url(youtube_channel_id)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Encoding": "identity",
        }
        async with httpx.AsyncClient(
            timeout=30.0, headers=headers, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return self.parse_atom_notification(response.content)


def _child_text(element: ET.Element, local_name: str, ns_uri: str | None = None) -> str | None:
    """Get text of a direct or descendant child by local name / optional namespace."""
    # Direct children with namespace
    if ns_uri:
        for child in element:
            if child.tag == f"{{{ns_uri}}}{local_name}" and child.text:
                return child.text.strip()

    # Any descendant whose tag ends with local_name
    for child in element.iter():
        tag = child.tag
        if tag == local_name or tag.endswith(f"}}{local_name}"):
            if child.text and child.text.strip():
                return child.text.strip()
    return None
