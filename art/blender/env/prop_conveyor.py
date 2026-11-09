"""prop_conveyor: conveyor belt section with rollers, side rails, a motor, a control box and crates on the belt
(8 x 1.5 x 1.2 m). Belt runs along X. Origin at the ground centre."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_conveyor"
rw.reset()
P = []
BZ = 0.62          # belt centre height
BR = 0.16          # belt end radius
BT = BZ + BR       # belt top 0.78
XE = 3.62          # end drum x
# belt (stadium loop, solid)
outline = []
for k in range(9):
    a = -math.pi / 2 + math.pi * k / 8
    outline.append((XE + BR * math.cos(a), BR * math.sin(a)))
for k in range(9):
    a = math.pi / 2 + math.pi * k / 8
    outline.append((-XE + BR * math.cos(a), BR * math.sin(a)))
P.append(E.upright_prism("belt", outline, 1.0, 0.0, 0, BZ, "M_Rubber"))
for i in range(16):
    x = -3.4 + i * 6.8 / 15
    P.append(rw.box("cleat", (0.05, 0.96, 0.03), (x, 0, BT + 0.012), mat=E.mat("M_Rubber")))
# end drums + side rails
for sx in (-1, 1):
    P.append(E.rod("drum", (sx * XE, -0.56, BZ), (sx * XE, 0.56, BZ), 0.12, 12, "M_Steel"))
for sy in (-1, 1):
    P.append(E.cbox("rail", (7.9, 0.08, 0.28), (0, sy * 0.56, BZ + 0.03), (0, 0, 0), "M_PaintedMetal__e8762c", 0.02))
    P.append(E.cbox("raillip", (7.9, 0.14, 0.04), (0, sy * 0.55, BT + 0.035), (0, 0, 0), "M_PaintedMetal__e8762c", 0.012))
    for sx in (-1, 1):
        P.append(E.disc("drumcap", 0.1, 0.04, (sx * XE, sy * 0.61, BZ), (0, sy, 0), 12, "M_Brass"))
        for k in range(3):
            P.append(rw.box("hz", (0.08, 0.02, 0.24), (sx * (3.45 - 0.16 * k), sy * 0.605, BZ + 0.03), (0, 35, 0),
                            mat=E.M("HazardBlack" if k % 2 else "HazardYellow")))
    for i in range(8):
        x = -2.8 + i * 0.8
        P.append(E.rivet("rollerbolt", (x, sy * 0.6, BZ - 0.03), 0.035, "M_Steel", lo=True))
# legs
for x in (-3.25, -1.1, 1.1, 3.25):
    for sy in (-1, 1):
        P.append(E.cbox("leg", (0.09, 0.09, BZ - 0.08), (x, sy * 0.5, (BZ - 0.08) / 2), (0, 0, 0), "M_Steel", 0.012))
        P.append(E.cbox("foot", (0.22, 0.16, 0.04), (x, sy * 0.5, 0.02), (0, 0, 0), "M_DarkMetal", 0.01))
    P.append(E.cbox("crossbar", (0.07, 1.0, 0.07), (x, 0, 0.22), (0, 0, 0), "M_Steel", 0.01))
# motor housing on the +Y side, +X end
mx = 3.0
P.append(E.cbox("motor", (0.75, 0.16, 0.5), (mx, 0.68, BZ - 0.12), (0, 0, 0), "M_PaintedMetal__4f6f8f", 0.03))
P.append(E.rod("motorcan", (mx - 0.32, 0.64, BZ - 0.1), (mx + 0.3, 0.64, BZ - 0.1), 0.12, 10, "M_DarkMetal"))
P.append(E.gear("drivegear", 0.17, 10, 0.04, 0.05, 0.0, (XE, 0.66, BZ), (0, 1, 0), "M_Brass", 0.006))
P.append(E.tube("drivebelt", [(XE, 0.66, BZ + 0.15), (mx + 0.1, 0.66, BZ + 0.0), (XE - 0.15, 0.66, BZ - 0.2)], 0.025, "M_Rubber", 0, True, 3))
for k in range(4):
    P.append(rw.box("vent", (0.4, 0.01, 0.03), (mx, 0.762, BZ - 0.22 + 0.06 * k), mat=E.M("IronDark")))
# control box on the -Y side, -X end
cx = -3.1
P.append(E.cbox("ctrlpost", (0.08, 0.08, 0.85), (cx, -0.66, 0.425), (0, 0, 0), "M_Steel", 0.01))
P.append(E.cbox("ctrlbox", (0.32, 0.14, 0.28), (cx, -0.66, 0.92), (0, 0, 0), "M_PaintedMetal__e8762c", 0.02))
P.append(E.disc("button", 0.05, 0.04, (cx - 0.06, -0.745, 0.95), (0, -1, 0), 10, "PaintRed"))
P.append(E.disc("button", 0.04, 0.04, (cx + 0.08, -0.745, 0.95), (0, -1, 0), 10, "PaintGreen"))
P.append(E.rod("ctrllever", (cx, -0.7, 1.05), (cx + 0.05, -0.72, 1.17), 0.015, 6, "Iron"))
P.append(E.ball("ctrlknob", 0.035, (cx + 0.05, -0.72, 1.17), "PaintRed", 8, 5))
# cargo on the belt
P += E.crate((0.48, 0.48, 0.42), (-1.85, -0.05, BT + 0.025), 6)
P += E.crate((0.4, 0.4, 0.38), (0.45, 0.1, BT + 0.025), -14)
P += E.sack((1.95, -0.05, BT + 0.025), 0.42, 0.2, 30, 0, seg=8)
ore = E.bipyramid("ore", 0.13, 0.22, 0.08, 5, (-0.75, 0.05, BT + 0.1), "M_Crystal", twist=10)
P.append(ore)
P.append(E.pebble("orerock", 0.17, (-0.75, 0.05, BT + 0.06), "M_StoneRough", seed=3, squash=0.6))
E.join(P, "Conveyor")
E.col_box("Belt", (7.9, 1.2, BT + 0.06), (0, 0, (BT + 0.06) / 2))
E.col_box("Crate", (0.46, 0.46, 0.44), (-1.85, -0.05, BT + 0.25), (0, 0, 6))
E.col_box("Crate", (0.4, 0.4, 0.38), (0.45, 0.1, BT + 0.22), (0, 0, -14))
E.col_box("Motor", (0.75, 0.18, 0.55), (mx, 0.67, BZ - 0.12))
E.col_box("Control", (0.34, 0.2, 1.06), (cx, -0.67, 0.53))
E.check(ASSET, (8.0, 1.5, 1.2), 4000)
rw.finish(ASSET, "env", previews=E.previews())
