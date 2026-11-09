"""item_mana_draught: tall blue mana potion, about 0.18 x 0.18 x 0.3 m.

A tall teardrop flask: a round bulb tapering into a long neck, filled with softly glowing blue mana
(glass M_Glass above the fill line, a lighter glowing surface shows through it), a parchment label with
a yellow star, a brass neck band, a cork sealed with a dark-blue wax cap that drips down its sides, and
white cartoon glints. One mesh object "ManaDraught", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_mana_draught"
rw.reset()

body = [(0.0, 0.0), (0.056, 0.0), (0.08, 0.016), (0.089, 0.056), (0.083, 0.098), (0.064, 0.132), (0.044, 0.158),
        (0.033, 0.184), (0.03, 0.212), (0.03, 0.23)]
lip = [(0.038, 0.234), (0.04, 0.244), (0.035, 0.249), (0.0, 0.249)]
b = il.Bottle(body, lip, fill=0.122, liquid="ManaBlue", top="ManaBlueTop", segs=24)
b.label(-18, 0.06, 0.1, 0.072, il.star_pts(5, 0.03, 0.013), "StarYellow")
b.shine(-64, 0.08, 0.014, 0.05)
b.shine(-48, 0.168, 0.01, 0.03)

parts = list(b.parts)
parts.append(pl.band("band", 0.04, 0.02, 0.013, (0, 0, 1), (0, 0, 0.196), il.mat("M_Brass"), 16, 0.0))
parts.append(il.cork(0.222, 0.288, 0.026, 0.036, 16))
# dark-blue wax cap over the cork top, with three drips
wax = [(0.0, 0.268), (0.0385, 0.268), (0.0405, 0.276), (0.0405, 0.289), (0.034, 0.298), (0.0, 0.3)]
parts.append(il.lathe("wax", wax, segs=16, m="ManaWax", smooth=50))
for k, (a, L) in enumerate(((-40, 0.022), (75, 0.014), (190, 0.018))):
    d = V((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
    top = d * 0.0395 + V((0, 0, 0.271))
    parts.append(pl.capsule("drip", top, top + V((0, 0, -L)) + d * 0.002, 0.0072, 6, 2, il.mat("ManaWax")))

flask = rw.join(parts, "ManaDraught")
il.finish_item(ASSET, (0.18, 0.18, 0.3))
