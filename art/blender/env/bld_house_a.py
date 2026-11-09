"""bld_house_a: crooked cartoon timber-frame house (6 x 5 x ~8 m).

Two floors with a jettied upper floor, a steep wonky bell-cast roof, a stone chimney, flower boxes and a round-topped
front door. Origin at the ground centre, front (door) facing -Y.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
V = E.V
ASSET = "bld_house_a"
rw.reset()
P = []  # visual parts

# ---------------------------------------------------------------- dimensions
GX, GY = 2.3, 1.8          # ground-floor half sizes (wall faces)
Z0, Z1 = 0.45, 2.85        # ground floor
UX, UY = 2.55, 2.1         # upper-floor half sizes (jetty)
U0, U1 = 3.08, 5.15        # upper floor
RX, RY = 2.74, 2.33        # roof rectangle half sizes
ZE, ZR = 5.14, 7.45        # eave / ridge heights
SAG, FLARE, TILT = 0.22, 1.3, 0.24

# ---------------------------------------------------------------- masses
P.append(E.rbox("plinth", (2 * GX + 0.3, 2 * GY + 0.3, Z0 + 0.2), (0, 0, (Z0 - 0.2) / 2), m="M_Stone", r=0.09))
P.append(E.rbox("walls", (2 * GX, 2 * GY, Z1 - Z0 + 0.1), (0, 0, (Z0 + Z1) / 2), m="M_Plaster", r=0.04))
P.append(E.rbox("jetty", (2 * UX + 0.12, 2 * UY + 0.12, 0.24), (0, 0, U0 - 0.1), m="M_WoodDark", r=0.04))
P.append(E.rbox("upper", (2 * UX, 2 * UY, U1 - U0 + 0.05), (0, 0, (U0 + U1) / 2), m="M_Plaster", r=0.04))
P.append(E.rbox("wallplate", (2 * UX + 0.1, 2 * UY + 0.1, 0.22), (0, 0, U1 - 0.02), m="M_WoodDark", r=0.04))

# joist ends under the jetty (front and back) and corner brackets
for sy in (-1, 1):
    n = 10
    for i in range(n):
        x = -GX + 0.2 + (2 * GX - 0.4) * i / (n - 1)
        P.append(E.rbox("joist", (0.14, UY - GY + 0.12, 0.16), (x, sy * (GY + (UY - GY) / 2), U0 - 0.27), m="M_WoodDark", r=0.025))
for sx in (-1, 1):
    for sy in (-1, 1):
        P.append(E.beam("corbel", (sx * (GX - 0.02), sy * (GY + 0.02), Z1 - 0.55), (sx * (GX + 0.18), sy * (UY - 0.08), U0 - 0.2),
                        0.16, 0.16, "M_WoodDark", 0.03))

# ---------------------------------------------------------------- timber framing
front = E.Face((0, -GY, 0), (1, 0, 0), (0, -1, 0))
back = E.Face((0, GY, 0), (-1, 0, 0), (0, 1, 0))
left = E.Face((-GX, 0, 0), (0, -1, 0), (-1, 0, 0))
right = E.Face((GX, 0, 0), (0, 1, 0), (1, 0, 0))
ufront = E.Face((0, -UY, 0), (1, 0, 0), (0, -1, 0))
uback = E.Face((0, UY, 0), (-1, 0, 0), (0, 1, 0))
uleft = E.Face((-UX, 0, 0), (0, -1, 0), (-1, 0, 0))
uright = E.Face((UX, 0, 0), (0, 1, 0), (1, 0, 0))


def frame_face(f, half, z0, z1, studs, braces, rails=()):
    out = []
    out.append(f.beam(-half, z0 + 0.08, half, z0 + 0.08, 0.18, 0.12, 0.06, extend=0.06))   # sill
    out.append(f.beam(-half, z1 - 0.08, half, z1 - 0.08, 0.18, 0.12, 0.06, extend=0.06))   # top plate
    for a in (-half, half):
        out.append(f.beam(a, z0, a, z1, 0.2, 0.14, 0.07))                                  # corner posts
    for a in studs:
        out.append(f.beam(a, z0 + 0.1, a, z1 - 0.1, 0.15, 0.12, 0.05))
    for (a0, b0, a1, b1) in braces:
        out.append(f.beam(a0, b0, a1, b1, 0.14, 0.1, 0.045))
    for (a0, a1, z) in rails:
        out.append(f.beam(a0, z, a1, z, 0.14, 0.1, 0.045))
    return out


# ground floor
P += frame_face(front, GX, Z0, Z1, studs=(-1.55, 0.05, 0.62, 1.9),
                braces=((-GX, Z0 + 0.15, -1.55, Z1 - 0.15),), rails=((0.62, 1.9, 1.1),))
P += frame_face(back, GX, Z0, Z1, studs=(-0.55, 0.55),
                braces=((-GX, Z0 + 0.15, -0.55, Z1 - 0.15), (GX, Z0 + 0.15, 0.55, Z1 - 0.15)), rails=((-0.55, 0.55, 1.1),))
P += frame_face(left, GY, Z0, Z1, studs=(0.0,), braces=((-GY, Z1 - 0.15, 0.0, Z0 + 0.15),), rails=((0.0, GY, 1.1),))
P += frame_face(right, GY, Z0, Z1, studs=(0.0,), braces=((-GY, Z0 + 0.15, 0.0, Z1 - 0.15), (GY, Z0 + 0.15, 0.0, Z1 - 0.15)))
# upper floor
P += frame_face(ufront, UX, U0, U1, studs=(-1.72, -0.68, 0.68, 1.72),
                braces=((-0.68, U0 + 0.15, 0.68, U1 - 0.15), (0.68, U0 + 0.15, -0.68, U1 - 0.15)),
                rails=((-1.72, -0.68, 3.55), (0.68, 1.72, 3.55)))
P += frame_face(uback, UX, U0, U1, studs=(-1.6, -0.6, 0.6, 1.6),
                braces=((-UX, U0 + 0.15, -1.6, U1 - 0.15), (UX, U0 + 0.15, 1.6, U1 - 0.15)),
                rails=((-0.6, 0.6, 3.55),))
P += frame_face(uleft, UY, U0, U1, studs=(-0.55, 0.55), braces=((-UY, U0 + 0.15, -0.55, U1 - 0.15), (UY, U0 + 0.15, 0.55, U1 - 0.15)),
                rails=((-0.55, 0.55, 3.55),))
P += frame_face(uright, UY, U0, U1, studs=(-0.55, 0.55), braces=((-UY, U1 - 0.15, -0.55, U0 + 0.15), (UY, U1 - 0.15, 0.55, U0 + 0.15)),
                rails=((-0.55, 0.55, 3.55),))

# ---------------------------------------------------------------- roof + gables
P += E.gable_roof(-RX, RX, -RY, RY, ZE, ZR, t=0.24, sag=SAG, flare=FLARE, nu=12, nv=7, tilt=TILT, ridge_r=0.14)

for sx in (-1, 1):
    xf = sx * UX
    pts = [(-UY, U1)]
    pts.append((UY, U1))
    k = 12
    for i in range(k + 1):
        y = UY - 2 * UY * i / k
        pts.append((y, E.roof_z(-RX, RX, -RY, RY, ZE, ZR, SAG, FLARE, TILT, "X", xf, y) - 0.02))
    # face_prism draws (a, b) with a along u; u = +Y on both ends keeps the polygon CCW-agnostic (normals recalculated)
    P.append(E.face_prism("gable", pts, 0.3, (xf - sx * 0.15, 0, 0), (0, 1, 0), "M_Plaster"))
    g = E.Face((xf, 0, 0), (0, sx, 0), (sx, 0, 0))
    zr = E.roof_z(-RX, RX, -RY, RY, ZE, ZR, SAG, FLARE, TILT, "X", xf, 0.0)
    P.append(g.beam(0, U1, 0, zr - 0.1, 0.18, 0.12, 0.06))                         # king post
    P.append(g.beam(-1.5, U1 + 0.1, 0, U1 + 1.05, 0.14, 0.1, 0.05))
    P.append(g.beam(1.5, U1 + 0.1, 0, U1 + 1.05, 0.14, 0.1, 0.05))
    win = E.window(0.5, 0.5, kind="round", frame="M_WoodDark")
    g.put(win, 0.0, U1 + 1.45, 0.06)
    P += win

# chimney (stone) through the roof on the +X / back side
CX, CY = 1.55, 0.95
P.append(E.rbox("chimney", (0.78, 0.78, 3.4), (CX, CY, 4.75 + 1.7), m="M_Stone", r=0.06))
P.append(E.rbox("chimcap", (1.0, 1.0, 0.16), (CX, CY, 8.0), m="M_Stone", r=0.05))
P.append(E.lathe("chimpot", [(0.2, 8.05), (0.22, 8.2), (0.17, 8.32), (0.2, 8.38), (0.15, 8.38)], 12, loc=(CX, CY, 0), m="M_Copper", cap_top=False))
P.append(E.rbox("chimband", (0.84, 0.84, 0.1), (CX, CY, 7.55), m="M_WoodDark", r=0.03))

# ---------------------------------------------------------------- door, windows, details
dr = E.door(1.1, 2.15, arch=True, m="M_WoodPlanks", frame="M_WoodDark", planks=4, round_window=True)
front.put(dr, -0.75, Z0, 0.0)
P += dr
for (w, d, h, x, z) in ((1.6, 0.36, 0.22, -0.75, 0.11), (1.4, 0.3, 0.2, -0.75, 0.33)):
    P.append(E.rbox("step", (w, d, h), (x, -GY - 0.15 - d / 2 - (0.0 if z < 0.2 else -0.12), z), m="M_Stone", r=0.04))

lamp, lamp_c = E.lantern((-1.85, -GY - 0.33, 2.25), "wall", wall_normal=(0, -1, 0))
P += lamp

w1 = E.window(0.85, 0.95, shutters="PaintTeal", flowerbox=True, seed=1)
front.put(w1, 1.26, 1.72, 0.0)
P += w1
for i, a in enumerate((-1.2, 1.2)):
    w = E.window(0.75, 0.9, shutters="PaintTeal", flowerbox=True, seed=10 + i,
                 flowers=("FlowerRed", "FlowerYellow", "FlowerPink") if i else ("FlowerPink", "FlowerWhite", "FlowerYellow"))
    ufront.put(w, a, 4.15, 0.0)
    P += w
for f, a, z, kw in ((left, 0.95, 1.75, dict(shutters="PaintTeal")),
                    (right, -0.9, 1.75, dict()),
                    (back, 0.0, 1.75, dict(shutters="PaintTeal", flowerbox=True)),
                    (uleft, 0.0, 4.15, dict(flowerbox=True)),
                    (uright, 0.0, 4.15, dict(shutters="PaintTeal")),
                    (uback, -0.0, 4.15, dict())):
    w = E.window(0.7, 0.85, seed=int(a * 10 + z), **kw)
    f.put(w, a, z, 0.0)
    P += w

# flower pots by the door
for x in (-1.55, 0.05):
    P.append(E.lathe("pot", [(0.13, 0.0), (0.18, 0.28), (0.2, 0.3), (0.2, 0.34), (0.16, 0.34)], 12, m="M_RoofTiles",
                     cap_top=True, smooth=40))
    E.place([P[-1]], (x, -GY - 0.42, 0.0))
    P += E.flower_cluster((x, -GY - 0.42, 0.22), 0.22, 5, seed=int(x * 7) + 3)

# rain barrel at the front-right corner
P += E.barrel(0.3, 0.8, (GX - 0.1, -GY - 0.45, 0.0), 15)

E.tri_breakdown(P, 20)
house = E.join(P, "HouseA")
W = E.wonk(house, 8.0, lean=(0.16, 0.05), twist=3.2, bulge=0.012)
rw.smooth(house, 40)

# ---------------------------------------------------------------- empties
rw.empty("LightPoint_0", W(lamp_c))
rw.empty("LightPoint_1", W((1.26, -GY - 0.45, 1.72)))
rw.empty("LightPoint_2", W((-1.2, -UY - 0.45, 4.15)))
rw.empty("Smoke", W((CX, CY, 8.45)))

# ---------------------------------------------------------------- collision
E.col_box("Base", (2 * GX + 0.3, 2 * GY + 0.3, Z1 + 0.2), (0, 0, (Z1 - 0.2) / 2))
E.col_box("Upper", (2 * UX + 0.1, 2 * UY + 0.1, U1 - U0 + 0.45), (0.03, 0, (U0 + U1) / 2 + 0.05), (0, 0, 1.2))
import math  # noqa: E402
for sy in (-1, 1):
    run, rise = RY, (ZR + 0.24) - (ZE + 0.24)
    L = math.hypot(run, rise)
    ang = math.degrees(math.atan2(rise, run))
    c = V((0.05, sy * RY / 2, (ZE + ZR) / 2 + 0.24 - 0.25))
    E.col_box("Roof", (2 * RX, L, 0.5), tuple(c), (-sy * ang, 0, 0))
E.col_box("Chimney", (0.8, 0.8, 2.0), tuple(W((CX, CY, 7.3))), (0, 0, 3.0))
E.col_box("Steps", (1.6, 0.6, 0.3), (-0.75, -GY - 0.45, 0.15))

E.check(ASSET, (6, 5, 8), 20000)
rw.finish(ASSET, "env", previews=E.previews())
