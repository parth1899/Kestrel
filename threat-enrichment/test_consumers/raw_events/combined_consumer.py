#!/usr/bin/env python3
"""
Simple RabbitMQ Consumer Test - Catches events.raw.* from Windows Agent
Routing: events.raw.windows-agent-001.process/file/network/system
"""

import json
import pika
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

def callback(ch, method, properties, body):
    """Process each raw event"""
    try:
        # Parse JSON
        event = json.loads(body)
        
        # Pretty print
        print(f"\n{'='*80}")
        print(f"[ * ] RAW EVENT RECEIVED")
        print(f"{'='*80}")
        print(f"[i] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[>] Routing Key: {method.routing_key}")
        print(f"[#] Event ID: {event.get('event_id', 'N/A')}")
        print(f"[!] Agent ID: {event.get('agent_id', 'N/A')}")
        print(f"[~] Event Type: {event.get('event_type', 'N/A')}")
        print(f"[t] Timestamp: {event.get('timestamp', 'N/A')}")
        
        # Pretty print payload
        payload = event.get('payload', {})
        print(f"\n[>] PAYLOAD:")
        print(json.dumps(payload, indent=2, default=str))
        
        print(f"{'='*80}\n")
        
        # ACK the message (remove this line to see messages accumulate in queue)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError as e:
        print(f"[x] Invalid JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[x] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def main():
    load_dotenv()
    
    # Connect
    print("[*] Connecting to RabbitMQ...")
    connection = pika.BlockingConnection(
        pika.URLParameters(os.getenv("RABBITMQ_URL"))
    )
    channel = connection.channel()
    
    # Declare exchange (same as agent)
    channel.exchange_declare(
        exchange='events',
        exchange_type='topic',
        durable=True
    )
    
    # Create temporary queue for testing
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind to ALL raw events from your agent
    channel.queue_bind(
        exchange='events',
        queue=queue_name,
        routing_key='events.raw.#'  # ← CATCHES ALL RAW EVENTS
    )
    
    print(f"[v] Bound to queue: {queue_name}")
    print("[*] Listening for raw events... (Ctrl+C to exit)")
    print("[i] Expected routing keys:")
    print("   events.raw.windows-agent-001.process")
    print("   events.raw.windows-agent-001.file")
    print("   events.raw.windows-agent-001.network")
    print("   events.raw.windows-agent-001.system")
    print("-" * 80)
    
    # Set QoS (process 1 message at a time)
    channel.basic_qos(prefetch_count=1)
    
    # Start consuming
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=False  # Manual ACK for reliability
    )
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
