from utils.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID PRIMARY KEY,
            event_id UUID NOT NULL,
            agent_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            score NUMERIC NOT NULL,
            severity TEXT NOT NULL,
            source TEXT NOT NULL,
            details JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """))
    conn.commit()
print("Alerts table ready.")