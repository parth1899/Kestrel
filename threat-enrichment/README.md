This microservice implements a Threat Intelligence Enrichment Service — part of the cybersecurity event-processing pipeline. Its job is to receive raw security events, enrich them with external threat intelligence sources, and output enriched events with a calculated threat score.

The service consists of three main parts:
1. FastAPI web server — provides a /health endpoint for monitoring service health.
2. RabbitMQ consumer — listens for raw events on a message queue (events.raw.#).
3. Enrichment logic — fetches intelligence data (VirusTotal, OTX, GeoIP, YARA) and enriches each event.

After enrichment, it stores results in PostgreSQL and republishes enriched events to RabbitMQ.