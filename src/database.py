import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
from .config import Config

class DatabaseManager:
    """Manages database connections and operations for the news ingestion pipeline."""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logging.info("Database connection closed")
    
    def create_tables(self):
        """Create the articles table with proper indexes."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            source VARCHAR(255) NOT NULL,
            url TEXT UNIQUE NOT NULL,
            publish_time TIMESTAMP,
            content TEXT,
            topic VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
        CREATE INDEX IF NOT EXISTS idx_articles_publish_time ON articles(publish_time);
        CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
        CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
        """
        
        try:
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            logging.info("Articles table created successfully")
        except Exception as e:
            logging.error(f"Failed to create tables: {e}")
            self.connection.rollback()
            raise
    
    def insert_article(self, article: Dict[str, Any]) -> bool:
        """Insert a single article into the database."""
        insert_sql = """
        INSERT INTO articles (title, source, url, publish_time, content, topic)
        VALUES (%(title)s, %(source)s, %(url)s, %(publish_time)s, %(content)s, %(topic)s)
        ON CONFLICT (url) DO NOTHING
        RETURNING id;
        """
        
        try:
            self.cursor.execute(insert_sql, article)
            result = self.cursor.fetchone()
            self.connection.commit()
            
            if result:
                logging.debug(f"Article inserted with ID: {result['id']}")
                return True
            else:
                logging.debug(f"Article already exists: {article['url']}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to insert article: {e}")
            self.connection.rollback()
            return False
    
    def insert_articles_batch(self, articles: List[Dict[str, Any]]) -> int:
        """Insert multiple articles in a batch operation."""
        if not articles:
            return 0
            
        insert_sql = """
        INSERT INTO articles (title, source, url, publish_time, content, topic)
        VALUES (%(title)s, %(source)s, %(url)s, %(publish_time)s, %(content)s, %(topic)s)
        ON CONFLICT (url) DO NOTHING
        """
        
        try:
            self.cursor.executemany(insert_sql, articles)
            rows_affected = self.cursor.rowcount
            self.connection.commit()
            logging.info(f"Batch insert completed: {rows_affected} articles inserted")
            return rows_affected
            
        except Exception as e:
            logging.error(f"Failed to insert articles batch: {e}")
            self.connection.rollback()
            return 0
    
    def get_recent_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent articles from the database."""
        select_sql = """
        SELECT * FROM articles 
        ORDER BY publish_time DESC 
        LIMIT %s
        """
        
        try:
            self.cursor.execute(select_sql, (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Failed to retrieve articles: {e}")
            return []
    
    def get_article_count_by_source(self) -> Dict[str, int]:
        """Get count of articles by source."""
        count_sql = """
        SELECT source, COUNT(*) as count 
        FROM articles 
        GROUP BY source 
        ORDER BY count DESC
        """
        
        try:
            self.cursor.execute(count_sql)
            results = self.cursor.fetchall()
            return {row['source']: row['count'] for row in results}
        except Exception as e:
            logging.error(f"Failed to get article counts: {e}")
            return {}