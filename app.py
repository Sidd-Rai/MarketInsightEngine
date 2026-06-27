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

def print_summary_report(ohlcv_summary=None, news_summary=None):
    """Print a clean summary of the ingestion run results"""
    print("\n" + "═"*70)
    print("📋 INGESTION SUMMARY REPORT")
    print("═"*70)
    
    if ohlcv_summary:
        print("\n📊 OHLCV Pricing Ingestion:")
        print(f"{'Ticker':<10} | {'Status':<12} | {'Stored':<8} | {'Skipped':<8} | {'Details'}")
        print("-" * 70)
        for ticker, result in ohlcv_summary.items():
            status = result["status"].upper()
            print(f"{ticker:<10} | {status:<12} | {result['stored']:<8} | {result['skipped']:<8} | {result['msg']}")
            
    if news_summary:
        print("\n📰 News Ingestion:")
        print(f"{'Ticker':<10} | {'Status':<12} | {'Stored':<8} | {'Skipped':<8} | {'Details'}")
        print("-" * 70)
        for ticker, result in news_summary.items():
            status = result["status"].upper()
            print(f"{ticker:<10} | {status:<12} | {result['stored']:<8} | {result['skipped']:<8} | {result['msg']}")
            
    print("═"*70)

def export_tables():
    """Export database tables to CSV files"""
    print("\n" + "═"*50)
    print("📤 EXPORT DATABASE TABLES TO CSV")
    print("═"*50)
    print("1. Export OHLCV Pricing Table")
    print("2. Export News Articles Table")
    print("3. Export Both Tables")
    print("4. Return to Main Menu")
    print("═"*50)
    
    choice = input("\nEnter your choice (1-4): ").strip()
    if choice not in ("1", "2", "3"):
        return
        
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXPORTS")
    os.makedirs(export_dir, exist_ok=True)
    
    if choice in ("1", "3"):
        try:
            df = pd.read_sql("SELECT * FROM ohlcv", engine)
            if not df.empty:
                export_path = os.path.join(export_dir, "ohlcv_export.csv")
                df.to_csv(export_path, index=False)
                print(f"✅ OHLCV data exported to: [ohlcv_export.csv](file://{export_path})")
            else:
                print("⚠️ No OHLCV price records found in database to export.")
        except Exception as e:
            print(f"❌ Error exporting OHLCV records: {e}")
            
    if choice in ("2", "3"):
        try:
            df = pd.read_sql("SELECT * FROM articles", engine)
            if not df.empty:
                export_path = os.path.join(export_dir, "news_export.csv")
                df.to_csv(export_path, index=False)
                print(f"✅ News articles exported to: [news_export.csv](file://{export_path})")
            else:
                print("⚠️ No News articles found in database to export.")
        except Exception as e:
            print(f"❌ Error exporting News articles: {e}")

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
        print("5. Export Database Tables to CSV")
        print("6. Exit")
        print("═"*50)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            print("\n--- Running OHLCV Ingestion Pipeline ---")
            ohlcv_res = fetch_ohlcv.main()
            print_summary_report(ohlcv_summary=ohlcv_res)
        elif choice == "2":
            print("\n--- Running News Ingestion Pipeline ---")
            news_res = fetch_news.main()
            print_summary_report(news_summary=news_res)
        elif choice == "3":
            print("\n--- Running Both Ingestion Pipelines ---")
            ohlcv_res = fetch_ohlcv.main()
            news_res = fetch_news.main()
            print_summary_report(ohlcv_summary=ohlcv_res, news_summary=news_res)
        elif choice == "4":
            print_db_summary()
        elif choice == "5":
            export_tables()
        elif choice == "6":
            print("\n👋 Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter a number between 1 and 6.")

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
        ohlcv_res = None
        news_res = None
        
        if args.fetch in ("all", "ohlcv"):
            print("\n--- Running OHLCV Ingestion Pipeline ---")
            ohlcv_res = fetch_ohlcv.main()
        if args.fetch in ("all", "news"):
            print("\n--- Running News Ingestion Pipeline ---")
            news_res = fetch_news.main()
            
        print_summary_report(ohlcv_summary=ohlcv_res, news_summary=news_res)
        print("\n✅ Ingestion execution completed successfully!")
    else:
        # Otherwise, start interactive menu
        menu()

if __name__ == "__main__":
    main()
