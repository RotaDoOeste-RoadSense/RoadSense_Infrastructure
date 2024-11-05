#docker build -t fluxo .
# terminal: sudo mount -t cifs -o username=rdt-windows,password=123456,ro //192.168.18.10/Extracoes /mnt/windows_share

docker rm -f fluxo2

docker run -it --name fluxo -v /mnt/windows_share/GPS:/mnt/teste/GPS_norte_from43 -v $(pwd):/app --network=host --gpus all fluxo 
