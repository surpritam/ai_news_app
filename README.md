# AI News App - News Ingestion Pipeline

A Python-based news ingestion system that fetches articles from NewsAPI and RSS feeds, normalizes the data, and stores them in a PostgreSQL database.

## Features

- **NewsAPI Integration**: Fetches articles with language and date filters
- **RSS Feed Parsing**: Supports major news sources (BBC, NYT, TechCrunch)
- **Data Normalization**: Standardizes article fields (title, source, URL, publish time, content)
- **PostgreSQL Storage**: Stores articles with indexed fields (topic, source, date)
- **Configurable Pipeline**: Environment-based configuration
- **Comprehensive Logging**: Detailed logging and error handling

## Requirements

- Python 3.7+
- PostgreSQL 12+
- NewsAPI key (get from https://newsapi.org/)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai_news_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Configure your `.env` file with:
   - `NEWS_API_KEY`: Your NewsAPI key
   - `DB_*`: PostgreSQL connection details

5. Set up the database:
```bash
python setup_db.py
```

## Usage

### Basic Usage

Run the complete pipeline:
```bash
python src/main.py
```

### Advanced Options

```bash
# Skip NewsAPI ingestion
python src/main.py --no-newsapi

# Skip RSS feed ingestion  
python src/main.py --no-rss

# Search for specific topics
python src/main.py --query "technology"

# Fetch articles from last 3 days
python src/main.py --days-back 3

# Enable verbose logging
python src/main.py --verbose
```

## Configuration

The pipeline is configured through environment variables:

### Required Variables
- `NEWS_API_KEY`: Your NewsAPI key
- `DB_PASSWORD`: PostgreSQL password

### Optional Variables
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: ai_news_app)
- `DB_USER`: Database user (default: postgres)
- `DEFAULT_LANGUAGE`: Language filter (default: en)
- `DEFAULT_DAYS_BACK`: Days to fetch back (default: 7)

## RSS Feeds

The pipeline currently supports these RSS feeds:
- **BBC**: http://feeds.bbci.co.uk/news/rss.xml
- **TechCrunch**: https://techcrunch.com/feed/
- **New York Times**: https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml

Additional feeds can be added in `src/config.py`.

## Database Schema

The `articles` table includes:
- `id`: Primary key
- `title`: Article title
- `source`: News source name
- `url`: Article URL (unique)
- `publish_time`: Publication timestamp
- `content`: Article content/description
- `topic`: Article category/topic
- `created_at`: Record creation timestamp

Indexes are created on: `source`, `publish_time`, `topic`, `created_at`

## Architecture

```
src/
├── __init__.py          # Package initialization
├── config.py           # Configuration management
├── database.py         # Database operations
├── news_api.py         # NewsAPI client
├── rss_parser.py       # RSS feed parser
└── main.py            # Main pipeline script

setup_db.py             # Database setup script
requirements.txt        # Python dependencies
.env.example           # Environment variables template
```

## Logging

Logs are written to both console and `news_ingestion.log` file. Use `--verbose` flag for debug-level logging.

## Error Handling

The pipeline includes comprehensive error handling:
- Invalid RSS feeds are skipped with warnings
- API rate limits and network errors are handled gracefully
- Database connection issues are logged and reported
- Duplicate articles (same URL) are ignored

## Development

To extend the pipeline:

1. **Add new RSS feeds**: Update `RSS_FEEDS` in `src/config.py`
2. **Add new news sources**: Implement additional clients similar to `news_api.py`
3. **Modify data schema**: Update database schema in `database.py`
4. **Add new topics**: Extend topic extraction logic in parsers