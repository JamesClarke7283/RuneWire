"""item_spun_cloth: a folded bolt of cream cloth tied with a blue ribbon, about 0.3 x 0.22 x 0.21 m.

Three plump folded layers of cream linen (M_Fabric tinted cream) stacked a little askew, pinched in where a satin
blue ribbon (flat) is tied tight round the middle; the ribbon finishes in a big bow on top with two tails trailing
down over the front edge. One mesh object "SpunCloth", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_spun_cloth"
rw.reset()

CLOTH = ml.tinted("M_Fabric", "f8e2ae")
RIB = ml.mat("RibbonBlue")
parts = []

# three folded layers, slightly askew, pinched in round the middle where the ribbon is tied
LAYERS = [((0.0, 0.0), 0.0, (0.3, 0.21, 0.06)), ((0.006, -0.004), 3.0, (0.29, 0.205, 0.058)),
          ((-0.004, 0.003), -2.5, (0.28, 0.2, 0.056))]
z = 0.0
for (off, rz, size) in LAYERS:
    o = pl.superellipsoid("layer", size, (0, 0, 0), 0.22, 0.42, 20, 10, CLOTH, 60)
    pl.xform(o, ml.Matrix.Translation(V((off[0], off[1], z + size[2] / 2))) @
             ml.Matrix.Rotation(math.radians(rz), 4, 'Z'))
    parts.append(o)
    z += size[2] * 0.88
TOP = z + LAYERS[-1][2][2] * 0.12
ZC = TOP / 2
for o in parts:
    for vx in o.data.vertices:
        f = math.exp(-(vx.co.x / 0.045) ** 2) * 0.07
        vx.co.y *= 1 - f
        vx.co.z = ZC + (vx.co.z - ZC) * (1 - f)
    o.data.update()

# ribbon loop round the middle (x = 0): a flat band on a rounded rectangle in the YZ plane, seam under the bow
RW_, RT = 0.021, 0.16            # half-width (along X) and thickness factor of the ribbon
HW = 0.21 / 2 * (1 - 0.07) + 0.004
Z0, Z1 = ZC - (ZC - 0.0) * (1 - 0.07) - 0.004, ZC + (TOP - ZC) * (1 - 0.07) + 0.004
R = 0.028
loop = [V((0.0, 0.0, Z1))]
for (cy, cz, a0) in ((-HW + R, Z1 - R, 90), (-HW + R, Z0 + R, 180), (HW - R, Z0 + R, 270), (HW - R, Z1 - R, 0)):
    for i in range(5):
        a = math.radians(a0 + 90 * i / 4)
        loop.append(V((0.0, cy + R * math.cos(a), cz + R * math.sin(a))))
loop.append(V((0.0, 0.0, Z1)))
parts.append(pl.sausage("ribbon", loop, RW_, 6, 1, RIB, (False, False), 1, False, 50, (1.0, RT), (1, 0, 0)))

# bow on top: a knot, two loops and two tails
K = V((0.0, -0.004, Z1 + 0.006))
parts.append(pl.superellipsoid("knot", (0.036, 0.042, 0.03), K, 0.5, 0.5, 12, 6, RIB, 60))
for sx in (-1, 1):
    bow = [K + V((sx * x, y, zz)) for (x, y, zz) in ((0.0, 0.0, 0.0), (0.035, -0.006, 0.03), (0.075, -0.01, 0.042),
                                                    (0.1, -0.012, 0.022), (0.092, -0.01, -0.002),
                                                    (0.055, -0.006, -0.006), (0.012, 0.0, 0.0))]
    parts.append(pl.sausage("bow", bow, 0.019, 6, 3, RIB, (False, False), 1, True, 60, (1.0, RT), (0, 1, 0)))
    tail = [K + V((sx * 0.014, -0.01, -0.004)), V((sx * 0.045, -0.07, Z1 + 0.004)),
            V((sx * 0.075, -HW + 0.008, Z1 - 0.006)), V((sx * 0.092, -HW - 0.003, Z1 - 0.04)),
            V((sx * 0.1, -HW - 0.005, Z1 - 0.068))]
    parts.append(pl.sausage("tail", tail, 0.017, 6, 3, ml.mat("RibbonBlueDark"), (False, False), 1, True, 60, (1.0, RT),
                            (1, 0, 0)))

cloth = rw.join(parts, "SpunCloth")
il.finish_item(ASSET, (0.3, 0.22, 0.21))
