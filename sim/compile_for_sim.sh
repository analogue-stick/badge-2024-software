#!/bin/bash

docker run -it --rm --env "TARGET=esp32s3" -v "$(pwd)"/:/firmware -u $UID -e HOME=/tmp molive0/esp_idf:v5.4
docker run -it --entrypoint /firmware/sim/merge-sim-firmwares.sh --env "TARGET=esp32s3" -v "$(pwd)"/:/firmware -u $UID -e HOME=/tmp molive0/esp_idf:v5.4