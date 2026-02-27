from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())
from sqlalchemy import text
from app.db.session import engine

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB OK ->", result.scalar())

if __name__ == "__main__":
    main()
