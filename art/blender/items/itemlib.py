"""itemlib: shared helpers for the RuneWire item pickups and treasure containers (art/blender/items/).

Import from an item generator script:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import itemlib as il
    rw, pl, V = il.rw, il.pl, il.V

Builds on rwlib and partlib (neither is edited). Conventions follow art/ASSET_SPEC.md: metres, +Z up,
the front faces -Y, user-facing angles in degrees. Pickups end with il.finish_item() (origin at the
bounding-box centre); the chests end with il.finish_container() (origin at the ground centre).
The env scripts node_ley_crystal / prop_sky_island / prop_workbench also import this module for its
rock and crystal helpers.

Main helpers
* M(name)            accent materials (flat colours and glows) shared by the items.
* lathe()            partlib.lathe_axis with the item defaults.
* curve_profile()    smooth (Catmull-Rom) lathe profile through a few control points.
* prof_radius()      outer radius of a lathe profile at a height (to wrap labels onto bottles).
* liquid_profile()   the liquid inside a bottle: the glass profile inset, cut flat at the fill level.
* lathe_map(), plane_map()   map flat 2D coordinates (x right, y up) onto a bottle / a flat face.
* wrap_slab()        rounded-rectangle label (parchment) wrapped onto a bottle.
* wrap_prism()       extruded 2D outline (heart, star, flame...) laid onto a bottle, label or face.
* gear()             cheap cartoon gear (optional hole, missing teeth), axis along any direction.
* hull_rock()        chunky faceted rock (convex hull of jittered points, flat facets, soft bevel).
* crystal_cluster()  a few chunky faceted crystals fanning out of one point.
* heart_pts(), star_pts(), flame_pts(), wing_pts()   2D outlines (counter-clockwise).
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, geometry

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, ".."), os.path.join(HERE, "..", "parts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import rwlib as rw  # noqa: E402
import partlib as pl  # noqa: E402

V = Vector
CAT = "items"


# --------------------------------------------------------------------------------------
# Accent materials (library M_* materials are used for anything that gets a texture in game)
# --------------------------------------------------------------------------------------

ACCENTS = {
    # name: ("flat", colour, roughness, metallic) or ("glow", colour, strength)
    "Gold": ("flat", "ffc93c", 0.3, 1.0),
    "Cork": ("flat", "c99158", 0.9, 0.0),
    "CorkDark": ("flat", "9c6a3c", 0.9, 0.0),
    "Parchment": ("flat", "f4e4bc", 0.9, 0.0),
    "Ink": ("flat", "3a2a28", 0.9, 0.0),
    "HeartRed": ("flat", "e3263f", 0.5, 0.0),
    "StarYellow": ("flat", "ffcf3a", 0.5, 0.0),
    "Twine": ("flat", "c9a46a", 0.9, 0.0),
    "Wax": ("flat", "b3263a", 0.5, 0.0),
    "Velvet": ("flat", "6e1d3c", 1.0, 0.0),
    "VelvetDeep": ("flat", "3c0f26", 1.0, 0.0),
    "VelvetViolet": ("flat", "3b1d5e", 1.0, 0.0),
    "VaultGlow": ("glow", "39d5c4", 3.0),
    "Iron": ("flat", "3b3f48", 0.45, 0.8),
    "Moss": ("flat", "6e9f3a", 0.95, 0.0),
    "MossLight": ("flat", "8cc04a", 0.95, 0.0),
    "Grass": ("flat", "6cc24a", 0.85, 0.0),
    "GrassDark": ("flat", "4f9e3a", 0.85, 0.0),
    "Root": ("flat", "7a5236", 0.9, 0.0),
    "Blueprint": ("flat", "3c74c4", 0.9, 0.0),
    "BlueprintInk": ("flat", "e8f3ff", 0.9, 0.0),
    "Paper": ("flat", "f4e6c2", 0.9, 0.0),
    "Hazard": ("flat", "f2c12e", 0.5, 0.0),
    "Rubber": ("flat", "2d2d31", 0.9, 0.0),
    "PatchCloth": ("flat", "2b3346", 0.95, 0.0),
    "PouchShadow": ("flat", "2a1a14", 1.0, 0.0),
    "HandleRed": ("flat", "c8323c", 0.5, 0.0),
    "Thread": ("flat", "e9d9b0", 0.9, 0.0),
    "Shine": ("flat", "fbfdff", 0.25, 0.0),
    # liquids: the bottle surface below the fill line, and the lighter liquid surface seen through the glass
    "TonicRed": ("flat", "d6163a", 0.25, 0.0),
    "TonicRedTop": ("flat", "ff6b80", 0.3, 0.0),
    "ManaBlue": ("glow", "2a62f0", 0.5),
    "ManaBlueTop": ("glow", "7fb2ff", 0.8),
    "SwiftGreen": ("glow", "00b57c", 0.45),
    "SwiftGreenTop": ("glow", "6dffd2", 0.8),
    "IronAmber": ("flat", "f08a12", 0.25, 0.0),
    "IronAmberTop": ("flat", "ffc65c", 0.3, 0.0),
    # glows
    "ManaWax": ("flat", "2e4aa8", 0.45, 0.0),
    "TealGlow": ("glow", "39d5c4", 3.0),
    "TealGlowSoft": ("glow", "39d5c4", 1.6),
    "SparkGlow": ("glow", "ffb81f", 2.2),
    "SparkCore": ("glow", "fff1a8", 2.5),
    "FlameCore": ("glow", "ffbf1a", 0.5),
    "LampGlow": ("glow", "ffcc66", 3.0),
    "RuneTeal": ("glow", "39d5c4", 2.0),
}


def M(name):
    """Accent material by name (see ACCENTS); created on first use."""
    k = ACCENTS[name]
    if k[0] == "glow":
        return rw.glow(name, k[1], k[2])
    return rw.flat(name, k[1], k[2], k[3])


def mat(m):
    """Resolve a material spec: library 'M_*' names pass through, accent names go through M()."""
    if m is None or isinstance(m, bpy.types.Material):
        return m
    if m in ACCENTS:
        return M(m)
    return m


# --------------------------------------------------------------------------------------
# Profiles and lathes
# --------------------------------------------------------------------------------------

def lathe(name, prof, axis=(0, 0, 1), loc=(0, 0, 0), segs=32, m=None, smooth=50, cap_bottom=False,
          cap_top=False, spin=0.0):
    """Revolve [(r, z), ...] (bottom -> top) about local Z, then aim local Z along `axis` and move to loc.
    Start/end the profile at r = 0 for closed solids."""
    return pl.lathe_axis(name, prof, axis, loc, segs, mat(m), cap_bottom, cap_top, smooth, spin)


def curve_profile(ctrl, per_seg=4):
    """Smooth profile through control points [(r, z), ...] (uniform Catmull-Rom)."""
    P = [V((r, z, 0.0)) for (r, z) in ctrl]
    n = len(P)
    out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else 2 * P[0] - P[1]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < n else 2 * P[-1] - P[-2]
        for k in range(per_seg):
            t = k / per_seg
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                       (3 * p1 - p0 - 3 * p2 + p3) * t3)
            out.append((max(q.x, 0.0), q.y))
    out.append((P[-1].x, P[-1].y))
    return out


def prof_radius(prof, z):
    """Outer radius of a lathe profile at height z (largest radius among the segments spanning z)."""
    best = None
    for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
        lo, hi = min(z0, z1), max(z0, z1)
        if hi - lo < 1e-9 or not (lo <= z <= hi):
            continue
        t = (z - z0) / (z1 - z0)
        r = r0 + (r1 - r0) * t
        best = r if best is None else max(best, r)
    return best if best is not None else 0.0


def liquid_profile(prof, inset, z0, z1, n=12):
    """Closed profile for the liquid inside a glass profile: inset by `inset`, from z0 up to the fill level z1."""
    pts = [(0.0, z0)]
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        pts.append((max(prof_radius(prof, z) - inset, 0.002), z))
    pts.append((0.0, z1))
    return pts


# --------------------------------------------------------------------------------------
# Mapping flat 2D artwork onto surfaces
# --------------------------------------------------------------------------------------

def lathe_map(rfunc, ang_c=0.0, z_c=0.0, off=0.002, thick=0.004, center=(0, 0, 0)):
    """Mapper (x, y, s) -> 3D point on a surface of revolution about the vertical axis through `center`
    (radius rfunc(z)). x = arc length (to the right as seen from outside), y = height above z_c,
    s = 0 (inner face, `off` above the surface) .. 1 (outer face, off + thick). ang_c in degrees:
    0 = the front (-Y), 90 = +X."""
    c = V(center)

    def P(x, y, s):
        z = z_c + y
        r = max(rfunc(z), 1e-4)
        a = math.radians(ang_c) + x / r
        rr = r + off + s * thick
        return (c.x + rr * math.sin(a), c.y - rr * math.cos(a), c.z + z)
    return P


def plane_map(center, u_dir, v_dir, off=0.0, thick=0.004):
    """Mapper (x, y, s) -> center + u*x + v*y + n*(off + s*thick), n = u x v (the side the art faces)."""
    c = V(center)
    u = V(u_dir).normalized()
    v = V(v_dir).normalized()
    n = u.cross(v).normalized()

    def P(x, y, s):
        return tuple(c + u * x + v * y + n * (off + s * thick))
    return P


def param_slab(name, P, nu, nv, m=None):
    """Thick sheet from P(u, v, s) with u, v in [0, 1] and s in {0, 1} (0 = inner, 1 = outer)."""
    bm = bmesh.new()
    g = {}
    for s in (0, 1):
        for j in range(nv + 1):
            for i in range(nu + 1):
                g[(i, j, s)] = bm.verts.new(P(i / nu, j / nv, s))
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((g[(i, j, 1)], g[(i + 1, j, 1)], g[(i + 1, j + 1, 1)], g[(i, j + 1, 1)]))
            bm.faces.new((g[(i, j, 0)], g[(i, j + 1, 0)], g[(i + 1, j + 1, 0)], g[(i + 1, j, 0)]))
    for i in range(nu):
        bm.faces.new((g[(i, 0, 0)], g[(i + 1, 0, 0)], g[(i + 1, 0, 1)], g[(i, 0, 1)]))
        bm.faces.new((g[(i, nv, 1)], g[(i + 1, nv, 1)], g[(i + 1, nv, 0)], g[(i, nv, 0)]))
    for j in range(nv):
        bm.faces.new((g[(0, j, 1)], g[(0, j + 1, 1)], g[(0, j + 1, 0)], g[(0, j, 0)]))
        bm.faces.new((g[(nu, j, 0)], g[(nu, j + 1, 0)], g[(nu, j + 1, 1)], g[(nu, j, 1)]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), 40)


def squircle(u, v, w, h, p=5.0):
    """Map the unit square (u, v in [0, 1]) onto a rounded rectangle w x h centred on 0 (superellipse power p)."""
    x, y = 2 * u - 1, 2 * v - 1
    mm = max(abs(x), abs(y))
    if mm < 1e-9:
        return (0.0, 0.0)
    s = (abs(x) ** p + abs(y) ** p) ** (1.0 / p)
    k = mm / s
    return (x * k * w / 2, y * k * h / 2)


def wrap_slab(name, mapper, w, h, nu=10, nv=4, m="Parchment", p=5.0, wobble=0.0, seed=0):
    """Rounded-rectangle label w x h laid through a mapper (lathe_map / plane_map). `wobble` (m) makes the
    outline a little hand-cut."""
    rnd = random.Random(seed)
    jit = {}

    def P(u, v, s):
        x, y = squircle(u, v, w, h, p)
        if wobble and (u in (0.0, 1.0) or v in (0.0, 1.0)):
            key = (round(u, 4), round(v, 4))
            if key not in jit:
                jit[key] = (rnd.uniform(-wobble, wobble), rnd.uniform(-wobble, wobble))
            x += jit[key][0]
            y += jit[key][1]
        return mapper(x, y, s)
    return param_slab(name, P, nu, nv, m)


def ccw(pts):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a += x0 * y1 - x1 * y0
    return list(pts) if a > 0 else list(reversed(pts))


def wrap_prism(name, pts2d, mapper, m=None, smooth_angle=30):
    """Extruded 2D outline (any simple polygon, concave is fine) laid through a mapper: s = 0 is the
    underside, s = 1 the top."""
    pts2d = ccw([(float(x), float(y)) for (x, y) in pts2d])
    tris = geometry.tessellate_polygon([[V((x, y, 0.0)) for (x, y) in pts2d]])
    bm = bmesh.new()
    bot = [bm.verts.new(mapper(x, y, 0.0)) for (x, y) in pts2d]
    top = [bm.verts.new(mapper(x, y, 1.0)) for (x, y) in pts2d]
    for (a, b, c) in tris:
        for ring, order in ((top, (a, b, c)), (bot, (c, b, a))):
            try:
                bm.faces.new([ring[i] for i in order])
            except ValueError:
                pass
    n = len(pts2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)


# --------------------------------------------------------------------------------------
# 2D outlines (counter-clockwise)
# --------------------------------------------------------------------------------------

def heart_pts(width, n=28):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        pts.append((16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    s = width / (max(xs) - min(xs))
    cy = (max(ys) + min(ys)) / 2
    return ccw([(x * s, (y - cy) * s) for (x, y) in pts])


def star_pts(n=5, r_out=0.5, r_in=0.22, phase=90.0, round_=0):
    pts = []
    for i in range(2 * n):
        a = math.radians(phase) + math.pi * i / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return ccw(pts)


def flame_pts(w, h, n=20):
    """Cartoon flame / teardrop (point up), centred on its bbox."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 0.5 * w * math.sin(t) * (1 - 0.55 * (1 + math.cos(t)) / 2) * 1.25
        y = -0.5 * h * math.cos(t)
        pts.append((x, y))
    return ccw(pts)


