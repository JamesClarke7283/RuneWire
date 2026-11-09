"""item_pouch_scavenger: "Scavenger's Sack", a big lumpy burlap sack of salvage, about 0.30 x 0.26 x 0.36 m.

A big, slouching, lumpy sack of dark burlap (M_Fabric__9c7442) bulging with salvage, patched with a riveted steel
plate and a riveted rusty plate, its neck tied with a fat rope knot; a brass gear and a steel gear poke out of
the ruffled mouth, and a red horseshoe magnet with steel tips hangs from the knot on a short cord, resting on the sack.
One mesh object "PouchScavenger", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_scavenger"
rw.reset()

BURLAP = "M_Fabric__9c7442"
ZN = 0.25
outer = [(0.0, 0.0), (0.1, 0.006), (0.15, 0.06), (0.15, 0.15), (0.12, 0.202), (0.08, 0.235),
         (0.058, ZN), (0.066, 0.27), (0.094, 0.302), (0.1, 0.318)]
inner = [(0.098, 0.326), (0.089, 0.33), (0.08, 0.321), (0.058, 0.3), (0.0, 0.292)]
sk = pk.Sack("sack", outer, inner, segs=28, per_seg=2, m=BURLAP, folds=(7, 0.14, ZN, 0.042),
             ruffle=(7, 0.16, ZN + 0.012, 0.322, 0.012),
             lumps=((2, 0.06, 20, 0.11, 0.07), (3, 0.05, 110, 0.07, 0.06), (5, 0.035, 40, 0.15, 0.05)),
             squash=0.84, lean=0.022, seed=5)
S = sk.surf
parts = [sk.obj]

# riveted metal patches
for (m, az, z, w, h, turn) in (("M_Steel", -38, 0.1, 0.085, 0.07, 6), ("M_Rust", 58, 0.15, 0.065, 0.075, -10)):
    a = math.radians(az)
    proj = pk.proj_plane((0, 0, z), (math.sin(a), -math.cos(a), 0))
    parts.append(pk.surf_slab("plate", S, proj, pk.squircle_map(w, h, 6.0, angle=turn), 4, 4, 0.001, 0.006, m))
    PS = pk.Surface(parts[-1])
    ca, sa = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = u * (w / 2 - 0.011), v * (h / 2 - 0.011)
        P, N = pk.surf_point(PS, proj, x * ca - y * sa, x * sa + y * ca)
        parts.append(pl.rivet(P, N, 0.0075, 0.0055, pk.mat("M_Steel"), 6))

# gears poking out of the mouth
parts.append(il.gear("gear_big", 0.056, 8, 0.016, 0.017, 0.0, (0.012, -0.014, 0.34), (0.35, -0.55, 0.55),
                     "M_Brass", spin=5))
parts.append(il.gear("gear_small", 0.036, 8, 0.011, 0.014, 0.0, (-0.04, 0.022, 0.326), (-0.6, -0.2, 0.55),
                     "M_Steel", spin=12))
parts.append(pl.rod("pipe", V((0.05, 0.03, 0.29)), V((0.07, 0.045, 0.345)), 0.011, 8, pk.mat("M_Copper")))

# rope tie with a fat knot at the front
c, rx, ry = sk.neck_ellipse(ZN + 0.002, 0.004)
parts.append(pk.loop_tube("rope", pk.ellipse_loop(c, rx, ry, 20), 0.0095, 6, "Twine"))
ka = math.radians(-24)
kd = V((math.sin(ka), -math.cos(ka), 0))
kp = c + V((kd.x * rx, kd.y * ry, 0)) + kd * 0.008
parts.append(pk.knot("knot", kp, 0.022, "Twine", (1.15, 0.85, 0.9), 2, 9, 6))
tail = [kp + V((0.006, -0.008, -0.004)), kp + V((0.022, -0.018, -0.022)), kp + V((0.03, -0.02, -0.05))]
parts.append(pl.sausage("rope_end", tail, [0.0085, 0.0085, 0.0075], 6, 1, pk.mat("Twine"), (True, True), 1, True, 60))

# horseshoe magnet hanging from the knot on a short cord, resting on the sack's bulging shoulder
MR, MT = 0.027, 0.0115                                  # bend radius, tube radius
guess = kp + V((-0.012, -0.055, -0.075))
p, n = S.nearest(guess)
mc = p + n * (MT + 0.004)                               # centre of the magnet's bend circle
uy = (kp - mc)
uy = (uy - uy.dot(n) * n).normalized()                  # in the surface plane, pointing back up at the knot
ux = n.cross(uy).normalized()
bend_top = mc + uy * MR
U = [mc + ux * (MR * math.cos(math.radians(t))) + uy * (MR * math.sin(math.radians(t)))
     for t in (180, 135, 90, 45, 0)]
U = [U[0] - uy * 0.026] + U + [U[-1] - uy * 0.026]
parts.append(pl.sausage("magnet", U, MT, 8, 2, pk.mat("MagnetRed"), (False, False), 1, True, 60))
for s_ in (-1, 1):
    tip0 = mc + ux * (s_ * MR) - uy * 0.026
    parts.append(pl.capsule("magnet_tip", tip0 + uy * 0.002, tip0 - uy * 0.018, MT * 1.03, 8, 1, pk.mat("Silver")))
ring = rw.torus("charm_ring", 0.009, 0.003, 10, 4, (0, 0, 0), mat=pk.mat("M_Steel"))
pl.align(ring, ux, bend_top + uy * 0.008)
parts.append(ring)
cord = [kp + V((-0.002, -0.012, -0.012)), (kp + bend_top) / 2 + n * 0.012, bend_top + uy * 0.014]
parts.append(pl.sausage("charm_cord", cord, 0.0035, 5, 2, pk.mat("Cord"), (True, True), 1, True, 60))

pouch = rw.join(parts, "PouchScavenger")
pk.fit(pouch, 0.36)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.36,))
