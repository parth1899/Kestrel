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
  "event_type": "system",
  "payload": {
    "architecture": "amd64",
    "available_memory": 1073741824,
    "cpu_count": 4,
    "cpu_usage": 98.5,
    "disk_usage": 99.9,
    "hostname": "Parths-Laptop",
    "os_version": "windows amd64",
    "total_memory": 16910159872,
    "uptime": 300
  },
  "enrichment": {
    "ioc_matches": ["high_resource_usage"],
    "reputation": {},
    "yara_hits": [],
    "geoip": {},
    "threat_score": 95.0
  },
  "timestamp": "2025-10-29T23:02:00+05:30"
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