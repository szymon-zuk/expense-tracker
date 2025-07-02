from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.expenses import Expense
from backend.app.schemas.expenses import (ExpenseCreate, ExpenseResponse,
                                          ExpenseUpdate)

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/expenses", response_model=List[ExpenseResponse])
def get_all_expenses(
    db: db_dependency,
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
):
    """Get all expenses with optional filtering and pagination"""
    query = select(Expense)

    # Apply filters
    if owner_id is not None:
        query = query.where(Expense.owner_id == owner_id)
    if category_id is not None:
        query = query.where(Expense.category_id == category_id)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    return result.scalars().all()


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: db_dependency):
    """Get a single expense by ID"""
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
    return expense


@router.post(
    "/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED
)
def create_expense(expense: ExpenseCreate, db: db_dependency):
    """Create a new expense"""
    db_expense = Expense(
        name=expense.name,
        description=expense.description,
        currency=expense.currency,
        amount=expense.amount,
        category_id=expense.category_id,
        owner_id=expense.owner_id,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, expense_update: ExpenseUpdate, db: db_dependency):
    """Update an existing expense"""
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    update_data = expense_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: db_dependency):
    """Delete an expense"""
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    db.delete(expense)
    db.commit()
    return None
