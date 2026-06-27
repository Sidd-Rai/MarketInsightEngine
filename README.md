# Market Insight Engine

Market Insight Engine is a structured, robust data ingestion pipeline designed to fetch financial market data—specifically OHLCV (Open, High, Low, Close, Volume) pricing data and financial news articles—and store them in a local SQLite database for downstream processing or modeling.

---

## 💻 Project Structure

The project has been restructured into a modular format:

```text
MarketInsightEngine/
├── DATABASE/
│   └── stock_data.db            # SQLite database file
├── LOGS/
│   ├── fetch_news.log           # Log file for news ingestion run
│   └── fetch_ohlcv.log          # Log file for pricing ingestion run
├── EXPORTS/
│   ├── ohlcv_export.csv         # Exported pricing CSV data
│   └── news_export.csv          # Exported news CSV data
├── documentation/
│   └── data_fetchers_analysis.md # Detailed codebase analysis report
├── src/
│   ├── __init__.py
│   ├── config.py                # Centralized configurations, API keys & tickers
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy models (Article, OHLCV) & schema definition
│   └── fetchers/
│       ├── __init__.py
│       ├── fetch_news.py        # NewsAPI and Finnhub API client
│       └── fetch_ohlcv.py       # Yahoo Finance historical prices client
├── app.py                       # CLI and interactive terminal orchestrator
├── requirements.txt             # Python dependencies
└── .env                         # API keys (NewsAPI & Finnhub)
```

---

## ✨ Key Features

1. **Terminal-Based Interactive Menu**:
   Run `python app.py` to launch an interactive menu where you can trigger ingestion pipelines, view database statistics (total records, tracked tickers), peek at the latest entries, or export data.
   
2. **Resilient Retry Mechanism (HTTPAdapter)**:
   Includes built-in resilience using `urllib3.util.Retry` and requests `HTTPAdapter`. It automatically retries on rate limits (HTTP 429) and transient server errors (HTTP 500, 502, 503, 504) with exponential backoff (up to 5 retries).
   
3. **Custom User-Agent Spoofing**:
   Appends a valid browser User-Agent to the requests session used by `yfinance`, preventing Yahoo Finance from blocking scraping queries as bot traffic.
   
4. **Dynamic Range Ingestion**:
   To conserve API limits and bandwidth, the pricing script dynamically queries the latest recorded date in the database for each ticker and only requests missing pricing data. If the database is already up-to-date (e.g. on weekends), it skips the API call entirely.
   
5. **Database Deduplication**:
   Ensures clean database tables by matching article titles + sources, and ticker symbols + dates before inserting new records.
   
6. **Ingestion Summary Report**:
   Provides a clear, tabular report post-execution (showing Ticker, Status, Stored Count, Skipped Count, and Details) for all pipeline operations in both interactive and CLI modes.
   
7. **CSV Exporters**:
   Allows exporting the ingested tables to clean CSV spreadsheets (`ohlcv_export.csv` and `news_export.csv`) inside the `EXPORTS/` directory.

---

## 🚀 How to Run

### Prerequisite: Setup API Keys
Create a `.env` file at the root of the project:
```env
NEWSAPI_KEY=your_newsapi_key
FINNHUB_KEY=your_finnhub_key
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Running the Orchestrator

* **Interactive Mode**:
  ```bash
  python app.py
  ```
  
* **Non-Interactive Mode (CLI)**:
  Run a specific ingestion pipeline directly:
  ```bash
  # Ingest both pricing and news
  python app.py --fetch all
  
  # Ingest pricing data only
  python app.py --fetch ohlcv
  
  # Ingest news articles only
  python app.py --fetch news
  ```
