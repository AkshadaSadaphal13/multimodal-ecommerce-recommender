import os
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "user_history.db"

# Resolve the local database from this file, not the shell's current directory.
# Docker and other deployments can override this with DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "", 1).split("?", 1)[0]
    if db_path != ":memory:":
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


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
        user_columns = {
            column["name"] for column in inspect(engine).get_columns("users")
        }
        with engine.begin() as connection:
            if "name" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN name VARCHAR(120)"
                )
            if "email" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN email VARCHAR(255)"
                )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email "
                "ON users (email) WHERE email IS NOT NULL"
            )

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

        migrate_legacy_database()


def migrate_legacy_database():
    """Copy records from the former backend/data database into the canonical DB."""
    legacy_path = PROJECT_ROOT / "backend" / "data" / "user_history.db"
    if not legacy_path.exists() or legacy_path.resolve() == DEFAULT_DATABASE_PATH.resolve():
        return

    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ? AS legacy", (str(legacy_path),))
        try:
            tables = {
                row[0]
                for row in connection.exec_driver_sql(
                    "SELECT name FROM legacy.sqlite_master WHERE type = 'table'"
                )
            }

            if "users" in tables:
                connection.exec_driver_sql(
                    "INSERT OR IGNORE INTO main.users (user_id, created_at, is_new_user) "
                    "SELECT user_id, created_at, is_new_user FROM legacy.users"
                )

            if "user_preferences" in tables:
                connection.exec_driver_sql(
                    "INSERT INTO main.user_preferences (user_id, category, min_price, max_price) "
                    "SELECT old.user_id, old.category, old.min_price, old.max_price "
                    "FROM legacy.user_preferences AS old "
                    "WHERE NOT EXISTS (SELECT 1 FROM main.user_preferences AS current "
                    "WHERE current.user_id = old.user_id AND current.category = old.category "
                    "AND current.min_price = old.min_price "
                    "AND current.max_price IS old.max_price)"
                )

            if "user_history" in tables:
                legacy_columns = {
                    row[1]
                    for row in connection.exec_driver_sql(
                        "PRAGMA legacy.table_info('user_history')"
                    )
                }
                legacy_event_id = "event_id" if "event_id" in legacy_columns else "NULL"
                connection.exec_driver_sql(
                    "INSERT INTO main.user_history "
                    "(user_id, product_id, event_type, event_id, query, timestamp) "
                    "SELECT old.user_id, old.product_id, old.event_type, "
                    f"{legacy_event_id}, old.query, old.timestamp "
                    "FROM legacy.user_history AS old "
                    "WHERE NOT EXISTS (SELECT 1 FROM main.user_history AS current "
                    "WHERE current.user_id = old.user_id "
                    "AND current.product_id = old.product_id "
                    "AND current.event_type = old.event_type "
                    "AND current.timestamp = old.timestamp "
                    "AND current.query IS old.query)"
                )

            connection.commit()
        finally:
            connection.exec_driver_sql("DETACH DATABASE legacy")
