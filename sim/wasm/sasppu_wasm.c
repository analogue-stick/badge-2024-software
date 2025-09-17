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
static uint8_t tildagon_fb_out[TILDAGON_DISPLAY_WIDTH * TILDAGON_DISPLAY_HEIGHT]
                              [4];

uint8_t *get_framebuffer() {
  // Convert the framebuffer from 565 to 8888 so Python doesn't have to.
  for (size_t i = 0; i < (TILDAGON_DISPLAY_WIDTH * TILDAGON_DISPLAY_HEIGHT);
       i++) {
    uint16_t col = (tildagon_fb[i] >> 8) | (tildagon_fb[i] << 8);
    uint8_t red = (col & 0b1111100000000000) >> 8;
    uint8_t green = (col & 0b0000011111100000) >> 3;
    uint8_t blue = (col & 0b0000000000011111) << 3;
    tildagon_fb_out[i][0] = blue;
    tildagon_fb_out[i][1] = green;
    tildagon_fb_out[i][2] = red;
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

MainState *get_main_state() { return &SASPPU_main_state; }
CMathState *get_cmath_state() { return &SASPPU_cmath_state; }
Background *get_background_0() { return &SASPPU_bg0_state; }
Background *get_background_1() { return &SASPPU_bg1_state; }
uint8_t get_hdma_enable() { return SASPPU_hdma_enable; }
bool get_forced_blank() { return SASPPU_forced_blank; }

Sprite *get_sprite(uint8_t index) { return &SASPPU_oam[index]; }
uint16_t get_bg0_map(uint8_t index) { return SASPPU_bg0[index]; }
uint16_t get_bg1_map(uint8_t index) { return SASPPU_bg1[index]; }
HDMAEntry *get_table_entry(uint8_t table, uint8_t index) {
  return &SASPPU_hdma_tables[table][index];
}

void set_main_state(MainState *v) {
  memcpy(&SASPPU_main_state, v, sizeof(MainState));
}
void set_cmath_state(CMathState *v) {
  memcpy(&SASPPU_cmath_state, v, sizeof(CMathState));
}
void set_background_0(Background *v) {
  memcpy(&SASPPU_bg0_state, v, sizeof(Background));
}
void set_background_1(Background *v) {
  memcpy(&SASPPU_bg1_state, v, sizeof(Background));
}
void set_hdma_enable(uint8_t v) { SASPPU_hdma_enable = v; }
void set_forced_blank(bool v) { SASPPU_forced_blank = v; }

void set_sprite(uint8_t index, Sprite *v) {
  memcpy(&SASPPU_oam[index], v, sizeof(Sprite));
}
void set_bg0_map(uint8_t index, uint16_t v) { SASPPU_bg0[index] = v; }
void set_bg1_map(uint8_t index, uint16_t v) { SASPPU_bg1[index] = v; }
void set_table_entry(uint8_t table, uint8_t index, HDMAEntry *v) {
  memcpy(&SASPPU_hdma_tables[table][index], v, sizeof(HDMAEntry));
}

uint16_t macro_CMATH(uint16_t col) { return SASPPU_CMATH(col); }

uint16_t macro_RGB555(uint16_t r, uint16_t g, uint16_t b) {
  return SASPPU_RGB555(r, g, b);
}
uint16_t macro_RGB555_CMATH(uint16_t r, uint16_t g, uint16_t b) {
  return SASPPU_RGB555_CMATH(r, g, b);
}

uint16_t macro_RGB888(uint16_t r, uint16_t g, uint16_t b) {
  return SASPPU_RGB888(r, g, b);
}
uint16_t macro_RGB888_CMATH(uint16_t r, uint16_t g, uint16_t b) {
  return SASPPU_RGB888_CMATH(r, g, b);
}

uint16_t macro_GREY555(uint16_t g) { return SASPPU_GREY555(g); }
uint16_t macro_GREY555_CMATH(uint16_t g) { return SASPPU_GREY555_CMATH(g); }

uint16_t macro_GREY888(uint16_t g) { return SASPPU_GREY888(g); }
uint16_t macro_GREY888_CMATH(uint16_t g) { return SASPPU_GREY888_CMATH(g); }

uint16_t macro_MUL_CHANNEL(uint16_t col, uint16_t mul) {
  return SASPPU_MUL_CHANNEL(col, mul);
}

uint16_t macro_MUL_RGB555(uint16_t r, uint16_t g, uint16_t b, uint16_t mul) {
  return SASPPU_MUL_RGB555(r, g, b, mul);
}
uint16_t macro_R_CHANNEL(uint16_t col) { return SASPPU_R_CHANNEL(col); }
uint16_t macro_G_CHANNEL(uint16_t col) { return SASPPU_G_CHANNEL(col); }
uint16_t macro_B_CHANNEL(uint16_t col) { return SASPPU_B_CHANNEL(col); }
uint16_t macro_CMATH_CHANNEL(uint16_t col) { return SASPPU_CMATH_CHANNEL(col); }

uint16_t macro_MUL_COL(uint16_t col, uint16_t mul) {
  return SASPPU_MUL_COL(col, mul);
}

uint16_t macro_TRANSPARENT_BLACK() { return SASPPU_TRANSPARENT_BLACK; }
uint16_t macro_OPAQUE_BLACK() { return SASPPU_OPAQUE_BLACK; }
uint16_t macro_RED() { return SASPPU_RED; }
uint16_t macro_GREEN() { return SASPPU_GREEN; }
uint16_t macro_BLUE() { return SASPPU_BLUE; }
uint16_t macro_WHITE() { return SASPPU_WHITE; }
