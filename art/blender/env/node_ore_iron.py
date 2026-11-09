"""node_ore_iron: "Iron Vein", a gathering node (mined), about 1.6 x 1.4 x 1.2 m. Origin at the ground centre.

The iron counterpart of node_ore_copper with a different look: a darker, blocky crag with clean fracture faces
and a slanted broken top instead of a heap of rounded boulders. It matches the item it yields (item_iron_ore):
the same dark blue-grey stone crusted with bubbly rust nodules.

Nodes:
  Rock     static base: a blocky dark blue-grey boulder (M_StoneRough tinted to #4b5468 in game, the same material
           as item_iron_ore) with a slanted broken top and fracture faces, a smaller block leaning on its low
           front-right corner, angular chunks and pebbles. Without the ore it reads as a plain natural crag.
  Harvest  child of Rock, ONE object: bubbly clusters of round rusty red-brown iron nodules (M_Rust, a few in
           M_DarkMetal), a crown of octahedral grey metal crystals (M_DarkMetal) on the high back edge and rust seams
           zig-zagging down every side (the game spins the node to a random yaw). Its origin is the top centre of
           the boulder: scaled to 0.05 the ore sinks into the rock (mined), scaled back to 1.0 it regrows.

Collision: Col_Vein_0-convcolonly, one cylinder (radius 0.75, height 1.2).
"""
import math
import os
import sys

from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "node_ore_iron"
S.reset()
ROCK = G.tinted("M_StoneRough", "4b5468")      # dark blue-grey in game (as item_iron_ore) and in the previews
RUST, METAL = "M_Rust", "M_DarkMetal"

# --- the crag: a blocky boulder with a slanted broken top, a leaning block, chunks and pebbles ---------------------
main = S.hull_rock("main", (1.36, 1.16, 1.74), (0, 0, 0), seed=8, n_points=18, jitter=0.24, rmin=0.86,
                   flat_bottom=0.5, dissolve_deg=6, bevel=0.035, m=ROCK,
                   cuts=[((0.0, 0.0, 0.5), (0.32, -0.36, 1.0)),        # slanted top, high at the back-left
                         ((0.56, 0.0, 0.0), (1.0, 0.3, 0.06)),         # fracture face, right
                         ((0.0, -0.5, 0.0), (-0.2, -1.0, 0.1))])       # fracture face, front
main.location = (-0.07, 0.05, 0.0)
G.on_ground(main)
lean = S.hull_rock("lean", (0.5, 0.62, 0.95), (0, 0, 0), seed=3, n_points=12, jitter=0.2, rmin=0.88, flat_bottom=0.4,
                   dissolve_deg=8, bevel=0.03, m=ROCK, cuts=[((0.0, 0.0, 0.3), (0.4, -0.5, 1.0))])
G.xform([lean], Matrix.Translation((0.55, -0.4, 0.0)) @ Matrix.Rotation(math.radians(-35), 4, 'Z') @
        Matrix.Rotation(math.radians(-16), 4, 'Y'))
G.on_ground(lean)
base = [main, lean]
for k, (x, y, s, rz) in enumerate(((-0.62, -0.38, (0.38, 0.34, 0.32), 20), (0.6, 0.4, (0.34, 0.3, 0.28), -15),
                                   (-0.5, 0.52, (0.3, 0.28, 0.24), 40))):
    c = S.hull_rock("chunk", s, (x, y, 0), seed=20 + k, n_points=8, jitter=0.2, rmin=0.88, flat_bottom=0.4,
                    dissolve_deg=10, bevel=0.02, m=ROCK, rot_z=rz)
    base.append(G.on_ground(c))
for k, (a, d, s) in enumerate(((15, 0.8, 0.12), (110, 0.74, 0.11), (200, 0.78, 0.12), (300, 0.76, 0.1))):
    p = S.hull_rock("pebble", (s * 1.5, s * 1.2, s), tuple(G.radial(a, d)), seed=40 + k, n_points=7, bevel=0.0,
                    flat_bottom=0.45, m=ROCK)
    base.append(G.on_ground(p))

