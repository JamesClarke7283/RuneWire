"""prop_sky_island: a small floating island, about 8 x 8 x 5 m.

ORIGIN AT THE CENTRE OF THE TOP WALKING SURFACE: the grassy top is at z = 0 and everything else hangs below.

A flat, very gently domed grassy top ("IslandGrass", a flat green; deliberately not named "Grass" so Godot
does not give the walkable ground its wind-sway foliage shader) with a rounded-square outline (so the square
collision box fits it), a soft rolled edge and a scalloped turf lip; a chunky faceted rocky underside
(M_StoneRough) in four stepped strata with jutting ledges and moss, tapering to a point about 3.55 m down;
thick dangling roots, teal ley crystals (M_Crystal) hanging beneath it (the lowest tip about 4.7 m down), and
on top a few mossy boulders, two round flowering bushes and some grass tufts.

Collision (-colonly boxes): Col_Top_0 (7 x 7 x 0.6, top face at z = 0) and Col_Under_0 / Col_Under_1 for the
rocky underside.
"""
import math
import os
import random
import sys

import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "items"))
import envlib as E  # noqa: E402
import itemlib as il  # noqa: E402

rw, pl, V = E.rw, il.pl, il.V
ASSET = "prop_sky_island"
rw.reset()
rnd = random.Random(7)
il.preview_glow("M_Crystal", "3ad9c8", "40e8da", 0.6)   # preview/icon only: Godot uses its crystal set
GRASS = rw.flat("IslandGrass", "6cc24a", 0.85, 0.0)
GRASS_DARK = rw.flat("IslandGrassDark", "4f9e3a", 0.85, 0.0)
R_TOP = 3.8                        # half-width of the walkable top at its edge middles
N = 48                             # outline points


def outline_r(a):
    """Rounded-square outline (superellipse p = 3.5) with an organic wobble, so the 7 x 7 m top collision box
    fits it closely: the edge middles sit 0.3 m outside the box, its corners about 0.5 m outside the grass."""
    c, s_ = abs(math.cos(a)), abs(math.sin(a))
    p = 3.5
    sq = (c ** p + s_ ** p) ** (-1.0 / p)
    return R_TOP * sq * (1 + 0.035 * math.sin(3 * a + 0.4) + 0.025 * math.sin(5 * a + 1.3))


# --- grassy top: a flat disc with a soft rolled edge (z = 0 at the centre) ------------------------------------------
def top_surface():
    bm = bmesh.new()
    rings = []
    prof = [(0.0, 0.0), (0.4, -0.006), (0.7, -0.02), (0.88, -0.045), (0.95, -0.08), (0.99, -0.15), (1.0, -0.26),
            (0.99, -0.36), (0.96, -0.42)]
    centre = bm.verts.new((0, 0, 0))
    for (f, z) in prof[1:]:
        ring = []
        for i in range(N):
            a = 2 * math.pi * i / N
            r = outline_r(a) * f
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for i in range(N):
        j = (i + 1) % N
        bm.faces.new((centre, rings[0][i], rings[0][j]))
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(N):
            j = (i + 1) % N
            bm.faces.new((a[i], b[i], b[j], a[j]))
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm("top", bm, GRASS, 40)


parts = [top_surface()]
# scalloped turf lip: soft green lobes hanging over the edge
for i in range(30):
    a = 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / 30
    r = outline_r(a) * 0.985
    s = rnd.uniform(0.4, 0.58)
    parts.append(rw.ico("lip", 0.5, 1, (r * math.cos(a), r * math.sin(a), -0.34 - rnd.uniform(0, 0.08)),
                        (0, 0, math.degrees(a)), (s * 0.55, s * 1.3, s * 0.55), GRASS if i % 3 else GRASS_DARK, None, 60))


