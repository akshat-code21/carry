"""Unit tests for WebSub Atom parsing and signature verification."""

import hashlib
import hmac

from src.config import Settings
from src.services.websub_service import WebSubService

SAMPLE_ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns="http://www.w3.org/2005/Atom">
  <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
  <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=UCtest"/>
  <title>YouTube video feed</title>
  <entry>
    <id>yt:video:dQw4w9WgXcQ</id>
    <yt:videoId>dQw4w9WgXcQ</yt:videoId>
    <yt:channelId>UCtestchannel</yt:channelId>
    <title>Market Outlook This Week</title>
    <published>2026-07-28T12:00:00+00:00</published>
    <updated>2026-07-28T12:00:00+00:00</updated>
  </entry>
  <entry>
    <id>yt:video:abc123XYZ00</id>
    <yt:videoId>abc123XYZ00</yt:videoId>
    <yt:channelId>UCtestchannel</yt:channelId>
    <title>Another Episode #shorts</title>
    <published>2026-07-28T13:00:00+00:00</published>
  </entry>
</feed>
"""


def test_parse_atom_notification_extracts_entries():
    entries = WebSubService.parse_atom_notification(SAMPLE_ATOM)
    assert len(entries) == 2
    assert entries[0].youtube_video_id == "dQw4w9WgXcQ"
    assert entries[0].youtube_channel_id == "UCtestchannel"
    assert entries[0].title == "Market Outlook This Week"
    assert entries[0].published_at is not None
    assert entries[1].youtube_video_id == "abc123XYZ00"


def test_parse_atom_empty_body():
    assert WebSubService.parse_atom_notification(b"") == []
    assert WebSubService.parse_atom_notification("not xml at all <<<") == []


def test_verify_signature_valid():
    settings = Settings(websub_secret="test-secret", public_base_url="https://example.com")
    service = WebSubService(settings)
    body = b"<feed>hello</feed>"
    digest = hmac.new(b"test-secret", body, hashlib.sha1).hexdigest()
    assert service.verify_signature(body, f"sha1={digest}") is True


def test_verify_signature_invalid():
    settings = Settings(websub_secret="test-secret", public_base_url="https://example.com")
    service = WebSubService(settings)
    assert service.verify_signature(b"body", "sha1=deadbeef") is False
    assert service.verify_signature(b"body", None) is False


def test_verify_signature_skipped_without_secret():
    settings = Settings(websub_secret="", public_base_url="https://example.com")
    service = WebSubService(settings)
    assert service.verify_signature(b"body", None) is True


def test_topic_and_callback_urls():
    settings = Settings(
        public_base_url="https://abc.ngrok-free.app/",
        websub_secret="x",
    )
    service = WebSubService(settings)
    assert service.callback_url == "https://abc.ngrok-free.app/api/websub/callback"
    assert "channel_id=UCxyz" in service.topic_url("UCxyz")


def test_build_atom_notification_roundtrip():
    atom = WebSubService.build_atom_notification(
        youtube_channel_id="UCtestchannel",
        youtube_video_id="simVid00001",
        title='Simulated "upload" & test',
    )
    entries = WebSubService.parse_atom_notification(atom)
    assert len(entries) == 1
    assert entries[0].youtube_video_id == "simVid00001"
    assert entries[0].youtube_channel_id == "UCtestchannel"
    assert "Simulated" in entries[0].title
