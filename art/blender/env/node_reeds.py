"""node_reeds: "Reed Clump", a gathering node (cut), about 1.2 x 1.2 x 1.8 m. Origin at the ground centre.

Nodes:
  Mud      static base: a small, lumpy mound of shore mud (Mud on top, darker wet MudDark on the flanks), a little
           puddle (Water), a few pebbles and a ring of cut reed stubs with slanted tops (ReedStub). Without the
           reeds it reads as a freshly cut reed bed.
  Harvest  child of Mud, ONE object: a clump of tall, strap-like golden-green reed blades arching outward (some bent
           over near the tip) and seven cattails: green stalks with fat brown velvety heads and little spikes on top,
           up to 1.8 m tall (the game spins the node to a random yaw). Its origin is the ground centre: scaled to
           0.05 the reeds sink into the mud (cut), scaled back to 1.0 they regrow.

Material notes (stationlib): everything in Harvest uses "ReedGrass*" materials. Godot gives "grass" names the
wind-sway foliage shader (double-sided), which moves each vertex by its height above the node origin; since blades,
stalks and heads all sway the same way, the cattail heads stay on their stalks. The stubs in the base are short and
don't sway.

Collision: Col_Reeds_0-convcolonly, one cylinder (radius 0.5, height 1.6).
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "node_reeds"
S.reset()
rnd = random.Random(29)
UP = V((0, 0, 1))

# --- the mud mound -------------------------------------------------------------------------------------------------
N = 16


def lump(a):
    return 0.1 * math.sin(3 * a + 0.6) + 0.06 * math.sin(5 * a + 2.0)


rings = [S.ring_pts(N, 0.56, 0.52, 0.0, wob=lump), S.ring_pts(N, 0.5, 0.46, 0.05, wob=lambda a: lump(a) * 0.8),
         S.ring_pts(N, 0.36, 0.33, 0.1, wob=lambda a: lump(a) * 0.5), S.ring_pts(N, 0.16, 0.15, 0.125)]
mud = S.loft("mud", rings, "Mud", True, True, 40, fan=True)
bpy.context.view_layer.update()
rw.set_mat_where(mud, M("MudDark"), lambda c, n: n.z < 0.5)     # wet, darker flanks
base = [mud]
# a little puddle on the front-left slope
p, n = S.surface_hit(mud, (-0.34, -0.2, 5.0), (0, 0, -1))
puddle = rw.cylinder("puddle", 0.075, 0.01, 10, (0, 0, 0), (0, 0, 0), M("Water"))
pl.xform(puddle, Matrix.Diagonal((1.5, 1.0, 1.0, 1.0)) @ Matrix.Rotation(math.radians(-30), 4, 'Z'))
base.append(pl.align(puddle, n, tuple(p - n * 0.002)))
for k, (a, d, s) in enumerate(((20, 0.56, 0.1), (160, 0.55, 0.12), (285, 0.5, 0.08))):
    pb = S.hull_rock("pebble", (s * 1.5, s * 1.2, s), tuple(G.radial(a, d)), seed=60 + k, n_points=8, bevel=0.0,
                     flat_bottom=0.45)
    base.append(G.on_ground(pb))
# cut stubs: what the reed cutter leaves behind
for k in range(9):
    a = 360.0 * k / 9 + rnd.uniform(-12, 12)
    d = rnd.uniform(0.08, 0.3)
    q, _ = S.surface_hit(mud, tuple(G.radial(a, d, 5.0)), (0, 0, -1))
    base.append(G.stub("stub", q - V((0, 0, 0.03)), rnd.uniform(0.02, 0.026), rnd.uniform(0.1, 0.17),
                       (math.cos(math.radians(a + 60)), math.sin(math.radians(a + 60))), 0.9, "ReedStub", 6))
mud_o = rw.join(base, "Mud", origin=(0, 0, 0))

# --- the reeds (all one Harvest object) ----------------------------------------------------------------------------
reeds = []
BLADE_MATS = ("ReedGrass", "ReedGrassGold", "ReedGrassGreen")
NB = 22
for k in range(NB):
    a = 360.0 * k / NB + rnd.uniform(-6, 6)
    out = G.radial(a, 1.0)
    d0 = rnd.uniform(0.04, 0.22)
    b = G.radial(a, d0, 0.06)
    h = rnd.uniform(0.95, 1.5) * (1.0 - d0 * 0.8)
    lean = rnd.uniform(0.18, 0.3) + d0 * 0.5
    bend = k % 3 == 1                            # every third blade flops over near the tip
    pts = [b, b + UP * h * 0.4 + out * lean * 0.12, b + UP * h * 0.75 + out * lean * 0.45]
    if bend:
        pts.append(b + UP * h * 0.88 + out * lean * 0.8)
        pts.append(b + UP * h * 0.74 + out * (lean * 0.8 + 0.18))
    else:
        pts.append(b + UP * h + out * lean)
    w = rnd.uniform(0.095, 0.115)
    ws = [w, w * 0.95, w * 0.72] + ([w * 0.42, 0.0] if bend else [0.0])
    side = UP.cross(out).normalized()
    tw = math.radians(rnd.uniform(25, 50) * (1 if k % 2 else -1))
    side = (side * math.cos(tw) + out * math.sin(tw)).normalized()
    reeds.append(G.ribbon("blade", pts, ws, side, BLADE_MATS[k % 3], keel=0.1, thick=0.01, res=2, tri=True))
# cattails: stalk, fat brown head, little spike
for k, (a, d, h, lean) in enumerate(((10, 0.06, 1.74, 0.1), (75, 0.14, 1.5, 0.2), (140, 0.1, 1.62, 0.16),
                                     (200, 0.16, 1.36, 0.26), (255, 0.05, 1.56, 0.12), (310, 0.15, 1.44, 0.22),
                                     (330, 0.24, 1.2, 0.3))):
    out = G.radial(a, 1.0)
    b = G.radial(a, d, 0.05)
    top = b + UP * h + out * lean

    def at(t):
        return b + UP * (h * t) + out * (lean * t * t)
    hb, ht = 0.72, 0.89                          # head from 72 % to 89 % of the stalk
    reeds.append(pl.sausage("stalk", [b, at(0.4), at(hb + 0.02)], [0.02, 0.018, 0.016], 5, 2, S.mat("ReedGrassGreen"),
                            (False, False), 1, True, 60))
    reeds.append(pl.sausage("head", [at(hb), at((hb + ht) / 2), at(ht)], [0.05, 0.055, 0.048], 8, 1,
                            S.mat("ReedGrassHead"), (True, True), 2, True, 70))
    reeds.append(pl.sausage("spike", [at(ht - 0.01), at(ht + 0.05), top], [0.015, 0.011, 0.006], 5, 1,
                            S.mat("ReedGrass"), (False, False), 1, True, 60))

harvest = G.join_harvest(reeds, (0, 0, 0), mud_o)

E.col_cyl("Reeds", 0.5, 1.6, (0, 0, 0.8))
G.ground_centre_on(None, [mud_o])      # built around the clump axis at the world origin: only drop it to z = 0
G.finish_node(ASSET, (1.2, 1.2, 1.8), 3000, mud_o, harvest, "ground centre")
