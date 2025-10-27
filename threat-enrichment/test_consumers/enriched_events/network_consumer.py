#!/usr/bin/env python3
"""
Enriched Network Event Consumer
Listens: events.enriched.windows-agent-001.network
"""
import json
import pika
import os
from dotenv import load_dotenv

load_dotenv()
print("NETWORK ENRICHED CONSUMER STARTED")
print("Listening for: events.enriched.windows-agent-001.network\n")

conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
ch = conn.channel()
q = ch.queue_declare('', exclusive=True).method.queue
ch.queue_bind(exchange='events', queue=q, routing_key='events.enriched.*.network')

def cb(ch, m, p, body):
    data = json.loads(body)
    e = data['enrichment']
    payload = data['payload']
    print("\n" + "="*60)
    print("ENRICHED NETWORK EVENT")
    print("="*60)
    print(f"Event ID : {data['event_id']}")
    print(f"Conn     : {payload.get('local_ip')}:{payload.get('local_port')} → {payload.get('remote_ip')}:{payload.get('remote_port')}")
    print(f"Process  : {payload.get('process_name')} (PID: {payload.get('process_id')})")
    print(f"Score    : {e.get('threat_score', 0):.1f}/100")
    print("-" * 40)
    if e.get('geoip'):
        g = e['geoip']
        print(f"GeoIP    : {g.get('city')}, {g.get('country')} ({g.get('lat')}, {g.get('lon')})")
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