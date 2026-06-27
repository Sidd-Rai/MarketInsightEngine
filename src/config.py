import os
from dotenv import load_dotenv

# Load environment variables from the project root .env file
load_dotenv()

# Project Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database Path (Ensure the directory exists)
DATABASE_DIR = os.path.join(BASE_DIR, "DATABASE")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DATABASE_DIR, "stock_data.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Logs Path (Ensure the directory exists)
LOGS_DIR = os.path.join(BASE_DIR, "LOGS")
os.makedirs(LOGS_DIR, exist_ok=True)
NEWS_LOG_PATH = os.path.join(LOGS_DIR, "fetch_news.log")
OHLCV_LOG_PATH = os.path.join(LOGS_DIR, "fetch_ohlcv.log")

# API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

# Ticker Lists
OHLCV_TICKERS = [
    "AAPL", "GOOGL", "MSFT", "TSLA", "META",
    "NVDA", "AMD", "INTC", "QCOM", "CRM",
    "PYPL", "SQ", "COIN", "MSTR",
    "SNOW", "OKTA", "NET",
    "UBER", "AMZN", "NFLX"
]
NEWS_TICKERS = [
    "AAPL", "GOOGL", "MSFT",
    "NVDA", "AMD", "INTC", "QCOM", "CRM",
    "PYPL", "SQ", "COIN", "MSTR",
    "SNOW", "OKTA", "NET",
    "UBER", "AMZN", "NFLX"
]

# Retry Configuration
OHLCV_RETRY_TOTAL = 5
OHLCV_RETRY_BACKOFF = 2
OHLCV_STATUS_FORCELIST = [429, 500, 502, 503, 504]

NEWS_RETRY_TOTAL = 5
NEWS_RETRY_BACKOFF = 2
NEWS_STATUS_FORCELIST = [429, 500, 502, 503, 504]
