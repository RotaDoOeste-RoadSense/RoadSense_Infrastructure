import pika
import json
import time
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


# Folder sem a ultima barra



folder = ("/mnt/windows_share/Extracoes/GPS")
folder = ("/mnt/hd1/Extracoes/PGRS_2025")

trip_direction = 'N' # ou 'S'


#tabela trips
import receber_nova_trip


#trip_id = receber_nova_trip.main(folder, trip_direction, production=False)

#trip_id = 20

#trip_id = 27

trip_id = 29


from utils import run_json_folder as run


json_folder = '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/jsons'


#from utils import run

#run(trip_id, 'GPS_norte.xlsx')

# # run(trip_id, json_folder, 0, 4378) # SUL
#run(trip_id, json_folder, 4437, 15612) # NORTE

# imagem 4437 - 15612

# trip_id=17


# for queue in ['Placa','Matinho','Horizontal','DrenagemSuperficial', 'Defensas']:
# for queue in ['Placa','Horizontal','DrenagemSuperficial', 'Defensas']:
for queue in ['Placa']:
#for queue in ['Horizontal']:
# #for queue in ['DrenagemSuperficial', 'Defensas']:
# #for queue in ['Matinho']:
     connection = connect_to_rabbit()
     channel = connection.channel()
     send_task(queue, {"trip_id": trip_id, "trip_direction": trip_direction, "folder": folder})
     connection.close()
