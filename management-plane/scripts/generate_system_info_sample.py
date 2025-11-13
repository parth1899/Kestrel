"""Generate sample rows for system_info to make metrics & charts non-empty.

Usage (PowerShell):
  python -m scripts.generate_system_info_sample 50
This will insert 50 synthetic system_info rows spanning the last ~50 minutes.

Requires that the `system_info` table exists in the connected Postgres DB.
"""
import os
import sys
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

from utils.db import engine  # uses same DATABASE_DSN & search_path

COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 30

hostnames = ["endpoint-a", "endpoint-b", "endpoint-c"]
oses = ["Windows 10", "Windows 11", "Windows Server 2022"]
architectures = ["x64", "arm64"]

with engine.begin() as conn:
    for i in range(COUNT):
        ts = datetime.utcnow() - timedelta(minutes=(COUNT - i))
        cpu_usage = random.uniform(5, 95)
        total_memory = 16 * 1024 * 1024 * 1024  # 16GB bytes
        available_memory = total_memory - int(random.uniform(0.1, 0.95) * total_memory)
        disk_usage = random.uniform(10, 98)
        uptime = random.randint(300, 200000)
        hostname = random.choice(hostnames)
        agent_id = f"agent-{hostname}"
        os_version = random.choice(oses)
        architecture = random.choice(architectures)
        cpu_count = random.choice([4, 8, 16])
        conn.execute(
            text(
                """
                INSERT INTO system_info (
                  id, agent_id, hostname, os_version, architecture, total_memory, available_memory,
                  cpu_count, cpu_usage, disk_usage, uptime, timestamp
                ) VALUES (
                  :id, :agent_id, :hostname, :os_version, :architecture, :total_memory, :available_memory,
                  :cpu_count, :cpu_usage, :disk_usage, :uptime, :timestamp
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "hostname": hostname,
                "os_version": os_version,
                "architecture": architecture,
                "total_memory": total_memory,
                "available_memory": available_memory,
                "cpu_count": cpu_count,
                "cpu_usage": cpu_usage,
                "disk_usage": disk_usage,
                "uptime": uptime,
                "timestamp": ts,
            },
        )

print(f"Inserted {COUNT} synthetic system_info rows.")