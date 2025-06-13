"""
sasppu.py wraps a WebAssembly-compiled sasppu in functions that act similar to the micropython interface.
"""
import os
import math
import sys

import wasmer
import wasmer_compiler_cranelift

from struct import pack, unpack_from

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
        self._i.exports.SASPPU_gfx_reset()

    def malloc(self, n):
        return self._i.exports.malloc(n)

    def free(self, p):
        self._i.exports.free(p)

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

TRANSPARENT_BLACK = _wasm._i.exports.macro_TRANSPARENT_BLACK()
OPAQUE_BLACK = _wasm._i.exports.macro_OPAQUE_BLACK()
RED = _wasm._i.exports.macro_RED()
GREEN = _wasm._i.exports.macro_GREEN()
BLUE = _wasm._i.exports.macro_BLUE()
WHITE = _wasm._i.exports.macro_WHITE()

HDMA_NOOP = 0
HDMA_DISABLE = 1
HDMA_MAIN_STATE_MAINSCREEN_COLOUR = 2
HDMA_MAIN_STATE_SUBSCREEN_COLOUR = 3
HDMA_MAIN_STATE_WINDOW1_LEFT = 4
HDMA_MAIN_STATE_WINDOW1_RIGHT = 5
HDMA_MAIN_STATE_WINDOW2_LEFT = 6
HDMA_MAIN_STATE_WINDOW2_RIGHT = 7
HDMA_MAIN_STATE_BGCOL_WINDOWS = 8
HDMA_MAIN_STATE_FLAGS = 9
HDMA_CMATH_STATE_SCREEN_FADE = 10
HDMA_CMATH_STATE_FLAGS = 11
HDMA_BACKGROUND0_X = 12
HDMA_BACKGROUND0_Y = 13
HDMA_BACKGROUND0_WINDOWS = 14
HDMA_BACKGROUND0_FLAGS = 15
HDMA_BACKGROUND1_X = 16
HDMA_BACKGROUND1_Y = 17
HDMA_BACKGROUND1_WINDOWS = 18
HDMA_BACKGROUND1_FLAGS = 19
HDMA_HDMA_ENABLE = 20

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
        if (self._bound == 0):
            bg = _wasm._i.exports.get_background_0()
        elif (self._bound == 1):
            bg = _wasm._i.exports.get_background_1()
        else:
            return
        unpacked = unpack_from('hhBB', _wasm._i.exports.memory.buffer, bg)
        self._x = unpacked[0]
        self._y = unpacked[1]
        self._windows = unpacked[2]
        self._flags = unpacked[3]

    def _save(self):
        if (self._bound < 0):
            return
        packed = pack('hhBB', self._x, self._y, self._windows, self._flags)
        p = _wasm.malloc(len(packed))
        mem = _wasm._i.exports.memory.uint8_view(p)
        mem[0 : len(packed)] = packed
        if (self._bound == 0):
            _wasm._i.exports.set_background_0(p)
        elif (self._bound == 1):
            _wasm._i.exports.set_background_1(p)
        _wasm.free(p)

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
        if (self._bound < 0):
            return
        cmath = _wasm._i.exports.get_cmath_state()
        unpacked = unpack_from('HB', _wasm._i.exports.memory.buffer, cmath)
        self._screen_fade = unpacked[0]
        self._flags = unpacked[1]

    def _save(self):
        if (self._bound < 0):
            return
        packed = pack('HB', self._screen_fade, self._flags)
        p = _wasm.malloc(len(packed))
        mem = _wasm._i.exports.memory.uint8_view(p)
        mem[0 : len(packed)] = packed
        _wasm._i.exports.set_cmath_state(p)
        _wasm.free(p)

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
        if (self._bound < 0):
            return
        main = _wasm._i.exports.get_main_state()
        unpacked = unpack_from('HHhhhhBB', _wasm._i.exports.memory.buffer, main)
        self._mainscreen_colour = unpacked[0]
        self._subscreen_colour = unpacked[1]
        self._window_1_left = unpacked[2]
        self._window_1_right = unpacked[3]
        self._window_2_left = unpacked[4]
        self._window_2_right = unpacked[5]
        self._bgcol_windows = unpacked[6]
        self._flags = unpacked[7]

    def _save(self):
        if (self._bound < 0):
            return
        packed = pack('HHhhhhBB',
                      self._mainscreen_colour,
                      self._subscreen_colour,
                      self._window_1_left,
                      self._window_1_right, 
                      self._window_2_left,
                      self._window_2_right, 
                      self._bgcol_windows,
                      self._flags
                      )
        p = _wasm.malloc(len(packed))
        mem = _wasm._i.exports.memory.uint8_view(p)
        mem[0 : len(packed)] = packed
        _wasm._i.exports.set_main_state(p)
        _wasm.free(p)

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
        if (self._bound < 0):
            return
        spr = _wasm._i.exports.get_sprite(self._bound)
        unpacked = unpack_from('hhBBBBBB', _wasm._i.exports.memory.buffer, spr)
        self._x = unpacked[0]
        self._y = unpacked[1]
        self._width = unpacked[2]
        self._height = unpacked[3]
        self._graphics_x = unpacked[4]
        self._graphics_y = unpacked[5]
        self._windows = unpacked[6]
        self._flags = unpacked[7]

    def _save(self):
        if (self._bound < 0):
            return
        packed = pack('hhBBBBBB',
                      self._x,
                      self._y,
                      self._width,
                      self._height, 
                      self._graphics_x,
                      self._graphics_y, 
                      self._windows,
                      self._flags)
        p = _wasm.malloc(len(packed))
        mem = _wasm._i.exports.memory.uint8_view(p)
        mem[0 : len(packed)] = packed
        _wasm._i.exports.set_sprite(self._bound, p)
        _wasm.free(p)

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
        entry = _wasm._i.exports.get_table_entry(self._table, key)
        unpacked = unpack_from('IH', _wasm._i.exports.memory.buffer, entry)
        return unpacked
    
    def __setitem__(self, key, entry):
        if (not isinstance(key, int)):
            raise TypeError("HDMA index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("HDMA index out of bounds ({val})".format(val=key))
        if ((not isinstance(entry, tuple)) or (len(entry) != 2) or (not isinstance(entry[0], int)) or (not isinstance(entry[1], int))):
            raise TypeError("HDMA value must be tuple of two integers")
        if (entry[0] < 0 or entry[0] > 0xFFFF):
            raise ValueError("HDMA value out of bounds ({val})".format(val=key))
        packed = pack('IH', entry[0], entry[1])
        p = _wasm.malloc(len(packed))
        mem = _wasm._i.exports.memory.uint8_view(p)
        mem[0 : len(packed)] = packed
        _wasm._i.exports.set_table_entry(self._table, key, p)
        _wasm.free(p)

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
        if (self._bg == 0):
            return _wasm._i.exports.get_bg0_map(key)
        else:
            return _wasm._i.exports.get_bg1_map(key)
    
    def __setitem__(self, key, tile):
        if (not isinstance(key, int)):
            raise TypeError("Map index must be integer")
        if (key < 0 or key >= len(self)):
            raise ValueError("Map index out of bounds ({val})".format(val=key))
        type_bound_u16(tile, "Map tile")
        if (self._bg == 0):
            _wasm._i.exports.set_bg0_map(key, tile)
        else:
            _wasm._i.exports.set_bg1_map(key, tile)

    def __len__(self):
        return (MAP_HEIGHT * MAP_WIDTH)
    
def cmath(col):
    return _wasm._i.exports.macro_CMATH(col)
def rgb555(r, g, b):
    return _wasm._i.exports.macro_RGB555(r, g, b)
def rgb555_cmath(r, g, b):
    return _wasm._i.exports.macro_RGB555_CMATH(r, g, b)
def rgb888(r, g, b):
    return _wasm._i.exports.macro_RGB888(r, g, b)
def rgb888_cmath(r, g, b):
    return _wasm._i.exports.macro_RGB888_CMATH(r, g, b)
def grey555(g):
    return _wasm._i.exports.macro_GREY555(g)
def grey555_cmath(g):
    return _wasm._i.exports.macro_GREY555_CMATH(g)
def grey888(g):
    return _wasm._i.exports.macro_GREY888(g)
def grey888_cmath(g):
    return _wasm._i.exports.macro_GREY888_CMATH()
def mul_channel(col, mul):
    return _wasm._i.exports.macro_MUL_CHANNEL(col, mul)
def mul_rgb555(r, g, b, mul):
    return _wasm._i.exports.macro_MUL_RGB555(r, g, b, mul)
def r_channel(col):
    return _wasm._i.exports.macro_R_CHANNEL(col)
def g_channel(col):
    return _wasm._i.exports.macro_G_CHANNEL(col)
def b_channel(col):
    return _wasm._i.exports.macro_B_CHANNEL(col)
def cmath_channel(col):
    return _wasm._i.exports.macro_CMATH_CHANNEL(col)
def mul_col(col, mul):
    return _wasm._i.exports.macro_MUL_COL(col, mul)
    
def blit_sprite(x: int, y: int, width: int, height: int, data: bytes, double_size: bool = False):
    if (len(data) < (width * height * 2)):
        raise ValueError("Data not large enough for size")
    p = _wasm.malloc(len(data))
    mem = _wasm._i.exports.memory.uint8_view(p)
    mem[0 : len(data)] = data
    res = _wasm._i.exports.SASPPU_blit_sprite(x, y, width, height, double_size, p)
    _wasm.free(p)
    return res

def fill_background(x: int, y: int, width: int, height: int, colour: int):
    res = _wasm._i.exports.SASPPU_fill_background(x, y, width, height, colour)
    return res

def draw_text_background(x: int, y: int, colour: int, line_width: int, text: str, double_size: bool = False, newline_height: int = 10):
    data = bytes(text + "\x00", encoding="ASCII")
    p = _wasm.malloc(len(data))
    mem = _wasm._i.exports.memory.uint8_view(p)
    mem[0 : len(data)] = data
    res = _wasm._i.exports.SASPPU_draw_text_background(x, y, colour, line_width, newline_height, double_size, p)
    _wasm.free(p)
    return res

def get_text_size(line_width: int, text: str, double_size: bool = False, newline_height: int = 10):
    data = bytes(text + "\x00", encoding="ASCII")
    p = _wasm.malloc(len(data) + 8)
    mem = _wasm._i.exports.memory.uint8_view(p)
    mem[0 : len(data)] = data
    mem[len(data): len(data) + 8] = [0,0,0,0,0,0,0,0]
    _wasm._i.exports.SASPPU_get_text_size(p + len(data), p + len(data) + 4, line_width, newline_height, double_size, p)
    (x, y) = unpack_from("II", _wasm._i.exports.memory.buffer, p + len(data))
    _wasm.free(p)
    return (x, y)

def gfx_reset():
    _wasm._i.exports.SASPPU_gfx_reset()

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

def __getattr__(name):
    if name == 'hdma_enable':
        return _wasm._i.exports.get_hdma_enable()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
def __setattr__(name, value):
    if name == 'hdma_enable':
        type_bound_u8(value, "HDMA enable")
        _wasm._i.exports.set_hdma_enable(value)
        return
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
