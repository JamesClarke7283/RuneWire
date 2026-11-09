"""prop_beacon: the Skyward Beacon (diameter 2 x 3 m), a goal marker floating 40 m above the Builder's Flats.

A tall faceted ley crystal (M_Crystal, 2.9 m tip to tip) with a glowing teal core band, held at the centre of an
armillary sphere of chunky brass rings: two upright rings crossing at the poles, where brass collars clasp the
crystal, and a slightly tilted equator ring with glowing teal studs, tied together by riveted copper clamps. Four
small crystal shards hang between the rings. The silhouette (a glowing spike through a sphere of rings) reads from far
away, and nothing sticks out sideways, so it spins cleanly about its vertical axis (the game spins and bobs the whole
model, and adds a teal light at its centre).

Origin at the beacon's centre (exception: not the ground). No collision (the game checks the distance to the centre).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_beacon"
PL.reset()
P = []
RR = 0.89                 # ring centre-line radius
RW = 0.09                 # ring half radial thickness
RD = 0.16                 # ring width (along its axis)
HT = 1.35                 # crystal pyramid heights (each)
MID = 0.3
CR = 0.46                 # crystal radius


def crystal_r(z):
    """Crystal radius at height z (8-sided bipyramid centred on the origin)."""
    t = max(0.0, abs(z) - MID / 2) / HT
    return CR * (1.0 - t)


# ---------------------------------------------------------------- the crystal and its core band
P.append(E.bipyramid("crystal", CR, HT, HT, 8, (0, 0, 0), "M_Crystal", twist=22.5, mid=MID))
P.append(PL.hoop("coreband", CR - 0.03, CR + 0.05, 0.12, (0, 0, 1), (0, 0, 0), 8, "TealGlow", 0.0))
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    P.append(PL.obox("bandrib", (0.06, 0.04, 0.2), ((CR + 0.05) * math.cos(a), (CR + 0.05) * math.sin(a), 0),
                     (0, 0, 1), (math.cos(a), math.sin(a), 0), "M_Brass", 0.012))

# ---------------------------------------------------------------- brass rings
# two upright rings crossing at the poles (planes at 45 and 135 degrees)
for ph in (45, 135):
    a = math.radians(ph)
    n = (-math.sin(a), math.cos(a), 0.0)
    P.append(PL.hoop("gyro", RR - RW, RR + RW, RD, n, (0, 0, 0), 40, "M_Brass", 0.3))
# the equator ring, slightly tilted (it wobbles as the beacon spins)
eq = PL.hoop("equator", RR - RW, RR + RW, RD, (0, 0, 1), (0, 0, 0), 40, "M_Brass", 0.3)
E.place([eq], (0, 0, 0), (12, 0, 0))
P.append(eq)
EQ_TILT = math.radians(12)


def eq_point(a, r):
    """Point on the tilted equator ring at angle a (about Z before the tilt), radius r."""
    x, y = r * math.cos(a), r * math.sin(a)
    return V((x, y * math.cos(EQ_TILT), y * math.sin(EQ_TILT)))


for k in range(8):
    a = math.radians(22.5 + 45 * k)
    if k % 2 == 0:
        continue
    P.append(rw.ico("stud", 0.07, 2, tuple(eq_point(a, RR + RW - 0.01)), (0, 0, 0), (1, 1, 1), M("TealGlow"), None,
                    60))
# copper clamps where the upright rings cross the equator
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = eq_point(a, 1.0).normalized()
    c = eq_point(a, RR)
    P.append(PL.obox("clamp", (0.26, 0.3, 0.22), tuple(c), (0, 0, 1), tuple(d), "M_Copper", 0.04))
    P.append(PL.rivet(tuple(c + d * 0.11), tuple(d), 0.04, 0.02, "M_Brass", 8))
# pole collars clasping the crystal where the upright rings cross
for sz in (1, -1):
    z = sz * (RR - 0.02)
    r = crystal_r(z)
    P.append(PL.hoop("collar", r - 0.01, r + 0.09, 0.18, (0, 0, 1), (0, 0, z), 12, "M_Brass", 0.3))
    P.append(PL.hoop("collarband", r + 0.07, r + 0.11, 0.07, (0, 0, 1), (0, 0, z), 12, "M_Copper", 0.0))

# ---------------------------------------------------------------- hanging shards between the rings
for k in range(4):
    a = math.radians(90 * k)
    d = V((math.cos(a), math.sin(a), 0))
    z = 0.4 if k % 2 else -0.36
    P.append(E.bipyramid("shard", 0.08, 0.2, 0.14, 6, tuple(d * 0.68 + V((0, 0, z))), "M_Crystal", twist=15 * k))

E.tri_breakdown(P, 16)
E.join(P, "Beacon")
PL.finish(ASSET, (2.0, 2.0, 3.0), 4000, origin_note="(origin = beacon centre)")
PL.qa(ASSET, ("front",))
