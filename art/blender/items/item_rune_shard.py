"""item_rune_shard: a glowing violet crystal shard embedded in a broken rune-stone fragment, about 0.4 m.

A chunky angular stone chunk (M_Stone) with clean fracture faces, a deep rune groove with a glowing violet
inlay (M_RuneGlow) carved into its flat front face, and a big faceted violet crystal (M_Crystal__a066ff)
bursting out of its broken top at an angle, with two smaller shards beside it.
One mesh object "RuneShard", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_rune_shard"
rw.reset()

CRY = "M_Crystal__a066ff"
il.preview_glow(CRY, "7d47f2", "a066ff", 0.5)   # preview/icon only: Godot tints its own crystal set

stone = il.hull_rock("stone", (0.34, 0.26, 0.26), (0, 0, 0.13), seed=7, n_points=12, jitter=0.18, rmin=0.92,
                     flat_bottom=0.5, bevel=0.012, m="M_Stone", dissolve_deg=4,
                     cuts=[((0, -0.075, 0), (0, -1, 0.12)), ((0.11, 0, 0), (1, 0.3, 0.25)), ((0, 0, 0.065), (-0.25, 0.3, 1)),
                           ((-0.12, 0.03, 0), (-1, 0.35, -0.1))])
p, n = il.surface_hit(stone, (-0.01, -1.0, 0.13), (0, 1, 0))
print("RWREPORT   rune face hit", tuple(round(x, 3) for x in p), "normal", tuple(round(x, 2) for x in n))
parts = [stone]
parts += il.carve_rune(stone, "othala", p, n, 0.075, 0.018, 0.012)

parts.append(pl.crystal("shard", (-0.01, 0.015, 0.13), (0.3, 0.1, 1), 0.34, 0.064, 6, 0.28, 0.06, il.mat(CRY), 12))
parts.append(pl.crystal("shard", (0.05, 0.0, 0.15), (0.95, -0.2, 0.8), 0.16, 0.038, 6, 0.35, 0.08, il.mat(CRY), 30))
parts.append(pl.crystal("shard", (-0.06, 0.035, 0.15), (-0.75, 0.25, 0.85), 0.13, 0.032, 6, 0.35, 0.08, il.mat(CRY), 5))

shard = rw.join(parts, "RuneShard")
rw.smooth(shard, 25)
il.finish_item(ASSET, (0.33, 0.25, 0.4))
