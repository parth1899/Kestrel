import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.base import Base
import models  # noqa: F401 - ensure models are imported so metadata has all tables

load_dotenv()

DATABASE_DSN = os.getenv("DATABASE_DSN", "sqlite:///./management.db")
# allow override of the schema name
MANAGEMENT_SCHEMA = os.getenv("MANAGEMENT_SCHEMA", "management")
# For SQLite, need check_same_thread=False when used with FastAPI's threaded server
if DATABASE_DSN.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
else:
    _connect_args = {}

engine = create_engine(
    DATABASE_DSN,
    connect_args=_connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_schema():
    """Ensure the dedicated schema exists when using Postgres (e.g., Neon).

    Using a separate schema keeps management-plane tables isolated from telemetry tables.
    """
    if DATABASE_DSN.startswith("postgres") or DATABASE_DSN.startswith("postgresql"):
        # Create the schema if missing. search_path will be set via a connect event.
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MANAGEMENT_SCHEMA}"))


def init_database():
    """Create schema and tables if they don't exist."""
    # If using Postgres/Neon, create the schema and call create_all within a connection
    # that has search_path set so tables are created inside the management schema.
    if DATABASE_DSN.startswith("postgres") or DATABASE_DSN.startswith("postgresql"):
        _ensure_schema()
        with engine.begin() as conn:
            Base.metadata.create_all(bind=conn)
    else:
        _ensure_schema()
        Base.metadata.create_all(bind=engine)

# For Postgres/Neon, set search_path on each new DB-API connection (avoids unsupported startup options)
try:
    from sqlalchemy import event

    if DATABASE_DSN.startswith("postgres") or DATABASE_DSN.startswith("postgresql"):
        @event.listens_for(engine, "connect")
        def _set_search_path(dbapi_connection, connection_record):
            try:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {MANAGEMENT_SCHEMA}, public")
            except Exception:
                # Don't fail connection if SET fails (e.g., during first-time schema creation)
                pass
except Exception:
    pass


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
