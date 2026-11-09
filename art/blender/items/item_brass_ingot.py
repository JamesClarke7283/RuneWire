"""item_brass_ingot: two chunky golden brass ingots stacked crosswise, about 0.25 x 0.25 x 0.11 m.

Trapezoid brass bars (M_Brass) with soft bevels; the top bar has a rounded cartouche pressed into it, its floor a
deep bronze enamel (flat), with a raised cog emblem (six wide, tapered teeth round a hexagonal hole).
One mesh object "BrassIngot", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_brass_ingot"
rw.reset()

parts, floor, u, v = ml.ingot_stack("M_Brass", spin=-12.0, panel=(0.075, 0.056), floor_mat="BrassDeep")
n = u.cross(v)
# raised cog emblem with a hexagonal hole through to the enamel floor
cog = ml.prism("emblem", ml.cog_pts(0.0245, 0.017, 6, 30), floor, u, v, 0.0036, "M_Brass", sink=0.0005)
hexagon = [(0.0075 * math.cos(math.radians(60 * i)), 0.0075 * math.sin(math.radians(60 * i))) for i in range(6)]
ml.deboss(cog, hexagon, floor + n * 0.0036, u, v, 0.006)
parts.append(cog)

ingots = rw.join(parts, "BrassIngot")
ml.preview_metals()
il.finish_item(ASSET, (0.25, 0.25, 0.11))
