"""flower_patch: a small cluster of cartoon wildflowers, about 0.45 x 0.45 x 0.45 m above the game's ground
line (z = 0.15).

Six flowers on gently curving stems fan out from one spot: four pink five-petal blooms with golden eyes and two
golden ones with pink eyes, cupped and tilted up toward the light at different heights, each stem carrying a
pointed leaf, and a small green sepal cup sits under each head. vegetation.gd sinks every instance 0.15 m, so
the flowers are built on that ground line (z = 0.15) and their stems run on down to z = -0.25 (no gap on
slopes). No collision.

Sway: every part (FlowerStem for stems and leaves, FlowerPink, FlowerGold) contains "flower", so
material_library.gd gives the whole patch the same small-plant wind sway (a few cm at the top) and the heads stay
on their stems; the double-sided foliage shader lets the petals and leaves be single-sided. ONE mesh object,
three materials, origin at the base centre.
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
ASSET = "flower_patch"
rw.reset()
rng = random.Random(4)
stem_m = rw.flat("FlowerStem", "5aa63a", 0.8)
pink_m = rw.flat("FlowerPink", "ff6fbf", 0.6)
gold_m = rw.flat("FlowerGold", "ffd23c", 0.6)
GL = sl.SINK                                   # the game's ground line (every instance is sunk 0.15 m)

# (azimuth deg, base radius, head height, lean (outward reach of the head), head radius, pink?)
FLOWERS = [
    (15, 0.02, 0.4, 0.05, 0.08, True),
    (80, 0.04, 0.31, 0.12, 0.072, False),
    (145, 0.04, 0.35, 0.11, 0.078, True),
    (210, 0.05, 0.27, 0.14, 0.068, False),
    (270, 0.04, 0.33, 0.12, 0.076, True),
    (330, 0.05, 0.25, 0.15, 0.07, True),
]
bm_stem, bm_pink, bm_gold = bmesh.new(), bmesh.new(), bmesh.new()
for i, (az, r0, h, lean, R, is_pink) in enumerate(FLOWERS):
    a = math.radians(az + rng.uniform(-6, 6))
    out = V((math.cos(a), math.sin(a), 0.0))
    base = out * r0 * 0.6 + V((0, 0, -0.25))
    head = out * (r0 + lean) + V((0, 0, GL + h))
    face = (out * 0.75 + V((0, 0, 1.0))).normalized()
    neck = head - face * 0.03
    pts = [base, out * r0 + V((0, 0, GL)), out * (r0 + lean * 0.06) + V((0, 0, GL + h * 0.25)),
           out * (r0 + lean * 0.4) + V((0, 0, GL + h * 0.62)), neck]
    nl.sweep_bm(bm_stem, pts, [0.016, 0.016, 0.015, 0.013, 0.012], sides=3, per_seg=1, cap_start=False,
                cap_end=False, phase=rng.uniform(0, 6.28))
    # a green sepal cup under the head (hides where the stem meets the petals)
    M3 = sl.frame(face)
    ring = [bm_stem.verts.new(head + M3 @ V((R * 0.42 * math.cos(k * 2 * math.pi / 5),
                                             R * 0.42 * math.sin(k * 2 * math.pi / 5), -0.004))) for k in range(5)]
    tipv = bm_stem.verts.new(head - face * 0.035)
    for k in range(5):
        bm_stem.faces.new((ring[(k + 1) % 5], ring[k], tipv))
    # one broad leaf from the stem, about halfway up, swinging out to one side
    lp = out * (r0 + lean * 0.2) + V((0, 0, GL + h * 0.4))
    sl.leaf_bm(bm_stem, lp, a + rng.choice((-1, 1)) * rng.uniform(0.7, 1.2), 0.15, 0.075, rise=0.35, droop=0.35,
               fold=0.3, tilt=rng.uniform(-0.3, 0.3))
    petals, eyes = (bm_pink, bm_gold) if is_pink else (bm_gold, bm_pink)
    sl.bloom_bm(petals, eyes, head, face, R=R, rc=R * 0.38, n_petals=5, cup=0.28, spin=rng.uniform(0, 6.28),
                petal_w=0.95, eye_h=0.8, back=False, cheap=True)
stems = nl.obj_from_bm("stems", bm_stem, stem_m)
pinks = nl.obj_from_bm("pinks", bm_pink, pink_m)
golds = nl.obj_from_bm("golds", bm_gold, gold_m)
nl.shade_smooth_all(stems)
for o in (pinks, golds):
    nl.shade_flat_all(o)
print("RWREPORT   parts: stems+leaves %d, pink %d, gold %d tris" % (sl.tris(stems), sl.tris(pinks), sl.tris(golds)))
obj = sl.one_mesh([stems, pinks, golds], ASSET)
sl.finish(ASSET, obj, 400, max_mats=3, ground_z=GL)
if sl.qa_on():
    sl.qa_render(ASSET, "sunk", (-0.75, -1.0, 0.4), objs=[obj])
sl.qa_extra(ASSET, sink=GL)
