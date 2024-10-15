#docker build -t fluxo .

docker rm -f fluxo2

docker run -it --name fluxo -v /media/GPS:/mnt/teste/GPS_norte_from43 -v $(pwd):/app --network=host fluxo
