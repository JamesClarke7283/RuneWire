"""bush_flower: a puffy flowering bush, about 1.5 x 1.5 x 1.2 m above the game's ground line (z = 0.15).

A taller, rounder cloud of leafy lumps than bush_round (M_Leaves) dotted with small cartoon blossoms: pink
five-petal flowers with golden eyes and golden flowers with pink eyes, cupped and turned toward the light, on
the upper two thirds of the bush. vegetation.gd sinks every instance 0.15 m, so the bush is built on that
ground line and its foliage runs on down to z = -0.45 (open underneath, never seen): no gap on slopes.

Sway: the blossoms use leaf-class names (FoliageBloomPink / FoliageBloomGold contain "foliage" but not
grass/flower/petal), so material_library.gd gives them exactly the same tiny wind sway as M_Leaves and they never
drift off the bush; the double-sided foliage shader also lets the petals be single quads. ONE mesh object, three
materials, origin at the base centre. No collision (vegetation.gd gives bushes none).
"""
import math
import os
import random
import sys

import bmesh

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
V = sl.V
ASSET = "bush_flower"
rw.reset()
GL = sl.SINK                                   # the game's ground line (every instance is sunk 0.15 m)
rng = random.Random(8)
pink = rw.flat("FoliageBloomPink", "ff6fbf", 0.6)
gold = rw.flat("FoliageBloomGold", "ffd23c", 0.6)

lumps = [
    ((0.0, 0.0, 0.65), (1.0, 0.98, 1.08)),        # core
    ((0.0, 0.0, 0.18), (1.3, 1.26, 0.72)),        # foot (runs below the ground line)
    ((0.4, -0.16, 0.46), (0.62, 0.6, 0.6)),       # belly ring
    ((0.3, 0.36, 0.50), (0.6, 0.6, 0.6)),
    ((-0.2, 0.42, 0.46), (0.6, 0.58, 0.58)),
    ((-0.44, 0.0, 0.50), (0.62, 0.6, 0.6)),
    ((-0.12, -0.42, 0.48), (0.6, 0.6, 0.58)),
    ((0.16, -0.2, 0.94), (0.6, 0.58, 0.56)),      # upper ring
    ((0.18, 0.24, 0.96), (0.56, 0.56, 0.54)),
    ((-0.26, 0.02, 0.94), (0.58, 0.56, 0.54)),
    ((0.0, 0.02, 1.16), (0.48, 0.46, 0.4)),       # crown
    ((0.0, 0.0, -0.2), (1.12, 1.08, 0.7)),        # skirt: hidden on flat ground, fills the gap on slopes
]
bush = nl.canopy("bush", lumps, "M_Leaves", voxel=0.035, target_tris=1000, noise_amt=0.1, noise_size=0.55,
                 seed=33, smooth_iters=2, subdiv=3)
nl.clip_below(bush, -0.45)

# --- blossoms: dropped onto the upper part of the bush ------------------------------------------------------------
bvh = sl.bvh_of(bush)
hits = sl.surface_points(bush, (0.0, 0.0, 0.52), sl.fib_dirs(22, zmin=-0.1, seed=5, jitter=0.3), bvh)
bm_p, bm_g = bmesh.new(), bmesh.new()          # pink petals + pink eyes / gold petals + gold eyes
for i, (p, n) in enumerate(hits):
    if p.z < GL + 0.3:
        continue
    face = (n + V((0, 0, 0.5))).normalized()    # turned a little toward the sky
    is_pink = (i % 5) not in (1, 3)
    R = rng.uniform(0.095, 0.11) if is_pink else rng.uniform(0.078, 0.09)
    centre = p + face * 0.022
    petals, eyes = (bm_p, bm_g) if is_pink else (bm_g, bm_p)
    sl.bloom_bm(petals, eyes, centre, face, R=R, rc=R * 0.36, n_petals=5, cup=0.22, spin=rng.uniform(0, 6.28),
                petal_w=0.92, eye_h=0.7, back=False, cheap=True)
bloom_p = nl.obj_from_bm("bloom_pink", bm_p, pink)
bloom_g = nl.obj_from_bm("bloom_gold", bm_g, gold)
for o in (bloom_p, bloom_g):
    nl.shade_flat_all(o)
print("RWREPORT   parts: bush %d, pink %d, gold %d tris; %d blossoms" % (
    sl.tris(bush), sl.tris(bloom_p), sl.tris(bloom_g), sum(1 for p, n in hits if p.z >= GL + 0.3)))
obj = sl.one_mesh([bush, bloom_p, bloom_g], ASSET)
sl.finish(ASSET, obj, 1600, max_mats=3, ground_z=GL)
if sl.qa_on():
    sl.qa_render(ASSET, "close", (-0.6, -1.0, 0.5), target=(0.0, -0.2, 0.75), radius=0.45, objs=[obj])
sl.qa_extra(ASSET, sink=GL)
