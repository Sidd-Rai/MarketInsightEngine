# view_data.py
import pandas as pd
from database import engine

# 1. Peek at the OHLCV Price Data
print("\n--- Recent OHLCV Records ---")
prices_df = pd.read_sql("SELECT * FROM ohlcv ORDER BY date DESC LIMIT 10", engine)
print(prices_df)

# 2. Peek at the News Articles
print("\n--- Recent News Articles ---")
news_df = pd.read_sql("SELECT ticker, title, source, published_date FROM articles LIMIT 10", engine)
pd.set_option('display.max_colwidth', 60)
print(news_df)