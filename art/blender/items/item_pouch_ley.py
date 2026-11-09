"""item_pouch_ley: "Ley-Woven Satchel", a teal woven satchel with glowing ley lines, about 0.35 x 0.15 x 0.35 m.

Pouch tier 5: a wide messenger satchel woven from two tones of teal cloth (a basket-weave checker of
M_Fabric__1fa89c / M_Fabric__127a72) under a dark-teal flap (M_Fabric__0f5a55). Glowing teal ley lines
(rw.glow 39d5c4) run round the flap's border and branch from a ley node ring above a brass turn-lock clasp;
brass tips on the flap corners, brass D-rings on the sides and a dark-teal shoulder strap (M_Fabric__0c4f4a) with a brass adjuster buckle arching over the top.
One mesh object "PouchLey", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_ley"
rw.reset()

WEAVE_A = "M_Fabric__1fa89c"
WEAVE_B = "M_Fabric__127a72"
FLAP = "M_Fabric__0f5a55"
GLOW = "LeyTeal"
BRASS = pk.mat("M_Brass")
W, D, H = 0.3, 0.1, 0.205
pp = pk.FlapPouch("satchel", (W, D, H), WEAVE_A, e_xy=0.28, e_z=0.4, segs=24, rings=12, taper=0.05, bulge=0.12,
                  round_bottom=0.07, axis_z=0.6)
pk.checker(pp.body, WEAVE_B, 2, 1)
parts = [pp.body]

# flap: straight front edge with rounded corners
A_EDGE = 116
edge = pk.FlapPouch.u_edge(0.27, A_EDGE + 3, A_EDGE - 4, 4.0)
flap = pp.flap("flap", 0.27, -58, edge, thick=0.011, m=FLAP, nu=12, nv=10)
parts.append(flap)
FS = pk.Surface(flap)

# glowing ley lines: a border inset from the flap edge, a node ring above the clasp and branches to it
border = pp.flap_edge(0.016, 7.0, 24, a_top=58.0)
parts.append(pk.surf_strap("ley", FS, pp.proj, border, 0.0065, 0.0028, 0.0004, GLOW, 1, n=34))
node_a = 92
ring = [(0.026 * math.cos(2 * math.pi * i / 16), node_a + 24.0 * math.sin(2 * math.pi * i / 16)) for i in range(17)]
parts.append(pk.surf_strap("ley_ring", FS, pp.proj, ring, 0.0065, 0.0028, 0.0004, GLOW, 1, n=17))
for sx in (-1, 1):
    branch = [(sx * 0.026, node_a), (sx * 0.06, node_a), (sx * 0.08, 78), (sx * 0.112, 78)]
    parts.append(pk.surf_strap("ley_branch", FS, pp.proj, branch, 0.006, 0.0028, 0.0004, GLOW, 1, smooth_path=False))
    P, N = pk.surf_point(FS, pp.proj, sx * 0.08, 78)
    parts.append(pl.disc("ley_dot", 0.0085, 0.004, tuple(N), tuple(P + N * 0.0015), pk.mat(GLOW), 10, 0.3))
P, N = pk.surf_point(FS, pp.proj, 0.0, node_a)
parts.append(pl.disc("ley_core", 0.012, 0.004, tuple(N), tuple(P + N * 0.0015), pk.mat(GLOW), 12, 0.3))

# brass turn-lock clasp at the flap's front edge
P, N, U, Vv = pk.surf_frame(FS, pp.proj, 0.0, A_EDGE - 4)
parts.append(pl.obox("clasp", (0.052, 0.034, 0.008), P + N * 0.003, U, N, BRASS, rounded=0.004, segments=1))
parts.append(pl.disc("clasp_knob", 0.011, 0.01, tuple(N), tuple(P + N * 0.01), BRASS, 12, 0.4))
parts.append(pl.obox("clasp_bar", (0.026, 0.007, 0.006), P + N * 0.016, U, N, BRASS, rounded=0.002, segments=1))
for sx in (-1, 1):
    parts.append(pl.rivet(P + U * (sx * 0.019) + N * 0.006, N, 0.0045, 0.003, BRASS, 6))
    # brass tips on the flap's corners
    Pc, Nc = pk.surf_point(FS, pp.proj, sx * 0.118, A_EDGE - 7)
    parts.append(pl.rivet(Pc, Nc, 0.0085, 0.0065, BRASS, 8))

# brass D-rings on the sides and the arched leather shoulder strap
ZR = 0.16
for sx in (-1, 1):
    P, N = pk.surf_point(pp.surf, pk.proj_cyl_z((0, 0, ZR)), sx * 90, 0.0)
    tab = pl.obox("ring_tab", (0.03, 0.026, 0.006), P + N * 0.002, (0, 1, 0), N, pk.mat("M_Leather__a07858"),
                  rounded=0.003, segments=1)
    parts.append(tab)
    dr = rw.torus("dring", 0.016, 0.0045, 14, 5, (0, 0, 0), (90, 0, 0), BRASS)
    dr.location = P + N * 0.012 + V((0, 0, 0.01))
    parts.append(dr)
c = V((0, 0, 0.17))
arch = []
for i in range(11):
    t = math.pi * i / 10
    lean = 0.012 * math.sin(2 * t)                 # a little floppy, not a stiff handle
    arch.append(V((-(W / 2 + 0.012) * math.cos(t) + lean, 0.0, 0.185 + 0.165 * math.sin(t) ** 0.8)))
parts.append(pk.strap("strap", arch, 0.026, 0.006, lambda q: (q - c).normalized(), "M_Fabric__0c4f4a", 2))
# adjuster buckle on the strap's left side
bi = 2
q = arch[bi]
tdir = (arch[bi + 1] - arch[bi - 1]).normalized()
nrm = (q - c).normalized()
parts += pk.buckle("strap_buckle", q + nrm * 0.004, nrm, tdir, 0.036, 0.026, 0.0045, BRASS, bar=True, prong=False)
for sx in (-1, 1):
    parts.append(pl.rivet(V((sx * (W / 2 + 0.014), 0.0, 0.205)), (sx, 0, 0), 0.0065, 0.005, BRASS, 6))

pouch = rw.join(parts, "PouchLey")
pk.fit(pouch, 0.35)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.35,))
