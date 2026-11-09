"""node_ore_copper: "Copper Vein", a gathering node (mined), about 1.6 x 1.4 x 1.2 m. Origin at the ground centre.

Nodes:
  Rock     static base: a chunky outcrop of three rounded, faceted M_StoneRough boulders leaning on each other,
           and a few pebbles. Without the ore it reads as a plain natural rock pile.
  Harvest  child of Rock, ONE object (M_Copper): a crown of big faceted copper nuggets on top of the main boulder,
           nugget clusters on every side (the game spins the node to a random yaw) and flat copper veins, studded
           with small nuggets, winding down between them. Its origin is the top centre of the main boulder:
           scaled to 0.05 the ore sinks into the rock (mined), scaled back to 1.0 it regrows.

Collision: Col_Vein_0-convcolonly, one cylinder (radius 0.75, height 1.2).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "node_ore_copper"
S.reset()
ORE = "M_Copper"

# --- rock outcrop: a main boulder, two boulders leaning on it, pebbles ----------------------------------------------
main = S.hull_rock("main", (1.24, 1.18, 1.5), (0, 0, 0), seed=12, n_points=24, jitter=0.28, rmin=0.86,
                   flat_bottom=0.45, bevel=0.04)
G.on_ground(main)
side_a = S.hull_rock("side_a", (0.7, 0.62, 0.72), (0.5, -0.46, 0), seed=6, n_points=16, jitter=0.3, rmin=0.82,
                     flat_bottom=0.4, bevel=0.03, rot_z=25)
G.on_ground(side_a)
side_b = S.hull_rock("side_b", (0.58, 0.55, 0.62), (-0.54, 0.44, 0), seed=9, n_points=14, jitter=0.3, rmin=0.82,
                     flat_bottom=0.4, bevel=0.025, rot_z=-20)
G.on_ground(side_b)
base = [main, side_a, side_b]
for k, (a, d, s) in enumerate(((40, 0.74, 0.15), (172, 0.72, 0.12), (248, 0.66, 0.13), (332, 0.76, 0.1))):
    p = S.hull_rock("pebble", (s * 1.5, s * 1.25, s), tuple(G.radial(a, d)), seed=30 + k, n_points=9, bevel=0.01,
                    flat_bottom=0.45)
    base.append(G.on_ground(p))

mn, mx = rw.bounds([main])
C = V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.42 * (mx.z - mn.z)))   # main boulder centre (for ray casts)
TOP, _ = S.surface_hit(main, (C.x, C.y, 50.0), (0, 0, -1))                  # Harvest origin: main boulder top centre


def centre_of(o, z):
    a, b = rw.bounds([o])
    return V(((a.x + b.x) / 2, (a.y + b.y) / 2, z))


CA, CB = centre_of(side_a, 0.2), centre_of(side_b, 0.2)

# --- the copper (all one Harvest object) ---------------------------------------------------------------------------
ore = []


def nug(name, target, p, n, size, seed, lean=None, sink=0.42):
    if p is not None:
        big = max(size) >= 0.17          # small chunks skip the bevel (cheaper; the outline carries them)
        ore.append(G.nugget(name, size, p, n, seed=seed, m=ORE, sink=sink, lean=lean, bevel=0.012 if big else 0.0,
                            n_points=10 if big else 8))


def drop(target, x, y):
    return S.surface_hit(target, (x, y, 50.0), (0, 0, -1))


# crown: a big central chunk with four around it, leaning outward
for k, (dx, dy, size, lean) in enumerate((
        (0.0, 0.0, (0.34, 0.3, 0.6), None),
        (0.2, 0.1, (0.26, 0.23, 0.32), (0.4, 0.2, 0.0)),
        (-0.19, 0.12, (0.25, 0.22, 0.3), (-0.4, 0.25, 0.0)),
        (0.06, -0.2, (0.24, 0.22, 0.3), (0.1, -0.45, 0.0)),
        (-0.15, -0.14, (0.18, 0.16, 0.22), (-0.35, -0.3, 0.0)))):
    p, n = drop(main, TOP.x + dx, TOP.y + dy)
    nug("crown", main, p, n, size, 40 + k, lean)

# clusters around the sides (az: degrees from +X; the front is az 270), each joined to the crown by a flat vein
# studded with a small nugget
CLUSTERS = ((215, 30, 0.26), (305, 27, 0.24), (40, 30, 0.25), (128, 27, 0.23))
for k, (az, el, s) in enumerate(CLUSTERS):
    p, n = S.hit_toward(main, C, S.sph(az, el))
    nug("side", main, p, n, (s, s * 0.9, s * 1.15), 60 + k)
    for j, (daz, del_, f) in enumerate(((15, 8, 0.6), (-12, -6, 0.48))):
        p2, n2 = S.hit_toward(main, C, S.sph(az + daz, el + del_))
        nug("side_small", main, p2, n2, (s * f, s * f * 0.9, s * f * 1.1), 70 + 3 * k + j)
    # the seam runs from the crown, past the cluster, down to the foot of the boulder
    path = G.arc_dirs(az + 30, 72, az + 3, el + 4, 6, zig=5)
    path += G.arc_dirs(az - 2, el - 4, az - 16, -4, 5, zig=5)[1:]
    ore.append(G.vein("vein", main, C, path, 0.042, 0.0, ORE, taper=(0.75, 1.1), flat=(0.42, 1.5),
                      smooth_path=False))
    p3, n3 = S.hit_toward(main, C, path[3])
    nug("stud", main, p3, n3, (0.11, 0.1, 0.12), 80 + k, sink=0.45)
    p4, n4 = S.hit_toward(main, C, S.sph(az - 14, 0))
    nug("foot", main, p4, n4, (0.15, 0.14, 0.17), 84 + k, sink=0.45)
# nuggets on the two leaning boulders
p, n = drop(side_a, CA.x + 0.03, CA.y - 0.04)
nug("side_a", side_a, p, n, (0.22, 0.2, 0.26), 90, lean=(0.15, -0.25, 0.0))
p, n = drop(side_a, CA.x + 0.2, CA.y + 0.02)
nug("side_a", side_a, p, n, (0.14, 0.13, 0.16), 91, lean=(0.4, 0.0, 0.0))
p, n = drop(side_b, CB.x - 0.05, CB.y + 0.04)
nug("side_b", side_b, p, n, (0.19, 0.17, 0.22), 92, lean=(-0.25, 0.2, 0.0))

rock = rw.join(base, "Rock", origin=(0, 0, 0))
harvest = G.join_harvest(ore, TOP, rock)

E.col_cyl("Vein", 0.75, 1.2, (0, 0, 0.6))
S.ground_centre([rock])
G.finish_node(ASSET, (1.6, 1.4, 1.2), 3000, rock, harvest, "top centre of the main boulder")
