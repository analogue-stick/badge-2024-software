"""
sasppu.py wraps a WebAssembly-compiled sasppu in functions that act similar to the micropython interface.
"""
import os
import math
import sys

import wasmer
import wasmer_compiler_cranelift

class Wasm:
    """
    Wasm wraps access to WebAssembly functions, converting to/from Python types
    as needed. It's intended to be used as a singleton.
    """

    def __init__(self):
        store = wasmer.Store(wasmer.engine.JIT(wasmer_compiler_cranelift.Compiler))
        simpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        wasmpath = os.path.join(simpath, "wasm", "sasppu.wasm")
        module = wasmer.Module(store, open(wasmpath, "rb").read())
        wasi_version = wasmer.wasi.get_version(module, strict=False)
        wasi_env = wasmer.wasi.StateBuilder("tildagonsim").finalize()
        import_object = wasi_env.generate_import_object(store, wasmer.wasi.Version.LATEST)
        instance = wasmer.Instance(module, import_object)
        self._i = instance

    def malloc(self, n):
        return self._i.exports.malloc(n)

    def free(self, p):
        self._i.exports.free(p)

    def ctx_parse(self, ctx, s):
        s = s.encode("utf-8")
        slen = len(s) + 1
        p = self.malloc(slen)
        mem = self._i.exports.memory.uint8_view(p)
        mem[0 : slen - 1] = s
        mem[slen - 1] = 0
        self._i.exports.ctx_parse(ctx, p)
        self.free(p)

    def ctx_new_for_framebuffer(self, width, height, stride, format):
        """
        Call ctx_new_for_framebuffer, but also first allocate the underlying
        framebuffer and return it alongside the Ctx*.
        """
        fb = self.malloc(stride * height)
        return fb, self._i.exports.ctx_new_for_framebuffer(
            fb, width, height, stride, format
        )

    def ctx_new_drawlist(self, width, height):
        return self._i.exports.ctx_new_drawlist(width, height)

    def ctx_apply_transform(self, ctx, *args):
        args = [float(a) for a in args]
        return self._i.exports.ctx_apply_transform(ctx, *args)

    def ctx_define_texture(self, ctx, eid, *args):
        s = eid.encode("utf-8")
        slen = len(s) + 1
        p = self.malloc(slen)
        mem = self._i.exports.memory.uint8_view(p)
        mem[0 : slen - 1] = s
        mem[slen - 1] = 0
        res = self._i.exports.ctx_define_texture(ctx, p, *args)
        self.free(p)
        return res

    def ctx_draw_texture(self, ctx, eid, *args):
        s = eid.encode("utf-8")
        slen = len(s) + 1
        p = self.malloc(slen)
        mem = self._i.exports.memory.uint8_view(p)
        mem[0 : slen - 1] = s
        mem[slen - 1] = 0
        args = [float(a) for a in args]
        res = self._i.exports.ctx_draw_texture(ctx, p, *args)
        self.free(p)
        return res

    def ctx_text_width(self, ctx, text):
        s = text.encode("utf-8")
        slen = len(s) + 1
        p = self.malloc(slen)
        mem = self._i.exports.memory.uint8_view(p)
        mem[0 : slen - 1] = s
        mem[slen - 1] = 0
        res = self._i.exports.ctx_text_width(ctx, p)
        self.free(p)
        return res

    def ctx_x(self, ctx):
        return self._i.exports.ctx_x(ctx)

    def ctx_y(self, ctx):
        return self._i.exports.ctx_y(ctx)

    def ctx_logo(self, ctx, *args):
        args = [float(a) for a in args]
        return self._i.exports.ctx_logo(ctx, *args)

    def ctx_destroy(self, ctx):
        return self._i.exports.ctx_destroy(ctx)

    def ctx_render_ctx(self, ctx, dctx):
        return self._i.exports.ctx_render_ctx(ctx, dctx)

    def stbi_load_from_memory(self, buf):
        p = self.malloc(len(buf))
        mem = self._i.exports.memory.uint8_view(p)
        mem[0 : len(buf)] = buf
        wh = self.malloc(4 * 3)
        res = self._i.exports.stbi_load_from_memory(p, len(buf), wh, wh + 4, wh + 8, 4)
        whmem = self._i.exports.memory.uint32_view(wh // 4)
        r = (res, whmem[0], whmem[1], whmem[2])
        self.free(p)
        self.free(wh)

        res, w, h, c = r
        b = self._i.exports.memory.uint8_view(res)
        if c == 3:
            return r
        for j in range(h):
            for i in range(w):
                b[i * 4 + j * w * 4 + 0] = int(
                    b[i * 4 + j * w * 4 + 0] * b[i * 4 + j * w * 4 + 3] / 255
                )
                b[i * 4 + j * w * 4 + 1] = int(
                    b[i * 4 + j * w * 4 + 1] * b[i * 4 + j * w * 4 + 3] / 255
                )
                b[i * 4 + j * w * 4 + 2] = int(
                    b[i * 4 + j * w * 4 + 2] * b[i * 4 + j * w * 4 + 3] / 255
                )
        return r

_wasm = Wasm()

SPRITE_COUNT = 256
SPRITE_CACHE = 16

MAP_WIDTH_POWER = 6
MAP_HEIGHT_POWER = 6
MAP_WIDTH = (1 << MAP_WIDTH_POWER)
MAP_HEIGHT = (1 << MAP_HEIGHT_POWER)

IC_SUCCESS = 0
IC_TOO_WIDE = 1
IC_TOO_TALL = 2
IC_INVALID_BIT_DEPTH = 3

WINDOW_A = (0b0001)
WINDOW_B = (0b0010)
WINDOW_AB = (0b0100)
WINDOW_X = (0b1000)
WINDOW_ALL = (0b1111)

BPP1 = 0
BPP2 = 1
BPP4 = 2
BPP8 = 3

#todo
TRANSPARENT_BLACK = 0
OPAQUE_BLACK = 0
RED = 0
GREEN = 0
BLUE = 0
WHITE = 0

def type_bound_i16(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < -0x8000 or v > 0x7FFF):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))
    
