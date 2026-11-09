"""item_fortune_tonic: "Gambler's Fortune", a flat green flask with a lucky clover, about 0.22 x 0.13 x 0.30 m.

A round, flattened flask (a moon-flask, squashed front to back) of glowing emerald-green tonic (glass M_Glass
above the fill line) flecked with gold, a parchment label on the front bearing a four-leaf clover, a brass neck
band, and a cork with a gold coin (embossed with a star) wedged upright into a slot in its top. White glints on
the glass. One mesh object "FortuneTonic", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_fortune_tonic"
rw.reset()

green = pk.glow("FortuneGreen", "1fb84a", 0.9)
green_top = pk.glow("FortuneGreenTop", "8dffa8", 0.9)
GOLD = pk.mat("Gold")

body = [(0.0, 0.0), (0.05, 0.0), (0.09, 0.018), (0.113, 0.06), (0.113, 0.106), (0.096, 0.146), (0.062, 0.172),
        (0.034, 0.188), (0.03, 0.204), (0.03, 0.224)]
lip = [(0.038, 0.228), (0.04, 0.238), (0.034, 0.242), (0.0, 0.242)]
b = il.Bottle(body, lip, fill=0.14, liquid=green, top=green_top, segs=24)
LZ = 0.078
b.label(-10, LZ, 0.1, 0.082, None, None, "Parchment", 0.006, 3, 8, 3)
# four-leaf clover on the label: four heart leaflets and a curved stem
cm = b.map(-10, LZ + 0.006, 0.0015 + 0.0058, 0.004)
for poly in pk.clover_leaves(0.058):
    b.parts.append(il.wrap_prism("clover", poly, cm, pk.mat("Clover"), 30))
stem = [(0.0, 0.0), (0.004, -0.012), (0.01, -0.024), (0.017, -0.032), (0.014, -0.034), (0.006, -0.026),
        (0.0, -0.014), (-0.003, -0.002)]
b.parts.append(il.wrap_prism("stem", stem, cm, pk.mat("Clover"), 30))
b.parts.append(il.wrap_prism("clover_hi", il.ellipse_pts(0.012, 0.012, 10), b.map(-10, LZ + 0.006, 0.0015 + 0.0095, 0.002),
                             pk.mat("CloverLight"), 30))
# gold flecks floating in the tonic (on the glass below the fill line, round the sides and back)
rnd = random.Random(8)
for (ang, z) in ((-48, 0.035), (-62, 0.1), (-42, 0.125), (120, 0.05), (150, 0.11), (175, 0.03)):
    b.parts.append(il.wrap_prism("fleck", il.star_pts(4, 0.009, 0.0035, rnd.uniform(0, 90)),
                                 b.map(ang, z, 0.0012, 0.0025), pk.mat("GoldThread"), 30))
b.shine(-58, 0.105, 0.014, 0.055)
b.shine(-48, 0.168, 0.01, 0.018)
glass = rw.join(list(b.parts), "glass", origin=(0, 0, 0))


def flatten(p):                                      # moon-flask: squash the body front to back, keep the neck round
    t = pk.smoothstep(0.15, 0.19, p.z)
    return V((p.x, p.y * (0.56 + 0.44 * t), p.z))


pk.deform(glass, flatten)
parts = [glass]

# brass neck band and the cork with a gold coin wedged into its top
parts.append(pl.band("band", 0.036, 0.018, 0.011, (0, 0, 1), (0, 0, 0.194), pk.mat("M_Brass"), 14, 0.0))
parts.append(il.cork(0.208, 0.278, 0.026, 0.035, 14))
CZ = 0.287
coin = il.coin("coin", (0, 0, CZ), 0.033, 0.0095, (0, 0, 0), GOLD, 18)
star = il.star_pts(5, 0.016, 0.007)
coin_parts = [coin]
for side in (-1, 1):
    # embossed star on each face (faces look along +-Z before the coin is stood up)
    coin_parts.append(il.wrap_prism("coin_star", star, il.plane_map((0, 0, CZ + side * 0.0045), (side, 0, 0), (0, 1, 0),
                                                                    0.0, 0.0022), GOLD, 30))
coin = rw.join(coin_parts, "coin", origin=(0, 0, CZ))
pk.transform(coin, pk.rot((0, 0, 1), -28, (0, 0, CZ)) @ pk.rot((1, 0, 0), 90, (0, 0, CZ)))
parts.append(coin)

tonic = rw.join(parts, "FortuneTonic")
pk.fit(tonic, 0.30)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.30,))
