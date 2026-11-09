"""tree_dead: twisted, leafless spooky tree for the ruined shrine, about 6 m tall.

A leaning, gnarled trunk with five roots carries two crooked "arms" that reach out sideways and
then up into clawed twig tips (some curl), a back limb and a crooked leader. A broken stub and a
dark hollow on the front add character. One mesh object (Trunk: dusky M_Bark tint + flat "Hollow"),
origin at the base centre. Collision: trunk cylinder.
"""
import math
import os
import random
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

BARK = "M_Bark__5c5160"     # dusky grey-violet bark
rw.reset()
rng = random.Random(9)
parts = []


def rot_about(v, axis, deg):
    return (Matrix.Rotation(math.radians(deg), 3, Vector(axis).normalized()) @ Vector(v)).normalized()


def twig(p0, d, length, r0, name, curl=0.0):
    """Pointed claw twig; `curl` (degrees) hooks the end over."""
    d = Vector(d).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    pts = [Vector(p0)]
    seg = length / 3
    dd = d
    for i in range(3):
        bend = curl * (i / 2.0) if curl else rng.uniform(-14, 14)
        dd = rot_about(dd, side, -bend)
        pts.append(pts[-1] + dd * seg)
    radii = [r0, r0 * 0.75, r0 * 0.5, r0 * 0.3]
    parts.append(nl.sweep(name, pts, radii, sides=8, per_seg=3, mat=BARK, tip=r0 * 2.5))


def limb(name, pts, r0, r1, claws):
    """Hand-placed crooked limb + claw twigs at its end: claws = [(dir, length, curl), ...]."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    radii = [r0 + (r1 - r0) * (i / (n - 1)) ** 0.8 for i in range(n)]
    parts.append(nl.sweep(name, pts, radii, sides=10, per_seg=3, mat=BARK))
    end = pts[-1]
    for i, (d, L, curl) in enumerate(claws):
        twig(end - (end - pts[-2]).normalized() * r1, d, L, r1 * 0.85, "%s_c%d" % (name, i), curl)


# --- trunk -------------------------------------------------------------------------------------
ang = nl.root_angles(5, seed=19)
gnarl = nl.lumpy_shaper(0.07, 1.3, seed=5, base=nl.root_shaper(ang, 0.32, 1.0, seed=19, sharp=4.0, foot=0.25))
trunk_pts = [(0, 0, -0.3), (0.08, 0.0, 0.8), (0.3, 0.04, 1.7), (0.32, 0.1, 2.5), (0.12, 0.15, 3.3),
             (-0.05, 0.2, 4.1), (0.05, 0.25, 4.85)]
parts.append(nl.sweep("Trunk", trunk_pts, [0.5, 0.42, 0.37, 0.32, 0.25, 0.18, 0.12], sides=16, per_seg=3,
                      mat=BARK, shaper=gnarl, twist=1.4))
parts += nl.root_sweeps(ang, seed=19, top=1.25, reach=1.45, r_top=0.3, r_tip=0.07, start_r=0.2, depth=-0.3,
                        reach_jitter=0.2, mid="fillet", mat=BARK)
# leader claws
for i, (d, L, c) in enumerate((((-0.5, 0.1, 1.0), 0.9, 0), ((0.6, 0.2, 1.0), 0.75, 40), ((0.1, -0.6, 0.9), 0.6, 0))):
    twig(trunk_pts[-1], d, L, 0.1, "lead_c%d" % i, c)

# --- arms and limbs ----------------------------------------------------------------------------
limb("ArmL", [(0.25, 0.06, 2.2), (-0.35, 0.0, 2.55), (-1.05, -0.12, 2.75), (-1.65, -0.18, 3.25),
              (-1.95, -0.12, 3.95)], 0.24, 0.11,
     [((-0.35, 0.0, 1.0), 0.95, 0), ((-0.9, -0.2, 0.6), 0.8, 55), ((0.1, -0.5, 1.0), 0.7, 0)])
limb("ArmR", [(0.3, 0.08, 2.65), (0.9, -0.08, 3.0), (1.55, -0.2, 3.15), (2.05, -0.25, 3.65),
              (2.25, -0.2, 4.3)], 0.22, 0.1,
     [((0.25, 0.1, 1.0), 0.9, 0), ((0.9, -0.1, 0.5), 0.75, -60), ((-0.2, 0.5, 1.0), 0.65, 0)])
limb("LimbB", [(0.15, 0.15, 3.0), (0.25, 0.7, 3.45), (0.4, 1.25, 3.9), (0.3, 1.6, 4.5)], 0.19, 0.09,
     [((0.0, 0.4, 1.0), 0.8, 0), ((0.5, 0.6, 0.4), 0.6, 50)])
# mid-arm claws for a busier silhouette
twig((-1.05, -0.12, 2.8), (-0.2, -0.6, 0.8), 0.75, 0.1, "midL", 0)
twig((1.55, -0.2, 3.2), (0.3, 0.6, 0.75), 0.7, 0.095, "midR", 35)
# broken stub low on the trunk
parts.append(nl.sweep("stub", [(0.3, 0.05, 1.55), (0.62, -0.25, 1.8), (0.78, -0.4, 1.92)], [0.15, 0.12, 0.1],
                      sides=10, per_seg=2, mat=BARK))

trunk = rw.join(parts, "Trunk", origin=(0, 0, 0))
nl.fuse(trunk, 0.02, 3300, smooth_iters=1)

# --- the hollow: dig a pit into the front of the trunk and paint it dark --------------------------
hit_z = 1.25
ok, loc, nor, _ = trunk.ray_cast(Vector((0.22, -3.0, hit_z)), Vector((0, 1, 0)))
if ok:
    c = loc + Vector((0, 0.16, 0))
    cutter = rw.ico("hollow_cut", 0.5, 3, tuple(c), scale=(0.36, 0.42, 0.6))
    rw.boolean(trunk, cutter, 'DIFFERENCE')
    dark = rw.flat("Hollow", "1e1626", 0.9)
    rw.set_mat_where(trunk, dark, lambda p, n: ((p.x - c.x) / 0.19) ** 2 + ((p.z - c.z) / 0.31) ** 2 < 1.0
                     and p.y > loc.y - 0.01)
    nl.shade_smooth_all(trunk)

# --- collision -------------------------------------------------------------------------------
rw.collision_cylinder("TrunkCol", 0.4, 3.2, loc=(0.15, 0.05, 1.3))

print("RWREPORT   trunk tris %d" % nl.tris(trunk))
rw.finish("tree_dead", "nature")
nl.finish_extra("tree_dead", "nature", views=("side", "front"))
