"""item_pouch_rune: "Rune-Stitched Pouch", a deep indigo pouch with glowing violet runes, about 0.28 x 0.22 x 0.29 m.

Pouch tier 4: a soft, round-bottomed pouch of deep indigo cloth (M_Fabric__4a2ea8) with a darker indigo envelope flap
(M_Fabric__2a1868) folding down to a point, sewn with glowing violet rune stitching (rw.glow a066ff) round
the flap and the front and back panels, a big glowing algiz rune on the flap, a sowilo rune on the back, and a silver clasp set with a violet gem at
the flap's point, catching on a silver hasp. One mesh object "PouchRune", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_rune"
rw.reset()

BODY = "M_Fabric__4a2ea8"
FLAP = "M_Fabric__2a1868"
GLOW = "RuneViolet"
SILVER = pk.mat("Silver")
W, D, H = 0.225, 0.11, 0.225
pp = pk.FlapPouch("pouch", (W, D, H), BODY, e_xy=0.48, e_z=0.6, segs=24, rings=12, taper=0.16, bulge=0.2,
                  round_bottom=0.18, axis_z=0.6)
parts = [pp.body]

# envelope flap folding down to a point
A_SIDE, A_TIP = 90, 128
edge = pk.FlapPouch.u_edge(0.18, A_TIP, A_SIDE, 1.15)
flap = pp.flap("flap", 0.18, -64, edge, thick=0.01, m=FLAP, nu=12, nv=11)
parts.append(flap)
FS = pk.Surface(flap)

# glowing rune stitching: round the flap's V edge, and round the lower front panel
path = pp.flap_edge(0.012, 6.0, 30, a_top=70.0)
parts += pk.surf_marks("stitch", FS, pp.proj, path, 19, (0.016, 0.0066, 0.0045), GLOW, sink=0.3)
FP = pk.proj_plane((0, 0, 0.1), (0, -1, 0))
seam = [(-0.086, 0.035), (-0.088, -0.02), (-0.074, -0.058), (-0.042, -0.078), (0.0, -0.084), (0.042, -0.078),
        (0.074, -0.058), (0.088, -0.02), (0.086, 0.035)]
parts += pk.surf_marks("seam", pp.surf, FP, seam, 15, (0.014, 0.0062, 0.0042), GLOW, sink=0.3)

# glowing stitching and a sowilo rune on the back panel too (the pickup spins in the world)
BP = pk.proj_plane((0, 0, 0.1), (0, 1, 0))
parts += pk.surf_marks("seam_back", pp.surf, BP, seam, 15, (0.014, 0.0062, 0.0042), GLOW, sink=0.3)
P, N, U, Vv = pk.surf_frame(pp.surf, BP, 0.0, -0.02)
parts += pl.glyph("sowilo", P + N * 0.0012, U, Vv, 0.05, 0.0085, 0.006, pk.mat(GLOW), "rune")

# a big glowing algiz rune on the flap
P, N, U, Vv = pk.surf_frame(FS, pp.proj, 0.0, 84)
parts += pl.glyph("algiz", P + N * 0.0015, U, -Vv, 0.058, 0.0095, 0.006, pk.mat(GLOW), "rune")

# silver clasp with a violet gem at the flap's point, and the hasp on the body below it
P, N = pk.surf_point(FS, pp.proj, 0.0, A_TIP - 7)
parts.append(pl.disc("clasp", 0.031, 0.01, tuple(N), tuple(P + N * 0.004), SILVER, 18, 0.35))
parts.append(rw.torus("clasp_rim", 0.029, 0.0045, 18, 4, (0, 0, 0), mat=SILVER))
pl.align(parts[-1], N, P + N * 0.009)
gem = rw.ico("gem", 0.017, 1, (0, 0, 0), (0, 0, 0), (1, 1, 0.6), pk.mat(GLOW), None, 0)
pl.align(gem, N, P + N * 0.012)
parts.append(gem)
Q, QN = pk.surf_point(pp.surf, pp.proj, 0.0, A_TIP + 9)
hasp = rw.torus("hasp", 0.011, 0.0035, 12, 4, (0, 0, 0), mat=SILVER)
pl.align(hasp, (1, 0, 0), Q + QN * 0.007 + V((0, 0, -0.004)))
parts.append(hasp)
parts.append(pl.obox("hasp_plate", (0.03, 0.016, 0.004), Q + QN * 0.001 + V((0, 0, -0.012)), (1, 0, 0), QN, SILVER,
                     rounded=0.003, segments=1))
# silver tips on the flap's side corners
for sx in (-1, 1):
    P, N = pk.surf_point(FS, pp.proj, sx * 0.076, edge(sx * 0.076) - 5)
    parts.append(pl.rivet(P, N, 0.0075, 0.0055, SILVER, 6))

pouch = rw.join(parts, "PouchRune")
pk.fit(pouch, 0.29)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.29,))
