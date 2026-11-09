"""bld_magic_shop: Lirael's spire, the spell vendor's tower on the town plaza (7 x 7 x ~14 m).

A round stone tower on a two-tier plinth, with a glowing rune band, violet rune windows, a little porch with a
lantern, a shop window full of glowing potions and a star banner. A corbelled, timber-framed upper room carries a
striped violet / teal onion dome with brass ribs; a ley crystal floats above the finial and more crystals hover
around the tower (all part of the mesh). Origin at the ground centre, front (door) facing -Y.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_magic_shop"
B.reset()
P = []
L = B.Lights()
rnd = random.Random(7)

VIOLET = "M_PaintedMetal__7a4fd0"
TEAL = "M_PaintedMetal__2fb3a6"
CLOTH = "M_Fabric__5236c8"


def d(theta):
    """Unit direction around the tower: theta 0 = front (-Y), 90 = +X."""
    a = math.radians(theta)
    return V((math.sin(a), -math.cos(a), 0))


# ---------------------------------------------------------------- tower radii
Z0 = 0.55                      # floor level (plinth top)
ZT = 7.4                       # top of the stone shaft
TOWER = [(2.55, Z0 - 0.05), (2.58, 1.0), (2.46, 2.2), (2.3, 3.6), (2.17, 5.0), (2.08, 6.4), (2.06, ZT)]


def tower_r(z):
    for (r0, z0), (r1, z1) in zip(TOWER[:-1], TOWER[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return TOWER[-1][0]


# ---------------------------------------------------------------- plinth and shaft
P.append(E.lathe("plinth0", [(3.2, -0.3), (3.25, 0.12), (3.12, 0.25), (2.95, 0.25)], 24, m="M_StoneRough", smooth=30, cap_bottom=False))
P.append(E.lathe("plinth1", [(2.95, 0.2), (2.92, 0.5), (2.82, Z0), (2.0, Z0)], 24, m="M_Stone", smooth=30, cap_bottom=False))
P.append(E.lathe("shaft", TOWER, 22, m="M_Stone", smooth=40, cap_bottom=False, cap_top=True))
for z, h, m in ((0.95, 0.35, "M_StoneRough"), (6.55, 0.22, "M_StoneRough")):
    r = tower_r(z) + 0.08
    P.append(E.lathe("band", [(r - 0.1, z - h / 2), (r, z - h / 2 + 0.04), (r, z + h / 2 - 0.04), (r - 0.1, z + h / 2)], 22,
                     m=m, smooth=40, cap_bottom=False, cap_top=False))
# glowing rune spiral: a stone ledge climbing one full turn round the shaft, carved with glyphs
HX0, HX1, HZ0, HZ1 = -125.0, 235.0, 3.0, 6.62
P.append(B.helix_band(d, tower_r, HX0, HX1, HZ0, HZ1, h=0.42, proud=0.11, n=56, m="M_StoneRough"))
P.append(B.helix_band(d, tower_r, HX0 + 4, HX1 - 4, HZ0 + 0.01, HZ1 - 0.01, h=0.19, proud=0.15, n=56, m="M_RuneGlow", inset=0.0,
                      chamfer=0.012))
for i in range(6):
    t = (i + 0.5) / 6
    th = HX0 + (HX1 - HX0) * t
    z = HZ0 + (HZ1 - HZ0) * t + 0.02
    r = tower_r(z)
    P.append(E.disc("medal", 0.3, 0.12, tuple(d(th) * (r + 0.16) + V((0, 0, z))), tuple(d(th)), 14, "M_StoneRough"))
    P += E.glyph(i * 3 + 1, 0.36, tuple(d(th) * (r + 0.235) + V((0, 0, z))), tuple(d(th)), "M_RuneGlow", 0.2, 0.04)
# a few jutting stones for hand-made charm
for i in range(16):
    th = rnd.uniform(0, 360)
    z = rnd.uniform(1.4, 6.3)
    if abs(((th + 180) % 360) - 180) < 30 and z < 3.6:
        continue
    r = tower_r(z)
    P.append(E.stone("jut", (rnd.uniform(0.35, 0.6), 0.2, rnd.uniform(0.2, 0.3)), tuple(d(th) * (r - 0.02) + V((0, 0, z))),
                     (0, 0, th), "M_Stone", 0.04, seed=i, jitter=4))

# ---------------------------------------------------------------- corbel table + upper room
UR = 2.62                      # upper room radius
U0, U1 = ZT + 0.1, ZT + 2.15   # upper room floor / eave
NC = 12
for i in range(NC):
    th = 360 * (i + 0.5) / NC
    base = d(th) * 1.9
    P.append(E.stone("corbel", (0.32, 0.8, 0.34), tuple(base + d(th) * 0.42 + V((0, 0, ZT - 0.12))), (0, 0, th), "M_Stone", 0.04))
    P.append(E.stone("corbel", (0.3, 0.55, 0.3), tuple(base + d(th) * 0.3 + V((0, 0, ZT - 0.45))), (0, 0, th), "M_Stone", 0.04))
P.append(E.lathe("floorring", [(1.9, U0 - 0.16), (UR + 0.12, U0 - 0.16), (UR + 0.12, U0 + 0.04), (1.9, U0 + 0.04)], 24,
                 m="M_WoodDark", smooth=30, cap_bottom=False, cap_top=False))
P.append(E.lathe("room", [(UR, U0), (UR, U1), (0.5, U1)], NC, m="M_Plaster", smooth=0, cap_bottom=False, cap_top=False, rot=(0, 0, 15)))
for i in range(NC):
    a = math.radians(360 * i / NC + 15)   # posts on the facet corners
    p = V((UR * math.cos(a), UR * math.sin(a), 0))
    P.append(E.rbox("post", (0.18, 0.18, U1 - U0), tuple(p * 1.012 + V((0, 0, (U0 + U1) / 2))), (0, 0, math.degrees(a)), "M_WoodDark", 0.03))
P.append(E.lathe("plate", [(UR - 0.05, U1 - 0.1), (UR + 0.1, U1 - 0.1), (UR + 0.1, U1 + 0.1), (UR - 0.05, U1 + 0.1)], NC,
                 m="M_WoodDark", smooth=0, cap_bottom=False, cap_top=False, rot=(0, 0, 15)))
# big arched rune windows on alternate facets (facet centres sit at 30*i deg from +X: theta = a + 90)
for i in range(NC):
    if i % 2 == 0:
        continue
    a = 360 * i / NC
    th = a + 90
    apo = UR * math.cos(math.pi / NC)
    w = E.window(0.78, 1.45, kind="arch", frame="M_WoodDark", glow="RuneWindow", sill=True, depth=0.08)
    E.place(w, tuple(d(th) * (apo + 0.01) + V((0, 0, (U0 + U1) / 2 + 0.02))), (0, 0, th))
    P += w
L.add(tuple(d(0) * (UR + 0.5) + V((0, 0, (U0 + U1) / 2))))

# ---------------------------------------------------------------- onion dome (violet / teal gores) + brass ribs
DZ = U1 + 0.05
dome_prof = [(UR + 0.22, DZ), (UR + 0.38, DZ + 0.3), (UR + 0.36, DZ + 0.75), (2.62, DZ + 1.25), (2.08, DZ + 1.8),
             (1.38, DZ + 2.3), (0.72, DZ + 2.72), (0.32, DZ + 3.02), (0.14, DZ + 3.3)]
NG = 16
dome = E.lathe("dome", [(UR - 0.2, DZ)] + dome_prof + [(0.0, DZ + 3.42)], NG, m=VIOLET, smooth=60, cap_bottom=True, cap_top=False)


def gore_teal(c, n):
    a = math.degrees(math.atan2(c.y, c.x)) % 360
    return int(a // (360 / NG)) % 2 == 1 and c.z > DZ + 0.05


rw.set_mat_where(dome, B.mat(TEAL), gore_teal)
P.append(dome)
for k in range(NG // 2):
    a = 2 * math.pi * (2 * k) / NG
    pts = [(rr * 1.015 * math.cos(a), rr * 1.015 * math.sin(a), z) for (rr, z) in dome_prof[1:]]
    P.append(E.tube("drib", pts, 0.055, "M_Brass", 1, smooth=True, ures=2))
P.append(E.ring("eavering", UR + 0.36, 0.09, (0, 0, DZ + 0.42), (0, 0, 1), "M_Brass", 32, 6))
# finial: brass spike with knobs, a little star, and a big ley crystal floating above it
FZ = DZ + 3.3
P.append(E.lathe("finial", [(0.16, FZ - 0.05), (0.2, FZ + 0.1), (0.08, FZ + 0.22), (0.16, FZ + 0.34), (0.07, FZ + 0.46), (0.03, FZ + 0.72),
                            (0.0, FZ + 0.76)], 10, m="M_Brass", smooth=50))
P.append(B.star_prism("finstar", 0.2, 0.09, 0.05, (0, 0, FZ + 0.56), (0, -1, 0), "StarGold"))
P.append(B.crystal("topcrystal", (0, 0, FZ + 1.2), 0.32, 1.1, (0, 0), "M_Crystal", 6, 15))
P.append(E.ring("toporbit", 0.62, 0.035, (0, 0, FZ + 1.2), (0.25, -0.2, 1), "TealGlowSoft", 24, 4))
P.append(E.ring("toporbit2", 0.5, 0.03, (0, 0, FZ + 1.3), (-0.3, 0.1, 1), "M_Brass", 24, 4))

# ---------------------------------------------------------------- porch, door, steps
DOOR_R = tower_r(1.5)
P.append(E.rbox("porchfloor", (2.5, 1.15, Z0 - 0.15), (0, -2.75, (Z0 + 0.15) / 2 + 0.02), m="M_Stone", r=0.05))
P.append(E.rbox("step", (2.1, 0.42, 0.3), (0, -3.5, 0.06), m="M_StoneRough", r=0.05))
dr = E.door(1.15, 2.35, arch=True, m="PaintViolet", frame="M_StoneRough", planks=4, round_window=True, frame_w=0.18)
E.place(dr, (0, -DOOR_R + 0.04, Z0))
P += dr
for sx in (-1, 1):
    P.append(E.lathe("column", [(0.22, 0.0), (0.22, 0.18), (0.15, 0.3), (0.13, 2.25), (0.2, 2.4), (0.2, 2.55), (0.0, 2.55)], 10,
                     loc=(sx * 1.0, -3.0, Z0 - 0.05), m="M_Stone", smooth=40))
PZ_E, PZ_R = Z0 + 2.5, Z0 + 3.45
P += E.gable_roof(-1.3, 1.3, -3.45, -1.75, PZ_E, PZ_R, t=0.16, sag=0.06, flare=1.2, nu=4, nv=4, m=VIOLET, ridge_mat=TEAL,
                  ridge_axis="Y", tilt=-0.08, ridge_r=0.1, barge="M_WoodDark", barge_r=0.07)
P.append(E.rbox("porchbeam", (2.3, 0.22, 0.24), (0, -3.0, PZ_E - 0.05), m="M_WoodDark", r=0.04))
pg = [(-1.15, PZ_E + 0.05), (1.15, PZ_E + 0.05), (0, PZ_R - 0.15)]
P.append(E.upright_prism("porchgable", pg, 0.12, -3.0, 0, 0, "M_Plaster"))
P += E.glyph(6, 0.42, (0, -3.08, PZ_E + 0.42), (0, -1, 0), "M_RuneGlow", 0.14, 0.04)
lamp, lc = E.lantern((0, -2.55, PZ_E + 0.05), "hang", scale=1.1)
P += lamp
L.add(lc)
# potted violet flowers by the steps
for sx in (-1, 1):
    pot = E.lathe("pot", [(0.17, 0.0), (0.23, 0.36), (0.26, 0.4), (0.26, 0.45), (0.21, 0.45)], 12, m="M_RoofTiles", smooth=40)
    E.place([pot], (sx * 1.6, -3.1, 0.0))
    P.append(pot)
    P += E.flower_cluster((sx * 1.6, -3.1, 0.3), 0.28, 6, seed=3 + sx, colors=("FlowerViolet", "FlowerBlue", "FlowerWhite"))

# ---------------------------------------------------------------- shop window with glowing potions (front-right)
SW_TH = 52.0
sw_c = d(SW_TH) * (tower_r(2.0) + 0.0) + V((0, 0, 2.05))
w = E.window(1.05, 1.35, kind="arch", frame="M_WoodDark", glow="WindowGlow", mullions=False, depth=0.12)
E.place(w, tuple(sw_c), (0, 0, SW_TH))
P += w
shelf = [E.rbox("shelf", (1.35, 0.42, 0.08), (0, -0.2, -0.72), m="M_WoodDark", r=0.02)]
for k, (x, g, h) in enumerate(((-0.45, "TealGlow", 0.32), (-0.15, "VioletGlow", 0.42), (0.15, "Ember", 0.28), (0.45, "TealGlow", 0.36))):
    prof = [(0.07, 0.0), (0.1, 0.03), (0.1, h * 0.55), (0.04, h * 0.75), (0.035, h), (0.05, h + 0.02), (0.0, h + 0.02)]
    b = E.lathe("potion", prof, 8, loc=(x, -0.25, -0.68), m=B.mat(g), smooth=50)
    shelf.append(b)
    shelf.append(rw.cylinder("cork", 0.04, 0.05, 6, (x, -0.25, -0.68 + h + 0.03), (0, 0, 0), E.mat("M_WoodPlanks")))
E.place(shelf, tuple(sw_c), (0, 0, SW_TH))
P += shelf
L.add(tuple(sw_c + d(SW_TH) * 0.5))
for sx in (-1, 1):
    P.append(E.beam("shelfbracket", tuple(sw_c + d(SW_TH) * 0.02 + d(SW_TH + 90) * sx * 0.5 + V((0, 0, -1.0))),
                    tuple(sw_c + d(SW_TH) * 0.38 + d(SW_TH + 90) * sx * 0.5 + V((0, 0, -0.78))), 0.06, 0.06, "M_WoodDark", 0.012))

# ---------------------------------------------------------------- rune windows on the shaft
for th, z, ww, hh in ((-55, 2.2, 0.62, 1.05), (180, 2.4, 0.62, 1.05), (235, 5.0, 0.72, 1.4), (0, 5.45, 0.72, 1.45),
                      (95, 2.3, 0.55, 0.9), (148, 2.95, 0.55, 0.9)):
    r = tower_r(z)
    w = E.window(ww, hh, kind="arch", frame="M_StoneRough", glow="RuneWindow", depth=0.1, frame_w=0.12)
    E.place(w, tuple(d(th) * (r - 0.02) + V((0, 0, z))), (0, 0, th))
    P += w
L.add(tuple(d(180) * (tower_r(2.4) + 0.5) + V((0, 0, 2.4))))

# ---------------------------------------------------------------- star banner on a brass arm (front-left)
# hangs flat in front of the tower from a brass rod on two brackets, facing the plaza at an angle
BTH = -42.0
BZ = 6.45
RO = tower_r(BZ) + 0.34
bpart = []
bpart.append(E.rod("bannerrod", (-0.68, -RO, BZ), (0.68, -RO, BZ), 0.05, 8, "M_Brass"))
for sx in (-1, 1):
    bpart.append(E.ball("rodknob", 0.09, (sx * 0.74, -RO, BZ), "StarGold", 10, 8))
    bpart.append(E.beam("rodbracket", (sx * 0.5, -RO + 0.42, BZ + 0.1), (sx * 0.5, -RO, BZ), 0.06, 0.06, "M_Brass", 0.012))
banner = E.cloth("banner", 1.1, 2.75, (0, -RO, BZ - 0.03), wave=0.05, waves=1.2, tail=0.45, m=CLOTH, t=0.03, nu=8, nv=10, sway=0.08)
bpart.append(banner)
bpart.append(B.star_prism("bstar", 0.36, 0.15, 0.18, (0, -RO - 0.05, BZ - 1.05), (0, -1, 0), "StarGold"))
for (x, z) in ((-0.3, -0.45), (0.3, -0.5), (0.0, -1.72)):
    bpart.append(B.star_prism("bstar2", 0.11, 0.05, 0.16, (x, -RO - 0.03, BZ + z), (0, -1, 0), "StarGold"))
for i in range(4):
    bpart.append(E.ring("bring", 0.06, 0.016, (-0.42 + 0.28 * i, -RO, BZ), (1, 0, 0), "M_Brass", 8, 4))
E.place(bpart, (0, 0, 0), (0, 0, BTH))
P += bpart

# ---------------------------------------------------------------- floating crystals around the tower
for k, (th, z, s, rr) in enumerate(((92, 5.3, 1.35, 3.08), (-86, 8.35, 1.15, 3.12), (196, 3.5, 1.2, 3.0))):
    c = d(th) * rr + V((0, 0, z))
    side = d(th + 90)
    P.append(B.crystal("fcrystal", tuple(c), 0.2 * s, s, (rnd.uniform(-8, 8), rnd.uniform(-8, 8)), "M_Crystal", 6, rnd.uniform(0, 40)))
    for sgn in (-1, 1):
        q = c + side * sgn * 0.2 * s + V((0, 0, -0.18 * s))
        P.append(B.crystal("fcrystal", tuple(q), 0.11 * s, 0.55 * s, tuple(V((0, sgn * 18, 0))), "M_Crystal", 5, rnd.uniform(0, 40)))
    P.append(E.ring("fring", 0.33 * s, 0.03, tuple(c - V((0, 0, s * 0.45))), (0, 0, 1), "TealGlowSoft", 18, 4))
    P.append(E.ring("fring2", 0.22 * s, 0.025, tuple(c - V((0, 0, s * 0.56))), (0, 0, 1), "M_Brass", 16, 4))
    for j in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        P.append(E.ball("mote", 0.05, tuple(c + V((math.cos(a) * s * 0.35, math.sin(a) * s * 0.35, rnd.uniform(-0.35, 0.35) * s))),
                        "TealGlow", 6, 4))

# ivy climbing the back-left of the tower (moss blobs, no sway)
for i in range(30):
    t = i / 29
    th = 212 + 26 * math.sin(t * 6.0) + rnd.uniform(-9, 9)
    z = 0.75 + t * 3.9 + rnd.uniform(-0.15, 0.15)
    r = tower_r(z)
    blob = rw.ico("ivy", rnd.uniform(0.3, 0.42) * (1.2 - 0.45 * t), 1, (0, 0, 0), (rnd.uniform(0, 40), 0, rnd.uniform(0, 90)),
                  (1.25, 0.5, 1.0), E.M("Moss" if i % 3 else "LeafDark"), None, 40)
    E.place([blob], tuple(d(th) * (r + 0.05) + V((0, 0, z))), (0, 0, th))
    P.append(blob)

E.tri_breakdown(P, 24)
main = E.join(P, "MagicShop")
W = E.wonk(main, 14.0, lean=(-0.12, 0.08), twist=4.0, bulge=0.012)
rw.smooth(main, 45)

# ---------------------------------------------------------------- empties
L.emit(W)

# ---------------------------------------------------------------- collision
E.col_cyl("Plinth", 3.2, 0.85, (0, 0, 0.12), verts=16)
E.col_frustum("Shaft", 2.58, 2.08, ZT - Z0 + 0.1, (0, 0, (Z0 + ZT) / 2), verts=16)
E.col_cyl("Room", UR + 0.15, U1 - ZT + 0.2, tuple(W((0, 0, (ZT + U1) / 2))), verts=16)
E.col_cyl("DomeLow", UR + 0.36, 1.3, tuple(W((0, 0, DZ + 0.65))), verts=16)
E.col_frustum("DomeHigh", 2.65, 0.3, 2.0, tuple(W((0, 0, DZ + 2.3))), verts=12)
E.col_box("Porch", (2.6, 1.4, PZ_R), (0, -2.85, PZ_R / 2))
E.col_box("Step", (2.1, 0.45, 0.25), (0, -3.5, 0.08))

E.check(ASSET, (7, 7, 14), 30000)
rw.finish(ASSET, "env", previews=E.previews())