def wing_pts(length=0.1, height=0.07, feathers=3, n_arc=4):
    """Little stylised wing in 2D: the root is at x = 0 (y from 0 to 0.55*height), it sweeps out and up to
    the tip at x = length, and the lower edge is scalloped into `feathers` rounded feather ends."""
    top = []
    for i in range(7):
        t = i / 6
        top.append((length * t, height * (0.55 + 0.45 * math.sin(t * math.pi / 2)) + height * 0.08 * math.sin(t * math.pi)))
    tip = top[-1]
    # feather ends from the tip back to the root along the lower edge
    pts = list(top)
    ends = []
    for k in range(feathers):
        f = 1 - k / feathers                   # 1 at the tip
        fx = length * (0.96 * f - 0.04)
        fy = height * (0.58 * f + 0.02) - height * 0.1
        ends.append((fx, fy))
    prev = tip
    for k, (fx, fy) in enumerate(ends):
        nxt_root = (length * (0.96 * (1 - (k + 1) / feathers) - 0.02), height * (0.58 * (1 - (k + 1) / feathers) + 0.12))
        # rounded feather end: arc from prev down around (fx, fy) and back up to the notch
        cx, cy = fx - length * 0.06, fy + height * 0.06
        rad = min(length / feathers * 0.55, height * 0.32)
        for j in range(n_arc + 1):
            a = math.radians(10 - 200 * j / n_arc)
            pts.append((cx + rad * math.cos(a) * 1.15, cy + rad * math.sin(a)))
        if k < feathers - 1:
            pts.append(nxt_root)
        prev = nxt_root
    pts.append((0.0, 0.0))
    # drop near-duplicates
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > 1e-4 or abs(out[-1][1] - p[1]) > 1e-4):
            out.append(p)
    return ccw(out)


