#!/bin/bash

docker run -it --rm --env "TARGET=esp32s3" -v "$(pwd)"/:/firmware -u $UID -e HOME=/tmp matthewwilkes/esp_idf:5.2.3
docker run -it --entrypoint /firmware/sim/merge-sim-firmwares.sh --env "TARGET=esp32s3" -v "$(pwd)"/:/firmware -u $UID -e HOME=/tmp matthewwilkes/esp_idf:5.2.3