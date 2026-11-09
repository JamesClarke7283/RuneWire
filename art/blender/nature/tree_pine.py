"""tree_pine: cartoon pine, about 9.2 m tall.

A straight tapering trunk with four little roots carries five droopy cone tiers whose scalloped
rims hang down in soft lobes. Trunk (M_Bark) + Canopy (M_Leaves__3f8a4a), both with the origin at
the base centre. Collision: one trunk cylinder.
"""
import os
import random
import sys

import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

rw.reset()
rng = random.Random(23)

# --- trunk -----------------------------------------------------------------------------------
ang = nl.root_angles(4, seed=23)
flare = nl.root_shaper(ang, strength=0.45, height=0.8, seed=23, sharp=4.0, foot=0.3)
parts = [nl.sweep("Trunk", [(0, 0, -0.3), (0, 0, 1.0), (0.02, 0, 3.0), (0.04, 0, 6.0), (0.06, 0, 8.4)],
                  [0.42, 0.34, 0.27, 0.18, 0.08], sides=14, per_seg=2, mat="M_Bark", shaper=flare)]
parts += nl.root_sweeps(ang, seed=23, top=0.65, reach=1.0, r_top=0.24, r_tip=0.09, start_r=0.15, depth=-0.25,
                        reach_jitter=0.15, mid=(0.6, 0.45, 0.9, 0.04), taper=(0.75, 0.5))
trunk = rw.join(parts, "Trunk", origin=(0, 0, 0))
nl.fuse(trunk, 0.025, 520, smooth_iters=2)

# --- canopy: five droopy tiers ------------------------------------------------------------------
tiers = [  # z_rim, z_apex, radius, lobes, droop  (each rim overhangs the tier below by 0.3-0.6 m)
    (1.85, 4.8, 2.4, 9, 0.15),
    (3.4, 6.0, 1.98, 8, 0.15),
    (4.85, 7.15, 1.6, 7, 0.15),
    (6.15, 8.15, 1.26, 6, 0.14),
    (7.4, 9.2, 0.92, 5, 0.13),
]
bm = bmesh.new()
for i, (zr, za, R, lobes, droop) in enumerate(tiers):
    lean = 0.03 * i * i                      # the top leans a touch, cartoon-style
    nl.pine_tier_bm(bm, (lean * 0.6, lean * 0.2), zr, za, R, lobes, droop, lobe_amp=0.14,
                    phase=rng.uniform(0, 6.28), seg_per_lobe=6, apex_offset=(0.05 * i, 0.0),
                    tilt=(rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03)))
can = nl.obj_from_bm("Canopy", bm, "M_Leaves__3f8a4a")
nl.fuse(can, 0.04, 2900, smooth_iters=1)

# --- collision -------------------------------------------------------------------------------
rw.collision_cylinder("TrunkCol", 0.36, 3.3, loc=(0, 0, 1.35))

print("RWREPORT   trunk tris %d canopy tris %d" % (nl.tris(trunk), nl.tris(can)))
rw.finish("tree_pine", "nature")
nl.finish_extra("tree_pine", "nature", views=("side", "front"), focus=[("trunk", [trunk], [can], "front34")])
