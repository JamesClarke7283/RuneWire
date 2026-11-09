"""rock_a: the small round boulder, about 1.5 x 1.5 x 1.2 m above the ground.

A squat, chunky dome of big flat facets with soft bevels (M_StoneRough): a broad crown, chiselled shoulders and
two flat cheeks, leaning a touch toward +X, with a puffy, lobed moss cushion (Moss) draped over the crown. A solid
skirt continues the walls about 1.45 m below z = 0, so tilted and sunk instances (and rocks on the steep rim
slopes) never show a floating edge. ONE mesh object, origin at the base centre. Collision: none in the model
(the game adds a 0.7 m sphere).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
ASSET = "rock_a"
rw.reset()
moss_m = rw.flat(*sl.MOSS, 0.95)

rock = sl.boulder("rock", (1.62, 1.56, 1.6), seed=7, skirt=1.5, n_top=12, jitter=0.45, rmin=0.84, shoulder=2.0,
                  plan=2.0, belly=0.16, n_ring=7, foot=0.97, taper=0.9, lean=(0.06, 0.0),
                  cuts=[(200, 84, 0.26), (45, 38, 0.2), (165, 42, 0.2), (250, 32, 0.22), (320, 50, 0.16),
                        (95, 2, 0.14), (205, 4, 0.12)],
                  bevel=0.06, segments=2, bevel_angle=30)
moss = sl.moss_pad("moss", rock, (-0.02, 0.04), 0.52, thick=0.15, mat=moss_m, seed=4, squash=(1.0, 0.92), rot=10,
                   lobes=((3, 0.16), (5, 0.1), (7, 0.05)), rings=(0.0, 0.3, 0.55, 0.75, 0.9, 1.0), seg=16,
                   puff=0.35, tuck=0.05, dome=(2.2, 0.6))
print("RWREPORT   parts: rock %d tris, moss %d tris" % (sl.tris(rock), sl.tris(moss)))
obj = sl.one_mesh([rock, moss], ASSET)
sl.finish(ASSET, obj, 600, col_r=0.7)
if sl.qa_on():
    sl.qa_render(ASSET, "skirt", (-1, -0.3, 0.1), objs=[obj])
sl.qa_extra(ASSET)
