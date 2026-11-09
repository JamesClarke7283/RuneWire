"""tree_oak: cartoon broadleaf tree, about 7.9 m tall.

Thick S-curved trunk with five buttress roots that forks into three limbs under a cloud-like
canopy of puffy lumps. Two mesh objects (Trunk: M_Bark, Canopy: M_Leaves), both with the origin
at the base centre so model-space height can drive wind sway. Collision: one trunk cylinder.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

rw.reset()

# --- trunk, roots, limbs (fused into one smooth surface) --------------------------------------
ang = nl.root_angles(5, seed=11)
flare = nl.root_shaper(ang, strength=0.5, height=1.2, seed=11, sharp=4.0, foot=0.3)
parts = [nl.sweep("Trunk", [(0, 0, -0.35), (0.05, 0, 0.7), (0.18, 0.05, 1.6), (0.08, 0.08, 2.5), (-0.05, 0.05, 3.1)],
                  [0.64, 0.56, 0.5, 0.46, 0.39], sides=20, per_seg=3, mat="M_Bark", shaper=flare)]
parts += nl.root_sweeps(ang, seed=11, top=0.95, reach=1.5, r_top=0.36, r_tip=0.13, start_r=0.25, depth=-0.3,
                        reach_jitter=0.15, mid=(0.6, 0.45, 0.9, 0.05), taper=(0.75, 0.5))
limbs = [  # (path, radii): all start inside the trunk and end inside the canopy
    ([(0.02, 0.05, 2.2), (-0.45, 0.1, 3.0), (-1.15, 0.2, 3.75), (-1.75, 0.3, 4.4)], [0.3, 0.24, 0.17, 0.12]),
    ([(0.05, 0.03, 2.3), (0.55, -0.12, 3.05), (1.2, -0.25, 3.8), (1.8, -0.3, 4.5)], [0.3, 0.24, 0.17, 0.12]),
    ([(0.0, 0.05, 2.6), (-0.1, 0.45, 3.4), (-0.2, 0.9, 4.2), (-0.15, 1.3, 4.8)], [0.26, 0.2, 0.15, 0.11]),
    ([(0.0, 0.0, 2.8), (0.15, -0.4, 3.6), (0.3, -0.9, 4.4)], [0.22, 0.17, 0.12]),
]
for i, (pts, rad) in enumerate(limbs):
    parts.append(nl.sweep("limb%d" % i, pts, rad, sides=10, per_seg=3, mat="M_Bark"))
trunk = rw.join(parts, "Trunk", origin=(0, 0, 0))
nl.fuse(trunk, 0.03, 1000, smooth_iters=2)

# --- canopy: lower ring of lumps, upper ring, crown ------------------------------------------
lumps = [
    ((0.1, 0.1, 5.75), (4.0, 3.8, 3.2)),       # core
    ((-2.25, 0.35, 4.75), (2.9, 2.8, 2.5)),    # lower ring
    ((-0.9, -1.85, 4.6), (2.7, 2.6, 2.3)),
    ((1.35, -1.45, 4.55), (2.8, 2.7, 2.35)),
    ((2.3, 0.6, 4.85), (2.8, 2.7, 2.4)),
    ((0.2, 2.0, 4.8), (2.9, 2.6, 2.4)),
    ((-1.0, 0.6, 6.5), (2.8, 2.7, 2.4)),       # upper ring
    ((1.15, -0.5, 6.45), (2.7, 2.6, 2.3)),
    ((0.35, 1.0, 6.6), (2.4, 2.3, 2.1)),
    ((0.15, 0.05, 7.25), (2.2, 2.1, 1.6)),     # crown
]
can = nl.canopy("Canopy", lumps, "M_Leaves", voxel=0.065, target_tris=2700, noise_amt=0.22, noise_size=1.1, seed=5)

# --- collision -------------------------------------------------------------------------------
rw.collision_cylinder("TrunkCol", 0.5, 3.6, loc=(0, 0, 1.45))

print("RWREPORT   trunk tris %d canopy tris %d" % (nl.tris(trunk), nl.tris(can)))
rw.finish("tree_oak", "nature")
nl.finish_extra("tree_oak", "nature", views=("side", "front"), focus=[("trunk", [trunk], [can], "front34")])
