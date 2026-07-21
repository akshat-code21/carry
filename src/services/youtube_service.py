"""YouTube service — channel/video metadata + transcript fetching."""

import logging
from datetime import datetime

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
    """YouTube Data API v3 implementation for channel/video metadata."""

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
        """List videos from a channel using the uploads playlist."""
        service = self._get_service()

        # Get the uploads playlist ID
        channel_response = service.channels().list(part="contentDetails", id=channel_id).execute()

        if not channel_response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"][
            "uploads"
        ]

        # Fetch videos from the uploads playlist
        videos: list[VideoMetadata] = []
        next_page_token = None

        while len(videos) < max_results:
            # Request some extra items per page in case there are shorts
            request = service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            response = request.execute()
            items = response.get("items", [])

            if not items:
                break

            # Fetch durations and statistics for this batch
            batch_ids = [item["contentDetails"]["videoId"] for item in items]
            details_response = (
                service.videos()
                .list(
                    part="contentDetails,statistics",
                    id=",".join(batch_ids),
                )
                .execute()
            )

            details_map = {}
            for detail_item in details_response.get("items", []):
                vid = detail_item["id"]
                duration_str = detail_item["contentDetails"].get("duration", "PT0S")
                duration_sec = self._parse_iso_duration(duration_str)
                view_count = int(detail_item.get("statistics", {}).get("viewCount", 0))
                details_map[vid] = (duration_sec, view_count)

            for item in items:
                if len(videos) >= max_results:
                    break

                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]

                dur, views = details_map.get(video_id, (0, 0))
                title = snippet.get("title", "")
                description = snippet.get("description", "")

                # Filter out YouTube Shorts: check duration AND #shorts tag
                # YouTube allows up to 3 min for shorts, so duration alone isn't reliable
                is_short = dur <= 60
                is_short = is_short or "#shorts" in title.lower()
                is_short = is_short or "#short" in title.lower()
                is_short = is_short or "#shorts" in description.lower()
                is_short = is_short or "#short" in description.lower()
                if is_short:
                    continue

                videos.append(
                    VideoMetadata(
                        video_id=video_id,
                        title=snippet["title"],
                        description=snippet.get("description", ""),
                        published_at=snippet["publishedAt"],
                        duration_sec=dur,
                        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        view_count=views,
                    )
                )

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return videos

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
