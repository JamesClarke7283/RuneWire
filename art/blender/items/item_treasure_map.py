"""item_treasure_map: a half-unrolled treasure map, about 0.34 m wide (lead-added item).

A parchment sheet unrolled between two chunky rolls with wooden end knobs, a muted green island with an
ink outline, a dotted red trail to a big red X, a little ink compass rose, a red wax seal and a twine tie
around the left roll. One mesh object "TreasureMap", origin at the centre (finished by itemlib).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_treasure_map"
rw.reset()
random.seed(7)
rw.flat("MapLand", "b9cf8a", 0.9, 0.0)
parts = []

# --- the sheet (top face at z = 0.006) and the two rolls --------------------------------------------------
SW, SD, ST = 0.25, 0.2, 0.006
parts.append(rw.rounded_box("sheet", (SW, SD, ST), 0.002, (0.0, 0.0, ST / 2), mat=il.mat("Parchment"), segments=1))
for x, r in ((-0.135, 0.03), (0.13, 0.022)):
    parts.append(rw.cylinder("roll", r, SD + 0.012, 18, (x, 0.0, r), (90, 0, 0), mat=il.mat("Parchment")))
    # the rolled edge shows a darker spiral line at each end
    for sy in (-1, 1):
        parts.append(rw.torus("roll_edge", r * 0.55, 0.0035, 14, 4, (x, sy * (SD / 2 + 0.007), r), (90, 0, 0), mat=il.mat("Ink")))
        parts.append(rw.sphere("knob", r * 0.62, 12, 6, (x, sy * (SD / 2 + 0.022), r), mat="M_WoodDark"))
# twine tie and wax seal on the left roll
parts.append(rw.torus("twine", 0.032, 0.0045, 18, 5, (-0.135, 0.045, 0.03), (90, 0, 0), mat=il.mat("Twine")))
parts.append(rw.torus("twine", 0.032, 0.0045, 18, 5, (-0.135, 0.035, 0.03), (90, 0, 0), mat=il.mat("Twine")))
parts.append(pl.disc("seal", 0.024, 0.009, (0, -1, 0.35), (-0.135, -0.01, 0.052), il.mat("Wax"), 14, 0.5))

# --- the map drawing on the sheet --------------------------------------------------------------------------
Z = ST + 0.0012
land = []
for i in range(14):
    a = 2 * math.pi * i / 14
    rr = 0.062 + random.uniform(-0.012, 0.014)
    land.append((0.005 + math.cos(a) * rr * 1.25, 0.004 + math.sin(a) * rr))
parts.append(rw.extrude_poly("land", land, 0.0016, (0, 0, Z), mat="MapLand"))
outline = [(0.005 + (x - 0.005) * 1.08, 0.004 + (y - 0.004) * 1.08) for (x, y) in land]
for i in range(len(outline)):
    a, b = outline[i], outline[(i + 1) % len(outline)]
    parts.append(pl.capsule("coast", (a[0], a[1], Z), (b[0], b[1], Z), 0.0022, 5, 1, il.mat("Ink")))
# dotted trail curling across the island to the X
trail = [(-0.085, -0.06), (-0.06, -0.05), (-0.037, -0.032), (-0.02, -0.008), (-0.002, 0.012), (0.02, 0.022), (0.04, 0.026)]
for (x, y) in trail:
    parts.append(pl.disc("dot", 0.0055, 0.0018, (0, 0, 1), (x, y, Z + 0.0004), il.mat("HeartRed"), 8, 0.3))
XC = (0.062, 0.034)
for ang in (45, -45):
    parts.append(rw.rounded_box("x_mark", (0.052, 0.012, 0.0035), 0.002, (XC[0], XC[1], Z + 0.001), (0, 0, ang),
                                mat=il.mat("HeartRed"), segments=1))
# compass rose in the corner
parts.append(rw.extrude_poly("rose", il.star_pts(4, 0.026, 0.008, 90.0), 0.002, (0.095, -0.07, Z), mat=il.mat("Ink")))
parts.append(rw.torus("rose_ring", 0.017, 0.0018, 16, 4, (0.095, -0.07, Z), mat=il.mat("Ink")))

rw.join(parts, "TreasureMap", origin=(0, 0, 0))
il.finish_item(ASSET)
