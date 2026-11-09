"""prop_scrap_pile: heap of rusty scrap - gears, plates, bolts, pipes, a tyre, a spring and a broken Cogwork drone
shell (4 x 4 x 1.8 m). Origin at the ground centre."""
import math
import os
import random
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_scrap_pile"
rw.reset()
rnd = random.Random(5)
P = []


def cut_below(o, z=0.0):
    rw.apply_modifiers(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(o.data)
    bm.free()
    return o


# mound: low lumps, cut flat at the ground
for (size, loc, rot, m, sub, seed) in (((3.6, 3.85, 1.5), (0.0, 0.05, 0.0), 10, "M_Rust", 3, 3),
                                       ((1.7, 1.5, 1.0), (-1.05, 1.0, 0.0), 30, "M_DarkMetal", 2, 5),
                                       ((1.6, 1.6, 0.9), (1.2, -0.85, 0.0), -20, "M_Rust", 2, 7)):
    b = rw.blob("mound", size, loc, (0, 0, rot), E.mat(m), sub, 0.16, 0.7, seed)
    cut_below(b)
    P.append(b)
# gears (big rusty one standing up, others scattered)
P.append(E.gear("biggear", 0.72, 12, 0.16, 0.18, 0.2, (0.3, 0.3, 1.0), (0.25, -0.4, 0.9), "M_Rust", 0.0))
P.append(E.rod("axle", (0.18, 0.5, 0.82), (0.45, 0.05, 1.18), 0.07, 8, "M_Steel"))
P.append(E.gear("gear", 0.46, 10, 0.11, 0.13, 0.12, (-0.75, -0.45, 0.78), (0.35, -0.25, 0.9), "M_Brass", 0.0))
P.append(E.gear("gear", 0.34, 9, 0.09, 0.1, 0.0, (1.0, 0.55, 0.66), (-0.6, 0.35, 0.7), "M_Copper", 0.0))
P.append(E.gear("gear", 0.27, 8, 0.07, 0.09, 0.08, (-0.15, -1.3, 0.34), (0.1, -0.6, 0.8), "M_Steel", 0.0))
# bent plates
for i, (loc, rot, size, m) in enumerate((((-0.15, -0.6, 0.86), (25, 10, 30), (1.0, 0.65, 0.05), "M_PaintedMetal__e8762c"),
                                         ((0.95, -0.1, 0.66), (-22, 35, -10), (0.8, 0.6, 0.05), "M_Steel"),
                                         ((-1.0, 0.4, 0.78), (40, -15, 70), (0.85, 0.55, 0.05), "M_PaintedMetal__5f8f6a"),
                                         ((0.35, 1.05, 0.58), (-35, 5, 20), (0.9, 0.5, 0.05), "M_Rust"),
                                         ((1.45, 0.75, 0.35), (10, -50, 60), (0.7, 0.5, 0.05), "M_PaintedMetal__e8762c"))):
    P.append(E.cbox("plate", size, loc, rot, m, 0.015))
    P.append(E.rivet("rivet", (loc[0], loc[1], loc[2] + 0.045), 0.035, "M_Brass", lo=True))
# more scrap on the slopes: I-beam stubs, extra plates and gears
for (p0, p1) in (((1.1, 1.1, 0.12), (1.75, 0.55, 0.5)), ((-1.75, -0.2, 0.1), (-1.05, -0.05, 0.62))):
    P.append(E.beam("ibeam", p0, p1, 0.22, 0.24, "M_PaintedMetal__e8762c", 0.02))
    P.append(E.beam("ibeamweb", p0, p1, 0.07, 0.3, "M_DarkMetal", 0.0))
for i, (loc, rot, size, m) in enumerate((((-1.55, 0.6, 0.25), (-30, 20, 15), (0.8, 0.55, 0.05), "M_Steel"),
                                         ((0.75, -1.45, 0.22), (35, 0, -15), (0.85, 0.5, 0.05), "M_PaintedMetal__5f8f6a"),
                                         ((-0.2, 1.65, 0.18), (-40, 0, 5), (0.7, 0.45, 0.05), "M_PaintedMetal__e8762c"))):
    P.append(E.cbox("plate", size, loc, rot, m, 0.015))
P.append(E.gear("gear", 0.36, 9, 0.09, 0.11, 0.1, (1.65, 0.0, 0.3), (0.9, 0.0, 0.5), "M_Brass", 0.0))
P.append(E.gear("gear", 0.3, 8, 0.08, 0.1, 0.0, (-0.6, 1.55, 0.35), (0.0, 0.8, 0.6), "M_Rust", 0.0))
# pipes sticking out
P.append(E.tube("scrappipe", [(-0.3, 0.6, 0.6), (-0.1, 0.75, 1.2), (0.05, 0.9, 1.72)], 0.09, "M_Copper", 1, True, 3))
P.append(E.rod("pipeflange", (0.04, 0.88, 1.66), (0.06, 0.92, 1.76), 0.14, 10, "M_Brass"))
P.append(E.tube("scrappipe2", [(0.9, 0.2, 0.3), (1.35, 0.3, 0.6), (1.7, 0.6, 0.45)], 0.07, "M_Steel", 1, True, 3))
# bolts and nuts
for i in range(6):
    a = rnd.uniform(0, 2 * math.pi)
    rr = rnd.uniform(0.6, 1.4)
    x, y = rr * math.cos(a), rr * math.sin(a)
    z = max(0.08, 0.85 * (1 - (rr / 1.75) ** 2) + 0.04)
    P.append(rw.cylinder("nut", 0.09, 0.07, 6, (x, y, z), (rnd.uniform(0, 70), rnd.uniform(0, 70), 0), E.mat("M_Steel")))
    P.append(E.rod("bolt", (x, y, z), (x + 0.17, y + 0.05, z + 0.06), 0.035, 6, "M_Steel"))
# spring
coil = []
for k in range(19):
    t = k / 18
    a = t * 5 * 2 * math.pi
    coil.append((1.3 + 0.14 * math.cos(a), 1.0 + 0.14 * math.sin(a), 0.15 + 0.5 * t))
P.append(E.tube("spring", coil, 0.03, "M_Copper", 0, False))
# tyre leaning on the pile
P.append(rw.torus("tyre", 0.36, 0.13, 14, 6, (1.55, -1.35, 0.45), (70, 0, 35), E.mat("M_Rubber")))
P.append(rw.cylinder("tyrehub", 0.2, 0.12, 10, (1.55, -1.35, 0.45), (70, 0, 35), E.mat("M_Steel")))
# broken drone shell (Cogwork Legion scout) at the front-left
d = []
d.append(E.lathe("droneshell", [(0.0, 0.55), (0.3, 0.5), (0.48, 0.34), (0.56, 0.14), (0.56, 0.0), (0.46, 0.0)], 14,
                 m="M_DarkMetal", cap_bottom=False, smooth=50))
d.append(E.lathe("droneband", [(0.56, 0.05), (0.6, 0.08), (0.6, 0.2), (0.56, 0.23)], 14, m="HazardYellow", cap_bottom=False, cap_top=False))
for k in range(4):
    a = math.pi / 2 + k * math.pi / 2 + 0.4
    d.append(rw.box("droneband", (0.09, 0.06, 0.16), (0.6 * math.cos(a), 0.6 * math.sin(a), 0.14), (0, 0, math.degrees(a)), E.M("HazardBlack")))
d.append(E.disc("droneeye", 0.2, 0.08, (0.0, -0.47, 0.32), (0, -1, 0.4), 14, "GlassDark"))
d.append(E.ring("droneeyerim", 0.22, 0.045, (0.0, -0.5, 0.32), (0, -1, 0.4), "M_Brass", 14, 4))
d.append(E.beam("crack", (-0.14, -0.53, 0.4), (0.12, -0.52, 0.25), 0.025, 0.03, "M_TechGlow", 0.0, up=(0, -1, 0)))
d.append(E.beam("dronearm", (0.4, 0.22, 0.22), (0.95, 0.6, 0.48), 0.1, 0.08, "M_DarkMetal", 0.015))
d.append(rw.cylinder("dronerotor", 0.32, 0.03, 10, (0.95, 0.6, 0.53), (12, 18, 0), E.mat("M_Steel")))
E.place(d, (-1.25, -1.3, 0.0), (0, 0, 0))
E.place(d, (0, 0, 0), (-18, 12, 25), pivot=(-1.25, -1.3, 0.0))
P += d
# a rusty barrel lying at the back
P += E.place(E.barrel(0.28, 0.75, (0, 0, 0), 0, seg=12, m="M_Rust", hoop="M_DarkMetal", lying=True), (-1.25, 1.3, 0.0), (0, 0, 35))
pile = E.join(P, "ScrapPile")
cut_below(pile, 0.0)
# collision: convex heap + the big gear
pts = []
for k in range(12):
    a = 2 * math.pi * k / 12
    pts.append((1.9 * math.cos(a), 1.85 * math.sin(a), 0.0))
    pts.append((0.8 * math.cos(a), 0.75 * math.sin(a), 0.8))
E.col_hull("Heap", pts)
E.col_box("BigGear", (1.4, 0.4, 1.4), (0.3, 0.3, 1.0), (0, 0, 20))
E.check(ASSET, (4.0, 4.0, 1.8), 4000)
rw.finish(ASSET, "env", previews=E.previews())
