"""Unit tests for YouTube Shorts detection and filtering during ingestion/backfill."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.youtube_service import YouTubeAPIService


def test_is_short_duration():
    """Test that videos with duration <= 180 seconds are identified as Shorts."""
    # Under or equal to 180 seconds -> Short
    assert YouTubeAPIService._is_short(duration_sec=30, title="Quick Tech Update") is True
    assert YouTubeAPIService._is_short(duration_sec=180, title="3 Min News") is True

    # Over 180 seconds -> Long-form
    assert YouTubeAPIService._is_short(duration_sec=181, title="181 Second Video") is False
    assert YouTubeAPIService._is_short(duration_sec=600, title="10 Min Deep Dive") is False


def test_is_short_title_hashtags():
    """Test that videos with #shorts or #short in title are identified as Shorts."""
    assert YouTubeAPIService._is_short(duration_sec=300, title="Market Breakdown #shorts") is True
    assert YouTubeAPIService._is_short(duration_sec=300, title="Nvidia News #SHORT") is True
    assert YouTubeAPIService._is_short(duration_sec=300, title="Regular Market Analysis") is False


def test_is_short_entry_metadata():
    """Test that yt-dlp metadata flags (is_short=True or /shorts/ URL) identify Shorts."""
    entry_short = {"is_short": True, "url": "https://youtube.com/watch?v=123"}
    entry_url = {"is_short": None, "url": "https://youtube.com/shorts/xyz123"}
    entry_normal = {"is_short": False, "url": "https://youtube.com/watch?v=456"}

    assert YouTubeAPIService._is_short(duration_sec=600, title="Video", entry=entry_short) is True
    assert YouTubeAPIService._is_short(duration_sec=600, title="Video", entry=entry_url) is True
    assert YouTubeAPIService._is_short(duration_sec=600, title="Video", entry=entry_normal) is False


@pytest.mark.asyncio
async def test_list_channel_videos_filters_shorts():
    """Test that list_channel_videos filters out Shorts and collects long-form videos."""
    yt_service = YouTubeAPIService()

    mock_entries = [
        {"id": "short1", "title": "Short 1 #shorts", "timestamp": 1600000000},
        {"id": "long1", "title": "Long Video 1", "timestamp": 1600000100},
        {"id": "short2", "title": "Short 2", "timestamp": 1600000200},
        {"id": "long2", "title": "Long Video 2", "timestamp": 1600000300},
    ]

    mock_api_items = [
        {
            "id": "short1",
            "contentDetails": {"duration": "PT30S"},
            "statistics": {"viewCount": "100"},
        },
        {
            "id": "long1",
            "contentDetails": {"duration": "PT10M"},
            "statistics": {"viewCount": "5000"},
        },
        {
            "id": "short2",
            "contentDetails": {"duration": "PT45S"},
            "statistics": {"viewCount": "200"},
        },
        {
            "id": "long2",
            "contentDetails": {"duration": "PT15M"},
            "statistics": {"viewCount": "8000"},
        },
    ]

    mock_service_obj = MagicMock()
    mock_videos_req = MagicMock()
    mock_videos_req.execute.return_value = {"items": mock_api_items}
    mock_service_obj.videos.return_value.list.return_value = mock_videos_req

    with (
        patch.object(yt_service, "_fetch_video_list_ytdlp", new_callable=AsyncMock) as mock_ytdlp,
        patch.object(yt_service, "_get_service", return_value=mock_service_obj),
    ):
        mock_ytdlp.return_value = mock_entries

        videos = await yt_service.list_channel_videos("UC12345", max_results=2)

        assert len(videos) == 2
        assert videos[0].video_id == "long1"
        assert videos[0].duration_sec == 600
        assert videos[1].video_id == "long2"
        assert videos[1].duration_sec == 900
