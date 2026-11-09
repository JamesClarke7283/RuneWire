"""item_greater_health_tonic: a big round potion of glowing red tonic, about 0.26 x 0.26 x 0.34 m.

The big brother of item_health_tonic: a larger, fuller round-bellied bottle of glowing red tonic (glass M_Glass
above the fill line) with a gold band studded with gold beads round its belly, a second gold band round its
shoulder, a gold collar on the neck, and instead of a cork a chunky ruby-red heart stopper framed in gold (with a
cartoon glint), sitting on a gold plug. White cartoon glints on the glass.
One mesh object "GreaterHealthTonic", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_greater_health_tonic"
rw.reset()

GOLD = pk.mat("Gold")
red = pk.glow("GreaterRed", "d00a24", 1.0)
red_top = pk.glow("GreaterRedTop", "ff4d64", 1.0)
pk.flat("RubyHeart", "e8193f", 0.25, 0.0)

body = [(0.0, 0.0), (0.06, 0.0), (0.1, 0.017), (0.122, 0.056), (0.126, 0.108), (0.114, 0.155), (0.085, 0.188),
        (0.054, 0.207), (0.046, 0.222), (0.046, 0.236)]
lip = [(0.055, 0.24), (0.057, 0.25), (0.051, 0.255), (0.0, 0.255)]
b = il.Bottle(body, lip, fill=0.172, liquid=red, top=red_top, segs=24)
b.shine(-64, 0.12, 0.018, 0.06)
b.shine(-54, 0.165, 0.013, 0.02)
parts = list(b.parts)

# a beaded gold band round the belly, a gold band round the shoulder and a gold collar on the neck
z = 0.105
r = b.r(z)
parts.append(pl.band("band", r + 0.007, 0.022, 0.012, (0, 0, 1), (0, 0, z), GOLD, 24, 0.0))
for k in range(8):
    a = math.radians(-135 + 45 * k)
    d = V((math.cos(a), math.sin(a), 0))
    parts.append(pl.rivet(d * (r + 0.007) + V((0, 0, z)), d, 0.0068, 0.005, GOLD, 5, "bead"))
z = 0.178
parts.append(pl.band("band", b.r(z) + 0.006, 0.016, 0.011, (0, 0, 1), (0, 0, z), GOLD, 24, 0.0))
parts.append(pl.band("collar", 0.054, 0.02, 0.012, (0, 0, 1), (0, 0, 0.226), GOLD, 16, 0.0))

# gold plug in the neck, then the gold-framed ruby heart stopper standing on it
TOP = 0.255
plug = [(0.0, 0.232), (0.038, 0.232), (0.04, TOP - 0.004), (0.052, TOP + 0.002), (0.052, TOP + 0.01),
        (0.034, TOP + 0.017), (0.024, TOP + 0.024), (0.0, TOP + 0.024)]
parts.append(il.lathe("plug", plug, segs=14, m=GOLD, smooth=40))
HW = 0.096
hh = HW * 27.1 / 32
hc = V((0, 0, TOP + 0.014 + hh / 2))
heart = il.wrap_prism("heart", il.heart_pts(HW, 22), il.plane_map(hc, (1, 0, 0), (0, 0, 1), -0.016, 0.032),
                      pk.mat("RubyHeart"), 40)
rw.add_bevel(heart, 0.009, 2, 50, harden=False)
rim = il.wrap_prism("heart_rim", il.heart_pts(HW * 1.16, 22), il.plane_map(hc + V((0, 0, -0.002)), (1, 0, 0), (0, 0, 1),
                                                                            -0.011, 0.022), GOLD, 40)
rw.add_bevel(rim, 0.005, 1, 50, harden=False)
glint = il.wrap_prism("glint", il.capsule_pts(0.009, 0.022), il.plane_map(hc + V((-HW * 0.25, 0, hh * 0.18)),
                                                                          (1, 0, 0), (0, 0, 1), -0.0175, 0.0015),
                      "Shine")
pk.transform(glint, pk.rot((0, 1, 0), -35, hc + V((-HW * 0.25, 0, hh * 0.18))))
stopper = rw.join([heart, rim, glint], "stopper", origin=(0, 0, 0))
pk.transform(stopper, pk.rot((0, 0, 1), -28))           # turn the heart toward the 3/4 view
parts.append(stopper)

tonic = rw.join(parts, "GreaterHealthTonic")
pk.fit(tonic, 0.34)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.34,))
