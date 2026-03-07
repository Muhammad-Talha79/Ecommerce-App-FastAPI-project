# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DATABASE_URL = "sqlite:///./ecommerce.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =====================================================
# DATABASE DEPENDENCY
# =====================================================

def get_db():
    """
    FastAPI dependency to provide a database session
    and close it after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()