def type_bound_u16(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < 0 or v > 0xFFFF):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))

def type_bound_i8(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < -0x80 or v > 0x7F):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))

def type_bound_u8(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < 0 or v > 0xFF):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))

def type_bound_i4(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < -0x8 or v > 0x7):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))

def type_bound_u4(v, name: str):
    if (not isinstance(v, int)):
        raise TypeError("{name} must be integer".format(name=name))
    if (v < 0 or v > 0xF):
        raise ValueError("{name} value out of bounds ({val})".format(name=name, val=v))
    
class HasBindPoint:
    def _load(self):
        pass

    def _save(self):
        pass

    def unbind(self):
        self._load()
        self._bound = -1

    def _bind_with_point(self, bind_point: int, flush: bool = True):
        if (not isinstance(bind_point, int)):
            raise TypeError("Bind point must be integer")
        if (bind_point < 0):
            self.unbind()
            return
        if (bind_point > self._max_bind):
            raise ValueError("Bind point out of bounds ({val})".format(val=bind_point))
        if (self._bound >= 0):
            self._unbind()
        self._bound = bind_point
        if (flush):
            self._save()
        else:
            self._load()

    def _bind(self, flush: bool = True):
        if (self._bound >= 0):
            self._unbind()
        self._bound = 0
        if (flush):
            self._save()
        else:
            self._load()

    def get_bind_point(self):
        if hasattr(self, "_max_bind"):
            if (self._bound < 0):
                return None
            return self._bound
        else:
            return self.bound == 0
    
    def __init__(self):
        self._bound = -1
        if (hasattr(self, "_max_bind")):
            self.bind = self._bind_with_point
        else:
            self.bind = self._bind
    
