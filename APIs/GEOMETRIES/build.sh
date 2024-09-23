docker build -t geom .

docker rm -f geom 
docker run -it --name geom geom bash
