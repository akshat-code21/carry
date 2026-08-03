"""Tests for YouTubeTranscriptFetcher including Supadata fallback."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.youtube_service import YouTubeTranscriptFetcher


@pytest.mark.asyncio
async def test_fetch_via_api_success():
    fetcher = YouTubeTranscriptFetcher()
    mock_seg = MagicMock()
    mock_seg.start = 0.0
    mock_seg.duration = 5.0
    mock_seg.text = "Hello world"

    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = [mock_seg]

    mock_list = MagicMock()
    mock_list.find_manually_created_transcript.return_value = mock_transcript

    with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_api:
        mock_api.return_value.list.return_value = mock_list
        segments = await fetcher.fetch_transcript("test_vid")

        assert len(segments) == 1
        assert segments[0].text == "Hello world"
        assert segments[0].start_sec == 0.0
        assert segments[0].end_sec == 5.0


@pytest.mark.asyncio
async def test_fetch_via_supadata_fallback():
    fetcher = YouTubeTranscriptFetcher()

    # Make primary api fail
    with patch.object(fetcher, "_fetch_via_api", side_effect=ValueError("IP Blocked")):
        with patch("src.services.youtube_service.settings.supadata_api_key", "test_key"):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "content": [
                        {"text": "Supadata line 1", "offset": 1.5, "duration": 3.0},
                        {"text": "Supadata line 2", "offset": 4.5, "duration": 2.5},
                    ]
                }
                mock_get.return_value = mock_resp

                segments = await fetcher.fetch_transcript("test_vid")

                assert len(segments) == 2
                assert segments[0].text == "Supadata line 1"
                assert segments[0].start_sec == 1.5
                assert segments[0].end_sec == 4.5
                assert segments[1].text == "Supadata line 2"