mn, mx = rw.bounds([main])
C = V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.42 * (mx.z - mn.z)))   # boulder centre (for ray casts)
TOP, _ = S.surface_hit(main, (C.x, C.y, 50.0), (0, 0, -1))                  # Harvest origin: boulder top centre
lmn, lmx = rw.bounds([lean])
CL = V(((lmn.x + lmx.x) / 2, (lmn.y + lmx.y) / 2, 0.35))

# --- the iron (all one Harvest object) -----------------------------------------------------------------------------
ore = []


def drop(target, x, y):
    return S.surface_hit(target, (x, y, 50.0), (0, 0, -1))


def crystal(p, n, s, seed, lean_=None, tall=1.5):
    """A grey metal octahedron (magnetite-like) of width s jutting from the rock."""
    if p is not None:
        d = (V(n) + V(lean_)).normalized() if lean_ else V(n)
        ore.append(G.octa("metal", s * 0.5, s * 0.5 * tall, p, d, seed, METAL, 0.33, 18,
                          0.012 if s >= 0.15 else 0.0))


def cluster(target, centre, d, count, r, seed, dark=-1):
    parts = G.nodules("nodule", target, centre, d, count, r, 12, seed, RUST)
    if 0 <= dark < len(parts):
        rw.set_mat(parts[dark], S.mat(METAL))
    ore.extend(parts)


# crown: grey metal crystals along the high back-left edge of the slanted top, with nodules at their feet
for k, (dx, dy, s, lean_) in enumerate(((-0.24, 0.18, 0.28, (-0.12, 0.1, 0.0)), (-0.02, 0.3, 0.21, (0.0, 0.25, 0.0)),
                                        (-0.36, -0.04, 0.19, (-0.25, -0.1, 0.0)))):
    p, n = drop(main, TOP.x + dx, TOP.y + dy)
    crystal(p, n, s, 50 + k, lean_)
for k, (dx, dy, r) in enumerate(((-0.1, 0.02, 0.13), (0.22, -0.12, 0.12))):
    p, _ = drop(main, TOP.x + dx, TOP.y + dy)
    cluster(main, C, p - C, 4, r, 60 + k, dark=2 if k == 1 else -1)

# the sides: a bubbly nodule cluster on each face, rust seams zig-zagging down between them
SIDES = ((225, 22, 0.12), (315, 16, 0.12), (45, 24, 0.12), (135, 18, 0.11))
for k, (az, el, r) in enumerate(SIDES):
    cluster(main, C, S.sph(az, el), 4, r * 1.08, 70 + k, dark=3 if k % 2 else -1)
    if k % 2 == 0:
        p, n = S.hit_toward(main, C, S.sph(az - 18, el - 16))
        cluster(main, C, p - C, 2, r * 0.75, 76 + k)
    if k < 3:
        path = G.arc_dirs(az + 30, 60, az + 12, -6, 9, zig=5)
        ore.append(G.vein("seam", main, C, path, 0.03, 0.0, RUST, taper=(0.7, 1.05), flat=(0.42, 1.5),
                          smooth_path=False))
# on the leaning block
cluster(lean, CL, V((0.75, -0.6, 0.45)), 3, 0.11, 90)
p, n = drop(lean, CL.x - 0.05, CL.y + 0.05)
crystal(p, n, 0.15, 91, (0.2, -0.3, 0.0), 1.3)

rock = rw.join(base, "Rock", origin=(0, 0, 0))
harvest = G.join_harvest(ore, TOP, rock)

E.col_cyl("Vein", 0.75, 1.2, (0, 0, 0.6))
S.ground_centre([rock])
G.finish_node(ASSET, (1.6, 1.4, 1.2), 3000, rock, harvest, "top centre of the boulder")
