import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Pakai SQLite jika di PythonAnywhere, MySQL jika lokal
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pinjamkampus.db")

engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try: