from __future__ import annotations
import aio_pika
import asyncio
import json
from typing import Any, Dict
from ..utils.config import load_config
from ..utils.logger import logger, audit
from ..genai.generator import find_existing_playbook, generate_playbook

# RabbitMQ consumer that reacts to alerts.* messages by ensuring a playbook exists.

async def _handle_alert(alert: Dict[str, Any]) -> None:
    existing = find_existing_playbook(alert)
    if existing is None:
        path = await generate_playbook(alert)
        logger.info(f"Generated playbook at {path}")
    else:
        logger.info(f"Found playbook: {existing}")


async def start_consumer() -> None:
    cfg = load_config()
    if not cfg["messaging"].get("enabled", True):
        logger.info("RabbitMQ consumer disabled via config")
        return

    url = cfg["messaging"]["rabbitmq_url"]
    exchange_name = cfg["messaging"]["exchange"]
    routing = cfg["messaging"].get("routing_key", "alerts.*")

    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange, routing_key=routing)
        logger.info(f"Bound to {exchange_name}:{routing}")
        async with queue.iterator() as it:
            async for msg in it:
                async with msg.process():
                    try:
                        payload = json.loads(msg.body.decode())
                        audit("alert_received", {"routing": msg.routing_key, "agent_id": payload.get("agent_id")})
                        await _handle_alert(payload)
                    except Exception as e:
                        logger.error(f"Alert handling error: {e}")


async def tail_file(path: str) -> None:
    # Optional local mode: tail a JSONL file and handle alerts as they appear.
    import aiofiles
    logger.info(f"Tailing alerts file: {path}")
    async with aiofiles.open(path, "r") as f:
        await f.seek(0, 2)
        while True:
            line = await f.readline()
            if not line:
                await asyncio.sleep(0.5)
                continue
            try:
                alert = json.loads(line)
                await _handle_alert(alert)
            except Exception as e:
                logger.error(f"File tail error: {e}")


async def ingest_file_once(path: str) -> None:
    # Process a JSON array file or JSONL file once (no tailing), suitable for batch runs.
    try:
        if path.lower().endswith(".jsonl"):
            # stream JSONL
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    alert = json.loads(line)
                    await _handle_alert(alert)
        else:
            # assume a JSON array of alerts
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for alert in data:
                    await _handle_alert(alert)
            elif isinstance(data, dict):
                # single alert dictionary
                await _handle_alert(data)
            else:
                logger.error("Unsupported JSON structure in alerts file")
    except Exception as e:
        logger.error(f"File ingestion error: {e}")
