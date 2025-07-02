from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import CurrentActiveUser
from backend.app.db.database import get_db
from backend.app.models.expenses import Category, Expense, User
from backend.app.schemas.expenses import (
    CategoryStats,
    CurrencyStats,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseStatistics,
    ExpenseUpdate,
)

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/expenses", response_model=List[ExpenseResponse])
def get_all_expenses(
    current_user: CurrentActiveUser,
    db: db_dependency,
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
):
    """Get all expenses for the current user with optional filtering and pagination"""
    query = select(Expense).where(Expense.owner_id == current_user.id)

    if category_id is not None:
        query = query.where(Expense.category_id == category_id)

    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.get("/expenses/statistics", response_model=ExpenseStatistics)
def get_expense_statistics(
    current_user: CurrentActiveUser,
    db: db_dependency,
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for statistics (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for statistics (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
    ),
    category_id: Optional[int] = Query(
        None, description="Filter statistics by category ID"
    ),
):
    """Get expense statistics for the current user in a specified time frame"""

    # Build filter conditions - always filter by current user
    conditions = [Expense.owner_id == current_user.id]
    if start_date:
        conditions.append(Expense.date >= start_date)
    if end_date:
        conditions.append(Expense.date <= end_date)
    if category_id is not None:
        conditions.append(Expense.category_id == category_id)

    # Build base query for statistics
    stats_query = select(
        func.sum(Expense.amount).label("total_amount"),
        func.count(Expense.id).label("total_expenses"),
        func.avg(Expense.amount).label("average_expense"),
    )

    for condition in conditions:
        stats_query = stats_query.where(condition)

    # Get basic statistics
    total_stats = db.execute(stats_query).first()

    # Get currency breakdown
    currency_query = select(
        Expense.currency,
        func.sum(Expense.amount).label("total_amount"),
        func.count(Expense.id).label("expense_count"),
        func.avg(Expense.amount).label("average_amount"),
    ).group_by(Expense.currency)

    for condition in conditions:
        currency_query = currency_query.where(condition)

    currency_results = db.execute(currency_query).all()

    # Get category breakdown
    category_query = (
        select(
            Expense.category_id,
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("expense_count"),
            func.avg(Expense.amount).label("average_amount"),
        )
        .join(Category, Expense.category_id == Category.id)
        .group_by(Expense.category_id, Category.name)
    )

    for condition in conditions:
        category_query = category_query.where(condition)

    category_results = db.execute(category_query).all()

    # Build response
    currency_breakdown = [
        CurrencyStats(
            currency=row.currency,
            total_amount=float(row.total_amount or 0),
            expense_count=row.expense_count,
            average_amount=float(row.average_amount or 0),
        )
        for row in currency_results
    ]

    category_breakdown = [
        CategoryStats(
            category_id=row.category_id,
            category_name=row.category_name,
            total_amount=float(row.total_amount or 0),
            expense_count=row.expense_count,
            average_amount=float(row.average_amount or 0),
        )
        for row in category_results
    ]

    # Create period summary
    period_summary = {}
    if start_date and end_date:
        days = (end_date - start_date).days
        period_summary["period_type"] = f"Custom ({days} days)"
        period_summary["period_description"] = (
            f"From {start_date.date()} to {end_date.date()}"
        )
    elif start_date:
        period_summary["period_type"] = "From date onwards"
        period_summary["period_description"] = f"From {start_date.date()} onwards"
    elif end_date:
        period_summary["period_type"] = "Up to date"
        period_summary["period_description"] = f"Up to {end_date.date()}"
    else:
        period_summary["period_type"] = "All time"
        period_summary["period_description"] = "All expenses"

    # Handle case where total_stats might be None
    if total_stats is None:
        total_amount = 0.0
        total_expenses = 0
        average_expense = 0.0
    else:
        total_amount = float(total_stats.total_amount or 0)
        total_expenses = total_stats.total_expenses or 0
        average_expense = float(total_stats.average_expense or 0)

    return ExpenseStatistics(
        total_amount=total_amount,
        total_expenses=total_expenses,
        average_expense=average_expense,
        date_range={"start_date": start_date, "end_date": end_date},
        currency_breakdown=currency_breakdown,
        category_breakdown=category_breakdown,
        period_summary=period_summary,
    )


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, current_user: CurrentActiveUser, db: db_dependency):
    """Get a single expense by ID (only user's own expenses)"""
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    # Ensure user can only access their own expenses
    if getattr(expense, "owner_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own expenses",
        )

    return expense


@router.post(
    "/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED
)
def create_expense(
    expense: ExpenseCreate, current_user: CurrentActiveUser, db: db_dependency
):
    """Create a new expense for the current user"""

    # Check if category exists
    if expense.category_id:
        category = db.get(Category, expense.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {expense.category_id} not found",
            )

    # Create new expense
    new_expense = Expense(
        name=expense.name,
        description=expense.description,
        amount=expense.amount,
        currency=expense.currency,
        category_id=expense.category_id,
        owner_id=current_user.id,
        date=datetime.utcnow(),
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    current_user: CurrentActiveUser,
    db: db_dependency,
):
    """Update an existing expense (only user's own expenses)"""

    # Get the expense
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    # Check ownership
    if getattr(expense, "owner_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own expenses",
        )

    # Update expense
    update_data = expense_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    return expense


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, current_user: CurrentActiveUser, db: db_dependency):
    """Delete an expense (only user's own expenses)"""

    # Get the expense
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    # Check ownership
    if getattr(expense, "owner_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own expenses",
        )

    db.delete(expense)
    db.commit()
