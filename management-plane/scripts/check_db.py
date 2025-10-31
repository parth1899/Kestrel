import os
import sys
from sqlalchemy import text

# Allow running as `python -m scripts.check_db` from project root OR `python check_db.py` from scripts/
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.db import engine, init_database


def main():
    print(f"Using DSN: {os.getenv('DATABASE_DSN', 'sqlite:///./management.db')}")
    init_database()
    # If using Postgres, query information_schema. For SQLite fallback, show sqlite_master.
    schema = os.getenv("MANAGEMENT_SCHEMA", "management")
    with engine.connect() as conn:
        # Print current DB and available schemas if Postgres
        if os.getenv("DATABASE_DSN", "").startswith("postgres") or os.getenv("DATABASE_DSN", "").startswith("postgresql"):
            dsn = os.getenv("DATABASE_DSN", "")
            if "sslmode" not in dsn:
                print("[hint] Neon often requires sslmode=require. Consider appending '?sslmode=require' to DATABASE_DSN.\n")
            try:
                dbname = conn.execute(text("SELECT current_database()"))
                print(f"Current database: {dbname.scalar()}\n")
            except Exception:
                pass
            try:
                result = conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
                schemas = ", ".join([r[0] for r in result.fetchall()])
                print(f"Available schemas: {schemas}")
            except Exception:
                pass
        if os.getenv("DATABASE_DSN", "").startswith("postgres") or os.getenv("DATABASE_DSN", "").startswith("postgresql"):
            result = conn.execute(
                text(
                    """
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                    ORDER BY table_name
                    """
                ),
                {"schema": schema},
            )
            rows = result.fetchall()
            print("Management schema tables:")
            for r in rows:
                print(f" - {r.table_schema}.{r.table_name}")
        else:
            # SQLite: list tables
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ))
            rows = result.fetchall()
            print("SQLite tables:")
            for r in rows:
                print(f" - {r[0]}")


if __name__ == "__main__":
    main()
