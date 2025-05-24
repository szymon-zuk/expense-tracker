from fastapi import FastAPI

from backend.app.db.database import SessionLocal
from backend.app.routers import expenses

app = FastAPI()


def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(expenses.router, tags=["expenses"])
