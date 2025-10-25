#!/usr/bin/env python3
"""
Process Events Consumer
Listens to: events.raw.windows-agent-001.process
"""
import json
import pika
from datetime import datetime
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("PROCESS CONSUMER STARTED")
    print("Listening for: events.raw.windows-agent-001.process\n")

    # connection = pika.BlockingConnection(
    #     pika.ConnectionParameters(host='localhost')
    # )
    connection = pika.BlockingConnection(
        pika.URLParameters(os.getenv("RABBITMQ_URL"))
    )
    channel = connection.channel()
    channel.exchange_declare(exchange='events', exchange_type='topic', durable=True)

    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='events', queue=queue_name, routing_key='events.raw.windows-agent-001.process')

    def callback(ch, method, properties, body):
        event = json.loads(body)
        payload = event['payload']
        # print("\nFULL PROCESS PAYLOAD:")
        print(json.dumps(payload, indent=2))
        # print(f"{datetime.now().strftime('%H:%M:%S')} [PROCESS] {event['payload'].get('process_name', 'unknown')} (PID: {event['payload'].get('process_id')})")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":
    main()