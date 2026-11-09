"""stump: a cartoon tree stump, about 1.6 x 1.6 m across its roots and 0.56 m tall to the sawn top, above the
game's ground line (z = 0.15).

A squat, slightly tapering trunk (M_Bark, radius 0.4) whose base swells into five root lobes; five fat roots
arch out of the lobes and dive into the ground. The top is a sawn face, tipped a little toward the front: a
raised bark lip around pale end grain (EndGrain) with two stepped growth rings, plus a small two-leaf sprout
growing from it. Moss (Moss) cushions sit on two roots where they leave the trunk.

The game sinks every instance 0.15 m, so the stump is built on that ground line; its flared trunk runs on down to
z = -0.45 and the root tips to about -0.45 too (no gap on slopes). The trunk stays inside the game's 0.45 m
collision sphere (only the low roots reach past it). ONE mesh object, three materials, origin at the base centre.
"""
import math
import os
import sys

import bmesh

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
V = sl.V
ASSET = "stump"
rw.reset()
GL = sl.SINK
bark = rw._resolve_mat("M_Bark")
grain = rw.flat(*sl.END_GRAIN, 0.9)
moss_m = rw.flat(*sl.MOSS, 0.95)

SIDES = 14
Z_TOP = GL + 0.56
TILT = (0.05, -0.1)                                 # dz per metre along x / y: the cut dips toward the front
ANG = nl.root_angles(5, seed=6, jitter=0.25)
flare = nl.root_shaper(ANG, strength=0.3, height=0.42, seed=6, sharp=3.0, ground=GL - 0.04, foot=0.3)

# --- trunk with the worked top -------------------------------------------------------------------------------------
bm = bmesh.new()
rings, _ = nl.sweep_bm(bm, [(0, 0, -0.45), (0, 0, GL - 0.04), (0.005, 0, GL + 0.07), (0.01, 0, GL + 0.19),
                            (0.02, 0.01, GL + 0.36), (0.02, 0.01, Z_TOP)],
                       [0.4, 0.4, 0.4, 0.4, 0.39, 0.37], sides=SIDES, per_seg=1, cap_start=True, cap_end=True,
                       shaper=nl.lumpy_shaper(0.04, 2.0, seed=3, base=flare), up_hint=(1, 0, 0))
top_ring = rings[-1]
for v in top_ring:
    v.co.z += TILT[0] * v.co.x + TILT[1] * v.co.y
top = max((f for f in bm.faces if len(f.verts) == SIDES), key=lambda f: f.calc_center_median().z)
GRAIN_I = 1
grain_faces = []
# bark lip, then the end grain: riser, ring band, riser, ring band
res = bmesh.ops.inset_region(bm, faces=[top], thickness=0.04, depth=0.0, use_even_offset=True)
lip = res["faces"]
for (t, d) in ((0.0, -0.022), (0.085, 0.0), (0.0, -0.016), (0.1, 0.0)):
    res = bmesh.ops.inset_region(bm, faces=[top], thickness=t, depth=d, use_even_offset=True)
    grain_faces += res["faces"]
grain_faces.append(top)
for f in bm.faces:
    f.material_index = 0
for f in grain_faces:
    f.material_index = GRAIN_I
trunk = nl.obj_from_bm("trunk", bm, None)
trunk.data.materials.append(bark)
trunk.data.materials.append(grain)
nl.shade_smooth_all(trunk)
for p in trunk.data.polygons:
    if p.material_index == GRAIN_I:
        p.use_smooth = False
parts = [trunk]

# --- roots: out of the lobes, arching down into the ground --------------------------------------------------------
roots = []
for k, a in enumerate(ANG):
    out = V((math.cos(a), math.sin(a), 0.0))
    reach = (0.86, 0.74, 0.82, 0.7, 0.78)[k]
    pts = [out * 0.24 + V((0, 0, GL + 0.36)), out * 0.5 + V((0, 0, GL + 0.2)), out * reach + V((0, 0, GL + 0.02)),
           out * (reach + 0.1) + V((0, 0, GL - 0.6))]
    r0 = (0.17, 0.15, 0.17, 0.14, 0.16)[k]
    roots.append(sl.tube("root%d" % k, pts, [r0, r0 * 0.88, r0 * 0.66, r0 * 0.45], sides=7, per_seg=1, mat=bark,
                         cap_start=True, cap_end=True, up_hint=(0, 0, 1)))
parts += roots

# --- moss cushions where two roots leave the trunk ------------------------------------------------------------------
moss = []
for k in (0, 2):
    a = ANG[k]
    c = (math.cos(a) * 0.52, math.sin(a) * 0.52)
    m = sl.moss_cushion("moss%d" % k, roots[k], [(c[0], c[1], 0.15, 0.12, 0.09),
                                                (c[0] * 1.28, c[1] * 1.28, 0.1, 0.09, 0.07)],
                        mat=moss_m, voxel=0.025, budget=60, seed=k, sink=0.45)
    if m is not None:
        moss.append(m)
parts += moss

# --- a tiny sprout on the sawn top (Moss green; no sway names, so it stays put) ---------------------------------
bvh = sl.bvh_of(trunk)
sp, _ = sl.drop(bvh, 0.12, -0.1)
bms = bmesh.new()
stem_top = sp + V((0.025, -0.015, 0.17))
nl.sweep_bm(bms, [sp - V((0, 0, 0.02)), sp + V((0.0, 0.0, 0.08)), stem_top], [0.02, 0.018, 0.016], sides=5,
            per_seg=1, cap_start=False, cap_end=True)
sl.leaf_bm(bms, stem_top - V((0, 0, 0.012)), math.radians(20), 0.15, 0.1, rise=0.4, droop=0.35, fold=0.35)
sl.leaf_bm(bms, stem_top - V((0, 0, 0.012)), math.radians(200), 0.12, 0.085, rise=0.4, droop=0.35, fold=0.35)
sprout = nl.obj_from_bm("sprout", bms, moss_m)
nl.shade_flat_all(sprout)
parts.append(sprout)

print("RWREPORT   parts: " + ", ".join("%s %d" % (o.name, sl.tris(o)) for o in parts))
obj = sl.one_mesh(parts, ASSET)
sl.finish(ASSET, obj, 800, max_mats=3, col_r=0.45, ground_z=GL)
if sl.qa_on():
    sl.qa_render(ASSET, "top", (-0.3, -0.5, 1.0), objs=[obj])
sl.qa_extra(ASSET, sink=GL)
