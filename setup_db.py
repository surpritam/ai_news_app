#!/usr/bin/env python3
"""
Database setup script for the AI News App.

This script creates the necessary database and tables for the news ingestion pipeline.
"""

import sys
import logging
from src.config import Config
from src.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Create database tables and indexes."""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")
        
        # Connect to database
        db_manager = DatabaseManager()
        db_manager.connect()
        logger.info("Connected to database successfully")
        
        # Create tables
        db_manager.create_tables()
        logger.info("Database tables created successfully")
        
        # Test the connection by getting current stats
        stats = db_manager.get_article_count_by_source()
        logger.info(f"Current article counts: {stats}")
        
        db_manager.disconnect()
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()