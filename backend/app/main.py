from backend.app.database import SessionLocal
from fastapi import FastAPI

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
