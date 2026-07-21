"""FastAPI dependency injection — provides services and DB sessions to route handlers."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.aggregation_service import AggregationService
from src.services.embedding_service import OpenAIEmbeddingService
from src.services.interfaces import EmbeddingProvider, LLMProvider, MarketDataSource
from src.services.llm_service import AnthropicLLMService
from src.services.llm_service import OpenAILLMService
from src.services.market_data_service import YFinanceMarketDataService
from src.services.search_service import SearchService
from src.services.theme_service import ThemeService


from src.config import get_settings

settings = get_settings()

# --- Service singletons (lazily initialized) ---

_llm_provider: LLMProvider | None = None
_embedding_provider: EmbeddingProvider | None = None
_market_data: MarketDataSource | None = None


def get_llm_provider() -> LLMProvider:
    global _llm_provider
    if _llm_provider is None:
        if settings.anthropic_api_key:
            _llm_provider = AnthropicLLMService()
        else:
            _llm_provider = OpenAILLMService()
    return _llm_provider


def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = OpenAIEmbeddingService()
    return _embedding_provider


def get_market_data() -> MarketDataSource:
    global _market_data
    if _market_data is None:
        _market_data = YFinanceMarketDataService()
    return _market_data


# --- Per-request dependencies ---


def get_theme_service(db: AsyncSession = Depends(get_db)) -> ThemeService:
    return ThemeService(db)


def get_search_service(
    db: AsyncSession = Depends(get_db),
    embedding: EmbeddingProvider = Depends(get_embedding_provider),
) -> SearchService:
    return SearchService(db, embedding)


def get_aggregation_service(
    db: AsyncSession = Depends(get_db),
) -> AggregationService:
    return AggregationService(db)