class HasWindows(HasBindPoint):
    def __init__(self):
        super(HasWindows, self).__init__()
        self._windows = 0xFF

    @property
    def windows(self):
        self._load()
        return self._windows

    @windows.setter
    def windows(self, v):
        type_bound_u8(v, "Windows")
        self._windows = v
        self._save()

    @property
    def window_1(self):
        self._load()
        return self._windows & 0xF

    @window_1.setter
    def window_1(self, v):
        type_bound_u4(v, "Window")
        self._load()
        self._windows &= 0xF0
        self._windows |= v
        self._save()

    @property
    def window_2(self):
        self._load()
        return (self._windows >> 4) & 0x0F

    @window_2.setter
    def window_2(self, v):
        type_bound_u4(v, "Window")
        self._load()
        self._windows &= 0x0F
        self._windows |= (v << 4)
        self._save()

class HasFlags(HasBindPoint):
    def __init__(self):
        super(HasFlags, self).__init__()
        self._flags = 0x00

    @property
    def flags(self):
        self._load()
        return self._flags

    @flags.setter
    def flags(self, v):
        type_bound_u8(v, "Flags")
        self._flags = v
        self._save()

class HasPosition(HasBindPoint):
    def __init__(self):
        super(HasPosition, self).__init__()
        self._x = 0x0000
        self._y = 0x0000

    @property
    def x(self):
        self._load()
        return self._x

    @x.setter
    def x(self, v):
        type_bound_i16(v, "Position")
        self._x = v
        self._save()

    @property
    def y(self):
        self._load()
        return self._y

    @y.setter
    def y(self, v):
        type_bound_i16(v, "Position")
        self._y = v
        self._save()

class Background(HasFlags, HasWindows, HasPosition, HasBindPoint):

    WIDTH_POWER = 8
    HEIGHT_POWER = 9
    WIDTH = (1 << WIDTH_POWER)
    HEIGHT = (1 << HEIGHT_POWER)
    C_MATH = (1 << 0)

    def __init__(self):
        self._max_bind = 1
        super(Background, self).__init__()

    def _load(self):
        pass

    def _save(self):
        pass

    def __eq__(self, other):
        if (not isinstance(other, Background)):
            raise TypeError("Other must be Background")
        self._load()
        other._load()
        equal = super(Background, self).__eq__(other)
        return equal
    
class CMathState(HasFlags, HasBindPoint):

    HALF_MAIN_SCREEN = (1 << 0)
    DOUBLE_MAIN_SCREEN = (1 << 1)
    HALF_SUB_SCREEN = (1 << 2)
    DOUBLE_SUB_SCREEN = (1 << 3)
    ADD_SUB_SCREEN = (1 << 4)
    SUB_SUB_SCREEN = (1 << 5)
    FADE_ENABLE = (1 << 6)
    CMATH_ENABLE = (1 << 7)

    def __init__(self):
        super(CMathState, self).__init__()
        self._screen_fade = 0xFF

    @property
    def screen_fade(self):
        self._load()
        return self._screen_fade

    @screen_fade.setter
    def screen_fade(self, v):
        type_bound_u8(v, "Fade")
        self._screen_fade = v
        self._save()

    def _load(self):
        pass

    def _save(self):
        pass

    def __eq__(self, other):
        if (not isinstance(other, CMathState)):
            raise TypeError("Other must be CMathState")
        self._load()
        other._load()
        equal = super(CMathState, self).__eq__(other)
        equal &= self._screen_fade == other._screen_fade
        return equal
    
