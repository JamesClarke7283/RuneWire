"""item_steel_plate: a thick square steel plate, about 0.28 x 0.28 m and 0.035 m thick (plus its bent corner).

A chunky square plate of steel (M_Steel) with soft bevelled edges, standing upright and facing the front (-Y),
leaning back a little. Four big domed brass rivets (M_Brass) sit near the corners, and the top-right corner is
bent forward toward the viewer in a smooth dog-ear. One mesh object "SteelPlate", origin at the centre.
"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
Matrix = ml.Matrix
ASSET = "item_steel_plate"
rw.reset()

S, T = 0.27, 0.034          # plate size and thickness
BEND_D0 = 0.122             # bend line: points with (x + y) / sqrt(2) beyond this fold up (top-right corner)
BEND_ZONE = 0.014           # width of the rounded fold
BEND_DEG = 50.0
DIAG = V((1, 1, 0)).normalized()

# plate: a bevelled slab in the XY plane (front face +Z) ...
plate = rw.box("plate", (S, S, T), mat="M_Steel")
md = plate.modifiers.new("Bevel", 'BEVEL')
md.width = 0.009
md.segments = 2
md.limit_method = 'ANGLE'
md.angle_limit = math.radians(40)
md.use_clamp_overlap = True
rw.apply_modifiers(plate)
# ... with clean edge loops along the fold: parallel cuts across the top-right corner
bm = bmesh.new()
bm.from_mesh(plate.data)
for k in range(3):
    d = BEND_D0 + BEND_ZONE * k / 2
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=DIAG * d,
                           plane_no=DIAG)
bm.to_mesh(plate.data)
bm.free()

# fold the corner up (toward +Z, which becomes the viewer side) about the bend line
axis = V((1, -1, 0)).normalized()
for vx in plate.data.vertices:
    co = V(vx.co)
    d = co.dot(DIAG) - BEND_D0
    if d <= 1e-7:
        continue
    t = min(1.0, d / BEND_ZONE)
    ang = math.radians(BEND_DEG) * (t * t * (3 - 2 * t))
    pivot = DIAG * BEND_D0 + V((0, 0, T / 2))       # fold about the front face, toward the viewer
    vx.co = pivot + Matrix.Rotation(ang, 3, axis) @ (co - pivot)
plate.data.update()
rw.smooth(plate, 40)

# four big domed brass rivets near the corners (on the front face, clear of the fold)
parts = [plate]
INSET = 0.058
for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    ins = INSET + (0.012 if sx > 0 and sy > 0 else 0.0)      # the folded corner's rivet sits a little further in
    parts.append(pl.rivet(V((sx * (S / 2 - ins), sy * (S / 2 - ins), T / 2)), (0, 0, 1), 0.023, 0.016,
                          ml.mat("M_Brass"), 12, "rivet", 0.4))
plate = rw.join(parts, "SteelPlate", origin=(0, 0, 0))
ml.preview_metals()

# stand the plate up facing -Y, leaning back a little
pl.xform(plate, Matrix.Rotation(math.radians(90 - 12), 4, 'X'))
il.finish_item(ASSET, (0.28, 0.1, 0.28))
