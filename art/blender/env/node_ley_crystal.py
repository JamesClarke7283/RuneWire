"""node_ley_crystal: a harvestable ley-crystal cluster, about 1.4 x 1.4 x 1.6 m. Origin at the ground centre.

Nodes:
  Rock       static base: a chunky faceted rock (M_StoneRough) with soft moss cushions, a few pebbles and three
             little crystal nubs that stay behind after harvesting (so a harvested node still reads as one).
  Crystals   child of Rock, ONE object: seven big chunky faceted teal ley crystals (M_Crystal) growing out of the
             rock top. Its origin is the top centre of the rock base, so scaling it towards 0 shrinks the
             crystals back into the rock (harvest) and scaling to 1 regrows them.

Collision: Col_Cluster_0-convcolonly, one cylinder (radius 0.65, height 1.5) around the whole cluster.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "items"))
import envlib as E  # noqa: E402
import itemlib as il  # noqa: E402

rw, pl, V = E.rw, il.pl, il.V
ASSET = "node_ley_crystal"
rw.reset()
il.preview_glow("M_Crystal", "3ad9c8", "40e8da", 0.6)   # preview/icon only: Godot uses its crystal set

# rock base ------------------------------------------------------------------------------------------------------
RS = (1.38, 1.34, 0.66)
rock = il.hull_rock("Rock", RS, (0, 0, 0), seed=21, n_points=18, jitter=0.3, rmin=0.86, flat_bottom=0.4,
                    bevel=0.04, m="M_StoneRough")
bpy_mn, bpy_mx = rw.bounds([rock])
rock.location.z = -bpy_mn.z                     # sit the rock on the ground
top, _ = il.surface_hit(rock, (0, 0, 10), (0, 0, -1))
TOP = V((0, 0, top.z))
parts = [rock]
parts += il.moss_on(rock, [(0.42, -0.25), (-0.45, -0.18), (-0.2, 0.42), (0.35, 0.33), (0.05, -0.45), (-0.5, 0.2)],
                    0.26, 7, squash=0.4)
for k, (a, d, s) in enumerate(((20, 0.72, 0.13), (150, 0.7, 0.1), (250, 0.66, 0.12), (310, 0.74, 0.09))):
    x, y = math.cos(math.radians(a)) * d, math.sin(math.radians(a)) * d
    parts.append(il.hull_rock("pebble", (s * 1.6, s * 1.3, s), (x, y, s * 0.3), seed=40 + k, n_points=10,
                              bevel=0.01, m="M_StoneRough", flat_bottom=0.4))
# little crystal nubs that stay after harvesting
for (a, d, L) in ((205, 0.42, 0.2), (330, 0.4, 0.17), (95, 0.38, 0.15)):
    dirv = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
    p, n = il.surface_hit(rock, tuple(dirv * d + V((0, 0, 10))), (0, 0, -1))
    if p is not None:
        parts.append(pl.crystal("nub", p - n * 0.03, (n + dirv * 0.4 + V((0, 0, 0.6))).normalized(), L, 0.055, 6, 0.35,
                                0.1, il.mat("M_Crystal"), a))
rock_o = rw.join(parts, "Rock", origin=(0, 0, 0))
rw.smooth(rock_o, 30)

# crystals: one object, origin at the top centre of the rock -----------------------------------------------------
SPECS = [
    ((0.06, -0.03, 1.0), 1.3, 0.19, 0),
    ((0.6, -0.42, 0.68), 0.86, 0.145, 20),
    ((-0.66, -0.3, 0.7), 0.8, 0.14, 35),
    ((-0.22, 0.72, 0.66), 0.82, 0.145, 10),
    ((0.52, 0.5, 0.72), 0.7, 0.125, 45),
    ((-0.1, -0.85, 0.52), 0.55, 0.115, 5),
    ((0.85, 0.05, 0.5), 0.45, 0.1, 25),
]
cr = []
for i, (d, L, r, spin) in enumerate(SPECS):
    d = V(d).normalized()
    base = TOP + V((d.x, d.y, 0)) * 0.12 - V((0, 0, 0.12))
    cr.append(pl.crystal("crystal%d" % i, base, d, L, r, 6, 0.3, 0.12, il.mat("M_Crystal"), spin))
crystals = rw.join(cr, "Crystals", origin=tuple(TOP))
rw.flat_shade(crystals)
pl.parent_keep(crystals, rock_o)

E.col_cyl("Cluster", 0.65, 1.5, (0, 0, 0.75))
E.check(ASSET, (1.4, 1.4, 1.6), 3000)
print("RWREPORT   Crystals origin (rock top centre) at (%.3f, %.3f, %.3f)" % tuple(crystals.matrix_world.translation))
rw.finish(ASSET, "env", previews=E.previews())
