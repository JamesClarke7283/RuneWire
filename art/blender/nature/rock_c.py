"""rock_c: the big split boulder, about 2.5 x 2.4 x 2.0 m above the ground.

One chunky faceted boulder (M_StoneRough) cracked clean in two: the halves lean apart from a hinge at ground
level so a V-shaped cleft opens at the top, and the smaller half has slumped a little lower, giving an uneven
twin-peak silhouette that reads apart from rock_a's dome and rock_b's block. A small stone is wedged in the
cleft and a moss cushion (Moss) sits on the lower half. Flat facets with soft bevels; the flat crack faces show
inside the cleft. Solid skirts continue the walls about 1.7 m below z = 0, so tilted and sunk instances (and rocks on
the steep rim slopes) never show a floating edge. ONE mesh object, origin at the base centre. Collision: none in
the model (the game adds a 1.2 m sphere).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
V = sl.V
ASSET = "rock_c"
rw.reset()
moss_m = rw.flat(*sl.MOSS, 0.95)

SKIRT = 1.8
CRACK_N = V((0.8, -0.6, 0.0)).normalized()     # the crack plane's normal (halves split along it)
CRACK_O = 0.16                                   # the crack sits this far toward +n from the centre
whole = sl.boulder_bm((2.62, 2.46, 2.4), seed=44, skirt=SKIRT, n_top=16, jitter=0.4, rmin=0.88, shoulder=2.7,
                      plan=2.3, belly=0.22, n_ring=9, foot=0.97, taper=0.9,
                      cuts=[(30, 84, 0.12), (60, 40, 0.15), (150, 35, 0.16), (240, 45, 0.14), (320, 30, 0.15),
                            (100, 0, 0.1), (200, 2, 0.08)])
big_bm, small_bm = sl.split_bm(whole, normal=tuple(CRACK_N), offset=CRACK_O, gap_deg=6.5, drop=(0.0, -0.36),
                               shift=0.03)
big = sl.stone("big", big_bm, bevel=0.065, segments=2, bevel_angle=30, floor=-SKIRT)
small = sl.stone("small", small_bm, bevel=0.065, segments=2, bevel_angle=30, floor=-SKIRT)

# a chockstone wedged in the cleft: dropped into the V until it touches both walls
side = CRACK_N.cross(sl.UP).normalized()
c0 = CRACK_N * (CRACK_O + 0.02) + side * -0.25
bvh_big, bvh_small = sl.bvh_of(big), sl.bvh_of(small)
z = 2.2
while z > 0.4:
    p = V((c0.x, c0.y, z))
    d1 = bvh_big.find_nearest(p)[3]
    d2 = bvh_small.find_nearest(p)[3]
    if d1 is not None and d2 is not None and min(d1, d2) < 0.2:
        break
    z -= 0.02
chock_bm = sl.boulder_bm((0.42, 0.5, 0.36), seed=73, skirt=0.0, n_top=8, jitter=0.4, rmin=0.85, shoulder=2.0,
                         plan=2.0, belly=0.45, n_ring=6, foot=0.8, taper=0.6, cuts=[(0, 60, 0.18)])
chock = sl.stone("chock", chock_bm, bevel=0.03, segments=1, bevel_angle=30)
chock.location = (c0.x, c0.y, z - 0.12)
sl.update()
rw.apply_transform(chock, location=True)

moss = sl.moss_pad("moss", small, tuple(CRACK_N * 0.68 + side * 0.08)[:2], 0.36, thick=0.13, mat=moss_m, seed=6,
                   squash=(1.0, 1.0), rot=20, lobes=((3, 0.18), (5, 0.1), (7, 0.05)),
                   rings=(0.0, 0.32, 0.58, 0.8, 0.93, 1.0), seg=15, puff=0.35, tuck=0.05, dome=(2.2, 0.6))
print("RWREPORT   parts: big %d, small %d, chock %d, moss %d tris; chock at z %.2f" % (
    sl.tris(big), sl.tris(small), sl.tris(chock), sl.tris(moss) if moss else -1, z))
obj = sl.one_mesh([big, small, chock, moss], ASSET)
sl.finish(ASSET, obj, 1200, col_r=1.2)
if sl.qa_on():
    sl.qa_render(ASSET, "skirt", (-1, -0.3, 0.1), objs=[obj])
    sl.qa_render(ASSET, "cleft", tuple(-side + V((0, 0, 0.6))), objs=[obj])
sl.qa_extra(ASSET)
