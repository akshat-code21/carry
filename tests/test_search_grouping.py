"""Unit tests for hybrid search consolidation: RRF fusion, per-video diversity
capping, and per-video grouping."""

from src.services.search_service import SearchService


def make_seg(seg_id: str, video_id: str, rank: float, search_type: str) -> dict:
    return {
        "id": seg_id,
        "video_id": video_id,
        "start_sec": 0.0,
        "end_sec": 10.0,
        "text": f"segment {seg_id}",
        "rank": rank,
        "search_type": search_type,
    }


class TestFuseRRF:
    def test_segment_in_both_lists_becomes_hybrid_with_combined_score(self):
        a = [make_seg("s1", "v1", rank=0.9, search_type="semantic")]
        b = [make_seg("s1", "v1", rank=0.06, search_type="keyword")]

        fused = SearchService._fuse_rrf([a, b])

        assert set(fused.keys()) == {"s1"}
        # RRF contribution from both lists: 2 * 1/(60+1)
        assert abs(fused["s1"]["_rrf"] - 2 * (1 / 61)) < 1e-9
        assert fused["s1"]["search_type"] == "hybrid"
        # Raw display score keeps the better of the two lists
        assert fused["s1"]["rank"] == 0.9

    def test_segment_in_single_list_keeps_origin(self):
        a = [
            make_seg("s1", "v1", rank=0.9, search_type="semantic"),
            make_seg("s2", "v2", rank=0.8, search_type="semantic"),
        ]

        fused = SearchService._fuse_rrf([a])

        assert fused["s1"]["_rrf"] > fused["s2"]["_rrf"]  # earlier rank scores higher
        assert fused["s1"]["search_type"] == "semantic"
        assert fused["s2"]["search_type"] == "semantic"

    def test_empty_lists(self):
        assert SearchService._fuse_rrf([]) == {}
        assert SearchService._fuse_rrf([[], []]) == {}


class TestSelectDiverse:
    def test_caps_segments_per_video(self):
        ranked = [{"id": f"s{i}", "video_id": "v1", "_rrf": 0.05 - i * 0.001} for i in range(6)] + [
            {"id": "x1", "video_id": "v2", "_rrf": 0.02}
        ]

        selected = SearchService._select_diverse(ranked, limit=10, max_per_video=4)

        v1 = [s for s in selected if s["video_id"] == "v1"]
        assert len(v1) == 4
        assert any(s["video_id"] == "v2" for s in selected)

    def test_respects_limit(self):
        ranked = [{"id": f"s{i}", "video_id": f"v{i}", "_rrf": 0.05} for i in range(30)]

        selected = SearchService._select_diverse(ranked, limit=20, max_per_video=4)

        assert len(selected) == 20

    def test_preserves_rank_order(self):
        ranked = [
            {"id": "a", "video_id": "v1", "_rrf": 0.03},
            {"id": "b", "video_id": "v2", "_rrf": 0.02},
            {"id": "c", "video_id": "v1", "_rrf": 0.01},
        ]

        selected = SearchService._select_diverse(ranked, limit=3, max_per_video=4)

        assert [s["id"] for s in selected] == ["a", "b", "c"]


