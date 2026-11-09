"""item_power_cell: a glass-cylinder power cell, about 0.14 x 0.14 x 0.29 m, standing upright.

A chunky glass tube (M_Glass above the fill line) full of glowing teal ley liquid (emissive flat 39d5c4) with a few
brighter bubbles at the glass, a copper electrode rod running down its middle, ribbed brass end caps joined by
four brass struts with rivets, and a brass terminal post on top with a red ring and a round knob beside a
raised red "+".
One mesh object "PowerCell", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_power_cell"
rw.reset()

BR = ml.mat("M_Brass")
Z0, Z1 = 0.042, 0.2            # glass tube between the caps
RG = 0.054                     # glass radius
FILL = 0.172
parts = []

# glass tube: liquid-coloured below the fill line (reads strongly in icons), glass above; liquid surface disc
tube = il.lathe("glass", [(0.0, Z0 - 0.004), (RG, Z0 - 0.004), (RG, FILL), (RG, Z1 + 0.004), (0.0, Z1 + 0.004)],
                (0, 0, 1), (0, 0, 0), 24, "M_Glass", 50)
rw.set_mat_where(tube, ml.mat("CellGlow"), lambda c, n: c.z < FILL - 1e-4)
parts.append(tube)
parts.append(rw.cylinder("surface", RG - 0.004, 0.003, 20, (0, 0, FILL - 0.003), mat=ml.mat("CellGlowHi")))
# copper electrode down the middle (seen above the liquid)
parts.append(pl.rod("electrode", V((0, 0, FILL - 0.03)), V((0, 0, Z1)), 0.011, 10, ml.mat("M_Copper")))
# bubbles at the glass
rnd = random.Random(4)
for (ang, z, r) in ((-30, 0.07, 0.009), (-10, 0.1, 0.006), (-48, 0.122, 0.0075), (-20, 0.148, 0.0055),
                    (15, 0.085, 0.0065), (-62, 0.095, 0.005), (5, 0.13, 0.0055)):
    a = math.radians(ang)
    d = V((math.sin(a), -math.cos(a), 0.0))
    parts.append(rw.ico("bubble", r, 1, tuple(d * (RG + r * 0.15) + V((0, 0, z))), (0, 0, rnd.uniform(0, 60)),
                        (1, 1, 1), ml.mat("CellGlowHi"), None, 70))


def cap(z_base, flip):
    """Ribbed brass end cap; z_base = the face against the glass, flip = grows downward."""
    s = -1 if flip else 1
    prof = [(0.0, 0.0), (0.068, 0.0), (0.072, 0.006), (0.072, 0.014), (0.066, 0.017), (0.066, 0.022), (0.071, 0.025),
            (0.071, 0.033), (0.064, 0.04), (0.0, 0.042)]
    if flip:
        prof = [(r, -h) for (r, h) in reversed(prof)]
    return il.lathe("cap", [(r, z_base + h) for (r, h) in prof], (0, 0, 1), (0, 0, 0), 24, BR, 40)


parts.append(cap(Z0, True))
parts.append(cap(Z1, False))
# four struts between the caps with rivets at both ends
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = V((math.cos(a), math.sin(a), 0.0))
    parts.append(pl.obox("strut", (0.016, 0.009, Z1 - Z0 + 0.012), d * (RG + 0.008) + V((0, 0, (Z0 + Z1) / 2)),
                         d.cross(V((0, 0, 1))), (0, 0, 1), BR, rounded=0.003, segments=1))
    for z in (Z0 + 0.012, Z1 - 0.012):
        parts.append(pl.rivet(d * (RG + 0.0125) + V((0, 0, z)), d, 0.0075, 0.005, BR, 6))
# terminal post: a short brass post with a red insulating ring and a round knob
ZT = Z1 + 0.042
parts.append(pl.rod("post", V((0, 0, ZT - 0.004)), V((0, 0, ZT + 0.018)), 0.014, 12, BR))
parts.append(pl.band("insulator", 0.024, 0.01, 0.012, (0, 0, 1), (0, 0, ZT + 0.006), ml.mat("TerminalRed"), 16, 0.4))
parts.append(rw.sphere("knob", 0.018, 14, 8, (0, 0, ZT + 0.028), mat=BR))
# a raised red "+" on the top cap, toward the viewer
PLUS = V((-0.043, -0.03, ZT))
for ang in (40, 130):
    bar = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
    parts.append(pl.obox("plus", (0.03, 0.009, 0.007), PLUS, bar, (0, 0, 1), ml.mat("TerminalRed"), rounded=0.0025,
                         segments=1))

cell = rw.join(parts, "PowerCell")
ml.preview_metals()
il.finish_item(ASSET, (0.14, 0.14, 0.29))
