"""item_arcane_thread: a skein of glowing teal thread on a brass bobbin, about 0.24 x 0.24 x 0.15 m.

A small brass bobbin lying on its side (along Blender X): two gear-toothed brass flanges with rivets, a brass axle
with turned end knobs, wound fat with a barrel of glowing teal arcane thread (emissive flat) criss-crossed by
brighter winding strands, and a loose end that curls off the front in a loop and finishes in a little teal
sparkle. Deliberately unlike item_shade_silk (an upright wooden spool of dark purple silk).
One mesh object "ArcaneThread", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_arcane_thread"
rw.reset()

X = V((1, 0, 0))
HL = 0.07          # half-length of the wound barrel (flanges just outside)
parts = []


def r_thread(h):
    t = h / HL
    return 0.043 + 0.016 * (1 - t * t)


# wound thread barrel and the brighter criss-cross winding strands
prof = [(0.0, -HL)] + [(r_thread(-HL + 2 * HL * i / 8), -HL + 2 * HL * i / 8) for i in range(9)] + [(0.0, HL)]
parts.append(il.lathe("thread", prof, X, (0, 0, 0), 20, ml.mat("ThreadGlow"), 70))


def winding(phase, turns, h0, h1, lift=0.0015):
    pts = []
    n = int(abs(turns) * 12) + 1
    for i in range(n):
        t = i / (n - 1)
        h = h0 + (h1 - h0) * t
        a = math.radians(phase) + 2 * math.pi * turns * t
        r = r_thread(h) + lift
        pts.append(V((h, r * math.cos(a), r * math.sin(a))))
    return pl.sausage("winding", pts, 0.0062, 6, 1, ml.mat("ThreadGlowHi"), (True, True), 1, True, 60)


parts.append(winding(200, 1.25, -0.06, 0.06))
parts.append(winding(20, -1.25, -0.06, 0.06))

# brass flanges: chunky gears with four rivets on the outer face, a hub boss and an axle with end knobs
for sx in (-1, 1):
    c = V((sx * (HL + 0.009), 0, 0))
    parts.append(il.gear("flange", 0.077, 10, 0.013, 0.017, 0.0, c, X * sx, "M_Brass", spin=9))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p = c + X * (sx * 0.0085) + V((0, math.cos(a) * 0.044, math.sin(a) * 0.044))
        parts.append(pl.rivet(p, X * sx, 0.0085, 0.006, ml.mat("M_Brass"), 6))
    parts.append(il.lathe("knob", [(0.0, 0.0), (0.021, 0.0), (0.022, 0.007), (0.017, 0.015), (0.0, 0.019)],
                          X * sx, c + X * (sx * 0.006), 12, "M_Brass", 40))

# the loose end: peels off the front of the barrel, loops round and ends in a little teal sparkle
a0 = math.radians(-70)
start = V((0.035, r_thread(0.035) * math.cos(a0), r_thread(0.035) * math.sin(a0)))
curl = [start, start + V((0.012, -0.022, -0.004)), V((0.07, -0.085, -0.03)), V((0.105, -0.1, 0.0)),
        V((0.09, -0.085, 0.035)), V((0.06, -0.09, 0.02)), V((0.07, -0.11, -0.01)), V((0.115, -0.125, -0.02))]
parts.append(pl.sausage("strand", curl, 0.0075, 6, 3, ml.mat("ThreadGlow"), (True, True), 1, True, 60))
parts += il.spark("sparkle", curl[-1] + V((0.012, -0.004, 0.004)), 0.024, 6, ml.mat("ThreadGlowHi"), 3,
                  ml.mat("ThreadGlowHi"))

bobbin = rw.join(parts, "ArcaneThread")
ml.preview_metals()
il.finish_item(ASSET, (0.24, 0.24, 0.15))
