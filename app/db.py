# app/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration - Optimized for both local development and Heroku
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Heroku provides PostgreSQL URLs that start with postgres:// but SQLAlchemy
    # now requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # For Heroku, use their recommended connection parameters
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 minutes
        connect_args={"sslmode": "require"}  # Required for Heroku PostgreSQL
    )
else:
    # Local development settings (uses environment variables)
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_NAME = os.environ.get("DB_NAME", "residere")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")

    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)

# Create a sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency function to get a database session.
    Used with FastAPI's dependency injection system.

    Yields:
        Session: A SQLAlchemy database session
    """
    db = None
    try:
        db = SessionLocal()
        # Test the connection
        db.execute("SELECT 1")
        yield db
    except Exception as e:
        if db:
            db.close()
        # Log the error but don't crash the app
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Database connection failed: {e}")
        # Return a mock session that won't crash the app
        yield None
    finally:
        if db:
            db.close()