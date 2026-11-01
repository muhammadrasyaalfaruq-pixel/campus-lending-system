import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://localhost/pinjamkampus_dev")

connect_args = {"connect_timeout": 30}
pool_class = None

# Serverless environment - avoid connection pooling
if os.getenv("VERCEL") or os.getenv("RAILWAY_ENVIRONMENT_NAME"):
    pool_class = NullPool

if "tidbcloud.com" in DATABASE_URL:
    ssl_ca = os.getenv("SSL_CA_PATH")
    if ssl_ca:
        connect_args["ssl"] = {"ca": ssl_ca}
    else:
        connect_args["ssl_verify_cert"] = False
        connect_args["ssl_verify_identity"] = False

engine_config = {
    "echo": False,
    "pool_pre_ping": True,
    "connect_args": connect_args,
}

if pool_class:
    engine_config["poolclass"] = pool_class

engine = create_engine(DATABASE_URL, **engine_config)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
