from fastapi import FastAPI

from backend.app.routers import expenses

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(expenses.router, tags=["expenses"])
