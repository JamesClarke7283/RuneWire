"""rock_b: the blocky slab rock, about 2.1 x 2.0 x 1.75 m above the ground.

A chunky, squarish block of big flat facets with broad chamfers (M_StoneRough): a slanted flat top that rises
toward the back, steep cheeks with cut corners, and a small round companion stone tucked against its front-left
foot. A moss tuft (Moss) sits on the top. Its silhouette (a block with a sloping top and a knuckle at its foot)
reads clearly apart from rock_a's dome and rock_c's split boulder. Solid skirts continue every wall about 1.5 m
below z = 0, so tilted and sunk instances (and rocks on the steep rim slopes) never show a floating edge.
ONE mesh object, origin at the base centre. Collision: none in the model (the game adds a 1.0 m sphere).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
ASSET = "rock_b"
rw.reset()
moss_m = rw.flat(*sl.MOSS, 0.95)

SKIRT = 1.6
block = sl.boulder_bm((2.2, 1.9, 1.7), seed=12, skirt=SKIRT, n_top=16, jitter=0.35, rmin=0.9, shoulder=4.0,
                      plan=3.0, belly=0.22, n_ring=8, foot=0.98, taper=0.92, shear=(0.06, 0.5),
                      cuts=[(268, 70, 0.22), (0, 50, 0.14), (180, 48, 0.15), (90, 52, 0.12), (315, 3, 0.13),
                            (135, 5, 0.11), (225, 2, 0.1), (45, 3, 0.08), (232, 24, 0.17), (305, 34, 0.15)])
main = sl.stone("block", block, bevel=0.08, segments=2, bevel_angle=30, floor=-SKIRT)
pebble = sl.boulder_bm((0.78, 0.68, 0.66), seed=31, n_top=9, jitter=0.4, rmin=0.84, shoulder=2.0,
                       plan=2.0, belly=0.22, n_ring=6, foot=0.95, taper=0.88, cuts=[(30, 62, 0.2), (200, 32, 0.18)],
                       centre=(-0.58, -0.7), spin=25, skirt=1.2)
comp = sl.stone("knuckle", pebble, bevel=0.05, segments=2, bevel_angle=30, floor=-1.2)
moss = sl.moss_pad("moss", main, (0.18, 0.2), 0.34, thick=0.12, mat=moss_m, seed=8, squash=(1.15, 0.9), rot=35,
                   lobes=((3, 0.18), (5, 0.1)), rings=(0.0, 0.35, 0.62, 0.84, 1.0), seg=13, puff=0.35, tuck=0.05,
                   dome=(2.2, 0.6))
print("RWREPORT   parts: block %d, knuckle %d, moss %d tris" % (sl.tris(main), sl.tris(comp), sl.tris(moss)))
obj = sl.one_mesh([main, comp, moss], ASSET)
sl.finish(ASSET, obj, 900, col_r=1.0)
if sl.qa_on():
    sl.qa_render(ASSET, "skirt", (-1, -0.3, 0.1), objs=[obj])
sl.qa_extra(ASSET)
