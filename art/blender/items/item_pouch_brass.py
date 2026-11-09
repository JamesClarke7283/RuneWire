"""item_pouch_brass: "Brass-Buckled Pouch", a sturdy dark leather pouch, about 0.27 x 0.16 x 0.30 m.

Pouch tier 3: a sturdy pouch of dark chocolate leather (M_Leather__a08070) under a darker rounded flap
(M_Leather__806058) bound along its edge in studded brass, with an arched brass carry handle on top; two short
tan leather straps (M_Leather__ffe8c8) hang from the flap down through two chunky brass buckles on the front,
and brass caps with fat studs wrap the two lower front corners. One mesh object "PouchBrass", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_brass"
rw.reset()

BODY = "M_Leather__a08070"
FLAP = "M_Leather__806058"
STRAP = "M_Leather__ffe8c8"
BRASS = pk.mat("M_Brass")
W, D, H = 0.24, 0.11, 0.215
pp = pk.FlapPouch("pouch", (W, D, H), BODY, e_xy=0.34, e_z=0.42, segs=24, rings=12, taper=0.26, bulge=0.18,
                  round_bottom=0.0, axis_z=0.62)
parts = [pp.body]

# flap: over the top and down the upper front, with a soft U edge
edge = pk.FlapPouch.u_edge(0.212, 100, 86, 2.0)
flap = pp.flap("flap", 0.212, -60, edge, thick=0.012, m=FLAP, nu=12, nv=9)
parts.append(flap)
FS = pk.Surface(flap)
both = pk.surface_of([pp.body, flap])

# closure straps: sewn onto the flap, hanging past its edge down to buckles on the body
FP = pk.proj_plane((0, 0, 0.1), (0, -1, 0))
for sx in (-1, 1):
    x = sx * 0.056
    P_top, _ = pk.surf_point(FS, pp.proj, x, edge(x) - 22)
    zt = P_top.z - 0.1
    path = [(x, zt), (x, zt - 0.03), (x, -0.025), (x, -0.058)]
    parts.append(pk.surf_strap("strap", both, FP, path, 0.034, 0.006, 0.0008, STRAP, 2, n=8))
    P, N = pk.surf_point(pp.surf, FP, x, -0.022)
    parts += pk.buckle("buckle", P + N * 0.007, N, (0, 0, 1), 0.05, 0.036, 0.0056, BRASS)
    P, N = pk.surf_point(FS, pp.proj, x, edge(x) - 16)
    parts.append(pl.rivet(P + N * 0.006, N, 0.007, 0.005, BRASS, 6))

# brass binding along the flap's whole edge, studded between the straps and at the corners
hw = 0.212 / 2 - 0.003
bind = [(x, edge(x) - 2.0) for x in [-hw + 2 * hw * i / 16 for i in range(17)]]
parts.append(pk.surf_strap("binding", FS, pp.proj, bind, 0.02, 0.005, 0.0003, BRASS, 1))
for x in (-0.088, -0.018, 0.018, 0.088):
    P, N = pk.surf_point(FS, pp.proj, x, edge(x) - 3.0)
    parts.append(pl.rivet(P + N * 0.0045, N, 0.0068 if abs(x) < 0.05 else 0.0085, 0.005, BRASS, 6))

# brass carry handle on top: an arched bar between two riveted brass mounts
ends = []
for sx in (-1, 1):
    P, N, U, Vv = pk.surf_frame(FS, pp.proj, sx * 0.05, -6)
    parts.append(pl.obox("mount", (0.026, 0.024, 0.007), P + N * 0.0035, U, N, BRASS, rounded=0.003, segments=1))
    parts.append(pl.rivet(P + N * 0.007 - U * (sx * 0.006), N, 0.0055, 0.004, BRASS, 6))
    ends.append(P + N * 0.009)
top = (ends[0] + ends[1]) / 2 + V((0, 0, 0.05))
arch = [ends[0], ends[0] + V((0.008, 0, 0.034)), top, ends[1] + V((-0.008, 0, 0.034)), ends[1]]
parts.append(pl.sausage("handle", arch, 0.0075, 8, 3, BRASS, (True, True), 2, True, 60))

# brass caps wrapped over the two lower front corners, three rivets each
for sx in (-1, 1):
    inner = V((sx * W * 0.26, -D * 0.1, H * 0.26))
    nrm = V((sx * 1.0, -1.1, -0.62)).normalized()
    cap, cproj = pk.wrap_cap("cap", pp.surf, inner, nrm, 58, 0.0065, BRASS, 3.0, nu=5, nv=5)
    parts.append(cap)
    P, N = pk.surf_point(pp.surf, cproj, 0.0, 0.0)           # one fat stud, on the cap's outer face
    parts.append(pl.rivet(P + N * 0.0068, N, 0.0095, 0.007, BRASS, 8))

pouch = rw.join(parts, "PouchBrass")
pk.fit(pouch, 0.30)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.30,))
