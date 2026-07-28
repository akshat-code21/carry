"""Tests for ETFMappingService — deterministic ETF resolution."""

import pytest

from src.services.etf_mapping_service import ETFMappingService


@pytest.fixture
def etf_service():
    """Create an ETFMappingService instance."""
    return ETFMappingService()


class TestETFMappingService:
    """Test the ETF mapping service resolution logic."""

    def test_resolve_by_theme(self, etf_service: ETFMappingService):
        """Theme-level lookup should return the most specific ETFs."""
        result = etf_service.resolve_etfs(theme="AI Chips")
        assert "SMH" in result
        assert "SOXX" in result

    def test_resolve_by_industry(self, etf_service: ETFMappingService):
        """Industry-level lookup should return sector ETFs."""
        result = etf_service.resolve_etfs(industry="Semiconductors")
        assert "SMH" in result
        assert "SOXX" in result

    def test_resolve_by_sector(self, etf_service: ETFMappingService):
        """Sector-level lookup should return broad ETFs."""
        result = etf_service.resolve_etfs(sector="Technology")
        assert "XLK" in result
        assert "QQQ" in result

    def test_fallback_chain_theme_to_industry_to_sector(self, etf_service: ETFMappingService):
        """When all levels are provided, results include all with most specific first."""
        result = etf_service.resolve_etfs(
            sector="Technology",
            industry="Semiconductors",
            theme="AI Chips",
        )
        # Theme-level ETFs should come first
        assert result.index("SMH") < result.index("XLK")

    def test_resolve_unknown_returns_empty(self, etf_service: ETFMappingService):
        """Unknown sector/industry/theme should return empty list."""
        result = etf_service.resolve_etfs(theme="Nonexistent Theme XYZ")
        assert result == []

    def test_resolve_deduplicates(self, etf_service: ETFMappingService):
        """Results should be deduplicated (SMH appears in both theme and industry)."""
        result = etf_service.resolve_etfs(
            industry="Semiconductors",
            theme="AI Chips",
        )
        # SMH appears in both but should only be listed once
        assert result.count("SMH") == 1

    def test_case_insensitive(self, etf_service: ETFMappingService):
        """Lookups should be case-insensitive."""
        result1 = etf_service.resolve_etfs(theme="ai chips")
        result2 = etf_service.resolve_etfs(theme="AI Chips")
        result3 = etf_service.resolve_etfs(theme="AI CHIPS")
        assert result1 == result2 == result3

    def test_is_etf(self, etf_service: ETFMappingService):
        """Known ETFs should be recognized."""
        assert etf_service.is_etf("SMH") is True
        assert etf_service.is_etf("SOXX") is True
        assert etf_service.is_etf("XLK") is True
        assert etf_service.is_etf("QQQ") is True
        # Common ETFs not only in sector maps must still classify as ETFs
        assert etf_service.is_etf("HYG") is True
        assert etf_service.is_etf("IWM") is True
        assert etf_service.is_etf("VOO") is True
        assert etf_service.is_etf("PAVE") is True
        assert etf_service.is_etf("IFRA") is True
        # Individual stocks should not be ETFs
        assert etf_service.is_etf("NVDA") is False
        assert etf_service.is_etf("AAPL") is False
        assert etf_service.is_etf(None) is False
        assert etf_service.is_etf("") is False

    def test_get_themes_for_etf(self, etf_service: ETFMappingService):
        """Reverse lookup should find themes for an ETF."""
        themes = etf_service.get_themes_for_etf("SMH")
        # SMH maps to AI Chips, Memory/Storage, Chip Manufacturing Equipment,
        # Semiconductors, and possibly China/Taiwan Tensions
        assert any("ai chips" in t.lower() for t in themes)
        assert any("semiconductor" in t.lower() for t in themes)

    def test_get_themes_for_unknown_etf(self, etf_service: ETFMappingService):
        """Unknown ETF should return empty list."""
        themes = etf_service.get_themes_for_etf("FAKEETF")
        assert themes == []

    def test_resolve_etfs_for_themes(self, etf_service: ETFMappingService):
        """Batch theme resolution should work."""
        themes = [
            {"name": "AI Chips", "level": "theme"},
            {"name": "Cybersecurity", "level": "theme"},
        ]
        result = etf_service.resolve_etfs_for_themes(themes)
        assert "SMH" in result
        assert any(etf in result for etf in ["HACK", "CIBR", "BUG"])

    def test_resolve_etfs_for_themes_industry_level(self, etf_service: ETFMappingService):
        """Industry-level themes should resolve correctly."""
        themes = [{"name": "Defense & Security", "level": "industry"}]
        result = etf_service.resolve_etfs_for_themes(themes)
        assert "ITA" in result

    def test_resolve_etfs_for_themes_sector_level(self, etf_service: ETFMappingService):
        """Sector-level themes should resolve correctly."""
        themes = [{"name": "Healthcare", "level": "sector"}]
        result = etf_service.resolve_etfs_for_themes(themes)
        assert "XLV" in result

    def test_get_all_etf_tickers(self, etf_service: ETFMappingService):
        """Should return a non-empty set of all known ETF tickers."""
        all_tickers = etf_service.get_all_etf_tickers()
        assert len(all_tickers) > 20  # We have ~40-60 unique ETFs
        assert "SMH" in all_tickers
        assert "QQQ" in all_tickers
        assert "XLK" in all_tickers

    def test_all_etf_tickers_uppercase(self, etf_service: ETFMappingService):
        """All ETF tickers should be uppercase."""
        all_tickers = etf_service.get_all_etf_tickers()
        for ticker in all_tickers:
            assert ticker == ticker.upper(), f"ETF ticker '{ticker}' is not uppercase"

    def test_financial_sector_etfs(self, etf_service: ETFMappingService):
        """Financials sector should resolve to standard financial ETFs."""
        result = etf_service.resolve_etfs(sector="Financials")
        assert "XLF" in result

    def test_energy_industry_etfs(self, etf_service: ETFMappingService):
        """Energy sector should include XLE."""
        result = etf_service.resolve_etfs(industry="Energy & Resources")
        assert "XLE" in result

    def test_clean_energy_theme_etfs(self, etf_service: ETFMappingService):
        """Clean Energy theme should include ICLN and TAN."""
        result = etf_service.resolve_etfs(theme="Clean Energy")
        assert "ICLN" in result
        assert "TAN" in result
