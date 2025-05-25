from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, String)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base
from backend.app.schemas.expenses import CurrencyEnum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String(length=256))
    is_active = Column(Boolean, default=True)
    expenses = relationship("Expense", back_populates="owner")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    currency = Column(Enum(CurrencyEnum, name="currency_enum"), nullable=False)
    amount = Column(Float)
    date = Column(DateTime, default=datetime.now(timezone.utc))
    owner_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    owner = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
