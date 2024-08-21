sudo docker build -t mato .

sudo docker rm -f mato

sudo docker run -v .:/app/ -it --name mato -p 8023:8023 mato bash
