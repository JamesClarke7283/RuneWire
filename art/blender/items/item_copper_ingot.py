"""item_copper_ingot: two chunky copper ingots stacked crosswise, about 0.25 x 0.25 x 0.11 m.

Trapezoid copper bars (M_Copper) with soft bevels; the top bar has a rounded cartouche pressed into it, its
floor a deep enamel brown (flat), with a raised copper gear emblem (eight chunky teeth round a hole).
One mesh object "CopperIngot", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_copper_ingot"
rw.reset()

parts, floor, u, v = ml.ingot_stack("M_Copper", spin=-12.0, panel=(0.075, 0.056), floor_mat="CopperDeep")
n = u.cross(v)
# raised gear emblem in the cartouche (its top sits just under the bar's top face)
parts.append(il.gear("emblem", 0.0235, 8, 0.0075, 0.0036, 0.0085, floor + n * 0.0018, n, "M_Copper", spin=0))

ingots = rw.join(parts, "CopperIngot")
ml.preview_metals()
il.finish_item(ASSET, (0.25, 0.25, 0.11))
