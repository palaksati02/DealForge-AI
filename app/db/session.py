import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
from app.core.logging import logger

def create_db_engine():
    db_url = settings.database_url
    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    try:
        eng = create_engine(
            db_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as e:
        logger.warning(
            f"Primary database connection to '{db_url.split('@')[-1] if '@' in db_url else db_url}' "
            f"unavailable ({e}). Automatically switching to local SQLite database for resilient cloud execution."
        )
        sqlite_url = "sqlite:///./dealforge.db"
        return create_engine(
            sqlite_url,
            echo=settings.DB_ECHO,
            connect_args={"check_same_thread": False}
        )

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

