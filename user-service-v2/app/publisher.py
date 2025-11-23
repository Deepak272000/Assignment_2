import pika
import json

def publish_user_updated(event):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.exchange_declare(exchange='user-events', exchange_type='fanout')

    channel.basic_publish(
        exchange='user-events',
        routing_key='',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )
    print("Published event:", event)

    connection.close()
