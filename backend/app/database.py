import os
from pathlib import Path

from sqlalchemy import create_engine, inspect
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
    from .models.user import User, UserPreference, UserHistory

    Base.metadata.create_all(bind=engine)

    # create_all does not add columns to an existing SQLite database.
    # Keep existing history while adding the optional client event ID used
    # to make localStorage-to-backend synchronization idempotent.
    if DATABASE_URL.startswith("sqlite"):
        columns = {
            column["name"]
            for column in inspect(engine).get_columns("user_history")
        }
        if "event_id" not in columns:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    "ALTER TABLE user_history ADD COLUMN event_id VARCHAR(100)"
                )
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_user_history_event_id "
                "ON user_history (event_id) WHERE event_id IS NOT NULL"
            )
