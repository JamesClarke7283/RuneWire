"""prop_signpost: wooden signpost with three painted plank arrows (1 x 1 x 3 m). Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_signpost"
rw.reset()
P = []
P.append(E.rbox("post", (0.16, 0.16, 2.78), (0, 0, 1.39), m="M_WoodDark", r=0.03))
P.append(E.rbox("collar", (0.22, 0.22, 0.06), (0, 0, 2.76), m="M_Brass", r=0.015))
P.append(rw.cone("cap", 0.18, 0.02, 0.16, 4, (0, 0, 2.87), (0, 0, 45), E.mat("M_RoofTiles")))
P.append(E.ball("finial", 0.05, (0, 0, 2.97), "M_Brass", 8, 6))
arrows = ((2.42, 4, "PaintTeal"), (2.05, 176, "PaintRed"), (1.68, 92, "PaintCream"))
for (z, ang, paint) in arrows:
    a = []
    body = [(-0.5, -0.1), (0.3, -0.1), (0.3, 0.1), (-0.5, 0.1), (-0.44, 0.0)]
    tip = [(0.3, -0.13), (0.49, 0.0), (0.3, 0.13)]
    a.append(E.upright_prism("arrow", body, 0.05, -0.105, 0, 0, "M_WoodPlanks", bevel=0.01))
    a.append(E.upright_prism("tip", tip, 0.056, -0.105, 0, 0, paint, bevel=0.01))
    for zz in (-0.035, 0.035):
        a.append(rw.box("ink", (0.42, 0.012, 0.022), (-0.06, -0.133, zz), mat=E.M("Ink")))
        a.append(rw.box("ink", (0.42, 0.012, 0.022), (-0.06, -0.077, zz), mat=E.M("Ink")))
    a.append(E.rivet("nail", (0.0, -0.135, 0.0), 0.016, "Iron"))
    E.place(a, (0, 0, z), (0, 0, ang))
    P += a
import math  # noqa: E402
for i in range(7):
    a = 2 * math.pi * i / 7 + 0.4
    r = 0.13 + 0.04 * ((i * 37) % 3) / 2
    d = 0.2 + 0.03 * (i % 2)
    P.append(E.pebble("rock", r, (d * math.cos(a), d * math.sin(a), r * 0.66), seed=i + 3, squash=0.75))
P.append(E.pebble("rock", 0.12, (0.05, -0.12, 0.25), seed=21, squash=0.7))
P += E.moss((0.0, 0.0, 0.3), 0.22, seed=2, n=3)
P += E.flower_cluster((0.27, -0.2, 0.05), 0.16, 4, seed=7, colors=("FlowerYellow", "FlowerWhite", "FlowerPink"))
E.join(P, "Signpost")
E.col_box("Post", (0.2, 0.2, 3.0), (0, 0, 1.5))
E.check(ASSET, (1.0, 1.0, 3.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
