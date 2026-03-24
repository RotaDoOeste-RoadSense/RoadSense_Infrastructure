import pika
import json
import time
import receber_nova_trip

RABBITMQ_HOST = '127.0.0.1'
def connect_to_rabbit():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST,
                                          credentials=pika.PlainCredentials(username='rdt', password='123456'),
                                          port=5673
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
        body=json.dumps(task_message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"[x] Mensagem enviada para {queue_name}: {task_message}")



trip_direction = 'N' 

#folder = '/media/rdt/hd3' # pasta que tem a pasta Cube

folder = '/media/rdt/hd3/viagem/' # pasta que contem a pasta Cube

trip_id = receber_nova_trip.main(folder, trip_direction, production=False)

print(f"Nova trip criada com ID: {trip_id}")

from utils import run_json_folder as run

json_folder = f'/{folder}/Cube'

run(trip_id, json_folder)

for queue in ['Placa','Vegetacao','Horizontal','DrenagemSuperficial', 'Defensas']:


     connection = connect_to_rabbit()
     channel = connection.channel()
     send_task(queue, {"trip_id": trip_id, "trip_direction": trip_direction, "folder": folder})
     connection.close()
