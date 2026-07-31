"""Unit tests for discovery helpers (Shorts filter, published parse)."""

from src.services.discovery_service import DiscoveryService


def test_is_short_by_duration():
    assert DiscoveryService._is_short(45, "Normal title") is True
    assert DiscoveryService._is_short(180, "Normal title") is True
    assert DiscoveryService._is_short(181, "Normal title") is False
    assert DiscoveryService._is_short(0, "Normal title") is False


def test_is_short_by_title():
    assert DiscoveryService._is_short(None, "Quick tip #shorts") is True
    assert DiscoveryService._is_short(300, "Episode #short") is True
    assert DiscoveryService._is_short(300, "Full market recap") is False
    assert DiscoveryService._is_short(300, "Full market recap", is_short_flag=True) is True


def test_parse_published():
    dt = DiscoveryService._parse_published("2026-07-28T12:00:00Z")
    assert dt is not None
    assert dt.year == 2026
    assert DiscoveryService._parse_published(None) is None
    assert DiscoveryService._parse_published("not-a-date") is None
