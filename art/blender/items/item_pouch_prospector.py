"""item_pouch_prospector: "Prospector's Satchel", a rugged canvas satchel, about 0.32 x 0.19 x 0.31 m.

A boxy, well-worn satchel of khaki canvas (M_Fabric__b8a46c) with a darker canvas flap (M_Fabric__8f7d4a) bound
in brown leather (M_Leather) and fastened by a leather strap through a steel buckle; a darker canvas patch with
cartoon stitches on the front, a little pickaxe (wooden handle, steel pick head) strapped to its left side, and
a fat gold nugget and a lump of grey ore poking up out of the top beside the flap. One mesh object "PouchProspector", origin at
the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_prospector"
rw.reset()

BODY = "M_Fabric__b8a46c"
FLAP = "M_Fabric__8f7d4a"
LEATHER = "M_Leather"
STEEL = pk.mat("M_Steel")
W, D, H = 0.26, 0.12, 0.215
pp = pk.FlapPouch("satchel", (W, D, H), BODY, e_xy=0.25, e_z=0.33, segs=24, rings=12, taper=0.04, bulge=0.12,
                  round_bottom=0.05, axis_z=0.6)
parts = [pp.body]

# flap (slid a little to the left, leaving room for the ore), bound in leather
A_EDGE = 112
FW, FX = 0.19, -0.022
edge = pk.FlapPouch.u_edge(FW, A_EDGE + 3, A_EDGE - 3, 5.0)
flap = pp.flap("flap", FW, -60, edge, thick=0.01, m=FLAP, nu=10, nv=9, x_off=FX)
parts.append(flap)
FS = pk.Surface(flap)
both = pk.surface_of([pp.body, flap])
bind = [(FX + x, edge(x) - 1.5) for x in [(-FW / 2 + 0.004) + (FW - 0.008) * i / 14 for i in range(15)]]
parts.append(pk.surf_strap("binding", FS, pp.proj, bind, 0.016, 0.0045, 0.0003, LEATHER, 1))

# leather strap down the front through a steel buckle
upper = [(FX, a) for a in (-50, -10, 40, 80, A_EDGE + 2)]
parts.append(pk.surf_strap("strap", both, pp.proj, upper, 0.032, 0.006, 0.0008, LEATHER, 2, n=8))
P_edge, _ = pk.surf_point(both, pp.proj, FX, A_EDGE + 2)
FP = pk.proj_plane((FX, 0, P_edge.z), (0, -1, 0))
parts.append(pk.surf_strap("strap_lo", pp.surf, FP, [(0.0, -0.025), (0.0, -0.1)], 0.034, 0.005, 0.0004, LEATHER, 2,
                           n=4))
P, N = pk.surf_point(pp.surf, FP, 0.0, -0.024)
parts += pk.buckle("buckle", P + N * 0.006, N, (0, 0, 1), 0.05, 0.036, 0.0055, STEEL)

# darker canvas patch with cartoon stitches, lower right of the front
PP = pk.proj_plane((0.05, 0, 0.06), (0, -1, 0))
parts.append(pk.surf_slab("patch", pp.surf, PP, pk.squircle_map(0.07, 0.05, 4.0, angle=-7), 5, 4, 0.0008, 0.004,
                          FLAP))
parts += pk.surf_marks("patch_stitch", pp.surf, PP, pk.squircle_outline(0.07, 0.05, 4.0, 28, angle=-7), 10,
                       (0.014, 0.0045, 0.0042), "SackThread", across=True, closed=True, sink=0.1)

# a fat gold nugget and a lump of grey ore poking up out of the top, right of the flap
nug = il.hull_rock("nugget", (0.075, 0.062, 0.07), (0.084, -0.012, 0.232), seed=4, n_points=16, jitter=0.35,
                   rmin=0.8, bevel=0.008, m=pk.mat("Nugget"), rot_z=-20, bevel_segments=2)
rw.smooth(nug, 50)
parts.append(nug)
ore = il.hull_rock("ore", (0.06, 0.055, 0.055), (0.098, 0.03, 0.214), seed=11, n_points=12, jitter=0.3, rmin=0.82,
                   bevel=0.006, m=pk.mat("Ore"), rot_z=25)
parts.append(ore)
for (p, s) in (((0.118, 0.012, 0.236), 0.013), ((0.082, 0.04, 0.236), 0.011)):
    parts.append(il.blob("fleck", (s * 1.3, s * 1.1, s * 0.8), p, pk.mat("Nugget"), 1, 1.0, 3, 0.0))

# pickaxe strapped to the left side
SIDE = pk.proj_plane((0, 0, 0.1), (-1, 0, 0))
pb, nb = pk.surf_point(pp.surf, SIDE, -0.01, -0.075)     # seen from -X: x runs toward the front (-Y), y up
pt, nt = pk.surf_point(pp.surf, SIDE, 0.02, 0.085)
HR = 0.011
a_end = pb + nb * (HR + 0.003)
b_end = pt + nt * (HR + 0.003)
d = (b_end - a_end).normalized()
b_end = b_end + d * 0.07                                   # the head stands above the satchel
a_end = a_end - d * 0.01
parts.append(pl.capsule("handle", a_end, b_end, HR, 8, 1, pk.mat("M_WoodPlanks")))
e = d.cross(V((-1, 0, 0))).normalized()                  # across the handle, in the side plane
hc = b_end - d * 0.004
head = [hc - e * 0.062 - d * 0.028, hc - e * 0.034 - d * 0.002, hc + d * 0.008, hc + e * 0.034 - d * 0.002,
        hc + e * 0.06 - d * 0.024]
parts.append(pl.sausage("pick_head", head, [0.0035, 0.011, 0.016, 0.011, 0.005], 8, 3, STEEL, (True, True), 2,
                        True, 50, (1.0, 0.78), (-1, 0, 0)))
parts.append(pl.band("ferrule", HR + 0.004, 0.022, 0.006, tuple(d), tuple(b_end - d * 0.024), STEEL, 10, 0.3))
for t in (0.25, 0.62):
    q = a_end.lerp(b_end, t)
    band_pts = [q + e * 0.022 + V((0.009, 0, 0)), q + e * 0.012 - V((HR + 0.004, 0, 0)), q - V((HR + 0.006, 0, 0)),
                q - e * 0.012 - V((HR + 0.004, 0, 0)), q - e * 0.022 + V((0.009, 0, 0))]
    parts.append(pk.strap("pick_strap", band_pts, 0.016, 0.004, (-1, 0, 0), LEATHER, 2))
    for s_ in (-1, 1):
        parts.append(pl.rivet(q + e * (s_ * 0.022) + V((0.004, 0, 0)), (-1, 0, 0), 0.0045, 0.0035,
                              pk.mat("M_Brass"), 6))

pouch = rw.join(parts, "PouchProspector")
pk.fit(pouch, 0.32)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.32,))
