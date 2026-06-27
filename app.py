import sys
import os
import argparse
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

# Ensure that the project root is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fetchers import fetch_ohlcv, fetch_news
from src.db.database import engine, OHLCV, Article

def print_db_summary():
    """Print general statistics and recent entries from the database"""
    session = Session(bind=engine)
    try:
        # Total counts
        ohlcv_count = session.query(func.count(OHLCV.id)).scalar()
        article_count = session.query(func.count(Article.id)).scalar()
        
        print("\n" + "="*50)
        print("📊 DATABASE SUMMARY")
        print("="*50)
        print(f"Total OHLCV Price Records: {ohlcv_count}")
        print(f"Total News Article Records: {article_count}")
        
        # Unique tickers
        tickers_ohlcv = session.query(OHLCV.ticker).distinct().all()
        tickers_news = session.query(Article.ticker).distinct().all()
        
        print(f"Tickers with pricing data: {', '.join([t[0] for t in tickers_ohlcv]) if tickers_ohlcv else 'None'}")
        print(f"Tickers with news articles: {', '.join([t[0] for t in tickers_news]) if tickers_news else 'None'}")
        print("="*50)
        
        # Interactive Peek Options
        while True:
            print("\nSelect peek option:")
            print("1. View latest 10 OHLCV price records")
            print("2. View latest 10 news articles")
            print("3. Return to main menu")
            
            choice = input("\nEnter choice (1-3): ").strip()
            if choice == "1":
                print("\n--- Recent OHLCV Records ---")
                df = pd.read_sql("SELECT ticker, date, open, high, low, close, volume FROM ohlcv ORDER BY date DESC LIMIT 10", engine)
                print(df if not df.empty else "No price data found.")
            elif choice == "2":
                print("\n--- Recent News Articles ---")
                df = pd.read_sql("SELECT ticker, title, source, published_date FROM articles ORDER BY published_date DESC LIMIT 10", engine)
                pd.set_option('display.max_colwidth', 50)
                print(df if not df.empty else "No news articles found.")
            elif choice == "3":
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
    finally:
        session.close()

def menu():
    """Terminal-based interactive menu"""
    while True:
        print("\n" + "═"*50)
        print("📈 MARKET INSIGHT ENGINE INTERACTIVE MENU")
        print("═"*50)
        print("1. Run OHLCV Pricing Ingestion Pipeline")
        print("2. Run News Ingestion Pipeline")
        print("3. Run Both Pipelines")
        print("4. Peek at Database / View Statistics")
        print("5. Exit")
        print("═"*50)
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n--- Running OHLCV Ingestion Pipeline ---")
            fetch_ohlcv.main()
        elif choice == "2":
            print("\n--- Running News Ingestion Pipeline ---")
            fetch_news.main()
        elif choice == "3":
            print("\n--- Running Both Ingestion Pipelines ---")
            fetch_ohlcv.main()
            fetch_news.main()
        elif choice == "4":
            print_db_summary()
        elif choice == "5":
            print("\n👋 Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter a number between 1 and 5.")

def main():
    parser = argparse.ArgumentParser(description="Market Insight Engine Ingestion Orchestrator")
    parser.add_argument(
        "--fetch",
        choices=["all", "ohlcv", "news"],
        help="Run ingestion pipeline directly (non-interactive mode)"
    )
    
    args = parser.parse_args()
    
    # If fetch arg is provided, run non-interactively
    if args.fetch:
        print("🚀 Starting Market Insight Engine ingestion pipelines (non-interactive)...")
        if args.fetch in ("all", "ohlcv"):
            print("\n--- Running OHLCV Ingestion Pipeline ---")
            fetch_ohlcv.main()
        if args.fetch in ("all", "news"):
            print("\n--- Running News Ingestion Pipeline ---")
            fetch_news.main()
        print("\n✅ Ingestion execution completed successfully!")
    else:
        # Otherwise, start interactive menu
        menu()

if __name__ == "__main__":
    main()
