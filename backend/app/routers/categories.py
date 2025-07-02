from typing import Annotated, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import CurrentActiveUser
from backend.app.db.database import get_db
from backend.app.models.expenses import Category, Expense
from backend.app.schemas.categories import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithStats,
)

router = APIRouter(prefix="/categories", tags=["categories"])

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=List[Union[CategoryResponse, CategoryWithStats]])
def get_categories(
    current_user: CurrentActiveUser,
    db: db_dependency,
    include_stats: bool = Query(False, description="Include usage statistics"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
):
    """Get all categories with optional usage statistics"""

    if include_stats:
        # Query with expense statistics
        query = (
            select(
                Category.id,
                Category.name,
                Category.description,
                func.count(Expense.id).label("expense_count"),
                func.coalesce(func.sum(Expense.amount), 0).label("total_amount"),
            )
            .outerjoin(Expense, Category.id == Expense.category_id)
            .group_by(Category.id, Category.name, Category.description)
            .offset(skip)
            .limit(limit)
        )

        result = db.execute(query).all()

        return [
            CategoryWithStats(
                id=row.id,
                name=row.name,
                description=row.description,
                expense_count=row.expense_count,
                total_amount=float(row.total_amount),
            )
            for row in result
        ]
    else:
        # Simple query without stats
        query = select(Category).offset(skip).limit(limit)
        result = db.execute(query).scalars().all()
        return result


@router.get("/{category_id}", response_model=CategoryWithStats)
def get_category(category_id: int, current_user: CurrentActiveUser, db: db_dependency):
    """Get a specific category with usage statistics"""

    # Query category with stats
    query = (
        select(
            Category.id,
            Category.name,
            Category.description,
            func.count(Expense.id).label("expense_count"),
            func.coalesce(func.sum(Expense.amount), 0).label("total_amount"),
        )
        .outerjoin(Expense, Category.id == Expense.category_id)
        .where(Category.id == category_id)
        .group_by(Category.id, Category.name, Category.description)
    )

    result = db.execute(query).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )

    return CategoryWithStats(
        id=result.id,
        name=result.name,
        description=result.description,
        expense_count=result.expense_count,
        total_amount=float(result.total_amount),
    )


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate, current_user: CurrentActiveUser, db: db_dependency
):
    """Create a new category"""

    # Check if category with this name already exists
    existing_category = (
        db.query(Category).filter(Category.name == category.name).first()
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists",
        )

    # Create new category
    db_category = Category(name=category.name, description=category.description)

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: CurrentActiveUser,
    db: db_dependency,
):
    """Update an existing category"""

    # Get the category
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )

    # Check if new name conflicts with existing category
    update_data = category_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing_category = (
            db.query(Category)
            .filter(Category.name == update_data["name"], Category.id != category_id)
            .first()
        )
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{update_data['name']}' already exists",
            )

    # Update category
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: CurrentActiveUser,
    db: db_dependency,
    force: bool = Query(
        False, description="Force delete even if category has expenses"
    ),
):
    """Delete a category"""

    # Get the category
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )

    # Check if category has expenses
    expense_count = (
        db.query(func.count(Expense.id))
        .filter(Expense.category_id == category_id)
        .scalar()
    )

    if expense_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category.name}' as it has {expense_count} associated expenses. Use force=true to delete anyway.",
        )

    # If force delete, update expenses to have null category_id
    if expense_count > 0 and force:
        db.query(Expense).filter(Expense.category_id == category_id).update(
            {Expense.category_id: None}
        )

    # Delete the category
    db.delete(category)
    db.commit()

    return None


@router.get("/{category_id}/expenses", response_model=List[dict])
def get_category_expenses(
    category_id: int,
    current_user: CurrentActiveUser,
    db: db_dependency,
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
):
    """Get all expenses for a specific category (user's expenses only)"""

    # Verify category exists
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found",
        )

    # Get user's expenses in this category
    query = (
        select(Expense)
        .where(Expense.category_id == category_id, Expense.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )

    expenses = db.execute(query).scalars().all()

    return [
        {
            "id": expense.id,
            "name": expense.name,
            "description": expense.description,
            "amount": expense.amount,
            "currency": expense.currency,
            "date": expense.date,
            "category_name": category.name,
        }
        for expense in expenses
    ]
