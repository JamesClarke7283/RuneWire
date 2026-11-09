"""ruin_pillar: a broken carved column of the Sunken Shrine (1.2 x 1.2 x 5 m).

Weathered pale stone: a two-step square plinth, a round base moulding and a softly fluted, slightly tapering and
leaning shaft that ends in a jagged break (high on one side, a rough fracture surface of M_StoneRough on top). Two
carved bands circle the shaft, each inlaid with faint violet runes (M_RuneGlow). Painted cracks run down the shaft,
chips of fallen stone sit in the plinth corners, and moss cushions sit on the plinth, on the break and creep down one
side of the shaft. Part of the ruin set (ruin_altar, ruin_arch, ruin_wall).

Origin at the ground centre (the game scatters these with a random yaw and a 0.85-1.15 scale).
Collision: a box for the plinth and a cylinder for the shaft.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "ruin_pillar"
PL.reset()
PL.preview_glow("M_RuneGlow", "7d4fe0", "a97bff", 1.8)   # previews only (Godot uses its own M_RuneGlow)
P = []

# ---------------------------------------------------------------- plinth and base moulding
P.append(PL.rough_block("plinth", (1.2, 1.2, 0.34), (0, 0, 0.17), (0, 0, 0), "M_Stone", 0.06, seed=1, amt=0.018))
P.append(PL.rough_block("plinth", (0.98, 0.98, 0.24), (0.01, -0.01, 0.45), (0, 0, 3), "M_Stone", 0.05, seed=2,
                        amt=0.02))
P.append(E.lathe("base", [(0.47, 0.56), (0.5, 0.6), (0.5, 0.66), (0.47, 0.7), (0.43, 0.72), (0.44, 0.76),
                          (0.0, 0.76)], 24, m="M_Stone", smooth=50, cap_bottom=False))

# ---------------------------------------------------------------- fluted shaft with a jagged break
HIGH = (0.6, -0.8)
shaft, tops = PL.broken_column("shaft", 0.74, 4.66, 0.42, 0.37, 12, 4, 0.035, 0.15, seed=3, high=HIGH, high_amt=0.3,
                               levels=4)
LEAN = [shaft]

# ---------------------------------------------------------------- carved rune bands
KEYS = (("algiz", "sowilo", "ingwaz", "othala", "kenaz", "tiwaz", "fehu", "dagaz"),
        ("eye", "hagal", "algiz", "ingwaz", "sowilo", "othala", "kenaz", "tiwaz"))
for k, z in enumerate((1.55, 3.05)):
    r = 0.42 - 0.05 * (z - 0.74) / 3.81 + 0.035
    LEAN.append(E.lathe("band", [(r - 0.07, z - 0.14), (r - 0.01, z - 0.13), (r, z - 0.1), (r, z + 0.1),
                                 (r - 0.01, z + 0.13), (r - 0.07, z + 0.14)], 24, m="M_Stone", smooth=40,
                        cap_bottom=False, cap_top=False))
    LEAN += PL.glyph_band((0, 0, 0), r, z, KEYS[k], 0.17, 0.04, 0.022, "M_RuneGlow", 11.25 + 22.5 * k, "rune")
# painted cracks
LEAN += PL.crack_cyl(0.395, math.radians(200), 2.75, 5, seed=1)
LEAN += PL.crack_cyl(0.4, math.radians(-40), 1.35, 4, seed=2)
LEAN += PL.crack_cyl(0.385, math.radians(95), 4.2, 4, seed=3)

# ---------------------------------------------------------------- moss
P += PL.moss((0.43, -0.41, 0.35), 0.17, 1, 3, 0.4, spread=0.4)
P += PL.moss((-0.47, 0.44, 0.35), 0.17, 2, 3, 0.4, spread=0.4)
P += PL.moss((-0.37, -0.36, 0.58), 0.16, 3, 3, 0.45, spread=0.3)
# chips of fallen stone in the plinth corners
P.append(PL.rough_block("chip", (0.2, 0.15, 0.12), (0.36, 0.37, 0.63), (8, -6, 35), "M_StoneRough", 0.03, seed=5,
                        amt=0.03))
P.append(PL.rough_block("chip", (0.13, 0.11, 0.09), (0.4, 0.25, 0.61), (-5, 10, 70), "M_StoneRough", 0.025, seed=6,
                        amt=0.02))
P.append(PL.rough_block("chip", (0.16, 0.12, 0.1), (-0.5, -0.1, 0.39), (6, 4, 15), "M_StoneRough", 0.025, seed=7,
                        amt=0.02))
# a cushion on the low side of the break, and a trail creeping down that side of the shaft
low = V((-HIGH[0], -HIGH[1], 0.0)).normalized()
ztop = min(t.z for t in tops)
LEAN += PL.moss(tuple(low * 0.18 + V((0, 0, ztop - 0.02))), 0.2, 4, 3, 0.45, spread=0.4)
for i, (z, s) in enumerate(((ztop - 0.12, 0.15), (ztop - 0.42, 0.12), (ztop - 0.72, 0.1), (ztop - 1.0, 0.08),
                            (ztop - 1.22, 0.06))):
    a = math.atan2(low.y, low.x) + 0.25 * math.sin(i * 2.1)
    r = 0.42 - 0.05 * (z - 0.74) / 3.81
    LEAN.append(rw.ico("moss", s, 1, (r * math.cos(a), r * math.sin(a), z), (0, 0, 30 * i), (0.9, 0.6, 1.4),
                       M("Moss" if i % 2 else "MossLight"), None, 40))
# the whole shaft leans a little (about its foot), toward its low side
E.place(LEAN, (0, 0, 0), (-2.2 * low.y, 2.2 * low.x, 0), pivot=(0, 0, 0.74))
P += LEAN

E.tri_breakdown(P, 16)
E.join(P, "RuinPillar")

# ---------------------------------------------------------------- collision
E.col_box("Plinth", (1.2, 1.2, 0.57), (0, 0, 0.285))
E.col_cyl("Shaft", 0.44, ztop - 0.5, (0, 0, 0.5 + (ztop - 0.5) / 2), verts=12)

PL.finish(ASSET, (1.2, 1.2, 5.0), 5000)
PL.qa(ASSET, ("front",))
