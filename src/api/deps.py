"""FastAPI dependency injection - provides services and DB sessions to route handlers."""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db
from src.services.aggregation_service import AggregationService
from src.services.embedding_service import OpenAIEmbeddingService
from src.services.finbert_service import FinBertService
from src.services.interfaces import EmbeddingProvider, LLMProvider, MarketDataSource
from src.services.llm_service import AnthropicLLMService, OpenAILLMService
from src.services.market_data_service import YFinanceMarketDataService
from src.services.query_router import QueryRouter
from src.services.search_answer_service import SearchAnswerService
from src.services.search_coverage_service import SearchCoverageService
from src.services.search_service import SearchService
from src.services.social_context_service import SocialContextService
from src.services.theme_service import ThemeService

settings = get_settings()

# --- Service singletons (lazily initialized) ---

_llm_provider: LLMProvider | None = None
_embedding_provider: EmbeddingProvider | None = None
_market_data: MarketDataSource | None = None
_query_router: QueryRouter | None = None
_finbert_service: FinBertService | None = None


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


def get_query_router() -> QueryRouter:
    global _query_router
    if _query_router is None:
        _query_router = QueryRouter()
    return _query_router


def get_finbert_service() -> FinBertService:
    global _finbert_service
    if _finbert_service is None:
        _finbert_service = FinBertService()
    return _finbert_service


# --- Per-request dependencies ---


def _tickerflow_service_getter(request: Request):
    """Lazily resolve the TickerFlow CollectionService from app.state."""
    return getattr(request.app.state, "tickerflow_service", None)


def get_social_context_service(request: Request) -> SocialContextService:
    """TickerFlow social-context fetcher backed by the lifespan-initialised service."""
    return SocialContextService(lambda: _tickerflow_service_getter(request))


def get_theme_service(db: AsyncSession = Depends(get_db)) -> ThemeService:
    return ThemeService(db)


def get_search_service(
    db: AsyncSession = Depends(get_db),
    embedding: EmbeddingProvider = Depends(get_embedding_provider),
) -> SearchService:
    return SearchService(db, embedding)


def get_search_answer_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    embedding: EmbeddingProvider = Depends(get_embedding_provider),
    social: SocialContextService = Depends(get_social_context_service),
) -> SearchAnswerService:
    return SearchAnswerService(
        db, embedding, coverage_service=SearchCoverageService(db, embedding), social_service=social
    )


def get_search_coverage_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
    embedding: EmbeddingProvider = Depends(get_embedding_provider),
    social: SocialContextService = Depends(get_social_context_service),
) -> SearchCoverageService:
    return SearchCoverageService(db, embedding, social_service=social)


def get_aggregation_service(
    db: AsyncSession = Depends(get_db),
) -> AggregationService:
    return AggregationService(db)
