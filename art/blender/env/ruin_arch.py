"""ruin_arch: a crumbling stone arch of the Sunken Shrine (6 x 1.2 x 6 m), a gateway the player walks through.

Two piers of stacked, hand-cut pale stone blocks (M_Stone) on chunky plinths, each with a carved course of faint
violet runes (M_RuneGlow) and a moulded impost. Nine wedge voussoirs span the 3.6 m opening; the big keystone stands
proud and carries a glowing rune on both faces, and faint runes line the soffit overhead. The left spandrel still
stands to a broken top, the right one has mostly fallen: one of its voussoirs has slipped, and its blocks lie at the
pier's foot. Painted cracks, moss on every ledge.

Origin at the ground centre; the opening runs along Y (the front faces -Y).
Collision: the piers, four boxes following the arch, the spandrels and the fallen blocks; the opening stays clear.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "ruin_arch"
PL.reset()
PL.preview_glow("M_RuneGlow", "7d4fe0", "a97bff", 1.8)   # previews only (Godot uses its own M_RuneGlow)
rnd = random.Random(4)
P = []
PX = 2.4                 # pier centre x (piers span 1.8 .. 3.0)
ZS = 3.16                # springing line
R1, R2 = 1.8, 2.45       # intrados / extrados radii
D = 1.0                  # voussoir and pier block depth

# ---------------------------------------------------------------- piers
COURSES = [(0.4, 1.02), (1.02, 1.64), (1.64, 2.26), (2.26, 2.88)]
for sx in (-1, 1):
    x = sx * PX
    P.append(PL.rough_block("plinth", (1.2, 1.2, 0.4), (x, 0, 0.2), (0, 0, 0), "M_Stone", 0.06, seed=10 + sx,
                            amt=0.02))
    for k, (z0, z1) in enumerate(COURSES):
        jx = rnd.uniform(-0.03, 0.03)
        jr = rnd.uniform(-1.5, 1.5)
        if sx > 0 and k == 3:
            # the right pier's top course has slipped outward a little
            jx, jr = 0.05, 3.0
        P.append(PL.rough_block("block", (1.06, D, z1 - z0 - 0.02), (x + jx, 0, (z0 + z1) / 2), (0, 0, jr), "M_Stone",
                                0.055, seed=20 + k + 5 * sx, amt=0.025))
    # carved rune course (second course): runes on the front and back, one on the inner face
    zr = (COURSES[1][0] + COURSES[1][1]) / 2
    for sy in (-1, 1):
        for i, key in enumerate(("algiz", "ingwaz") if sx < 0 else ("sowilo", "othala")):
            c = V((x - 0.25 + 0.5 * i, sy * D / 2, zr))
            P += PL.glyph(key, c, (-sy, 0, 0), (0, 0, 1), 0.26, 0.045, 0.024, "M_RuneGlow")
    P += PL.glyph("eye" if sx < 0 else "hagal", (x - sx * 0.53, 0, zr), (0, -sx, 0), (0, 0, 1), 0.28, 0.045, 0.024,
                  "M_RuneGlow")
    # impost (capital) with a moulded lip
    P.append(PL.rough_block("impost", (1.14, 1.08, 0.17), (x, 0, 2.97), (0, 0, 0), "M_Stone", 0.05, seed=30 + sx,
                            amt=0.015))
    P.append(PL.rough_block("impost", (1.2, 1.16, 0.13), (x, 0, 3.1), (0, 0, 0), "M_Stone", 0.045, seed=33 + sx,
                            amt=0.015))

# ---------------------------------------------------------------- voussoirs and keystone
NV = 9
for i in range(NV):
    th0 = math.radians(180.0 * i / NV)
    th1 = math.radians(180.0 * (i + 1) / NV)
    gap = math.radians(0.7)
    a0, a1 = th0 + gap, th1 - gap
    key = i == NV // 2
    r_in, r_out = (R1 - 0.06, R2 + 0.32) if key else (R1, R2)
    pts = [(r_in * math.cos(a0), r_in * math.sin(a0)), (r_out * math.cos(a0), r_out * math.sin(a0)),
           (r_out * math.cos(a1), r_out * math.sin(a1)), (r_in * math.cos(a1), r_in * math.sin(a1))]
    # the polygon must be CCW in (x, z): the order above runs CW for angles increasing CCW, so reverse it
    pts = list(reversed(pts))
    o = E.upright_prism("keystone" if key else "voussoir", pts, D + (0.2 if key else 0.0), 0.0, 0.0, ZS, "M_Stone",
                        0.05)
    if i == 2:
        # the slipped voussoir on the right shoulder (i = 2 sits at 40..60 degrees)
        E.place([o], (0.03, 0.04, -0.07), (0, -4, 0), pivot=(R2 * math.cos(th1), 0, ZS + R2 * math.sin(th1)))
    P.append(o)
# keystone rune on both faces
for sy in (-1, 1):
    P += PL.glyph("othala", (0, sy * (D / 2 + 0.1), ZS + (R1 + R2 + 0.26) / 2), (-sy, 0, 0), (0, 0, 1), 0.42, 0.06,
                  0.026, "M_RuneGlow")
# faint runes on the soffit (underside of the arch), seen when walking through
for i, key in ((1, "kenaz"), (3, "tiwaz"), (5, "fehu"), (7, "sowilo")):
    th = math.radians(180.0 * (i + 0.5) / NV)
    n = V((-math.cos(th), 0, -math.sin(th)))          # points down / inward
    rc = R1 * math.cos(math.radians(90.0 / NV - 0.7))        # the soffit is a flat chord: sit on its middle
    c = V((rc * math.cos(th), 0, ZS + rc * math.sin(th)))
    tan = V((-math.sin(th), 0, math.cos(th)))
    P += PL.glyph(key, c, (0, 1, 0), tan, 0.32, 0.04, 0.022, "M_RuneGlow")

# ---------------------------------------------------------------- spandrels: the left one stands, the right one has fallen


def extr(a_deg, r=R2 + 0.02):
    a = math.radians(a_deg)
    return (r * math.cos(a), ZS + r * math.sin(a))


left_low = [(-2.98, ZS), extr(180), extr(160), (-2.98, ZS + 0.85)]
left_high = [(-2.98, ZS + 0.89), extr(158), extr(138), extr(128), (-2.02, ZS + 2.1), (-2.38, ZS + 2.32),
             (-2.7, ZS + 2.2), (-2.98, ZS + 2.3)]
for pts, seed in ((left_low, 1), (left_high, 2)):
    o = E.upright_prism("spandrel", list(reversed(pts)), D - 0.04, 0.0, 0.0, 0.0, "M_Stone", 0.05)
    P.append(o)
right_low = [(2.98, ZS), (2.98, ZS + 0.55), (2.78, ZS + 0.66), extr(12), extr(0)]
P.append(E.upright_prism("spandrel", list(reversed(right_low)), D - 0.06, 0.0, 0.0, 0.0, "M_Stone", 0.05))

# ---------------------------------------------------------------- fallen blocks and rubble at the right pier's foot
P.append(PL.rough_block("fallen", (0.62, 0.5, 0.42), (1.52, -0.12, 0.21), (0, 0, 24), "M_Stone", 0.05, seed=50,
                        amt=0.04))
P.append(PL.rough_block("fallen", (0.5, 0.42, 0.34), (1.6, 0.34, 0.5), (14, -18, -12), "M_StoneRough", 0.05, seed=51,
                        amt=0.04))
P.append(PL.rough_block("fallen", (0.36, 0.3, 0.26), (-1.55, 0.28, 0.13), (0, 0, -30), "M_StoneRough", 0.04, seed=52,
                        amt=0.03))
for (x, y, r, seed) in ((1.25, -0.42, 0.09, 1), (1.18, 0.1, 0.07, 2), (-1.42, -0.3, 0.07, 3), (1.32, 0.48, 0.06, 4)):
    P.append(PL.pebble((x, y, r * 0.4), r, seed, "M_StoneRough", 0.6))

# ---------------------------------------------------------------- painted cracks
P += PL.crack_face((-2.35, -D / 2, 2.1), (1, 0, 0), (0, 0, 1),
                   [(0.0, 0.0), (0.12, -0.18), (0.05, -0.36), (0.18, -0.55)])
P += PL.crack_face((2.55, -D / 2, 0.85), (1, 0, 0), (0, 0, 1), [(0.0, 0.0), (-0.1, 0.16), (0.02, 0.34)])
P += PL.crack_face((-2.3, D / 2, 1.3), (-1, 0, 0), (0, 0, 1), [(0.0, 0.0), (0.1, 0.2), (0.0, 0.42), (0.14, 0.56)])

# ---------------------------------------------------------------- moss
P += PL.moss((-2.72, -0.32, ZS + 0.02), 0.24, 1, 3, 0.45, spread=0.3)
P += PL.moss((2.74, 0.3, ZS + 0.02), 0.22, 2, 3, 0.45, spread=0.3)
P += PL.moss((-2.42, 0.05, ZS + 2.26), 0.3, 3, 4, 0.45, spread=0.4)
P += PL.moss((-0.3, 0.12, ZS + R2 + 0.33), 0.28, 4, 3, 0.45, spread=0.5)
P += PL.moss((2.74, -0.18, ZS + 0.6), 0.2, 5, 3, 0.45, spread=0.3)
P += PL.moss((-2.45, -0.46, 0.4), 0.2, 6, 3, 0.4, spread=0.3)
P += PL.moss((2.3, 0.46, 0.4), 0.18, 7, 3, 0.4, spread=0.3)
P += PL.moss((1.55, -0.12, 0.43), 0.18, 8, 3, 0.45, spread=0.3)
P += PL.moss((-1.62, 0.3, ZS + R2 * 0.72), 0.16, 9, 2, 0.45, spread=0.3)
# moss hanging over the edges, front and back
for (loc, nrm, n, size, drop, seed) in (((-2.45, -0.48, ZS + 2.24), (0, -1, 0), 4, 0.15, 0.6, 2),
                                        ((-2.72, -0.58, ZS - 0.02), (0, -1, 0), 2, 0.1, 0.25, 3),
                                        ((2.6, 0.58, ZS - 0.02), (0, 1, 0), 3, 0.1, 0.32, 4),
                                        ((-2.7, 0.48, ZS + 2.2), (0, 1, 0), 3, 0.14, 0.5, 6),
                                        ((2.8, -0.47, ZS + 0.58), (0, -1, 0), 2, 0.12, 0.3, 7),
                                        ((-1.98, -0.5, ZS + 1.36), (0, -1, 0), 3, 0.12, 0.36, 8),
                                        ((0.75, 0.5, ZS + 2.36), (0, 1, 0), 2, 0.12, 0.3, 9)):
    P += PL.moss_drape(loc, nrm, n, size, drop, seed)

E.tri_breakdown(P, 16)
E.join(P, "RuinArch")

# ---------------------------------------------------------------- collision
for sx in (-1, 1):
    E.col_box("Pier", (1.24, 1.2, ZS), (sx * PX, 0, ZS / 2))
RM = (R1 + R2) / 2
for k in range(4):
    a0, a1 = math.radians(45 * k), math.radians(45 * (k + 1))
    p0 = (RM * math.cos(a0), 0, ZS + RM * math.sin(a0))
    p1 = (RM * math.cos(a1), 0, ZS + RM * math.sin(a1))
    E.col_beam("Arch", p0, p1, D, R2 - R1 + 0.15, up=(math.cos((a0 + a1) / 2), 0, math.sin((a0 + a1) / 2)), extend=0.2)
E.col_box("Spandrel", (0.55, D, 2.2), (-2.72, 0, ZS + 1.1))
E.col_box("Spandrel", (0.5, D, 0.6), (2.75, 0, ZS + 0.3))
E.col_box("Fallen", (0.7, 1.0, 0.75), (1.55, 0.1, 0.37), (0, 0, 10))

PL.finish(ASSET, (6.0, 1.2, 6.0), 5000)
PL.qa(ASSET, ("front",))
