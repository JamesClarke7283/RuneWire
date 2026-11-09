"""item_scrap_gear: a chunky rusty salvaged gear, 0.4 m across, standing upright (axis along Blender Y).

A thick rusty gear rim (M_Rust) with one broken tooth, four spokes and a dark-metal hub (M_DarkMetal), a
big hex bolt through the middle with a washer on the front and a nut + thread stub on the back, a couple
of dark-metal patch plates riveted over cracks. One mesh object "ScrapGear", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_scrap_gear"
rw.reset()

R, TH = 0.2, 0.075
FRONT = V((0, -1, 0))
parts = [il.gear("rim", R, 10, 0.05, TH, 0.118, (0, 0, 0), (0, -1, 0), "M_Rust", spin=4, bevel=0.008, skip=(7,))]
# hub and four spokes
parts.append(il.lathe("hub", [(0.0, -0.05), (0.05, -0.05), (0.058, -0.04), (0.058, 0.04), (0.05, 0.05),
                              (0.0, 0.05)], (0, -1, 0), (0, 0, 0), 20, "M_DarkMetal", 40))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    parts.append(pl.beam_between("spoke", d * 0.045, d * 0.13, (0.05, 0.05), il.mat("M_Rust"), rounded=0.012,
                                 up=(0, 1, 0)))

# the bolt: washer + hex head on the front, nut + thread stub on the back
parts.append(pl.bolt(FRONT * 0.05, FRONT, 0.034, 0.024, il.mat("M_Steel"), "bolt", True, 15))
parts.append(pl.bolt(-FRONT * 0.05, -FRONT, 0.03, 0.02, il.mat("M_DarkMetal"), "nut", True, 0))
parts.append(il.lathe("thread", [(0.0, 0.07), (0.017, 0.07), (0.017, 0.098), (0.012, 0.103), (0.0, 0.103)],
                      (0, 1, 0), (0, 0, 0), 10, "M_Steel", 40))

# riveted patch plates over two cracks on the rim face (front)
for (ang, w) in ((182, 0.07), (-18, 0.06)):
    a = math.radians(ang)
    p = V((math.cos(a) * 0.135, -TH / 2 - 0.004, math.sin(a) * 0.135))
    plate = pl.obox("patch", (w, 0.03, 0.012), p, (-math.sin(a), 0, math.cos(a)), FRONT, il.mat("M_DarkMetal"),
                    rounded=0.004, segments=1)
    parts.append(plate)
    t = V((-math.sin(a), 0, math.cos(a)))
    for s in (-1, 1):
        parts.append(pl.rivet(p + t * (s * (w / 2 - 0.012)) + FRONT * 0.006, FRONT, 0.0075, 0.005,
                              il.mat("M_Brass"), 5))

gearo = rw.join(parts, "ScrapGear")
rw.smooth(gearo, 35)
il.finish_item(ASSET, (0.4, 0.2, 0.4))
