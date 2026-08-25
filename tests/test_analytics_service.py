"""Tests for the analytics service — event recording and rollup bumps."""

import uuid

from src.analytics.service import AnalyticsService, current_user_id


class TestDisabled:
    def test_record_event_noop_when_disabled(self):
        svc = AnalyticsService(enabled=False)
        # Must not raise (and must not touch any DB)
        svc.record_event("page_viewed", payload={"route": "/x"})
        svc.record_api_request(
            user_id=None,
            method="GET",
            path="/x",
            route_template="/x",
            status_code=200,
            duration_ms=1.0,
        )
        svc.record_llm_usage(provider="openai", model="m", purpose="p")
        svc.record_new_user(uuid.uuid4())


class TestContextAttribution:
    async def test_current_user_id_contextvar_defaults_none(self):
        assert current_user_id.get() is None

    async def test_record_llm_usage_uses_contextvar(self, monkeypatch):
        """When no explicit user_id passed, falls back to the context var."""
        svc = AnalyticsService(enabled=True)
        captured = {}

        async def fake_write(self, *rows, bumps=None):
            captured["rows"] = rows
            captured["bumps"] = bumps

        monkeypatch.setattr(AnalyticsService, "_write", fake_write)
        current_user_id.set("11111111-1111-1111-1111-111111111111")

        try:
            svc.record_llm_usage(
                provider="openai",
                model="gpt-test",
                purpose="search_classify",
                input_tokens=10,
                output_tokens=5,
            )
            await svc.flush()
        finally:
            current_user_id.set(None)

        assert len(captured["rows"]) == 1
        assert captured["rows"][0].user_id == uuid.UUID("11111111-1111-1111-1111-111111111111")
        assert captured["bumps"]["counters"] == {"llm_input_tokens": 10, "llm_output_tokens": 5}

    async def test_invalid_user_id_string_is_dropped_not_raised(self, monkeypatch):
        svc = AnalyticsService(enabled=True)
        captured = {}

        async def fake_write(self, *rows, bumps=None):
            captured["rows"] = rows

        monkeypatch.setattr(AnalyticsService, "_write", fake_write)
        svc.record_event("search_performed", user_id="not-a-uuid", payload={})
        await svc.flush()
        assert captured["rows"][0].user_id is None

    async def test_record_api_request_bumps_rollup(self, monkeypatch):
        svc = AnalyticsService(enabled=True)
        captured = {}

        async def fake_write(self, *rows, bumps=None):
            captured["bumps"] = bumps

        monkeypatch.setattr(AnalyticsService, "_write", fake_write)
        uid = str(uuid.uuid4())
        svc.record_api_request(
            user_id=uid,
            method="GET",
            path="/api/videos",
            route_template="/api/videos",
            status_code=200,
            duration_ms=12.3,
        )
        await svc.flush()

        assert captured["bumps"]["counters"] == {"api_calls": 1}
