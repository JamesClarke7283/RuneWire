"""item_iron_ore: a blocky lump of iron ore, about 0.27 x 0.24 x 0.26 m.

A chunky, angular dark blue-grey boulder (M_StoneRough tinted dark blue-grey, with clean fracture faces and a
slanted broken top), crusted with bubbly clusters of round rusty red-brown iron nodules (M_Rust) and two small
shiny dark-metal ones (M_DarkMetal), like cartoon kidney ore. Its blocky silhouette and round nodules set it apart
from the low, nugget-studded item_copper_ore. One mesh object "IronOre", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_iron_ore"
rw.reset()

ROCK = ml.tinted("M_StoneRough", "4b5468")   # dark blue-grey in game and in the previews
C = V((0, 0, 0))
rock = il.hull_rock("rock", (0.3, 0.27, 0.34), C, seed=8, n_points=16, jitter=0.26, rmin=0.86, flat_bottom=0.72,
                    bevel=0.013, m=ROCK, dissolve_deg=5,
                    cuts=[((0, -0.095, 0), (0.15, -1, 0.1)), ((0.11, 0, 0), (1, 0.2, 0.1)),
                          ((0, 0, 0.12), (0.35, -0.3, 1.0))])
parts = [rock]


def cluster(d, r, count, spread, seed, dark=-1):
    """Bubbly crust of round nodules around the surface point in direction d (index `dark` is dark metal)."""
    p0, n0 = ml.on_surface(rock, C, [d])[0]
    u, v, _ = ml.plane_frame(n0, (0, 0, 1) if abs(n0.z) < 0.9 else (0, 1, 0))
    out = []
    rr = random.Random(seed)
    for i in range(count):
        if i == 0:
            off, rad = V((0, 0, 0)), r
        else:
            a = 2 * math.pi * (i - 1) / (count - 1) + rr.uniform(-0.5, 0.5)
            off = (u * math.cos(a) + v * math.sin(a)) * spread * rr.uniform(0.8, 1.15)
            rad = r * rr.uniform(0.5, 0.72)
        hit = ml.on_surface(rock, C, [(p0 + off) - C])
        if not hit:
            continue
        p, n = hit[0]
        m = "M_DarkMetal" if i == dark else "M_Rust"
        out.append(rw.ico("nodule", rad, 2, tuple(p - n * rad * 0.05), (0, 0, rr.uniform(0, 90)), (1, 1, 1), ml.mat(m),
                          None, 70))
    return out


parts += cluster((-0.9, -0.6, -0.1), 0.03, 5, 0.034, 1)
parts += cluster((0.3, -0.55, 0.9), 0.027, 4, 0.03, 2, dark=2)
parts += cluster((0.95, -0.3, -0.1), 0.026, 4, 0.03, 3)
parts += cluster((0.05, -0.97, 0.25), 0.026, 4, 0.03, 4)
parts += cluster((-0.75, 0.55, 0.45), 0.026, 4, 0.03, 5, dark=1)
parts += cluster((0.35, 0.9, -0.1), 0.026, 4, 0.03, 6)
# loose single nodules
for (d, r) in (((-0.35, -0.9, 0.55), 0.017), ((0.75, -0.6, 0.3), 0.016)):
    p, n = ml.on_surface(rock, C, [d])[0]
    parts.append(rw.ico("nodule", r, 2, tuple(p - n * r * 0.1), (0, 0, 0), (1, 1, 1), ml.mat("M_Rust"), None, 70))

ore = rw.join(parts, "IronOre")
ml.preview_metals()
il.finish_item(ASSET, (0.27, 0.24, 0.27))
