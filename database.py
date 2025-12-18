from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Replace values with your PostgreSQL credentials
DATABASE_URL = "postgresql://jobscraperuser:jobscraperpassword@localhost:5433/jobscraperapp"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Database connected:", conn.execute(text("SELECT 1")).scalar())
    except Exception as e:
        print("❌ Connection failed:", e)