def capsule_pts(w, h, n=6):
    """Stadium outline w wide, h tall (vertical), centred on 0."""
    r = w / 2
    c = max(h / 2 - r, 0.0)
    pts = []
    for i in range(n + 1):
        a = math.pi * i / n
        pts.append((r * math.cos(a), c + r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        pts.append((r * math.cos(a), -c + r * math.sin(a)))
    return ccw(pts)


def ellipse_pts(w, h, n=20, p=2.0):
    """Superellipse outline w x h (p = 2 is an ellipse, larger p is boxier)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s_ = math.cos(a), math.sin(a)
        pts.append((w / 2 * math.copysign(abs(c) ** (2 / p), c), h / 2 * math.copysign(abs(s_) ** (2 / p), s_)))
    return ccw(pts)


def wrench_head_pts(R, jaw_w, jaw_d, n=14):
    """Open-ended wrench head: a disc of radius R with a jaw slot (jaw_w wide, jaw_d deep) opening toward +y."""
    a0 = math.asin(min(0.95, jaw_w / 2 / R))
    pts = []
    for i in range(n + 1):
        t = math.pi / 2 + a0 + (2 * math.pi - 2 * a0) * i / n
        pts.append((R * math.cos(t), R * math.sin(t)))
    yb = R * math.cos(a0) - jaw_d
    pts += [(jaw_w / 2, yb), (-jaw_w / 2, yb)]
    return ccw(pts)


def bolt_pts(h):
    """Chunky lightning bolt, h tall, centred."""
    k = h / 0.06
    pts = [(-0.006, 0.03), (0.016, 0.03), (0.004, 0.007), (0.016, 0.007), (-0.012, -0.03), (-0.002, -0.004),
           (-0.015, -0.004)]
    return ccw([(x * k, y * k) for (x, y) in pts])


def shield_pts(w, h, n=6):
    """Heater-shield outline (flat top, pointed bottom), centred on its bbox."""
    pts = [(-w / 2, h / 2), (w / 2, h / 2)]
    for i in range(1, n + 1):
        t = i / n
        pts.append((w / 2 * math.cos(t * math.pi / 2) ** 0.8, h / 2 - h * (0.35 + 0.65 * math.sin(t * math.pi / 2))))
    for i in range(n - 1, 0, -1):
        t = i / n
        pts.append((-w / 2 * math.cos(t * math.pi / 2) ** 0.8, h / 2 - h * (0.35 + 0.65 * math.sin(t * math.pi / 2))))
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) > 1e-5 or abs(out[-1][1] - p[1]) > 1e-5:
            out.append(p)
    return ccw(out)


# --------------------------------------------------------------------------------------
# Bottles
# --------------------------------------------------------------------------------------

class Bottle:
    """A cartoon potion bottle built from a smooth body profile. Below the fill line the bottle's own surface
    is the liquid colour (so it reads strongly in icons and at a distance); above it the surface is glass,
    and the lighter liquid surface shows through it.

    body_ctrl  control points [(r, z), ...] from (0, 0) at the bottom centre up to the neck
    lip        straight points appended after the smoothed body (lip / rim), ending at r = 0
    fill       liquid level (height)
    liquid     material below the fill line; top = material of the liquid surface (defaults to liquid)
    """

    def __init__(self, body_ctrl, lip, fill, liquid, top=None, segs=24, per_seg=2, glass="M_Glass"):
        prof = curve_profile(body_ctrl, per_seg) + list(lip)
        self.prof = insert_level(prof, fill)
        self.fill = fill
        o = lathe("bottle", self.prof, segs=segs, m=glass, smooth=60)
        rw.set_mat_where(o, mat(liquid), lambda c, n: c.z < fill - 1e-4)
        self.glass = o
        rt = self.r(fill) - 0.004
        self.surface = rw.cylinder("surface", rt, 0.003, max(12, segs - 4), (0, 0, fill - 0.003),
                                   mat=mat(top or liquid))
        self.parts = [o, self.surface]

    def r(self, z):
        return prof_radius(self.prof, z)

    def map(self, ang_c, z_c, off=0.0015, thick=0.004):
        return lathe_map(self.r, ang_c, z_c, off, thick)

    def label(self, ang_c, z_c, w, h, icon_pts=None, icon_mat=None, m="Parchment", thick=0.004, seed=1,
              nu=8, nv=3):
        """Parchment label (wrapped onto the glass) with an optional raised 2D icon on it."""
        out = [wrap_slab("label", self.map(ang_c, z_c, 0.0015, thick), w, h, nu, nv, m, 5.0, w * 0.02, seed)]
        if icon_pts:
            out.append(wrap_prism("label_icon", icon_pts, self.map(ang_c, z_c, 0.0015 + thick * 0.9, 0.0035),
                                  icon_mat))
        self.parts += out
        return out

    def shine(self, ang_c, z_c, w=0.014, h=0.05):
        """Cartoon glint: a white stroke on the glass."""
        o = wrap_prism("shine", capsule_pts(w, h), self.map(ang_c, z_c, 0.0016, 0.0015), "Shine")
        self.parts.append(o)
        return o


def insert_level(prof, z):
    """Insert a profile point at height z on the first (outer, upward) segment that crosses it."""
    out = list(prof)
    for i in range(len(out) - 1):
        (r0, z0), (r1, z1) = out[i], out[i + 1]
        if z0 < z < z1 and abs(z1 - z0) > 1e-9:
            t = (z - z0) / (z1 - z0)
            if min(abs(z - z0), abs(z1 - z)) > 1e-4:
                out.insert(i + 1, (r0 + (r1 - r0) * t, z))
            break
    return out


def cork(z0, z1, r0, r1, segs=16, m="Cork", top_round=0.35):
    """Tapered cork plug from z0 (r0, inside the neck) up to a rounded top at z1 (radius r1)."""
    h = z1 - z0
    b = min(r1 * top_round, h * 0.3)
    prof = [(0.0, z0), (r0, z0), (r0 + (r1 - r0) * 0.5, z0 + h * 0.5), (r1, z1 - b), (r1 - b * 0.35, z1 - b * 0.3),
            (r1 - b, z1), (0.0, z1)]
    return lathe("cork", prof, segs=segs, m=m, smooth=40)


# --------------------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------------------

def gear(name, radius, teeth=10, depth=0.03, thick=0.04, hole=0.0, loc=(0, 0, 0), normal=(0, -1, 0), m="M_Brass",
         spin=0.0, bevel=0.0, skip=(), tooth_round=True):
    """Cartoon gear built straight into a mesh, axis along `normal`, centred on loc (half the thickness on
    each side). `skip` = tooth indices to leave out (broken teeth). With tooth_round the tooth tips get a
    soft extra point so they read chunky rather than square."""
    pts = []
    sp = math.radians(spin)
    for t in range(teeth):
        a0 = 2 * math.pi * t / teeth + sp
        step = 2 * math.pi / teeth
        if t in skip:
            for f in (0.0, 0.25, 0.5, 0.75):
                a = a0 + step * f
                pts.append((radius - depth) * V((math.cos(a), math.sin(a), 0)))
            continue
        prof = [(0.0, 0.0), (0.18, 0.0), (0.28, 1.0), (0.5, 1.06 if tooth_round else 1.0), (0.72, 1.0), (0.82, 0.0)]
        for (f, h) in prof:
            a = a0 + step * f
            pts.append((radius - depth + depth * h) * V((math.cos(a), math.sin(a), 0)))
    n = len(pts)
    bm = bmesh.new()
    top = [bm.verts.new((p.x, p.y, thick / 2)) for p in pts]
    bot = [bm.verts.new((p.x, p.y, -thick / 2)) for p in pts]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    if hole and hole > 0:
        k = max(12, teeth * 2)
        ti = [bm.verts.new((hole * math.cos(2 * math.pi * i / k + sp), hole * math.sin(2 * math.pi * i / k + sp), thick / 2)) for i in range(k)]
        bi = [bm.verts.new((hole * math.cos(2 * math.pi * i / k + sp), hole * math.sin(2 * math.pi * i / k + sp), -thick / 2)) for i in range(k)]
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((ti[i], ti[j], bi[j], bi[i]))
        for cap, inner, sign in ((top, ti, 1), (bot, bi, -1)):
            for i in range(k):
                j = (i + 1) % k
                o0 = int(round(i * n / k)) % n
                o1 = int(round(j * n / k)) % n
                ring = []
                q = o0
                while True:
                    ring.append(cap[q])
                    if q == o1:
                        break
                    q = (q + 1) % n
                face = ring + [inner[j], inner[i]]
                if sign < 0:
                    face = list(reversed(face))
                try:
                    bm.faces.new(face)
                except ValueError:
                    pass
    else:
        bm.faces.new(top)
        bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    g = pl.obj_from_bm(name, bm, mat(m), 0)
    if bevel and bevel > 0:
        rw.add_bevel(g, bevel, 1, 40, harden=False)
        rw.apply_modifiers(g)
    pl.align(g, normal, loc)
    rw.smooth(g, 30)
    return g


def _fib_dirs(n, rng, jitter=0.35):
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        th = ga * i
        d = V((math.cos(th) * r, math.sin(th) * r, z))
        d += V((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
        out.append(d.normalized())
    return out


def hull_rock(name, size, loc=(0, 0, 0), seed=0, n_points=16, jitter=0.35, rmin=0.8, flat_bottom=0.0,
              flat_top=0.0, dissolve_deg=8.0, bevel=0.02, m="M_StoneRough", rot_z=0.0, bevel_segments=1, cuts=()):
    """Chunky faceted cartoon rock: convex hull of jittered points on an ellipsoid of `size`, big flat facets.
    flat_bottom / flat_top (0..1) slice the bottom / top flat at that fraction of the half-height.
    cuts = [(point, outward_normal), ...] slice off everything beyond each plane (clean fracture faces);
    points are relative to the rock centre, before rot_z."""
    rng = random.Random(seed)
    sx, sy, sz = (s / 2.0 for s in size)
    bm = bmesh.new()
    for d in _fib_dirs(n_points, rng, jitter):
        r = rng.uniform(rmin, 1.0)
        bm.verts.new((d.x * sx * r, d.y * sy * r, d.z * sz * r))
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    unused = list({v for v in res.get("geom_interior", []) + res.get("geom_unused", [])
                   if isinstance(v, bmesh.types.BMVert) and v.is_valid})
    if unused:
        bmesh.ops.delete(bm, geom=unused, context='VERTS')
    planes = [((0, 0, sign * sz * amount), (0, 0, sign)) for (amount, sign) in ((flat_bottom, -1), (flat_top, 1))
              if amount]
    planes += [(tuple(c), tuple(n)) for (c, n) in cuts]
    for (co, no) in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r2 = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no, clear_outer=True)
        edges = [e for e in r2["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            try:
                bmesh.ops.edgeloop_fill(bm, edges=edges)
            except Exception:
                bmesh.ops.holes_fill(bm, edges=edges)
    if dissolve_deg:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:], edges=bm.edges[:])
    if rot_z:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(rot_z), 3, 'Z'))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=V(loc))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = pl.obj_from_bm(name, bm, mat(m), 0)
    rw.flat_shade(o)
    if bevel:
        md = o.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel
        md.segments = bevel_segments
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(25)
        md.harden_normals = True
        md.use_clamp_overlap = True
        rw.apply_modifiers(o)
    return o


def surface_hit(o, origin, direction):
    """Ray-cast onto object o (world space). Returns (point, normal) or (None, None)."""
    bpy.context.view_layer.update()
    mw = o.matrix_world
    inv = mw.inverted()
    lo = inv @ V(origin)
    ld = (inv.to_3x3() @ V(direction)).normalized()
    ok, loc, nrm, _ = o.ray_cast(lo, ld)
    if not ok:
        return None, None
    return mw @ loc, (mw.to_3x3().inverted().transposed() @ nrm).normalized()


def face_frame(n):
    """(u, v) spanning a surface with normal n: u horizontal (to the right seen from outside), v 'up'."""
    n = V(n).normalized()
    u = V((0, 0, 1)).cross(n)
    if u.length < 1e-4:
        u = V((1, 0, 0))
    u.normalize()
    return u, n.cross(u).normalized()


def carve_rune(target, key, point, normal, size, groove=0.016, depth=0.012, inlay="M_RuneGlow", inlay_w=None):
    """Carve a rune groove into `target` at a surface point and return the glowing inlay strokes."""
    u, v = face_frame(normal)
    n = V(normal).normalized()
    pl.carve(target, pl.glyph_cutters(key, V(point), u, v, size, groove, depth * 2))
    w = inlay_w if inlay_w else groove * 0.7
    return pl.glyph(key, V(point) - n * (depth - 0.004), u, v, size, w, 0.008, mat(inlay), "rune")


def moss_on(target, points, size=0.07, seed=0, m=("Moss", "MossLight"), squash=0.45, sink=0.35):
    """Soft flattened moss cushions dropped onto target's surface from above at the given (x, y) points."""
    rnd = random.Random(seed)
    out = []
    for i, (x, y) in enumerate(points):
        p, n = surface_hit(target, (x, y, 50.0), (0, 0, -1))
        if p is None:
            continue
        s = size * rnd.uniform(0.75, 1.2)
        o = rw.ico("moss", 0.5, 2, (0, 0, 0), (0, 0, rnd.uniform(0, 90)), (s * 1.2, s, s * squash), mat(m[i % len(m)]),
                   None, 70)
        pl.align(o, n, p - n * (s * squash * 0.5 * sink))
        out.append(o)
    return out


def crystal_cluster(base, specs, m="M_Crystal", sides=6):
    """Crystals fanning out from `base`: specs = [(direction, length, radius, spin_deg), ...].
    Each is a faceted prism with a pointed tip (partlib.crystal), its foot sunk a little below base."""
    out = []
    b = V(base)
    for i, (d, L, r, spin) in enumerate(specs):
        d = V(d).normalized()
        out.append(pl.crystal("crystal%d" % i, b - d * (L * 0.12), d, L, r, sides, 0.3, 0.1, m, spin))
    return out


def blob(name, size, loc=(0, 0, 0), m=None, subdiv=2, squash=1.0, seed=0, noise=0.0, rot=(0, 0, 0)):
    """Soft lump (moss, coal, puffs). With noise > 0 the surface gets a gentle lumpy displacement."""
    o = rw.ico(name, 0.5, subdiv, loc, rot, (size[0], size[1], size[2] * squash), mat(m), None, 70)
    if noise:
        rw.add_displace_noise(o, noise, 0.5, seed)
        rw.apply_modifiers(o)
        purge_helpers()
        rw.smooth(o, 70)
    return o


def purge_helpers():
    for o in list(bpy.context.scene.objects):
        if o.get("rw_helper") and o.type == 'EMPTY':
            used = any(md.type == 'DISPLACE' and md.texture_coords_object == o
                       for ob in bpy.context.scene.objects if ob.type == 'MESH' for md in ob.modifiers)
            if not used:
                bpy.data.objects.remove(o, do_unlink=True)


def spark(name, center, r=0.04, spikes=8, m="SparkGlow", seed=3, core="SparkCore"):
    """Cartoon fizzing spark: a glowing core ball with chunky spikes in all directions."""
    rnd = random.Random(seed)
    c = V(center)
    parts = [rw.ico(name + "_core", r * 0.42, 1, tuple(c), (0, 0, 0), (1, 1, 1), mat(core), None, 0)]
    dirs = _fib_dirs(spikes, rnd, 0.25)
    for i, d in enumerate(dirs):
        L = r * rnd.uniform(0.8, 1.15)
        parts.append(pl.crystal(name + "_spike", c + d * (r * 0.15), d, L, r * 0.24, 4, 0.75, 0.0, mat(m),
                                rnd.uniform(0, 90)))
    return parts


# --------------------------------------------------------------------------------------
# Finishing
# --------------------------------------------------------------------------------------

def report_size(asset, expect=None):
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    s = mx - mn
    msg = "RWREPORT   ITEM %s size %.3f x %.3f x %.3f, tris %d" % (asset, s.x, s.y, s.z, rw.tri_count())
    if expect:
        msg += " (brief ~%s)" % " x ".join("%.2f" % e for e in expect)
    print(msg)
    return s


def preview_glass(alpha=0.22, base="7f9fb8"):
    """Godot replaces M_Glass by name with its own glass shader. rwlib's Blender stand-in is a brightly lit
    light-blue film whose diffuse is ADDED over whatever sits behind it, which turns saturated contents
    (embers, liquids) pale pink in the previews and icons. Use a thinner, darker film for the renders so the
    contents keep their colour. Only the Blender stand-in changes (the game uses material_library.gd)."""
    m = bpy.data.materials.get("M_Glass")
    if m is None:
        return
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Base Color"].default_value = rw._lin(base)
    m.diffuse_color = rw._lin(base)[:3] + (alpha,)


def preview_glow(mat_name, base_hex, emit_hex, strength):
    """Previews/icons only: AgX washes bright emission toward white, so library glows (M_EmberGlow,
    M_TechGlow...) can be given a darker base and a moderate emission to keep their hue in the icon.
    Godot replaces library M_* materials by name, so the game look is unaffected."""
    m = rw._resolve_mat(mat_name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(base_hex)
    b.inputs["Emission Color"].default_value = rw._lin(emit_hex)
    b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = rw._lin(base_hex)[:3] + (m.diffuse_color[3],)
    return m


def finish_item(asset, expect=None, previews=("front34", "back34"), glass_alpha=0.22):
    """Pickups: move every root so the bounding-box centre is the origin, then rw.finish (icon=True)."""
    preview_glass(glass_alpha)
    bpy.context.view_layer.update()
    pl.recentre()
    for o in pl.roots():
        if o.type == 'MESH':
            rw.set_origin(o, (0, 0, 0))
    bpy.context.view_layer.update()
    report_size(asset, expect)
    rw.finish(asset, CAT, previews=previews, icon=True)


def ground_centre_roots():
    """Containers / props: shift the roots so the visible bbox is centred in X/Y and sits on z = 0."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    shift = V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in pl.roots():
        o.location -= shift
    bpy.context.view_layer.update()
    return shift


def qa_render(asset, tag, view="front34", size=480, category=CAT, folder=None):
    """Extra QA render (after rw.finish has saved and exported). Goes to art/previews/<category>/ when
    folder is None, else to `folder`."""
    folder = folder or os.path.join(rw.ART, "previews", category)
    return rw.render_view(os.path.join(folder, "%s_%s.png" % (asset, tag)), view, size)


# --------------------------------------------------------------------------------------
# Containers (chests): arched lids, liners, coin piles, finishing with an open-lid QA render
# --------------------------------------------------------------------------------------

def arch_pt(t, ry, rz, y_c, z0):
    """Point on an elliptical arch around the X axis: t = 0 at the front bottom (-Y), pi/2 at the top, pi at the back."""
    return (y_c - ry * math.cos(t), z0 + rz * math.sin(t))


def arch_slab(name, x0, x1, ry, rz, y_c, z0, t0, t1, thick, nv=8, m=None, nu=1, out=0.0):
    """Curved slab following the elliptical arch between angles t0..t1 (radians), from x0 to x1.
    The outer surface lies `out` beyond the arch (ry + out, rz + out), the inner surface `thick` below it."""
    def P(u, v, s):
        t = t0 + (t1 - t0) * v
        d = out - thick * (1 - s)
        y, z = arch_pt(t, ry + d, rz + d, y_c, z0)
        return (x0 + (x1 - x0) * u, y, z)
    return param_slab(name, P, nu, nv, m)


def d_cap(name, x0, x1, ry, rz, y_c, z0, n=12, m=None):
    """D-shaped end wall (the arch outline closed by its chord), extruded from x0 to x1."""
    pts = [arch_pt(math.pi * i / n, ry, rz, y_c, z0) for i in range(n + 1)]
    pts2 = ccw([(y, z) for (y, z) in pts])
    tris = geometry.tessellate_polygon([[V((a, b, 0.0)) for (a, b) in pts2]])
    bm = bmesh.new()
    lo = [bm.verts.new((x0, a, b)) for (a, b) in pts2]
    hi = [bm.verts.new((x1, a, b)) for (a, b) in pts2]
    for (a, b, c) in tris:
        bm.faces.new([hi[a], hi[b], hi[c]])
        bm.faces.new([lo[c], lo[b], lo[a]])
    k = len(pts2)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), 30)


def liner(name, x0, x1, y0, y1, z0, z1, m="Velvet"):
    """Open-top box lining (floor + four walls) with its faces pointing INTO the hollow."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    o = rw.mesh_from_data(name, v, f, mat=mat(m))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    c = V(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for fc in bm.faces:
        if fc.normal.dot(c - fc.calc_center_median()) < 0:
            fc.normal_flip()
    bm.to_mesh(o.data)
    bm.free()
    rw.flat_shade(o)
    return o


def coin(name, loc, r=0.045, t=0.012, tilt=(0, 0, 0), m="Gold", segs=10):
    """A loose gold coin (a cheap chamfered disc) for treasure piles."""
    prof = [(0.0, -t / 2), (r * 0.9, -t / 2), (r, 0.0), (r * 0.9, t / 2), (0.0, t / 2)]
    o = lathe(name, prof, (0, 0, 1), (0, 0, 0), segs, m, 40)
    rot = Matrix.Rotation(math.radians(tilt[0]), 4, 'X') @ Matrix.Rotation(math.radians(tilt[1]), 4, 'Y') @ \
        Matrix.Rotation(math.radians(tilt[2]), 4, 'Z')
    o.data.transform(rot)
    o.location = loc
    return o


def coin_pile(center, rx, ry, h, n=9, seed=1, m="Gold", coin_r=0.045, subdiv=2):
    """A heap of gold: a soft gold mound with loose coins scattered on and around it. center = base centre."""
    rnd = random.Random(seed)
    c = V(center)
    out = [blob("goldheap", (rx * 2, ry * 2, h * 2), (c.x, c.y, c.z), m, subdiv, 1.0, seed, 0.0)]
    # keep only the upper half of the mound (the floor hides the rest)
    bm = bmesh.new()
    o = out[0]
    bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, c.z - o.location.z), plane_no=(0, 0, -1),
                           clear_outer=True)
    bm.to_mesh(o.data)
    bm.free()
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        f = rnd.uniform(0.15, 1.05)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        q = max(0.0, 1 - (x / rx) ** 2 - (y / ry) ** 2)
        z = c.z + h * math.sqrt(q) + 0.004
        nx, ny = x / (rx * rx), y / (ry * ry)
        slope = math.degrees(math.atan(h * math.hypot(nx, ny) / max(math.sqrt(q), 0.25)))
        tilt = (rnd.uniform(-12, 12) + slope * (-ny / max(math.hypot(nx, ny), 1e-6)),
                rnd.uniform(-12, 12) + slope * (nx / max(math.hypot(nx, ny), 1e-6)), rnd.uniform(0, 90))
        out.append(coin("coin", (c.x + x, c.y + y, z), coin_r * rnd.uniform(0.9, 1.1), coin_r * 0.26, tilt, m))
    return out


def finish_container(asset, body, lid, open_deg=-100.0, expect=None):
    """Chests: the visible bbox must sit on z = 0 centred in X/Y (the body origin is the ground centre).
    After rw.finish has saved/exported the closed chest, render QA previews with the lid swung open by
    `open_deg` about its local X (negative = front rises and swings back) to <asset>_open*.png."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    print("RWREPORT   CONTAINER %s bbox min (%.3f, %.3f, %.3f) max (%.3f, %.3f, %.3f)" % (
        asset, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z))
    hp = lid.matrix_world.translation
    print("RWREPORT   CONTAINER %s Lid hinge (origin) at (%.3f, %.3f, %.3f), parent=%s; open = rotate local X by %.0f deg" % (
        asset, hp.x, hp.y, hp.z, lid.parent.name if lid.parent else "-", open_deg))
    report_size(asset, expect)
    rw.finish(asset, CAT, icon=True)
    lid.rotation_euler = (math.radians(open_deg), 0, 0)
    bpy.context.view_layer.update()
    mn2, mx2 = rw.bounds()
    print("RWREPORT   CONTAINER %s open bbox min (%.3f, %.3f, %.3f) max (%.3f, %.3f, %.3f)" % (
        asset, mn2.x, mn2.y, mn2.z, mx2.x, mx2.y, mx2.z))
    folder = os.path.join(rw.ART, "previews", CAT)
    rw.render_view(os.path.join(folder, "%s_open_front34.png" % asset), "front34", 640)
    rw.render_view(os.path.join(folder, "%s_open_side.png" % asset), "side", 480)
