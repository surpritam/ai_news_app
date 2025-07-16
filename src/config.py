import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the news ingestion pipeline."""
    
    # NewsAPI configuration
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    NEWS_API_BASE_URL = 'https://newsapi.org/v2'
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'ai_news_app')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Default settings
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
    DEFAULT_DAYS_BACK = int(os.getenv('DEFAULT_DAYS_BACK', 7))
    
    # RSS feed URLs for major news sources
    RSS_FEEDS = {
        'BBC': 'http://feeds.bbci.co.uk/news/rss.xml',
        'TechCrunch': 'https://techcrunch.com/feed/',
        'New York Times': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'
    }
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.NEWS_API_KEY:
            raise ValueError("NEWS_API_KEY environment variable is required")
        if not cls.DB_PASSWORD:
            raise ValueError("DB_PASSWORD environment variable is required")
        return True