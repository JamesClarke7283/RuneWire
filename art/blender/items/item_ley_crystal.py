"""item_ley_crystal: a cluster of chunky teal ley crystals on a small mossy rock, about 0.3 x 0.27 x 0.3 m.

A faceted rock base (M_StoneRough) with soft moss cushions (flat greens) and four big faceted teal ley
crystals (M_Crystal) fanning out of it - one tall central spire and three leaning companions - plus a
little sprout of a fifth. One mesh object "LeyCrystal", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_ley_crystal"
rw.reset()

il.preview_glow("M_Crystal", "3ad9c8", "40e8da", 0.5)   # preview/icon only: Godot uses its crystal set

rock = il.hull_rock("rock", (0.3, 0.26, 0.15), (0, 0, 0.06), seed=5, n_points=16, jitter=0.28, rmin=0.86,
                    flat_bottom=0.5, bevel=0.012, m="M_StoneRough")
parts = [rock]
parts += il.moss_on(rock, [(0.095, -0.05), (-0.1, -0.04), (-0.03, 0.085), (0.08, 0.07), (0.0, -0.095)], 0.075, 3)
parts += il.crystal_cluster((0.0, 0.0, 0.1), [
    ((0.06, 0.03, 1.0), 0.24, 0.055, 0),
    ((0.85, -0.4, 0.7), 0.16, 0.042, 25),
    ((-0.8, -0.3, 0.75), 0.145, 0.04, 40),
    ((-0.2, 0.85, 0.7), 0.13, 0.036, 10),
])
parts.append(pl.crystal("sprout", (0.06, -0.06, 0.09), (0.3, -0.9, 0.6), 0.08, 0.024, 6, 0.35, 0.1, il.mat("M_Crystal"), 15))

cl = rw.join(parts, "LeyCrystal")
il.finish_item(ASSET, (0.3, 0.27, 0.3))
