from typing import Generator

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config.settings import get_settings

settings = get_settings()

engine = create_engine(str(settings.postgres_url), echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Create and get database session.

    :yield: database session.
    """
    db = SessionLocal()
    try:
        yield db
    except HTTPException:
        db.rollback()
        raise
    finally:
        db.close()
