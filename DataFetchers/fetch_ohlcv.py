# fetch_ohlcv.py
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import engine, OHLCV, Base
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fetch_ohlcv.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA", "META"]

# def fetch_ohlcv_data(ticker, days=30):
#     """
#     Fetch OHLCV data from yfinance
    
#     Args:
#         ticker: Stock symbol
#         days: How many days back to fetch
    
#     Returns:
#         DataFrame with OHLCV data
#     """
#     try:
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=days)
        
#         logger.info(f"Fetching {ticker} OHLCV data from {start_date.date()} to {end_date.date()}")
        
#         # Download data
#         data = yf.download(
#             ticker,
#             start=start_date.strftime("%Y-%m-%d"),
#             end=end_date.strftime("%Y-%m-%d"),
#             progress=False  # Don't print download progress
#         )
        
#         logger.info(f"Fetched {len(data)} trading days for {ticker}")
#         return data
        
#     except Exception as e:
#         logger.error(f"Failed to fetch {ticker}: {e}")
#         return None

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
        
        # FIX: Use yf.Ticker().history() instead of yf.download() 
        # to prevent the Pandas MultiIndex 'Series' error.
        stock = yf.Ticker(ticker)
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
        return
    
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
    except Exception as e:
        session.rollback()
        logger.error(f"Database commit failed: {e}")

def main():
    """Fetch and store OHLCV data for all tickers"""
    session = Session(bind=engine)
    
    try:
        for ticker in TICKERS:
            logger.info(f"=== Processing {ticker} ===")
            
            # Fetch OHLCV data
            df = fetch_ohlcv_data(ticker, days=30)
            
            # Store to database
            store_ohlcv_to_db(ticker, df, session)
            
            logger.info(f"Completed {ticker}\n")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()
    logger.info("OHLCV fetch completed")