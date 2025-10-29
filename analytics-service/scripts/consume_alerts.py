#!/usr/bin/env python3
import asyncio
import aio_pika
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    conn = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
    async with conn:
        channel = await conn.channel()
        exchange = await channel.get_exchange("alerts")

        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange, routing_key="alerts.#")

        print("ALERT CONSUMER STARTED — Listening on alerts.#")
        print("Press Ctrl+C to stop.\n")

        async with queue.iterator() as q:
            async for msg in q:
                async with msg.process():
                    data = json.loads(msg.body)
                    severity = data.get("severity", "unknown")
                    score = data.get("score", 0)
                    event_type = data.get("event_type", "unknown")
                    process = data["details"]["features"].get("process_name", "N/A")

                    print(f"ALERT [{severity.upper()}] score={score} | {event_type} | {process}")
                    print(f"   event_id: {data['event_id']}")
                    print(f"   reasons: {data['details']['reasons']}")
                    print("-" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")