from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from src.config import DATABASE_URL

# Added check_same_thread=False for safety
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    # Added index=True for fast lookups
    ticker = Column(String(10), nullable=False, index=True) 
    title = Column(String(500), nullable=False)
    content = Column(String(10000))
    source = Column(String(100))
    published_date = Column(DateTime)
    fetched_date = Column(DateTime, default=datetime.now)

class OHLCV(Base):
    __tablename__ = "ohlcv"
    
    id = Column(Integer, primary_key=True)
    # Added index=True for fast lookups
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

# Create tables
Base.metadata.create_all(engine)
print("✅ Database created!")
