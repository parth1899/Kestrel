# scripts/simulate_alerts.py
#!/usr/bin/env python3
import asyncio
import aio_pika
import json
import uuid
from dotenv import load_dotenv
import os

load_dotenv()

SAMPLE_EVENT = {
  "event_id": str(uuid.uuid4()),
  "agent_id": "windows-agent-001",
  "event_type": "process",
  "payload": {
    "command_line": "mimikatz.exe \"sekurlsa::logonpasswords\" exit",
    "cpu_usage": 85.5,
    "end_time": "2025-10-28T23:56:51.9416524+05:30",
    "event_type": "start",
    "executable_path": "C:\\Temp\\mimikatz.exe",
    "hash": "d41d8cd98f00b204e9800998ecf8427e",
    "memory_usage": 52428800,
    "parent_process_id": 0,
    "process_id": 9999,
    "process_name": "mimikatz.exe",
    "severity": "high",
    "signature": "",
    "start_time": "2025-10-29T12:00:00+05:30",
    "username": "PARTHS-LAPTOP\\parth"
  },
  "enrichment": {
    "ioc_matches": ["system_parent", "suspicious_command"],
    "reputation": {
      "vt": {"positives": 67, "total": 76}
    },
    "yara_hits": ["mimikatz", "credential_dumper", "sekurlsa"],
    "geoip": {},
    "threat_score": 95.0
  },
  "timestamp": "2025-10-29T12:00:01+05:30"
}

async def main():
    connection = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
    async with connection:
        channel = await connection.channel()
        exchange = await channel.get_exchange("events")

        message = aio_pika.Message(
            body=json.dumps(SAMPLE_EVENT).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        routing_key = f"events.enriched.{SAMPLE_EVENT['agent_id']}.{SAMPLE_EVENT['event_type']}"
        await exchange.publish(message, routing_key=routing_key)

        print(f"PUBLISHED → {routing_key}")
        print(f"   event_id: {SAMPLE_EVENT['event_id']}")
        print(f"   threat_score: {SAMPLE_EVENT['enrichment']['threat_score']}")

if __name__ == "__main__":
    asyncio.run(main())