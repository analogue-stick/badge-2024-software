#!/bin/bash

docker run -it --rm --env "TARGET=esp32s3" -v "$(pwd)"/../:/firmware -u $UID -p 3333:3333 -e HOME=/tmp molive0/esp_idf:v5.4 qemu
