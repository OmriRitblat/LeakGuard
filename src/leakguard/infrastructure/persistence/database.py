
"""SQLAlchemy database connection and session configuration."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine() -> Engine:
    """Create a SQLAlchemy engine from environment variables."""
    load_dotenv(".env", override=False)

    required_vars = (
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    )

    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise ValueError(
            f"Missing database environment variables: {', '.join(missing)}"
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )

    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a factory for database sessions."""
    return sessionmaker(bind=engine, expire_on_commit=False)
