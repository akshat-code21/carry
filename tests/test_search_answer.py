"""Unit tests for search answer synthesis helpers (parsing, prompts, caching keys)."""

import json

from src.services.search_answer_service import (
    CITATION_TEXT_LIMIT,
    MAX_KEY_POINTS,
    SEGMENT_TEXT_LIMIT,
    build_user_prompt,
    hash_query,
    map_citations,
    normalize_query,
    parse_llm_response,
)

VALID_IDS = {"s1", "s2", "s3"}


class TestNormalizeAndHash:
    def test_normalizes_case_and_whitespace(self):
        assert normalize_query("  Anthropic's   IPO in\n2027 ") == "anthropic's ipo in 2027"

    def test_hash_is_stable_and_sensitive(self):
        assert hash_query("Anthropic IPO") == hash_query("anthropic  IPO")
        assert hash_query("Anthropic IPO") != hash_query("Nvidia outlook")
        assert len(hash_query("anything")) == 64


class TestBuildUserPrompt:
    def _seg(self, seg_id: str, text: str) -> dict:
        return {
            "id": seg_id,
            "video_id": "v1",
            "start_sec": 12.0,
            "text": text,
            "video_title": "Big Tech Bets",
            "channel_title": "Alpha Street",
        }

    def test_includes_ids_titles_and_truncates_long_text(self):
        long_text = "x" * (SEGMENT_TEXT_LIMIT + 500)
        prompt = build_user_prompt("Anthropic IPO?", [self._seg("s1", long_text)])

        assert "Query: Anthropic IPO?" in prompt
        assert "[s1]" in prompt
        assert 'Alpha Street — "Big Tech Bets"' in prompt
        # Truncated to the limit, no overflow
        assert ("x" * SEGMENT_TEXT_LIMIT) in prompt
        assert ("x" * (SEGMENT_TEXT_LIMIT + 1)) not in prompt


class TestParseLLMResponse:
    def test_valid_payload_with_citation_filtering_and_order(self):
        raw = json.dumps(
            {
                "summary": "Commentators are split.",
                "key_points": ["IPO timing unclear", "  ", "Bulls cite demand", 42],
                "cited_segment_ids": ["s3", "unknown", "s1", "s3"],
            }
        )

        parsed = parse_llm_response(raw, VALID_IDS)

        assert parsed is not None
        assert parsed["summary"] == "Commentators are split."
        # Blank/non-string key points dropped, trimmed
        assert parsed["key_points"] == ["IPO timing unclear", "Bulls cite demand"]
        # Unknown ids filtered, duplicates removed, LLM order preserved
        assert parsed["cited_segment_ids"] == ["s3", "s1"]

    def test_key_points_capped(self):
        raw = json.dumps(
            {
                "summary": "s",
                "key_points": [f"point {i}" for i in range(10)],
                "cited_segment_ids": [],
            }
        )

        parsed = parse_llm_response(raw, VALID_IDS)

        assert len(parsed["key_points"]) == MAX_KEY_POINTS

    def test_returns_none_on_garbage(self):
        assert parse_llm_response("not json", VALID_IDS) is None
        assert parse_llm_response('["a list"]', VALID_IDS) is None

    def test_returns_none_without_summary(self):
        raw = json.dumps({"key_points": [], "cited_segment_ids": []})
        assert parse_llm_response(raw, VALID_IDS) is None


def make_seg(seg_id: str) -> dict:
    return {
        "id": seg_id,
        "video_id": f"video_{seg_id}",
        "start_sec": 61.5,
        "end_sec": 70.0,
        "text": "y" * (CITATION_TEXT_LIMIT + 100),
        "video_title": f"Title {seg_id}",
        "channel_title": "Channel A",
        "youtube_video_id": "abc123",
    }


class TestMapCitations:
    def test_maps_metadata_in_order_with_truncated_text(self):
        segments = [make_seg("s1"), make_seg("s2")]

        citations = map_citations(["s2", "s1"], segments)

        assert [c["segment_id"] for c in citations] == ["s2", "s1"]
        first = citations[0]
        assert first["video_id"] == "video_s2"
        assert first["start_sec"] == 61.5
        assert len(first["text"]) == CITATION_TEXT_LIMIT
        assert first["channel_title"] == "Channel A"
