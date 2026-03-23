# # mkdir /home/rdt/Documents
# cd /home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema
# rm -rf cube/*
# ln -s '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube/' '/tmp/cube'
# xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap '/home/servidor/CAMPOGRANDE-RONDONOPOLIS5-000000.pgr' '/tmp/cube/' 2048


# export HOME=/tmp
# export XDG_CACHE_HOME=/tmp/.cache
# export MESA_SHADER_CACHE_DIR=/tmp/.cache/mesa
# export __GL_SHADER_DISK_CACHE_PATH=/tmp/.cache/nvidia 2>/dev/null || true
# mkdir -p "$XDG_CACHE_HOME" "$MESA_SHADER_CACHE_DIR" /tmp/.cache/nvidia 2>/dev/null || true

#xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap "/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/CAMERA 360 KM108 11.02.26-000000.pgr" "/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/output/" 2048 
#& xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap "/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/CAMERA 360 KM108 11.02.26-000000.pgr" "/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/output2/" 2048 & wait
xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap "/home/servidor/pgr_testes/CAMERA 360 KM108 11.02.26-000000.pgr" "/home/servidor/pgr_testes/output/" 2048 & xvfb-run -a /usr/src/ladybug/bin/LadybugCubeMap "/home/servidor/pgr_testes/CAMERA 360 KM108 11.02.26-000000.pgr" "/home/servidor/pgr_testes/output2/" 2048 & wait