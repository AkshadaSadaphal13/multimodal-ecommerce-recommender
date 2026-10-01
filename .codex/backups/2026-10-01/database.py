import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Local development:
# data/user_history.db
#
# Docker can override this using DATABASE_URL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/user_history.db"
)

if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)

    if not db_path.startswith("/"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models.user import User, UserPreference, UserHistory

    Base.metadata.create_all(bind=engine)