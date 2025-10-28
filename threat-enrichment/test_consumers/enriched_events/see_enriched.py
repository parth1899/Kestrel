# see_enriched.py
import pika, json, os
from dotenv import load_dotenv
load_dotenv()

conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
ch = conn.channel()
q = ch.queue_declare('', exclusive=True).method.queue
ch.queue_bind(exchange='events', queue=q, routing_key='events.enriched.*.file')

def cb(ch, m, p, body):
    print("\nFULL ENRICHED MESSAGE:")
    print(json.dumps(json.loads(body), indent=2))
    ch.basic_ack(m.delivery_tag)

ch.basic_consume(queue=q, on_message_callback=cb)
print("Listening for ALL enriched events...")
ch.start_consuming()