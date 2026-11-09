"""prop_race_ring: a Valley Rally rune ring (diameter 9 m, 1 m thick), flown through at speed high over the valley.

The ring stands upright in the XZ plane; its opening faces -Y / +Y (the game yaws it to face the next ring). A
chunky brass hoop (inner face at 4.1 m, outer at 4.48 m) wraps a glowing teal ley band that forms the 4 m inner
radius and stands proud of both faces, so the ring reads as a glowing circle head-on and as a glowing band from the
side. Twelve teal runes run around each face, and four copper clamp housings on the diagonals carry big teal lenses
front and back. Symmetric front / back, so it reads the same from either side.

Origin at the ring centre (exception: not the ground). No collision (the game checks the distance to the centre).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_race_ring"
PL.reset()
P = []
AX = (0, 1, 0)
R_IN, R_HOOP, R_OUT = 4.0, 4.08, 4.48
HD = 0.38                                 # half depth of the brass hoop


def radial(a):
    return V((math.cos(a), 0.0, math.sin(a)))


def tangent(a):
    return V((-math.sin(a), 0.0, math.cos(a)))


# ---------------------------------------------------------------- hoop and glowing ley band
P.append(PL.hoop("hoop", R_HOOP, R_OUT, 2 * HD, AX, (0, 0, 0), 40, "M_Brass", 0.12))
P.append(PL.hoop("leyband", R_IN, R_HOOP + 0.04, 2 * HD + 0.1, AX, (0, 0, 0), 40, "TealGlow", 0.0))

# ---------------------------------------------------------------- runes around both faces
RC = 4.28                                 # rune centre line on the flat part of each face
for j in range(12):
    a = math.radians(67.5 + 22.5 * (j % 3) + 90 * (j // 3))
    key = PL.RUNE_KEYS[j % len(PL.RUNE_KEYS)]
    for sy in (-1, 1):
        c = radial(a) * RC + V((0, sy * HD, 0))
        u = -tangent(a) if sy < 0 else tangent(a)
        P += PL.glyph(key, c, u, radial(a), 0.22, 0.065, 0.026, "TealGlow", "rune")

# ---------------------------------------------------------------- copper clamp housings with teal lenses
for k in range(4):
    a = math.radians(45 + 90 * k)
    rd, tg = radial(a), tangent(a)
    c = rd * ((R_IN - 0.03 + 4.5) / 2)
    P.append(PL.obox("clamp", (0.62, 0.92, 4.5 - R_IN + 0.03), tuple(c), tuple(tg), tuple(rd), "M_Copper", 0.06, 1))
    for sy in (-1, 1):
        lc = rd * 4.24 + V((0, sy * 0.465, 0))
        P.append(E.ring("bezel", 0.17, 0.03, tuple(lc), AX, "M_Brass", 12, 4))
        P.append(E.disc("lens", 0.15, 0.05, tuple(lc), AX, 12, "TealGlow"))
    # brass straps where the clamp grips the hoop
    for s in (-1, 1):
        P.append(PL.obox("strap", (0.06, 0.96, 4.5 - R_IN + 0.01), tuple(c + tg * (s * 0.33)), tuple(tg), tuple(rd),
                         "M_Brass", 0.02, 1))

E.tri_breakdown(P, 20)
E.join(P, "RaceRing")
PL.finish(ASSET, (9.0, 1.0, 9.0), 4000, origin_note="(origin = ring centre)")
PL.qa(ASSET, ("front", "side"))
