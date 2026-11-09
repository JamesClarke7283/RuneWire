"""tree_oak_small: young cartoon broadleaf tree, about 4.7 m tall.

Slimmer, gently leaning trunk with four little roots, three limbs and a rounder canopy of seven
puffy lumps. Same node layout as tree_oak: Trunk (M_Bark) + Canopy (M_Leaves), both with the
origin at the base centre. Collision: one trunk cylinder.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

rw.reset()

# --- trunk, roots, limbs -------------------------------------------------------------------
ang = nl.root_angles(4, seed=7)
flare = nl.root_shaper(ang, strength=0.45, height=0.75, seed=7, sharp=4.0, foot=0.3)
parts = [nl.sweep("Trunk", [(0, 0, -0.3), (0.03, 0.0, 0.5), (0.12, 0.03, 1.15), (0.1, 0.05, 1.75), (0.0, 0.05, 2.2)],
                  [0.4, 0.33, 0.29, 0.27, 0.22], sides=16, per_seg=3, mat="M_Bark", shaper=flare)]
parts += nl.root_sweeps(ang, seed=7, top=0.6, reach=0.95, r_top=0.22, r_tip=0.09, start_r=0.15, depth=-0.25,
                        reach_jitter=0.15, mid=(0.6, 0.45, 0.9, 0.04), taper=(0.75, 0.5))
limbs = [
    ([(0.08, 0.04, 1.5), (-0.25, 0.08, 2.05), (-0.7, 0.15, 2.55), (-1.05, 0.2, 2.95)], [0.18, 0.14, 0.1, 0.08]),
    ([(0.1, 0.04, 1.6), (0.45, -0.08, 2.15), (0.85, -0.15, 2.6), (1.1, -0.2, 3.0)], [0.18, 0.14, 0.1, 0.08]),
    ([(0.05, 0.05, 1.85), (0.0, 0.3, 2.45), (-0.05, 0.6, 2.95)], [0.15, 0.11, 0.08]),
]
for i, (pts, rad) in enumerate(limbs):
    parts.append(nl.sweep("limb%d" % i, pts, rad, sides=10, per_seg=3, mat="M_Bark"))
trunk = rw.join(parts, "Trunk", origin=(0, 0, 0))
nl.fuse(trunk, 0.022, 700, smooth_iters=2)

# --- canopy ----------------------------------------------------------------------------------
lumps = [
    ((0.05, 0.05, 3.35), (2.7, 2.6, 2.3)),     # core
    ((-1.2, 0.25, 2.85), (1.9, 1.85, 1.65)),   # lower ring
    ((-0.25, -1.15, 2.75), (1.85, 1.8, 1.6)),
    ((1.15, -0.3, 2.9), (1.9, 1.8, 1.65)),
    ((0.35, 1.1, 2.9), (1.85, 1.8, 1.6)),
    ((-0.45, 0.2, 4.05), (1.8, 1.75, 1.5)),    # top
    ((0.55, -0.2, 4.0), (1.7, 1.65, 1.45)),
]
can = nl.canopy("Canopy", lumps, "M_Leaves", voxel=0.045, target_tris=1900, noise_amt=0.14, noise_size=0.8, seed=17)

# --- collision -------------------------------------------------------------------------------
rw.collision_cylinder("TrunkCol", 0.3, 2.5, loc=(0, 0, 0.95))

print("RWREPORT   trunk tris %d canopy tris %d" % (nl.tris(trunk), nl.tris(can)))
rw.finish("tree_oak_small", "nature")
nl.finish_extra("tree_oak_small", "nature", views=("side", "front"), focus=[("trunk", [trunk], [can], "front34")])
