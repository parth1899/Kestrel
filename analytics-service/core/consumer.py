# analytics-service/core/consumer.py
import uuid
import aio_pika
import json
import asyncio
from typing import Callable
from jsonschema import validate, ValidationError

from core.models import EnrichedEvent, Alert
from core.alerting import publish_alert, write_alert_to_db
from utils.logger import log
from detectors.ensemble import EnsembleDetector


# --------------------------------------------------------------------------- #
# The extractor factory is *injected* – no direct import of features here
# --------------------------------------------------------------------------- #
ExtractorFactory = Callable[[str], "BaseFeatureExtractor"]   # forward ref OK


async def start_consumer(
    config: dict,
    get_extractor: ExtractorFactory,          # <-- injected
) -> None:
    """
    Consume ``events.enriched.*`` messages, run the analytics pipeline
    and emit alerts when the score exceeds the threshold.
    """
    connection = await aio_pika.connect_robust(config["rabbitmq"]["url"])
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            config["rabbitmq"]["exchange"], aio_pika.ExchangeType.TOPIC, durable=True
        )

        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange, routing_key="events.enriched.#")

        ensemble = EnsembleDetector()

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = message.body.decode()
                        data = json.loads(body)

                        # ---- schema validation ------------------------------------------------
                        with open("schemas/enriched_event.json") as f:
                            schema = json.load(f)
                        validate(instance=data, schema=schema)

                        # ---- turn into Pydantic model -----------------------------------------
                        event = EnrichedEvent(**data)

                        # ---- feature extraction (injected) ------------------------------------
                        extractor = get_extractor(event.event_type)
                        features = extractor.extract(event)

                        # ---- detection ---------------------------------------------------------
                        score, reasons = ensemble.detect(
                            features, event.agent_id, event.event_type
                        )

                        # ---- alerting ----------------------------------------------------------
                        if score >= 50:
                            severity = (
                                "critical" if score >= 80 else
                                "high" if score >= 65 else
                                "medium"
                            )
                            alert = Alert(
                                id=uuid.uuid4(),
                                event_id=event.event_id,
                                agent_id=event.agent_id,
                                event_type=event.event_type,
                                score=score,
                                severity=severity,
                                source="analytics",
                                details={
                                    "features": features,
                                    "reasons": reasons,
                                    "model": "ensemble",
                                },
                            )
                            write_alert_to_db(alert)
                            await publish_alert(channel, alert, config)

                    except ValidationError as e:
                        log.error(f"Schema validation failed: {e}")
                    except Exception as e:                     # pragma: no cover
                        log.error(f"Unexpected processing error: {e}")