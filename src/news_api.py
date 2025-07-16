import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .config import Config

class NewsAPIClient:
    """Client for fetching articles from NewsAPI."""
    
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = Config.NEWS_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'X-Api-Key': self.api_key,
            'User-Agent': 'AI News App/1.0'
        })
    
    def fetch_everything(self, 
                        query: str = None,
                        language: str = None,
                        from_date: datetime = None,
                        to_date: datetime = None,
                        page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch articles using the 'everything' endpoint with filters.
        
        Args:
            query: Keywords or phrases to search for
            language: Language code (e.g., 'en', 'es', 'fr')
            from_date: Start date for articles
            to_date: End date for articles
            page_size: Number of articles per page (max 100)
        
        Returns:
            List of normalized article dictionaries
        """
        url = f"{self.base_url}/everything"
        
        # Set default values
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        if from_date is None:
            from_date = datetime.now() - timedelta(days=Config.DEFAULT_DAYS_BACK)
        
        if to_date is None:
            to_date = datetime.now()
        
        params = {
            'language': language,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'pageSize': min(page_size, 100),  # API limit is 100
            'sortBy': 'publishedAt'
        }
        
        if query:
            params['q'] = query
        
        articles = []
        page = 1
        
        try:
            while True:
                params['page'] = page
                
                logging.info(f"Fetching NewsAPI page {page} with params: {params}")
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data['status'] != 'ok':
                    logging.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                    break
                
                page_articles = data.get('articles', [])
                if not page_articles:
                    break
                
                # Normalize the articles
                normalized_articles = [self._normalize_article(article, 'NewsAPI') 
                                     for article in page_articles]
                articles.extend(normalized_articles)
                
                logging.info(f"Fetched {len(page_articles)} articles from page {page}")
                
                # Check if we've reached the end
                total_results = data.get('totalResults', 0)
                if len(articles) >= total_results or len(page_articles) < page_size:
                    break
                
                page += 1
                
                # Safety limit to avoid infinite loops
                if page > 10:  # Max 1000 articles (10 pages * 100 articles)
                    logging.warning("Reached maximum page limit for NewsAPI")
                    break
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch from NewsAPI: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while fetching from NewsAPI: {e}")
        
        logging.info(f"Total articles fetched from NewsAPI: {len(articles)}")
        return articles
    
    def fetch_top_headlines(self, 
                           country: str = None,
                           category: str = None,
                           language: str = None,
                           page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch top headlines using the 'top-headlines' endpoint.
        
        Args:
            country: Country code (e.g., 'us', 'gb', 'ca')
            category: Category (business, entertainment, general, health, science, sports, technology)
            language: Language code
            page_size: Number of articles per page
        
        Returns:
            List of normalized article dictionaries
        """
        url = f"{self.base_url}/top-headlines"
        
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        params = {
            'language': language,
            'pageSize': min(page_size, 100)
        }
        
        if country:
            params['country'] = country
        if category:
            params['category'] = category
        
        try:
            logging.info(f"Fetching top headlines with params: {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'ok':
                logging.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get('articles', [])
            normalized_articles = [self._normalize_article(article, 'NewsAPI-Headlines') 
                                 for article in articles]
            
            logging.info(f"Fetched {len(normalized_articles)} top headlines")
            return normalized_articles
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch top headlines: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error while fetching top headlines: {e}")
            return []
    
    def _normalize_article(self, article: Dict[str, Any], source_prefix: str = 'NewsAPI') -> Dict[str, Any]:
        """
        Normalize article data to a standard format.
        
        Args:
            article: Raw article data from NewsAPI
            source_prefix: Prefix to add to the source name
        
        Returns:
            Normalized article dictionary
        """
        # Parse publish time
        publish_time = None
        if article.get('publishedAt'):
            try:
                publish_time = datetime.fromisoformat(
                    article['publishedAt'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                logging.warning(f"Failed to parse publish time: {article.get('publishedAt')}")
        
        # Extract source name
        source_name = source_prefix
        if article.get('source') and article['source'].get('name'):
            source_name = f"{source_prefix}-{article['source']['name']}"
        
        # Determine topic (basic categorization based on source or content)
        topic = self._extract_topic(article, source_name)
        
        return {
            'title': article.get('title', '').strip(),
            'source': source_name,
            'url': article.get('url', ''),
            'publish_time': publish_time,
            'content': article.get('content', '') or article.get('description', ''),
            'topic': topic
        }
    
    def _extract_topic(self, article: Dict[str, Any], source_name: str) -> str:
        """
        Extract topic from article based on source and content.
        
        Args:
            article: Article data
            source_name: Name of the source
        
        Returns:
            Topic string
        """
        # Simple topic extraction based on source
        source_lower = source_name.lower()
        
        if 'techcrunch' in source_lower or 'tech' in source_lower:
            return 'technology'
        elif 'business' in source_lower or 'financial' in source_lower:
            return 'business'
        elif 'sports' in source_lower:
            return 'sports'
        elif 'health' in source_lower or 'medical' in source_lower:
            return 'health'
        elif 'science' in source_lower:
            return 'science'
        else:
            return 'general'