# --- rocky underside: stepped faceted frustums following the outline, tapering to a point -------------------------
def stratum(name, z0, z1, f0, f1, seed, n=11, bulge=0.06):
    """Faceted rock frustum between z0 (top, radius f0 x outline) and z1 (bottom, radius f1 x outline)."""
    r = random.Random(seed)
    pts = []
    ph = r.uniform(0, 2 * math.pi)
    for (z, f, k) in ((z0, f0, n), ((z0 + z1) / 2, (f0 + f1) / 2 * (1 + bulge), n - 2), (z1, f1, max(5, n - 4))):
        for i in range(k):
            a = ph + 2 * math.pi * (i + r.uniform(-0.25, 0.25)) / k
            rr = outline_r(a) * f * r.uniform(0.92, 1.0)
            pts.append((rr * math.cos(a), rr * math.sin(a), z + r.uniform(-0.12, 0.12) * (z0 - z1) * 0.5))
    bm = bmesh.new()
    for q in pts:
        bm.verts.new(q)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(6), verts=bm.verts[:], edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = pl.obj_from_bm(name, bm, "M_StoneRough", 0)
    rw.flat_shade(o)
    md = o.modifiers.new("Bevel", 'BEVEL')
    md.width = 0.06
    md.segments = 1
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(25)
    md.harden_normals = True
    rw.apply_modifiers(o)
    return o


STRATA = [  # z top, z bottom, radius fraction top, bottom
    (-0.25, -1.35, 0.95, 0.82, 3),
    (-1.22, -2.2, 0.72, 0.55, 5),
    (-2.08, -2.95, 0.49, 0.3, 9),
    (-2.82, -3.55, 0.27, 0.03, 13),
]
for (z0, z1, f0, f1, seed) in STRATA:
    parts.append(stratum("stratum", z0, z1, f0, f1, seed))
# jutting ledges on the sides
for k, (a, z, f, s) in enumerate(((30, -0.9, 0.86, 1.0), (165, -1.5, 0.82, 0.85), (255, -0.85, 0.86, 0.9),
                                  (100, -2.2, 0.6, 0.75), (320, -2.5, 0.5, 0.7))):
    ar = math.radians(a)
    d = V((math.cos(ar), math.sin(ar), 0))
    parts.append(il.hull_rock("ledge", (s * 1.5, s * 1.2, s * 0.85), tuple(d * outline_r(ar) * f + V((0, 0, z))),
                              seed=30 + k, n_points=12, bevel=0.04, m="M_StoneRough", rot_z=a))
# moss on the top edges of the steps (the ledge between one stratum and the next)
for k, (a, z, f) in enumerate(((15, -1.24, 0.77), (70, -1.23, 0.76), (130, -1.25, 0.77), (200, -2.1, 0.52),
                               (250, -1.23, 0.77), (300, -2.12, 0.52), (345, -1.24, 0.77), (110, -2.85, 0.29))):
    ar = math.radians(a)
    p = V((math.cos(ar), math.sin(ar), 0)) * outline_r(ar) * f + V((0, 0, z))
    parts.append(rw.ico("moss", 0.5, 1, tuple(p), (0, 0, a), (0.8, 0.45, 0.3), il.M("Moss" if k % 2 else "MossLight"),
                        None, 50))

# --- dangling roots ----------------------------------------------------------------------------------------------
for k, (a, f, z0, L) in enumerate(((20, 0.82, -1.35, 1.5), (75, 0.55, -2.2, 1.2), (140, 0.82, -1.35, 1.8),
                                   (200, 0.3, -2.95, 1.0), (250, 0.82, -1.35, 1.3), (300, 0.55, -2.2, 1.4))):
    ar = math.radians(a)
    d = V((math.cos(ar), math.sin(ar), 0))
    p0 = d * outline_r(ar) * (f - 0.06) + V((0, 0, z0 + 0.15))
    pts = [p0, p0 + d * 0.2 + V((0, 0, -L * 0.35)), p0 + d * 0.15 + V((0.1, -0.1, -L * 0.7)), p0 + d * 0.3 + V((0, 0, -L))]
    parts.append(pl.sausage("root", pts, [0.13, 0.1, 0.075, 0.035], 6, 2, il.mat("Root"), (True, True), 1, True, 60))
    if k % 2 == 0:
        q = pts[1]
        parts.append(pl.sausage("rootlet", [q, q + d * 0.3 + V((0.05, 0.05, -0.25)), q + d * 0.45 + V((0, 0, -0.65))],
                                [0.06, 0.045, 0.02], 5, 2, il.mat("Root"), (True, True), 1, True, 60))

