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
  "event_type": "file",
  "payload": {
    "event_type": "create",
    "file_hash": "a" * 64,
    "file_name": "__PSScriptPolicyTest_malicious.ps1",
    "file_path": "C:\\Users\\parth\\AppData\\Local\\Temp\\__PSScriptPolicyTest_malicious.ps1",
    "file_size": 1024,
    "file_type": ".ps1",
    "process_id": 0,
    "process_name": "",
    "severity": "high"
  },
  "enrichment": {
    "ioc_matches": ["otx_pulses", "suspicious_name"],
    "reputation": {
      "vt": {"positives": 45, "total": 76},
      "otx": {"pulses": 120}
    },
    "yara_hits": ["PowerShell_Suspicious_Temp_File", "Malicious_PS1_Dropper"],
    "geoip": {},
    "threat_score": 85.0
  },
  "timestamp": "2025-10-29T23:00:00+05:30"
}

async def main():
    conn = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
    async with conn:
        channel = await conn.channel()
        exchange = await channel.get_exchange("events")
        body = json.dumps(SAMPLE_EVENT).encode()
        message = aio_pika.Message(body=body, content_type="application/json", delivery_mode=2)
        rk = f"events.enriched.{SAMPLE_EVENT['agent_id']}.{SAMPLE_EVENT['event_type']}"
        await exchange.publish(message, routing_key=rk)
        print(f"PUBLISHED → {rk}")
        print(f"   threat_score: {SAMPLE_EVENT['enrichment']['threat_score']}")

if __name__ == "__main__":
    asyncio.run(main())