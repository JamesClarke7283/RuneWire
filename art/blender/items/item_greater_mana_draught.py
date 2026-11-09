"""item_greater_mana_draught: a tall flask of glowing blue mana, about 0.19 x 0.19 x 0.36 m.

The big brother of item_mana_draught: a tall conical flask (wide rounded base, long tapering body and neck)
filled high with glowing blue mana (glass M_Glass above the fill line), dressed in gold filigree (pairs of scroll
curls front and back between gold bands at the base and the shoulder), a gold collar, and a puffy glowing gold star stopper on a
gold plug. White cartoon glints on the glass. One mesh object "GreaterManaDraught", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_greater_mana_draught"
rw.reset()

GOLD = pk.mat("Gold")
blue = pk.glow("GreaterBlue", "2f6bff", 1.0)
blue_top = pk.glow("GreaterBlueTop", "8fc2ff", 1.0)
star_m = pk.glow("StarStopper", "ffcf3a", 1.2)

ZS = 0.92                                             # squeeze the flask a little to keep it near 0.36 m
body = [(r, z * ZS) for (r, z) in ((0.0, 0.0), (0.07, 0.0), (0.089, 0.014), (0.093, 0.045), (0.087, 0.1),
                                  (0.071, 0.152), (0.052, 0.194), (0.036, 0.226), (0.031, 0.252), (0.031, 0.264))]
lip = [(r, z * ZS) for (r, z) in ((0.039, 0.268), (0.041, 0.278), (0.035, 0.282), (0.0, 0.282))]
b = il.Bottle(body, lip, fill=0.168 * ZS, liquid=blue, top=blue_top, segs=24)
b.shine(-62, 0.08, 0.015, 0.065)
b.shine(-50, 0.175, 0.01, 0.024)
parts = list(b.parts)
FIL = pk.mat("GoldThread")

# gold bands at the base and the shoulder, a collar on the neck
for (z, w) in ((0.028, 0.02), (0.138, 0.016)):
    parts.append(pl.band("band", b.r(z) + 0.006, w, 0.011, (0, 0, 1), (0, 0, z), GOLD, 24, 0.0))
parts.append(pl.band("collar", 0.039, 0.02, 0.011, (0, 0, 1), (0, 0, 0.226), GOLD, 14, 0.0))

# gold filigree between the bands: a mirrored pair of C-scrolls (a little lyre) on the front and on the back


def scroll(size, sgn):
    """C-scroll rising from (0, 0): a stem curving out and up into an inward-curling spiral (mirrored by sgn)."""
    cx, cy, r0 = 0.42 * size, 0.64 * size, 0.3 * size
    pts = [(0.0, 0.0), (0.05 * size, 0.3 * size)]
    for i in range(10):
        t = i / 9
        a = math.pi - 2 * math.pi * 1.05 * t                # clockwise from the spiral's left side
        r = r0 * (1 - 0.72 * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return [(sgn * x, y) for (x, y) in pts]


for ang in (-28, 152):
    M = b.map(ang, 0.042, 0.0035, 0.0)
    for sgn in (-1, 1):
        pts = [V(M(x, y, 0.0)) for (x, y) in scroll(0.08, sgn)]
        parts.append(pl.sausage("filigree", pts, 0.0046, 5, 1, FIL, (True, True), 1, True, 60))
    parts.append(rw.sphere("bead", 0.0085, 8, 5, M(0.0, 0.076, 0.0), mat=FIL))

# gold plug and the puffy star stopper
TOP = 0.282 * ZS
plug = [(0.0, TOP - 0.024), (0.028, TOP - 0.024), (0.03, TOP - 0.002), (0.04, TOP + 0.004), (0.04, TOP + 0.012),
        (0.022, TOP + 0.02), (0.016, TOP + 0.03), (0.0, TOP + 0.03)]
parts.append(il.lathe("plug", plug, segs=12, m=GOLD, smooth=40))
SR = 0.047
sc = V((0, 0, TOP + 0.022 + SR * 0.92))
star = il.wrap_prism("star", il.star_pts(5, SR, SR * 0.5), il.plane_map(sc, (1, 0, 0), (0, 0, 1), -0.014, 0.028),
                     star_m, 40)
rw.add_bevel(star, 0.009, 3, 60, harden=False)
star = rw.join([star], "star", origin=(0, 0, 0))
pk.transform(star, pk.rot((0, 0, 1), -28))
parts.append(star)

flask = rw.join(parts, "GreaterManaDraught")
pk.fit(flask, 0.36)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.36,))
