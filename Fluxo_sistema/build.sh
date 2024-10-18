#docker build -t fluxo .

docker rm -f fluxo2

docker run -it --name fluxo -v /mnt/windows_share/GPS:/mnt/teste/GPS_norte_from43 -v $(pwd):/app --network=host fluxo
