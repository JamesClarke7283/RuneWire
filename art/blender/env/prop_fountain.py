"""prop_fountain: the Emberwick plaza fountain (diameter 6 x 4 m), the centrepiece of the town square at (0, 0).

A round stone basin (M_Stone) on a plinth ring, crowned by sixteen chunky coping stones, with a riveted brass band
and eight brass medallions carrying glowing teal ley runes. It holds a flat glossy water disc at basin height
(rw.flat "Water" 4fb7d9) with lily pads, a pink lotus and a few wishing coins left on the rim. A stout carved column
with a teal rune band rises from a glowing ley ring on the water to an upper bowl; four brass spouts on its lip pour
arcs of water into the basin, each landing in a ring of foam, and a little copper frog on the rim spits a fifth.
From the upper bowl a brass armature (stem, gear collar, glowing emitter cup, four curled claws tied by a brass ring
with copper knuckles, glowing tips) cradles a big floating ley crystal (M_Crystal) with four small orbiting shards.
Nothing touches the crystal.

Origin at the ground centre. Collision: the basin rim only, a ring of 16 boxes (the player can wade in the basin).
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_fountain"
PL.reset()
rnd = random.Random(11)
P = []

RO = 3.0        # coping outer radius (the 6 m footprint)
RI = 2.3        # inner wall radius
ZC = 0.7        # top of the wall = underside of the coping
ZW = 0.64       # basin water level
ZB = 2.0        # upper bowl water level
CZ = 3.13       # crystal centre

# ---------------------------------------------------------------- basin: plinth, wall, coping
P.append(E.lathe("basin", [(2.95, 0.0), (2.98, 0.03), (2.98, 0.15), (2.92, 0.19), (2.84, 0.22), (2.8, 0.42),
                           (2.84, 0.64), (2.86, ZC + 0.02), (RI, ZC + 0.02), (RI, 0.5), (0.0, 0.5)], 40,
                 m="M_Stone", smooth=35, cap_bottom=False))
NCOP = 16
for i in range(NCOP):
    th0 = i * 360.0 / NCOP + 0.7
    th1 = (i + 1) * 360.0 / NCOP - 0.7
    dz = rnd.uniform(-0.012, 0.012)
    dr = rnd.uniform(-0.025, 0.008)
    blk = E.arc_block("coping", (0, 0), RI - 0.05 + dr, RO + dr, th0, th1, ZC, ZC + 0.19 + dz, nu=2, m="M_Stone")
    rw.add_bevel(blk, 0.05, 1, 30, harden=False)
    rw.smooth(blk, 30)
    P.append(blk)

# brass band with rivets just under the coping
P.append(PL.hoop("band", 2.82, 2.885, 0.1, (0, 0, 1), (0, 0, 0.63), 40, "M_Brass", 0.0))
P += PL.rivet_circle((0, 0, 0.63), (0, 0, 1), 2.885, 12, 0.026, 0.015, "M_Brass", 15.0)

# eight brass medallions with teal ley runes, rough stone panels between them
RUNES8 = ("algiz", "sowilo", "ingwaz", "fehu", "othala", "kenaz", "dagaz", "tiwaz")
for i in range(8):
    a = math.radians(i * 45.0 + 22.5)
    n = V((math.cos(a), math.sin(a), 0.0))
    t = V((-math.sin(a), math.cos(a), 0.0))
    c = n * 2.8 + V((0, 0, 0.4))
    P.append(PL.lathe_ax("medal", [(0.0, -0.03), (0.21, -0.03), (0.215, 0.025), (0.17, 0.04), (0.15, 0.022),
                                   (0.0, 0.022)], tuple(n), tuple(c), 12, "M_Brass", 40, False, False))
    P += PL.glyph(RUNES8[i], c + n * 0.024, t, (0, 0, 1), 0.24, 0.05, 0.02, "TealGlow", "medalrune")
    b = math.radians(i * 45.0)
    nb = V((math.cos(b), math.sin(b), 0.0))
    P.append(PL.rough_block("wallstone", (0.66, 0.12, 0.24), tuple(nb * 2.81 + V((0, 0, 0.36 + 0.07 * (i % 2)))),
                            (0, 0, math.degrees(b) + 90), "M_StoneRough", 0.03, seed=i, amt=0.02))

# water, lily pads, a lotus, wishing coins
P.append(PL.flat_disc("water", RI + 0.02, (0, 0, ZW), 40, "Water"))
# a glowing ley ring on the water around the column foot
P.append(PL.hoop("leyring", 0.94, 1.08, 0.014, (0, 0, 1), (0, 0, ZW + 0.006), 28, "TealGlowSoft", 0.0))


def lily(r, ang, size, rot, light=False):
    pts = [(0.0, 0.0)]
    for k in range(11):
        q = math.radians(20 + 320 * k / 10)
        pts.append((size * math.cos(q), size * math.sin(q)))
    o = E.poly_prism("lilypad", pts, 0.025, (0, 0, 0), (0, 0, rot), "LilyPadLight" if light else "LilyPad")
    E.place([o], (r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)), ZW + 0.016))
    return o


P.append(lily(1.7, 25, 0.27, 40))
P.append(lily(1.85, 100, 0.22, 200, True))
P.append(lily(1.7, 190, 0.25, 120))
P.append(lily(1.8, 280, 0.28, 300, True))
P.append(lily(2.02, 300, 0.16, 10))
# lotus on the first pad
lc = V((1.7 * math.cos(math.radians(25)), 1.7 * math.sin(math.radians(25)), ZW + 0.03))
for k in range(6):
    q = 2 * math.pi * k / 6
    d = V((math.cos(q), math.sin(q), 0.0))
    up = (d * 0.6 + V((0, 0, 0.8))).normalized()
    pet = rw.sphere("petal", 0.08, 6, 4, (0, 0, 0), (0, 0, 0), (0.55, 0.38, 1.0), M("LotusPink"))
    PL.align(pet, tuple(up), None, x_hint=(-d.y, d.x, 0))
    E.place([pet], tuple(lc + d * 0.035 + up * 0.065))
    P.append(pet)
P.append(rw.sphere("lotusheart", 0.045, 6, 4, tuple(lc + V((0, 0, 0.05))), (0, 0, 0), (1, 1, 0.7), M("LotusHeart")))
for (r, ang, tilt) in ((2.62, 205, (4, -3)), (2.7, 214, (-3, 2)), (2.6, 77, (-5, 0))):
    P.append(PL.coin((r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)), ZC + 0.2), 0.065, tilt))

# ---------------------------------------------------------------- column and upper bowl
P.append(E.lathe("column", [(0.9, 0.5), (0.9, 0.74), (0.82, 0.8), (0.66, 0.86), (0.56, 0.96), (0.52, 1.08),
                            (0.48, 1.42), (0.52, 1.47), (0.58, 1.5), (0.58, 1.56), (0.5, 1.6), (0.0, 1.6)], 20,
                 m="M_Stone", smooth=40, cap_bottom=False))
P.append(E.ring("collar", 0.53, 0.04, (0, 0, 1.0), (0, 0, 1), "M_Brass", 20, 4))
P += PL.glyph_band((0, 0, 0), 0.5, 1.25, ("algiz", "ingwaz", "sowilo", "othala", "fehu", "kenaz"), 0.26, 0.045,
                   0.024, "TealGlow", 15.0, "colrune")
P.append(E.lathe("bowl", [(0.0, 1.56), (0.52, 1.56), (0.74, 1.66), (0.98, 1.76), (1.16, 1.88), (1.25, 1.96),
                          (1.26, 2.05), (1.19, 2.1), (1.1, 2.08), (1.06, ZB - 0.01), (0.0, ZB - 0.01)], 28,
                 m="M_Stone", smooth=40, cap_bottom=False))
P.append(PL.flat_disc("bowlwater", 1.09, (0, 0, ZB), 28, "Water"))

# four brass spouts pouring arcs of water into the basin
for k in range(4):
    a = math.radians(45 + 90 * k)
    n = V((math.cos(a), math.sin(a), 0.0))
    d = (n + V((0, 0, -0.25))).normalized()
    base = n * 1.15 + V((0, 0, 1.98))
    P.append(PL.lathe_ax("spout", [(0.0, -0.02), (0.1, -0.02), (0.085, 0.1), (0.082, 0.18), (0.12, 0.27),
                                   (0.096, 0.3), (0.06, 0.27), (0.0, 0.27)], tuple(d), tuple(base), 10, "M_Brass",
                         45, False, False))
    mouth = base + d * 0.275
    r0 = mouth.xy.length
    reach = 2.02 - r0
    pts = []
    for s in range(6):
        t = s / 5
        pts.append(tuple(n * (r0 + reach * t) + V((0, 0, mouth.z - 0.25 * reach * t - (mouth.z - 0.25 * reach - ZW - 0.01) * t * t))))
    P.append(E.tube("stream", pts, 0.075, "WaterLight", 2, True, 2, True, taper=(1.0, 1.3)))
    hit = n * 2.02 + V((0, 0, ZW + 0.012))
    P.append(E.ring("foam", 0.17, 0.045, tuple(hit), (0, 0, 1), "Foam", 12, 4))
    P.append(rw.ico("foam", 0.12, 1, tuple(hit + V((0, 0, 0.02))), (0, 0, 0), (1.2, 1.2, 0.55), M("Foam"), None, 40))

# a little verdigris copper frog on the rim, spitting a stream into the basin
FA = 0.0
fn = V((math.cos(FA), math.sin(FA), 0.0))
fs = V((-fn.y, fn.x, 0.0))
frog = [rw.sphere("frog", 0.16, 10, 7, (0, 0, 0.12), (0, 0, 0), (1.05, 1.15, 0.8), PL.mat("M_Copper"))]
frog.append(rw.sphere("frogchin", 0.11, 8, 5, (0, 0.09, 0.075), (0, 0, 0), (1.15, 0.9, 0.6), PL.mat("M_Copper")))
for sx in (-1, 1):
    frog.append(rw.sphere("frogeye", 0.062, 8, 6, (sx * 0.08, 0.07, 0.23), (0, 0, 0), (1, 1, 1), PL.mat("M_Copper")))
    frog.append(rw.sphere("frogeyewhite", 0.044, 8, 4, (sx * 0.087, 0.105, 0.24), (0, 0, 0), (1, 0.6, 1), M("PaintCream")))
    frog.append(rw.sphere("frogpupil", 0.024, 6, 4, (sx * 0.09, 0.127, 0.243), (0, 0, 0), (1, 0.6, 1.25), M("Ink")))
    frog.append(rw.sphere("froghaunch", 0.1, 8, 5, (sx * 0.13, -0.06, 0.07), (0, 0, 0), (0.75, 1.25, 0.7), PL.mat("M_Copper")))
    frog.append(rw.sphere("frogfoot", 0.05, 6, 4, (sx * 0.16, 0.06, 0.018), (0, 0, 0), (1.1, 1.5, 0.4), PL.mat("M_Copper")))
    frog.append(PL.sausage("frogarm", [(sx * 0.08, 0.1, 0.1), (sx * 0.1, 0.15, 0.05), (sx * 0.1, 0.17, 0.02)], 0.028, 6,
                           2, "M_Copper", (True, True), 2))
    frog.append(rw.sphere("froghand", 0.04, 6, 4, (sx * 0.1, 0.18, 0.015), (0, 0, 0), (1.1, 1.3, 0.45), PL.mat("M_Copper")))
frog.append(PL.sausage("froglip", [(-0.075, 0.155, 0.1), (0.0, 0.18, 0.095), (0.075, 0.155, 0.1)], 0.016, 6, 2, "Ink",
                       (True, True), 2))
fbase = fn * 2.64 + V((0, 0, ZC + 0.19))
PL.place_rel(frog, fbase, fs, -fn, (0, 0, 1))
P += frog
mouth = fbase - fn * 0.19 + V((0, 0, 0.1))
pts = []
for s in range(6):
    t = s / 5
    pts.append(tuple(mouth - fn * (0.6 * t) + V((0, 0, 0.12 * t - (0.12 + mouth.z - ZW - 0.01) * t * t))))
P.append(E.tube("spit", pts, 0.035, "WaterLight", 2, True, 2, True, taper=(1.0, 1.4)))
hit = mouth - fn * 0.6
P.append(E.ring("foam", 0.11, 0.032, (hit.x, hit.y, ZW + 0.012), (0, 0, 1), "Foam", 12, 4))

# ---------------------------------------------------------------- brass armature and the floating ley crystal
P.append(E.lathe("stem", [(0.0, ZB - 0.03), (0.24, ZB - 0.03), (0.24, ZB + 0.05), (0.16, ZB + 0.1), (0.14, 2.18),
                          (0.14, 2.24), (0.2, 2.27), (0.33, 2.32), (0.35, 2.37), (0.31, 2.4), (0.24, 2.38),
                          (0.0, 2.38)], 16, m="M_Brass", smooth=45, cap_bottom=False))
P.append(E.disc("emitter", 0.24, 0.012, (0, 0, 2.385), (0, 0, 1), 16, "TealGlow"))
P.append(E.gear("gear", 0.29, 10, 0.06, 0.07, 0.14, (0, 0, 2.15), (0, 0, 1), "M_Brass"))
ARM = [(0.24, 2.3), (0.46, 2.38), (0.66, 2.56), (0.78, 2.86), (0.78, 3.22), (0.68, 3.55), (0.5, 3.74)]
RAD = [0.075, 0.072, 0.068, 0.064, 0.06, 0.055, 0.05]
for k in range(4):
    a = math.radians(90 * k)
    n = V((math.cos(a), math.sin(a), 0.0))
    pts = [n * r + V((0, 0, z)) for (r, z) in ARM]
    P.append(PL.sausage("arm", pts, RAD, 8, 2, "M_Brass", (True, True), 2))
    tip = pts[-1]
    inward = (V((0, 0, CZ + 0.5)) - tip).normalized()
    P.append(PL.lathe_ax("tipcup", [(0.0, -0.02), (0.065, -0.02), (0.075, 0.03), (0.06, 0.05), (0.0, 0.04)],
                         tuple(inward), tuple(tip + inward * 0.03), 8, "M_Brass", 40, False, False))
    P.append(rw.ico("tiporb", 0.055, 1, tuple(tip + inward * 0.1), (0, 0, 0), (1, 1, 1), M("TealGlow"), None, 0))
    P.append(rw.sphere("knuckle", 0.085, 8, 6, tuple(n * 0.78 + V((0, 0, 2.86))), (0, 0, 0), (1, 1, 1),
                       PL.mat("M_Copper")))
P.append(E.ring("brace", 0.78, 0.038, (0, 0, 2.86), (0, 0, 1), "M_Brass", 32, 5))
P.append(E.bipyramid("crystal", 0.44, 0.72, 0.5, 8, (0, 0, CZ), "M_Crystal", twist=22.5, mid=0.36))
for k in range(4):
    a = math.radians(45 + 90 * k)
    n = V((math.cos(a), math.sin(a), 0.0))
    z = CZ + (0.28 if k % 2 else -0.2)
    P.append(E.bipyramid("shard", 0.07, 0.16, 0.11, 6, tuple(n * 0.63 + V((0, 0, z))), "M_Crystal", twist=k * 20))

E.tri_breakdown(P, 24)
E.join(P, "Fountain")

# ---------------------------------------------------------------- collision: the basin rim only
for i in range(16):
    a = math.radians((i + 0.5) * 22.5)
    E.col_box("Rim", (1.12, 0.7, ZC + 0.2), (2.65 * math.cos(a), 2.65 * math.sin(a), (ZC + 0.2) / 2),
              (0, 0, math.degrees(a) + 90))

PL.finish(ASSET, (6.0, 6.0, 4.0), 12000)
PL.qa(ASSET, ("front", "top"))
