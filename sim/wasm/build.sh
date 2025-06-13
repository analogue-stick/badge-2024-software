#!/usr/bin/env bash

set -e -x

# Work around Nix badness.
# See: https://github.com/NixOS/nixpkgs/issues/139943
emscriptenpath="$(dirname $(dirname $(which emcc)))"
if [[ "${emscriptenpath}" = /nix/store/* ]]; then
    if [ ! -d ~/.emscripten_cache ]; then
        cp -rv "$emscriptenpath/share/emscripten/cache" ~/.emscripten_cache
        chmod u+rwX -R ~/.emscripten_cache
    fi
    export EM_CACHE=~/.emscripten_cache
fi


emcc ctx.c \
    -I ../../components/ctx/ \
    -I ../../components/ctx/fonts/ \
    -D SIMULATOR \
    -s EXPORTED_FUNCTIONS=\
_ctx_new_for_framebuffer,\
_ctx_new_drawlist,\
_ctx_parse,\
_ctx_apply_transform,\
_ctx_text_width,\
_ctx_x,\
_ctx_y,\
_ctx_render_ctx,\
_ctx_logo,\
_ctx_define_texture,\
_ctx_draw_texture,\
_ctx_destroy,\
_stbi_load_from_memory,\
_malloc,\
_free \
    --no-entry -flto -O3 \
    -o ctx.wasm

mkdir -p sasppu || true
python3 ../../components/sasppu/src/generated.py sasppu/gen.h

emcc sasppu_wasm.c \
    -I ../../components/sasppu/include/private \
    -I ../../components/sasppu/include/public \
    -I ../../components/sasppu/src \
    -I . \
    -D SIMULATOR \
    -s EXPORTED_FUNCTIONS=\
_SASPPU_render,\
_SASPPU_gfx_reset,\
_SASPPU_copy_sprite,\
_SASPPU_copy_sprite_transparent,\
_SASPPU_blit_sprite,_SASPPU_blit_sprite_transparent,\
_SASPPU_paletted_sprite,\
_SASPPU_paletted_sprite_transparent,\
_SASPPU_compressed_sprite,\
_SASPPU_compressed_sprite_transparent,\
_SASPPU_fill_sprite,\
_SASPPU_draw_text_sprite,\
_SASPPU_draw_text_next_sprite,\
_SASPPU_copy_background,\
_SASPPU_copy_background_transparent,\
_SASPPU_blit_background,\
_SASPPU_blit_background_transparent,\
_SASPPU_paletted_background,\
_SASPPU_paletted_background_transparent,\
_SASPPU_compressed_background,\
_SASPPU_compressed_background_transparent,\
_SASPPU_fill_background,\
_SASPPU_draw_text_background,\
_SASPPU_draw_text_next_background,\
_get_framebuffer,\
_get_main_state,\
_get_cmath_state,\
_get_background_0,\
_get_background_1,\
_get_hdma_enable,\
_get_sprite,\
_get_bg0_map,\
_get_bg1_map,\
_get_table_entry,\
_set_main_state,\
_set_cmath_state,\
_set_background_0,\
_set_background_1,\
_set_hdma_enable,\
_set_sprite,\
_set_bg0_map,\
_set_bg1_map,\
_set_table_entry,\
_macro_CMATH,\
_macro_RGB555,\
_macro_RGB555_CMATH,\
_macro_RGB888,\
_macro_RGB888_CMATH,\
_macro_GREY555,\
_macro_GREY555_CMATH,\
_macro_GREY888,\
_macro_GREY888_CMATH,\
_macro_MUL_CHANNEL,\
_macro_MUL_RGB555,\
_macro_R_CHANNEL,\
_macro_G_CHANNEL,\
_macro_B_CHANNEL,\
_macro_CMATH_CHANNEL,\
_macro_MUL_COL,\
_macro_TRANSPARENT_BLACK,\
_macro_OPAQUE_BLACK,\
_macro_RED,\
_macro_GREEN,\
_macro_BLUE,\
_macro_WHITE,\
_render,\
_malloc,\
_free \
    --no-entry -flto -O3 \
    -o sasppu.wasm
