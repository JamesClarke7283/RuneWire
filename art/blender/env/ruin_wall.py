"""ruin_wall: a broken wall segment of the Sunken Shrine (6 x 1 x 3 m) with fallen blocks at its foot.

Six courses of hand-cut pale stone blocks (M_Stone, a few M_StoneRough) laid in running bond. The wall stands to
its full height (with cap stones) at the left end and breaks down in steps toward the right, where fallen blocks lie
on the lower courses and at the foot. One block is missing low down, leaving a hole right through. The fourth course
is a carved band of faint violet runes (M_RuneGlow) on both faces. Painted cracks, moss on every step, moss hanging
over the edges and pebbles in the grass. Both faces are finished (the game places these radially, seen from both
sides).

Origin at the ground centre; the wall runs along X, its faces look -Y / +Y.
Collision: stepped boxes following the broken top, plus the fallen blocks.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "ruin_wall"
PL.reset()
PL.preview_glow("M_RuneGlow", "7d4fe0", "a97bff", 1.8)   # previews only (Godot uses its own M_RuneGlow)
rnd = random.Random(21)
P = []
H = 0.47                                                # course height
T = 0.58                                                # wall thickness
XMIN = [-3.0, -2.97, -3.0, -2.95, -3.0, -2.96]
XMAX = [3.0, 2.72, 2.05, 1.3, 0.45, -0.55]
BAND = 3
HOLE = (2, -1.45)                                       # (course, x) of the missing block
RUNES = ["algiz", "sowilo", "ingwaz", "othala", "kenaz", "tiwaz", "fehu", "dagaz", "eye", "hagal"]
seed = 0
for c in range(6):
    z0 = c * H
    x = XMIN[c]
    edges = [x]
    first = (0.5 if c % 2 else 0.9) + rnd.uniform(-0.08, 0.08)
    x += first
    while x < XMAX[c] - 0.35:
        edges.append(x)
        x += rnd.uniform(0.82, 1.08)
    edges.append(XMAX[c])
    for k, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        xm = (a + b) / 2
        if c == HOLE[0] and a < HOLE[1] < b:
            continue
        seed += 1
        last = k == len(edges) - 2 and c > 0
        m = "M_StoneRough" if rnd.random() < 0.2 else "M_Stone"
        rot = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1.5, 1.5) + (4.0 if last else 0.0))
        size = (b - a - 0.035, T + rnd.uniform(-0.03, 0.02), H - 0.03)
        if last:
            size = (size[0] - 0.06, size[1], size[2] - 0.03)
        P.append(PL.rough_block("block", size, (xm + (0.03 if last else 0.0), rnd.uniform(-0.015, 0.015), z0 + H / 2),
                                rot, m, 0.05, seed=seed, amt=0.03 if last else 0.02))
        if c == BAND:
            for sy in (-1, 1):
                P += PL.glyph(RUNES[(k * 2 + (sy > 0)) % len(RUNES)], (xm, sy * (size[1] / 2), z0 + H / 2), (-sy, 0, 0),
                              (0, 0, 1), 0.27, 0.045, 0.024, "M_RuneGlow")

# cap stones on the full-height end
ZT = 6 * H
for (x0, x1, tilt, seed2) in ((-3.0, -2.15, 0.0, 1), (-2.12, -1.3, 1.5, 2), (-1.27, -0.62, -3.0, 3)):
    P.append(PL.rough_block("cap", (x1 - x0 - 0.03, T + 0.14, 0.2), ((x0 + x1) / 2, 0, ZT + 0.1), (0, tilt, 0),
                            "M_Stone", 0.05, seed=100 + seed2, amt=0.02))

# ---------------------------------------------------------------- fallen blocks
P.append(PL.rough_block("fallen", (0.62, 0.46, 0.4), (2.5, 0.0, 2 * H + 0.17), (6, -14, 18), "M_Stone", 0.05, seed=201,
                        amt=0.04))
P.append(PL.rough_block("fallen", (0.5, 0.4, 0.34), (2.72, 0.02, H + 0.19), (-8, 22, -10), "M_StoneRough", 0.05,
                        seed=202, amt=0.04))
P.append(PL.rough_block("fallen", (0.46, 0.18, 0.28), (1.6, -0.39, 0.14), (0, 6, 6), "M_Stone", 0.04, seed=203,
                        amt=0.03))
P.append(PL.rough_block("fallen", (0.4, 0.17, 0.26), (0.4, 0.39, 0.13), (0, -7, -8), "M_StoneRough", 0.04, seed=204,
                        amt=0.03))
P.append(PL.rough_block("fallen", (0.34, 0.16, 0.22), (-2.2, -0.39, 0.11), (0, 9, 10), "M_StoneRough", 0.04, seed=205,
                        amt=0.03))
for (x, y, r, sd) in ((2.15, -0.42, 0.08, 1), (2.9, 0.4, 0.07, 2), (-0.9, 0.42, 0.07, 3), (1.1, -0.43, 0.06, 4),
                      (-2.7, 0.41, 0.06, 5), (0.0, -0.42, 0.05, 6)):
    P.append(PL.pebble((x, y, r * 0.4), r, sd, "M_StoneRough", 0.6))

# ---------------------------------------------------------------- painted cracks
P += PL.crack_face((-2.3, -T / 2, 2.55), (1, 0, 0), (0, 0, 1), [(0.0, 0.0), (0.12, -0.2), (0.04, -0.4), (0.2, -0.62)])
P += PL.crack_face((-0.2, -T / 2, 0.85), (1, 0, 0), (0, 0, 1), [(0.0, 0.0), (-0.14, -0.16), (-0.08, -0.34)])
P += PL.crack_face((0.9, T / 2, 1.5), (-1, 0, 0), (0, 0, 1), [(0.0, 0.0), (0.1, 0.18), (0.0, 0.36), (0.12, 0.52)])
P += PL.crack_face((-1.9, T / 2, 0.4), (-1, 0, 0), (0, 0, 1), [(0.0, 0.0), (-0.1, 0.2), (0.04, 0.38)])

# ---------------------------------------------------------------- moss on the steps, over the edges and at the foot
for c in range(1, 6):
    x = XMAX[c] - 0.22
    P += PL.moss((x, 0.0, (c + 1) * H + 0.01), 0.2, 10 + c, 3, 0.45, spread=0.5)
P += PL.moss((-2.4, 0.05, ZT + 0.21), 0.24, 20, 3, 0.45, spread=0.5)
P += PL.moss((2.85, 0.05, H + 0.01), 0.16, 21, 2, 0.45, spread=0.4)
for (loc, nrm, n, size, drop, sd) in (((-0.75, -T / 2, 5 * H + 0.02), (0, -1, 0), 3, 0.13, 0.42, 1),
                                      ((1.1, T / 2, 4 * H + 0.02), (0, 1, 0), 3, 0.12, 0.38, 2),
                                      ((-2.0, -0.36, ZT + 0.2), (0, -1, 0), 4, 0.13, 0.62, 3),
                                      ((-1.6, 0.36, ZT + 0.2), (0, 1, 0), 3, 0.12, 0.45, 4),
                                      ((1.85, -T / 2, 3 * H + 0.02), (0, -1, 0), 2, 0.11, 0.3, 5),
                                      ((0.3, T / 2, 5 * H + 0.02), (0, 1, 0), 2, 0.12, 0.3, 6)):
    P += PL.moss_drape(loc, nrm, n, size, drop, sd)
for (x, y, r, sd) in ((-2.6, -0.37, 0.12, 30), (0.9, 0.37, 0.12, 31), (-1.0, -0.37, 0.11, 32), (2.4, 0.37, 0.11, 33)):
    P += PL.moss((x, y, 0.02), r, sd, 3, 0.4, spread=0.3)

E.tri_breakdown(P, 16)
E.join(P, "RuinWall")

# ---------------------------------------------------------------- collision: stepped boxes along the broken top
steps = [(-3.0, -0.55, ZT + 0.2), (-0.55, 0.45, 5 * H), (0.45, 1.3, 4 * H), (1.3, 2.05, 3 * H), (2.05, 2.75, 2 * H),
         (2.75, 3.0, H)]
for (x0, x1, h) in steps:
    E.col_box("Wall", (x1 - x0, T + 0.04, h), ((x0 + x1) / 2, 0, h / 2))
E.col_box("Fallen", (0.8, 0.6, 0.42), (2.6, 0.0, 2 * H + 0.2), (0, 0, 15))

PL.finish(ASSET, (6.0, 1.0, 3.0), 5000)
PL.qa(ASSET, ("front",))
