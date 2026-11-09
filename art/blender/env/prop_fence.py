"""prop_fence: wooden picket fence segment (2 x 0.2 x 1.1 m). Posts at both ends (outer faces at x = +-1.0) so
segments placed end to end along X butt cleanly. Origin at the ground centre, front faces -Y."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_fence"
rw.reset()
rnd = random.Random(4)
P = []
for sx in (-1, 1):
    x = sx * 0.92
    P.append(E.rbox("post", (0.16, 0.16, 0.98), (x, 0, 0.49), m="M_WoodDark", r=0.025))
    P.append(E.rbox("postcap", (0.2, 0.2, 0.05), (x, 0, 1.0), m="M_WoodDark", r=0.015))
    P.append(rw.cone("cap", 0.12, 0.0, 0.1, 4, (x, 0, 1.075), (0, 0, 45), E.mat("M_WoodDark")))
for z in (0.3, 0.74):
    P.append(E.rbox("rail", (1.72, 0.05, 0.08), (0, 0.035, z), m="M_WoodDark", r=0.015))
n = 7
for i in range(n):
    x = -0.72 + 1.44 * i / (n - 1)
    h = 0.93 + rnd.uniform(-0.04, 0.03)
    w = 0.12
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - 0.08), (0.0, h), (-w / 2, h - 0.08)]
    pk = E.upright_prism("picket", pts, 0.035, -0.02, 0, 0.04, "M_WoodPlanks", bevel=0.008)
    E.place([pk], (x, 0, 0), (0, 0, 0))
    E.place([pk], (0, 0, 0), (0, rnd.uniform(-3, 3), 0), pivot=(x, -0.02, 0.0))
    P.append(pk)
    for z in (0.3, 0.74):
        P.append(E.rivet("nail", (x, -0.04, z), 0.012, "Iron"))
E.join(P, "Fence")
E.col_box("Fence", (2.0, 0.2, 1.1), (0, 0, 0.55))
E.check(ASSET, (2.0, 0.2, 1.1), 4000)
rw.finish(ASSET, "env", previews=E.previews())
