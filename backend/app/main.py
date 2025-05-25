from fastapi import FastAPI

from backend.app.db.database import get_db
from backend.app.routers import expenses

app = FastAPI()
db = get_db()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(expenses.router, tags=["expenses"])
