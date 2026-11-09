"""prop_well: stone well with a little tiled roof, a windlass, a rope and buckets (diameter 2 x 3 m).
Origin at the ground centre."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_well"
rw.reset()
P = []
RO, RI, H = 0.94, 0.66, 0.8
ring = E.lathe("wellring", [(RO - 0.04, 0.0), (RO, 0.08), (RO - 0.02, H - 0.12), (RO + 0.04, H - 0.1), (RO + 0.04, H),
                            (RI - 0.03, H), (RI - 0.03, H - 0.1), (RI, H - 0.12), (RI, 0.35)], 20, m="M_Stone", smooth=35)
P.append(ring)
rw.set_mat_where(ring, E.M("GlassDark"), lambda c, n: n.z > 0.9 and c.z < 0.4)
# chunky rim stones
for i in range(10):
    a = 2 * math.pi * i / 10 + 0.15
    rr = (RO + RI) / 2
    P.append(E.stone("rimstone", (0.36, 0.27, 0.13), (rr * math.cos(a), rr * math.sin(a), H + 0.04), (0, 0, math.degrees(a) + 90),
                     b=0.035, seed=i, jitter=3))
for i in range(6):
    a = 2 * math.pi * i / 6 + 0.5
    P.append(E.stone("wallstone", (0.32, 0.12, 0.2), ((RO - 0.01) * math.cos(a), (RO - 0.01) * math.sin(a), 0.25 + 0.2 * (i % 2)),
                     (0, 0, math.degrees(a) + 90), m="M_StoneRough", b=0.03, seed=i + 20, jitter=4))
# posts, windlass, crank
PX = 0.8
for sx in (-1, 1):
    P.append(E.rbox("post", (0.14, 0.16, 1.66), (sx * PX, 0, H + 0.73), m="M_WoodDark", r=0.025))
    P.append(E.beam("brace", (sx * PX, -0.02, 2.0), (sx * (PX - 0.3), -0.02, 2.28), 0.1, 0.08, "M_WoodDark", 0.015))
P.append(E.rod("windlass", (-PX, 0, 1.78), (PX, 0, 1.78), 0.1, 12, "M_WoodPlanks"))
for x in (-0.12, -0.04, 0.04, 0.12):
    P.append(E.ring("coil", 0.105, 0.022, (x, 0, 1.78), (1, 0, 0), "Rope", 12, 4))
P.append(E.rod("axle", (PX, 0, 1.78), (PX + 0.15, 0, 1.78), 0.03, 8, "Iron"))
P.append(E.rod("crank", (PX + 0.15, 0, 1.78), (PX + 0.15, -0.0, 1.5), 0.025, 8, "Iron"))
P.append(E.rod("handle", (PX + 0.13, 0, 1.5), (PX + 0.13, -0.16, 1.5), 0.03, 8, "M_WoodDark"))
# rope and hanging bucket
P.append(E.rod("rope", (0.0, -0.1, 1.72), (0.0, -0.1, 1.12), 0.018, 6, "Rope"))
bucket = E.lathe("bucket", [(0.13, 0.0), (0.16, 0.26), (0.17, 0.27), (0.15, 0.27), (0.13, 0.03)], 12, m="M_WoodPlanks", cap_top=False)
P.append(bucket)
E.place([bucket], (0.0, -0.1, 0.8))
for z in (0.86, 1.02):
    P.append(E.ring("bband", 0.148 + (z - 0.86) * 0.12, 0.012, (0.0, -0.1, z), (0, 0, 1), "Iron", 12, 4))
P.append(E.tube("bhandle", [(-0.16, -0.1, 1.06), (0.0, -0.1, 1.14), (0.16, -0.1, 1.06)], 0.012, "Iron", 1, True, 3))
# second bucket resting on the rim
b2 = E.lathe("bucket2", [(0.12, 0.0), (0.15, 0.24), (0.16, 0.25), (0.14, 0.25), (0.12, 0.03)], 12, m="M_WoodPlanks", cap_top=False)
P.append(b2)
E.place([b2], (-0.62, -0.55, H + 0.1))
P.append(E.ring("bband", 0.145, 0.012, (-0.62, -0.55, H + 0.2), (0, 0, 1), "Iron", 12, 4))
P.append(E.disc("water", 0.13, 0.01, (-0.62, -0.55, H + 0.3), (0, 0, 1), 12, "Water"))
# roof
P += E.gable_roof(-0.93, 0.93, -0.74, 0.74, 2.3, 2.93, t=0.09, sag=0.05, flare=1.15, nu=6, nv=3, tilt=0.04, ridge_r=0.07,
                  barge_r=0.05, barge_off=0.025)
E.join(P, "Well")
E.col_cyl("Ring", RO + 0.04, H, (0, 0, H / 2), verts=12)
for sx in (-1, 1):
    E.col_box("Post", (0.16, 0.18, 1.6), (sx * PX, 0, H + 0.8))
E.col_box("Roof", (1.9, 1.48, 0.4), (0, 0, 2.6))
E.check(ASSET, (2.0, 2.0, 3.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
