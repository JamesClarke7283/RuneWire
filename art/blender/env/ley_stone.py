"""ley_stone: a ley standing stone (1.2 x 0.8 x 3.5 m) that players touch to attune it for fast travel.

A chunky, slightly leaning, pot-bellied menhir of cool blue-grey rough stone (M_StoneRough tinted) with a slanted,
rounded top, planted in a rough plinth slab.
Big teal ley glyphs are inlaid down its front, two more on its back and one on each side, linked by little glowing
studs. A riveted brass band hugs its shoulders, and a mini ley crystal (M_Crystal) floats above the top inside a faint
teal halo with two orbiting shards. Moss and a few pebbles soften the plinth.

Origin at the ground centre; the front faces -Y (the game yaws it randomly and adds a teal light 2.5 m up).
Collision: a convex hull around the stone and a box for the plinth.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "ley_stone"
PL.reset()
rnd = random.Random(7)
P = []
STONE = "M_StoneRough__a9b4c2"
N = 13

# ---------------------------------------------------------------- the menhir
# (z, half width X, half depth Y)
SECT = [(0.1, 0.43, 0.265), (0.22, 0.455, 0.278), (0.5, 0.468, 0.285), (0.9, 0.462, 0.28), (1.3, 0.44, 0.27),
        (1.7, 0.41, 0.255), (2.05, 0.38, 0.24), (2.3, 0.35, 0.222), (2.5, 0.31, 0.2), (2.65, 0.23, 0.155),
        (2.73, 0.12, 0.085)]
TOP = 2.77
PH = [rnd.uniform(0, 6.28) for _ in range(3)]


def lean(z):
    return 0.06 * (z / TOP) ** 2


def wob(a):
    return 0.045 * math.sin(3 * a + PH[0]) + 0.03 * math.sin(5 * a + PH[1]) + 0.02 * math.sin(2 * a + PH[2])


def slant(x, z):
    """Slanted top: the last rings rise toward +X."""
    return 0.15 * max(0.0, (z - 2.35) / 0.38) * x / 0.33


def section(z):
    for (z0, w0, d0), (z1, w1, d1) in zip(SECT[:-1], SECT[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return E.lerp(w0, w1, t), E.lerp(d0, d1, t)
    return SECT[-1][1], SECT[-1][2]


rings = []
for (z, w, d) in SECT:
    pts = PL.ring_pts(N, w, d, z, (lean(z), 0.0), 2.5, 0.0, wob)
    rings.append([(x, y, zz + slant(x - lean(z), zz)) for (x, y, zz) in pts])
stone = PL.loft("menhir", rings, STONE, cap_bottom=False, cap_top=True, smooth_angle=34,
                top_point=(lean(TOP) + 0.03, 0.0, TOP + 0.04))
P.append(stone)
P.append(PL.rough_block("plinth", (1.16, 0.76, 0.17), (0, 0, 0.085), (0, 0, 2), STONE, 0.045, seed=3, amt=0.025))

# ---------------------------------------------------------------- teal ley glyphs (projected onto the stone)
GLYPHS = [((0, -1, 0), 0.68, "algiz", 0.44), ((0, -1, 0), 1.3, "ingwaz", 0.4), ((0, -1, 0), 1.86, "sowilo", 0.36),
          ((0, 1, 0), 0.95, "othala", 0.42), ((0, 1, 0), 1.65, "kenaz", 0.38),
          ((-1, 0, 0), 1.25, "tiwaz", 0.32), ((1, 0, 0), 1.25, "fehu", 0.32)]
for (tw, z, key, size) in GLYPHS:
    P += PL.glyph_on(stone, key, tw, z, size, 0.085, 0.05, "TealGlow", name="rune", x=lean(z))
# glowing studs linking the front glyphs
for z in (0.99, 1.58, 2.08):
    hit = PL.surface_hit(stone, V((lean(z), -3.0, z)), (0, 1, 0))
    if hit:
        P.append(rw.ico("stud", 0.04, 1, tuple(hit[0]), (0, 0, 0), (1, 1, 1), M("TealGlow"), None, 60))

# ---------------------------------------------------------------- riveted brass band on the shoulders
ZB0, ZB1 = 2.14, 2.27
band_rings = []
for z in (ZB0, ZB1):
    w, d = section(z)
    band_rings.append(PL.ring_pts(N, w + 0.035, d + 0.035, z, (lean(z), 0.0), 2.5, 0.0, wob))
P.append(PL.loft("band", band_rings, "M_Brass", True, True, 40))
for i in range(6):
    a = 2 * math.pi * (i + 0.5) / 6
    w, d = section((ZB0 + ZB1) / 2)
    zm = (ZB0 + ZB1) / 2
    p = PL.ring_pts(1, w + 0.035, d + 0.035, zm, (lean(zm), 0.0), 2.5, a, wob)[0]
    nrm = V((p[0] - lean(zm), p[1] * (w / d) ** 2, 0.0)).normalized()
    P.append(PL.rivet(p, tuple(nrm), 0.028, 0.016, "M_Brass", 6))

# ---------------------------------------------------------------- the floating mini crystal
CX, CZ = lean(TOP) + 0.02, 3.15
P.append(E.bipyramid("crystal", 0.15, 0.33, 0.2, 6, (CX, 0, CZ), "M_Crystal", twist=15, mid=0.1))
halo = E.ring("halo", 0.27, 0.014, (0, 0, 0), (0, 0, 1), "TealGlowSoft", 24, 4)
E.place([halo], (CX, 0, CZ - 0.02), (14, -8, 0))
P.append(halo)
for (ang, z, s) in ((40, CZ - 0.12, 1.0), (220, CZ + 0.1, 0.8)):
    a = math.radians(ang)
    P.append(E.bipyramid("shard", 0.04 * s, 0.09 * s, 0.06 * s, 5, (CX + 0.36 * math.cos(a), 0.36 * math.sin(a) * 0.6, z),
                         "M_Crystal", twist=ang))

# ---------------------------------------------------------------- moss and pebbles on the plinth
for (x, y, r, seed) in ((-0.4, -0.22, 0.16, 1), (0.38, 0.22, 0.17, 2), (0.42, -0.25, 0.1, 3), (-0.36, 0.25, 0.12, 4)):
    P += PL.moss((x, y, 0.17), r, seed, 3, 0.45, spread=0.4)
P += PL.moss((lean(2.35) - 0.22, -0.12, 2.3), 0.11, 5, 2, 0.5, spread=0.4)
for (x, y, r, seed) in ((0.47, -0.27, 0.07, 1), (-0.48, 0.05, 0.065, 2), (0.15, -0.32, 0.05, 4)):
    P.append(PL.pebble((x, y, 0.17 + r * 0.35), r, seed, STONE, 0.65))

E.tri_breakdown(P, 16)
E.join(P, "LeyStone")

# ---------------------------------------------------------------- collision: a hull around the stone
hull = []
for k in (0, 3, 6, 8, 10):
    hull += rings[k][::2]
E.col_hull("Stone", hull + [(lean(TOP), 0.0, TOP + 0.04)])
E.col_box("Plinth", (1.16, 0.76, 0.17), (0, 0, 0.085), (0, 0, 2))

PL.finish(ASSET, (1.2, 0.8, 3.5), 3000)
PL.qa(ASSET, ("front", "side"))
