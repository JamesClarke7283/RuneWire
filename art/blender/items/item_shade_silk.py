"""item_shade_silk: a wooden spool wound with shimmering dark-purple ghost silk, about 0.25 x 0.22 x 0.33 m.

A chunky turned-wood spool (M_WoodPlanks flanges with chamfered rims, a brass hub ring round a dark axle
hole on top) wound fat with ghost silk (M_Fabric__3b2357) in soft ridges, a few lighter shimmer strands,
glowing teal threads wrapped round it (rw.glow), and a loose ghostly end of silk peeling off and floating
up and away in a wavy, tapering ribbon. One mesh object "ShadeSilk", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_shade_silk"
rw.reset()

SILK = "M_Fabric__3b2357"
SHIMMER = "M_Fabric__7a5cb8"
H, ZA, ZB = 0.3, 0.032, 0.268


def r_silk(z):
    t = (z - ZA) / (ZB - ZA)
    return 0.069 + 0.012 * math.sin(math.pi * t) + 0.0022 * math.sin(2 * math.pi * 7 * t)


# flanges and the wound silk
fl = [(0.0, 0.0), (0.094, 0.0), (0.103, 0.008), (0.103, 0.024), (0.094, 0.032), (0.0, 0.032)]
parts = [il.lathe("flange", fl, segs=28, m="M_WoodPlanks", smooth=40),
         il.lathe("flange", [(r, H - z) for (r, z) in reversed(fl)], segs=28, m="M_WoodPlanks", smooth=40)]
prof = [(0.0, ZA - 0.002)] + [(r_silk(ZA + (ZB - ZA) * i / 24), ZA + (ZB - ZA) * i / 24) for i in range(25)] + \
       [(0.0, ZB + 0.002)]
parts.append(il.lathe("silk", prof, segs=24, m=SILK, smooth=70))
# brass hub round a dark axle hole, top and bottom
for (z, n) in ((H, (0, 0, 1)), (0.0, (0, 0, -1))):
    parts.append(pl.band("hub", 0.03, 0.012, 0.014, n, (0, 0, z), il.mat("M_Brass"), 16, 0.3))
    parts.append(pl.disc("hole", 0.017, 0.006, n, (0, 0, z), il.mat("PouchShadow"), 12))


def wound(phase, turns, z0, z1, mat, r=0.0065, lift=0.0015):
    pts = []
    n = int(turns * 14) + 1
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        a = math.radians(phase) + 2 * math.pi * turns * t
        rr = r_silk(z) + lift
        pts.append(V((rr * math.cos(a), rr * math.sin(a), z)))
    return pl.sausage("thread", pts, r, 6, 1, il.mat(mat), (True, True), 1, True, 60)


parts.append(wound(200, 1.3, 0.06, 0.24, "TealGlow"))
parts.append(wound(20, 1.1, 0.085, 0.215, "TealGlow"))
parts.append(wound(110, 0.9, 0.05, 0.25, SHIMMER, 0.0075, 0.0))
parts.append(wound(290, 0.8, 0.07, 0.2, SHIMMER, 0.0075, 0.0))

# the loose ghostly end: peels off the spool on the right and floats up and away in a wavy, tapering ribbon
a0 = math.radians(-35)
start = V((r_silk(0.16) * math.cos(a0), r_silk(0.16) * math.sin(a0), 0.16))
wisp = [start, start + V((0.03, -0.02, 0.01)), V((0.13, -0.05, 0.2)), V((0.12, -0.045, 0.26)), V((0.15, -0.05, 0.31)),
        V((0.185, -0.055, 0.345))]
parts.append(pl.sausage("wisp", wisp, [0.02, 0.024, 0.024, 0.019, 0.012, 0.003], 8, 4, il.mat(SILK), (True, True), 2,
                        True, 60, (0.26, 1.0), (0, -1, 0)))
parts.append(pl.sausage("wisp_thread", [p + V((-0.002, -0.007, 0.0)) for p in wisp[1:5]], [0.0042, 0.0042, 0.0038, 0.003], 5,
                        3, il.mat("TealGlow"), (True, True), 1, True, 60))

spool = rw.join(parts, "ShadeSilk")
il.finish_item(ASSET, (0.24, 0.22, 0.34))
