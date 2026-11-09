"""item_iron_ingot: two chunky grey iron ingots stacked crosswise, about 0.25 x 0.25 x 0.11 m.

Trapezoid iron bars (M_Steel tinted to a darker, neutral iron grey) with soft bevels; the top bar has a rounded
cartouche pressed into it, its floor a near-black enamel (flat), with a raised smithing-hammer emblem set
diagonally.
One mesh object "IronIngot", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_iron_ingot"
rw.reset()

IRON = ml.tinted("M_Steel", "7a8088")   # mid iron grey (plain M_Steel stays the lighter, bluer steel)
parts, floor, u, v = ml.ingot_stack(IRON, spin=-12.0, panel=(0.078, 0.056), floor_mat="IronDeep")
# raised hammer emblem set diagonally, like a smith's mark (its top sits just under the bar's top face)
parts.append(ml.prism("emblem", ml.rot2(ml.hammer_pts(0.062, 0.04), 28), floor, u, v, 0.0036, IRON, sink=0.0005))

ingots = rw.join(parts, "IronIngot")
ml.preview_metals()
il.finish_item(ASSET, (0.25, 0.25, 0.11))
