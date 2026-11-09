"""prop_pipes: cluster of copper and steel pipes on steel stands, with valves, handwheels and a gauge
(6 x 2 x 3 m). Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_pipes"
rw.reset()
P = []
YA, YB, YC = -0.6, 0.55, -0.02
# pipe A: big copper inverted U
P += E.pipe("pipeA", [(-2.78, YA, -0.02), (-2.78, YA, 0.92), (2.78, YA, 0.92), (2.78, YA, -0.02)], 0.17, "M_Copper", bend=0.35, res=2)
# pipe B: steel, rises and steps up
P += E.pipe("pipeB", [(-2.45, YB, -0.02), (-2.45, YB, 1.68), (1.55, YB, 1.68), (1.55, YB, 2.7), (2.82, YB, 2.7), (2.82, YB, 1.85)],
            0.13, "M_Steel", bend=0.3, res=2)
# pipe C: thin copper with a drop into a valve box
P += E.pipe("pipeC", [(-2.85, YC, -0.02), (-2.85, YC, 2.3), (0.65, YC, 2.3), (0.65, YC, 1.05)], 0.09, "M_Copper", bend=0.25, res=2)
# flanged couplings along the runs
for x in (-1.6, 0.3, 1.9):
    P.append(E.rod("coupling", (x - 0.05, YA, 0.92), (x + 0.05, YA, 0.92), 0.25, 12, "M_Brass"))
for x in (-0.9, 0.9):
    P.append(E.rod("coupling", (x - 0.04, YB, 1.68), (x + 0.04, YB, 1.68), 0.19, 12, "M_Brass"))
P.append(E.rod("coupling", (-1.0, YC, 2.3), (-0.92, YC, 2.3), 0.14, 10, "M_Brass"))
# valves
P.append(E.rod("valveA", (-1.25, YA, 0.92), (-0.95, YA, 0.92), 0.25, 12, "M_Brass"))
P += E.valve_wheel((-1.1, YA, 1.38), (0, 0, 1), 0.26, "PaintRed", 4, 0.28)
P.append(E.rod("valveB", (0.05, YB, 1.68), (0.35, YB, 1.68), 0.2, 12, "M_Brass"))
P += E.valve_wheel((0.2, YB - 0.38, 1.68), (0, -1, 0), 0.2, "PaintRed", 4, 0.22)
P.append(E.rod("lever", (0.65, YC - 0.1, 1.45), (0.65, YC - 0.36, 1.62), 0.025, 6, "Iron"))
P.append(E.ball("leverknob", 0.05, (0.65, YC - 0.36, 1.62), "PaintRed", 8, 5))
P.append(E.rod("leverbody", (0.65, YC, 1.36), (0.65, YC, 1.54), 0.13, 10, "M_Brass"))
# gauge on B's riser
P += E.gauge((-2.45, YB - 0.2, 1.15), (0, -1, 0), 0.2, -30)
P.append(E.rod("gaugestem", (-2.45, YB - 0.1, 1.15), (-2.45, YB, 1.15), 0.03, 6, "M_Brass"))
# valve box where pipe C ends
P.append(E.cbox("valvebox", (0.62, 0.5, 1.0), (0.65, YC, 0.5), (0, 0, 0), "M_PaintedMetal__4f7f6a", 0.04))
P += E.rivet_line((0.38, YC - 0.255, 0.1), (0.38, YC - 0.255, 0.9), 4, 0.025, "M_Brass", None)
P += E.rivet_line((0.92, YC - 0.255, 0.1), (0.92, YC - 0.255, 0.9), 4, 0.025, "M_Brass", None)
P.append(E.rbox("hazard", (0.5, 0.02, 0.14), (0.65, YC - 0.26, 0.82), m="HazardYellow", r=0.0))
for k in range(4):
    P.append(rw.box("hzstripe", (0.05, 0.022, 0.17), (0.5 + k * 0.1, YC - 0.262, 0.82), (0, 40, 0), mat=E.M("HazardBlack")))
# steam whistle on top of B
P.append(E.rod("whistlestem", (2.2, YB, 2.83), (2.2, YB, 2.95), 0.04, 8, "M_Brass"))
P.append(E.lathe("whistle", [(0.07, 2.92), (0.08, 2.98), (0.05, 3.0), (0.0, 3.0)], 8, loc=(2.2, YB, 0), m="M_Brass", smooth=30))
# stands
for x in (-1.75, 1.15):
    for y in (-0.85, 0.85):
        P.append(E.cbox("standpost", (0.12, 0.12, 2.05), (x, y, 1.025), (0, 0, 0), "M_PaintedMetal__e8762c", 0.02))
        P.append(E.cbox("standfoot", (0.3, 0.22, 0.05), (x, y, 0.025), (0, 0, 0), "M_Steel", 0.015))
    for z in (0.72, 1.52, 2.1):
        P.append(E.cbox("standbeam", (0.12, 1.82, 0.1), (x, 0, z), (0, 0, 0), "M_PaintedMetal__e8762c", 0.02))
    # clamps over the pipes
    P.append(E.tube("clampA", [(x, YA - 0.19, 0.78), (x, YA - 0.19, 0.95), (x, YA, 1.11), (x, YA + 0.19, 0.95), (x, YA + 0.19, 0.78)],
                    0.025, "M_Steel", 0, False))
    P.append(E.tube("clampB", [(x, YB - 0.15, 1.57), (x, YB - 0.15, 1.7), (x, YB, 1.83), (x, YB + 0.15, 1.7), (x, YB + 0.15, 1.57)],
                    0.022, "M_Steel", 0, False))
E.join(P, "Pipes")
E.col_beam("PipeA", (-2.78, YA, 0.92), (2.78, YA, 0.92), 0.4, 0.4, extend=0.2)
for x in (-2.78, 2.78):
    E.col_box("PipeA", (0.4, 0.4, 0.95), (x, YA, 0.47))
E.col_beam("PipeB", (-2.45, YB, 1.68), (1.55, YB, 1.68), 0.3, 0.3, extend=0.15)
E.col_box("PipeB", (0.3, 0.3, 1.7), (-2.45, YB, 0.85))
E.col_box("PipeB", (1.6, 0.3, 1.3), (2.2, YB, 2.25))
E.col_beam("PipeC", (-2.85, YC, 2.3), (0.65, YC, 2.3), 0.22, 0.22, extend=0.1)
E.col_box("PipeC", (0.22, 0.22, 2.3), (-2.85, YC, 1.15))
E.col_box("ValveBox", (0.62, 0.5, 1.4), (0.65, YC, 0.7))
for x in (-1.75, 1.15):
    E.col_box("Stand", (0.16, 1.9, 2.1), (x, 0, 1.05))
E.check(ASSET, (6.0, 2.0, 3.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
