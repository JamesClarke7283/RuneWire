"""bld_arena_wall: one arc segment of the Arena of Echoes ring wall (24 per ring, ~8.6 x 2.5 thick x ~8.6 m).

The ring centre is at Blender (0, -30, 0): the inner face has radius 30 m, the outer face 32.5 m, and the segment
spans 15 degrees (-7.5 .. +7.5). Both ends are cut exactly on the radial planes through the ring centre, and every
continuous layer comes from bldlib.ARENA_LAYERS (shared with bld_arena_gate), so 24 copies rotated 15 degrees apart
about the ring centre close the ring without gaps or overlaps. Half pilasters at each end meet their neighbour's to
make one pilaster per joint.

Inner face (towards the arena, -Y): a blind stone arch with voussoirs, a keystone carved with a glowing rune, a
bronze shield medallion and a hanging lantern; crenellated parapet. On the walkway: a brass ley pylon with a floating
teal crystal. Outer face: arrow slits and a band course. Origin at the ground centre of the inner face.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_arena_wall"
B.reset()
P = []
L = B.Lights()
rnd = random.Random(24)
C = B.ARENA_C
R0, R1, H = B.AR0, B.AR1, B.AHALF

# ---------------------------------------------------------------- shared ring layers and joint pilasters
P += B.arena_band(-H, H)
P += B.arena_half_pilasters(-H, -H + B.APIL)
P += B.arena_half_pilasters(H - B.APIL, H)
# merlons on the inner parapet (one every 7.5 degrees round the ring)
for th in (-3.75, 3.75):
    P.append(E.arc_block("merlon", C, 29.95, 30.6, th - 1.2, th + 1.2, 6.6, 7.08, 1, "M_Stone"))
    P.append(E.arc_block("merloncap", C, 29.9, 30.65, th - 1.3, th + 1.3, 7.06, 7.18, 1, "M_StoneRough"))

# ---------------------------------------------------------------- inner face: blind arch (built flat, then bent onto r = 30)
IN = []
AW, ASP, ARI, VD = 5.0, 3.25, 1.95, 0.46       # arch width, spring height, rise, voussoir depth
NV = 11
ra, rb = AW / 2 + VD / 2, ARI + VD / 2
for i in range(NV):
    phi = math.pi * (i + 0.5) / NV
    xm, zm = ra * math.cos(phi), ASP + rb * math.sin(phi)
    tx, tz = -ra * math.sin(phi), rb * math.cos(phi)
    beta = math.degrees(math.atan2(tz, tx))
    key = i == NV // 2
    size = (0.78, 0.34, VD + 0.26) if key else (0.64, 0.24, VD)
    IN.append(E.stone("vous", size, (xm, -size[1] / 2 + 0.06, zm + (0.08 if key else 0)), (0, -beta, 0),
                      "M_StoneRough" if key or i % 2 else "M_Stone", 0.05, seed=i, jitter=0 if key else 1.5))
for sx in (-1, 1):
    for k in range(4):
        z = 0.72 + (ASP - 0.72) * (k + 0.5) / 4
        wide = k % 2 == 0
        IN.append(E.stone("jamb", (VD + (0.14 if wide else -0.02), 0.22, (ASP - 0.72) / 4 - 0.04), (sx * ra, -0.05, z),
                          (0, 0, 0), "M_Stone" if wide else "M_StoneRough", 0.05, seed=k + 5 * sx, jitter=1.0))
    IN.append(E.rbox("impost", (VD + 0.3, 0.3, 0.22), (sx * ra, -0.09, ASP + 0.02), m="M_StoneRough", r=0.04))
B.ring_bend(IN, R0)
P += IN
# keystone rune, shield medallion, hanging lantern (all on the mid line, so no bending needed)
KZ = ASP + rb + 0.08
P += E.glyph(3, 0.42, (0, -0.32, KZ), (0, -1, 0), "M_RuneGlow", 0.17, 0.05)
P.append(E.disc("medal", 0.82, 0.16, (0, -0.06, 2.45), (0, -1, 0), 20, "M_StoneRough"))
P.append(E.disc("shield", 0.66, 0.1, (0, -0.16, 2.45), (0, -1, 0), 18, "M_Copper"))
P.append(E.ring("shieldrim", 0.67, 0.06, (0, -0.2, 2.45), (0, -1, 0), "M_Brass", 20, 6))
P.append(E.ball("boss", 0.16, (0, -0.24, 2.45), "M_Brass", 10, 6))
P += E.glyph(6, 0.62, (0, -0.22, 2.45), (0, -1, 0), "M_RuneGlow", 0.11, 0.04)
P.append(E.beam("lampbracket", (0, 0.02, 4.72), (0, -0.62, 4.72), 0.08, 0.1, "IronDark", 0.015))
P.append(E.beam("lampbrace", (0, 0.02, 4.32), (0, -0.4, 4.7), 0.06, 0.06, "IronDark", 0.012))
lamp, lc = E.lantern((0, -0.58, 4.68), "hang", scale=1.15)
P += lamp
L.add(lc)
# moss tufts on the inner plinth
for k, x in enumerate((-2.9, 1.6, 3.3)):
    mo = E.moss((x, -0.2, 0.68), 0.32, seed=k, n=3)
    B.ring_bend(mo, R0)
    P += mo

# ---------------------------------------------------------------- outer face: arrow slits, band course, jutting stones
OUT = []
for sx in (-1, 1):
    OUT.append(rw.box("slit", (0.16, 0.08, 1.0), (sx * 1.7, 0.0, 3.6), mat=E.mat("WindowGlow")))
    OUT.append(E.rbox("slitcap", (0.5, 0.2, 0.16), (sx * 1.7, 0.06, 4.18), m="M_StoneRough", r=0.03))
    OUT.append(E.rbox("slitsill", (0.44, 0.2, 0.14), (sx * 1.7, 0.06, 3.04), m="M_StoneRough", r=0.03))
for i in range(5):
    x = rnd.uniform(-3.0, 3.0)
    z = rnd.uniform(1.3, 5.2)
    if abs(abs(x) - 1.7) < 0.5 and 2.8 < z < 4.4:
        continue
    OUT.append(E.stone("jut", (rnd.uniform(0.4, 0.65), 0.18, rnd.uniform(0.22, 0.3)), (x, 0.03, z), (0, 0, 0), "M_Stone", 0.04,
                       seed=i, jitter=3))
B.ring_bend(OUT, R1)
P += OUT
P.append(E.arc_block("band", C, 32.48, 32.64, -H + B.APIL, H - B.APIL, 2.55, 2.75, 5, "M_StoneRough"))

# ---------------------------------------------------------------- brass ley pylon on the walkway
py, pyc = B.ley_pylon(0.0, (30.58 + 32.07) / 2, 6.28, 1.0)
P += py

E.tri_breakdown(P, 24)
main = E.join(P, "ArenaWall")
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit()

# ---------------------------------------------------------------- collision
B.arena_hulls("Wall", -H, H, 29.85, 32.62, -0.2, 6.95, n=3)
E.col_cyl("Pylon", 0.48, 2.3, (pyc[0], pyc[1], 6.28 + 1.0), verts=10)

E.check(ASSET, (8.6, 3.5, 8.6), 8000)
rw.finish(ASSET, "env", previews=E.previews())
