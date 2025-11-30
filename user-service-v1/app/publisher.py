import pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

def publish_user_updated(event):
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declare exchange
    channel.exchange_declare(exchange='user-events', exchange_type='fanout')

    # Publish message
    channel.basic_publish(
        exchange='user-events',
        routing_key='',
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    print("Published event:", event)
    connection.close()
