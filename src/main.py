#!/usr/bin/env python3
"""
News Ingestion Pipeline

This script fetches articles from NewsAPI and RSS feeds, normalizes the data,
and stores them in a PostgreSQL database.
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

from .config import Config
from .database import DatabaseManager
from .news_api import NewsAPIClient
from .rss_parser import RSSParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('news_ingestion.log')
    ]
)

logger = logging.getLogger(__name__)

class NewsIngestionPipeline:
    """Main pipeline for ingesting news articles from various sources."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.news_api_client = NewsAPIClient()
        self.rss_parser = RSSParser()
        
    def run(self, 
            fetch_newsapi: bool = True, 
            fetch_rss: bool = True,
            newsapi_query: str = None,
            days_back: int = None) -> Dict[str, Any]:
        """
        Run the complete news ingestion pipeline.
        
        Args:
            fetch_newsapi: Whether to fetch from NewsAPI
            fetch_rss: Whether to fetch from RSS feeds
            newsapi_query: Optional query string for NewsAPI
            days_back: Number of days back to fetch (default from config)
        
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            'start_time': datetime.now(),
            'newsapi_articles': 0,
            'rss_articles': 0,
            'total_fetched': 0,
            'total_stored': 0,
            'errors': []
        }
        
        try:
            # Validate configuration
            Config.validate()
            logger.info("Configuration validated successfully")
            
            # Connect to database
            self.db_manager.connect()
            
            # Create tables if they don't exist
            self.db_manager.create_tables()
            
            all_articles = []
            
            # Fetch from NewsAPI
            if fetch_newsapi:
                try:
                    logger.info("Starting NewsAPI ingestion...")
                    newsapi_articles = self._fetch_from_newsapi(newsapi_query, days_back)
                    all_articles.extend(newsapi_articles)
                    stats['newsapi_articles'] = len(newsapi_articles)
                    logger.info(f"NewsAPI ingestion completed: {len(newsapi_articles)} articles")
                except Exception as e:
                    error_msg = f"NewsAPI ingestion failed: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Fetch from RSS feeds
            if fetch_rss:
                try:
                    logger.info("Starting RSS feed ingestion...")
                    rss_articles = self.rss_parser.parse_all_feeds()
                    all_articles.extend(rss_articles)
                    stats['rss_articles'] = len(rss_articles)
                    logger.info(f"RSS ingestion completed: {len(rss_articles)} articles")
                except Exception as e:
                    error_msg = f"RSS ingestion failed: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Store articles in database
            if all_articles:
                logger.info(f"Storing {len(all_articles)} articles in database...")
                
                # Filter out articles with missing required fields
                valid_articles = self._filter_valid_articles(all_articles)
                logger.info(f"Valid articles after filtering: {len(valid_articles)}")
                
                # Store in database
                stored_count = self.db_manager.insert_articles_batch(valid_articles)
                stats['total_stored'] = stored_count
                
                logger.info(f"Database storage completed: {stored_count} articles stored")
            
            stats['total_fetched'] = len(all_articles)
            stats['end_time'] = datetime.now()
            stats['duration'] = stats['end_time'] - stats['start_time']
            
            # Log final statistics
            self._log_statistics(stats)
            
            return stats
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            raise
        finally:
            # Always disconnect from database
            self.db_manager.disconnect()
    
    def _fetch_from_newsapi(self, query: str = None, days_back: int = None) -> List[Dict[str, Any]]:
        """Fetch articles from NewsAPI."""
        if days_back is None:
            days_back = Config.DEFAULT_DAYS_BACK
        
        from_date = datetime.now() - timedelta(days=days_back)
        
        # Fetch general articles
        articles = self.news_api_client.fetch_everything(
            query=query,
            from_date=from_date
        )
        
        # Also fetch top headlines
        headlines = self.news_api_client.fetch_top_headlines()
        articles.extend(headlines)
        
        return articles
    
    def _filter_valid_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out articles with missing required fields."""
        valid_articles = []
        
        for article in articles:
            # Check required fields
            if not article.get('title') or not article.get('url'):
                logger.debug(f"Skipping article with missing title or URL: {article}")
                continue
            
            # Ensure source is present
            if not article.get('source'):
                article['source'] = 'Unknown'
            
            # Ensure topic is present
            if not article.get('topic'):
                article['topic'] = 'general'
            
            valid_articles.append(article)
        
        return valid_articles
    
    def _log_statistics(self, stats: Dict[str, Any]):
        """Log detailed statistics about the ingestion process."""
        logger.info("=== News Ingestion Pipeline Statistics ===")
        logger.info(f"Start time: {stats['start_time']}")
        logger.info(f"End time: {stats['end_time']}")
        logger.info(f"Duration: {stats['duration']}")
        logger.info(f"NewsAPI articles fetched: {stats['newsapi_articles']}")
        logger.info(f"RSS articles fetched: {stats['rss_articles']}")
        logger.info(f"Total articles fetched: {stats['total_fetched']}")
        logger.info(f"Total articles stored: {stats['total_stored']}")
        
        if stats['errors']:
            logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                logger.warning(f"  - {error}")
        
        # Get database statistics
        try:
            self.db_manager.connect()
            source_counts = self.db_manager.get_article_count_by_source()
            logger.info("Articles by source:")
            for source, count in source_counts.items():
                logger.info(f"  {source}: {count}")
            self.db_manager.disconnect()
        except Exception as e:
            logger.warning(f"Failed to get database statistics: {e}")

def main():
    """Main entry point for the news ingestion pipeline."""
    parser = argparse.ArgumentParser(description='News Ingestion Pipeline')
    parser.add_argument('--no-newsapi', action='store_true', 
                       help='Skip NewsAPI ingestion')
    parser.add_argument('--no-rss', action='store_true', 
                       help='Skip RSS feed ingestion')
    parser.add_argument('--query', type=str, 
                       help='Query string for NewsAPI search')
    parser.add_argument('--days-back', type=int, 
                       help='Number of days back to fetch articles')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting news ingestion pipeline...")
    
    try:
        pipeline = NewsIngestionPipeline()
        stats = pipeline.run(
            fetch_newsapi=not args.no_newsapi,
            fetch_rss=not args.no_rss,
            newsapi_query=args.query,
            days_back=args.days_back
        )
        
        if stats['errors']:
            logger.error("Pipeline completed with errors")
            sys.exit(1)
        else:
            logger.info("Pipeline completed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()