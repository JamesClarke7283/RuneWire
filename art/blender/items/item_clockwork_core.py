"""item_clockwork_core: a palm-sized brass clockwork heart, about 0.22 x 0.22 x 0.27 m.

A spherical brass armillary cage (an equator ring and two meridian rings, studded where they cross) with
turned brass caps top and bottom, holding a glowing orange tech core (M_TechGlow) wrapped by two little
brass and copper gears, and a butterfly wind-up key on top. One mesh object "ClockworkCore", origin at
the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_clockwork_core"
rw.reset()

R = 0.092
il.preview_glow("M_TechGlow", "ff6a10", "ff7a1a", 0.6)   # preview/icon only: Godot swaps M_* materials by name
brass = il.mat("M_Brass")
parts = []
# cage rings
parts.append(rw.torus("ring", R, 0.0095, 26, 6, (0, 0, 0), (0, 0, 0), brass))
parts.append(rw.torus("ring", R, 0.0085, 26, 6, (0, 0, 0), (90, 0, 0), brass))
parts.append(rw.torus("ring", R, 0.0085, 26, 6, (0, 0, 0), (0, 90, 0), brass))
for a in range(4):                                       # studs where the meridians cross the equator
    d = V((math.cos(math.radians(90 * a)), math.sin(math.radians(90 * a)), 0))
    parts.append(pl.rivet(d * (R + 0.008), d, 0.014, 0.008, brass, 8))
# caps
cap = [(0.0, R - 0.025), (0.034, R - 0.025), (0.036, R - 0.01), (0.03, R + 0.008), (0.018, R + 0.014), (0.0, R + 0.014)]
parts.append(il.lathe("cap", cap, segs=14, m="M_Brass", smooth=40))
parts.append(il.lathe("cap", [(r, -z) for (r, z) in reversed(cap)], segs=14, m="M_Brass", smooth=40))
parts.append(il.lathe("foot", [(0.0, -R - 0.03), (0.04, -R - 0.03), (0.044, -R - 0.024), (0.04, -R - 0.016),
                               (0.02, -R - 0.008), (0.0, -R - 0.008)], segs=16, m="M_Brass", smooth=40))
# glowing core and gears
parts.append(rw.sphere("core", 0.046, 18, 10, (0, 0, 0), mat="M_TechGlow"))
parts.append(pl.band("core_band", 0.05, 0.016, 0.008, (0, 0, 1), (0, 0, 0), il.mat("M_Copper"), 18, 0.0))
parts.append(il.gear("gear", 0.042, 9, 0.011, 0.012, 0.014, (0.0, -0.05, 0.012), (0, -1, 0.15), "M_Brass", spin=8))
parts.append(il.gear("gear", 0.034, 8, 0.01, 0.011, 0.011, (0.052, 0.012, -0.018), (1, 0.1, 0.2), "M_Copper"))
parts.append(il.gear("gear", 0.03, 7, 0.009, 0.01, 0.0, (-0.05, 0.02, 0.03), (-1, 0.2, -0.1), "M_Brass", spin=4))
# posts holding the core between the caps
for sz in (-1, 1):
    parts.append(pl.rod("post", V((0, 0, sz * 0.04)), V((0, 0, sz * (R - 0.02))), 0.011, 8, brass))
# wind-up key on top
KZ = R + 0.014
parts.append(pl.rod("key_shaft", V((0, 0, KZ - 0.005)), V((0, 0, KZ + 0.024)), 0.0085, 8, brass))
parts.append(pl.rivet(V((0, 0, KZ + 0.02)), (0, 0, 1), 0.015, 0.009, brass, 10))
for sx in (-1, 1):
    parts.append(pl.disc("key_wing", 0.021, 0.011, (0, 1, 0), (sx * 0.021, 0, KZ + 0.047), brass, 14, 0.3))
parts.append(pl.obox("key_mid", (0.016, 0.015, 0.03), (0, 0, KZ + 0.04), rounded=0.005, segments=1, mat=brass))

core = rw.join(parts, "ClockworkCore")
il.finish_item(ASSET, (0.2, 0.2, 0.28))
