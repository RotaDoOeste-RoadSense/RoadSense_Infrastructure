import pika
import json
import time
RABBITMQ_HOST = '127.0.0.1'
def connect_to_rabbit():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST,
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
        body=json.dumps(task_message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"[x] Mensagem enviada para {queue_name}: {task_message}")


# Folder sem a ultima barra
#folder = "/mnt/hd1/Extracoes/SP_2024_sul"
#trip_id = 2
#trip_direction = 'S' # ou 'S'

folder = "/mnt/windows_share/GPS"
trip_id = 2
trip_direction = 'N' # ou 'S'


#tabela trips
import receber_nova_trip
# trip_id = receber_nova_trip.main(folder, trip_direction)

# # # tabela GPS
# from utils import run as table_gps
# table_gps(trip_id, 'trips/GPS_norte.xlsx')

### importar dados pelos jsons


from utils import run_json_folder as run
json_folder = '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube'

run(trip_id, json_folder)




# for queue in ['Placa','Matinho','Horizontal','DrenagemSuperficial', 'Defensas']:
# #for queue in ['Matinho']:
# #for queue in ['DrenagemSuperficial', 'Defensas']:
# # for queue in ['Defensas']:
#     connection = connect_to_rabbit()
#     channel = connection.channel()
#     send_task(queue, {"trip_id": trip_id, "trip_direction": trip_direction, "folder": folder})
#     connection.close()