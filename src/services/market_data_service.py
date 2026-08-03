"""Market data service — yfinance implementation."""

import logging
from datetime import date, timedelta

from src.services.interfaces import MarketDataSource, PricePoint

logger = logging.getLogger(__name__)


class YFinanceMarketDataService(MarketDataSource):
    """Fetches stock/ETF price data via yfinance."""

    async def get_price_history(self, ticker: str, start: date, end: date) -> list[PricePoint]:
        """Fetch daily OHLCV data for a ticker between start and end dates."""
        import yfinance as yf

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),  # end is exclusive in yfinance
            )

            if df.empty:
                logger.warning(f"No price data returned for {ticker} ({start} to {end})")
                return []

            return [
                PricePoint(
                    date=idx.date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
                for idx, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to fetch price data for {ticker}: {e}")
            return []

    async def get_price_at_date(self, ticker: str, target_date: date) -> float | None:
        """Get close price on or near a date.

        Forward-fills to next trading day if the target date is a weekend/holiday.
        Tries up to 7 days forward to find a valid trading day.
        """
        import yfinance as yf

        try:
            stock = yf.Ticker(ticker)
            # Fetch a week of data around the target date to handle weekends/holidays
            start = target_date
            end = target_date + timedelta(days=7)

            df = stock.history(
                start=start.isoformat(),
                end=end.isoformat(),
            )

            if df.empty:
                logger.warning(f"No price data found for {ticker} near {target_date}")
                return None

            # Return the close price of the first available trading day
            return float(df.iloc[0]["Close"])
        except Exception as e:
            logger.error(f"Failed to get price for {ticker} at {target_date}: {e}")
            return None
