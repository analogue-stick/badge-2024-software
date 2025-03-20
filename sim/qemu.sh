#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source /opt/esp-idf/export.sh
PATH=~/qemu/bin:$PATH

    #-drive file=/home/molive/Projects/lcd_qemu_rgb_panel/build/qemu_efuse.bin,if=none,format=raw,id=efuse \
    #-display sdl \
    #-global driver=nvram.esp32c3.efuse,property=drive,value=efuse \
    #-serial tcp::5555,server \
qemu-system-xtensa -M esp32s3 \
    -drive file="$SCRIPT_DIR"/merged-firmware.bin,if=mtd,format=raw \
    -global driver=timer.esp32s3.timg,property=wdt_disable,value=true \
    -nic user,model=open_eth \
    -m 2M \
    -gdb tcp::3333 -S #\
    #&
    
#python /opt/esp-idf/tools/idf_monitor.py \
#    -p socket://localhost:5555 \
#    -b 115200 \
#    --toolchain-prefix xtensa-esp32s3-elf- \
#    --target esp32s3 \
#    --revision 0 \
#    "$SCRIPT_DIR"/../micropython/ports/esp32/build-tildagon/micropython.elf