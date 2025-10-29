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
  "event_type": "network",
  "payload": {
    "bytes_received": 2048,
    "bytes_sent": 1024,
    "connection_id": "192.168.1.100:50000-185.156.47.22:443-TCP",
    "event_type": "connect",
    "local_ip": "192.168.1.100",
    "local_port": 50000,
    "process_id": 1234,
    "process_name": "powershell.exe",
    "protocol": "TCP",
    "remote_ip": "185.156.47.22",
    "remote_port": 443,
    "severity": "high"
  },
  "enrichment": {
    "ioc_matches": ["known_c2"],
    "reputation": {
      "otx": {"pulses": 85}
    },
    "yara_hits": [],
    "geoip": {
      "country": "Russia",
      "city": "Moscow",
      "lat": 55.75,
      "lon": 37.62,
      "org": "Malicious ISP"
    },
    "threat_score": 90.0
  },
  "timestamp": "2025-10-29T23:01:00+05:30"
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