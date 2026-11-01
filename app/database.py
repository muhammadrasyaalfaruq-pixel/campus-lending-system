import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/pinjamkampus_dev")

connect_args = {}
if "tidbcloud.com" in DATABASE_URL:
    # Use SSL CA if provided; otherwise disable verification to avoid runtime crash in Vercel
    ssl_ca = os.getenv("SSL_CA_PATH")
    if ssl_ca:
        connect_args = {"ssl": {"ca": ssl_ca}}
    else:
        connect_args = {"ssl": {"ssl_verify_cert": False, "ssl_verify_identity": False}}


engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
