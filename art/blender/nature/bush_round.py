"""bush_round: a puffy cartoon bush, about 1.5 x 1.5 x 1.15 m above the game's ground line (z = 0.15).

A cloud of round leafy lumps (M_Leaves, the same set as the oak canopy) fused into one soft surface: a wide
belly ring of lumps, a smaller upper ring and a crown, slightly lopsided so the scalloped silhouette reads from
every side. vegetation.gd sinks every instance 0.15 m, so the bush is built on that ground line and its foliage
runs on down to z = -0.45 (open underneath, never seen): no gap under the downhill edge on slopes.
ONE mesh object, ONE material, origin at the base centre. No collision (vegetation.gd gives bushes none).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
ASSET = "bush_round"
rw.reset()
GL = sl.SINK                                   # the game's ground line (every instance is sunk 0.15 m)

lumps = [
    ((0.0, 0.0, 0.66), (1.08, 1.04, 0.95)),       # core
    ((0.0, 0.0, 0.26), (1.42, 1.36, 0.72)),       # foot (runs below the ground line)
    ((0.43, 0.1, 0.54), (0.66, 0.64, 0.6)),       # belly ring
    ((0.14, 0.44, 0.52), (0.64, 0.62, 0.58)),
    ((-0.3, 0.34, 0.56), (0.66, 0.64, 0.6)),
    ((-0.44, -0.1, 0.50), (0.62, 0.6, 0.56)),
    ((-0.18, -0.42, 0.54), (0.64, 0.62, 0.58)),
    ((0.28, -0.35, 0.50), (0.62, 0.6, 0.56)),
    ((0.2, 0.08, 0.92), (0.58, 0.56, 0.52)),      # upper ring
    ((-0.2, 0.18, 0.94), (0.56, 0.54, 0.5)),
    ((-0.04, -0.22, 0.90), (0.56, 0.54, 0.5)),
    ((0.03, 0.02, 1.13), (0.44, 0.42, 0.38)),     # crown
    ((0.0, 0.0, -0.2), (1.12, 1.08, 0.7)),        # skirt: hidden on flat ground, fills the gap on slopes
]
bush = nl.canopy("bush", lumps, "M_Leaves", voxel=0.035, target_tris=1150, noise_amt=0.1, noise_size=0.55,
                 seed=21, smooth_iters=2, subdiv=3)
nl.clip_below(bush, -0.45)
obj = sl.one_mesh([bush], ASSET)
sl.finish(ASSET, obj, 1200, max_mats=1, ground_z=GL)
sl.qa_extra(ASSET, sink=GL)
