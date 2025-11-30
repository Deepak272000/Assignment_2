import pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

def publish_user_updated(event):
    try:
        print(f"→ Publishing event to RabbitMQ: {event}")
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(exchange='user-events', exchange_type='fanout', durable=True)

        # Publish message
        channel.basic_publish(
            exchange='user-events',
            routing_key='',
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f"✓ Event published successfully to user-events exchange")
        connection.close()
    except Exception as e:
        print(f"✗ Failed to publish event: {e}")
