"""
AI News App - News Ingestion Pipeline

A Python-based news ingestion system that fetches articles from NewsAPI and RSS feeds,
normalizes the data, and stores them in a PostgreSQL database.
"""

__version__ = "1.0.0"
__author__ = "AI News App Team"

from .config import Config
from .database import DatabaseManager
from .news_api import NewsAPIClient
from .rss_parser import RSSParser

__all__ = [
    'Config',
    'DatabaseManager', 
    'NewsAPIClient',
    'RSSParser'
]