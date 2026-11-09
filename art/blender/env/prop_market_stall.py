"""prop_market_stall: wooden market stall with a striped cloth awning and goods on the counter (3 x 2 x 3 m).
Counter faces -Y. Empty LightPoint at the hanging lantern. Origin at the ground centre."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_market_stall"
rw.reset()
rnd = random.Random(3)
P = []
HX = 1.38                 # post x
YF, YB = -0.53, 0.9       # front / back post y
CZ = 0.95                 # counter top
# posts
for sx in (-1, 1):
    P.append(E.rbox("post", (0.12, 0.12, 2.3), (sx * HX, YF, 1.15), m="M_WoodDark", r=0.02))
    P.append(E.rbox("post", (0.12, 0.12, 2.86), (sx * HX, YB, 1.43), m="M_WoodDark", r=0.02))
    P.append(E.beam("sidebeam", (sx * HX, YF, 2.22), (sx * HX, YB, 2.78), 0.1, 0.1, "M_WoodDark", 0.02))
P.append(E.rbox("frontbeam", (2 * HX + 0.1, 0.1, 0.12), (0, YF, 2.24), m="M_WoodDark", r=0.02))
P.append(E.rbox("backbeam", (2 * HX + 0.1, 0.1, 0.12), (0, YB, 2.8), m="M_WoodDark", r=0.02))
# counter: plank front, top board, shelf below
P.append(E.rbox("countertop", (2 * HX + 0.2, 0.72, 0.07), (0, YF + 0.22, CZ), m="M_WoodPlanks", r=0.02))
for i in range(5):
    x = -HX + 0.29 + i * (2 * HX - 0.58) / 4
    P.append(E.rbox("frontplank", ((2 * HX - 0.15) / 5 - 0.02, 0.05, CZ - 0.06), (x, YF - 0.09, (CZ - 0.06) / 2), m="M_WoodPlanks", r=0.012))
P.append(E.rbox("kick", (2 * HX, 0.06, 0.1), (0, YF - 0.12, 0.08), m="M_WoodDark", r=0.015))
P.append(E.rbox("rail", (2 * HX, 0.06, 0.08), (0, YF - 0.12, CZ - 0.12), m="M_WoodDark", r=0.015))
P.append(E.rbox("shelf", (2 * HX - 0.1, 0.6, 0.05), (0, YF + 0.22, 0.35), m="M_WoodPlanks", r=0.012))
# striped awning (sloping down to the front, scalloped valance)
SL = 12
cols = ("M_Fabric__d94a3a", "M_Fabric__f3e7cf")
ax0, ax1 = -HX - 0.12, HX + 0.12
for i in range(SL):
    u0, u1 = i / SL, (i + 1) / SL

    def Pf(u, v, s, u0=u0, u1=u1):
        x = E.lerp(ax0, ax1, E.lerp(u0, u1, u))
        y = E.lerp(YB + 0.08, YF - 0.3, v)
        z = E.lerp(2.9, 2.26, v) - 0.07 * math.sin(math.pi * v) + s * 0.03
        return (x, y, z)
    P.append(E.param_slab("awning", Pf, 1, 2, cols[i % 2]))
    # scallop flap
    xm = E.lerp(ax0, ax1, (u0 + u1) / 2)
    w = (ax1 - ax0) / SL
    flap = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, -0.2), (w * 0.3, -0.27), (0.0, -0.29), (-w * 0.3, -0.27), (-w / 2, -0.2)]
    f = E.upright_prism("flap", flap, 0.025, YF - 0.3, xm, 2.27, cols[i % 2])
    P.append(f)
# sign board on the awning front
P.append(E.rbox("sign", (0.9, 0.05, 0.32), (0, YF - 0.3, 2.68), (14, 0, 0), m="M_WoodPlanks", r=0.02))
P.append(E.ball("signapple", 0.09, (0, YF - 0.34, 2.68), "Apple", 8, 6))
P.append(E.rod("signleaf", (0.0, YF - 0.35, 2.76), (0.07, YF - 0.35, 2.81), 0.025, 5, "Leaf"))
# goods: baskets of fruit, bread, cheese, bottles
def basket(x, y, fruit, n, r_fruit):
    out = [E.lathe("basket", [(0.16, 0.0), (0.22, 0.12), (0.25, 0.13), (0.25, 0.16), (0.21, 0.16), (0.0, 0.14)], 10,
                   loc=(x, y, CZ + 0.035), m="Hay", smooth=40)]
    for k in range(n):
        a = 2 * math.pi * k / max(1, n - 1) + 0.4
        rr = 0.0 if k == n - 1 else 0.115
        out.append(E.ball("fruit", r_fruit, (x + rr * math.cos(a), y + rr * math.sin(a), CZ + 0.2 + (0.07 if k == n - 1 else 0)), fruit, 8, 6))
    return out


P += basket(-0.95, YF + 0.18, "Apple", 5, 0.075)
P += basket(-0.35, YF + 0.22, "Orange", 5, 0.075)
P += basket(0.95, YF + 0.2, "Cabbage", 4, 0.1)
for i in range(3):
    P.append(E.ball("bread", 0.08, (0.25 + i * 0.16, YF + 0.12 + 0.03 * i, CZ + 0.07), "Bread", 8, 5, (1.6, 0.9, 0.7)))
P.append(E.lathe("cheese", [(0.14, 0.0), (0.15, 0.04), (0.14, 0.09), (0.0, 0.09)], 12, loc=(0.42, YF + 0.42, CZ + 0.035), m="Cheese", smooth=40))
for i, c in enumerate(("BottleGreen", "BottleBlue", "BottleGreen")):
    x = 0.95 + 0.0 * i
    P.append(E.lathe("bottle", [(0.05, 0.0), (0.055, 0.14), (0.02, 0.2), (0.02, 0.25), (0.0, 0.25)], 6, loc=(-0.05 + 0.12 * i, YF + 0.48, CZ + 0.035), m=c, smooth=70))
# crates and a sack behind / under the counter
P += E.crate((0.5, 0.45, 0.45), (-0.8, YF + 0.32, 0.38), 4)
P += E.sack((0.75, YF + 0.3, 0.38), 0.5, 0.2, 15, 0)
# hanging lantern under the awning
lamp, lc = E.lantern((-HX + 0.25, YF - 0.0, 2.22), "hang", scale=0.8)
P += lamp
E.join(P, "MarketStall")
rw.empty("LightPoint", lc)
E.col_box("Counter", (2 * HX + 0.2, 0.75, CZ + 0.04), (0, YF + 0.2, (CZ + 0.04) / 2))
for sx in (-1, 1):
    E.col_box("Post", (0.14, 0.14, 2.3), (sx * HX, YF, 1.15))
    E.col_box("Post", (0.14, 0.14, 2.68), (sx * HX, YB, 1.34))
L = math.hypot(YB - YF + 0.38, 0.64)
E.col_box("Awning", (2 * HX + 0.24, L, 0.12), (0, (YB + YF) / 2 - 0.11, 2.55), (math.degrees(math.atan2(0.64, YB - YF + 0.38)), 0, 0))
E.check(ASSET, (3.0, 2.0, 3.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
