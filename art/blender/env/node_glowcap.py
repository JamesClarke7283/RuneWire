"""node_glowcap: "Glowcap Patch", a gathering node (picked), about 1.2 x 1.2 x 0.9 m. Origin at the ground centre.

Nodes:
  Stump    static base: a mossy, rotting tree stump (M_Bark) with five flared roots arching into the ground, a jagged
           broken rim of pale rotten wood (RotWood) around a dark hollow (RotWoodDark), puffy moss cushions on the
           rim, moss along the top of three roots, a dark knot hole and a pebble. Without the mushrooms it reads as
           a plain natural stump.
  Harvest  child of Stump, ONE object: a cluster of big cartoon toadstools with glowing teal-blue caps (GlowcapCap,
           rw.glow 4fd8ff), glowing gills (GlowcapGill), white spots and pale stems: five growing out of the hollow
           top and three from the bark on the sides (the game spins the node to a random yaw). Its origin is the
           top centre of the stump (the floor of the hollow): scaled to 0.05 the mushrooms sink into the stump
           (picked), scaled back to 1.0 they regrow.

Collision: Col_Patch_0-convcolonly, one cylinder (radius 0.55, height 0.9).
"""
import math
import os
import random
import sys

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "node_glowcap"
S.reset()
rnd = random.Random(17)

# --- the stump: one loft from the root flares up to a jagged rim and down into the hollow -------------------------
N = 18
R_TOP = 0.32


def flare(a, amt):
    return amt * max(0.0, math.cos(5 * a + 0.4)) ** 3


def jag(a):
    """Broken-wood rim: two tall splinters, a smaller one and a little unevenness."""
    return (0.15 * max(0.0, math.cos(a - 0.9)) ** 14 + 0.1 * max(0.0, math.cos(a - 3.6)) ** 12 +
            0.06 * max(0.0, math.cos(a - 5.2)) ** 10 + 0.012 * math.sin(7 * a))


def ring(r, z, fl=0.0, jg=0.0, wob=0.0):
    pts = []
    for i in range(N):
        a = 2 * math.pi * i / N
        rr = r * (1 + flare(a, fl) + wob * math.sin(3 * a + 1.0))
        pts.append((rr * math.cos(a), rr * math.sin(a), z + jg * jag(a)))
    return pts


rings = [ring(0.4, 0.0, 0.32), ring(0.37, 0.07, 0.18), ring(0.345, 0.17, 0.06, 0, 0.02), ring(0.33, 0.3, 0, 0, 0.02),
         ring(R_TOP, 0.39, 0, 0.5, 0.015), ring(R_TOP - 0.005, 0.44, 0, 1.0), ring(0.25, 0.43, 0, 0.8),
         ring(0.19, 0.37, 0, 0.2), ring(0.09, 0.34)]
stump = S.loft("stump", rings, "M_Bark", True, True, 40, fan=True)
bpy.context.view_layer.update()
rw.set_mat_where(stump, M("RotWood"), lambda c, n: c.z > 0.36 and math.hypot(c.x, c.y) < R_TOP - 0.01 and n.z > 0.2)
rw.set_mat_where(stump, M("RotWoodDark"), lambda c, n: math.hypot(c.x, c.y) < 0.235 and c.z > 0.3)
base = [stump]

# roots arching out of the flares into the ground
for k, (az, L) in enumerate(((10, 1.0), (84, 1.06), (156, 1.0), (232, 1.08), (300, 1.04))):
    pts = [G.radial(az, 0.2, 0.25), G.radial(az + 3, 0.35 * L, 0.17), G.radial(az + 7, 0.46 * L, 0.07),
           G.radial(az + 10, 0.56 * L, -0.04)]
    root = pl.sausage("root", pts, [0.11, 0.1, 0.075, 0.055], 7, 1, S.mat("M_Bark"), (False, True), 2, True, 60)
    G.clip_below(root, 0.0)
    if k in (0, 2, 3):    # a carpet of moss along the top of the root
        bpy.context.view_layer.update()
        rw.set_mat_where(root, M("Moss"), lambda c, n: n.z > 0.55 and 0.3 < math.hypot(c.x, c.y) < 0.52)
    base.append(root)

