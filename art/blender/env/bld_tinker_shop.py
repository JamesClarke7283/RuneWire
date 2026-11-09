"""bld_tinker_shop: Gus's shop, the tinker vendor on the town plaza (8 x 6 x ~6 m).

A cosy timber-framed shop with a big open counter facing the plaza (-Y) under a red / cream striped awning, shelves
of gizmos behind the counter, crates and a barrel by the side, a copper stovepipe with a little propeller, and a big
brass gear sign standing on the roof: it has one big round robot eye and a tiny top hat, like Gus himself.
Origin at the ground centre, front (counter) facing -Y.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_tinker_shop"
B.reset()
P = []
L = B.Lights()

RED, CREAM = "M_Fabric__d94a3a", "M_Fabric__f3e4c2"

# ---------------------------------------------------------------- dimensions
HX = 3.25                 # half width of the walls
FY, BY = -1.85, 2.45      # front / back wall faces
Z0, ZE, ZR = 0.35, 3.05, 4.55
CX0, CX1 = -2.7, 1.25     # counter opening x range
CZ0, CZ1 = 1.15, 2.75     # counter top / opening top
REC = 0.85
RX0, RX1, RY0, RY1 = -HX - 0.38, HX + 0.38, FY - 0.45, BY + 0.42

# ---------------------------------------------------------------- masses
P.append(E.rbox("plinth", (2 * HX + 0.3, BY - FY + 0.3, 0.6), (0, (FY + BY) / 2, 0.05), m="M_Stone", r=0.07))
P.append(E.rbox("core", (2 * HX, BY - FY - REC, ZE - Z0 + 0.1), (0, (FY + REC + BY) / 2, (Z0 + ZE) / 2), m="M_Plaster", r=0.04))
for (x0, x1, z0, z1) in ((-HX, CX0, Z0, ZE), (CX1, HX, Z0, ZE), (CX0, CX1, Z0, CZ0), (CX0, CX1, CZ1, ZE)):
    P.append(E.rbox("front", (x1 - x0 + 0.02, REC + 0.04, z1 - z0 + 0.02), ((x0 + x1) / 2, FY + REC / 2, (z0 + z1) / 2), m="M_Plaster", r=0.035))
# roof + gables
P += E.gable_roof(RX0, RX1, RY0, RY1, ZE, ZR, t=0.22, sag=0.12, flare=1.3, nu=10, nv=6, tilt=0.14, ridge_r=0.13)
for sx in (-1, 1):
    xf = sx * HX
    pts = [(FY, ZE - 0.05), (BY, ZE - 0.05)]
    k = 10
    for i in range(k + 1):
        y = BY - (BY - FY) * i / k
        pts.append((y, E.roof_z(RX0, RX1, RY0, RY1, ZE, ZR, 0.12, 1.3, 0.14, "X", xf, y) - 0.02))
    P.append(E.face_prism("gable", pts, 0.26, (xf - sx * 0.13, 0, 0), (0, 1, 0), "M_Plaster"))
    g = E.Face((xf, 0, 0), (0, sx, 0), (sx, 0, 0))
    yc = (FY + BY) / 2
    zr = E.roof_z(RX0, RX1, RY0, RY1, ZE, ZR, 0.12, 1.3, 0.14, "X", xf, yc)
    P.append(g.beam(sx * yc, ZE, sx * yc, zr - 0.1, 0.16, 0.12, 0.06))
    win = E.window(0.42, 0.42, kind="round", frame="M_WoodDark")
    g.put(win, sx * (yc - 0.95), ZE + 0.55, 0.06)
    P += win

# ---------------------------------------------------------------- timber framing
YC = (FY + BY) / 2
front = E.Face((0, FY, 0), (1, 0, 0), (0, -1, 0))
back = E.Face((0, BY, 0), (-1, 0, 0), (0, 1, 0))
left = E.Face((-HX, YC, 0), (0, -1, 0), (-1, 0, 0))     # a = YC - y
right = E.Face((HX, YC, 0), (0, 1, 0), (1, 0, 0))      # a = y - YC


def frame(f, half, posts, braces, rails=()):
    out = [f.beam(-half, Z0 + 0.08, half, Z0 + 0.08, 0.18, 0.12, 0.06, extend=0.05),
           f.beam(-half, ZE - 0.08, half, ZE - 0.08, 0.2, 0.12, 0.06, extend=0.05)]
    for a in (-half, half):
        out.append(f.beam(a, Z0, a, ZE, 0.2, 0.14, 0.07))
    for a in posts:
        out.append(f.beam(a, Z0 + 0.1, a, ZE - 0.1, 0.15, 0.12, 0.05))
    for (a0, b0, a1, b1) in braces:
        out.append(f.beam(a0, b0, a1, b1, 0.14, 0.1, 0.045))
    for (a0, a1, z) in rails:
        out.append(f.beam(a0, z, a1, z, 0.14, 0.1, 0.045))
    return out


HD = (BY - FY) / 2
P += frame(front, HX, (), ())
P += frame(back, HX, (-1.2, 1.2), ((-HX, Z0 + 0.15, -1.2, ZE - 0.15), (HX, Z0 + 0.15, 1.2, ZE - 0.15)), rails=((-1.2, 1.2, 1.2),))
P += frame(left, HD, (0.95,), ((0.95, Z0 + 0.15, HD, ZE - 0.15),))
P += frame(right, HD, (0.2,), ((0.2, Z0 + 0.15, HD, ZE - 0.15),))

# ---------------------------------------------------------------- counter, interior, shelves of gizmos
P.append(rw.box("interior", (CX1 - CX0 + 0.1, 0.04, CZ1 - CZ0 + 0.1), ((CX0 + CX1) / 2, FY + REC - 0.03, (CZ0 + CZ1) / 2), mat=E.mat("Interior")))
P.append(E.rbox("ctop", (CX1 - CX0 + 0.3, REC + 0.45, 0.12), ((CX0 + CX1) / 2, FY + REC / 2 - 0.22, CZ0 + 0.02), m="M_WoodPlanks", r=0.03))
P.append(E.rbox("ctrim", (CX1 - CX0 + 0.34, 0.08, 0.1), ((CX0 + CX1) / 2, FY - 0.45, CZ0 + 0.0), m="M_Brass", r=0.025))
for i in range(4):
    x = CX0 + 0.5 + (CX1 - CX0 - 1.0) * i / 3
    P.append(E.rbox("cpanel", (0.78, 0.06, 0.55), (x, FY - 0.04, (Z0 + CZ0) / 2 + 0.02), m="PaintTeal", r=0.03))
    P.append(E.rivet("criv", (x, FY - 0.08, (Z0 + CZ0) / 2 + 0.02), 0.045, "M_Brass"))
for sx in (CX0 - 0.1, CX1 + 0.1):
    P.append(E.rbox("cpost", (0.22, 0.24, CZ1 - Z0 + 0.15), (sx, FY - 0.03, (Z0 + CZ1) / 2 + 0.05), m="M_WoodDark", r=0.04))
P.append(E.rbox("clintel", (CX1 - CX0 + 0.5, 0.26, 0.24), ((CX0 + CX1) / 2, FY - 0.04, CZ1 + 0.1), m="M_WoodDark", r=0.04))
SY = FY + REC - 0.2
for z in (1.68, 2.25):
    P.append(E.rbox("shelf", (CX1 - CX0 - 0.1, 0.36, 0.06), ((CX0 + CX1) / 2, SY, z), m="M_WoodDark", r=0.015))


def gizmo(kind, x, z, s=1.0):
    y = SY - 0.02
    out = []
    if kind == "gear":
        out += B.gear_wheel("gz", 0.16 * s, 8, (x, y - 0.05, z + 0.17 * s), (0, -1, 0), 0.05, m="M_Brass", spokes=0, hub=0.05)
    elif kind == "clock":
        out.append(E.disc("gzc", 0.15 * s, 0.08, (x, y, z + 0.16 * s), (0, -1, 0), 12, "M_Copper"))
        out.append(E.disc("gzf", 0.12 * s, 0.02, (x, y - 0.05, z + 0.16 * s), (0, -1, 0), 12, "Dial"))
        out.append(E.beam("gzh", (x, y - 0.065, z + 0.16 * s), (x + 0.07 * s, y - 0.065, z + 0.22 * s), 0.02, 0.01, "Ink", 0.0, up=(0, -1, 0)))
    elif kind == "bottle":
        out.append(E.lathe("gzb", [(0.06, 0.0), (0.07, 0.15), (0.03, 0.22), (0.03, 0.27), (0.0, 0.27)], 8, loc=(x, y, z), m="BottleGreen", smooth=50))
    elif kind == "box":
        out.append(E.rbox("gzx", (0.26 * s, 0.22, 0.2 * s), (x, y, z + 0.1 * s), m="M_PaintedMetal", r=0.02))
        out.append(E.disc("gzd", 0.04, 0.02, (x, y - 0.12, z + 0.1 * s), (0, -1, 0), 8, "TealGlow"))
    elif kind == "spring":
        pts = [(x + 0.07 * math.cos(t * 0.6), y + 0.07 * math.sin(t * 0.6), z + 0.012 * t) for t in range(24)]
        out.append(E.tube("gzs", pts, 0.015, "M_Steel", 0, smooth=False))
    elif kind == "lamp":
        lp, lc = E.lantern((x, y, z), "post", scale=0.7)
        out += lp
    elif kind == "head":
        out.append(rw.sphere("gzr", 0.14, 10, 6, (x, y, z + 0.14), (0, 0, 0), (1, 1, 0.9), E.mat("M_Brass")))
        out.append(E.disc("gze", 0.06, 0.03, (x, y - 0.13, z + 0.15), (0, -1, 0), 10, "TealGlow"))
        out.append(rw.cylinder("gzt", 0.06, 0.12, 8, (x, y, z + 0.3), (0, 0, 0), E.mat("Charcoal")))
    return out


row1 = (("gear", 1.0), ("bottle", 1.0), ("clock", 1.0), ("box", 1.0), ("spring", 1.0), ("head", 1.0), ("gear", 1.3), ("bottle", 1.0))
row2 = (("box", 1.2), ("clock", 1.3), ("lamp", 1.0), ("gear", 0.9), ("bottle", 1.0), ("box", 1.0), ("spring", 1.0), ("clock", 1.0))
for row, z in ((row1, 1.71), (row2, 2.28)):
    for i, (k, sc) in enumerate(row):
        x = CX0 + 0.3 + (CX1 - CX0 - 0.6) * i / (len(row) - 1)
        P += gizmo(k, x, z, sc)
# things on the counter: a brass bell, a till, a jar of bolts, a little lamp
P.append(E.lathe("bell", [(0.13, 0.0), (0.12, 0.04), (0.09, 0.1), (0.06, 0.16), (0.02, 0.19), (0.0, 0.2)], 12,
                 loc=(-0.2, FY - 0.25, CZ0 + 0.08), m="M_Brass", smooth=50))
P.append(E.ball("bellknob", 0.025, (-0.2, FY - 0.25, CZ0 + 0.3), "M_Brass", 6, 4))
P.append(E.rbox("till", (0.55, 0.42, 0.34), (-1.6, FY - 0.05, CZ0 + 0.25), (0, 0, 8), m="M_Brass", r=0.05))
P.append(E.rbox("tilltop", (0.45, 0.2, 0.18), (-1.6, FY + 0.06, CZ0 + 0.5), (-20, 0, 8), m="M_Copper", r=0.04))
for i in range(3):
    P.append(E.ball("tillkey", 0.035, (-1.75 + 0.15 * i, FY - 0.28, CZ0 + 0.36), "Dial", 6, 4))
P.append(rw.cylinder("jar", 0.11, 0.24, 10, (0.45, FY - 0.15, CZ0 + 0.2), (0, 0, 0), E.mat("M_Glass")))
for i in range(4):
    P.append(rw.cylinder("bolt", 0.035, 0.05, 6, (0.42 + 0.04 * (i % 2), FY - 0.15 + 0.03 * (i // 2), CZ0 + 0.12 + 0.05 * i), (0, 0, 0), E.mat("M_Steel")))
P.append(rw.cylinder("jarlid", 0.12, 0.04, 10, (0.45, FY - 0.15, CZ0 + 0.33), (0, 0, 0), E.mat("M_Copper")))
lamp, lc = E.lantern((0.95, FY - 0.15, CZ0 + 0.08), "post", scale=0.85)
P += lamp
L.add(lc)
L.add(((CX0 + CX1) / 2 - 0.4, FY + 0.3, 2.3))

# ---------------------------------------------------------------- striped awning with a scalloped valance
AX0, AX1 = CX0 - 0.3, CX1 + 0.3
AW_N = 8
AY_OUT = -3.0
prof = []
for i in range(7):
    t = i / 6
    y = FY - 0.02 + (AY_OUT - FY + 0.02) * t
    z = ZE - 0.05 - 0.58 * t - 0.12 * math.sin(math.pi * t)
    prof.append((y, z))
for i in range(AW_N):
    x0 = AX0 + (AX1 - AX0) * i / AW_N
    x1 = AX0 + (AX1 - AX0) * (i + 1) / AW_N
    m = RED if i % 2 == 0 else CREAM
    P.append(B.sweep("awning", [(x0, y, z) for (y, z) in prof], (x1 - x0, 0, 0), -0.04, m, smooth=50))
    val = B.scallop_outline(x1 - x0, 0.0, 0.16, 1, -0.22, 6)
    P.append(E.upright_prism("valance", [(x + (x0 + x1) / 2, z + prof[-1][1]) for (x, z) in val], 0.035, AY_OUT - 0.01, 0, 0, m))
P.append(E.rod("awnrod", (AX0 - 0.05, AY_OUT, prof[-1][1] - 0.02), (AX1 + 0.05, AY_OUT, prof[-1][1] - 0.02), 0.035, 8, "M_Brass"))
for x in (AX0 + 0.12, AX1 - 0.12):
    P.append(E.rod("awnbrace", (x, FY - 0.05, CZ1 - 0.25), (x, AY_OUT + 0.1, prof[-1][1] - 0.04), 0.03, 6, "IronDark"))
    P.append(E.ball("awnknob", 0.06, (x, AY_OUT, prof[-1][1] - 0.02), "M_Brass", 8, 6))

# ---------------------------------------------------------------- door (right of the counter) and step
DX = 2.3
dr = E.door(0.98, 2.1, arch=True, m="PaintTeal", frame="M_WoodDark", planks=3, round_window=True)
front.put(dr, DX, Z0, 0.0)
P += dr
P.append(E.rbox("doorstep", (1.3, 0.45, 0.28), (DX, FY - 0.3, 0.12), m="M_StoneRough", r=0.05))
lp, lpc = E.lantern((DX + 0.82, FY - 0.32, 2.35), "wall", wall_normal=(0, -1, 0))
P += lp
L.add(lpc)
# little hanging blade sign over the door: a spanner
P.append(E.rod("signarm", (DX - 0.6, FY - 0.02, 2.82), (DX - 0.6, FY - 0.75, 2.82), 0.03, 6, "IronDark"))
P.append(E.rbox("bladesign", (0.06, 0.55, 0.42), (DX - 0.6, FY - 0.45, 2.5), m="PaintCream", r=0.03))
P.append(E.beam("bladespanner", (DX - 0.6, FY - 0.25, 2.37), (DX - 0.6, FY - 0.63, 2.63), 0.07, 0.08, "M_Steel", 0.015, up=(1, 0, 0)))
for k in (-1, 1):
    P.append(E.rod("signchain", (DX - 0.6, FY - 0.45 + k * 0.2, 2.82), (DX - 0.6, FY - 0.45 + k * 0.2, 2.71), 0.012, 4, "IronDark"))

# ---------------------------------------------------------------- windows on the sides and back
for (f, a, z, kw) in ((left, -0.3, 1.85, dict(shutters="PaintTeal", flowerbox=True)),
                      (right, -0.9, 1.85, dict(shutters="PaintTeal")),
                      (back, 1.75, 1.85, dict(flowerbox=True)), (back, -1.95, 1.85, dict())):
    w = E.window(0.8, 0.9, seed=int(a * 10 + z), **kw)
    f.put(w, a, z, 0.0)
    P += w
L.add(left.p(-0.3, 1.85, 0.5))

# ---------------------------------------------------------------- crates, barrel, stovepipe
P += E.crate((0.8, 0.8, 0.8), (-3.75, -0.85, 0.0), 6)
P += E.crate((0.7, 0.7, 0.7), (-3.72, 0.05, 0.0), -10)
P += E.crate((0.6, 0.6, 0.6), (-3.74, -0.6, 0.8), 18)
for i in range(4):
    P += B.gear_wheel("cgear", 0.12 + 0.04 * (i % 2), 8, (-3.95 + 0.18 * i, -0.85 - 0.42, 0.25 + 0.12 * i), (0, -1, 0.3), 0.05,
                      m="M_Brass" if i % 2 else "M_Copper", spokes=0, hub=0.04)
P += E.barrel(0.32, 0.85, (-3.62, 1.3, 0.0), 30)
P += E.sack((-3.7, 2.1, 0.0), 0.65, 0.26, 20, 6)
# copper stovepipe up the right wall with a spinning propeller cowl
SPX, SPY = HX + 0.28, 1.15
P += E.pipe("stove", [(HX + 0.02, SPY, 1.0), (SPX, SPY, 1.0), (SPX, SPY, 5.2)], 0.13, "M_Copper", 0.25)
for z in (2.0, 3.4):
    P.append(E.beam("stovestrap", (HX, SPY, z), (SPX, SPY, z), 0.08, 0.05, "IronDark", 0.012))
P.append(rw.cone("cowl", 0.26, 0.08, 0.3, 10, (SPX, SPY, 5.35), (0, 0, 0), E.mat("M_Brass")))
P.append(E.rod("propshaft", (SPX, SPY, 5.45), (SPX, SPY, 5.72), 0.025, 6, "M_Steel"))
for k in range(3):
    a = 2 * math.pi * k / 3
    P.append(E.beam("blade", (SPX, SPY, 5.7), (SPX + 0.36 * math.cos(a), SPY + 0.36 * math.sin(a), 5.72), 0.12, 0.025, "PaintRed", 0.01,
                    up=(0, 0, 1)))
P.append(E.ball("prophub", 0.06, (SPX, SPY, 5.72), "M_Brass", 8, 6))

# ---------------------------------------------------------------- the gear sign on the roof: one big eye and a top hat
GY = -0.75
gz_roof = E.roof_z(RX0, RX1, RY0, RY1, ZE, ZR, 0.12, 1.3, 0.14, "X", 0.0, GY) + 0.22
GR = 0.92
GC = V((-0.35, GY, gz_roof + GR + 0.18))
P += B.gear_wheel("signgear", GR, 12, tuple(GC), (0, -1, 0), 0.2, m="M_Brass", spokes=0, hub=0.0, rim=0.2, depth=0.17)
P.append(E.disc("eyewhite", GR - 0.35, 0.14, tuple(GC), (0, -1, 0), 20, "Dial"))
P.append(E.disc("iris", 0.27, 0.05, tuple(GC + V((0.04, -0.08, 0.03))), (0, -1, 0), 16, "TealGlow"))
P.append(E.disc("pupil", 0.13, 0.05, tuple(GC + V((0.05, -0.11, 0.03))), (0, -1, 0), 12, "GlassDark"))
P.append(E.ball("glint", 0.05, tuple(GC + V((-0.04, -0.14, 0.12))), "FlowerWhite", 6, 4))
P.append(E.ring("eyebezel", GR - 0.33, 0.05, tuple(GC + V((0, -0.07, 0))), (0, -1, 0), "M_Copper", 20, 6))
for sx in (-1, 1):
    foot = V((GC.x + sx * 0.55, GY + 0.05, E.roof_z(RX0, RX1, RY0, RY1, ZE, ZR, 0.12, 1.3, 0.14, "X", GC.x + sx * 0.55, GY) + 0.2))
    P.append(E.beam("signleg", tuple(foot), tuple(GC + V((sx * 0.3, 0.12, -0.55))), 0.1, 0.1, "IronDark", 0.02, up=(0, -1, 0)))
    P.append(E.rbox("signfoot", (0.3, 0.3, 0.08), tuple(foot), m="IronDark", r=0.02))
hat_base = GC + V((0.22, 0.0, GR - 0.06))
hat = [rw.cylinder("hatbrim", 0.34, 0.05, 14, (0, 0, 0.025), (0, 0, 0), E.mat("Charcoal")),
       rw.cylinder("hatcrown", 0.21, 0.36, 14, (0, 0, 0.23), (0, 0, 0), E.mat("Charcoal")),
       rw.cylinder("hatband", 0.215, 0.07, 14, (0, 0, 0.1), (0, 0, 0), E.mat("PaintRed"))]
E.place(hat, tuple(hat_base), (0, 16, 0))
P += hat

E.tri_breakdown(P, 24)
main = E.join(P, "TinkerShop")
W = E.wonk(main, 6.5, lean=(0.1, -0.04), twist=2.5, bulge=0.012)
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit(W)
rw.empty("Smoke", tuple(W((SPX, SPY, 5.5))))

# ---------------------------------------------------------------- collision
E.col_box("Shop", (2 * HX + 0.3, BY - FY + 0.3, ZE + 0.2), (0, YC, (ZE - 0.2) / 2))
E.col_box("Counter", (CX1 - CX0 + 0.4, 0.5, CZ0 + 0.2), ((CX0 + CX1) / 2, FY - 0.2, (CZ0 + 0.2) / 2 - 0.1))
for sy in (-1, 1):
    run, rise = (RY1 - RY0) / 2, ZR - ZE
    Lr = math.hypot(run, rise)
    ang = math.degrees(math.atan2(rise, run))
    E.col_box("Roof", (RX1 - RX0, Lr, 0.45), (0, (RY0 + RY1) / 2 + sy * run / 2, (ZE + ZR) / 2 + 0.1), (-sy * ang, 0, 0))
E.col_box("Crates", (1.0, 2.0, 1.4), (-3.75, -0.4, 0.7))
E.col_cyl("Barrel", 0.36, 0.9, (-3.62, 1.3, 0.45))
E.col_box("Sign", (2.0, 0.4, 2.0), tuple(W(GC)))

E.check(ASSET, (8, 6, 6), 25000)
rw.finish(ASSET, "env", previews=E.previews())
