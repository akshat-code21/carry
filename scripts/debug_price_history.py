"""Diagnostic script: calls yfinance directly (bypassing FastAPI/logging)
to see exactly why /api/tickers/{ticker}/price-history is returning [].

Run from repo root:
    uv run python scripts/debug_price_history.py NVDA

Safe to delete after debugging.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main(ticker: str) -> None:
    import yfinance as yf

    print(f"yfinance version: {yf.__version__}")

    end = date.today()
    start = end - timedelta(days=730)
    print(f"Fetching {ticker} from {start} to {end}")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
        )
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame empty? {df.empty}")
        if not df.empty:
            print(df.head())
            print("...")
            print(df.tail())
        else:
            print("Empty DataFrame returned -- trying a shorter, more recent window (last 30 days)...")
            df2 = stock.history(period="1mo")
            print(f"1mo period fetch shape: {df2.shape}, empty? {df2.empty}")
            if not df2.empty:
                print(df2.tail())

        # Also try .info to see if the ticker resolves at all
        try:
            info = stock.fast_info
            print(f"fast_info: {dict(info)}")
        except Exception as e:
            print(f"fast_info failed: {e}")

    except Exception as e:
        import traceback

        print(f"EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    main(ticker_arg)
