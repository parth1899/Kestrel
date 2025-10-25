#!/usr/bin/env python3
"""
Component A: Threat Intelligence Enrichment Service
"""
import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import os
import yaml
import pika
import psycopg2
import redis
import httpx
import yara
import geoip2.database
from jsonschema import validate, ValidationError
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("enrichment")

# Load config
with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

# Connections
pg_conn = psycopg2.connect(os.getenv("DATABASE_DSN", CONFIG['database']['dsn'] % os.environ))
redis_client = redis.Redis(host=CONFIG['redis']['host'], port=CONFIG['redis']['port'], db=CONFIG['redis']['db'], decode_responses=True)
geoip_reader = geoip2.database.Reader(CONFIG['enrichment']['geoip_db'])
yara_rules = yara.compile(filepath="yara_rules/suspicious.yar")

OTX_API_KEY = os.getenv("OTX_API_KEY")
VT_API_KEY = os.getenv("VT_API_KEY")

# Schemas
with open("schemas/raw_event.json") as f:
    RAW_SCHEMA = json.load(f)
with open("schemas/enriched_event.json") as f:
    ENRICHED_SCHEMA = json.load(f)

app = FastAPI(title="Threat Enrichment Service")

class Health(BaseModel):
    status: str
    components: Dict[str, bool]

@app.get("/health", response_model=Health)
def health():
    return {
        "status": "healthy",
        "components": {
            "rabbitmq": True,
            "postgres": pg_conn.closed == 0,
            "redis": redis_client.ping(),
            "geoip": True
        }
    }