class MainState(HasFlags, HasBindPoint):

    SPR0_ENABLE = (1 << 0)
    SPR1_ENABLE = (1 << 1)
    BG0_ENABLE = (1 << 2)
    BG1_ENABLE = (1 << 3)
    CMATH_ENABLE = (1 << 4)
    BGCOL_WINDOW_ENABLE = (1 << 5)

    def __init__(self):
        super(MainState, self).__init__()
        self._window_1_left = 0x00
        self._window_2_left = 0x00
        self._window_1_right = 0xFF
        self._window_2_right = 0xFF
        self._mainscreen_colour = 0x0000
        self._subscreen_colour = 0x0000
        self._bgcol_windows = 0xFF

    @property
    def window_1_left(self):
        self._load()
        return self._window_1_left

    @window_1_left.setter
    def window_1_left(self, v):
        type_bound_u8(v, "Window bound")
        self._window_1_left = v
        self._save()

    @property
    def window_1_right(self):
        self._load()
        return self._window_1_right

    @window_1_right.setter
    def window_1_right(self, v):
        type_bound_u8(v, "Window bound")
        self._window_1_right = v
        self._save()

    @property
    def window_2_left(self):
        self._load()
        return self._window_2_left

    @window_2_left.setter
    def window_2_left(self, v):
        type_bound_u8(v, "Window bound")
        self._window_2_left = v
        self._save()

    @property
    def window_2_right(self):
        self._load()
        return self._window_2_right

    @window_2_right.setter
    def window_2_right(self, v):
        type_bound_u8(v, "Window bound")
        self._window_2_right = v
        self._save()

    @property
    def mainscreen_colour(self):
        self._load()
        return self._mainscreen_colour

    @mainscreen_colour.setter
    def mainscreen_colour(self, v):
        type_bound_u16(v, "Colour")
        self._mainscreen_colour = v
        self._save()

    @property
    def subscreen_colour(self):
        self._load()
        return self._subscreen_colour

    @subscreen_colour.setter
    def subscreen_colour(self, v):
        type_bound_u16(v, "Colour")
        self._subscreen_colour = v
        self._save()

    @property
    def bgcol_windows(self):
        self._load()
        return self._bgcol_windows

    @bgcol_windows.setter
    def bgcol_windows(self, v):
        type_bound_u8(v, "Windows")
        self._bgcol_windows = v
        self._save()

    @property
    def bgcol_window_1(self):
        self._load()
        return self._bgcol_windows & 0xF

    @bgcol_window_1.setter
    def bgcol_window_1(self, v):
        type_bound_u4(v, "Window")
        self._load()
        self._bgcol_windows &= 0xF0
        self._bgcol_windows |= v
        self._save()

    @property
    def bgcol_window_2(self):
        self._load()
        return (self._bgcol_windows >> 4) & 0x0F

    @bgcol_window_2.setter
    def bgcol_window_2(self, v):
        type_bound_u4(v, "Window")
        self._load()
        self._bgcol_windows &= 0x0F
        self._bgcol_windows |= (v << 4)
        self._save()

    def _load(self):
        pass

    def _save(self):
        pass

    def __eq__(self, other):
        if (not isinstance(other, MainState)):
            raise TypeError("Other must be MainState")
        self._load()
        other._load()
        equal = super(MainState, self).__eq__(other)
        equal &= self._window_1_left == other._window_1_left
        equal &= self._window_1_right == other._window_1_right
        equal &= self._window_2_left == other._window_2_left
        equal &= self._window_2_right == other._window_2_right
        equal &= self._mainscreen_colour == other._mainscreen_colour
        equal &= self._subscreen_colour == other._subscreen_colour
        equal &= self._bgcol_windows == other._bgcol_windows
        return equal
    
