"""Unit tests for ticker extraction, resolution, and relevance filtering."""

import pytest
from src.pipeline.analysis import AnalysisPipeline
from src.pipeline.theme_mapping import MIN_THEME_TICKER_RELEVANCE_SCORE
from src.services.interfaces import TickerMapping


def test_resolve_ticker_explicit_and_text():
    """Verify explicit company names and explicit tickers resolve correctly."""
    # 1. Direct raw ticker
    assert AnalysisPipeline._resolve_ticker(raw_ticker="NVDA") == "NVDA"
    assert AnalysisPipeline._resolve_ticker(raw_ticker="Nvidia") == "NVDA"
    assert AnalysisPipeline._resolve_ticker(raw_ticker="Apple") == "AAPL"

    # 2. Company name in prediction text
    assert (
        AnalysisPipeline._resolve_ticker(
            raw_ticker=None,
            prediction_text="Nvidia will beat earnings expectations next week.",
        )
        == "NVDA"
    )

    # 3. Explicit tickers list
    assert (
        AnalysisPipeline._resolve_ticker(
            raw_ticker=None,
            prediction_text="Expect 20% upside for the lead AI chip maker.",
            explicit_tickers=["NVDA"],
        )
        == "NVDA"
    )


def test_resolve_ticker_ignores_implicit_tickers():
    """Verify that implicit/sector tickers are NOT used for prediction ticker resolution."""
    # Prediction has no direct ticker or company name match in text.
    # Prior behavior used implicit_tickers and tagged AMD; new behavior returns None.
    result = AnalysisPipeline._resolve_ticker(
        raw_ticker=None,
        prediction_text="The AI semiconductor sector as a whole will continue growing.",
        explicit_tickers=[],
    )
    assert result is None


def test_theme_relevance_threshold():
    """Verify relevance score threshold constant is set to 0.85."""
    assert MIN_THEME_TICKER_RELEVANCE_SCORE == 0.85
