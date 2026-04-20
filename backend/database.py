




"""
GradeOps - Database Configuration
"""
 
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
 
load_dotenv()
 
# Pull credentials from .env (fallback to hardcoded defaults for dev)
DB_USER     = os.getenv("DB_USER", "subhajit")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Datadb@2026")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "gradeops_db")
 
# URL-encode password to handle special chars like '@'
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
 
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # auto-reconnect on stale connections
    pool_size=10,
    max_overflow=20,
)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
 
def get_db():
    """FastAPI dependency: yields a DB session and closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()        