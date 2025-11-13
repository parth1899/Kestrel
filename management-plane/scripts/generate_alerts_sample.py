"""Generate synthetic alerts to populate the alerts table and drive decisions.

Usage:
  python -m scripts.generate_alerts_sample 30

This will insert N alerts with a mix of severities and event types.
"""
import sys
import uuid
import random
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

from utils.db import engine

COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 20

severities = ["low", "medium", "high", "critical"]
event_types = ["process", "network", "file", "system"]

def build_details(event_type: str) -> dict:
    base = {"model": "ensemble", "features": {}, "reasons": {"rule": [], "anomaly": [], "behavioral": []}}
    if event_type == "process":
        base["features"] = {
            "process_name": random.choice(["mimikatz.exe", "calc.exe", "powershell.exe", "svchost.exe"]),
            "hash_known_malicious": random.choice([True, False, False]),
            "vt_positives": random.randint(0, 70),
            "is_suspicious_path": random.choice([True, False]),
            "yara_hits_count": random.randint(0, 3),
        }
    elif event_type == "network":
        base["features"] = {
            "remote_ip": random.choice(["127.0.0.1", "95.111.200.207", "13.73.244.6", "10.0.0.5"]),
            "local_ip": "192.168.1." + str(random.randint(2, 250)),
            "remote_port": random.randint(1024, 65000),
            "protocol": random.choice(["TCP", "UDP"]),
            "is_loopback": False,
            "is_private_ip": random.choice([True, False]),
            "threat_score": random.uniform(0, 90),
        }
    elif event_type == "file":
        base["features"] = {
            "file_name": random.choice(["payload.dll", "report.docx", "script.ps1", "archive.zip"]),
            "yara_hits_count": random.randint(0, 5),
            "hash_known_malicious": random.choice([True, False, False]),
        }
    else:
        base["features"] = {
            "cpu_usage": random.uniform(0, 95),
            "memory_pressure": random.uniform(0, 95),
        }
    # Reasons
    if random.random() < 0.4:
        base["reasons"]["anomaly"].append("anomaly_high")
    if random.random() < 0.3:
        base["reasons"]["behavioral"].append("behavioral_outlier")
    if random.random() < 0.5:
        base["reasons"]["rule"].append("rule_" + str(random.randint(1, 5)))
    return base

with engine.begin() as conn:
    for i in range(COUNT):
        alert_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        agent_id = "windows-agent-001"
        event_type = random.choice(event_types)
        severity = random.choice(severities)
        score = round(random.uniform(10, 95), 2)
        details = build_details(event_type)
        ts = datetime.utcnow() - timedelta(minutes=random.randint(0, 120))
        conn.execute(
            text(
                """
                INSERT INTO alerts (
                  id, event_id, agent_id, event_type, score, severity, source, details, created_at
                ) VALUES (
                  :id, :event_id, :agent_id, :event_type, :score, :severity, :source, :details, :created_at
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": alert_id,
                "event_id": event_id,
                "agent_id": agent_id,
                "event_type": event_type,
                "score": score,
                "severity": severity,
                "source": "analytics",
                "details": json.dumps(details),
                "created_at": ts,
            },
        )

print(f"Inserted {COUNT} synthetic alerts.")