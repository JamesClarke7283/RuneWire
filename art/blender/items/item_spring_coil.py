"""item_spring_coil: a fat cartoon steel coil spring, about 0.18 x 0.18 x 0.25 m, standing upright.

A thick steel wire (M_Steel) wound 6.5 turns with a slight cartoon barrel bulge: the end turns are closed (each
touches its neighbour) and ground flat top and bottom so the spring stands on flat ends, and the middle turns
open up into wide springy gaps. One mesh object "SpringCoil", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_spring_coil"
rw.reset()

H = 0.25          # height between the ground-flat ends
RW = 0.0135       # wire radius
RC = 0.072        # coil radius (to the wire centre)
N = 6.5           # total turns
PC = 2.1 * RW     # closed pitch (end turns touch)
STEPS = 18        # path points per turn


def ss(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def w(t):
    """0 on the closed end turns, 1 on the open middle ones."""
    return ss((t - 0.75) / 0.5) * ss((N - 0.75 - t) / 0.5)


# solve for the open pitch so that the path spans H (the grind planes sit on the path at both ends)
M = int(N * 400)
iw = sum(w((i + 0.5) * N / M) for i in range(M)) * N / M
PA = PC + (H - PC * N) / iw

pts = []
n = int(N * STEPS)
z = 0.0
for i in range(n + 1):
    t = N * i / n
    if i:
        tm = N * (i - 0.5) / n
        z += (PC + (PA - PC) * w(tm)) * N / n
    a = 2 * math.pi * t
    r = RC * (1 + 0.06 * math.sin(math.pi * t / N))            # cartoon barrel bulge
    pts.append(V((r * math.cos(a), r * math.sin(a), z)))
spring = pl.sausage("SpringCoil", pts, RW, 9, 1, ml.mat("M_Steel"), (True, True), 2, True, 70)

# grind the ends flat: nothing goes below z = 0 or above z = H
for vx in spring.data.vertices:
    vx.co.z = min(max(vx.co.z, 0.0), z)
spring.data.update()
rw.smooth(spring, 50)
print("RWREPORT   spring open pitch %.4f m, gap %.4f m, path height %.4f m" % (PA, PA - 2 * RW, z))

ml.preview_metals()
il.finish_item(ASSET, (0.18, 0.18, 0.25))