# === ENRICHMENT FUNCTIONS ===
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def otx_lookup(indicator: str, indicator_type: str) -> Dict:
    if indicator_type == "hash":
        url = f"https://otx.alienvault.com/api/v1/indicators/file/{indicator}/general"
    elif indicator_type == "ip":
        url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{indicator}/general"
    else:
        raise ValueError("Unsupported indicator type")

    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return {"pulses": data.get("pulse_info", {}).get("count", 0)}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def vt_lookup(file_hash: str) -> Dict:
    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    headers = {"x-apikey": VT_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            return {"positives": 0, "total": 0}
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        return {"positives": data.get("malicious", 0) + data.get("suspicious", 0), "total": sum(data.values())}

async def enrich_file(event: Dict) -> Dict:
    payload = event['payload']
    file_hash = payload.get('file_hash')
    file_name = payload.get('file_name', '')
    enrichment = {
        "ioc_matches": [],
        "reputation": {"vt": {}, "otx": {}},
        "yara_hits": [],
        "geoip": {},
        "threat_score": 0.0
    }

    # YARA on file_name
    try:
        matches = yara_rules.match(data=file_name)
        enrichment['yara_hits'] = [m.rule for m in matches]
        if matches:
            enrichment['threat_score'] += 30
    except Exception as e:
        log.warning(f"YARA failed: {e}")

    if file_hash:
        # VT
        cache_key_vt = f"vt:{file_hash}"
        cached_vt = redis_client.get(cache_key_vt)
        if cached_vt:
            vt = json.loads(cached_vt)
        else:
            try:
                vt = await vt_lookup(file_hash)
                redis_client.setex(cache_key_vt, timedelta(hours=CONFIG['redis']['ttl_hours']), json.dumps(vt))
            except Exception as e:
                log.error(f"VT failed: {e}")
                vt = {"positives": 0, "total": 0}
        enrichment['reputation']['vt'] = vt
        if vt['positives'] > 0:
            enrichment['ioc_matches'].append("vt_malicious")
            enrichment['threat_score'] += (vt['positives'] / vt['total']) * 50 if vt['total'] > 0 else 0

        # OTX for hash
        cache_key_otx = f"otx:hash:{file_hash}"
        cached_otx = redis_client.get(cache_key_otx)
        if cached_otx:
            otx = json.loads(cached_otx)
        else:
            try:
                otx = await otx_lookup(file_hash, "hash")
                redis_client.setex(cache_key_otx, timedelta(hours=CONFIG['redis']['ttl_hours']), json.dumps(otx))
            except Exception as e:
                log.error(f"OTX hash failed: {e}")
                otx = {"pulses": 0}
        enrichment['reputation']['otx'] = otx
        if otx['pulses'] > 0:
            enrichment['ioc_matches'].append("otx_pulses")
            enrichment['threat_score'] += min(otx['pulses'] * 5, 20)

    enrichment['threat_score'] = min(enrichment['threat_score'], 100)
    enrichment['ioc_matches'] = list(set(enrichment['ioc_matches']))  # Dedup
    return enrichment

async def enrich_network(event: Dict) -> Dict:
    payload = event['payload']
    remote_ip = payload.get('remote_ip')
    enrichment = {
        "ioc_matches": [],
        "reputation": {"otx": {}},
        "yara_hits": [],
        "geoip": {},
        "threat_score": 0.0
    }

    if remote_ip and remote_ip not in ["::1", "127.0.0.1", "0.0.0.0"]:
        # GeoIP
        cache_key_geo = f"geoip:{remote_ip}"
        cached_geo = redis_client.get(cache_key_geo)
        if cached_geo:
            enrichment['geoip'] = json.loads(cached_geo)
        else:
            try:
                resp = geoip_reader.city(remote_ip)
                geo_data = {
                    "country": resp.country.name,
                    "city": resp.city.name,
                    "lat": resp.location.latitude,
                    "lon": resp.location.longitude
                }
                enrichment['geoip'] = geo_data
                redis_client.setex(cache_key_geo, timedelta(hours=CONFIG['redis']['ttl_hours']), json.dumps(geo_data))
            except Exception as e:
                log.warning(f"GeoIP failed: {e}")

        # OTX for IP
        cache_key_otx = f"otx:ip:{remote_ip}"
        cached_otx = redis_client.get(cache_key_otx)
        if cached_otx:
            otx = json.loads(cached_otx)
        else:
            try:
                otx = await otx_lookup(remote_ip, "ip")
                redis_client.setex(cache_key_otx, timedelta(hours=CONFIG['redis']['ttl_hours']), json.dumps(otx))
            except Exception as e:
                log.error(f"OTX IP failed: {e}")
                otx = {"pulses": 0}
        enrichment['reputation']['otx'] = otx
        if otx['pulses'] > 0:
            enrichment['ioc_matches'].append("otx_pulses_ip")
            enrichment['threat_score'] += min(otx['pulses'] * 5, 30)

    enrichment['ioc_matches'] = list(set(enrichment['ioc_matches']))
    return enrichment

# === CONSUMER ===
def process_message(ch, method, properties, body):
    try:
        raw = json.loads(body)
        validate(raw, RAW_SCHEMA)

        event_type = raw['event_type']
        enrichment = {}

        if event_type == "file":
            enrichment = asyncio.run(enrich_file(raw))
        elif event_type == "network":
            enrichment = asyncio.run(enrich_network(raw))

        # Save to DB
        cur = pg_conn.cursor()
        cur.execute("""
            INSERT INTO enrichments (
                id, event_type, event_id, agent_id,
                ioc_matches, reputation, yara_hits, geoip, threat_score, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            str(uuid.uuid4()),
            event_type,
            raw['event_id'],
            raw['agent_id'],
            json.dumps(enrichment.get('ioc_matches', [])),
            json.dumps(enrichment.get('reputation', {})),
            json.dumps(enrichment.get('yara_hits', [])),
            json.dumps(enrichment.get('geoip', {})),
            enrichment.get('threat_score', 0)
        ))
        pg_conn.commit()
        cur.close()

        # Publish enriched
        enriched_event = {
            "event_id": raw['event_id'],
            "agent_id": raw['agent_id'],
            "event_type": event_type,
            "payload": raw['payload'],
            "enrichment": enrichment,
            "timestamp": raw['timestamp']
        }
        validate(enriched_event, ENRICHED_SCHEMA)

        ch.basic_publish(
            exchange=CONFIG['rabbitmq']['exchange'],
            routing_key=f"events.enriched.{raw['agent_id']}.{event_type}",
            body=json.dumps(enriched_event)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log.info(f"Enriched {event_type}: {raw['event_id']} | Score: {enrichment.get('threat_score', 0)}")

    except ValidationError as e:
        log.error(f"Schema failed: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        log.error(f"Failed: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consumer():
    conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
    ch = conn.channel()
    ch.exchange_declare(exchange='events', exchange_type='topic', durable=True)
    q = ch.queue_declare('', exclusive=True).method.queue
    ch.queue_bind(exchange='events', queue=q, routing_key='events.raw.#')
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=q, on_message_callback=process_message)
    log.info("Enrichment service consuming events.raw.#")
    ch.start_consuming()

# === ENTRYPOINT ===
if __name__ == "__main__":
    import threading
    threading.Thread(target=start_consumer, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)