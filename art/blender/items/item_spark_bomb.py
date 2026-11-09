"""item_spark_bomb: round cartoon bomb, about 0.2 x 0.2 x 0.26 m.

A dark iron ball (M_DarkMetal) strapped with a brass equator band and a brass band over the top, both
riveted; a round brass-rimmed porthole on the front glazed with a faceted glowing teal ley crystal (M_Crystal); a
brass fuse collar on top with a short curly fuse and a fizzing star-burst spark (rw.glow) at its tip.
One mesh object "SparkBomb", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_spark_bomb"
rw.reset()

R = 0.085
parts = [rw.sphere("ball", R, 20, 10, (0, 0, 0), mat="M_DarkMetal")]
brass = il.mat("M_Brass")

# brass bands: around the equator and over the top (in the XZ plane, clear of the front window)
parts.append(pl.band("equator", R + 0.007, 0.026, 0.014, (0, 0, 1), (0, 0, 0), brass, 22, 0.35))
parts.append(pl.band("over", R + 0.007, 0.024, 0.014, (0, 1, 0), (0, 0, 0), brass, 22, 0.35))
for i in range(8):
    a = math.radians(22.5 + 45 * i)
    d = V((math.cos(a), math.sin(a), 0))
    if d.y < -0.8:
        continue                                     # the front porthole sits there
    parts.append(pl.rivet(d * (R + 0.007), d, 0.009, 0.006, brass, 5))
for a in (-50, 25, 155, 230):
    t = math.radians(a)
    d = V((math.cos(t), 0, math.sin(t)))
    parts.append(pl.rivet(d * (R + 0.007), d, 0.009, 0.006, brass, 5))

# porthole on the front, above the equator band, with a glowing ley crystal behind it
el = math.radians(22)
d = V((0, -math.cos(el), math.sin(el)))
c = d * (R - 0.004)
parts.append(rw.torus("bezel", 0.033, 0.0105, 18, 6, (0, 0, 0), mat="M_Brass"))
pl.align(parts[-1], d, c)
parts.append(rw.ico("lens", 0.031, 1, (0, 0, 0), (0, 0, 0), (1, 1, 0.55), "M_Crystal", None, 0))
pl.align(parts[-1], d, c + d * 0.002)
for k in range(4):
    a = math.radians(45 + 90 * k)
    e = pl.frame_matrix(d) @ V((math.cos(a), math.sin(a), 0))
    parts.append(pl.rivet(c + e * 0.033 + d * 0.009, d, 0.006, 0.004, brass, 5))

# fuse collar, curly fuse and the spark
parts.append(il.lathe("collar", [(0.0, R - 0.02), (0.034, R - 0.02), (0.036, R - 0.004), (0.031, R + 0.01),
                                 (0.024, R + 0.014), (0.024, R + 0.022), (0.029, R + 0.025), (0.029, R + 0.034),
                                 (0.0, R + 0.034)], segs=14, m="M_Brass", smooth=40))
fuse = [V((0, 0, R + 0.025)), V((0.004, -0.002, R + 0.048)), V((0.02, -0.006, R + 0.064)), V((0.04, -0.01, R + 0.068))]
parts.append(pl.sausage("fuse", fuse, [0.0095, 0.009, 0.0085, 0.008], 8, 3, il.mat("Twine"), (False, True), 2,
                        True, 60))
parts += il.spark("spark", fuse[-1] + V((0.014, -0.003, 0.008)), 0.03, 8)

bomb = rw.join(parts, "SparkBomb")
il.finish_item(ASSET, (0.2, 0.2, 0.26))
