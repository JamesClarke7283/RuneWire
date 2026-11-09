"""item_regen_salve: "Mender's Salve", a round tin of green salve with its lid tipped open, about 0.22 x 0.20 x 0.10 m.

A squat round steel tin (M_Steel) with a green enamel band round its side, brim-full of glossy green salve with a
soft-serve swirl; its lid (steel, green enamel top with a cream leaf emblem and veins) sits tipped half open,
slid back and tilted on the rim so the emblem faces the 3/4 view above the uncovered salve.
One mesh object "RegenSalve", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_regen_salve"
rw.reset()

STEEL = pk.mat("M_Steel")
ENAMEL = pk.flat("MenderGreen", "2f9a46", 0.45, 0.0)
EMBLEM = pk.flat("MenderEmblem", "f6ecc8", 0.6, 0.0)
SALVE = pk.mat("SalveGreen")
SALVE_HI = pk.mat("SalveLight")
R, HT = 0.092, 0.056                                    # tin radius and height

tin = [(0.0, 0.0), (R - 0.006, 0.0), (R - 0.001, 0.005), (R, 0.014), (R, HT - 0.004), (R - 0.003, HT),
       (R - 0.007, HT - 0.001), (R - 0.007, HT - 0.012)]
parts = [il.lathe("tin", tin, segs=28, m=STEEL, smooth=40)]
parts.append(pl.band("enamel", R + 0.002, 0.026, 0.004, (0, 0, 1), (0, 0, 0.029), ENAMEL, 28, 0.0))
# the salve: a glossy dome with a soft-serve swirl peak
salve = [(R - 0.0068, HT - 0.012), (R - 0.0068, HT - 0.004), (R - 0.02, HT - 0.001), (0.05, HT + 0.002),
         (0.03, HT + 0.005), (0.0, HT + 0.006)]
parts.append(il.lathe("salve", salve, segs=24, m=SALVE, smooth=60))
# soft-serve swirl: three stacked creamy rings shrinking upward and a curled tip, in the uncovered front-left
SX, SY = -0.046, -0.036
for (r, z) in ((0.024, HT + 0.011), (0.017, HT + 0.024), (0.01, HT + 0.035)):
    parts.append(rw.torus("swirl", r, 0.0105 - 0.0018 * (z - HT) / 0.013, 16, 6, (SX + 0.002, SY, z), mat=SALVE_HI))
parts.append(pl.sausage("swirl_tip", [V((SX + 0.004, SY, HT + 0.039)), V((SX + 0.002, SY, HT + 0.048)),
                                      V((SX - 0.007, SY + 0.003, HT + 0.052))],
                        [0.007, 0.005, 0.0025], 8, 2, SALVE_HI, (True, True), 2, True, 60))

# lid: a steel puck with a rolled rim, green enamel top and a cream leaf emblem, hinged at the back and tipped open
LZ = HT + 0.001
lid_parts = [il.lathe("lid", [(0.0, LZ), (R + 0.004, LZ), (R + 0.006, LZ + 0.005), (R + 0.006, LZ + 0.012),
                              (R + 0.002, LZ + 0.016), (0.0, LZ + 0.016)], segs=28, m=STEEL, smooth=40)]
lid_parts.append(pl.disc("lid_enamel", R - 0.008, 0.004, (0, 0, 1), (0, 0, LZ + 0.016), ENAMEL, 28, 0.3))
top = V((0, 0, LZ + 0.0175))
lid_parts.append(il.wrap_prism("emblem", pk.leaf_shape_pts(0.05, 0.11, 10), il.plane_map(top, (1, 0, 0), (0, 1, 0),
                                                                                       0.0, 0.0035), EMBLEM, 30))
lid_parts.append(pl.obox("vein", (0.08, 0.0045, 0.002), top + V((0, -0.002, 0.0035)), (0, 1, 0), (0, 0, 1), ENAMEL))
for s_ in (-1, 1):
    for k in range(2):
        y = -0.018 + 0.03 * k
        lid_parts.append(pl.obox("vein", (0.024, 0.0035, 0.002), top + V((s_ * 0.009, y, 0.0035)),
                                 (s_ * 0.55, 1, 0), (0, 0, 1), ENAMEL))
lid = rw.join(lid_parts, "lid", origin=(0, 0, 0))
# tipped half open: slid toward the back-right and tilted so its front-left edge dips onto the salve
sdir = V((0.85, 0.53, 0.0)).normalized()
axis = V((0, 0, 1)).cross(sdir)
c0 = V((0, 0, LZ))
pk.transform(lid, il.Matrix.Translation(sdir * 0.074 + V((0, 0, 0.006))) @ pk.rot(axis, -19, c0))
parts.append(lid)
salve_tin = rw.join(parts, "RegenSalve", origin=(0, 0, 0))
pk.fit(salve_tin, 0.22)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.22,))
