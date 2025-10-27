#!/usr/bin/env python3
"""
Enriched Process Event Consumer
Listens: events.enriched.windows-agent-001.process
"""
import json
import pika
import os
from dotenv import load_dotenv

load_dotenv()
print("PROCESS ENRICHED CONSUMER STARTED")
print("Listening for: events.enriched.windows-agent-001.process\n")

conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
ch = conn.channel()
q = ch.queue_declare('', exclusive=True).method.queue
ch.queue_bind(exchange='events', queue=q, routing_key='events.enriched.*.process')

def cb(ch, m, p, body):
    data = json.loads(body)
    e = data['enrichment']
    payload = data['payload']
    print("\n" + "="*60)
    print("ENRICHED PROCESS EVENT")
    print("="*60)
    print(f"Event ID : {data['event_id']}")
    print(f"Process  : {payload.get('process_name')} (PID: {payload.get('process_id')})")
    print(f"Parent   : PID {payload.get('parent_process_id')}")
    print(f"Cmdline  : {payload.get('command_line')}")
    print(f"Score    : {e.get('threat_score', 0):.1f}/100")
    print("-" * 40)
    if e.get('ioc_matches'):
        print(f"IOCs     : {', '.join(e['ioc_matches'])}")
    if e.get('reputation', {}).get('vt'):
        print(f"VT       : {e['reputation']['vt']['positives']}/{e['reputation']['vt']['total']}")
    print("\nFULL ENRICHMENT:")
    print(json.dumps(e, indent=2))
    print("="*60 + "\n")
    ch.basic_ack(m.delivery_tag)

ch.basic_consume(queue=q, on_message_callback=cb)
ch.start_consuming()