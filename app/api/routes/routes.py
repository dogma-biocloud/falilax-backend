from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine

router = APIRouter()

@router.get("/db-test")
def db_test():
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
    return {"db": value}