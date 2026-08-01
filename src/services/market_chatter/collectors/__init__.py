"""Collectors package for raw market chatter ingestion."""

from src.services.market_chatter.collectors.base import BaseCollector, RawItem
from src.services.market_chatter.collectors.news_collector import NewsCollector
from src.services.market_chatter.collectors.reddit_collector import RedditCollector
from src.services.market_chatter.collectors.stocktwits_collector import StockTwitsCollector
from src.services.market_chatter.collectors.twitter_collector import TwitterCollector

__all__ = [
    "BaseCollector",
    "RawItem",
    "RedditCollector",
    "StockTwitsCollector",
    "NewsCollector",
    "TwitterCollector",
]
