import _sim
import time

times = []
def update_times():
    global times
    now = time.ticks_ms()
    times.append(now)
    times = [time for time in times if time > now - 1000]

def gfx_init():
    pass

def start_display_flip_task():
    pass

def section_ready(section):
    return True

def all_sections_ready():
    return True

def flip_sasppu_section(section):
    if (section == 3):
        update_times()
        _sim.display_update_sasppu()

def end_frame(ctx):
    update_times()
    _sim.display_update(ctx)

def start_frame():
    return _sim.start_frame()

def hexagon(ctx, x, y, dim):
    return ctx.round_rectangle(x-dim, y-dim, 2*dim, 2*dim, dim).fill()

def get_fps():
    return len(times)