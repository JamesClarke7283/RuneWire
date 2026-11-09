"""bld_house_b: round stone tower-house (5 x 5 x ~9 m), a companion to bld_house_a.

A round stone ground floor with a jettied, twelve-sided half-timbered upper storey (plaster and dark timber like
bld_house_a), a flared witch-hat roof of terracotta tiles with a brass rooster weathervane, a little timber balcony
with flower boxes over the round-topped front door, teal shutters, and a stone chimney climbing the back.
Origin at the ground centre, front (door) facing -Y.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_house_b"
B.reset()
P = []
L = B.Lights()
rnd = random.Random(5)

CY = 0.15                      # the tower axis sits a touch behind the origin so the balcony fits the footprint
C = V((0, CY, 0))


def d(theta):
    a = math.radians(theta)
    return V((math.sin(a), -math.cos(a), 0))


CTH_J = 138
Z0 = 0.35
ZJ = 4.0                        # jetty (top of the stone storey)
U1 = 5.85                       # top of the timber storey
STONE = [(2.08, Z0 - 0.05), (2.1, 0.8), (2.04, 2.4), (1.96, ZJ)]


def stone_r(z):
    for (r0, z0), (r1, z1) in zip(STONE[:-1], STONE[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return STONE[-1][0]


UR = 2.12                       # upper storey radius (12 facets)
NF = 12

# ---------------------------------------------------------------- stone storey
P.append(E.lathe("plinth", [(2.3, -0.2), (2.32, 0.15), (2.22, Z0), (1.5, Z0)], 22, loc=tuple(C), m="M_StoneRough", smooth=30, cap_bottom=False))
P.append(E.lathe("stone", STONE + [(0.5, ZJ)], 22, loc=tuple(C), m="M_Stone", smooth=40, cap_bottom=False))
P.append(E.lathe("course", [(2.0, ZJ - 0.32), (2.06, ZJ - 0.28), (2.06, ZJ - 0.06), (2.0, ZJ)], 22, loc=tuple(C), m="M_StoneRough", smooth=40,
                 cap_bottom=False, cap_top=False))
for i in range(14):
    th = rnd.uniform(0, 360)
    z = rnd.uniform(0.7, 3.4)
    a = abs(((th + 180) % 360) - 180)
    if a < 32 or abs(a - 74) < 16 or a > 160 or abs(th - CTH_J) < 18:
        continue
    P.append(E.stone("jut", (rnd.uniform(0.35, 0.55), 0.18, rnd.uniform(0.2, 0.28)), tuple(C + d(th) * (stone_r(z) - 0.03) + V((0, 0, z))),
                     (0, 0, th), "M_Stone", 0.04, seed=i, jitter=4))
# joist ends under the jetty
for i in range(18):
    th = 360 * (i + 0.5) / 18
    P.append(E.rbox("joist", (0.13, 0.32, 0.15), tuple(C + d(th) * 2.0 + V((0, 0, ZJ + 0.02))), (0, 0, th), "M_WoodDark", 0.025))

# ---------------------------------------------------------------- timber upper storey (facets centred on theta = 0, 30, ...)
P.append(E.lathe("floor", [(1.8, ZJ), (UR + 0.1, ZJ), (UR + 0.1, ZJ + 0.18), (1.8, ZJ + 0.18)], NF, loc=tuple(C), m="M_WoodDark", smooth=0,
                 cap_bottom=False, cap_top=False, rot=(0, 0, 15)))
P.append(E.lathe("upper", [(UR, ZJ + 0.1), (UR, U1), (0.5, U1)], NF, loc=tuple(C), m="M_Plaster", smooth=0, cap_bottom=False,
                 cap_top=False, rot=(0, 0, 15)))
P.append(E.lathe("plate", [(UR - 0.04, U1 - 0.18), (UR + 0.08, U1 - 0.18), (UR + 0.08, U1 + 0.02), (UR - 0.04, U1 + 0.02)], NF, loc=tuple(C),
                 m="M_WoodDark", smooth=0, cap_bottom=False, cap_top=False, rot=(0, 0, 15)))
APO = UR * math.cos(math.pi / NF)
HALF = UR * math.sin(math.pi / NF)
facets = {}
for k in range(NF):
    th = 30.0 * k
    f = E.Face(tuple(C + d(th) * APO), tuple(d(th + 90)), tuple(d(th)))
    facets[k] = f
    # corner post on the left edge of each facet
    P.append(f.beam(-HALF, ZJ + 0.18, -HALF, U1 - 0.1, 0.16, 0.12, 0.06))
# mid rails and braces on the facets without windows or the balcony door
WIN_F = {0: "door", 2: "win", 4: "win", 6: "win", 9: "win"}
for k in range(NF):
    if k in WIN_F:
        continue
    f = facets[k]
    P.append(f.beam(-HALF, 4.95, HALF, 4.95, 0.13, 0.1, 0.045))
    s0 = 1 if k % 2 else -1
    P.append(f.beam(-s0 * (HALF - 0.08), ZJ + 0.27, s0 * (HALF - 0.08), 4.86, 0.12, 0.1, 0.045))
    P.append(f.beam(s0 * (HALF - 0.08), 5.05, -s0 * (HALF - 0.08), U1 - 0.22, 0.12, 0.1, 0.045))
for k, kind in WIN_F.items():
    if kind != "win":
        continue
    w = E.window(0.62, 0.78, shutters="PaintTeal" if k in (2, 9) else None, flowerbox=k in (4, 6), seed=k,
                 flowers=("FlowerRed", "FlowerYellow", "FlowerPink"))
    facets[k].put(w, 0.0, 4.98, 0.0)
    P += w
# balcony door on the front facet
bd = E.door(0.8, 1.48, arch=True, m="M_WoodPlanks", frame="M_WoodDark", planks=3, knob=True, round_window=True)
facets[0].put(bd, 0.0, ZJ + 0.18, 0.0)
P += bd

# ---------------------------------------------------------------- the balcony
BZ = ZJ + 0.18
BR = 2.5
P.append(E.arc_block("deck", (C.x, C.y), 1.9, BR, 180 - 42, 180 + 42, BZ - 0.16, BZ, nu=8, m="M_WoodPlanks"))
P.append(E.arc_block("deckedge", (C.x, C.y), BR - 0.08, BR + 0.02, 180 - 43, 180 + 43, BZ - 0.22, BZ - 0.08, nu=8, m="M_WoodDark"))
rail = []
for i in range(13):
    th = -40 + 80 * i / 12
    p = C + d(th) * (BR - 0.08)
    P.append(E.rbox("baluster", (0.07, 0.07, 0.72), tuple(p + V((0, 0, BZ + 0.36))), (0, 0, th), "M_WoodDark", 0.015))
    rail.append(tuple(p + V((0, 0, BZ + 0.78))))
P.append(E.tube("rail", rail, 0.06, "M_WoodDark", 1, smooth=True, ures=2))
P.append(E.tube("rail2", [(x, y, z - 0.52) for (x, y, z) in rail], 0.035, "M_WoodDark", 1, smooth=True, ures=2))
for sgn in (-1, 1):
    # end posts against the wall and flower boxes hung on the rail
    p_end = C + d(sgn * 41) * 2.2
    P.append(E.rbox("endpost", (0.12, 0.12, 0.95), tuple(p_end + V((0, 0, BZ + 0.47))), (0, 0, sgn * 41), "M_WoodDark", 0.02))
    for zz, rr in ((0.78, 0.06), (0.26, 0.035)):
        P.append(E.rod("siderail", tuple(p_end + V((0, 0, BZ + zz))), tuple(C + d(sgn * 40) * (BR - 0.08) + V((0, 0, BZ + zz))), rr, 6,
                       "M_WoodDark"))
    fb_c = C + d(sgn * 22) * (BR - 0.1) + V((0, 0, BZ + 0.93))
    fb = [E.rbox("fbox", (0.75, 0.22, 0.2), (0, 0, 0), m="M_WoodPlanks", r=0.03),
          rw.box("soil", (0.68, 0.15, 0.04), (0, 0, 0.09), mat=E.M("Soil"))]
    for j in range(5):
        fb.append(rw.ico("leaf", 0.09, 1, (-0.28 + 0.14 * j, rnd.uniform(-0.04, 0.04), 0.14), (0, 0, rnd.uniform(0, 90)), (1.2, 1, 0.8),
                         E.M("Leaf" if j % 2 else "LeafDark"), None, 30))
        fb.append(rw.ico("flower", 0.05, 1, (-0.26 + 0.13 * j, rnd.uniform(-0.05, 0.05), 0.23), (0, 0, 0), (1, 1, 0.75),
                         E.M(("FlowerPink", "FlowerYellow", "FlowerRed")[j % 3]), None, 0))
    E.place(fb, tuple(fb_c), (0, 0, sgn * 22))
    P += fb
for th in (-30, 0, 30):
    p0 = C + d(th) * (stone_r(3.0) - 0.02) + V((0, 0, 3.0))
    p1 = C + d(th) * (BR - 0.15) + V((0, 0, BZ - 0.2))
    P.append(E.beam("bracket", tuple(p0), tuple(p1), 0.12, 0.12, "M_WoodDark", 0.025, up=tuple(d(th))))

# ---------------------------------------------------------------- witch-hat roof + weathervane
RZ = U1 - 0.08
roof = E.cone_roof(2.47, 2.55, RZ, t=0.2, flare=0.5, seg=24, lean=(0.16, 0.06), m="M_RoofTiles", lip=0.14, curl=0.1)
E.place([roof], tuple(C))
P.append(roof)
TIP = C + V((0.16 + 0.1 * 0.16, 0.06 + 0.1 * 0.06, RZ + 2.55))
P.append(E.lathe("tipcap", [(0.13, -0.1), (0.15, 0.02), (0.08, 0.1), (0.0, 0.12)], 10, loc=tuple(TIP), m="M_Brass", smooth=50))
VZ = TIP.z + 0.1
P.append(E.rod("vanerod", tuple(TIP + V((0, 0, 0.05))), tuple(TIP + V((0, 0, 0.78))), 0.025, 6, "M_Brass"))
P.append(E.ball("vaneball", 0.07, tuple(TIP + V((0, 0, 0.2))), "M_Brass", 8, 6))
for k, ang in enumerate((0, 90, 180, 270)):
    a = math.radians(ang)
    dv = V((math.cos(a), math.sin(a), 0))
    P.append(E.rod("vanearm", tuple(TIP + V((0, 0, 0.3))), tuple(TIP + V((0, 0, 0.3)) + dv * 0.32), 0.016, 5, "M_Brass"))
    P.append(E.ball("vanetip", 0.04, tuple(TIP + V((0, 0, 0.3)) + dv * 0.34), "M_Brass", 6, 4))
AZ = TIP.z + 0.55
P.append(E.rod("arrow", tuple(TIP + V((-0.42, 0, 0.45))), tuple(TIP + V((0.42, 0, 0.45))), 0.02, 6, "M_Brass"))
P.append(rw.cone("arrowhead", 0.07, 0.0, 0.16, 6, tuple(TIP + V((0.48, 0, 0.45))), (0, 90, 0), E.mat("M_Brass")))
P.append(E.upright_prism("fletch", [(-0.48, -0.1), (-0.32, -0.02), (-0.32, 0.02), (-0.48, 0.1), (-0.42, 0.0)], 0.02, TIP.y, TIP.x,
                         TIP.z + 0.45, "M_Brass"))
ROO = [(-0.22, 0.0), (0.12, 0.0), (0.18, 0.08), (0.2, 0.18), (0.17, 0.24), (0.22, 0.26), (0.28, 0.29), (0.21, 0.31), (0.19, 0.36),
       (0.16, 0.41), (0.13, 0.37), (0.1, 0.4), (0.08, 0.34), (0.06, 0.25), (0.0, 0.19), (-0.08, 0.21), (-0.13, 0.4), (-0.18, 0.28),
       (-0.27, 0.36), (-0.25, 0.22), (-0.32, 0.2), (-0.23, 0.08)]
P.append(E.upright_prism("rooster", [(x * 1.35, z * 1.35) for (x, z) in ROO], 0.035, TIP.y, TIP.x, TIP.z + 0.48, "M_Brass"))

# ---------------------------------------------------------------- front door, steps, lantern, pots
DR = stone_r(1.4)
dr = E.door(1.08, 2.15, arch=True, m="M_WoodPlanks", frame="M_WoodDark", planks=4, round_window=True)
E.place(dr, tuple(C + d(0) * (DR - 0.05) + V((0, 0, Z0))))
P += dr
P.append(E.arc_block("step", (C.x, C.y), 1.9, 2.62, 180 - 22, 180 + 22, -0.1, 0.18, nu=4, m="M_Stone"))
P.append(E.arc_block("step2", (C.x, C.y), 1.9, 2.36, 180 - 18, 180 + 18, 0.1, Z0, nu=4, m="M_Stone"))
lp, lc = E.lantern(tuple(C + d(-28) * (stone_r(2.3) + 0.3) + V((0, 0, 2.3))), "wall", wall_normal=tuple(d(-28)))
P += lp
L.add(lc)
for th in (-36, 36):
    pot = E.lathe("pot", [(0.14, 0.0), (0.19, 0.3), (0.21, 0.33), (0.21, 0.37), (0.17, 0.37)], 12, m="M_RoofTiles", smooth=40)
    q = C + d(th) * 2.42
    E.place([pot], tuple(q))
    P.append(pot)
    P += E.flower_cluster(tuple(q + V((0, 0, 0.24))), 0.22, 5, seed=int(th) + 9, colors=("FlowerPink", "FlowerYellow", "FlowerWhite"))

# ---------------------------------------------------------------- ground-floor windows
for th, z, kw in ((-74, 1.8, dict(shutters="PaintTeal", flowerbox=True)), (74, 1.8, dict(shutters="PaintTeal", flowerbox=True)),
                  (180, 1.9, dict())):
    w = E.window(0.7, 0.88, seed=int(th), **kw)
    E.place(w, tuple(C + d(th) * (stone_r(z) - 0.03) + V((0, 0, z))), (0, 0, th))
    P += w
L.add(tuple(C + d(-74) * (stone_r(1.8) + 0.5) + V((0, 0, 1.8))))
L.add(tuple(C + d(0) * (APO + 0.7) + V((0, 0, BZ + 0.9))))

# ---------------------------------------------------------------- chimney up the back-right, rain barrel
CTH = 138
cb = C + d(CTH) * 2.18
P.append(E.rbox("chimney", (0.72, 0.62, 7.75), tuple(cb + V((0, 0, 7.75 / 2 - 0.2))), (0, 0, CTH), "M_Stone", 0.05))
P.append(E.rbox("chimcap", (0.9, 0.8, 0.16), tuple(cb + V((0, 0, 7.6))), (0, 0, CTH), "M_StoneRough", 0.04))
P.append(E.rbox("chimband", (0.8, 0.7, 0.1), tuple(cb + V((0, 0, 6.9))), (0, 0, CTH), "M_WoodDark", 0.03))
P.append(E.lathe("chimpot", [(0.16, 7.65), (0.18, 7.82), (0.14, 7.92), (0.17, 7.98), (0.12, 7.98)], 10, loc=(cb.x, cb.y, 0), m="M_Copper",
                 cap_top=False))
P += E.barrel(0.3, 0.8, tuple(C + d(108) * 2.3), 10)

E.tri_breakdown(P, 24)
main = E.join(P, "HouseB")
W = E.wonk(main, 9.0, lean=(0.12, -0.05), twist=4.0, bulge=0.012, center=(C.x, C.y))
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit(W)
rw.empty("Smoke", tuple(W(cb + V((0, 0, 8.05)))))

# ---------------------------------------------------------------- collision
E.col_cyl("Stone", 2.32, ZJ + 0.2, (C.x, C.y, (ZJ - 0.2) / 2), verts=16)
E.col_cyl("Upper", UR + 0.12, U1 - ZJ, tuple(W(C + V((0, 0, (ZJ + U1) / 2)))), verts=12)
E.col_frustum("Roof", 2.47, 0.25, 2.45, tuple(W(C + V((0.06, 0.02, RZ + 1.3)))), verts=12)
E.col_box("Chimney", (0.75, 0.7, 7.7), tuple(W(cb + V((0, 0, 3.7)))), (0, 0, CTH))
E.col_box("Balcony", (2.5, 0.65, 1.15), tuple(C + d(0) * 2.2 + V((0, 0, BZ + 0.35))))
E.col_box("Steps", (1.6, 0.6, 0.35), tuple(C + d(0) * 2.32 + V((0, 0, 0.1))))

E.check(ASSET, (5, 5, 9), 25000)
rw.finish(ASSET, "env", previews=E.previews())
