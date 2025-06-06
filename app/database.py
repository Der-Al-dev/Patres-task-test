from os.path import abspath, dirname, join

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = dirname(abspath(__file__))
DATA_DIR = join(BASE_DIR, "..", "data")
DB_PATH = join(DATA_DIR, "library.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # только для SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
