"""YouTube service — channel/video metadata + transcript fetching."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from src.config import get_settings
from src.services.interfaces import (
    ChannelMetadata,
    TranscriptSegmentDTO,
    TranscriptSource,
    VideoMetadata,
    YouTubeService,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class YouTubeAPIService(YouTubeService):
    """YouTube Data API v3 + yt-dlp for channel/video metadata.

    Uses yt-dlp for video listing (robust Shorts detection via ``!is_short``)
    and YouTube Data API for channel metadata and per-video details.
    """

    def __init__(self) -> None:
        self._api_key = settings.youtube_api_key
        self._service = None

    def _get_service(self):
        """Lazily initialize the YouTube API client."""
        if self._service is None:
            if not self._api_key:
                raise ValueError("YOUTUBE_API_KEY is not set. Please set it in your .env file.")
            from googleapiclient.discovery import build

            self._service = build("youtube", "v3", developerKey=self._api_key)
        return self._service

    async def get_channel_info(self, channel_id: str) -> ChannelMetadata:
        """Fetch channel metadata via YouTube Data API v3."""
        service = self._get_service()
        request = service.channels().list(
            part="snippet,contentDetails",
            id=channel_id,
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")

        item = response["items"][0]
        snippet = item["snippet"]

        return ChannelMetadata(
            channel_id=channel_id,
            title=snippet["title"],
            description=snippet.get("description", ""),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        )

    async def list_channel_videos(
        self, channel_id: str, max_results: int = 20
    ) -> list[VideoMetadata]:
        """List videos from a channel, excluding Shorts (via yt-dlp).

        Uses yt-dlp's ``!is_short`` match filter (checks YouTube's internal
        metadata — more reliable than duration + hashtags). Falls back to the
        YouTube Data API only for per-video details (duration, view count).
        """
        entries = await self._fetch_video_list_ytdlp(channel_id, max_results)
        if not entries:
            return []

        service = self._get_service()

        # Batch-fetch video details via Data API (duration, view count)
        batch_ids = [e["id"] for e in entries[:max_results]]
        details_response = (
            service.videos()
            .list(
                part="contentDetails,statistics",
                id=",".join(batch_ids),
            )
            .execute()
        )

        details_map = {}
        for item in details_response.get("items", []):
            vid = item["id"]
            dur = self._parse_iso_duration(item["contentDetails"].get("duration", "PT0S"))
            views = int(item.get("statistics", {}).get("viewCount", 0))
            details_map[vid] = (dur, views)

        videos: list[VideoMetadata] = []
        for entry in entries[:max_results]:
            vid = entry["id"]
            details = details_map.get(vid)
            if details is None:
                continue  # video deleted or made private between calls
            dur, views = details

            pub = entry.get("timestamp")
            if pub:
                pub = datetime.fromtimestamp(pub, tz=timezone.utc).isoformat()
            else:
                pub = ""

            videos.append(
                VideoMetadata(
                    video_id=vid,
                    title=entry.get("title", ""),
                    description=entry.get("description", ""),
                    published_at=pub,
                    duration_sec=dur,
                    thumbnail_url=entry.get("thumbnail", ""),
                    view_count=views,
                )
            )

        return videos

    async def _fetch_video_list_ytdlp(self, channel_id: str, max_results: int) -> list[dict]:
        """Fetch video list from a channel via yt-dlp, filtering out Shorts.

        Uses ``--flat-playlist`` (fast, no per-video extraction) and
        ``--match-filter "!is_short"`` for robust Shorts detection.
        """
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

        # Fetch extra entries to account for Shorts that get filtered out
        fetch_limit = max(max_results * 3, 50)

        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--match-filter",
            "!is_short",
            "--dump-json",
            "--no-warnings",
            "--playlist-end",
            str(fetch_limit),
            "--ignore-errors",
            channel_url,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"yt-dlp failed (exit {process.returncode}): {error_msg}")

            entries = []
            for line in stdout.decode().strip().split("\n"):
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            return entries

        except FileNotFoundError:
            raise RuntimeError(
                "yt-dlp is not installed. Install it with: brew install yt-dlp  "
                "or: pip install yt-dlp"
            )

    async def get_video_info(self, video_id: str) -> VideoMetadata:
        """Fetch metadata for a single video."""
        service = self._get_service()
        response = (
            service.videos().list(part="snippet,contentDetails,statistics", id=video_id).execute()
        )

        if not response.get("items"):
            raise ValueError(f"Video not found: {video_id}")

        item = response["items"][0]
        snippet = item["snippet"]

        return VideoMetadata(
            video_id=video_id,
            title=snippet["title"],
            description=snippet.get("description", ""),
            published_at=snippet["publishedAt"],
            duration_sec=self._parse_iso_duration(item["contentDetails"].get("duration", "PT0S")),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            view_count=int(item.get("statistics", {}).get("viewCount", 0)),
        )

    @staticmethod
    def _parse_iso_duration(duration_str: str) -> int:
        """Parse ISO 8601 duration (PT1H2M3S) to total seconds."""
        import re

        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds


class YouTubeTranscriptFetcher(TranscriptSource):
    """Fetches transcripts via youtube-transcript-api with yt-dlp + Whisper fallback."""

    async def fetch_transcript(self, video_id: str) -> list[TranscriptSegmentDTO]:
        """Fetch transcript, trying auto-captions first, then ASR fallback."""
        # Primary: youtube-transcript-api
        try:
            return await self._fetch_via_api(video_id)
        except Exception as e:
            logger.warning(
                f"Caption fetch failed for {video_id}, will attempt Whisper fallback: {e}"
            )

        # Fallback: yt-dlp + Whisper (not implemented in v1 — requires local Whisper)
        raise NotImplementedError(
            f"Whisper fallback not yet implemented. Caption fetch failed for {video_id}. "
            "Set up whisper or faster-whisper for ASR fallback."
        )

    async def _fetch_via_api(self, video_id: str) -> list[TranscriptSegmentDTO]:
        """Fetch transcript using youtube-transcript-api."""
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi().list(video_id)

        # Try manually created English transcript first, then auto-generated
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                pass

        if transcript is None:
            raise ValueError(f"No English transcript available for video {video_id}")

        raw_segments = transcript.fetch()

        return [
            TranscriptSegmentDTO(
                start_sec=seg.start,
                end_sec=seg.start + seg.duration,
                text=seg.text,
            )
            for seg in raw_segments
        ]
