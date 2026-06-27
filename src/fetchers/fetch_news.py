# fetch_news.py
import os
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.db.database import engine, Article, Base
import logging
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from src.config import (
    NEWSAPI_KEY,
    FINNHUB_KEY,
    NEWS_TICKERS,
    NEWS_RETRY_TOTAL,
    NEWS_RETRY_BACKOFF,
    NEWS_STATUS_FORCELIST,
    NEWS_LOG_PATH
)

# Setup logging to track what happens
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(NEWS_LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure HTTP session with retries
http_session = requests.Session()
retries = Retry(
    total=NEWS_RETRY_TOTAL,
    backoff_factor=NEWS_RETRY_BACKOFF,
    status_forcelist=NEWS_STATUS_FORCELIST
)
http_session.mount("http://", HTTPAdapter(max_retries=retries))
http_session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_news_from_newsapi(ticker, days=7):
    """
    Fetch news articles from NewsAPI for a given ticker
    
    Args:
        ticker: Stock symbol (e.g., "AAPL")
        days: How many days back to search (default: last 7 days)
    
    Returns:
        List of article dictionaries
    """
    url = "https://newsapi.org/v2/everything"
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    params = {
        "q": ticker,  # Search query
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "sortBy": "publishedAt",  # Newest first
        "language": "en",
        "apiKey": NEWSAPI_KEY
    }
    
    try:
        logger.info(f"Fetching NewsAPI articles for {ticker}")
        response = http_session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data["status"] != "ok":
            logger.error(f"NewsAPI error: {data.get('message')}")
            return []
        
        articles = data.get("articles", [])
        logger.info(f"Fetched {len(articles)} articles for {ticker}")
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from NewsAPI: {e}")
        return []

def fetch_news_from_finnhub(ticker):
    """
    Fetch news from Finnhub API for a given ticker
    
    Args:
        ticker: Stock symbol
    
    Returns:
        List of news dictionaries
    """
    url = "https://finnhub.io/api/v1/company-news"
    
    params = {
        "symbol": ticker,
        "token": FINNHUB_KEY,
        "limit": 50  # Max articles per request
    }
    
    try:
        logger.info(f"Fetching Finnhub news for {ticker}")
        response = http_session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        news_items = response.json()
        logger.info(f"Fetched {len(news_items)} news items for {ticker}")
        
        # Finnhub returns a list directly, not wrapped in an object
        return news_items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from Finnhub: {e}")
        return []
    
def parse_and_validate_newsapi_article(article, ticker):
    """
    Convert NewsAPI article to database format and validate
    
    Returns:
        Article object or None if invalid
    """
    try:
        # Validate required fields
        if not article.get("title") or not article.get("content"):
            return None
        
        # Check for paywalls
        content = article.get("content", "")
        if "[+" in content or "requires subscription" in content.lower():
            return None
        
        # Parse publish date
        published_at = article.get("publishedAt", "")
        try:
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except:
            pub_date = datetime.now()
        
        # Create Article object
        article_obj = Article(
            ticker=ticker,
            title=article.get("title", "")[:500],  # Cap at 500 chars
            content=article.get("content", ""),
            source=article.get("source", {}).get("name", "Unknown"),
            published_date=pub_date,
            fetched_date=datetime.now()
        )
        
        return article_obj
        
    except Exception as e:
        logger.error(f"Error parsing article: {e}")
        return None

def parse_and_validate_finnhub_news(news_item, ticker):
    """Convert Finnhub news to database format"""
    try:
        if not news_item.get("headline") or not news_item.get("summary"):
            return None
        
        # Convert Unix timestamp to datetime
        timestamp = news_item.get("datetime", 0)
        try:
            pub_date = datetime.fromtimestamp(timestamp)
        except:
            pub_date = datetime.now()
        
        article_obj = Article(
            ticker=ticker,
            title=news_item.get("headline", "")[:500],
            content=news_item.get("summary", ""),
            source=news_item.get("source", "Unknown"),
            published_date=pub_date,
            fetched_date=datetime.now()
        )
        
        return article_obj
        
    except Exception as e:
        logger.error(f"Error parsing Finnhub news: {e}")
        return None
    
def store_articles_to_db(articles, session):
    """
    Store validated articles to database, avoiding duplicates
    """
    stored_count = 0
    skipped_count = 0
    
    for article in articles:
        if article is None:
            continue
        
        try:
            # Check if article already exists (by title + source)
            existing = session.query(Article).filter(
                Article.title == article.title,
                Article.source == article.source
            ).first()
            
            if existing:
                skipped_count += 1
                logger.debug(f"Skipping duplicate: {article.title[:50]}")
                continue
            
            # Add new article
            session.add(article)
            stored_count += 1
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
    
    try:
        session.commit()
        logger.info(f"Stored {stored_count} new articles, skipped {skipped_count} duplicates")
        return stored_count, skipped_count
    except Exception as e:
        session.rollback()
        logger.error(f"Database commit failed: {e}")
        return 0, 0

def main():
    """Orchestrate the full news fetch pipeline"""
    session = Session(bind=engine)
    summary = {}
    
    try:
        for ticker in NEWS_TICKERS:
            logger.info(f"=== Processing {ticker} ===")
            try:
                # Fetch from both sources
                newsapi_articles = fetch_news_from_newsapi(ticker)
                finnhub_news = fetch_news_from_finnhub(ticker)
                
                # Parse and validate NewsAPI articles
                parsed_newsapi = [
                    parse_and_validate_newsapi_article(art, ticker)
                    for art in newsapi_articles
                ]
                
                # Parse and validate Finnhub news
                parsed_finnhub = [
                    parse_and_validate_finnhub_news(news, ticker)
                    for news in finnhub_news
                ]
                
                # Combine and store
                all_articles = parsed_newsapi + parsed_finnhub
                stored, skipped = store_articles_to_db(all_articles, session)
                summary[ticker] = {"status": "success", "stored": stored, "skipped": skipped, "msg": f"Stored {stored}, skipped {skipped}"}
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                summary[ticker] = {"status": "failed", "stored": 0, "skipped": 0, "msg": str(e)}
            
            logger.info(f"Completed {ticker}\n")
    
    finally:
        session.close()
    return summary

if __name__ == "__main__":
    main()
    logger.info("News fetch completed")
