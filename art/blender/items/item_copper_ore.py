"""item_copper_ore: a chunky lump of copper ore, about 0.3 x 0.25 x 0.19 m.

A rounded, big-faceted grey rock (M_StoneRough) studded with chunky bright copper nuggets (M_Copper) bursting
out of its faces, flat copper veins inlaid between them and a scatter of little copper specks.
One mesh object "CopperOre", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_copper_ore"
rw.reset()

C = V((0, 0, 0))
rock = il.hull_rock("rock", (0.33, 0.28, 0.215), C, seed=11, n_points=14, jitter=0.22, rmin=0.88, flat_bottom=0.6,
                    bevel=0.014, m="M_StoneRough", dissolve_deg=8)
parts = [rock]

# chunky nuggets: (direction from the centre, size, seed, spin, sink)
NUGS = [
    ((-0.55, -0.75, 0.45), (0.085, 0.075, 0.085), 3, 10, 0.34),
    ((0.4, -0.8, 0.3), (0.07, 0.064, 0.07), 5, 40, 0.36),
    ((-0.1, -0.15, 1.0), (0.095, 0.085, 0.09), 7, 0, 0.36),
    ((-0.95, 0.05, 0.2), (0.07, 0.065, 0.068), 9, 25, 0.38),
    ((0.8, 0.15, 0.5), (0.078, 0.07, 0.075), 13, 60, 0.36),
    ((0.2, 0.85, 0.45), (0.07, 0.064, 0.07), 17, 15, 0.38),
    ((-0.5, 0.75, 0.5), (0.062, 0.056, 0.06), 19, 70, 0.4),
    ((0.05, -0.55, 0.85), (0.05, 0.046, 0.05), 37, 30, 0.38),
]
for (d, size, seed, spin, sink) in NUGS:
    p, n = ml.on_surface(rock, C, [d])[0]
    parts.append(ml.nugget("nugget", size, p, n, seed, "M_Copper", sink=sink, n_points=10, jitter=0.32, spin=spin))
# little specks
for (d, s, seed) in (((0.05, -0.95, -0.2), 0.034, 21), ((-0.8, -0.5, -0.1), 0.032, 23), ((0.6, -0.4, 0.75), 0.03, 25),
                     ((0.92, -0.25, 0.0), 0.034, 27), ((0.6, 0.65, -0.1), 0.03, 29), ((-0.7, 0.45, -0.05), 0.03, 31),
                     ((-0.3, -0.85, 0.05), 0.028, 33), ((0.35, 0.35, 0.9), 0.03, 35)):
    h = ml.on_surface(rock, C, [d])
    if h:
        parts.append(ml.nugget("speck", (s, s * 0.9, s * 0.85), h[0][0], h[0][1], seed, "M_Copper", sink=0.4,
                               n_points=7))
# flat copper veins inlaid between the nuggets
for (a, b, seed) in (((-0.55, -0.75, 0.45), (0.4, -0.8, 0.3), 1), ((-0.55, -0.75, 0.45), (-0.95, 0.05, 0.2), 2),
                     ((-0.1, -0.15, 1.0), (0.8, 0.15, 0.5), 3), ((-0.95, 0.05, 0.2), (-0.5, 0.75, 0.5), 4),
                     ((0.4, -0.8, 0.3), (0.92, -0.25, 0.0), 5), ((0.2, 0.85, 0.45), (0.8, 0.15, 0.5), 6)):
    parts.append(ml.vein("vein", rock, C, a, b, 0.022, 0.007, 14, "M_Copper", 0.06, seed, 6, 1))

ore = rw.join(parts, "CopperOre")
ml.preview_metals()
il.finish_item(ASSET, (0.3, 0.25, 0.19))
