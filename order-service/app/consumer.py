import pika
import json
from .database import orders_collection
import os
import time

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def start_consumer():
    max_retries = 5
    retry_count = 0
    connection = None
    channel = None
    
    while retry_count < max_retries:
        try:
            print(f"Attempting to connect to RabbitMQ at {RABBIT_URL}...")
            params = pika.URLParameters(RABBIT_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            # Declare exchange + queue so they appear in UI
            channel.exchange_declare(exchange="user-events", exchange_type="fanout", durable=False)
            channel.queue_declare(queue="user-updates", durable=False)
            channel.queue_bind(queue="user-updates", exchange="user-events")

            print("✓ Connected to RabbitMQ successfully!")
            print("✓ Waiting for messages in user-updates queue...")
            break
        except Exception as e:
            retry_count += 1
            print(f"✗ Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(5)
            else:
                print("✗ Max retries reached. Consumer not started.")
                return

    def callback(ch, method, properties, body):
        try:
            event = json.loads(body)
            print(f"✓ RECEIVED EVENT: {event}")

            userId = event["userId"]
            new_email = event["email"]
            
            # Handle both V1 (string) and V2 (object) address formats
            address_data = event.get("address") or event.get("deliveryAddress")
            if isinstance(address_data, dict):
                # V2 format: convert to string
                new_address = f"{address_data.get('street', '')}, {address_data.get('city', '')}, {address_data.get('postal', '')}"
            else:
                # V1 format: already a string
                new_address = address_data

            # update ALL orders for that user
            result = orders_collection.update_many(
                {"userId": userId},
                {"$set": {
                    "email": new_email,
                    "deliveryAddress": new_address
                }}
            )

            print(f"✓ Updated {result.modified_count} orders for user {userId}")
            print(f"  - Email: {new_email}")
            print(f"  - Address: {new_address}")
        except Exception as e:
            print(f"✗ Error processing event: {e}")

    channel.basic_consume(queue="user-updates", on_message_callback=callback, auto_ack=True)
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumer stopped by user")
        channel.stop_consuming()
    except Exception as e:
        print(f"✗ Consumer error: {e}")

if __name__ == "__main__":
    start_consumer()