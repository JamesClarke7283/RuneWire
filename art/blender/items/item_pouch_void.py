"""item_pouch_void: "Bottomless Pouch" (legendary), a midnight pouch holding a starry void, about 0.23 x 0.23 x 0.32 m.

Pouch tier 6: a plump pouch of midnight-violet cloth (M_Fabric__2a2160) embroidered with gold-thread stars,
tilted toward the viewer so its wide, rolled-rim mouth shows a swirling void inside (glowing deep-violet
disc with two bright violet spiral arms and white star sparkles, rw.glow a066ff), a few stars drifting up
out of it, and a gold drawstring tied in a knot whose two cords end in fat gold tassels.
One mesh object "PouchVoid", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_void"
rw.reset()

CLOTH = "M_Fabric__2a2160"
GOLD = pk.mat("Gold")
ZN = 0.17                                            # neck
outer = [(0.0, 0.0), (0.072, 0.005), (0.11, 0.035), (0.122, 0.08), (0.113, 0.124), (0.09, 0.153), (0.073, ZN),
         (0.077, 0.184), (0.092, 0.203), (0.104, 0.219)]
inner = [(0.106, 0.229), (0.099, 0.236), (0.089, 0.232), (0.08, 0.222), (0.05, 0.214), (0.0, 0.211)]
sk = pk.Sack("pouch", outer, inner, segs=28, per_seg=2, m=CLOTH, mouth_m="VoidDeep", folds=(7, 0.09, ZN, 0.035),
             ruffle=(7, 0.035, ZN + 0.012, 0.226, 0.003), lumps=((2, 0.03, 60, 0.08, 0.06),), squash=0.92,
             lean=0.0, seed=7)
S = sk.surf
parts = [sk.obj]

# the void: two bright spiral arms and star sparkles on the dark glowing mouth
top = pk.proj_plane((0, 0, 0.214), (0, 0, 1), (0, 1, 0))
for ph in (0.0, math.pi):
    arm = [(r * math.cos(a + ph), r * math.sin(a + ph)) for (r, a) in
           ((0.006 + 0.066 * i / 11, 2 * math.pi * 0.85 * i / 11) for i in range(12))]
    parts.append(pk.surf_strap("swirl", S, top, arm, 0.016, 0.003, 0.0006, "VoidViolet", 1, taper=(0.35, 1.0)))
star4 = [(0.0, 1.0), (0.22, 0.22), (1.0, 0.0), (0.22, -0.22), (0.0, -1.0), (-0.22, -0.22), (-1.0, 0.0),
         (-0.22, 0.22)]
for (x, y, s) in ((0.035, -0.03, 0.011), (-0.042, 0.02, 0.009), (0.012, 0.05, 0.008), (-0.02, -0.052, 0.008),
                  (0.055, 0.03, 0.007)):
    parts.append(pk.surf_prism("spark", star4, S, top, 0.0025, 0.002, "StarWhite", scale=s, center=(x, y)))
parts.append(rw.ico("core", 0.012, 1, (0, 0, 0.217), (0, 0, 0), (1, 1, 0.5), pk.mat("StarWhite"), None, 0))

# gold stars embroidered on the cloth
for (az, z, s, turn) in ((-52, 0.085, 0.046, 8), (12, 0.05, 0.034, -12), (-110, 0.11, 0.03, 20), (150, 0.09, 0.04, 0),
                         (80, 0.1, 0.032, 15)):
    a = math.radians(az)
    proj = pk.proj_plane((0, 0, z), (math.sin(a), -math.cos(a), 0))
    parts.append(pk.surf_prism("star", il.star_pts(5, 0.5, 0.21), S, proj, 0.0018, 0.0028, "GoldThread", scale=s,
                               angle=turn))

# gold drawstring round the neck and a knot at the front
c, rx, ry = sk.neck_ellipse(ZN + 0.002, 0.003)
parts.append(pk.loop_tube("cord", pk.ellipse_loop(c, rx, ry, 22), 0.0075, 6, GOLD))
ka = math.radians(-25)
kd = V((math.sin(ka), -math.cos(ka), 0))
kp = c + V((kd.x * rx, kd.y * ry, 0)) + kd * 0.007
parts.append(pk.knot("knot", kp, 0.016, GOLD, (1.15, 0.8, 0.9), 3))
pouch = rw.join(parts, "PouchVoid", origin=(0, 0, 0))

# tilt the pouch toward the viewer so the void shows, then hang the tassels straight down from the knot
TILT = pk.rot((0, 0, 1), -32) @ pk.rot((1, 0, 0), 20, (0, 0, 0.12))
pk.transform(pouch, TILT)
knot_w = TILT @ kp
extra = []
hit = pk.Surface(pouch)
for (dx, L, sway) in ((-0.024, 0.07, -0.006), (0.02, 0.05, 0.008)):
    p0 = knot_w + V((dx * 0.3, -0.004, -0.008))
    p3 = knot_w + V((dx, -0.018, -L))
    pts = [p0, p0 + V((dx * 0.4, -0.012, -L * 0.35)), p3 + V((sway, -0.004, L * 0.25)), p3]
    fixed = []
    for q in pts:
        h, hn = hit.nearest(q)
        fixed.append(h + hn * 0.008 if (q - h).dot(hn) < 0.008 else q)
    extra.append(pl.sausage("tassel_cord", fixed, 0.0055, 6, 2, GOLD, (True, False), 1, True, 60))
    extra.append(pk.tassel("tassel", fixed[-1] + V((0, 0, 0.004)), (0, 0, -1), 0.05, 0.015, GOLD, None, 8, 8))
# a few stars drifting up out of the mouth
mouth = TILT @ V((0, 0, 0.216))
up = (TILT.to_3x3() @ V((0, 0, 1))).normalized()
for (off, s, turn) in (((0.045, -0.03, 0.045), 0.024, 10), ((-0.04, -0.02, 0.085), 0.018, -15),
                       ((0.018, -0.015, 0.125), 0.014, 30)):
    p = mouth + up * off[2] + V((off[0], off[1], 0))
    pts = [(x * s, y * s) for (x, y) in star4]
    o = il.wrap_prism("float_star", pts, il.plane_map(p, (1, 0, 0), (0, 0, 1), -0.004, 0.008), pk.mat("StarWhite"))
    pk.transform(o, pk.rot((0, 0, 1), -32 + turn, p))
    extra.append(o)
pouch = rw.join([pouch] + extra, "PouchVoid")
pk.fit(pouch, 0.32)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.32,))
