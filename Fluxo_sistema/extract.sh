# mkdir /home/rdt/Documents
cd /home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema
rm -rf cube/*
#xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap '/home/servidor/CAMPOGRANDE-RONDONOPOLIS5-000000.pgr' '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube/' 2048
ln -s '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube/' '/tmp/cube'
xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap '/home/servidor/CAMPOGRANDE-RONDONOPOLIS5-000000.pgr' '/tmp/cube/' 2048
