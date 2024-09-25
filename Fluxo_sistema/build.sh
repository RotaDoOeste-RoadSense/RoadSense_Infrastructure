docker build -t fluxo .

docker rm -f fluxo

docker run -it --name fluxo -v /mnt/ssh/dados/database_2022_test:/mnt/teste -v $(pwd):/app --network=host fluxo
