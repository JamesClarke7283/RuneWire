"""item_health_tonic: round red healing potion, about 0.22 x 0.22 x 0.3 m.

A fat round-bellied bottle, two-thirds full of red tonic (glass M_Glass above the fill line), a short neck with a
brass band and a rolled lip, a chunky cork, a hand-cut parchment label with a red heart on the front,
and a white cartoon glint on the glass. One mesh object "HealthTonic", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_health_tonic"
rw.reset()

# belly (radius 0.11 at z = 0.1), neck from z ~0.19, rolled lip at 0.24
body = [(0.0, 0.0), (0.052, 0.0), (0.086, 0.016), (0.106, 0.052), (0.111, 0.1), (0.1, 0.146), (0.074, 0.18),
        (0.047, 0.198), (0.041, 0.215), (0.041, 0.234)]
lip = [(0.049, 0.238), (0.051, 0.247), (0.046, 0.252), (0.0, 0.252)]
b = il.Bottle(body, lip, fill=0.152, liquid="TonicRed", top="TonicRedTop", segs=28)

# label with a heart, turned a little toward the 3/4 camera
b.label(-18, 0.092, 0.135, 0.08, il.heart_pts(0.056), "HeartRed")
b.shine(-62, 0.135, 0.016, 0.055)
b.shine(-50, 0.172, 0.012, 0.016)

parts = list(b.parts)
# brass band at the base of the neck, cork
parts.append(pl.band("band", 0.05, 0.022, 0.014, (0, 0, 1), (0, 0, 0.205), il.mat("M_Brass"), 16, 0.0))
parts.append(il.cork(0.222, 0.3, 0.035, 0.046, 16))

tonic = rw.join(parts, "HealthTonic")
il.finish_item(ASSET, (0.22, 0.22, 0.3))
