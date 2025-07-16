import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from .config import Config

class RSSParser:
    """Parser for RSS feeds from major news sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI News App RSS Parser/1.0'
        })
    
    def parse_all_feeds(self) -> List[Dict[str, Any]]:
        """
        Parse all configured RSS feeds and return normalized articles.
        
        Returns:
            List of normalized article dictionaries from all feeds
        """
        all_articles = []
        
        for source_name, feed_url in Config.RSS_FEEDS.items():
            logging.info(f"Parsing RSS feed for {source_name}: {feed_url}")
            articles = self.parse_feed(feed_url, source_name)
            all_articles.extend(articles)
            logging.info(f"Fetched {len(articles)} articles from {source_name}")
        
        logging.info(f"Total articles from all RSS feeds: {len(all_articles)}")
        return all_articles
    
    def parse_feed(self, feed_url: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Parse a single RSS feed and return normalized articles.
        
        Args:
            feed_url: URL of the RSS feed
            source_name: Name of the news source
        
        Returns:
            List of normalized article dictionaries
        """
        try:
            # Fetch the RSS feed
            response = self.session.get(feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logging.warning(f"RSS feed has parsing issues for {source_name}: {feed.bozo_exception}")
            
            # Normalize entries
            articles = []
            for entry in feed.entries:
                article = self._normalize_rss_entry(entry, source_name)
                if article and article['url']:  # Only add articles with valid URLs
                    articles.append(article)
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch RSS feed for {source_name}: {e}")
            return []
        except Exception as e:
            logging.error(f"Failed to parse RSS feed for {source_name}: {e}")
            return []
    
    def _normalize_rss_entry(self, entry: Any, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Normalize an RSS entry to a standard article format.
        
        Args:
            entry: RSS entry object from feedparser
            source_name: Name of the news source
        
        Returns:
            Normalized article dictionary or None if invalid
        """
        try:
            # Extract title
            title = getattr(entry, 'title', '').strip()
            if not title:
                logging.warning(f"Entry missing title from {source_name}")
                return None
            
            # Extract URL
            url = getattr(entry, 'link', '').strip()
            if not url:
                logging.warning(f"Entry missing URL from {source_name}: {title}")
                return None
            
            # Parse publish time
            publish_time = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    import time
                    timestamp = time.mktime(entry.published_parsed)
                    publish_time = datetime.fromtimestamp(timestamp)
                except (ValueError, TypeError, OverflowError):
                    logging.warning(f"Failed to parse publish time for {title}")
            
            # If no published_parsed, try published string
            if not publish_time and hasattr(entry, 'published'):
                publish_time = self._parse_date_string(entry.published)
            
            # Extract content
            content = ''
            if hasattr(entry, 'content') and entry.content:
                # Content is usually a list of content objects
                if isinstance(entry.content, list) and entry.content:
                    content = entry.content[0].get('value', '')
            
            # Fallback to summary/description
            if not content:
                content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            
            # Clean HTML tags from content
            content = self._clean_html(content)
            
            # Determine topic based on source and content
            topic = self._extract_topic_from_rss(entry, source_name)
            
            return {
                'title': title,
                'source': source_name,
                'url': url,
                'publish_time': publish_time,
                'content': content,
                'topic': topic
            }
            
        except Exception as e:
            logging.error(f"Failed to normalize RSS entry from {source_name}: {e}")
            return None
    
    def _parse_date_string(self, date_string: str) -> Optional[datetime]:
        """
        Parse various date string formats to datetime.
        
        Args:
            date_string: Date string in various formats
        
        Returns:
            Parsed datetime object or None
        """
        # Common RSS date formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
            '%a, %d %b %Y %H:%M:%S GMT',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        logging.warning(f"Failed to parse date string: {date_string}")
        return None
    
    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags and clean up text content.
        
        Args:
            text: Text that may contain HTML
        
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Simple HTML tag removal (for production, consider using BeautifulSoup)
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_topic_from_rss(self, entry: Any, source_name: str) -> str:
        """
        Extract topic from RSS entry based on categories, tags, or source.
        
        Args:
            entry: RSS entry object
            source_name: Name of the news source
        
        Returns:
            Topic string
        """
        # Check for categories/tags in the entry
        if hasattr(entry, 'tags') and entry.tags:
            # Use the first tag as topic
            first_tag = entry.tags[0].get('term', '').lower()
            if first_tag:
                return first_tag
        
        # Check for category
        if hasattr(entry, 'category'):
            return entry.category.lower()
        
        # Source-based topic extraction
        source_lower = source_name.lower()
        
        if 'techcrunch' in source_lower:
            return 'technology'
        elif 'bbc' in source_lower:
            # BBC has various sections
            if hasattr(entry, 'link'):
                link = entry.link.lower()
                if '/business/' in link:
                    return 'business'
                elif '/technology/' in link:
                    return 'technology'
                elif '/science/' in link:
                    return 'science'
                elif '/health/' in link:
                    return 'health'
                elif '/sport/' in link:
                    return 'sports'
            return 'general'
        elif 'nytimes' in source_lower or 'nyt' in source_lower:
            # Try to extract from URL structure
            if hasattr(entry, 'link'):
                link = entry.link.lower()
                if '/business/' in link:
                    return 'business'
                elif '/technology/' in link or '/tech/' in link:
                    return 'technology'
                elif '/science/' in link:
                    return 'science'
                elif '/health/' in link:
                    return 'health'
                elif '/sports/' in link:
                    return 'sports'
            return 'general'
        else:
            return 'general'
    
    def validate_feed_url(self, feed_url: str) -> bool:
        """
        Validate that a feed URL is accessible and contains valid RSS/Atom content.
        
        Args:
            feed_url: URL of the RSS feed to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            response = self.session.get(feed_url, timeout=10)
            response.raise_for_status()
            
            # Try to parse the feed
            feed = feedparser.parse(response.content)
            
            # Check if it's a valid feed with entries
            return len(feed.entries) > 0
            
        except Exception as e:
            logging.error(f"Feed validation failed for {feed_url}: {e}")
            return False