import pika
import json
import time

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

pgr_folder = '/mnt/hd1/Extracoes/fevereiro_2026/pgr_links'
# pgr_folder = '/mnt/hd1/Extracoes/UFMT/VICTOR2/VICTOR/'
# pgr_folder = '/mnt/hd3/PGRs/CHAPADAO DO SUL  - VOTOPORANGA'
#pgr_folder = '/home/servidor/'

frames_output_folder = '/mnt/hd1/Extracoes/fevereiro_2026/Cube'

connection = connect_to_rabbit()
channel = connection.channel()
send_task('PGR', {"pgr_folder": pgr_folder, "frames_output_folder": frames_output_folder})
connection.close()