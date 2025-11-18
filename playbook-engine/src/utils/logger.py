import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

# Centralized logger and JSONL auditor. Keeps simple, thread/async-safe writes.

BASE_DIR = Path(__file__).resolve().parents[2]  # playbook-engine/
DATA_DIR = BASE_DIR / "data"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure app logger
logger = logging.getLogger("playbook_engine")
logger.setLevel(logging.INFO)

_stream = logging.StreamHandler()
_stream.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(_stream)

_file = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=2_000_000, backupCount=3)
_file.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(_file)


def audit(event: str, payload: Dict[str, Any]) -> None:
    """Append a single JSON line to data/audit.jsonl with UTC timestamp."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.utcnow().isoformat() + "Z", "event": event, **payload}
    # Keeping IO simple and safe for low throughput. For high TPS, use a queue.
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
