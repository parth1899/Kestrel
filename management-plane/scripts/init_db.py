import os
import sys

# Allow running as `python -m scripts.init_db` from project root OR `python init_db.py` from scripts/
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.db import init_database

if __name__ == "__main__":
    init_database()
    print("Database initialized.")