TOP, _ = S.surface_hit(stump, (0.0, 0.0, 50.0), (0, 0, -1))        # Harvest origin: top centre (hollow floor)

# moss: cushions on the rim and on top of some roots (dropped from above onto the stump / roots)
moss_pts = [(0.27, 0.08), (-0.06, 0.29), (-0.28, -0.06), (0.1, -0.28)]
for k, (x, y) in enumerate(moss_pts):
    p, n = S.surface_hit(stump, (x, y, 50.0), (0, 0, -1))
    if p is not None:
        r = rnd.uniform(0.08, 0.1)
        nn = (n + V((0, 0, 1.5))).normalized()
        base.append(G.dome("moss", r, r * 0.8, p, nn, "MossLight" if k % 2 else "Moss", 10, 2, 0.4,
                           squash=(1.3, 1.0), spin=math.degrees(math.atan2(y, x)), wall=False))
        base.append(G.dome("moss", r * 0.62, r * 0.6, p + G.radial(math.degrees(math.atan2(y, x)) + 90, r * 0.95),
                           nn, "Moss" if k % 2 else "MossLight", 8, 2, 0.4, wall=False))
# a dark rotten knot hole in the bark
p, n = S.hit_toward(stump, (0, 0, 0.24), G.radial(262, 1.0))
base.append(G.dome("knot", 0.06, 0.012, p, n, "RotWoodDark", 8, 1, 0.5, squash=(0.75, 1.25), wall=False))
base.append(pl.align(E.ring("knot_rim", 0.062, 0.018, (0, 0, 0), (0, 0, 1), "M_Bark", 10, 4), n, tuple(p)))
for k, (a, d, s) in enumerate(((50, 0.6, 0.12),)):
    p = S.hull_rock("pebble", (s * 1.4, s * 1.2, s), tuple(G.radial(a, d)), seed=31 + k, n_points=8, bevel=0.0,
                    flat_bottom=0.45)
    base.append(G.on_ground(p))

# --- the glowcaps (all one Harvest object) ---------------------------------------------------------------------------
caps = []


def top_pt(x, y):
    p, _ = S.surface_hit(stump, (x, y, 50.0), (0, 0, -1))
    return p


# in the hollow: one big, two medium and two small toadstools
for k, (x, y, az, lean, L, r, segs, spots) in enumerate((
        (0.02, 0.02, 205, 0.16, 0.36, 0.235, 12, 5),
        (0.12, -0.09, 300, 0.4, 0.22, 0.15, 10, 3),
        (-0.1, 0.11, 115, 0.42, 0.2, 0.14, 10, 3),
        (0.13, 0.13, 40, 0.55, 0.13, 0.085, 8, 2),
        (-0.15, -0.1, 235, 0.5, 0.12, 0.08, 8, 2))):
    caps += G.mushroom(top_pt(x, y) - V((0, 0, 0.01)), az, lean, L, r, segs=segs, spots=spots, seed=40 + k,
                       stem_segs=8 if r > 0.1 else 7, stem_res=2 if r > 0.2 else 1)
# from the bark on the sides: stems curl out and up
for k, (az, z, r, L) in enumerate(((330, 0.24, 0.11, 0.15), (150, 0.2, 0.095, 0.13), (65, 0.3, 0.075, 0.11))):
    d = G.radial(az, 1.0)
    p, n = S.hit_toward(stump, (0, 0, z), d)
    caps += G.mushroom(p - n * 0.03, az, 0.95, L, r, upright=0.75, segs=8, spots=2, seed=60 + k, stem_segs=7,
                       stem_res=1, kick=0.5)

stump_o = rw.join(base, "Stump", origin=(0, 0, 0))
harvest = G.join_harvest(caps, TOP, stump_o)

E.col_cyl("Patch", 0.55, 0.9, (0, 0, 0.45))
S.ground_centre([stump_o])
G.finish_node(ASSET, (1.2, 1.2, 0.9), 3000, stump_o, harvest, "top centre of the stump (hollow floor)",
              preview_glows={"GlowcapCap": ("1f8fc4", "4fd8ff", 0.75), "GlowcapGill": ("1c6fa8", "2f9fd6", 0.5)})
