
from glob import glob
import os
import time
from concurrent.futures import ThreadPoolExecutor
import subprocess
import threading
import uuid
import multiprocessing



def generate_commands(input_folder, output_folder, start_display=99):
    pgrs = glob(input_folder + '/*.pgr')
    pgrs = sorted(filter(lambda _: _.endswith('000000.pgr'), pgrs))
    print(f'quantidade de pgrs = {len(pgrs)}')
  
    os.makedirs(output_folder, exist_ok=True)
    commands_ln = []
    commands = []

    for j, pgr in enumerate(pgrs):
        display_num = start_display + j
        folder_path = f'/tmp/{str(uuid.uuid4())}'
        os.makedirs(folder_path, exist_ok=True)
        
        output_foldername = os.path.basename(output_folder)
        
        commands_ln.append(f"ln -s '{output_folder}' {folder_path}")
        #commands.append(f"xvfb-run --server-num={display_num} LadybugCubeMap '{pgr}' '{output_folder}/{output_foldername}/' 2048")
        
        commands.append(f"xvfb-run -a LadybugCubeMap '{pgr}' '{folder_path}/{output_foldername}/' 2048")
    return [commands_ln, commands]


def keep_connection_alive(connection, stop_event: threading.Event):
    """Thread para manter a conexão Pika ativa, com condição de parada."""
    while not stop_event.is_set():
        try:
            # time_limit pequeno para acordar e checar o stop_event com frequência
            connection.process_data_events(time_limit=1)
        except Exception as e:
            print(f"[⚠️ Thread Pika] Erro ao processar eventos: {e}")
            break
        time.sleep(1)
    print("[ℹ️ Thread Pika] Encerrando.")


# def executar_comando(cmd):
#     print(f"Iniciando: {cmd}")
#     start = time.time()
#     subprocess.run(cmd, shell=True, check=True)  # <- se falhar, levanta exceção
#     print(f"✔️ Finalizado: {cmd} em {time.time() - start:.1f}s")

def executar_comando(cmd): 
    print(f"Iniciando: {cmd}") 
    start = time.time() 
    try: 
        subprocess.run(cmd, shell=True, check=True) 
        print(f"✔️ Finalizado: {cmd} em {time.time() - start:.1f}s") 
    except subprocess.CalledProcessError as e: 
        print(f"❌ Erro ao executar: {cmd}\n{e}")

def run(connection, pgr_folder, frames_output_folder):
    start = time.time()
    comandos_ln, comandos = generate_commands(
        pgr_folder,
        frames_output_folder,
        start_display=99
    )

    stop_event = threading.Event()
    thread = threading.Thread(
        target=keep_connection_alive,
        args=(connection, stop_event),
        daemon=True
    )
    thread.start()

    try:
        # 1) garante que TODOS os ln -s terminaram (ou para no primeiro erro)
        with ThreadPoolExecutor(max_workers=1) as executor:
            list(executor.map(executar_comando, comandos_ln))

        # 2) só depois roda os comandos pesados em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(executar_comando, comandos))

    finally:
        stop_event.set()
        thread.join(timeout=5)

    tempo = time.time() - start
    print(f"demorou {tempo} s")


# if __name__ == '__main__':
    
#     run(connection, pgr_folder='/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/',
#         frames_output_folder='/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube')
    
        