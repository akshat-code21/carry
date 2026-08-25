"""Unit tests for search coverage intelligence (weekly buckets, momentum,
stance aggregation, prompt formatting, cache keys)."""

from datetime import UTC, datetime, timedelta

from src.services.search_coverage_service import (
    aggregate_stances,
    coverage_cache_key,
    format_coverage_for_prompt,
    weekly_volume,
    wow_delta_pct,
)

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)  # Monday noon


def dt(days_ago: float) -> datetime:
    return NOW - timedelta(days=days_ago)


class TestWeeklyVolume:
    def test_fourteen_day_window_makes_two_buckets(self):
        volume = weekly_volume([], window_days=14, now=NOW)

        assert len(volume) == 2
        assert volume[0]["week_start"] == "2026-08-10"
        assert volume[1]["week_start"] == "2026-08-17"
        assert all(v["count"] == 0 for v in volume)

    def test_distributes_videos_across_bucket_boundary(self):
        # 3 days ago -> newer bucket; 10 days ago -> older bucket
        dates = [dt(3), dt(2.5), dt(10)]

        volume = weekly_volume(dates, window_days=14, now=NOW)

        assert volume[0]["count"] == 1
        assert volume[1]["count"] == 2

    def test_ignores_undated_and_out_of_window(self):
        dates = [None, dt(30), dt(-1)]  # future date also ignored

        volume = weekly_volume(dates, window_days=14, now=NOW)

        assert all(v["count"] == 0 for v in volume)

    def test_naive_datetimes_treated_as_utc(self):
        naive = dt(4).replace(tzinfo=None)

        volume = weekly_volume([naive], window_days=14, now=NOW)

        assert volume[1]["count"] == 1


class TestWowDeltaPct:
    def test_computes_growth(self):
        volume = [{"week_start": "a", "count": 40}, {"week_start": "b", "count": 56}]

        assert wow_delta_pct(volume) == 40.0

    def test_computes_decline(self):
        volume = [{"week_start": "a", "count": 10}, {"week_start": "b", "count": 4}]

        assert wow_delta_pct(volume) == -60.0

    def test_none_when_previous_week_empty(self):
        volume = [{"week_start": "a", "count": 0}, {"week_start": "b", "count": 5}]

        assert wow_delta_pct(volume) is None

    def test_none_with_single_bucket(self):
        assert wow_delta_pct([{"week_start": "a", "count": 9}]) is None


class TestAggregateStances:
    def test_maps_finbert_labels(self):
        classifications = [
            {"sentiment": "bullish", "confidence": 0.9},
            {"sentiment": "bearish", "confidence": 0.8},
            {"sentiment": "neutral", "confidence": 0.7},
        ]

        counts = aggregate_stances(classifications)

        assert counts == {"positive": 1, "neutral": 1, "negative": 1}

    def test_low_confidence_falls_back_to_neutral(self):
        counts = aggregate_stances(
            [
                {"sentiment": "bullish", "confidence": 0.49},
                {"sentiment": "bearish", "confidence": None},
            ]
        )

        assert counts == {"positive": 0, "neutral": 2, "negative": 0}

    def test_unknown_labels_become_neutral(self):
        counts = aggregate_stances([{"sentiment": "mixed", "confidence": 0.99}, {}])

        assert counts["neutral"] == 2


class TestFormatCoverageForPrompt:
    def test_full_block_including_momentum(self):
        payload = {
            "total_videos": 78,
            "positive": 55,
            "neutral": 5,
            "negative": 18,
            "window_days": 14,
            "wow_delta_pct": 40.0,
        }

        line = format_coverage_for_prompt(payload)

        assert "78 videos" in line
        assert "55 positive / 5 neutral / 18 negative" in line
        assert "up 40% week-over-week" in line

    def test_omits_momentum_when_null(self):
        payload = {
            "total_videos": 3,
            "positive": 2,
            "neutral": 1,
            "negative": 0,
            "window_days": 14,
            "wow_delta_pct": None,
        }

        line = format_coverage_for_prompt(payload)

        assert "week-over-week" not in line

    def test_none_safe(self):
        assert format_coverage_for_prompt(None) is None
        assert format_coverage_for_prompt({"total_videos": 0}) is None


class TestCoverageCacheKey:
    def test_stable_and_window_sensitive(self):
        assert coverage_cache_key("Anthropic IPO", 14) == coverage_cache_key("anthropic  IPO ", 14)
        assert coverage_cache_key("Anthropic IPO", 14) != coverage_cache_key("Anthropic IPO", 30)
