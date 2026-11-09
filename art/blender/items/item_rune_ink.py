"""item_rune_ink: a squat glass inkwell of glowing violet rune ink with a feather quill in it, about 0.2 x 0.2 x 0.31 m.

A wide, low, round-shouldered glass inkwell (M_Glass above the ink line) filled with glowing violet ink (emissive
flat c060ff), with a thick open rolled lip, a brass collar round its neck and two fat drips of ink running down the
shoulder. A big white feather quill (a smooth curved vane with two notches) with a violet-dipped tip leans out of
the mouth. One mesh object "RuneInk", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_rune_ink"
rw.reset()

INK, INK_TOP = ml.mat("InkGlow"), ml.mat("InkGlowTop")
body = [(0.0, 0.0), (0.08, 0.0), (0.094, 0.014), (0.097, 0.04), (0.086, 0.066), (0.06, 0.082), (0.04, 0.09)]
lip = [(0.039, 0.1), (0.05, 0.104), (0.052, 0.114), (0.046, 0.12), (0.034, 0.12), (0.032, 0.108)]
b = il.Bottle(body, lip, fill=0.058, liquid=INK, top=INK_TOP, segs=24)
b.shine(-62, 0.035, 0.014, 0.034)
parts = list(b.parts)

# brass collar round the neck
parts.append(pl.band("collar", 0.047, 0.014, 0.01, (0, 0, 1), (0, 0, 0.094), ml.mat("M_Brass"), 18, 0.3))

# two fat ink drips running down the shoulder from the lip, half sunk into the glass
for (ang, z1, rr) in ((-38, 0.058, 0.0075), (-8, 0.07, 0.0065)):
    a = math.radians(ang)
    d = V((math.sin(a), -math.cos(a), 0.0))
    zs = [0.114, 0.106, 0.098, 0.09, 0.082, z1 + 0.01, z1]
    pts = [d * (b.r(z) + rr * 0.35) + V((0, 0, z)) for z in zs]
    parts.append(pl.sausage("drip", pts, [rr * 0.8, rr * 0.8, rr * 0.75, rr * 0.75, rr * 0.85, rr * 1.1, rr * 1.35], 8,
                            2, INK, (True, True), 2, True, 60))

# the feather quill leaning out of the mouth
MOUTH = V((0.0, 0.0, 0.12))
D = V((0.32, 0.22, 1.0)).normalized()
CAM = V((-0.8, -1.0, 0.7)).normalized()
F = (CAM - CAM.dot(D) * D).normalized()               # the vane faces the viewer
parts.append(pl.sausage("shaft", [MOUTH - D * 0.07, MOUTH + D * 0.05, MOUTH + D * 0.19], [0.0055, 0.0055, 0.0035],
                        8, 2, ml.mat("QuillWhite"), (True, True), 2, True, 60))


def vane_shape(xn):
    """Feather outline: narrow at the base, broad in the middle, rounded-pointed tip."""
    return (0.55 + 0.45 * math.sin(math.pi * (xn + 1) / 2) ** 0.8) * (1 - 0.35 * max(xn, 0.0) ** 2)


VL = 0.165
VC = MOUTH + D * 0.115
vane = ml.pod("vane", VC, D, F, VL, 0.062, 0.012, "QuillWhite", 14, 7, vane_shape, None, 0.0, 0.0, 80, 0.06)
rw.set_mat_where(vane, ml.mat("QuillViolet"), lambda c, n: (c - MOUTH).dot(D) > 0.165)
# two V notches in the vane's edges (one each side) make it read as a feather
side = F.cross(D).normalized()
cuts = []
for (t, s_, depth) in ((-0.25, 1, 0.024), (0.3, -1, 0.02)):
    xn = t
    half_w = 0.031 * vane_shape(xn) * math.sqrt(1 - xn * xn) + 0.06 * VL * xn * xn     # pod edge incl. its sweep
    edge = VC + D * (xn * VL / 2) + side * (s_ * half_w)
    tip = edge - side * (s_ * depth) + D * 0.004
    tri = [edge + D * 0.006 + side * (s_ * 0.006), edge - D * 0.008 + side * (s_ * 0.006), tip]
    bm = ml.bmesh.new()
    lo = [bm.verts.new(p - F * 0.03) for p in tri]
    hi = [bm.verts.new(p + F * 0.03) for p in tri]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    ml.bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cuts.append(pl.obj_from_bm("notch", bm, None, 0))
pl.carve(vane, cuts)
rw.smooth(vane, 60)
parts.append(vane)

ink = rw.join(parts, "RuneInk")
il.finish_item(ASSET, (0.2, 0.2, 0.31))
