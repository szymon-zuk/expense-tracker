from datetime import datetime
from enum import StrEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CurrencyEnum(StrEnum):
    USD = "USD"
    EUR = "EUR"
    PLN = "PLN"
    GBP = "GBP"


class ExpenseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: CurrencyEnum
    amount: float
    category_id: int


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[CurrencyEnum] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    owner_id: Optional[int] = None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    currency: Optional[CurrencyEnum] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    owner_id: Optional[int] = None
    date: Optional[datetime] = None


class CategoryStats(BaseModel):
    """Statistics for a specific category"""

    category_id: int
    category_name: Optional[str] = None
    total_amount: float
    expense_count: int
    average_amount: float


class CurrencyStats(BaseModel):
    """Statistics for a specific currency"""

    currency: CurrencyEnum
    total_amount: float
    expense_count: int
    average_amount: float


class ExpenseStatistics(BaseModel):
    """Complete expense statistics for a time period"""

    total_amount: float
    total_expenses: int
    average_expense: float
    date_range: Dict[str, Optional[datetime]]
    currency_breakdown: List[CurrencyStats]
    category_breakdown: List[CategoryStats]
    period_summary: Dict[str, str]
