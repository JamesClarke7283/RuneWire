"""prop_smokestack: brick and rusted-metal factory smokestack with steel bands, a caged ladder and a
soot-blackened crown (diameter 3 x 20 m). Empty Smoke at the top. Origin at the ground centre."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
V = E.V
ASSET = "prop_smokestack"
rw.reset()
P = []
# square brick base with a sloped cap
P.append(E.cbox("base", (2.96, 2.96, 2.4), (0, 0, 1.2), (0, 0, 0), "M_Stone", 0.06))
P.append(rw.cone("basecap", 1.48 * math.sqrt(2), 1.3 * math.sqrt(2), 0.45, 4, (0, 0, 2.62), (0, 0, 45), E.mat("M_Stone")))
P.append(E.cbox("baseband", (3.0, 3.0, 0.16), (0, 0, 2.38), (0, 0, 0), "M_StoneRough", 0.04))
# arched iron clean-out door + plaque
door = E.door(0.9, 1.5, arch=True, m="Iron", frame="M_StoneRough", planks=3, straps=False, knob=False, frame_w=0.16)
E.place(door, (0, -1.48, 0.0))
P += door
P.append(E.rbox("plaque", (0.7, 0.05, 0.3), (0, -1.5, 1.9), m="M_Brass", r=0.03))
# stack: brick lower section, corbel, rusted upper section, crown
prof_b = [(1.24, 2.7), (1.2, 4.0), (1.12, 9.8), (0.0, 9.8)]
P.append(E.lathe("brick", prof_b, 24, m="M_Stone", smooth=40, cap_bottom=False))
P.append(E.lathe("corbel", [(1.1, 9.7), (1.2, 9.85), (1.2, 10.15), (1.08, 10.3)], 24, m="M_StoneRough", cap_bottom=False, cap_top=False))
prof_m = [(1.06, 10.2), (1.02, 14.0), (0.94, 18.5), (0.0, 18.5)]
P.append(E.lathe("metal", prof_m, 20, m="M_Rust", smooth=40, cap_bottom=False))
for i, z in enumerate((11.4, 13.4, 15.4, 17.4)):
    r = 1.06 - (z - 10.2) * (0.12 / 8.3)
    P.append(E.lathe("band", [(r - 0.01, z - 0.12), (r + 0.06, z - 0.09), (r + 0.06, z + 0.09), (r - 0.01, z + 0.12)], 20,
                     m="M_DarkMetal", cap_bottom=False, cap_top=False, smooth=40))
    if i in (0, 2):
        P += E.rivet_ring((0, 0, z), r + 0.06, 12, 0.035, "M_Steel", lo=True)
crown = [(0.92, 18.4), (0.98, 18.8), (1.12, 19.3), (1.18, 19.55), (1.18, 19.75), (1.08, 19.82), (0.86, 19.82), (0.86, 19.5)]
c = E.lathe("crown", crown, 20, m="M_DarkMetal", smooth=40, cap_bottom=False, cap_top=True)
rw.set_mat_where(c, E.M("Soot"), lambda cc, n: cc.z > 19.2)
P.append(c)
P.append(E.lathe("soot", [(1.0, 19.0), (1.1, 19.6), (1.12, 19.7)], 20, m="Soot", cap_bottom=False, cap_top=False, smooth=40))
P.append(E.disc("flue", 0.86, 0.02, (0, 0, 19.45), (0, 0, 1), 20, "Soot"))
# caged ladder on the front-left
A = math.radians(-120)
d = V((math.cos(A), math.sin(A), 0))
side = V((-d.y, d.x, 0))


def surf_r(z):
    if z < 10.2:
        return 1.24 - (z - 2.7) * (0.12 / 7.1)
    return 1.06 - (z - 10.2) * (0.12 / 8.3)


def lp(z, off, s):
    return tuple(d * (surf_r(z) + off) + side * s + V((0, 0, z)))


Z0, Z1 = 2.75, 19.3
for s in (-0.22, 0.22):
    P.append(E.rod("lrail", lp(Z0, 0.28, s), lp(Z1, 0.28, s), 0.03, 6, "M_Steel"))
z = Z0 + 0.25
while z < Z1:
    P.append(E.rod("rung", lp(z, 0.28, -0.22), lp(z, 0.28, 0.22), 0.022, 5, "M_Steel", cap="NOTHING"))
    z += 0.5
for zz in (4.0, 7.5, 11.0, 14.5, 18.0):
    P.append(E.rod("standoff", lp(zz, 0.02, 0.0), lp(zz, 0.28, 0.0), 0.03, 6, "M_Steel"))
z = 8.2
while z < Z1 - 0.3:
    hoop = []
    for k in range(7):
        a = math.pi * k / 6
        hoop.append(lp(z, 0.28 + 0.3 * math.sin(a), -0.24 * math.cos(a) - 0.0))
    hoop = [lp(z, 0.28, -0.24)] + [tuple(V(p)) for p in hoop[1:-1]] + [lp(z, 0.28, 0.24)]
    P.append(E.tube("hoop", hoop, 0.02, "M_Steel", 0, False))
    z += 1.6
# maintenance gallery near the top
GZ = 16.3
gr = surf_r(GZ)
P.append(E.lathe("gallery", [(gr - 0.05, GZ - 0.06), (1.34, GZ - 0.06), (1.34, GZ + 0.04), (gr - 0.05, GZ + 0.04)], 20,
                 m="M_Steel", cap_bottom=False, cap_top=False, smooth=30))
P.append(E.ring("railtop", 1.3, 0.03, (0, 0, GZ + 0.95), (0, 0, 1), "M_Steel", 20, 4))
P.append(E.ring("railmid", 1.3, 0.022, (0, 0, GZ + 0.5), (0, 0, 1), "M_Steel", 20, 4))
for k in range(8):
    a = 2 * math.pi * k / 8 + 0.1
    P.append(E.rod("railpost", (1.3 * math.cos(a), 1.3 * math.sin(a), GZ), (1.3 * math.cos(a), 1.3 * math.sin(a), GZ + 0.95), 0.025, 5, "M_Steel"))
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.3
    P.append(E.beam("bracket", (gr * math.cos(a), gr * math.sin(a), GZ - 0.8), (1.2 * math.cos(a), 1.2 * math.sin(a), GZ - 0.06),
                    0.07, 0.07, "M_Steel", 0.012))
st = E.join(P, "Smokestack")
# gentle cartoon lean at the top
LEAN = 0.2
E.deform(st, lambda p: V((p.x + LEAN * max(0.0, (p.z - 2.7) / 17.3) ** 2, p.y, p.z)))
rw.smooth(st, 40)
rw.empty("Smoke", (LEAN * 1.0, 0.0, 20.0))
E.col_box("Base", (3.0, 3.0, 2.85), (0, 0, 1.425))
E.col_cyl("StackLow", 1.24, 7.6, (0.02, 0, 6.5), verts=12)
E.col_cyl("StackHigh", 1.1, 9.8, (0.17, 0, 15.0), verts=12)
E.check(ASSET, (3.0, 3.0, 20.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
