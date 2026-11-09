"""cliff_a: a big layered rock formation, about 10 x 6 x 8 m above the ground (ASSET_SPEC Batch D).

A mesa of chunky stacked strata (soft-bevelled slabs, walls leaning in a touch, the beds dipping ~2 degrees):
thick, jutting grey beds (M_StoneRough) alternate with thin, recessed sandstone bands (M_StoneRough__ffd2a6).
Above a broad base it rises into two towers, a tall one toward +X (8 m) and a squat one toward -X with a saddle
between, so the silhouette (seen from the map's middle, 240-300 m away) is a stepped twin-peak butte rather than
a box. Vertical joints notch the walls and every ledge steps in or out. Moss (Moss) caps the two tower tops and
the saddle; two fallen blocks lean on the base's ends. The base continues 9 m below z = 0 and flares out a
little: the game sinks cliffs 1.5 m, tilts them up to 11.5 degrees and places them on the rim's slopes (up to
~50 degrees), so the downhill side shows more of the base. ONE mesh object, origin at the base centre.
Collision: none in the model (the game adds a 4 m sphere).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
ASSET = "cliff_a"
rw.reset()
moss_m = rw.flat(*sl.MOSS, 0.95)
GREY = "M_StoneRough"
WARM = sl.tinted_stone("ffd2a6").name
DIP = (0.018, 0.03)
SKIRT = 9.0

# Thick grey "hard" beds jut out; thin warm "soft" beds between them are recessed (weathered back), so every
# band throws a ledge. Joints (V-notches) share angles through a stack so they run down several beds.
J_BASE = [(18, 0.7, 4), (78, 0.55, 4), (128, 0.6, 4), (197, 0.75, 4), (262, 0.6, 4), (333, 0.65, 4)]
J_A = [(35, 0.6, 6), (110, 0.45, 6), (190, 0.55, 6), (290, 0.6, 6)]
J_B = [(70, 0.45, 7), (200, 0.5, 7), (310, 0.4, 7)]
# (name, centre, rx, ry, z0, z1, material, corners, seed, joints, inset)
LAYERS = [
    ("plinth", (0.0, 0.0), 5.0, 3.0, -SKIRT, 1.0, GREY, 10, 1, J_BASE, 0.12),
    ("soft1", (0.1, 0.04), 4.62, 2.68, 0.94, 1.55, WARM, 10, 2, J_BASE, 0.05),
    ("hard2", (0.05, -0.05), 4.88, 2.88, 1.49, 3.0, GREY, 10, 3, J_BASE, 0.2),
    ("soft3", (0.12, 0.02), 4.35, 2.52, 2.94, 3.45, WARM, 10, 4, J_BASE, 0.05),
    ("hard4", (0.0, 0.05), 4.55, 2.7, 3.39, 4.45, GREY, 10, 5, J_BASE, 0.18),
    ("towerA_soft", (1.85, 0.12), 2.62, 2.18, 4.39, 4.92, WARM, 9, 6, J_A, 0.05),
    ("towerA_hard", (1.9, 0.05), 2.95, 2.42, 4.86, 6.45, GREY, 9, 7, J_A, 0.22),
    ("towerA_soft2", (2.0, 0.1), 2.35, 2.0, 6.39, 6.85, WARM, 9, 8, J_A, 0.05),
    ("towerA_top", (2.1, 0.05), 2.38, 2.06, 6.79, 8.0, GREY, 9, 9, J_A, 0.2),
    ("towerB_soft", (-2.55, -0.18), 1.75, 1.85, 4.39, 4.85, WARM, 8, 10, J_B, 0.05),
    ("towerB_top", (-2.6, -0.12), 1.98, 2.08, 4.79, 5.95, GREY, 8, 11, J_B, 0.2),
]

parts = []
for (name, c, rx, ry, z0, z1, mat, n, seed, joints, inset) in LAYERS:
    pts = sl.outline(n, rx, ry, seed=seed * 17, centre=c, p=2.1, jitter=0.14, notches=joints, phase=seed * 0.61,
                     ang_jitter=0.35)
    hard = mat == GREY
    o = sl.slab(name, pts, z0, z1, mat=rw._resolve_mat(mat), bevel=0.17 if hard else 0.1, segments=2 if hard else 1,
                bevel_angle=32, inset=inset, dip=DIP, flare=0.6 if z0 < 0 else 0.0, top_jitter=0.04, seed=seed,
                floor=(z0 < 0))
    parts.append(o)

# two broken-off blocks slumped against the plinth's ends (talus; tall enough to show above the game's 1.5 m sink)
for i, (c, size, seed, spin) in enumerate((((-4.1, 1.75), (2.3, 1.9, 3.2), 81, 20),
                                           ((4.25, -1.75), (2.0, 1.7, 2.7), 82, -35))):
    bm = sl.boulder_bm(size, seed=seed, skirt=5.0, n_top=10, jitter=0.4, rmin=0.86, shoulder=2.6, plan=2.4,
                       belly=0.25, n_ring=7, foot=0.97, taper=0.95, lean=(0.0, 0.0), centre=c, spin=spin,
                       cuts=[(spin + 90, 70, 0.18), (spin + 200, 35, 0.15), (spin + 320, 40, 0.15)])
    parts.append(sl.stone("talus%d" % i, bm, mat=rw._resolve_mat(GREY), bevel=0.12, segments=1, bevel_angle=30,
                          floor=-5.0))

layer = {o.name: o for o in parts}
moss = [
    sl.moss_pad("mossA", layer["towerA_top"], (2.1, 0.08), 1.5, thick=0.2, mat=moss_m, seed=3, squash=(1.05, 0.95),
                rot=10, lobes=((3, 0.14), (5, 0.08), (8, 0.05)), rings=(0.0, 0.4, 0.7, 0.88, 1.0), seg=18, puff=0.3,
                tuck=0.08, dome=(2.5, 0.6)),
    sl.moss_pad("mossB", layer["towerB_top"], (-2.6, -0.12), 1.35, thick=0.17, mat=moss_m, seed=4, squash=(1.0, 1.05),
                rot=40, lobes=((3, 0.14), (5, 0.08)), rings=(0.0, 0.45, 0.78, 1.0), seg=15, puff=0.3, tuck=0.08,
                dome=(2.5, 0.6)),
    sl.moss_pad("mossS", layer["hard4"], (-0.3, 0.95), 1.0, thick=0.15, mat=moss_m, seed=5, squash=(1.2, 0.8),
                rot=0, lobes=((3, 0.16), (5, 0.1)), rings=(0.0, 0.45, 0.78, 1.0), seg=14, puff=0.3, tuck=0.08,
                dome=(2.5, 0.6)),
]
print("RWREPORT   parts: " + ", ".join("%s %d" % (o.name, sl.tris(o)) for o in parts + [m for m in moss if m]))
obj = sl.one_mesh(parts + moss, ASSET)
sl.finish(ASSET, obj, 4000, col_r=4.0)
if sl.qa_on():
    sl.qa_render(ASSET, "skirt", (-1, -0.3, 0.1), objs=[obj])
    sl.qa_render(ASSET, "low", (-0.2, -1.0, 0.05), objs=[obj])
sl.qa_extra(ASSET)
