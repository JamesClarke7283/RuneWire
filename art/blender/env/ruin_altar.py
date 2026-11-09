"""ruin_altar: the stepped altar platform at the heart of the Sunken Shrine (6 x 6 x 1.2 m). The player stands on it.

Three square tiers of weathered stone (a rough M_StoneRough base, pale M_Stone above) with big cornerstones climb
to a 3.8 m walkable top at 0.98 m; a few blocks have been pushed out of the risers. The top carries a magic circle
inlaid flush with the stone in faint violet M_RuneGlow: three rings, eight runes, four spokes and a central eye. The
middle tier's risers carry rune glyphs, and four short broken pillars with rune collars guard the corners of the
bottom tier. Painted cracks, moss in the corners and hanging over the edges, a fallen pillar drum by one corner.
Symmetric, so it can be approached from any side (the shrine's four arches face it).

Origin at the ground centre.
Collision: a square frustum ramp over the tiers (slope ~42 deg, under the player's 50 deg floor limit, up to the flat
top at 0.98 m) and a cylinder per corner pillar.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "ruin_altar"
PL.reset()
PL.preview_glow("M_RuneGlow", "7d4fe0", "a97bff", 1.8)   # previews only (Godot uses its own M_RuneGlow)
rnd = random.Random(31)
P = []
TIERS = [(3.0, 0.0, 0.34), (2.45, 0.34, 0.68), (1.9, 0.68, 0.98)]   # (half width, z0, z1)
ZT = TIERS[-1][2]
SIDES = [((0, -1, 0), (1, 0, 0)), ((1, 0, 0), (0, 1, 0)), ((0, 1, 0), (-1, 0, 0)), ((-1, 0, 0), (0, -1, 0))]

# ---------------------------------------------------------------- tiers: chamfered slabs with big cornerstones
Q = 0.62                                                            # cornerstone size
sd = 0
for k, (hw, z0, z1) in enumerate(TIERS):
    h = z1 - z0 + (0.0 if k == 0 else 0.03)
    zc = z1 - h / 2
    P.append(PL.rough_block("tier", (2 * hw - 0.04, 2 * hw - 0.04, h), (0, 0, zc), (0, 0, 0.3 * k),
                            "M_StoneRough" if k == 0 else "M_Stone", 0.06, seed=k + 1, amt=0.015))
    for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        sd += 1
        P.append(PL.rough_block("quoin", (Q, Q, h + 0.025), (sx * (hw - Q / 2 - 0.01), sy * (hw - Q / 2 - 0.01), zc + 0.0125),
                                (0, 0, rnd.uniform(-2, 2)), "M_StoneRough" if (sd % 3 == 0) else "M_Stone", 0.06, seed=sd,
                                amt=0.03))
# a few weathered blocks pushed out of the risers
for (n, t, k, off, sd2) in (((0, -1, 0), (1, 0, 0), 0, -1.2, 1), ((1, 0, 0), (0, 1, 0), 0, 0.9, 2),
                            ((0, 1, 0), (-1, 0, 0), 1, 0.6, 3), ((-1, 0, 0), (0, -1, 0), 0, -0.4, 4),
                            ((0, -1, 0), (1, 0, 0), 1, 1.0, 5)):
    n, t = V(n), V(t)
    hw, z0, z1 = TIERS[k]
    o = PL.rough_block("pushed", (0.8, 0.3, z1 - z0 - 0.04), (0, 0, 0), (0, 0, 0), "M_Stone", 0.05, seed=200 + sd2,
                       amt=0.03)
    PL.place_rel([o], n * (hw - 0.17) + t * off + V((0, 0, (z0 + z1) / 2 - 0.01)), t, V((-t.y, t.x, 0.0)), V((0, 0, 1)))
    E.place([o], (0, 0, 0), (0, 0, 3 * (1 if sd2 % 2 else -1)), pivot=tuple(n * hw + t * off))
    P.append(o)

# ---------------------------------------------------------------- rune bands on the middle tier's risers
KEYS = ["algiz", "sowilo", "ingwaz", "othala", "kenaz", "tiwaz", "fehu", "dagaz"]
hw, z0, z1 = TIERS[1]
for s, (n, t) in enumerate(SIDES):
    n, t = V(n), V(t)
    for i, off in enumerate((-1.55, 1.55)):
        c = n * (hw + 0.0) + t * off + V((0, 0, (z0 + z1) / 2))
        P += PL.glyph(KEYS[(2 * s + i) % 8], c, t, (0, 0, 1), 0.22, 0.04, 0.024, "M_RuneGlow")

# ---------------------------------------------------------------- the magic circle on top (flush inlays)
ZI = ZT + 0.003
P.append(PL.hoop("circle", 1.1, 1.19, 0.02, (0, 0, 1), (0, 0, ZI), 32, "M_RuneGlow", 0.0))
P.append(PL.hoop("circle", 0.72, 0.78, 0.02, (0, 0, 1), (0, 0, ZI), 24, "M_RuneGlow", 0.0))
P.append(PL.hoop("circle", 0.2, 0.25, 0.02, (0, 0, 1), (0, 0, ZI), 12, "M_RuneGlow", 0.0))
for i in range(8):
    a = math.radians(22.5 + 45 * i)
    rd = V((math.cos(a), math.sin(a), 0.0))
    tg = V((-math.sin(a), math.cos(a), 0.0))
    P += PL.glyph(KEYS[i], rd * 0.94 + V((0, 0, ZI)), tg, rd, 0.24, 0.04, 0.02, "M_RuneGlow")
for i in range(4):
    a = math.radians(90 * i)
    rd = V((math.cos(a), math.sin(a), 0.0))
    P.append(PL.obox("spoke", (0.48, 0.04, 0.02), tuple(rd * 0.48 + V((0, 0, ZI))), tuple(rd), (0, 0, 1),
                     "M_RuneGlow"))
P += PL.glyph("eye", (0, 0, ZI), (1, 0, 0), (0, 1, 0), 0.28, 0.04, 0.02, "M_RuneGlow")

# ---------------------------------------------------------------- four short broken pillars on the bottom tier corners
PZ = TIERS[0][2]
TOPS = (1.24, 1.02, 1.17, 0.95)
for i, (sx, sy) in enumerate(((1, -1), (1, 1), (-1, 1), (-1, -1))):
    cx, cy = sx * 2.64, sy * 2.64
    base = PL.rough_block("pbase", (0.62, 0.62, 0.16), (cx, cy, PZ + 0.08), (0, 0, rnd.uniform(-4, 4)), "M_Stone", 0.04,
                          seed=60 + i, amt=0.015)
    P.append(base)
    shaft, tops = PL.broken_column("pshaft", PZ + 0.14, TOPS[i] - 0.08, 0.25, 0.235, 8, 2, 0.02, 0.06, seed=70 + i,
                                   high=(sx, sy), high_amt=0.07, levels=2)
    E.place([shaft], (cx, cy, 0))
    P.append(shaft)
    zb = PZ + 0.42
    P.append(E.lathe("pband", [(0.22, zb - 0.08), (0.27, zb - 0.075), (0.28, zb - 0.05), (0.28, zb + 0.05),
                               (0.27, zb + 0.075), (0.22, zb + 0.08)], 10, loc=(cx, cy, 0), m="M_Stone", smooth=40,
                     cap_bottom=False, cap_top=False))
    # a faint rune on the collar, facing out of the corner
    rd = V((sx, sy, 0.0)).normalized()
    P += PL.glyph(KEYS[(3 * i + 1) % 8], V((cx, cy, zb)) + rd * 0.28, (-rd.y, rd.x, 0.0), (0, 0, 1), 0.12, 0.026, 0.016,
                  "M_RuneGlow")
    P += PL.moss((cx - sx * 0.05, cy - sy * 0.05, min(t.z for t in tops) + 0.02), 0.13, 80 + i, 1, 0.45, spread=0.3)
# a fallen drum from the shortest pillar
drum = E.lathe("drum", [(0.0, -0.15), (0.24, -0.15), (0.25, -0.12), (0.25, 0.12), (0.24, 0.15), (0.0, 0.15)], 10,
               m="M_Stone", smooth=40)
E.place([drum], (-2.15, -2.62, PZ + 0.25), (90, 0, 28))
P.append(drum)

# ---------------------------------------------------------------- cracks and moss
P += PL.crack_face((-1.2, -3.0, 0.3), (1, 0, 0), (0, 0, 1), [(0.0, 0.0), (0.1, -0.1), (0.05, -0.22), (0.16, -0.3)])
P += PL.crack_face((2.45, 0.7, 0.62), (0, 1, 0), (0, 0, 1), [(0.0, 0.0), (-0.12, -0.1), (-0.06, -0.22)])
for (x, y, z, r, sd) in ((2.15, 2.15, 0.68, 0.18, 1), (-2.15, -2.15, 0.68, 0.15, 2), (1.6, -1.6, ZT, 0.15, 3),
                         (-1.6, 1.6, ZT, 0.16, 4), (2.72, 0.5, PZ, 0.13, 5), (-0.6, 2.72, PZ, 0.13, 6)):
    P += PL.moss((x, y, z + 0.01), r * 1.3, sd, 3, 0.42, spread=0.45)
for (loc, nrm, n, size, drop, sd) in (((-0.9, -2.45, 0.68), (0, -1, 0), 2, 0.1, 0.22, 1),
                                      ((1.0, 1.9, ZT), (0, 1, 0), 2, 0.1, 0.2, 3),
                                      ((-1.9, 0.9, ZT), (-1, 0, 0), 1, 0.1, 0.18, 4)):
    P += PL.moss_drape(loc, nrm, n, size, drop, sd)

E.tri_breakdown(P, 16)
E.join(P, "RuinAltar")

# ---------------------------------------------------------------- collision
E.col_frustum("Steps", 3.0, 1.9, ZT, (0, 0, ZT / 2), square=True)
for i, (sx, sy) in enumerate(((1, -1), (1, 1), (-1, 1), (-1, -1))):
    E.col_cyl("Pillar", 0.3, TOPS[i], (sx * 2.64, sy * 2.64, TOPS[i] / 2), verts=10)

PL.finish(ASSET, (6.0, 6.0, 1.2), 5000)
PL.qa(ASSET, ("front", "top"))