class Sprite(HasFlags, HasWindows, HasPosition, HasBindPoint):

    WIDTH_POWER = 8
    HEIGHT_POWER = 8
    WIDTH = (1 << WIDTH_POWER)
    HEIGHT = (1 << HEIGHT_POWER)
    ENABLED = (1 << 0)
    PRIORITY = (1 << 1)
    FLIP_X = (1 << 2)
    FLIP_Y = (1 << 3)
    C_MATH = (1 << 4)
    DOUBLE = (1 << 5)

    def __init__(self):
        self._max_bind = SPRITE_COUNT - 1
        super(Sprite, self).__init__()
        self._width = 32
        self._height = 32
        self._graphics_x = 32
        self._graphics_y = 32

    @property
    def width(self):
        self._load()
        return self._width

    @width.setter
    def width(self, v):
        type_bound_u8(v, "Dimension")
        if ((v & 0x7) > 0):
            raise ValueError("Width must be multiple of 8 ({val})".format(val=v))
        self._width = v
        self._save()

    @property
    def height(self):
        self._load()
        return self._height

    @height.setter
    def height(self, v):
        type_bound_u8(v, "Dimension")
        self._height = v
        self._save()

    @property
    def graphics_x(self):
        self._load()
        return self._graphics_x

    @graphics_x.setter
    def graphics_x(self, v):
        type_bound_u8(v, "Graphics position")
        if ((v & 0x7) > 0):
            raise ValueError("Graphics x position must be multiple of 8 ({val})".format(val=v))
        self._graphics_x = v
        self._save()

    @property
    def graphics_y(self):
        self._load()
        return self._graphics_y

    @graphics_y.setter
    def graphics_y(self, v):
        type_bound_u8(v, "Graphics position")
        self._graphics_y = v
        self._save()

    def _load(self):
        pass

    def _save(self):
        pass

    def __eq__(self, other):
        if (not isinstance(other, Sprite)):
            raise TypeError("Other must be Sprite")
        self._load()
        other._load()
        equal = super(Sprite, self).__eq__(other)
        equal &= self._width == other._width
        equal &= self._height == other._height
        equal &= self._graphics_x == other._graphics_x
        equal &= self._graphics_y == other._graphics_y
        return equal
    
class OAM:
    #def __init__(self):
    #    self._i = 0

    #def __iter__(self):
    #    return self

    #def __next__(self): 
    #    self._i += 1
    #    if self._i < SPRITE_COUNT:
    #        return self[self._i]
    #    raise StopIteration
    
    def __getitem__(self, key):
        if (not isinstance(key, int)):
            raise TypeError("OAM index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("OAM index out of bounds ({val})".format(val=key))
        spr = Sprite()
        spr.bind(key, False)
        return spr

    def __setitem__(self, key, spr):
        if (not isinstance(key, int)):
            raise TypeError("OAM index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("OAM index out of bounds ({val})".format(val=key))
        if (not isinstance(spr, Sprite)):
            raise TypeError("OAM value must be Sprite")
        bind_point = spr._bound
        spr.bind(key)
        spr.bind(bind_point, False)
        return spr
    
    def __len__(self):
        return SPRITE_COUNT
    
class HDMA:
    def __init__(self, table):
        self._table = table

    def __getitem__(self, key):
        if (not isinstance(key, int)):
            raise TypeError("HDMA index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("HDMA index out of bounds ({val})".format(val=key))
        #todo
        return 0
    
    def __setitem__(self, key, entry):
        if (not isinstance(key, int)):
            raise TypeError("HDMA index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("HDMA index out of bounds ({val})".format(val=key))
        #todo

    def __len__(self):
        return (240)

class MAP:
    def __init__(self, bg):
        self._bg = bg

    def __getitem__(self, key):
        if (not isinstance(key, int)):
            raise TypeError("Map index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("Map index out of bounds ({val})".format(val=key))
        #todo
        return 0
    
    def __setitem__(self, key, tile):
        if (not isinstance(key, int)):
            raise TypeError("Map index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("Map index out of bounds ({val})".format(val=key))
        type_bound_u16(tile, "Map tile")
        #todo

    def __len__(self):
        return (MAP_HEIGHT * MAP_WIDTH)

oam = OAM()
bg0 = MAP(0)
bg1 = MAP(1)
hdma_0 = HDMA(0)
hdma_1 = HDMA(1)
hdma_2 = HDMA(2)
hdma_3 = HDMA(3)
hdma_4 = HDMA(4)
hdma_5 = HDMA(5)
hdma_6 = HDMA(6)
hdma_7 = HDMA(7)

_hdma_enable = 0x00

def __getattr__(name):
    if name == 'hdma_enable':
        return _hdma_enable
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def __setattr__(name, value):
    if name == 'hdma_enable':
        type_bound_u16(value, "HDMA enable")
        _hdma_enable = value
        return
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
