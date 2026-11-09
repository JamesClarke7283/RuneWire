"""item_iron_tonic: "Ironhide Tonic", a squat steel-banded flask of amber liquid, about 0.24 x 0.24 x 0.28 m.

A wide, squat, round-shouldered flask of amber/orange tonic (glass M_Glass above the fill line) caged by
two riveted steel bands joined by four steel straps, a steel shield badge on the front, a brass neck
band and a stopper shaped like a brass cog with a little knob handle. White glints on the glass.
One mesh object "IronTonic", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_iron_tonic"
rw.reset()

body = [(0.0, 0.0), (0.088, 0.0), (0.111, 0.018), (0.116, 0.066), (0.105, 0.114), (0.072, 0.141), (0.046, 0.152),
        (0.04, 0.176)]
lip = [(0.048, 0.18), (0.05, 0.19), (0.045, 0.195), (0.0, 0.195)]
b = il.Bottle(body, lip, fill=0.124, liquid="IronAmber", top="IronAmberTop", segs=24)
b.shine(-66, 0.11, 0.013, 0.03)
parts = list(b.parts)

# steel cage: two bands, four straps between them, rivets where they cross
Z_BANDS = (0.03, 0.104)
for z in Z_BANDS:
    r = b.r(z)
    parts.append(pl.band("band", r + 0.008, 0.02, 0.015, (0, 0, 1), (0, 0, z), il.mat("M_Steel"), 20, 0.0))
STRAPS = (-52, 52, 128, 232)
zc = (Z_BANDS[0] + Z_BANDS[1]) / 2
for a in STRAPS:
    parts.append(il.wrap_slab("strap", b.map(a, zc, 0.0005, 0.0065), 0.024, Z_BANDS[1] - Z_BANDS[0], 1, 4,
                              "M_Steel", 12.0))
    for z in Z_BANDS:
        d = V((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
        parts.append(pl.rivet(d * (b.r(z) + 0.008) + V((0, 0, z)), d, 0.0085, 0.006, il.mat("M_Brass"), 5))

# shield badge on the front with a rivet boss
parts.append(il.wrap_prism("shield", il.shield_pts(0.05, 0.056), b.map(-14, zc, 0.0008, 0.006), "M_Steel"))
d = V((math.sin(math.radians(-14)), -math.cos(math.radians(-14)), 0))
parts.append(pl.rivet(d * (b.r(zc + 0.005) + 0.006) + V((0, 0, zc + 0.005)), d, 0.011, 0.008, il.mat("M_Brass"), 8))

# neck band, cork plug and the cog stopper with a knob
parts.append(pl.band("neckband", 0.048, 0.016, 0.012, (0, 0, 1), (0, 0, 0.158), il.mat("M_Brass"), 16, 0.0))
parts.append(il.cork(0.168, 0.207, 0.033, 0.036, 10, "CorkDark", 0.1))
parts.append(il.gear("cog", 0.062, 8, 0.016, 0.026, 0.0, (0, 0, 0.217), (0, 0, 1), "M_Brass", spin=11.25))
parts.append(il.lathe("knob", [(0.0, 0.226), (0.024, 0.226), (0.024, 0.234), (0.012, 0.24), (0.011, 0.252),
                               (0.017, 0.256), (0.021, 0.266), (0.017, 0.276), (0.008, 0.28), (0.0, 0.281)], segs=10,
                      m="M_Steel", smooth=60))

tonic = rw.join(parts, "IronTonic")
il.finish_item(ASSET, (0.24, 0.24, 0.28))
