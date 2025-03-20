#!/bin/bash
set -e -o pipefail

find /firmware -name '.git' -exec bash -c 'git config --global --add safe.directory ${0%/.git}' {} \;

cd /firmware
cd micropython
make -C mpy-cross

cd ports/esp32/boards
ln -sfn ../../../../tildagon ./tildagon

cd ..
PATH=/qemu/bin:$PATH BOARD=tildagon USER_C_MODULES=/firmware/drivers/micropython.cmake idf.py qemu --graphics --gdb --qemu-extra-args \"-m 2M\" monitor