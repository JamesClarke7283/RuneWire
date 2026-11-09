"""mushroom_cluster: three cartoon toadstools with glowing teal undersides, 0.3-0.8 m tall.

A big toadstool (0.8 m), a medium one (0.5 m) and a small one (0.3 m) grow from one spot, their curved cream
stems leaning apart so the violet, white-spotted caps tilt outward and the glowing teal gills show from every
side; the outer rim band of each cap glows too, so the teal also reads from above. The heights are measured
from the game's ground line: vegetation.gd sinks every instance 0.15 m, so the mushrooms stand on z = 0.15 and
their stems run on down to z = -0.3 (no gap on slopes). Violet caps keep them apart from the harvestable
node_glowcap (glowing blue caps).

Materials (names avoid the foliage words, so Godot keeps the glow and nothing sways): ToadcapCap (violet),
ToadcapStem (cream stems and cap spots), ToadcapGill (teal glow). ONE mesh object, origin at the base centre.
No collision (vegetation.gd gives mushrooms none). Built with env/gatherlib.mushroom().
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
V = sl.V
G = sl.gather()
pl = G.pl
ASSET = "mushroom_cluster"
rw.reset()
rw.flat("ToadcapCap", "9b5ae6", 0.55)
rw.flat("ToadcapStem", "f3ebd6", 0.8)
rw.glow("ToadcapGill", "35f0d2", 2.4)
MATS = dict(cap_m="ToadcapCap", gill_m="ToadcapGill", stem_m="ToadcapStem", spot_m="ToadcapStem")
GL = sl.SINK                                   # the game's ground line

# (base x, y, azimuth, lean, stem length, cap radius, cap height, upright, segs, spots, seed)
SHROOMS = [
    ((-0.03, 0.06), 135, 0.22, 0.6, 0.28, 0.21, 0.5, 12, 5, 3),      # big: top about 0.8 above the ground line
    ((0.15, -0.02), 350, 0.45, 0.4, 0.19, 0.135, 0.3, 11, 3, 7),     # medium: about 0.5
    ((-0.14, -0.1), 195, 0.58, 0.235, 0.125, 0.095, 0.25, 9, 2, 11), # small: about 0.3
]
gill = rw._resolve_mat("ToadcapGill")


def glow_rim(cap, r):
    """Give the outer band of the cap (from the lip up to the first dome ring) the gill glow too, so the teal
    shows as a glowing rim from above as well as underneath."""
    sl.update()
    mw = cap.matrix_world
    gi = [i for i, m in enumerate(cap.data.materials) if m == gill][0]
    under = [p for p in cap.data.polygons if p.material_index == gi]
    axis = -sum((mw.to_3x3() @ p.normal for p in under), V()).normalized()
    c0 = sum((mw @ v.co for v in cap.data.vertices), V()) / len(cap.data.vertices)
    for p in cap.data.polygons:
        c = mw @ p.center - c0
        h = c.dot(axis)
        rad = (c - axis * h).length
        if rad > 0.86 * r and -0.4 < (mw.to_3x3() @ p.normal).normalized().dot(axis) < 0.55:
            p.material_index = gi


parts = []
for (x, y), az, lean, L, r, h, up, segs, spots, seed in SHROOMS:
    base = V((x, y, GL - 0.02))
    got = G.mushroom(base, az, lean, L, r, cap_h=h, stem_r=r * 0.34, upright=up, spots=spots, seed=seed, segs=segs,
                     spot_r=0.22, stem_segs=8 if r > 0.15 else 7, stem_res=2 if r > 0.15 else 1, kick=0.1, **MATS)
    glow_rim(got[1], r)
    parts += got
    # the buried part of the stem, down to z = -0.3: a little thinner than the stem's flared foot and ending
    # inside it, below the ground line, so its open top never shows
    parts.append(pl.sausage("stem_root", [V((x, y, -0.3)), V((x, y, GL - 0.035))], r * 0.34 * 1.2,
                            8 if r > 0.15 else 7, 1, G.S.mat("ToadcapStem"), (False, None), 1, False, 70))
print("RWREPORT   parts: %d objects, %d tris" % (len(parts), sum(sl.tris(p) for p in parts)))
obj = sl.one_mesh(parts, ASSET)
sl.finish(ASSET, obj, 900, max_mats=3, ground_z=GL,
          preview_glows={"ToadcapGill": ("1d8f80", "35f0d2", 0.9)})
if sl.qa_on():
    sl.qa_render(ASSET, "under", (-0.6, -1.0, -0.15), objs=[obj])
sl.qa_extra(ASSET, sink=GL)
