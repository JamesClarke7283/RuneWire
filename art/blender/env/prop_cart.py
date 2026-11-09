"""prop_cart: decorative two-wheeled wooden hand cart loaded with goods (3 x 1.6 x 1.6 m).
Long axis along X (shafts towards -X), wheels on the +-Y sides. Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_cart"
rw.reset()
P = []
BX0, BX1 = -0.62, 1.42       # bed extent along X
BZ = 0.78                    # bed top
WR = 0.58                    # wheel radius
AX = 0.28                    # axle x
# bed: planks along X on two long beams
for i in range(5):
    y = -0.48 + 0.24 * i
    P.append(E.rbox("bedplank", (BX1 - BX0, 0.22, 0.06), ((BX0 + BX1) / 2, y, BZ - 0.03), m="M_WoodPlanks", r=0.015))
for sy in (-1, 1):
    P.append(E.rbox("beam", (BX1 - BX0 + 0.1, 0.12, 0.14), ((BX0 + BX1) / 2, sy * 0.42, BZ - 0.13), m="M_WoodDark", r=0.025))
    # side rails with stakes
    P.append(E.rbox("siderail", (BX1 - BX0, 0.06, 0.1), ((BX0 + BX1) / 2, sy * 0.57, BZ + 0.3), m="M_WoodDark", r=0.02))
    P.append(E.rbox("siderail", (BX1 - BX0, 0.05, 0.08), ((BX0 + BX1) / 2, sy * 0.57, BZ + 0.12), m="M_WoodPlanks", r=0.015))
    for x in (BX0 + 0.05, (BX0 + BX1) / 2, BX1 - 0.05):
        P.append(E.rbox("stake", (0.07, 0.07, 0.42), (x, sy * 0.57, BZ + 0.16), m="M_WoodDark", r=0.015))
for x in (BX0 + 0.03, BX1 - 0.03):
    P.append(E.rbox("endrail", (0.06, 1.1, 0.1), (x, 0, BZ + 0.3), m="M_WoodDark", r=0.02))
# shafts toward -X with a rest stick
for sy in (-1, 1):
    P.append(E.beam("shaft", (BX0 + 0.5, sy * 0.4, BZ - 0.13), (-1.48, sy * 0.36, 0.5), 0.09, 0.09, "M_WoodDark", 0.02))
    P.append(E.ball("shaftend", 0.055, (-1.47, sy * 0.36, 0.5), "M_Brass", 8, 5))
P.append(E.rod("crossbar", (-1.25, -0.37, 0.56), (-1.25, 0.37, 0.56), 0.035, 8, "M_WoodDark"))
P.append(E.beam("reststick", (-1.0, 0.0, 0.0), (-1.02, 0.0, 0.66), 0.08, 0.08, "M_WoodDark", 0.015))
P.append(E.rod("restbar", (-1.02, -0.38, 0.62), (-1.02, 0.38, 0.62), 0.03, 8, "M_WoodDark"))
# axle + wheels
P.append(E.rod("axle", (AX, -0.72, WR), (AX, 0.72, WR), 0.05, 8, "Iron"))
for sy in (-1, 1):
    P += E.wheel(WR, 0.12, (AX, sy * 0.72, WR), (0, 1, 0), spokes=8, m="M_WoodDark", tyre="Iron", seg=16)
    P.append(E.beam("axlemount", (AX - 0.2, sy * 0.44, BZ - 0.18), (AX + 0.2, sy * 0.44, BZ - 0.18), 0.1, 0.12, "M_WoodDark", 0.02))
# cargo
P += E.crate((0.5, 0.5, 0.5), (1.05, -0.22, BZ), 6)
P += E.sack((1.05, -0.2, BZ + 0.5), 0.3, 0.16, 40, 0, seg=8)
P += E.crate((0.4, 0.4, 0.36), (1.08, 0.3, BZ), -12)
P += E.barrel(0.25, 0.78, (0.42, 0.25, BZ), 20, seg=12, m="M_WoodDark")
P += E.sack((0.0, -0.25, BZ), 0.55, 0.24, 20, 12)
P += E.sack((-0.3, 0.2, BZ), 0.5, 0.22, -30, -14)
for i, (x, y, r) in enumerate(((0.45, -0.3, 0.13), (0.6, -0.12, 0.11), (0.22, -0.05, 0.12))):
    P.append(E.ball("pumpkin", r, (x, y, BZ + r * 0.8), "Pumpkin", 8, 5, (1.0, 1.0, 0.8)))
    P.append(E.rod("stem", (x, y, BZ + r * 1.5), (x + 0.02, y, BZ + r * 1.75), 0.015, 5, "LeafDark"))
# canvas tarp over the back crates
tarp = E.sheet("tarp", lambda u, v: (0.82 + 0.58 * u, -0.5 + 1.0 * v, BZ + 0.5 + 0.06 * __import__("math").sin(v * 3.14159) - 0.25 * abs(2 * v - 1) ** 3), 4, 6,
               "M_Fabric__d8c9a0")
E.solidify(tarp, 0.02)
P.append(tarp)
E.join(P, "Cart")
E.col_box("Bed", (BX1 - BX0, 1.2, 0.95), ((BX0 + BX1) / 2, 0, BZ + 0.12), (0, 0, 0))
for sy in (-1, 1):
    E.col_cyl("Wheel", WR, 0.14, (AX, sy * 0.72, WR), (90, 0, 0), verts=12)
E.col_beam("Shafts", (BX0, 0, BZ - 0.15), (-1.48, 0, 0.5), 0.9, 0.12)
E.check(ASSET, (3.0, 1.6, 1.6), 4000)
rw.finish(ASSET, "env", previews=E.previews())
