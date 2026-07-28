"""Tests for stock vs ETF instrument detection and discovery mode resolution."""

import pytest

from src.services.query_router import QueryRouter
from src.services.search_service import SearchService


class TestDetectInstrumentType:
    """Heuristic instrument_type detection from free-text queries."""

    def test_explicit_etf_query(self):
        assert QueryRouter.detect_instrument_type("Best semiconductor ETFs?") == "etfs"
        assert QueryRouter.detect_instrument_type("AI sector etf picks") == "etfs"
        assert QueryRouter.detect_instrument_type("which ETF for clean energy") == "etfs"
        assert QueryRouter.detect_instrument_type("top energy sector funds") == "etfs"
        assert QueryRouter.detect_instrument_type("defense index fund") == "etfs"

    def test_explicit_stock_query(self):
        assert QueryRouter.detect_instrument_type("Best AI stocks?") == "stocks"
        assert QueryRouter.detect_instrument_type("semiconductor stocks to watch") == "stocks"
        assert QueryRouter.detect_instrument_type("top biotech equities") == "stocks"

    def test_ambiguous_defaults_to_none(self):
        # No instrument words → None (caller defaults to stocks)
        assert QueryRouter.detect_instrument_type("semiconductors to watch") is None
        assert QueryRouter.detect_instrument_type("AI plays") is None
        assert QueryRouter.detect_instrument_type("defense picks") is None

    def test_mixed_prefers_earlier_signal(self):
        assert QueryRouter.detect_instrument_type("ETFs and stocks for AI") == "etfs"
        assert QueryRouter.detect_instrument_type("stocks and ETFs for AI") == "stocks"


class TestHeuristicClassify:
    """Full heuristic classification including instrument_type."""

    def test_etf_sector_discovery(self):
        result = QueryRouter._heuristic_classify("Best semiconductor ETFs?")
        assert result is not None
        assert result.intent == "sector_discovery"
        assert result.instrument_type == "etfs"
        assert result.sector_hint is not None
        assert "semiconductor" in result.sector_hint

    def test_stock_sector_discovery(self):
        result = QueryRouter._heuristic_classify("Best AI stocks?")
        assert result is not None
        assert result.intent == "sector_discovery"
        assert result.instrument_type == "stocks"

    def test_ambiguous_sector_defaults_stocks(self):
        result = QueryRouter._heuristic_classify("semiconductors")
        assert result is not None
        assert result.intent == "sector_discovery"
        assert result.instrument_type == "stocks"


class TestResolveDiscoveryMode:
    """Channel type takes precedence over query instrument_type."""

    def test_institutional_always_etfs(self):
        assert (
            SearchService.resolve_discovery_mode(
                channel_type="institutional", instrument_type="stocks"
            )
            == "etfs"
        )

    def test_individual_always_stocks(self):
        assert (
            SearchService.resolve_discovery_mode(
                channel_type="individual", instrument_type="etfs"
            )
            == "stocks"
        )

    def test_global_uses_instrument_type(self):
        assert (
            SearchService.resolve_discovery_mode(
                channel_type=None, instrument_type="etfs"
            )
            == "etfs"
        )
        assert (
            SearchService.resolve_discovery_mode(
                channel_type=None, instrument_type="stocks"
            )
            == "stocks"
        )

    def test_global_defaults_stocks(self):
        assert SearchService.resolve_discovery_mode(None, None) == "stocks"
        assert SearchService.resolve_discovery_mode(None, "unknown") == "stocks"


class TestNoEtfTaxonomySeeds:
    """Theme taxonomy must not seed ETF symbols as stock mappings."""

    def test_taxonomy_has_no_known_etfs(self):
        import json
        from pathlib import Path

        from src.services.etf_mapping_service import ETFMappingService

        tax_path = Path(__file__).parent.parent / "data" / "theme_taxonomy.json"
        data = json.loads(tax_path.read_text())
        etf_service = ETFMappingService()
        leaked: list[tuple[str, str]] = []

        def walk(obj: object, theme: str = "") -> None:
            if isinstance(obj, dict):
                name = obj.get("name", theme) if isinstance(obj.get("name"), str) else theme
                for t in obj.get("tickers", []) or []:
                    if isinstance(t, str) and etf_service.is_etf(t):
                        leaked.append((name, t.upper()))
                for v in obj.values():
                    walk(v, name)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v, theme)

        walk(data)
        assert leaked == [], f"ETF tickers still seeded in taxonomy: {leaked}"
