from Placas import run as placas
from Horizontal import run as horizontal
from Drenagem import run as drainage
from Vegetacao import run as vegetacao
from Defensa import run as defensas
from utils_pgr import run as pgr

import multiprocessing
from multiprocessing import Process
import pika
import json
import os
import time


class DynamicQueue:
    def __init__(self, rabbitmq_host, queue_name, default_method):
        self.rabbitmq_host = rabbitmq_host
        self.queue_name = queue_name
        self.default_method = default_method
        self.connection = self.connect_to_rabbit()
        self.time = time.time()

        channel = self.connection.channel()
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
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=43200,
                        socket_timeout=43200,
                        connection_attempts=10,
                        retry_delay=5,
                        port=5673
                    )
                )
                return connection
            except pika.exceptions.AMQPConnectionError:
                print("Tentando se conectar ao RabbitMQ...", flush=True)
                time.sleep(5)

    def callback(self, ch, method, properties, body):
        try:
            task = json.loads(body)
            self.process_task(task)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[!] Erro ao processar mensagem: {e}", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def process_task(self, task):
        if 'trip_id' in task:
            print(f"[x] {self.queue_name} processando tarefa trip {task['trip_id']}", flush=True)
            self.time = time.time()
            #self.default_method(self.connection, task['folder'], task['trip_id'])
            self.default_method(self.connection, task['folder'], task['trip_id'], task['trip_direction'])
            print(f"[x] {self.queue_name} concluiu a tarefa trip {task['trip_id']}!", flush=True)
            tempo = time.time() - self.time
            print(f" {self.queue_name} [x] Tempo gasto na tarefa: {tempo} segundos", flush=True)
        elif 'pgr_folder' in task:
            print(f"[x] {self.queue_name} processando tarefa PGR {task['pgr_folder']}", flush=True)
            pgr(self.connection, task['pgr_folder'], task['frames_output_folder'])
            print(f"[x] {self.queue_name} concluiu a tarefa PGR {task['pgr_folder']}!", flush=True)
        else:
            raise ValueError("Mensagem não contém os campos esperados ('trip_id' ou 'pgr_folder')")


def run_dynamic(rabbitmq_host, queue_name, default_method):
    while True:
        try:
            DynamicQueue(rabbitmq_host, queue_name, default_method)
        except Exception as e:
            print(f"[!] Erro na fila {queue_name}: {e}", flush=True)
            time.sleep(5)


if __name__ == '__main__':
    rabbitmq_host = 'localhost'

    processes = [
        Process(target=run_dynamic, args=(rabbitmq_host, 'Placa', placas)),
        Process(target=run_dynamic, args=(rabbitmq_host, 'DrenagemSuperficial', drainage)),
        Process(target=run_dynamic, args=(rabbitmq_host, 'Horizontal', horizontal)),
        Process(target=run_dynamic, args=(rabbitmq_host, 'Vegetacao', vegetacao)),
        Process(target=run_dynamic, args=(rabbitmq_host, 'Defensas', defensas)),
        Process(target=run_dynamic, args=(rabbitmq_host, 'PGR', pgr)),  
    ]

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()