class TestBuildGroups:
    def _videos_map(self, *vids: str) -> dict:
        return {
            vid: {
                "id": vid,
                "channel_id": f"ch_{vid}",
                "youtube_video_id": f"yt_{vid}",
                "title": f"Title {vid}",
                "thumbnail_url": None,
                "published_at": "2026-08-01T00:00:00+00:00",
            }
            for vid in vids
        }

    def _channels_map(self, *chans: str) -> dict:
        return {c: {"id": c, "title": f"Channel {c}"} for c in chans}

    def test_groups_by_video_with_top_split_and_ordering(self):
        segments = [
            make_seg("s1", "vA", rank=0.9, search_type="semantic"),
            make_seg("s2", "vB", rank=0.8, search_type="keyword"),
            make_seg("s3", "vA", rank=0.7, search_type="keyword"),
            make_seg("s4", "vB", rank=0.6, search_type="keyword"),
            make_seg("s5", "vB", rank=0.5, search_type="semantic"),
        ]
        for i, seg in enumerate(segments):
            seg["_rrf"] = 0.05 - i * 0.001

        groups = SearchService._build_groups(
            segments, self._videos_map("vA", "vB"), self._channels_map("ch_vA", "ch_vB"), {}
        )

        assert len(groups) == 2
        # Ordered by best fused rank: vA's best member outranks vB's
        assert groups[0]["video_id"] == "vA"
        assert groups[1]["video_id"] == "vB"

        group_a = groups[0]
        assert group_a["hit_count"] == 2
        assert [s["id"] for s in group_a["top_segments"]] == ["s1", "s3"]
        assert group_a["remaining_segments"] == []
        assert group_a["video_title"] == "Title vA"
        assert group_a["channel_title"] == "Channel ch_vA"

        group_b = groups[1]
        assert len(group_b["top_segments"]) == 2
        assert [s["id"] for s in group_b["remaining_segments"]] == ["s5"]

    def test_hit_count_prefers_truthful_keyword_count(self):
        segments = [make_seg("s1", "vA", rank=0.9, search_type="keyword")]
        segments[0]["_rrf"] = 0.05

        # Pool only carried 1 member but full-text index says 8 matches exist
        groups = SearchService._build_groups(
            segments, self._videos_map("vA"), self._channels_map(), {"vA": 8}
        )

        assert groups[0]["hit_count"] == 8

    def test_internal_fusion_score_not_required(self):
        segments = [make_seg("s1", "vA", rank=0.9, search_type="keyword")]
        segments[0]["_rrf"] = 0.05

        groups = SearchService._build_groups(
            segments, self._videos_map("vA"), self._channels_map(), {}
        )

        assert groups[0]["best_rank"] > 0


class TestApplyGroupSort:
    def test_recent_sorts_by_published_at_descending(self):
        groups = [
            {"video_id": "old", "published_at": "2025-01-01T00:00:00+00:00"},
            {"video_id": "new", "published_at": "2026-08-20T00:00:00+00:00"},
            {"video_id": "mid", "published_at": "2026-01-15T00:00:00+00:00"},
        ]

        SearchService._apply_group_sort(groups, "recent")

        assert [g["video_id"] for g in groups] == ["new", "mid", "old"]

    def test_recent_pushes_missing_dates_last(self):
        groups = [
            {"video_id": "no_date", "published_at": None},
            {"video_id": "dated", "published_at": "2026-08-20T00:00:00+00:00"},
        ]

        SearchService._apply_group_sort(groups, "recent")

        assert [g["video_id"] for g in groups] == ["dated", "no_date"]

    def test_relevance_sort_is_noop_preserving_rank_order(self):
        groups = [
            {"video_id": "a", "best_rank": 0.03, "published_at": "2025-01-01T00:00:00+00:00"},
            {"video_id": "b", "best_rank": 0.02, "published_at": "2026-08-20T00:00:00+00:00"},
        ]

        SearchService._apply_group_sort(groups, "relevance")

        assert [g["video_id"] for g in groups] == ["a", "b"]


class TestComputeHasMore:
    def test_keyword_mode_true_when_more_matching_videos_exist(self):
        hit_counts = {f"v{i}": 3 for i in range(10)}

        has_more = SearchService._compute_has_more(
            hit_counts=hit_counts, group_count=6, candidate_count=80, pool_size=80
        )

        assert has_more is True

    def test_keyword_mode_false_when_all_videos_returned(self):
        hit_counts = {"v1": 3, "v2": 5}

        has_more = SearchService._compute_has_more(
            hit_counts=hit_counts, group_count=2, candidate_count=8, pool_size=80
        )

        assert has_more is False

    def test_semantic_mode_falls_back_to_pool_exhaustion(self):
        exhausted = SearchService._compute_has_more(
            hit_counts={}, group_count=20, candidate_count=100, pool_size=100
        )
        not_exhausted = SearchService._compute_has_more(
            hit_counts={}, group_count=20, candidate_count=42, pool_size=100
        )

        assert exhausted is True
        assert not_exhausted is False
