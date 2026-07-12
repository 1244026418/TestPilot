from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from app import models

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "role" not in user_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'"))

    additions = {
        "test_cases": {
            "assertions_json": "TEXT NOT NULL DEFAULT ('[]')",
            "extractors_json": "TEXT NOT NULL DEFAULT ('[]')",
        },
        "test_runs": {
            "environment_id": "INTEGER NULL",
            "environment_name": "VARCHAR(128) NULL",
        },
        "test_results": {
            "request_url": "TEXT NULL",
            "assertion_results_json": "TEXT NOT NULL DEFAULT ('[]')",
            "extracted_variables_json": "TEXT NOT NULL DEFAULT ('[]')",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in additions.items():
            if table_name not in table_names:
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
