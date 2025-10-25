#!/usr/bin/env python3
"""
Network Events Consumer
Listens to: events.raw.windows-agent-001.network
"""
import json
import pika
from datetime import datetime
import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    print("NETWORK CONSUMER STARTED")
    print("Listening for: events.raw.windows-agent-001.network\n")

    connection = pika.BlockingConnection(
        pika.URLParameters(os.getenv("RABBITMQ_URL"))
    )
    channel = connection.channel()
    channel.exchange_declare(exchange='events', exchange_type='topic', durable=True)

    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='events', queue=queue_name, routing_key='events.raw.windows-agent-001.network')

    def callback(ch, method, properties, body):
        event = json.loads(body)
        payload = event['payload']
        # print("\nFULL NETWORK PAYLOAD:")
        print(json.dumps(payload, indent=2))
        # print(f"{datetime.now().strftime('%H:%M:%S')} [NETWORK] {payload.get('local_ip')}:{payload.get('local_port')} → {payload.get('remote_ip')}:{payload.get('remote_port')} ({payload.get('process_name')})")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":
    main()