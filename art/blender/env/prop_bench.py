"""prop_bench: park bench with wooden slats on curly cast-iron side frames (2 x 0.6 x 0.9 m).
Seat faces -Y, backrest at +Y. Empties SitPoint_0 / SitPoint_1 on the seat. Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_bench"
rw.reset()
P = []
IRON = "M_DarkMetal"
for sx in (-1, 1):
    x = sx * 0.8
    # front leg (curving forward at the foot)
    P.append(E.tube("leg", [(x, -0.27, 0.0), (x, -0.22, 0.12), (x, -0.2, 0.3), (x, -0.22, 0.42)], 0.03, IRON, 1, True, 3))
    # back leg rising into the backrest support
    P.append(E.tube("back", [(x, 0.24, 0.0), (x, 0.19, 0.18), (x, 0.17, 0.42), (x, 0.22, 0.65), (x, 0.27, 0.88)], 0.03, IRON, 1, True, 3))
    # seat rail
    P.append(E.tube("rail", [(x, -0.25, 0.41), (x, 0.2, 0.41)], 0.026, IRON, 1, False))
    # arm rest with a scroll at the front
    P.append(E.tube("arm", [(x, 0.21, 0.64), (x, -0.05, 0.66), (x, -0.22, 0.64), (x, -0.28, 0.58), (x, -0.24, 0.53), (x, -0.19, 0.56)],
                    0.025, IRON, 1, True, 3))
    P.append(E.tube("armpost", [(x, -0.2, 0.42), (x, -0.21, 0.6)], 0.02, IRON, 1, False))
    P.append(E.ball("foot", 0.04, (x, -0.27, 0.02), "M_Brass", 8, 5))
    P.append(E.ball("foot", 0.04, (x, 0.24, 0.02), "M_Brass", 8, 5))
    P.append(E.ball("knob", 0.03, (x, -0.2, 0.56), "M_Brass", 8, 5))
for y in (-0.22, -0.11, 0.0, 0.11):
    P.append(E.rbox("slat", (2.0, 0.095, 0.045), (0, y, 0.45), m="M_WoodPlanks", r=0.018))
for i, z in enumerate((0.56, 0.69, 0.82)):
    y = 0.2 + 0.035 * i
    P.append(E.rbox("bslat", (2.0, 0.04, 0.1), (0, y, z), (-14, 0, 0), m="M_WoodPlanks", r=0.016))
for sx in (-1, 1):
    for y in (-0.22, -0.11, 0.0, 0.11):
        P.append(E.rivet("bolt", (sx * 0.8, y, 0.476), 0.014, "M_Brass"))
E.join(P, "Bench")
rw.empty("SitPoint_0", (-0.48, -0.06, 0.475))
rw.empty("SitPoint_1", (0.48, -0.06, 0.475))
E.col_box("Seat", (2.0, 0.52, 0.475), (0, -0.04, 0.2375))
E.col_box("Back", (2.0, 0.12, 0.44), (0, 0.24, 0.68), (-14, 0, 0))
E.check(ASSET, (2.0, 0.6, 0.9), 4000)
rw.finish(ASSET, "env", previews=E.previews())
