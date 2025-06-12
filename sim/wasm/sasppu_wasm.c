#define USE_INLINE_ASM 0
#define QEMU_EMULATOR 1
#define SASPPU_ESP 0
#include "help.c"
#include "sasppu.c"
#include <stddef.h>

#include <stdint.h>

#define TILDAGON_DISPLAY_WIDTH 240
#define TILDAGON_DISPLAY_HEIGHT 240

static uint16_t tildagon_fb[TILDAGON_DISPLAY_WIDTH * TILDAGON_DISPLAY_HEIGHT]
    __attribute__((aligned(16)));
static uint8_t
    tildagon_fb_out[4][TILDAGON_DISPLAY_WIDTH * TILDAGON_DISPLAY_HEIGHT];

uint8_t *get_framebuffer() {
  // Convert the framebuffer from 565 to 8888 so Python doesn't have to.
  for (size_t i = 0; i < TILDAGON_DISPLAY_WIDTH * TILDAGON_DISPLAY_HEIGHT;
       i++) {
    uint16_t col = tildagon_fb[i];
    uint8_t red = (col & 0b1111100000000000) >> 8;
    uint8_t green = (col & 0b0000011111100000) >> 2;
    uint8_t blue = (col & 0b0000000000011111) << 3;
    tildagon_fb_out[i][0] = red;
    tildagon_fb_out[i][1] = green;
    tildagon_fb_out[i][2] = blue;
    tildagon_fb_out[i][3] = 0xFF;
  }
  return (uint8_t *)tildagon_fb_out;
}

uint8_t *render() {
  SASPPU_render((uint16x8_t *)(tildagon_fb), 0);
  SASPPU_render((uint16x8_t *)(tildagon_fb), 1);
  SASPPU_render((uint16x8_t *)(tildagon_fb), 2);
  SASPPU_render((uint16x8_t *)(tildagon_fb), 3);
  return get_framebuffer();
}

MainState get_main_state() { return SASPPU_main_state; }
CMathState get_cmath_state() { return SASPPU_cmath_state; }
Background get_background_0() { return SASPPU_bg0_state; }
Background get_background_1() { return SASPPU_bg1_state; }
uint8_t get_hdma_enable() { return SASPPU_hdma_enable; }

Sprite get_sprite(uint8_t index) { return SASPPU_oam[index]; }
uint16_t get_bg0_map(uint8_t index) { return SASPPU_bg0[index]; }
uint16_t get_bg1_map(uint8_t index) { return SASPPU_bg1[index]; }
HDMAEntry get_table_entry(uint8_t table, uint8_t index) {
  return SASPPU_hdma_tables[table][index];
}

void set_main_state(MainState v) { SASPPU_main_state = v; }
void set_cmath_state(CMathState v) { SASPPU_cmath_state = v; }
void set_background_0(Background v) { SASPPU_bg0_state = v; }
void set_background_1(Background v) { SASPPU_bg1_state = v; }
void set_hdma_enable(uint8_t v) { SASPPU_hdma_enable = v; }

void set_sprite(uint8_t index, Sprite v) { SASPPU_oam[index] = v; }
void set_bg0_map(uint8_t index, uint16_t v) { SASPPU_bg0[index] = v; }
void set_bg1_map(uint8_t index, uint16_t v) { SASPPU_bg1[index] = v; }
void set_table_entry(uint8_t table, uint8_t index, HDMAEntry v) {
  SASPPU_hdma_tables[table][index] = v;
}
