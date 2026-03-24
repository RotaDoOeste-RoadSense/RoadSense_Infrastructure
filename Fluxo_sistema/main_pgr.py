import pika
import json
import time
import os

RABBITMQ_HOST = '127.0.0.1'
def connect_to_rabbit():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST,
                                            port=5673,
                                          credentials=pika.PlainCredentials(username='rdt', password='123456')
                                          )
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("Tentando se conectar ao RabbitMQ...")
            time.sleep(5)
def send_task(queue_name, task_message):
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(task_message, ensure_ascii=False).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json", content_encoding="utf-8")
    )
    print(f"[x] Mensagem enviada para {queue_name}: {task_message}")


pgr_folder = '/media/rdt/hd3/viagem/'

frames_output_folder = '/media/rdt/hd3/viagem/Cube/'
os.makedirs(frames_output_folder, exist_ok=True)

connection = connect_to_rabbit()
channel = connection.channel()
send_task('PGR', {"pgr_folder": pgr_folder, "frames_output_folder": frames_output_folder})
connection.close()