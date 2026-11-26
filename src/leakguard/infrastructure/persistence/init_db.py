
"""Initialize the LeakGuard PostgreSQL database schema."""

from sqlalchemy import text

from leakguard.infrastructure.persistence.database import create_db_engine
from leakguard.infrastructure.persistence.orm_models import Base


def init_db() -> None:
    """Enable required extensions and create missing tables."""
    engine = create_db_engine()

    try:
        with engine.begin() as connection:
            # Required for the VECTOR column in secret_vectors.
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )

            # Create all registered ORM tables.
            Base.metadata.create_all(bind=connection)

        print("Database schema initialized successfully.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    init_db()
