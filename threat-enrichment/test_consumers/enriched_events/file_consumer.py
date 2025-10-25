#!/usr/bin/env python3
"""
Enriched File Event Consumer
Listens: events.enriched.windows-agent-001.file
"""
import json
import pika
import os
from dotenv import load_dotenv

load_dotenv()
print("FILE ENRICHED CONSUMER STARTED")
print("Listening for: events.enriched.windows-agent-001.file\n")

conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
ch = conn.channel()
q = ch.queue_declare('', exclusive=True).method.queue
ch.queue_bind(exchange='events', queue=q, routing_key='events.enriched.*.file')

def cb(ch, m, p, body):
    data = json.loads(body)
    e = data['enrichment']
    print("\n" + "="*60)
    print("ENRICHED FILE EVENT")
    print("="*60)
    print(f"Event ID : {data['event_id']}")
    print(f"File     : {data['payload'].get('file_name')}")
    print(f"Path     : {data['payload'].get('file_path')}")
    print(f"Hash     : {data['payload'].get('file_hash')}")
    print(f"Score    : {e.get('threat_score', 0):.1f}/100")
    print("-" * 40)
    if e.get('yara_hits'):
        print(f"YARA     : {', '.join(e['yara_hits'])}")
    if e['reputation'].get('vt', {}).get('positives', 0) > 0:
        vt = e['reputation']['vt']
        print(f"VT       : {vt['positives']}/{vt['total']} engines")
    if e['reputation'].get('otx', {}).get('pulses', 0) > 0:
        print(f"OTX      : {e['reputation']['otx']['pulses']} pulses")
    if e.get('ioc_matches'):
        print(f"IOCs     : {', '.join(e['ioc_matches'])}")
    print("\nFULL ENRICHMENT:")
    print(json.dumps(e, indent=2))
    print("="*60 + "\n")
    ch.basic_ack(m.delivery_tag)

ch.basic_consume(queue=q, on_message_callback=cb)
ch.start_consuming()