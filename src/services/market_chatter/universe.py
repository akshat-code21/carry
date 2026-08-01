"""S&P 100 symbol universe for TickerFlow.

Phase 1 restricts the ticker universe to the S&P 100 to keep Adanos API
usage predictable within budget limits.
"""

from __future__ import annotations

import re

SP100_SYMBOLS = frozenset(
    """
    AAPL ABBV ABT ACN ADBE AIG AMAT AMD AMGN AMT AMZN AVGO AXP BA BAC BK BKNG
    BLK BMY BNY BRK.B C CAT CHTR CL CMCSA COF COP COST CRM CSCO CVS CVX DE DHR
    DIS DOW DUK EMR EXC F FDX GD GE GEV GILD GM GOOG GOOGL GS HD HONA IBM INTC
    INTU ISRG JNJ JPM KHC KO LIN LLY LMT LOW LRCX MA MCD MCK MDLZ MDT MET META
    MMM MO MRK MS MSFT MU NEE NFLX NKE NOW NVDA ORCL OXY PEP PFE PG PLTR PM QCOM
    RTX SBUX SCHW SO SPG T TMO TMUS TSLA TXN UBER UNH UNP UPS USB V VZ WFC WMT XOM
    """.split()
)

_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}(?:\.[A-Z])?$")


def normalize_symbol(value: str) -> str:
    return value.strip().upper().replace("-", ".")


def is_supported_symbol(value: str) -> bool:
    """Validate ticker formatting. Allows any valid 1-5 letter ticker symbol."""
    if not value or not isinstance(value, str):
        return False
    symbol = normalize_symbol(value)
    return bool(_SYMBOL_PATTERN.fullmatch(symbol))
