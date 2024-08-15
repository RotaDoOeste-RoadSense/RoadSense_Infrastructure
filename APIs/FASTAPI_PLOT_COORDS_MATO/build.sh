sudo docker build -t mato .

sudo docker rm -f mato

sudo docker run -v .:/app/ -it --name mato -p 8022:8022 mato bash
