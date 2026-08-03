"""ETF Mapping Service — resolves sectors/industries/themes to ETF tickers.

Loads a static JSON mapping file once and provides deterministic
ETF resolution with a theme → industry → sector fallback chain.

Also maintains an expanded known-ETF universe used by is_etf() so common
funds (HYG, IWM, VOO, …) are never treated as single-name stocks.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ETF_MAPPINGS_FILE = Path(__file__).parent.parent.parent / "data" / "etf_mappings.json"

# Liquid / commonly discussed ETFs that may not appear in sector theme maps.
# Used only for classification (is_etf), not for theme→ETF recommendation.
_EXTRA_KNOWN_ETFS: frozenset[str] = frozenset(
    {
        # Broad market / indices
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "VOO",
        "VTI",
        "IVV",
        "SPLG",
        "VT",
        "VXUS",
        "IEFA",
        "EFA",
        "EEM",
        "VWO",
        "IEMG",
        "ACWI",
        # Sector SPDRs / peers
        "XLK",
        "XLF",
        "XLE",
        "XLV",
        "XLI",
        "XLY",
        "XLP",
        "XLU",
        "XLB",
        "XLRE",
        "XLC",
        "VGT",
        "VFH",
        "VDE",
        "VHT",
        "VIS",
        "VCR",
        "VDC",
        "VPU",
        "VAW",
        "VNQ",
        "VOX",
        # Bond / credit / rates
        "HYG",
        "JNK",
        "LQD",
        "TLT",
        "IEF",
        "SHY",
        "BND",
        "AGG",
        "TIP",
        "TIPS",
        "TBT",
        "TMF",
        "GOVT",
        "VCIT",
        "VCSH",
        "EMB",
        "BIL",
        "SGOV",
        # Commodities / alternatives
        "GLD",
        "IAU",
        "SLV",
        "USO",
        "UNG",
        "DBC",
        "PDBC",
        "DBA",
        "GDX",
        "GDXJ",
        # Thematic / industry
        "SMH",
        "SOXX",
        "IGV",
        "WCLD",
        "BOTZ",
        "ROBO",
        "HACK",
        "CIBR",
        "BUG",
        "ARKK",
        "ARKG",
        "ARKF",
        "ARKW",
        "ARKQ",
        "ARKX",
        "ICLN",
        "TAN",
        "QCLN",
        "LIT",
        "DRIV",
        "IDRV",
        "PBW",
        "KBE",
        "KRE",
        "KIE",
        "XRT",
        "RTH",
        "JETS",
        "PEJ",
        "IBB",
        "XBI",
        "BBH",
        "IHI",
        "PPH",
        "ITA",
        "PPA",
        "XAR",
        "PAVE",
        "IFRA",
        "SKYY",
        "NERD",
        "IPAY",
        "XOP",
        "OIH",
        "XME",
        # Country / region
        "MCHI",
        "EWT",
        "FXI",
        "KWEB",
        "EWJ",
        "EWZ",
        "INDA",
        # Volatility / leveraged common
        "VIXY",
        "UVXY",
        "SQQQ",
        "TQQQ",
        "SOXL",
        "SOXS",
        "SPXU",
        "UPRO",
        # Real estate / misc
        "IYR",
        "SCHH",
        "REM",
        "AMLP",
        "MLPA",
    }
)


class ETFMappingService:
    """Resolves sectors, industries, and themes to their representative ETFs.

    Uses a hardcoded JSON mapping for determinism and zero LLM cost.
    Loads the mapping file once and caches it in memory.
    """

    _loaded: bool = False
    _sector_etfs: dict[str, list[str]] = {}
    _industry_etfs: dict[str, list[str]] = {}
    _theme_etfs: dict[str, list[str]] = {}
    _all_etf_tickers: set[str] = set()

    def __init__(self) -> None:
        if not ETFMappingService._loaded:
            self._load()

    def _load(self) -> None:
        """Load ETF mappings from the JSON file."""
        if not _ETF_MAPPINGS_FILE.exists():
            logger.warning(f"ETF mappings file not found: {_ETF_MAPPINGS_FILE}")
            ETFMappingService._all_etf_tickers = set(_EXTRA_KNOWN_ETFS)
            ETFMappingService._loaded = True
            return

        try:
            with open(_ETF_MAPPINGS_FILE) as f:
                data = json.load(f)

            ETFMappingService._sector_etfs = {
                k.lower(): v for k, v in data.get("sector_etfs", {}).items()
            }
            ETFMappingService._industry_etfs = {
                k.lower(): v for k, v in data.get("industry_etfs", {}).items()
            }
            ETFMappingService._theme_etfs = {
                k.lower(): v for k, v in data.get("theme_etfs", {}).items()
            }

            # Optional explicit list in JSON plus mapped tickers plus extras
            tickers: set[str] = set(_EXTRA_KNOWN_ETFS)
            for raw in data.get("known_etfs", []) or []:
                if isinstance(raw, str) and raw.strip():
                    tickers.add(raw.strip().upper())
            for etf_list in ETFMappingService._sector_etfs.values():
                tickers.update(t.upper() for t in etf_list)
            for etf_list in ETFMappingService._industry_etfs.values():
                tickers.update(t.upper() for t in etf_list)
            for etf_list in ETFMappingService._theme_etfs.values():
                tickers.update(t.upper() for t in etf_list)

            ETFMappingService._all_etf_tickers = tickers
            ETFMappingService._loaded = True

            total_maps = (
                len(ETFMappingService._sector_etfs)
                + len(ETFMappingService._industry_etfs)
                + len(ETFMappingService._theme_etfs)
            )
            logger.info(
                f"Loaded {total_maps} ETF mapping groups and "
                f"{len(tickers)} known ETF tickers from {_ETF_MAPPINGS_FILE}"
            )
        except Exception as e:
            logger.error(f"Failed to load ETF mappings: {e}")
            ETFMappingService._all_etf_tickers = set(_EXTRA_KNOWN_ETFS)
            ETFMappingService._loaded = True

    def resolve_etfs(
        self,
        sector: str | None = None,
        industry: str | None = None,
        theme: str | None = None,
    ) -> list[str]:
        """Resolve ETFs for a given sector/industry/theme.

        Uses the most specific match available with fallback chain:
        theme → industry → sector.

        Returns a deduplicated list of ETF ticker symbols.
        """
        etfs: list[str] = []

        # Most specific first: theme-level ETFs
        if theme:
            theme_etfs = self._theme_etfs.get(theme.lower(), [])
            if theme_etfs:
                etfs.extend(theme_etfs)

        # Then industry-level ETFs
        if industry:
            industry_etfs = self._industry_etfs.get(industry.lower(), [])
            if industry_etfs:
                etfs.extend(industry_etfs)

        # Broadest: sector-level ETFs
        if sector:
            sector_etfs = self._sector_etfs.get(sector.lower(), [])
            if sector_etfs:
                etfs.extend(sector_etfs)

        # Deduplicate while preserving order (most specific first)
        seen: set[str] = set()
        unique: list[str] = []
        for etf in etfs:
            upper = etf.upper()
            if upper not in seen:
                seen.add(upper)
                unique.append(upper)

        return unique

    def resolve_etfs_for_themes(
        self,
        themes: list[dict],
    ) -> list[str]:
        """Resolve ETFs from a list of theme dicts (as returned by _match_themes
        or theme hierarchy).

        Each dict should have at minimum a 'name' key.
        Attempts to match at theme level, then walks up to industry/sector if the
        theme hierarchy data is available.

        Returns a deduplicated list of ETF tickers.
        """
        all_etfs: list[str] = []

        for theme_info in themes:
            name = theme_info.get("name", "")
            level = theme_info.get("level", "theme")
            # Try to resolve at whatever level this is
            if level == "sector":
                all_etfs.extend(self.resolve_etfs(sector=name))
            elif level == "industry":
                all_etfs.extend(self.resolve_etfs(industry=name))
            else:
                all_etfs.extend(self.resolve_etfs(theme=name))

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for etf in all_etfs:
            if etf not in seen:
                seen.add(etf)
                unique.append(etf)

        return unique

    def resolve_etfs_for_text(self, text: str) -> list[str]:
        """Match unstructured text (e.g. transcript narratives or mention text)
        against taxonomy keywords to resolve ETFs.

        Returns a deduplicated list of ETF ticker symbols.
        """
        text_lower = text.lower()
        matched_etfs: list[str] = []

        # 1. Match theme-level names
        for theme_name, etfs in self._theme_etfs.items():
            if theme_name in text_lower:
                matched_etfs.extend(etfs)

        # 2. Match industry-level names / keywords
        for ind_name, etfs in self._industry_etfs.items():
            kw = ind_name.split("/")[0].split("&")[0].strip()
            if kw.lower() in text_lower or ind_name in text_lower:
                matched_etfs.extend(etfs)

        # 3. Match sector-level names / keywords
        for sec_name, etfs in self._sector_etfs.items():
            kw = sec_name.split("/")[0].strip()
            if kw.lower() in text_lower or sec_name in text_lower:
                matched_etfs.extend(etfs)

        seen: set[str] = set()
        unique: list[str] = []
        for etf in matched_etfs:
            upper = etf.upper()
            if upper not in seen:
                seen.add(upper)
                unique.append(upper)

        return unique

    def get_all_etf_tickers(self) -> set[str]:
        """Return the full set of known ETF tickers (mappings + extras).

        Cached after load — used for is_etf classification.
        """
        if not ETFMappingService._loaded:
            self._load()
        return set(ETFMappingService._all_etf_tickers)

    def is_etf(self, ticker: str | None) -> bool:
        """Check if a ticker is a known ETF (not a single-name equity)."""
        if not ticker:
            return False
        if not ETFMappingService._loaded:
            self._load()
        return ticker.strip().upper() in ETFMappingService._all_etf_tickers

    def get_themes_for_etf(self, etf_ticker: str) -> list[str]:
        """Reverse lookup: given an ETF ticker, find which themes it maps to.

        Useful for the ETF detail page — when a user views SMH, we can
        show all semiconductor-related predictions.
        """
        etf_upper = etf_ticker.upper()
        matched_themes: list[str] = []

        for theme_name, etfs in self._theme_etfs.items():
            if etf_upper in [e.upper() for e in etfs]:
                matched_themes.append(theme_name)

        for industry_name, etfs in self._industry_etfs.items():
            if etf_upper in [e.upper() for e in etfs]:
                matched_themes.append(industry_name)

        for sector_name, etfs in self._sector_etfs.items():
            if etf_upper in [e.upper() for e in etfs]:
                matched_themes.append(sector_name)

        return matched_themes
