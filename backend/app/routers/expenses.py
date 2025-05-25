from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.expenses import Expense
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()
get_db()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/expenses")
async def get_all_expenses(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Expense))
    return result.scalars().all()
