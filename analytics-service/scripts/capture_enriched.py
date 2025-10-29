#!/usr/bin/env python3
import aio_pika
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
OUTPUT_DIR.mkdir(exist_ok=True)

async def capture():
    conn = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
    async with conn:
        channel = await conn.channel()
        exchange = await channel.get_exchange("events")  # 👈 don't redeclare it

        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange, "events.enriched.#")

        print(f"Capturing to {OUTPUT_DIR}... Press Ctrl+C to stop.")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        event_type = data["event_type"]
                        event_id = data["event_id"]

                        filename = f"enriched_{event_type}_{event_id[:8]}.json"
                        with open(OUTPUT_DIR / filename, "w") as f:
                            json.dump(data, f, indent=2)
                        print(f"Saved {filename}")
                    except Exception as e:
                        print("Error processing message:", e)

if __name__ == "__main__":
    asyncio.run(capture())
