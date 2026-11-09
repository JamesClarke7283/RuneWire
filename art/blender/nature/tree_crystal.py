"""tree_crystal: magic tree of the whispering forest, about 6 m tall.

Three pale strands twist around each other into a trunk, then unravel into curving branches;
two more branches split off below. Every branch ends in a big burst of glowing teal crystals
(M_Crystal) instead of leaves, with a tall crown burst in the middle and a few small sprouts along
the limbs. Trunk (pale M_Bark tint) + Canopy (all crystals), both with the origin at the base
centre. Collision: one trunk cylinder.
"""
import math
import os
import random
import sys

import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

BARK = "M_Bark__ece6f7"      # pale, faintly lilac bark
rw.reset()
rng = random.Random(31)

parts = []
ends = []          # (end point, end direction, burst size 0..1)
sprouts = []       # (point, direction) small crystal sprouts on the limbs


def unit(a):
    return Vector((math.cos(a), math.sin(a), 0))


# --- twisted trunk: three strands that unravel into branches ------------------------------------
N = 3
Z0, Z1 = -0.3, 2.45
TURNS = 0.8
for k in range(N):
    pts, rad = [], []
    steps = 7
    for i in range(steps + 1):
        t = i / steps
        z = Z0 + (Z1 - Z0) * t
        a = 2 * math.pi * k / N + TURNS * 2 * math.pi * t
        rh = 0.2 - 0.05 * t
        cx = 0.1 * math.sin(t * math.pi)                 # gentle bow in the trunk
        pts.append(Vector((cx + rh * math.cos(a), rh * math.sin(a), z)))
        rad.append(0.26 - 0.08 * t)
    a_end = 2 * math.pi * k / N + TURNS * 2 * math.pi + 0.3
    out = unit(a_end)
    base = pts[-1]
    reach = (0.9, 1.0, 0.85)[k]
    for (rr, rise), r in zip(((0.5, 0.5), (1.15, 1.05), (1.6, 1.6), (1.8, 2.05)), (0.17, 0.14, 0.12, 0.1)):
        pts.append(base + out * rr * reach + Vector((0, 0, rise)))
        rad.append(r)
    parts.append(nl.sweep("strand%d" % k, pts, rad, sides=10, per_seg=2, mat=BARK))
    ends.append((pts[-1], (pts[-1] - pts[-2]).normalized(), 1.1))
    sprouts.append((pts[-3], (out + Vector((0, 0, 0.4))).normalized()))

# two more branches in the gaps between the strands
for k, (a, z0, reach, top) in enumerate(((math.radians(70), 2.1, 1.55, 1.75), (math.radians(250), 2.25, 1.5, 1.95))):
    out = unit(a)
    p0 = Vector((0.08, 0, z0))
    pts = [p0, p0 + out * 0.45 * reach + Vector((0, 0, 0.55)), p0 + out * 0.95 * reach + Vector((0, 0, 1.2)),
           p0 + out * reach + Vector((0, 0, top))]
    parts.append(nl.sweep("branch%d" % k, pts, [0.16, 0.13, 0.11, 0.09], sides=10, per_seg=3, mat=BARK))
    ends.append((pts[-1], (pts[-1] - pts[-2]).normalized(), 0.95))

# central leader up to the crown burst
crown_pts = [(0.05, 0.0, 1.9), (0.1, -0.05, 3.1), (0.04, -0.08, 4.1), (0.08, -0.1, 4.75)]
parts.append(nl.sweep("leader", crown_pts, [0.18, 0.15, 0.12, 0.1], sides=10, per_seg=2, mat=BARK))
ends.append((Vector(crown_pts[-1]), Vector((0.03, -0.03, 1)).normalized(), 1.35))

# a short side twig low on the trunk with a little burst
twig = [(0.05, 0.05, 1.45), (0.42, -0.28, 1.85), (0.68, -0.5, 2.2)]
parts.append(nl.sweep("twig", twig, [0.12, 0.09, 0.075], sides=8, per_seg=2, mat=BARK))
ends.append((Vector(twig[-1]), (Vector(twig[-1]) - Vector(twig[-2])).normalized(), 0.45))

# flared foot and roots
ang = nl.root_angles(4, seed=31)
flare = nl.root_shaper(ang, strength=0.5, height=0.9, seed=31, sharp=4.0, foot=0.3)
parts.append(nl.sweep("foot", [(0, 0, -0.3), (0.03, 0, 0.5), (0.06, 0, 1.1)], [0.46, 0.38, 0.27], sides=16,
                      per_seg=3, mat=BARK, shaper=flare))
parts += nl.root_sweeps(ang, seed=31, top=0.95, reach=1.1, r_top=0.26, r_tip=0.08, start_r=0.16, depth=-0.3,
                        reach_jitter=0.12, mid="fillet", mat=BARK)
trunk = rw.join(parts, "Trunk", origin=(0, 0, 0))
nl.fuse(trunk, 0.022, 1600, smooth_iters=2)

# --- crystal bursts ----------------------------------------------------------------------------
bm = bmesh.new()
for i, (p, d, s) in enumerate(ends):
    dd = (d + Vector((0, 0, 0.35))).normalized()       # bias the bursts a little upward
    n = 7 if s >= 0.8 else 4
    nl.crystal_cluster_bm(bm, p, dd, n=n, length=(0.6 * s, 1.6 * s), radius=(0.17 * s, 0.33 * s), spread=0.95,
                          seed=100 + i * 7, sink=0.25, min_z=0.05)
for i, (p, d) in enumerate(sprouts):
    nl.crystal_cluster_bm(bm, p, d, n=3, length=(0.3, 0.6), radius=(0.07, 0.12), spread=0.5, seed=300 + i * 5,
                          sink=0.4)
can = nl.obj_from_bm("Canopy", bm, "M_Crystal")
nl.shade_flat_all(can)

# --- collision -------------------------------------------------------------------------------
rw.collision_cylinder("TrunkCol", 0.42, 3.0, loc=(0, 0, 1.2))

print("RWREPORT   trunk tris %d canopy tris %d" % (nl.tris(trunk), nl.tris(can)))
rw.finish("tree_crystal", "nature")
nl.finish_extra("tree_crystal", "nature", views=("side", "front"), focus=[("trunk", [trunk], [can], "front34")])
