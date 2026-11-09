"""item_reed_fiber: a tied bundle of dried reeds, about 0.32 m long, lying along Blender X.

Ten chunky tapered reeds in golden-green, gold and straw tones, pinched together in the middle by three wraps
of brown twine (with a knot and two loose ends on top) and splaying out at both ends; three of them carry brown
cattail seed heads near their right-hand tips. One mesh object "ReedFiber", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_reed_fiber"
rw.reset()

rnd = random.Random(12)
L = 0.31
COLS = ["ReedGold", "ReedGreen", "ReedTan", "ReedGold", "ReedGreen", "ReedGold"]
parts = []
plume_tips = []
NREED = 10
for i in range(NREED):
    phi = 2 * math.pi * i / NREED + rnd.uniform(-0.25, 0.25)
    d = V((0, math.cos(phi), math.sin(phi)))
    r_mid = 0.007 + 0.017 * ((i * 7) % NREED) / NREED          # packed core at the tie
    r_end = r_mid * 1.4 + rnd.uniform(0.035, 0.06)              # splayed ends
    twist = rnd.uniform(-0.35, 0.35)                            # the two ends fan a little differently
    kl, kr = rnd.uniform(0.86, 1.0), rnd.uniform(0.86, 1.0)
    pts, rads = [], []
    for (f, rr) in ((-kl, 0.62), (-0.55, 0.9), (0.0, 1.0), (0.55, 0.9), (kr, 0.62)):
        x = f * L / 2
        s = abs(f) ** 1.6
        rot = V((0, math.cos(phi + twist * f), math.sin(phi + twist * f)))
        off = rot * (r_mid + (r_end - r_mid) * s)
        pts.append(V((x, 0, 0)) + off)
        rads.append(0.0105 * rr * rnd.uniform(0.92, 1.08))
    parts.append(pl.sausage("reed", pts, rads, 5, 3, ml.mat(COLS[i % len(COLS)]), (True, True), 1, True, 60))
    if i in (0, 4, 7):
        plume_tips.append((pts[-2].lerp(pts[-1], 0.55), (pts[-1] - pts[-2]).normalized()))

# brown cattail seed heads near the right-hand tips (a fat capsule round the reed)
for (p, t) in plume_tips:
    parts.append(pl.capsule("cattail", p - t * 0.032, p + t * 0.032, 0.0175, 8, 3, ml.mat("ReedHead")))

# twine: three wraps round the waist, a knot on top and two loose ends
for x in (-0.014, 0.0, 0.014):
    parts.append(rw.torus("twine", 0.031, 0.0058, 16, 5, (x, 0, 0), (0, 90, 0), ml.mat("TwineBrown")))
parts.append(rw.ico("knot", 0.011, 2, (0.0, 0.0, 0.036), (0, 0, 0), (1.2, 1.0, 0.8), ml.mat("TwineBrown"), None, 70))
for sx in (-1, 1):
    parts.append(pl.sausage("twine_end", [V((0.004 * sx, 0, 0.038)), V((0.018 * sx, -0.012, 0.046)),
                                          V((0.03 * sx, -0.02, 0.04))], 0.005, 6, 3, ml.mat("TwineBrown"),
                            (True, True), 1, True, 60))

bundle = rw.join(parts, "ReedFiber")
pl.xform(bundle, ml.Matrix.Rotation(math.radians(-8), 4, 'Y'))   # tip it a little so it isn't ruler-straight
il.finish_item(ASSET, (0.32, 0.14, 0.18))
