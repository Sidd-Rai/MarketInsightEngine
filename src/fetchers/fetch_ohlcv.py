# fetch_ohlcv.py
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.db.database import engine, OHLCV, Base
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from src.config import (
    OHLCV_TICKERS,
    OHLCV_RETRY_TOTAL,
    OHLCV_RETRY_BACKOFF,
    OHLCV_STATUS_FORCELIST,
    OHLCV_LOG_PATH
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OHLCV_LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure HTTP session with retries for yfinance requests
http_session = requests.Session()
http_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})
retries = Retry(
    total=OHLCV_RETRY_TOTAL,
    backoff_factor=OHLCV_RETRY_BACKOFF,
    status_forcelist=OHLCV_STATUS_FORCELIST
)
http_session.mount("http://", HTTPAdapter(max_retries=retries))
http_session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_ohlcv_data(ticker, days=30):
    """
    Fetch OHLCV data from yfinance
    
    Args:
        ticker: Stock symbol
        days: How many days back to fetch
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching {ticker} OHLCV data from {start_date.date()} to {end_date.date()}")
        
        # Use yf.Ticker().history() with HTTPAdapter retry support
        stock = yf.Ticker(ticker, session=http_session)
        data = stock.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d")
        )
        
        logger.info(f"Fetched {len(data)} trading days for {ticker}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to fetch {ticker}: {e}")
        return None

def store_ohlcv_to_db(ticker, df, session):
    """
    Store OHLCV data to database
    
    Args:
        ticker: Stock symbol
        df: DataFrame with OHLCV data
        session: Database session
    """
    if df is None or df.empty:
        logger.warning(f"No data to store for {ticker}")
        return 0, 0
    
    stored_count = 0
    skipped_count = 0
    
    for date, row in df.iterrows():
        try:
            # Check if this date already exists for this ticker
            existing = session.query(OHLCV).filter(
                OHLCV.ticker == ticker,
                OHLCV.date == date.date()
            ).first()
            
            if existing:
                skipped_count += 1
                logger.debug(f"Skipping existing data for {ticker} on {date.date()}")
                continue
            
            # Create OHLCV record
            ohlcv_record = OHLCV(
                ticker=ticker,
                date=date.date(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"])
            )
            
            session.add(ohlcv_record)
            stored_count += 1
            
        except Exception as e:
            logger.error(f"Error storing OHLCV for {ticker} on {date}: {e}")
    
    try:
        session.commit()
        logger.info(f"Stored {stored_count} OHLCV records for {ticker}, skipped {skipped_count}")
        return stored_count, skipped_count
    except Exception as e:
        session.rollback()
        logger.error(f"Database commit failed: {e}")
        return 0, 0

def main():
    """Fetch and store OHLCV data for all tickers"""
    session = Session(bind=engine)
    summary = {}
    
    try:
        for ticker in OHLCV_TICKERS:
            logger.info(f"=== Processing {ticker} ===")
            try:
                # Check latest date in database
                latest_record = session.query(OHLCV).filter(
                    OHLCV.ticker == ticker
                ).order_by(OHLCV.date.desc()).first()
                
                if latest_record:
                    latest_date = latest_record.date.date() if hasattr(latest_record.date, "date") else latest_record.date
                    start_date = latest_date + timedelta(days=1)
                    end_date = datetime.now().date()
                    
                    if start_date >= end_date:
                        logger.info(f"Data for {ticker} is already up-to-date (latest date: {latest_date}). Skipping fetch.")
                        summary[ticker] = {"status": "up-to-date", "stored": 0, "skipped": 0, "msg": f"Already up-to-date (latest: {latest_date})"}
                        continue
                    
                    days_to_fetch = (end_date - latest_date).days
                    logger.info(f"Latest record date is {latest_date}. Fetching last {days_to_fetch} days.")
                    df = fetch_ohlcv_data(ticker, days=days_to_fetch)
                else:
                    logger.info(f"No existing data for {ticker}. Fetching default 30 days.")
                    df = fetch_ohlcv_data(ticker, days=30)
                
                # Store to database
                if df is not None and not df.empty:
                    stored, skipped = store_ohlcv_to_db(ticker, df, session)
                    summary[ticker] = {"status": "success", "stored": stored, "skipped": skipped, "msg": f"Stored {stored}, skipped {skipped}"}
                else:
                    summary[ticker] = {"status": "warning", "stored": 0, "skipped": 0, "msg": "No data returned from API"}
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                summary[ticker] = {"status": "failed", "stored": 0, "skipped": 0, "msg": str(e)}
            
            logger.info(f"Completed {ticker}\n")
    
    finally:
        session.close()
    return summary

if __name__ == "__main__":
    main()
    logger.info("OHLCV fetch completed")
