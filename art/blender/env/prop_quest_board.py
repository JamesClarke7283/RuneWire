"""prop_quest_board: wooden notice board with a little tiled roof, pinned parchment notes and wanted posters
(2.5 x 0.6 x 2.6 m). The board faces -Y. Empty LightPoint at the little lantern. Origin at the ground centre."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_quest_board"
rw.reset()
rnd = random.Random(11)
P = []
PX = 1.08
for sx in (-1, 1):
    P.append(E.rbox("post", (0.16, 0.16, 2.28), (sx * PX, 0.0, 1.14), m="M_WoodDark", r=0.025))
    for sy in (-1, 1):
        P.append(E.beam("foot", (sx * PX, sy * 0.25, 0.0), (sx * PX, 0.0, 0.42), 0.08, 0.08, "M_WoodDark", 0.015, up=(1, 0, 0)))
# board: vertical planks inside a frame
BZ0, BZ1 = 0.82, 2.02
for i in range(8):
    x = -0.93 + i * (1.86 / 7)
    P.append(E.rbox("plank", (0.225, 0.06, BZ1 - BZ0), (x, 0.02, (BZ0 + BZ1) / 2), m="M_WoodPlanks", r=0.012))
for z in (BZ0, BZ1):
    P.append(E.rbox("frame", (2.18, 0.1, 0.1), (0, 0.0, z), m="M_WoodDark", r=0.02))
# little roof
P += E.gable_roof(-1.18, 1.18, -0.27, 0.27, 2.2, 2.52, t=0.08, sag=0.04, flare=1.1, nu=6, nv=3, tilt=0.03, ridge_r=0.06,
                  barge_r=0.045, barge_off=0.02)
P.append(E.rbox("roofbeam", (2.3, 0.1, 0.1), (0, 0.0, 2.2), m="M_WoodDark", r=0.02))
# notes: (x, z, w, h, rot, material, kind)
notes = [(-0.72, 1.62, 0.36, 0.46, 4, "Paper", "text"), (-0.28, 1.7, 0.3, 0.36, -6, "PaperOld", "text"),
         (0.15, 1.55, 0.42, 0.56, 2, "PaperOld", "wanted"), (0.66, 1.66, 0.4, 0.5, -3, "Paper", "wanted"),
         (-0.6, 1.08, 0.42, 0.3, -2, "PaperOld", "text"), (-0.12, 1.12, 0.32, 0.4, 7, "Paper", "text"),
         (0.38, 1.05, 0.28, 0.3, -8, "PaperBlue", "text"), (0.78, 1.12, 0.3, 0.38, 5, "PaperOld", "map")]
for (x, z, w, h, rot, m, kind) in notes:
    n = [rw.box("note", (w, 0.012, h), (0, -0.006, 0), mat=E.M(m))]
    if kind == "text":
        for k in range(4):
            lw = w * (0.75 if k < 3 else 0.45)
            n.append(rw.box("ink", (lw, 0.006, 0.022), (-(w * 0.75 - lw) / 2, -0.014, h * 0.3 - k * h * 0.17), mat=E.M("Ink")))
    elif kind == "wanted":
        n.append(rw.box("ink", (w * 0.8, 0.006, 0.05), (0, -0.014, h * 0.38), mat=E.M("Ink")))
        n.append(rw.cylinder("face", w * 0.16, 0.008, 12, (0, -0.015, h * 0.08), (90, 0, 0), E.M("Ink")))
        n.append(rw.cylinder("shoulders", w * 0.26, 0.008, 12, (0, -0.015, -h * 0.17), (90, 0, 0), E.M("Ink")))
        n.append(rw.box("cover", (w * 0.7, 0.01, h * 0.12), (0, -0.016, -h * 0.3), mat=E.M(m)))
        n.append(rw.box("bounty", (w * 0.5, 0.006, 0.035), (0, -0.022, -h * 0.33), mat=E.M("PinRed")))
    else:
        n.append(E.tube("route", [(-w * 0.3, -0.014, -h * 0.3), (-w * 0.05, -0.014, 0.0), (w * 0.2, -0.014, -h * 0.1), (w * 0.3, -0.014, h * 0.3)],
                        0.01, "PinRed", 0, True, 2))
        n.append(rw.box("x1", (0.07, 0.006, 0.015), (w * 0.3, -0.016, h * 0.3), (0, 45, 0), mat=E.M("Ink")))
        n.append(rw.box("x2", (0.07, 0.006, 0.015), (w * 0.3, -0.016, h * 0.3), (0, -45, 0), mat=E.M("Ink")))
    n.append(E.ball("pin", 0.022, (0, -0.02, h * 0.42), "PinRed", 6, 4))
    E.place(n, (x, -0.01, z), (0, rot, 0))
    P += n
# little lantern hanging from the roof edge
lamp, lc = E.lantern((-1.0, -0.2, 2.16), "hang", scale=0.6)
P += lamp
P.append(E.rod("lhook", (-1.0, -0.2, 2.17), (-1.0, -0.04, 2.17), 0.012, 5, "Iron"))
E.join(P, "QuestBoard")
rw.empty("LightPoint", lc)
E.col_box("Board", (2.34, 0.2, 2.2), (0, 0.0, 1.1))
E.col_box("Roof", (2.36, 0.56, 0.3), (0, 0.0, 2.36))
E.check(ASSET, (2.5, 0.6, 2.6), 4000)
rw.finish(ASSET, "env", previews=E.previews())
