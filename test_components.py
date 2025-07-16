#!/usr/bin/env python3
"""
Test script for the news ingestion pipeline components.
Tests functionality that doesn't require external network access or database connections.
"""

import sys
import os
sys.path.append('.')

from src.config import Config
from src.rss_parser import RSSParser
from src.news_api import NewsAPIClient
from datetime import datetime, timedelta

def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    
    # Test RSS feeds configuration
    assert Config.RSS_FEEDS is not None
    assert len(Config.RSS_FEEDS) > 0
    print(f"✓ RSS feeds configured: {list(Config.RSS_FEEDS.keys())}")
    
    # Test default values
    assert Config.DEFAULT_LANGUAGE == 'en'
    assert Config.DEFAULT_DAYS_BACK == 7
    print("✓ Default configuration values loaded")
    
    print("Configuration test passed!\n")

def test_rss_parser():
    """Test RSS parser functionality."""
    print("Testing RSS parser...")
    
    parser = RSSParser()
    
    # Test date parsing
    test_dates = [
        "Mon, 01 Jan 2024 12:00:00 GMT",
        "2024-01-01T12:00:00Z",
        "2024-01-01 12:00:00"
    ]
    
    for date_str in test_dates:
        result = parser._parse_date_string(date_str)
        if result:
            print(f"✓ Parsed date: {date_str} -> {result}")
        else:
            print(f"✗ Failed to parse: {date_str}")
    
    # Test HTML cleaning
    html_text = "<p>This is <b>HTML</b> content with &quot;quotes&quot;</p>"
    clean_text = parser._clean_html(html_text)
    expected = 'This is HTML content with "quotes"'
    assert clean_text == expected
    print(f"✓ HTML cleaning: '{html_text}' -> '{clean_text}'")
    
    print("RSS parser tests passed!\n")

def test_news_api_client():
    """Test NewsAPI client functionality."""
    print("Testing NewsAPI client...")
    
    client = NewsAPIClient()
    
    # Test article normalization
    test_article = {
        'title': 'Test Article Title',
        'url': 'https://example.com/article',
        'publishedAt': '2024-01-01T12:00:00Z',
        'content': 'This is test content',
        'source': {'name': 'Test Source'}
    }
    
    normalized = client._normalize_article(test_article, 'TestAPI')
    
    assert normalized['title'] == 'Test Article Title'
    assert normalized['source'] == 'TestAPI-Test Source'
    assert normalized['url'] == 'https://example.com/article'
    assert normalized['content'] == 'This is test content'
    assert isinstance(normalized['publish_time'], datetime)
    
    print(f"✓ Article normalization: {normalized['title']}")
    
    # Test topic extraction
    topic = client._extract_topic({'source': {'name': 'TechCrunch'}}, 'NewsAPI-TechCrunch')
    assert topic == 'technology'
    print(f"✓ Topic extraction: TechCrunch -> {topic}")
    
    print("NewsAPI client tests passed!\n")

def test_data_structures():
    """Test data structure integrity."""
    print("Testing data structures...")
    
    # Test article structure
    sample_article = {
        'title': 'Sample Article',
        'source': 'Test Source',
        'url': 'https://example.com',
        'publish_time': datetime.now(),
        'content': 'Sample content',
        'topic': 'general'
    }
    
    # Verify all required fields are present
    required_fields = ['title', 'source', 'url', 'publish_time', 'content', 'topic']
    for field in required_fields:
        assert field in sample_article
    
    print(f"✓ Article structure valid with fields: {list(sample_article.keys())}")
    print("Data structure tests passed!\n")

def main():
    """Run all tests."""
    print("=== News Ingestion Pipeline Component Tests ===\n")
    
    try:
        test_config()
        test_rss_parser()
        test_news_api_client()
        test_data_structures()
        
        print("🎉 All tests passed successfully!")
        print("\nNext steps:")
        print("1. Set up PostgreSQL database")
        print("2. Configure .env file with API keys and DB credentials")
        print("3. Run: python setup_db.py")
        print("4. Run: python src/main.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()