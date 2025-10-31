import os
import sys

# Allow running as `python -m scripts.sample_data` from project root OR `python sample_data.py` from scripts/
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.db import session_scope
from models import Policy, Rule, DetectorConfig


def seed():
    with session_scope() as db:
        policy = Policy(name="Default Policy", description="Baseline policy")
        db.add(policy)
        db.flush()

        rule = Rule(
            name="Block suspicious process",
            type="rule_based",
            definition='{"process_name": "malware.exe", "action": "alert"}',
            policy_id=policy.id,
        )
        db.add(rule)

        det = DetectorConfig(
            detector_name="rule_based",
            params='{"severity_threshold": "medium"}',
            version="1.0",
        )
        db.add(det)


if __name__ == "__main__":
    seed()
    print("Seed data inserted.")
