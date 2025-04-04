import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

# Environment variable to choose database type
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

if DB_TYPE == "mysql":
    # MySQL connection configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = quote_plus(os.getenv("MYSQL_PASSWORD"))
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_recycle=180,  # recycles the connection after 3 minutes
        pool_size=20,  # maximum number of connections to keep open
        max_overflow=50,  # Allow more overflow connections
        pool_timeout=60,  # Increase the timeout to wait for a connection
    )

elif DB_TYPE == "sqlite":
    # SQLite configuration
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "sqlite.db")

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

else:
    raise ValueError("Invalid DB_TYPE specified. Choose 'mysql' or 'sqlite'.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