# --- hanging ley crystals -------------------------------------------------------------------------------------------
for (p, d, L, r, spin) in (((0.0, 0.0, -3.3), (0.04, -0.03, -1), 1.4, 0.3, 0),
                           ((0.25, -0.2, -3.2), (0.45, -0.35, -1), 0.7, 0.17, 30),
                           ((-1.3, 0.7, -2.6), (-0.35, 0.25, -1), 1.1, 0.25, 20),
                           ((1.25, 0.95, -2.4), (0.4, 0.3, -1), 0.95, 0.22, 40)):
    parts.append(pl.crystal("crystal", V(p), V(d), L, r, 6, 0.3, 0.12, il.mat("M_Crystal"), spin))

# --- on top: boulders, bushes, grass tufts, flowers -------------------------------------------------------------------
for k, (x, y, s) in enumerate(((1.9, 1.5, 0.95), (2.6, 0.6, 0.55), (-2.3, -1.7, 0.7))):
    parts.append(il.hull_rock("boulder", (s * 1.3, s * 1.1, s * 0.9), (x, y, s * 0.22), seed=50 + k, n_points=14, bevel=0.04,
                              m="M_StoneRough", flat_bottom=0.45))
    parts.append(rw.ico("moss", 0.5, 1, (x - s * 0.1, y, s * 0.55), (0, 0, 20 * k), (s * 0.7, s * 0.55, s * 0.18),
                        il.M("Moss"), None, 50))
BUSH = rw.flat("IslandBush", "4fa83a", 0.85, 0.0)
FLOWERS = ("FlowerPink", "FlowerYellow", "FlowerWhite")
for k, (x, y, s) in enumerate(((-1.5, 2.1, 0.95), (1.0, -2.3, 0.8))):
    for j in range(3):
        a = 2 * math.pi * j / 3 + k
        parts.append(rw.ico("bush", 0.5, 1, (x + math.cos(a) * s * 0.33, y + math.sin(a) * s * 0.33, s * 0.25),
                            (0, 0, 30 * j), (s, s * 0.9, s * 0.8), BUSH, None, 50))
    for j in range(4):
        a = 2 * math.pi * (j + 0.5) / 4 + k
        parts.append(rw.ico("flower", 0.5, 1, (x + math.cos(a) * s * 0.4, y + math.sin(a) * s * 0.4, s * 0.58),
                            (0, 0, 0), (0.22, 0.22, 0.14), E.M(FLOWERS[(j + k) % 3]), None, 0))


def tuft(cx, cy, n=6, h=0.6):
    bm = bmesh.new()
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.3, 0.3)
        hh = h * rnd.uniform(0.75, 1.15)
        b = V((cx + 0.04 * math.cos(a), cy + 0.04 * math.sin(a), -0.03))
        out = V((math.cos(a), math.sin(a), 0))
        side = V((-out.y, out.x, 0))
        w = 0.12
        v0 = bm.verts.new(b - side * w)
        v1 = bm.verts.new(b + side * w)
        v2 = bm.verts.new(b + out * (hh * 0.22) + side * (w * 0.7) + V((0, 0, hh * 0.55)))
        v3 = bm.verts.new(b + out * (hh * 0.22) - side * (w * 0.7) + V((0, 0, hh * 0.55)))
        tip = bm.verts.new(b + out * (hh * 0.5) + V((0, 0, hh)))
        bm.faces.new((v0, v1, v2, v3))
        bm.faces.new((v3, v2, tip))
    o = pl.obj_from_bm("tuft", bm, rw.flat("IslandTuft", "7fd156", 0.85, 0.0), 0)
    sol = o.modifiers.new("Solid", 'SOLIDIFY')
    sol.thickness = 0.03
    rw.apply_modifiers(o)
    return o


for (x, y) in ((0.6, 1.0), (-0.9, -0.6), (-2.4, 0.9), (2.4, -0.4), (-0.3, 3.0)):
    parts.append(tuft(x, y))

island = E.join(parts, "SkyIsland", origin=(0, 0, 0))
rw.smooth(island, 35)
E.col_box("Top", (7.0, 7.0, 0.6), (0, 0, -0.3))
E.col_box("Under", (5.6, 5.6, 1.7), (0, 0, -1.45))
E.col_box("Under", (3.2, 3.2, 1.5), (0, 0, -3.05))
E.check(ASSET, (8.0, 8.0, 5.0), 5000)
rw.finish(ASSET, "env", previews=E.previews())
