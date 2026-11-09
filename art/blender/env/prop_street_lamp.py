"""prop_street_lamp: iron lamp post with a brass lantern holding a warm glowing crystal (0.6 x 0.6 x 4 m).
Empty LightPoint at the crystal. Origin at the ground centre."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_street_lamp"
rw.reset()
P = []

# stepped octagonal base (flat-to-flat 0.6 m)
R = 0.3 / math.cos(math.radians(22.5))
P.append(E.lathe("base", [(R, 0.0), (R, 0.12), (R * 0.86, 0.15), (R * 0.8, 0.26), (R * 0.6, 0.29), (R * 0.52, 0.4),
                          (R * 0.36, 0.44), (0.0, 0.44)], 8, m="M_DarkMetal", smooth=0, rot=(0, 0, 22.5)))
# tapered post with mouldings and a brass knot
prof = [(0.13, 0.43), (0.11, 0.5), (0.1, 0.7), (0.09, 1.35), (0.12, 1.42), (0.13, 1.5), (0.12, 1.58), (0.088, 1.65),
        (0.078, 2.8), (0.11, 2.86), (0.11, 2.95), (0.08, 3.0), (0.08, 3.12), (0.0, 3.12)]
P.append(E.lathe("post", prof, 12, m="M_DarkMetal", smooth=50))
P.append(E.ring("band", 0.128, 0.026, (0, 0, 1.5), (0, 0, 1), "M_Brass", 14, 5))
P.append(E.ring("band", 0.11, 0.02, (0, 0, 2.905), (0, 0, 1), "M_Brass", 14, 5))
# scroll brackets under the lantern
for i in range(4):
    a = math.pi / 4 + i * math.pi / 2
    ca, sa = math.cos(a), math.sin(a)
    pts = [(0.07 * ca, 0.07 * sa, 2.88), (0.17 * ca, 0.17 * sa, 2.95), (0.23 * ca, 0.23 * sa, 3.08), (0.18 * ca, 0.18 * sa, 3.18),
           (0.13 * ca, 0.13 * sa, 3.12)]
    P.append(E.tube("scroll", pts, 0.024, "M_Brass", 1, smooth=True, ures=3))
    P.append(E.ball("scrollend", 0.03, (0.13 * ca, 0.13 * sa, 3.12), "M_Brass", 8, 5))
# lantern (hexagonal)
P.append(E.lathe("lbase", [(0.09, 3.1), (0.23, 3.18), (0.23, 3.25), (0.0, 3.25)], 6, m="M_Brass", smooth=0))
P.append(E.lathe("glass", [(0.19, 3.25), (0.21, 3.47), (0.19, 3.7), (0.0, 3.7)], 6, m="M_Glass", smooth=0, cap_bottom=False))
for i in range(6):
    a = 2 * math.pi * i / 6
    p0 = (0.2 * math.cos(a), 0.2 * math.sin(a), 3.25)
    pm = (0.222 * math.cos(a), 0.222 * math.sin(a), 3.47)
    p1 = (0.2 * math.cos(a), 0.2 * math.sin(a), 3.7)
    P.append(E.tube("lbar", [p0, pm, p1], 0.022, "M_Brass", 1, smooth=False))
P.append(E.ring("lband", 0.218, 0.02, (0, 0, 3.47), (0, 0, 1), "M_Brass", 12, 4))
crystal = E.bipyramid("crystal", 0.11, 0.17, 0.14, 6, (0, 0, 3.46), "LampGlow", mid=0.08)
P.append(crystal)
P.append(E.ball("glowcore", 0.07, (0, 0, 3.46), "LampGlow", 8, 6))
P.append(E.lathe("lroof", [(0.27, 3.68), (0.27, 3.73), (0.16, 3.82), (0.06, 3.9), (0.035, 3.92), (0.0, 3.92)], 6, m="M_Brass", smooth=0))
P.append(E.ball("finial", 0.045, (0, 0, 3.955), "M_Brass", 8, 6))
E.join(P, "StreetLamp")
rw.empty("LightPoint", (0, 0, 3.46))
E.col_cyl("Base", 0.3, 0.44, (0, 0, 0.22), verts=8)
E.col_cyl("Post", 0.13, 3.0, (0, 0, 1.8), verts=8)
E.col_cyl("Lantern", 0.25, 0.85, (0, 0, 3.55), verts=8)
E.check(ASSET, (0.6, 0.6, 4.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
