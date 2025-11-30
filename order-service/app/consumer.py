import pika
import json
from .database import orders_collection
import os

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def start_consumer():
    params = pika.URLParameters(RABBIT_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declare exchange + queue so they appear in UI
    channel.exchange_declare(exchange="user-events", exchange_type="fanout")
    channel.queue_declare(queue="user-updates", durable=True)
    channel.queue_bind(queue="user-updates", exchange="user-events")

    print("Waiting for messages in user-updates")

    def callback(ch, method, properties, body):
        event = json.loads(body)
        print(" RECEIVED EVENT:", event)

        userId = event["userId"]
        new_email = event["email"]
        new_address = event.get("address") or event.get("deliveryAddress")

        # update ALL orders for that user
        orders_collection.update_many(
            {"userId": userId},
            {"$set": {
                "email": new_email,
                "deliveryAddress": new_address
            }}
        )

        print(" Updated orders for user", userId)

    channel.basic_consume(queue="user-updates", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()