from enum import StrEnum
from typing import Optional

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
    owner_id: int


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
