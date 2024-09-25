docker build -t struc .

docker rm -f struc 
docker run -it --name struc struc bash
