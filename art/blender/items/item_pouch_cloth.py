"""item_pouch_cloth: "Patched Cloth Pouch", a small beige drawstring sack, about 0.27 x 0.22 x 0.30 m.

The humblest pouch tier: a lumpy little sack of beige cloth (M_Fabric__f0c888) gathered at the neck into a
frilly ruffled top with a dark mouth, pulled shut by a brown drawstring tied in a fat knot at the front with
two dangling ends; three mismatched patches (faded red, blue and green cloth, M_Fabric tints) held on with big
dark cartoon stitches, and a stitched seam down the left side.
One mesh object "PouchCloth", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_cloth"
rw.reset()

CLOTH = "M_Fabric__f0c888"
ZN = 0.206                                            # neck (drawstring) height
outer = [(0.0, 0.0), (0.075, 0.006), (0.115, 0.04), (0.124, 0.09), (0.11, 0.138), (0.075, 0.178), (0.05, ZN - 0.002),
         (0.056, 0.222), (0.074, 0.246), (0.086, 0.264)]
inner = [(0.087, 0.274), (0.079, 0.282), (0.066, 0.279), (0.045, 0.264), (0.0, 0.258)]
sk = pk.Sack("sack", outer, inner, segs=32, per_seg=2, m=CLOTH, folds=(8, 0.12, ZN, 0.045),
             ruffle=(8, 0.13, ZN + 0.006, 0.276, 0.007), lumps=((2, 0.045, 30, 0.08, 0.06), (3, 0.035, 100, 0.06, 0.05)),
             squash=0.86, lean=0.008, seed=3)
parts = [sk.obj]
S = sk.surf

# mismatched patches with big stitches across their edges ---------------------------------------------------------
PATCHES = (  # (tint, azimuth, elevation, z, w, h, turn)
    ("M_Fabric__d23a2c", -52, 0, 0.098, 0.08, 0.068, 9),
    ("M_Fabric__3a78d8", 2, 0, 0.036, 0.066, 0.054, -14),
    ("M_Fabric__62b830", 160, 0, 0.1, 0.075, 0.06, 6),
)
for k, (tint, az, el, z, w, h, turn) in enumerate(PATCHES):
    a = math.radians(az)
    n = V((math.sin(a), -math.cos(a), math.sin(math.radians(el))))
    proj = pk.proj_plane((0, 0, z), n)
    parts.append(pk.surf_slab("patch", S, proj, pk.squircle_map(w, h, 4.0, angle=turn), 5, 4, 0.0008, 0.0045, tint))
    edge = pk.squircle_outline(w, h, 4.0, 32, angle=turn)
    count = int(round((w + h) * 2 / 0.025))
    parts += pk.surf_marks("stitch", S, proj, edge, count, (0.016, 0.0048, 0.0042), "SackThread", across=True,
                           closed=True, sink=0.1)

# seam down the left side
seam_proj = pk.proj_cyl_z((0, 0, 0))
seam = [(-90, 0.16), (-90, 0.12), (-90, 0.08), (-90, 0.04), (-90, 0.012)]
parts += pk.surf_marks("seam", S, seam_proj, seam, 7, (0.013, 0.0045, 0.004), "SackThread", across=False)

# drawstring: loop round the neck, a fat knot at the front and two dangling ends with little end knots ----------------
c, rx, ry = sk.neck_ellipse(ZN, 0.004)
parts.append(pk.loop_tube("cord", pk.ellipse_loop(c, rx, ry, 24), 0.0085, 6, "Cord"))
ka = math.radians(-22)
kd = V((math.sin(ka), -math.cos(ka), 0))
kp = c + V((kd.x * rx, kd.y * ry, 0)) + kd * 0.006
parts.append(pk.knot("knot", kp, 0.02, "Cord", (1.1, 0.8, 0.85), 2))
for side, (dx, dz, sway) in ((-1, (-0.028, -0.075, 0.01)), (1, (0.02, -0.06, -0.006))):
    p0 = kp + kd * 0.004
    p1 = p0 + V((dx * 0.35, -0.012, -0.02))
    p2 = p0 + V((dx * 0.8, -0.02, dz * 0.65))
    p3 = p0 + V((dx + sway, -0.024, dz))
    # keep the dangling ends just outside the sack surface
    pts = []
    for q in (p0, p1, p2, p3):
        h, hn = S.nearest(q)
        pts.append(h + hn * 0.009 if (q - h).dot(hn) < 0.009 else q)
    parts.append(pl.sausage("cord_end", pts, 0.0078, 6, 2, pk.mat("Cord"), (True, True), 1, True, 60))
    parts.append(pk.knot("end_knot", pts[-1], 0.013, "Cord", (1, 1, 1.1), 5 + side, 8, 5))

pouch = rw.join(parts, "PouchCloth")
pk.fit(pouch, 0.30)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.30,))
