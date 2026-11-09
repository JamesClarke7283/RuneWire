"""prop_tank: riveted copper industrial tank on steel legs, with pipes, valves, a pressure gauge and a glowing
sight glass (diameter 4 x 6 m). Origin at the ground centre, gauge facing -Y."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_tank"
rw.reset()
P = []
R = 1.86
prof = [(0.0, 1.22), (0.65, 1.28), (1.2, 1.42), (1.58, 1.6), (1.8, 1.82), (R, 2.05), (R, 4.95), (1.8, 5.18), (1.58, 5.4),
        (1.2, 5.58), (0.66, 5.7), (0.45, 5.72)]
body = E.lathe("tank", prof, 22, m="M_Copper", smooth=40)
P.append(body)
for z in (2.15, 3.55, 4.85):
    P.append(E.lathe("band", [(R - 0.01, z - 0.09), (R + 0.06, z - 0.07), (R + 0.06, z + 0.07), (R - 0.01, z + 0.09)], 22,
                     m="M_Brass", cap_bottom=False, cap_top=False, smooth=40))
for z in (2.15, 4.85):
    P += E.rivet_ring((0, 0, z), R + 0.06, 11, 0.035, "M_Brass", lo=True, phase=0.1)
# legs with cross braces
LR = 1.52
legs = []
for i in range(4):
    a = math.radians(45 + 90 * i)
    x, y = LR * math.cos(a), LR * math.sin(a)
    x2, y2 = 1.66 * math.cos(a), 1.66 * math.sin(a)
    P.append(E.beam("leg", (x, y, 0.0), (x2, y2, 2.2), 0.2, 0.2, "M_PaintedMetal__5f6b78", 0.03))
    P.append(E.cbox("foot", (0.44, 0.44, 0.07), (x, y, 0.035), (0, 0, 45 + 90 * i), "M_Steel", 0.02))
    legs.append(((x, y), (x2, y2)))
for i in range(4):
    (a0, a1), (b0, b1) = legs[i], legs[(i + 1) % 4]
    pa = (a0[0] * 0.98, a0[1] * 0.98, 0.3)
    pb = (b0[0] * 0.98 + (b1[0] - b0[0]) * 0.55, b0[1] * 0.98 + (b1[1] - b0[1]) * 0.55, 1.45)
    P.append(E.beam("brace", pa, pb, 0.07, 0.07, "M_Steel", 0.015))
    pa = (b0[0] * 0.98, b0[1] * 0.98, 0.3)
    pb = (a0[0] * 0.98 + (a1[0] - a0[0]) * 0.55, a0[1] * 0.98 + (a1[1] - a0[1]) * 0.55, 1.45)
    P.append(E.beam("brace", pa, pb, 0.07, 0.07, "M_Steel", 0.015))
# gauge on the front
P += E.gauge((0, -R - 0.09, 3.1), (0, -1, 0), 0.3, 40)
P.append(E.rbox("gaugemount", (0.18, 0.12, 0.25), (0, -R - 0.02, 3.1 - 0.3), m="M_Brass", r=0.02))
# glowing sight glass (front right)
a = math.radians(-58)
gx, gy = (R + 0.14) * math.cos(a), (R + 0.14) * math.sin(a)
P.append(E.rod("sightglass", (gx, gy, 2.35), (gx, gy, 4.6), 0.075, 8, "M_Glass"))
P.append(E.rod("sightfluid", (gx, gy, 2.4), (gx, gy, 3.9), 0.05, 8, "TealGlow"))
for z in (2.33, 4.62):
    P.append(E.rbox("sightcap", (0.2, 0.2, 0.1), (gx, gy, z), (0, 0, math.degrees(a)), m="M_Brass", r=0.02))
    P.append(E.rod("sightarm", (gx, gy, z), ((R - 0.05) * math.cos(a), (R - 0.05) * math.sin(a), z), 0.04, 6, "M_Brass"))
# hatch, handwheel and vent on top
P.append(E.lathe("hatch", [(0.42, 5.7), (0.42, 5.8), (0.36, 5.84), (0.0, 5.84)], 12, m="M_Brass", smooth=40))
P += E.valve_wheel((0, 0, 5.9), (0, 0, 1), 0.24, "PaintRed", 4, 0.08)
P.append(E.rod("vent", (0.95, 0.6, 5.3), (0.95, 0.6, 5.75), 0.07, 8, "M_Steel"))
P.append(E.lathe("ventcap", [(0.07, 5.72), (0.17, 5.77), (0.14, 5.82), (0.0, 5.84)], 8, m="M_Steel", smooth=30))
# outlet pipe: bottom dome -> down -> out to +X -> into the ground, with a valve
P += E.pipe("outlet", [(0, 0, 1.25), (0, 0, 0.62), (1.82, 0, 0.62), (1.82, 0, -0.02)], 0.12, "M_Steel", bend=0.3, res=2)
P.append(E.rod("valvebody", (0.95, 0, 0.62), (1.15, 0, 0.62), 0.19, 10, "M_Brass"))
P += E.valve_wheel((1.05, 0, 0.93), (0, 0, 1), 0.2, "PaintRed", 4, 0.12)
# inlet pipe on the -X side coming down to the ground
P += E.pipe("inlet", [(-R + 0.05, 0.35, 4.55), (-1.98, 0.35, 4.55), (-1.98, 0.35, -0.02)], 0.1, "M_Steel", bend=0.12, res=2)
P += E.valve_wheel((-1.98, 0.35 - 0.24, 2.6), (0, -1, 0), 0.16, "PaintRed", 4, 0.1)
P.append(E.rod("inletvalve", (-1.98, 0.35, 2.48), (-1.98, 0.35, 2.72), 0.15, 10, "M_Brass"))
# brass maker's plate
P.append(E.rbox("plate", (0.6, 0.06, 0.32), (-0.75, -R + 0.08, 2.6), (0, 0, -24), m="M_Brass", r=0.03))
E.join(P, "Tank")
E.col_cyl("Tank", R + 0.06, 4.7, (0, 0, 3.55), verts=16)
for (x, y), (x2, y2) in legs:
    E.col_box("Leg", (0.24, 0.24, 2.2), ((x + x2) / 2, (y + y2) / 2, 1.1))
E.col_box("Outlet", (0.3, 0.3, 0.8), (1.82, 0, 0.4))
E.col_box("Inlet", (0.26, 0.26, 4.6), (-1.98, 0.35, 2.3))
E.check(ASSET, (4.0, 4.0, 6.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
