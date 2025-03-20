#!/bin/bash
set -e -o pipefail

. /opt/esp/entrypoint.sh
cd /firmware/micropython/ports/esp32
export PATH=~/qemu/bin:$PATH

idf.py qemu --graphics --gdb --qemu-extra-args \"-m 2M\" monitor