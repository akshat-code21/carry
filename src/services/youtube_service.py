"""YouTube service — channel/video metadata + transcript fetching."""

import asyncio
import json
import logging
from datetime import UTC, datetime

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

    @staticmethod
    def _is_short(duration_sec: int, title: str = "", entry: dict | None = None) -> bool:
        """Check if a video is a YouTube Short.

        A video is considered a Short if:
        - duration_sec <= 60 (standard YouTube Shorts duration threshold)
        - title contains '#shorts' or '#short'
        - entry dict metadata explicitly marks it as short (is_short=True or /shorts/ in URL)
        """
        if duration_sec > 0 and duration_sec <= 60:
            return True

        title_lower = title.lower()
        if "#shorts" in title_lower or "#short" in title_lower:
            return True

        if entry:
            if entry.get("is_short") is True:
                return True
            url = entry.get("url", "") or entry.get("webpage_url", "")
            if "/shorts/" in url:
                return True

        return False

    async def list_channel_videos(
        self, channel_id: str, max_results: int = 20
    ) -> list[VideoMetadata]:
        """List long-form videos from a channel, explicitly excluding Shorts.

        Fetches video metadata and filters out any videos with duration <= 60 seconds
        or Shorts flags/hashtags until up to `max_results` long-form videos are obtained.
        """
        entries = []
        try:
            entries = await self._fetch_video_list_ytdlp(channel_id, max_results)
        except Exception as e:
            logger.warning(
                f"yt-dlp video list fetch failed ({e}), falling back to YouTube Data API"
            )

        if not entries:
            return await self._list_channel_videos_api(channel_id, max_results)

        service = self._get_service()
        videos: list[VideoMetadata] = []

        # Process entries in batches of 50 (YouTube Data API max batch size)
        chunk_size = 50
        for i in range(0, len(entries), chunk_size):
            chunk_entries = entries[i : i + chunk_size]
            batch_ids = [e["id"] for e in chunk_entries if e.get("id")]
            if not batch_ids:
                continue

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

            for entry in chunk_entries:
                vid = entry.get("id")
                if not vid:
                    continue

                details = details_map.get(vid)
                if details is None:
                    continue  # Video deleted or private

                dur, views = details
                title = entry.get("title", "")

                if self._is_short(duration_sec=dur, title=title, entry=entry):
                    logger.info(f"Skipping YouTube Short: {title} ({vid}) - duration: {dur}s")
                    continue

                pub = entry.get("timestamp")
                if pub:
                    pub = datetime.fromtimestamp(pub, tz=UTC).isoformat()
                else:
                    pub = ""

                videos.append(
                    VideoMetadata(
                        video_id=vid,
                        title=title,
                        description=entry.get("description", ""),
                        published_at=pub,
                        duration_sec=dur,
                        thumbnail_url=entry.get("thumbnail", ""),
                        view_count=views,
                    )
                )

                if len(videos) >= max_results:
                    return videos

        return videos

    async def _list_channel_videos_api(
        self, channel_id: str, max_results: int = 20
    ) -> list[VideoMetadata]:
        """Fallback to list channel videos using YouTube Data API v3 directly."""
        service = self._get_service()

        # Step 1: Get channel's uploads playlist ID
        channel_req = service.channels().list(part="contentDetails", id=channel_id)
        channel_res = channel_req.execute()
        items = channel_res.get("items", [])

        if not items and channel_id.startswith("@"):
            channel_req = service.channels().list(part="contentDetails", forHandle=channel_id)
            channel_res = channel_req.execute()
            items = channel_res.get("items", [])

        if not items:
            logger.warning(f"Could not find channel via Data API: {channel_id}")
            return []

        uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        videos: list[VideoMetadata] = []
        next_page_token = None

        while len(videos) < max_results:
            playlist_req = service.playlistItems().list(
                part="snippet",
                playlistId=uploads_id,
                maxResults=min(50, (max_results - len(videos)) * 3),
                pageToken=next_page_token,
            )
            playlist_res = playlist_req.execute()
            playlist_items = playlist_res.get("items", [])

            if not playlist_items:
                break

            video_ids = [
                item["snippet"]["resourceId"]["videoId"]
                for item in playlist_items
                if item.get("snippet", {}).get("resourceId", {}).get("videoId")
            ]

            if not video_ids:
                break

            details_req = service.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids),
            )
            details_res = details_req.execute()

            for item in details_res.get("items", []):
                vid = item["id"]
                snippet = item["snippet"]
                dur = self._parse_iso_duration(item["contentDetails"].get("duration", "PT0S"))
                title = snippet.get("title", "")

                if self._is_short(duration_sec=dur, title=title):
                    logger.info(f"Skipping YouTube Short (API): {title} ({vid}) - duration: {dur}s")
                    continue

                views = int(item.get("statistics", {}).get("viewCount", 0))
                pub = snippet.get("publishedAt", "")

                videos.append(
                    VideoMetadata(
                        video_id=vid,
                        title=title,
                        description=snippet.get("description", ""),
                        published_at=pub,
                        duration_sec=dur,
                        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        view_count=views,
                    )
                )

                if len(videos) >= max_results:
                    break

            next_page_token = playlist_res.get("nextPageToken")
            if not next_page_token:
                break

        return videos

    async def _fetch_video_list_ytdlp(self, channel_id: str, max_results: int) -> list[dict]:
        """Fetch video list from a channel via yt-dlp.

        Uses ``--flat-playlist`` (fast, no per-video extraction).
        """
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

        # Fetch extra entries to account for Shorts that get filtered out
        fetch_limit = max(max_results * 5, 100)

        cmd = [
            "yt-dlp",
            "--flat-playlist",
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
