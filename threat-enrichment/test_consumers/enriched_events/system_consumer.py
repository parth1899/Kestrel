#!/usr/bin/env python3
"""
Enriched System Event Consumer
Listens: events.enriched.windows-agent-001.system
"""
import json
import pika
import os
from dotenv import load_dotenv

load_dotenv()
print("SYSTEM ENRICHED CONSUMER STARTED")
print("Listening for: events.enriched.windows-agent-001.system\n")

conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
ch = conn.channel()
q = ch.queue_declare('', exclusive=True).method.queue
ch.queue_bind(exchange='events', queue=q, routing_key='events.enriched.*.system')

def cb(ch, m, p, body):
    data = json.loads(body)
    e = data['enrichment']
    payload = data['payload']
    print("\n" + "="*60)
    print("ENRICHED SYSTEM EVENT")
    print("="*60)
    print(f"Event ID : {data['event_id']}")
    print(f"Host     : {payload.get('hostname')}")
    print(f"OS       : {payload.get('os_version')} {payload.get('architecture')}")
    print(f"Memory   : {payload.get('available_memory', 0) / (1024**3):.1f} GB free")
    print(f"CPU      : {payload.get('cpu_usage', 0):.1f}%")
    print(f"Score    : {e.get('threat_score', 0):.1f}/100")
    print("-" * 40)
    print("\nFULL ENRICHMENT:")
    print(json.dumps(e, indent=2))
    print("="*60 + "\n")
    ch.basic_ack(m.delivery_tag)

ch.basic_consume(queue=q, on_message_callback=cb)
ch.start_consuming()