Tildagon badge simulator
===

This simulator is based on qemu-system-xtensa, which has esp32s3 support. As of right now, micropython hangs trying to initialise the ADCs.

To try it out, build the docker container in this folder 

    docker build . -t molive0/esp_idf:v5.4

and then run `docker-run.sh`

    ./docker-run.sh

My launch.json and tasks.json from vscode are also provided.