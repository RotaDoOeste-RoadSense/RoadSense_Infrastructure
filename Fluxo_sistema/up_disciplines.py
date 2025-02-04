
from Placas import run as placas
import threading
import multiprocessing
from multiprocessing import Process
import pika
import json
import sys
import time
import os

class Queue:
    def __init__(self,rabbitmq_host,queue_name,method,*args):
        self.rabbitmq_host = rabbitmq_host
        self.queue_name = queue_name
        self.method = method
        self.args = args
        connection = self.connect_to_rabbit()
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        print(f'[*] Aguardando tarefas para {self.queue_name}. Pressione CTRL+C para sair.', flush=True)
        channel.start_consuming()
    def connect_to_rabbit(self):
        rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.rabbitmq_host,
                        credentials=credentials
                        )
                )
                return connection
            except pika.exceptions.AMQPConnectionError:
                print("Tentando se conectar ao RabbitMQ...", flush=True)
                time.sleep(5)
    def process_task(self,task):
        print(f"[x] {self.queue_name} processando tarefa {task['trip_id']}", flush=True)
        self.method(*self.args)
        print(f"[x] {self.queue_name} concluiu a tarefa {task['trip_id']}!", flush=True)

    def callback(self,ch, method, properties, body):
        task = json.loads(body)
        self.process_task(task)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def run_placas(rabbitmq_host,folder,trip_id,trip_direction):
    fila = Queue(rabbitmq_host,'Placa',placas,folder,trip_id)

# QUEUE_NAME = sys.argv[1]
if __name__=='__main__':
    rabbitmq_host = 'localhost'
    folder = "/mnt/windows_share/GPS"
    trip_id = 1
    trip_direction = 'N' # ou 'S'
    procs = []
    procs.append(
        Process(target=run_placas, args=(rabbitmq_host,folder,trip_id,trip_direction,))
        )
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()