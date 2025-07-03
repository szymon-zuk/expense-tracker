from datetime import datetime, timezone
from typing import Generator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth.dependencies import get_current_active_user
from backend.app.db.base import Base
from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.models.expenses import Category, Expense, User
from backend.app.schemas.expenses import CurrencyEnum

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        id=1,
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_2(db_session: Session) -> User:
    """Create a second test user for testing ownership."""
    user = User(
        id=2,
        email="testuser2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_categories(db_session: Session) -> list[Category]:
    """Create test categories."""
    categories = [
        Category(id=1, name="Food", description="Food expenses"),
        Category(id=2, name="Transportation", description="Transportation costs"),
        Category(id=3, name="Entertainment", description="Entertainment expenses"),
    ]
    for category in categories:
        db_session.add(category)
    db_session.commit()
    for category in categories:
        db_session.refresh(category)
    return categories


@pytest.fixture(scope="function")
def test_expenses(
    db_session: Session, test_user: User, test_categories: list[Category]
) -> list[Expense]:
    """Create test expenses."""
    expenses = [
        Expense(
            id=1,
            name="Grocery Shopping",
            description="Weekly groceries",
            amount=50.0,
            currency=CurrencyEnum.USD,
            category_id=1,
            owner_id=test_user.id,
            date=datetime(2023, 1, 15, tzinfo=timezone.utc),
        ),
        Expense(
            id=2,
            name="Gas Station",
            description="Car fuel",
            amount=30.0,
            currency=CurrencyEnum.USD,
            category_id=2,
            owner_id=test_user.id,
            date=datetime(2023, 1, 20, tzinfo=timezone.utc),
        ),
        Expense(
            id=3,
            name="Movie Tickets",
            description="Weekend movie",
            amount=25.0,
            currency=CurrencyEnum.EUR,
            category_id=3,
            owner_id=test_user.id,
            date=datetime(2023, 2, 5, tzinfo=timezone.utc),
        ),
    ]
    for expense in expenses:
        db_session.add(expense)
    db_session.commit()
    for expense in expenses:
        db_session.refresh(expense)
    return expenses


@pytest.fixture(scope="function")
def client(db_session: Session, test_user: User) -> TestClient:
    """Create a test client with mocked authentication."""

    def override_get_db():
        yield db_session

    def override_get_current_active_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_user_2(db_session: Session, test_user_2: User) -> TestClient:
    """Create a test client with mocked authentication for second user."""

    def override_get_db():
        yield db_session

    def override_get_current_active_user():
        return test_user_2

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
