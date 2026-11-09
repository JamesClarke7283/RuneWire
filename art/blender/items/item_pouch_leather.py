"""item_pouch_leather: "Leather Belt Pouch", a plump brown leather pouch, about 0.29 x 0.21 x 0.27 m.

Pouch tier 2: a stuffed, U-bottomed pouch of warm brown leather (M_Leather__ffd2a0) with a dark brown flap
(M_Leather__9a6a50) folded over its top and down the front into a rounded tongue, cream saddle stitching round
the flap edge, and a fat round brass button stud on a brass washer holding the tongue shut. On the back a
stitched leather belt loop stands proud. One mesh object "PouchLeather", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_leather"
rw.reset()

BODY = "M_Leather__ffd2a0"
FLAP = "M_Leather__9a6a50"
W, D, H = 0.235, 0.105, 0.21
pp = pk.FlapPouch("pouch", (W, D, H), BODY, e_xy=0.3, e_z=0.38, segs=24, rings=12, taper=0.06, bulge=0.14,
                  round_bottom=0.12, axis_z=0.6)
parts = [pp.body]

# flap: from just behind the top edge, over the top, down the front into a rounded tongue
A_SIDE, A_TIP = 104, 140
edge = pk.FlapPouch.tongue_edge(A_SIDE, A_TIP, 0.062, 0.85)
flap = pp.flap("flap", 0.196, -62, edge, thick=0.011, m=FLAP, nu=12, nv=11)
parts.append(flap)
FS = pk.Surface(flap)
path = pp.flap_edge(0.012, 6.0, 36, a_top=70.0)
parts += pk.surf_marks("stitch", FS, pp.proj, path, 22, (0.013, 0.0042, 0.0032), "PaleThread", sink=0.35)

# saddle stitching round the lower front panel (its top ends tuck under the flap)
FP = pk.proj_plane((0, 0, 0.1), (0, -1, 0))
seam = [(-0.098, 0.012), (-0.098, -0.04), (-0.086, -0.068), (-0.05, -0.08), (0.0, -0.083), (0.05, -0.08),
        (0.086, -0.068), (0.098, -0.04), (0.098, 0.012)]
parts += pk.surf_marks("seam", pp.surf, FP, seam, 20, (0.012, 0.004, 0.003), "PaleThread", sink=0.35)

# brass button stud on the tongue, sitting on a washer ring
P, N = pk.surf_point(FS, pp.proj, 0.0, A_TIP - 11)
parts.append(pl.rivet(P + N * 0.002, N, 0.025, 0.018, pk.mat("M_Brass"), 14, "stud", 0.4))
ring = rw.torus("washer", 0.028, 0.005, 16, 5, (0, 0, 0), mat=pk.mat("M_Brass"))
pl.align(ring, N, P + N * 0.001)
parts.append(ring)

# belt loop on the back: a stitched strap standing off the back panel
BP = pk.proj_plane((0, 0, 0.105), (0, 1, 0))
top, tn = pk.surf_point(pp.surf, BP, 0.0, 0.06)
bot, bn = pk.surf_point(pp.surf, BP, 0.0, -0.07)
loop_pts = [top - tn * 0.002, top + tn * 0.012 + V((0, 0, -0.008)), (top + bot) / 2 + V((0, 0.022, 0)),
            bot + bn * 0.012 + V((0, 0, 0.008)), bot - bn * 0.002]
parts.append(pk.strap("belt_loop", loop_pts, 0.07, 0.009, (0, 1, 0), FLAP, 3))
for (p, n) in ((top, tn), (bot, bn)):
    for sx in (-1, 1):
        parts.append(pl.obox("loop_stitch", (0.004, 0.012, 0.003), p + n * 0.008 + V((sx * 0.024, 0, 0)), (1, 0, 0),
                             n, pk.mat("PaleThread")))

pouch = rw.join(parts, "PouchLeather")
pk.fit(pouch, 0.29)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.29,))
