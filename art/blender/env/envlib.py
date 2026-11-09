"""envlib: shared helpers for the RuneWire environment batch (Batch C, art/blender/env/).

Import from an env generator script:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import envlib as E
    rw = E.rw

Everything here builds on rwlib (which must not be edited). Conventions follow ASSET_SPEC.md:
metres, +Z up, the front faces -Y, rotations in DEGREES, origin at the ground centre.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.abspath(os.path.join(HERE, ".."))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import rwlib as rw  # noqa: E402

CAT = "env"
V = Vector


def previews():
    """Preview views for rw.finish (override with RW_PREVIEWS=front34 while iterating)."""
    v = os.environ.get("RW_PREVIEWS")
    return tuple(x for x in v.split(",") if x) if v else ("front34", "back34")


# --------------------------------------------------------------------------------------
# Accent materials (flat colours / glows). Large surfaces use library M_* materials.
# --------------------------------------------------------------------------------------

ACCENTS = {
    # name: (kind, colour, roughness-or-strength, metallic)
    "WindowGlow": ("glow", "ffc25e", 1.5),
    "LampGlow": ("glow", "ffcc66", 3.0),
    "TealGlow": ("glow", "3ff0d8", 3.0),
    "TealGlowSoft": ("glow", "3ff0d8", 1.5),
    "VioletGlow": ("glow", "b07cff", 3.0),
    "ForgeGlow": ("glow", "ff7a2e", 2.5),
    "Iron": ("flat", "3b3f48", 0.45, 0.8),
    "IronDark": ("flat", "2a2c33", 0.5, 0.7),
    "Soot": ("flat", "2b2729", 0.95, 0.0),
    "Interior": ("flat", "1d1824", 1.0, 0.0),
    "Paper": ("flat", "f4e6c2", 0.9, 0.0),
    "PaperOld": ("flat", "e3c98f", 0.9, 0.0),
    "PaperBlue": ("flat", "bcd7ea", 0.9, 0.0),
    "Ink": ("flat", "3a2a28", 0.9, 0.0),
    "PinRed": ("flat", "d9433a", 0.4, 0.0),
    "Leaf": ("flat", "52ad3f", 0.8, 0.0),
    "LeafDark": ("flat", "3a8a3a", 0.8, 0.0),
    "Moss": ("flat", "6e9f3a", 0.95, 0.0),
    "Soil": ("flat", "5a3b26", 0.95, 0.0),
    "FlowerPink": ("flat", "ff7fb3", 0.6, 0.0),
    "FlowerYellow": ("flat", "ffd53f", 0.6, 0.0),
    "FlowerRed": ("flat", "ff5245", 0.6, 0.0),
    "FlowerWhite": ("flat", "fff3df", 0.6, 0.0),
    "FlowerBlue": ("flat", "7aa8ff", 0.6, 0.0),
    "FlowerViolet": ("flat", "b27cff", 0.6, 0.0),
    "PaintTeal": ("flat", "2e8f8a", 0.6, 0.0),
    "PaintBlue": ("flat", "3f6fb8", 0.6, 0.0),
    "PaintGreen": ("flat", "4f913c", 0.6, 0.0),
    "PaintRed": ("flat", "c0453a", 0.6, 0.0),
    "PaintCream": ("flat", "f1e3c0", 0.6, 0.0),
    "HazardYellow": ("flat", "f2c12e", 0.5, 0.0),
    "HazardBlack": ("flat", "2b2b30", 0.5, 0.0),
    "Gold": ("flat", "ffc93c", 0.3, 1.0),
    "Rope": ("flat", "c9a46a", 0.9, 0.0),
    "Hay": ("flat", "e8c25a", 0.9, 0.0),
    "Dial": ("flat", "f6efdc", 0.5, 0.0),
    "Needle": ("flat", "d63a2f", 0.5, 0.0),
    "GlassDark": ("flat", "27324a", 0.1, 0.0),
    "Apple": ("flat", "d93d2f", 0.5, 0.0),
    "Orange": ("flat", "f28c28", 0.5, 0.0),
    "Pumpkin": ("flat", "e8862a", 0.6, 0.0),
    "Bread": ("flat", "d79e57", 0.8, 0.0),
    "Cabbage": ("flat", "8fd15a", 0.7, 0.0),
    "Grape": ("flat", "7b4fb8", 0.5, 0.0),
    "Cheese": ("flat", "ffd257", 0.7, 0.0),
    "BottleGreen": ("flat", "3f9e6b", 0.2, 0.0),
    "BottleBlue": ("flat", "4f78d6", 0.2, 0.0),
    "TargetRed": ("flat", "d8392f", 0.6, 0.0),
    "TargetWhite": ("flat", "f6efe2", 0.6, 0.0),
    "Charcoal": ("flat", "35303a", 0.9, 0.0),
}


def M(name):
    """Get an accent material by name (see ACCENTS)."""
    if name == "Water":   # the spec asks for rw.flat("Water", "4fb7d9"); glossy for the preview
        return rw.flat("Water", "4fb7d9", 0.08, 0.0)
    k = ACCENTS[name]
    if k[0] == "glow":
        return rw.glow(name, k[1], k[2])
    return rw.flat(name, k[1], k[2], k[3])


def mat(m):
    """Resolve a material spec: 'M_*' library names pass through, other names go via M()."""
    if m is None or isinstance(m, bpy.types.Material):
        return m
    if m.startswith("M_"):
        return m
    if m in ACCENTS or m == "Water":
        return M(m)
    return m


# --------------------------------------------------------------------------------------
# Small math helpers
# --------------------------------------------------------------------------------------

def deg(e):
    return tuple(math.degrees(a) for a in e)


def frame_euler(x_axis, up=(0, 0, 1)):
    """Euler (degrees) of a frame whose local +X points along x_axis and local +Z is as close to `up` as possible."""
    x = V(x_axis).normalized()
    u = V(up)
    if abs(x.dot(u.normalized())) > 0.999:
        u = V((0, 1, 0)) if abs(x.y) < 0.9 else V((1, 0, 0))
    y = u.cross(x).normalized()
    z = x.cross(y).normalized()
    m = Matrix((x, y, z)).transposed()
    return deg(m.to_euler())


def z_to_euler(d, roll_hint=(1, 0, 0)):
    """Euler (degrees) mapping local +Z onto direction d."""
    z = V(d).normalized()
    h = V(roll_hint)
    if abs(z.dot(h.normalized())) > 0.99:
        h = V((0, 1, 0)) if abs(z.y) < 0.9 else V((0, 0, 1))
    y = z.cross(h).normalized()
    x = y.cross(z).normalized()
    m = Matrix((x, y, z)).transposed()
    return deg(m.to_euler())


def lerp(a, b, t):
    return a + (b - a) * t


def place(objs, loc=(0, 0, 0), rot=(0, 0, 0), pivot=(0, 0, 0)):
    """Rigidly move objects: rotate about `pivot` by `rot` (degrees), then translate by `loc`.
    The rotation is baked into each mesh; every node keeps only a location."""
    R = Euler(tuple(math.radians(a) for a in rot)).to_matrix().to_4x4()
    T = Matrix.Translation(V(loc)) @ Matrix.Translation(V(pivot)) @ R @ Matrix.Translation(-V(pivot))
    out = []
    for o in (objs if isinstance(objs, (list, tuple)) else [objs]):
        if o is None:
            continue
        o.matrix_world = T @ o.matrix_world
        if o.type == 'MESH':
            rw.apply_transform(o)
        out.append(o)
    return out


def deform(o, fn):
    """Apply fn(world Vector) -> world Vector to every vertex (modifiers are applied first)."""
    rw.apply_modifiers(o)
    mw = o.matrix_world
    inv = mw.inverted()
    for v in o.data.vertices:
        v.co = inv @ V(fn(mw @ v.co))
    o.data.update()
    clear_custom_normals(o)
    return o


def clear_custom_normals(o):
    try:
        if o.data.has_custom_normals:
            rw._active(o)
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception:
        pass
    return o


# --------------------------------------------------------------------------------------
# Primitive wrappers
# --------------------------------------------------------------------------------------

def rbox(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=None, r=0.03, seg=1):
    """Rounded box (live bevel); r is clamped to the smallest half-size."""
    r = min(r, min(size) * 0.45)
    if r <= 0.002:
        return rw.box(name, size, loc, rot, mat(m))
    return rw.rounded_box(name, size, r, loc, rot, mat(m), seg)


def cbox(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=None, b=0.02, seg=1):
    """Chamfered box (angle-limited bevel, cheap: ~44 tris with seg=1)."""
    b = min(b, min(size) * 0.45)
    o = rw.box(name, size, loc, rot, mat(m))
    if b > 0.001:
        rw.add_bevel(o, b, seg, 40, harden=False)
    return o


def beam(name, p0, p1, w=0.15, h=0.15, m="M_WoodDark", r=0.025, up=(0, 0, 1), extend=0.0, seg=1):
    """Box-section beam from p0 to p1 (local X along the beam, local Z towards `up`)."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    c = (p0 + p1) / 2
    size = (d.length + 2 * extend, w, h)
    rot = frame_euler(d, up)
    if r > 0:
        return rbox(name, size, tuple(c), rot, m, r, seg)
    return rw.box(name, size, tuple(c), rot, mat(m))


def rod(name, p0, p1, r=0.05, verts=12, m="M_Steel", cap="NGON"):
    """Cylinder from p0 to p1."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    return rw.cylinder(name, r, d.length, verts, tuple((p0 + p1) / 2), z_to_euler(d), mat(m), cap=cap)


def disc(name, r, depth, loc, normal=(0, 0, 1), verts=24, m=None):
    return rw.cylinder(name, r, depth, verts, loc, z_to_euler(normal), mat(m))


def ball(name, r, loc, m=None, seg=8, rings=6, scale=(1, 1, 1)):
    return rw.sphere(name, r, seg, rings, loc, (0, 0, 0), scale, mat(m))


def ring(name, major, minor, loc=(0, 0, 0), normal=(0, 0, 1), m="M_Brass", seg=24, mseg=8):
    return rw.torus(name, major, minor, seg, mseg, loc, z_to_euler(normal), mat(m))


def lathe(name, profile, seg=24, loc=(0, 0, 0), m=None, smooth=50, cap_bottom=True, cap_top=True, rot=(0, 0, 0)):
    return rw.lathe(name, profile, seg, loc, rot, mat(m), None, cap_bottom, cap_top, smooth)


def poly_prism(name, pts2d, depth, loc=(0, 0, 0), rot=(0, 0, 0), m=None, bevel=0.0):
    """Extrude a CCW 2D polygon (X, Y) along local Z (centred). Use rot=(90,0,0) to stand it up facing -Y:
    then 2D (x, y) -> world (x, ., y)."""
    return rw.extrude_poly(name, pts2d, depth, loc, rot, mat(m), bevel)


def upright_prism(name, pts_xz, depth, y=0.0, x0=0.0, z0=0.0, m=None, bevel=0.0):
    """Polygon given in the XZ plane (as seen from the front, -Y), extruded along Y, centred at y."""
    o = rw.extrude_poly(name, pts_xz, depth, (x0, y, z0), (90, 0, 0), mat(m), 0.0)
    if bevel > 0:
        rw.add_bevel(o, bevel, 1, 40, harden=False)
    return o


def tube(name, pts, r=0.04, m="M_Copper", res=1, smooth=True, ures=3, caps=True, taper=None):
    """Tube along a path (pipes, frames, ropes). Unlike rw.tube this keeps the curve resolution low:
    `res` = bevel resolution (cross-section 4 + 2*res verts), `ures` = segments per bezier span."""
    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.bevel_depth = r
    cd.bevel_resolution = res
    cd.resolution_u = ures
    cd.use_fill_caps = caps
    pts = [tuple(p) for p in pts]
    sp = cd.splines.new('BEZIER' if smooth else 'POLY')
    if smooth:
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
    else:
        sp.points.add(len(pts) - 1)
        for pt, p in zip(sp.points, pts):
            pt.co = (p[0], p[1], p[2], 1.0)
    if taper is not None:
        seq = sp.bezier_points if smooth else sp.points
        for i, pt in enumerate(seq):
            t = i / max(1, len(pts) - 1)
            pt.radius = taper[0] + (taper[1] - taper[0]) * t
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    rw._active(o)
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    if m is not None:
        rw.set_mat(o, mat(m))
    rw.smooth(o, 60)
    return o


def gear(name, radius, teeth=10, depth=0.08, thick=0.1, hole=0.0, loc=(0, 0, 0), normal=(0, -1, 0), m="M_Brass",
         bevel=0.0, spin=0.0, spokes=0):
    """Cheap cartoon gear (built directly as a mesh; ~32 tris per tooth with a hole, ~16 without). The axis points
    along `normal` (default: faces the front, -Y). `bevel` adds a 1-segment chamfer (doubles the cost)."""
    n = teeth * 4
    sp = math.radians(spin)
    outer = []
    for i in range(n):
        a = 2 * math.pi * i / n + sp
        phase = i % 4
        r = radius if phase in (1, 2) else radius - depth
        outer.append((r * math.cos(a), r * math.sin(a)))
    bm = bmesh.new()
    top = [bm.verts.new((x, y, thick / 2)) for (x, y) in outer]
    bot = [bm.verts.new((x, y, -thick / 2)) for (x, y) in outer]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    if hole and hole > 0:
        k = max(8, teeth * 2)
        ti = [bm.verts.new((hole * math.cos(2 * math.pi * i / k + sp), hole * math.sin(2 * math.pi * i / k + sp), thick / 2)) for i in range(k)]
        bi = [bm.verts.new((hole * math.cos(2 * math.pi * i / k + sp), hole * math.sin(2 * math.pi * i / k + sp), -thick / 2)) for i in range(k)]
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((ti[i], ti[j], bi[j], bi[i]))
        # annulus caps: connect each inner vert to the outer verts in its sector
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
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(g)
    rw.set_mat(g, mat(m))
    if bevel and bevel > 0:
        rw.add_bevel(g, bevel, 1, 40, harden=False)
    parts = [g]
    if spokes and hole:
        pass
    place([g], loc, z_to_euler(normal))
    rw.smooth(g, 30)
    return g


def join(objs, name, origin=(0, 0, 0), smooth=None):
    objs = [x for x in objs if x is not None]
    if os.environ.get("RW_TRIS"):
        extremes(objs)
        tri_breakdown(objs)
    o = rw.join(objs, name, origin)
    if smooth:
        rw.smooth(o, smooth)
    return o


def face_prism(name, pts2d, depth, center, u_dir, m=None, bevel=0.0):
    """Polygon drawn on a vertical wall plane: 2D (a, b) -> center + a*u_dir + b*Z, extruded `depth` along the
    wall normal (centred on the plane)."""
    u = V(u_dir).normalized()
    up = V((0, 0, 1))
    n = u.cross(up).normalized()
    Mx = Matrix((u, up, n)).transposed()
    o = rw.extrude_poly(name, pts2d, depth, tuple(center), deg(Mx.to_euler()), mat(m), 0.0)
    if bevel > 0:
        rw.add_bevel(o, bevel, 1, 40, harden=False)
    return o


class Face:
    """A vertical wall face: origin on the face, `u` = horizontal direction along the face, `n` = outward normal.
    Face coordinates (a, z): a along u from the origin, z = world height."""

    def __init__(self, origin, u, n):
        self.o = V(origin)
        self.u = V(u).normalized()
        self.n = V(n).normalized()

    def p(self, a, z, out=0.0):
        return self.o + self.u * a + V((0, 0, z)) + self.n * out

    def rot(self):
        """Euler (degrees) that turns a local '-Y facing' detail onto this face."""
        ang = math.degrees(math.atan2(-self.n.x, self.n.y)) + 180.0
        return (0, 0, ang)

    def put(self, objs, a, z, out=0.0):
        """Place details built in the local window/door frame (wall y=0 facing -Y) onto this face."""
        return place(objs, tuple(self.p(a, z, out)), self.rot())

    def beam(self, a0, z0, a1, z1, w=0.16, depth=0.12, proud=0.05, m="M_WoodDark", r=0.025, extend=0.0):
        p0 = self.p(a0, z0, proud - depth / 2)
        p1 = self.p(a1, z1, proud - depth / 2)
        return beam("tb", p0, p1, w, depth, m, r, up=tuple(self.n), extend=extend)


# --------------------------------------------------------------------------------------
# Parametric slab (roofs, cloth, awnings, curved walls)
# --------------------------------------------------------------------------------------

def param_slab(name, P, nu, nv, m=None, close_u=False):
    """Thick sheet from a parametric surface. P(u, v, s) -> (x, y, z) with u, v in [0, 1] and s in {0, 1}
    (0 = bottom / inner surface, 1 = top / outer surface). Normals are made consistent and outward."""
    bm = bmesh.new()
    nu_v = nu if close_u else nu + 1
    grid = {}
    for s in (0, 1):
        for j in range(nv + 1):
            for i in range(nu_v):
                grid[(i, j, s)] = bm.verts.new(P(i / nu, j / nv, s))

    def g(i, j, s):
        return grid[(i % nu_v if close_u else i, j, s)]

    for j in range(nv):
        for i in range(nu):
            bm.faces.new((g(i, j, 1), g(i + 1, j, 1), g(i + 1, j + 1, 1), g(i, j + 1, 1)))
            bm.faces.new((g(i, j, 0), g(i, j + 1, 0), g(i + 1, j + 1, 0), g(i + 1, j, 0)))
    for i in range(nu):
        bm.faces.new((g(i, 0, 0), g(i + 1, 0, 0), g(i + 1, 0, 1), g(i, 0, 1)))
        bm.faces.new((g(i, nv, 1), g(i + 1, nv, 1), g(i + 1, nv, 0), g(i, nv, 0)))
    if not close_u:
        for j in range(nv):
            bm.faces.new((g(0, j, 1), g(0, j + 1, 1), g(0, j + 1, 0), g(0, j, 0)))
            bm.faces.new((g(nu, j, 0), g(nu, j + 1, 0), g(nu, j + 1, 1), g(nu, j, 1)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m is not None:
        rw.set_mat(o, mat(m))
    return o


def sheet(name, P, nu, nv, m=None):
    """Single-sided grid surface P(u, v) -> (x, y, z) (cloth that gets a solidify later, ground decals...)."""
    bm = bmesh.new()
    grid = {}
    for j in range(nv + 1):
        for i in range(nu + 1):
            grid[(i, j)] = bm.verts.new(P(i / nu, j / nv))
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m is not None:
        rw.set_mat(o, mat(m))
    return o


def solidify(o, t, offset=0.0):
    md = o.modifiers.new("Solid", 'SOLIDIFY')
    md.thickness = t
    md.offset = offset
    md.use_even_offset = True
    rw.apply_modifiers(o)
    return o


# --------------------------------------------------------------------------------------
# Collision proxies
# --------------------------------------------------------------------------------------

_col_n = {}


def _col_name(tag):
    n = _col_n.get(tag, 0)
    _col_n[tag] = n + 1
    return "Col_%s_%d" % (tag, n)


def col_box(tag, size, loc, rot=(0, 0, 0)):
    """Box collision proxy (exported as <name>-colonly)."""
    return rw.collision_box(_col_name(tag), size, loc, rot)


def col_beam(tag, p0, p1, w, h, up=(0, 0, 1), extend=0.0):
    """Oriented box collision between two points (local X along p0->p1, local Z toward `up`)."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    return rw.collision_box(_col_name(tag), (d.length + 2 * extend, w, h), tuple((p0 + p1) / 2), frame_euler(d, up))


def col_cyl(tag, r, depth, loc, rot=(0, 0, 0), verts=12):
    """Convex cylinder collision proxy (exported as <name>-convcolonly)."""
    return rw.collision_cylinder(_col_name(tag), r, depth, loc, rot, None, verts)


def col_frustum(tag, r_bottom, r_top, depth, loc, verts=16, square=False):
    """Convex frustum proxy (ramps around pads and stepped platforms). With square=True, r_* are HALF-WIDTHS
    of an axis-aligned square frustum."""
    if square:
        rb, rt, verts, rot = r_bottom * math.sqrt(2), r_top * math.sqrt(2), 4, (0, 0, 45)
    else:
        rb, rt, rot = r_bottom, r_top, (0, 0, 0)
    o = rw.cone(_col_name(tag) + "-convcolonly", rb, rt, depth, verts, loc, rot)
    o.display_type = 'WIRE'
    o.hide_render = True
    return o


def col_hull(tag, verts):
    """Convex hull proxy from a point list (-convcolonly)."""
    bm = bmesh.new()
    for p in verts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new("hull")
    bm.to_mesh(me)
    bm.free()
    name = _col_name(tag) + "-convcolonly"
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.display_type = 'WIRE'
    o.hide_render = True
    return o


def collision_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and ("-colonly" in o.name or "-convcolonly" in o.name)]


# --------------------------------------------------------------------------------------
# Reusable building details
# --------------------------------------------------------------------------------------

def rivet(name, loc, r=0.03, m="M_Brass", lo=False):
    if lo:
        return rw.sphere(name, r, 5, 3, loc, (0, 0, 0), (1, 1, 1), mat(m))
    return rw.sphere(name, r, 6, 4, loc, (0, 0, 0), (1, 1, 1), mat(m))


def rivet_line(p0, p1, n, r=0.03, m="M_Brass", end_inset=0.0):
    p0, p1 = V(p0), V(p1)
    out = []
    for i in range(n):
        t = (i + 0.5) / n if end_inset is None else (i / max(1, n - 1))
        p = p0.lerp(p1, t)
        out.append(rivet("rivet", tuple(p), r, m))
    return out


def rivet_ring(center, radius, n, r=0.03, m="M_Brass", axis="Z", phase=0.0, lo=False):
    c = V(center)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + phase
        if axis == "Z":
            p = c + V((radius * math.cos(a), radius * math.sin(a), 0))
        elif axis == "Y":
            p = c + V((radius * math.cos(a), 0, radius * math.sin(a)))
        else:
            p = c + V((0, radius * math.cos(a), radius * math.sin(a)))
        out.append(rivet("rivet", tuple(p), r, m, lo))
    return out


def arch_outline(w, spring, rise=None, n=10, bottom=0.0):
    """Closed CCW outline (x, z) of a round-topped opening: straight jambs from `bottom` to `spring`,
    then an elliptical arch of half-width w/2 and height `rise` (default w/2)."""
    rise = w / 2 if rise is None else rise
    pts = [(-w / 2, bottom), (w / 2, bottom)]
    for i in range(n + 1):
        a = math.pi * i / n
        pts.append((w / 2 * math.cos(a), spring + rise * math.sin(a)))
    pts.append((-w / 2, bottom))
    # remove the duplicate closing point and duplicate jamb points
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > 1e-6 or abs(out[-1][1] - p[1]) > 1e-6):
            out.append(p)
    if abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def arch_path(w, spring, rise=None, n=10, bottom=0.0):
    """Open path (x, z) up the left jamb, over the arch and down the right jamb (for tube frames)."""
    rise = w / 2 if rise is None else rise
    pts = [(-w / 2, bottom)]
    for i in range(n + 1):
        a = math.pi - math.pi * i / n
        pts.append((w / 2 * math.cos(a), spring + rise * math.sin(a)))
    pts.append((w / 2, bottom))
    return pts


def window(w=0.9, h=1.1, kind="rect", shutters=None, flowerbox=False, frame="M_WoodDark", glow="WindowGlow",
           mullions=True, sill=True, depth=0.1, flowers=("FlowerPink", "FlowerYellow", "FlowerRed"), seed=0,
           frame_w=0.09, shutter_open=25):
    """A window built in a local frame: wall face is the plane y=0, the window faces -Y, centred on (0, 0, 0)
    (x = across, z = up). Returns a list of objects; move it with place(objs, loc, (0, 0, angle))."""
    rnd = random.Random(seed)
    parts = []
    fw = frame_w
    if kind == "round":
        r = w / 2
        parts.append(disc("pane", r * 0.98, 0.04, (0, -0.015, 0), (0, -1, 0), 20, glow))
        parts.append(ring("frame", r, fw * 0.55, (0, -0.04, 0), (0, -1, 0), frame, 20, 8))
        if mullions:
            parts.append(rbox("mul", (w * 0.95, 0.05, 0.05), (0, -0.05, 0), (0, 0, 0), frame, 0.015))
            parts.append(rbox("mul", (0.05, 0.05, w * 0.95), (0, -0.05, 0), (0, 0, 0), frame, 0.015))
        return parts
    if kind == "arch":
        spring = h / 2 - w / 2
        outline = arch_outline(w, spring, w / 2, 10, -h / 2)
        parts.append(upright_prism("pane", outline, 0.04, -0.015, 0, 0, glow))
        path = arch_path(w + fw * 0.6, spring, w / 2 + fw * 0.3, 12, -h / 2)
        parts.append(tube("frame", [(x, -0.05, z) for (x, z) in path], fw * 0.55, frame, 1, smooth=False))
        if mullions:
            parts.append(rbox("mul", (0.05, 0.05, h * 0.96), (0, -0.05, 0), (0, 0, 0), frame, 0.015))
            parts.append(rbox("mul", (w * 0.96, 0.05, 0.05), (0, -0.05, spring), (0, 0, 0), frame, 0.015))
    else:
        parts.append(rw.box("pane", (w, 0.04, h), (0, -0.015, 0), mat=mat(glow)))
        parts.append(rbox("jamb", (fw, depth, h + fw), (-w / 2 - fw / 2 + 0.02, -depth / 2, 0), (0, 0, 0), frame, 0.02))
        parts.append(rbox("jamb", (fw, depth, h + fw), (w / 2 + fw / 2 - 0.02, -depth / 2, 0), (0, 0, 0), frame, 0.02))
        parts.append(rbox("head", (w + 2 * fw + 0.08, depth + 0.02, fw * 1.1), (0, -depth / 2, h / 2 + fw * 0.45), (0, 0, 0), frame, 0.025))
        if mullions:
            parts.append(rbox("mul", (0.05, 0.05, h), (0, -0.04, 0), (0, 0, 0), frame, 0.015))
            parts.append(rbox("mul", (w, 0.05, 0.05), (0, -0.04, 0.05 * h), (0, 0, 0), frame, 0.015))
    if sill:
        parts.append(rbox("sill", (w + 2 * fw + 0.14, depth + 0.08, 0.08), (0, -depth / 2 - 0.04, -h / 2 - 0.03), (0, 0, 0), frame, 0.025))
    if shutters:
        sw = w / 2 + 0.02
        for sx in (-1, 1):
            ang = sx * -shutter_open
            # hinge at the outer edge of the frame
            hx = sx * (w / 2 + fw)
            sh = []
            nb = 2
            for b in range(nb):
                bx = hx + sx * (sw * (b + 0.5) / nb)
                sh.append(rbox("shutter", (sw / nb - 0.015, 0.05, h * 0.98), (bx, -0.06, 0), (0, 0, 0), shutters, 0.015))
            for zz in (-h * 0.3, h * 0.3):
                sh.append(rbox("batten", (sw * 0.95, 0.04, 0.08), (hx + sx * sw / 2, -0.095, zz), (0, 0, 0), shutters, 0.015))
            sh.append(beam("brace", (hx + sx * 0.06, -0.095, -h * 0.25), (hx + sx * (sw - 0.06), -0.095, h * 0.25), 0.035, 0.07, shutters, 0.012, up=(0, -1, 0)))
            place(sh, (0, 0, 0), (0, 0, ang), pivot=(hx, -0.03, 0))
            parts += sh
    if flowerbox:
        bw = w + 0.3
        bz = -h / 2 - 0.2
        parts.append(rbox("fbox", (bw, 0.3, 0.24), (0, -0.2, bz), (0, 0, 0), "M_WoodPlanks", 0.03))
        parts.append(rw.box("soil", (bw - 0.08, 0.22, 0.04), (0, -0.2, bz + 0.11), mat=M("Soil")))
        for (bx, bzz) in ((-bw * 0.32, 0.0), (bw * 0.32, 0.0)):
            parts.append(beam("bracket", (bx, -0.02, bz - 0.25), (bx, -0.3, bz - 0.1), 0.05, 0.06, "M_WoodDark", 0.015))
        nleaf = max(3, int(bw / 0.22))
        for i in range(nleaf):
            x = -bw / 2 + 0.12 + (bw - 0.24) * i / max(1, nleaf - 1)
            parts.append(rw.ico("leaf", 0.1 + rnd.uniform(0, 0.03), 1, (x, -0.2 + rnd.uniform(-0.05, 0.05), bz + 0.17 + rnd.uniform(0, 0.04)),
                                (0, 0, rnd.uniform(0, 90)), (1.2, 1.0, 0.8), M("Leaf" if i % 2 else "LeafDark"), None, 30))
        nfl = max(3, int(bw / 0.2))
        for i in range(nfl):
            x = -bw / 2 + 0.1 + (bw - 0.2) * (i + rnd.uniform(-0.2, 0.2)) / max(1, nfl - 1)
            fc = flowers[i % len(flowers)]
            parts.append(rw.ico("flower", 0.055, 1, (x, -0.24 + rnd.uniform(-0.06, 0.06), bz + 0.27 + rnd.uniform(0, 0.06)),
                                (0, 0, 0), (1, 1, 0.75), M(fc), None, 0))
    return parts


def door(w=1.1, h=2.1, arch=True, m="M_WoodPlanks", frame="M_WoodDark", planks=4, straps=True, knob=True,
         frame_w=0.14, recess=0.0, round_window=False):
    """Decorative door in the local wall frame (wall plane y=0, faces -Y, bottom at z=0, centred on x=0)."""
    parts = []
    spring = h - w / 2 if arch else h
    gap = 0.025
    pw = (w - gap * (planks - 1)) / planks
    for i in range(planks):
        x0 = -w / 2 + i * (pw + gap)
        x1 = x0 + pw
        if arch:
            pts = [(x0, 0), (x1, 0)]
            ns = 4
            for k in range(ns + 1):
                x = x1 - (x1 - x0) * k / ns
                t = max(-1.0, min(1.0, x / (w / 2)))
                pts.append((x, spring + (w / 2) * math.sqrt(max(0.0, 1 - t * t))))
            outline = []
            for p in pts:
                if not outline or abs(outline[-1][0] - p[0]) > 1e-6 or abs(outline[-1][1] - p[1]) > 1e-6:
                    outline.append(p)
        else:
            outline = [(x0, 0), (x1, 0), (x1, h), (x0, h)]
        parts.append(upright_prism("plank", outline, 0.08, -0.04 + recess, 0, 0, m, 0.012))
    if arch:
        path = arch_path(w + frame_w * 0.9, spring, w / 2 + frame_w * 0.45, 14, 0)
        parts.append(tube("dframe", [(x, -0.07 + recess, z) for (x, z) in path], frame_w * 0.5, frame, 1, smooth=False))
    else:
        parts.append(rbox("jamb", (frame_w, 0.16, h + frame_w), (-w / 2 - frame_w / 2, -0.06 + recess, (h + frame_w) / 2), (0, 0, 0), frame, 0.03))
        parts.append(rbox("jamb", (frame_w, 0.16, h + frame_w), (w / 2 + frame_w / 2, -0.06 + recess, (h + frame_w) / 2), (0, 0, 0), frame, 0.03))
        parts.append(rbox("lintel", (w + 2 * frame_w + 0.1, 0.18, frame_w * 1.2), (0, -0.07 + recess, h + frame_w * 0.6), (0, 0, 0), frame, 0.03))
    if straps:
        for zz in (h * 0.22, min(h * 0.62, spring)):
            parts.append(rbox("strap", (w * 0.86, 0.03, 0.08), (-w * 0.04, -0.095 + recess, zz), (0, 0, 0), "Iron", 0.012))
            parts.append(rivet("nail", (-w * 0.3, -0.11 + recess, zz), 0.02, "Iron"))
            parts.append(rivet("nail", (w * 0.15, -0.11 + recess, zz), 0.02, "Iron"))
    if knob:
        parts.append(ring("knocker", 0.07, 0.016, (w * 0.28, -0.115 + recess, h * 0.47), (0, -1, 0), "M_Brass", 12, 6))
        parts.append(ball("knob", 0.035, (w * 0.28, -0.1 + recess, h * 0.53), "M_Brass", 8, 6))
    if round_window:
        parts.append(disc("dwin", 0.13, 0.03, (0, -0.09 + recess, spring + 0.05), (0, -1, 0), 14, "WindowGlow"))
        parts.append(ring("dwinr", 0.14, 0.03, (0, -0.1 + recess, spring + 0.05), (0, -1, 0), "M_Brass", 14, 6))
    return parts


def lantern(loc, kind="wall", m="M_Brass", glow="LampGlow", scale=1.0, wall_normal=(0, -1, 0), light=None):
    """Brass lantern. kind 'wall' (bracket toward wall_normal's opposite), 'hang' (hangs below loc) or 'post' (sits on loc).
    Returns (parts, light_point_location)."""
    s = scale
    parts = []
    c = V(loc)
    if kind == "hang":
        c = c - V((0, 0, 0.35 * s))
    elif kind == "post":
        c = c + V((0, 0, 0.22 * s))
    # body
    parts.append(rw.cylinder("lcap", 0.13 * s, 0.05 * s, 8, tuple(c + V((0, 0, -0.16 * s))), (0, 0, 22.5), mat(m)))
    parts.append(rw.cone("lroof", 0.17 * s, 0.03 * s, 0.14 * s, 8, tuple(c + V((0, 0, 0.17 * s))), (0, 0, 22.5), mat(m)))
    parts.append(rw.cylinder("lglass", 0.1 * s, 0.26 * s, 8, tuple(c), (0, 0, 22.5), mat("M_Glass")))
    parts.append(rw.cylinder("lcore", 0.06 * s, 0.17 * s, 8, tuple(c), (0, 0, 0), mat(glow)))
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p = c + V((0.1 * s * math.cos(a), 0.1 * s * math.sin(a), 0))
        parts.append(rod("lbar", p + V((0, 0, -0.14 * s)), p + V((0, 0, 0.12 * s)), 0.014 * s, 6, m))
    parts.append(ring("lring", 0.05 * s, 0.012 * s, tuple(c + V((0, 0, 0.27 * s))), (1, 0, 0), m, 10, 5))
    if kind == "wall":
        n = V(wall_normal).normalized()
        back = c - n * 0.32 * s
        top = c + V((0, 0, 0.3 * s))
        parts.append(rod("larm", tuple(back + V((0, 0, 0.3 * s))), tuple(top), 0.018 * s, 6, "Iron"))
        parts.append(rbox("lplate", (0.12 * s, 0.03 * s, 0.22 * s) if abs(n.y) > 0.5 else (0.03 * s, 0.12 * s, 0.22 * s),
                          tuple(back + V((0, 0, 0.26 * s))), (0, 0, 0), "Iron", 0.01))
    elif kind == "hang":
        parts.append(rod("lchain", tuple(V(loc)), tuple(c + V((0, 0, 0.27 * s))), 0.012 * s, 5, "Iron"))
    return parts, tuple(c)


def flower_cluster(center, radius=0.35, n=6, seed=0, colors=("FlowerPink", "FlowerYellow", "FlowerWhite")):
    rnd = random.Random(seed)
    c = V(center)
    parts = []
    for i in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        p = c + V((math.cos(a) * radius * 0.4, math.sin(a) * radius * 0.4, 0.08))
        parts.append(rw.ico("bushleaf", radius * 0.45, 1, tuple(p), (0, 0, rnd.uniform(0, 90)), (1.1, 1.0, 0.75), M("Leaf" if i % 2 else "LeafDark"), None, 30))
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0, radius * 0.7)
        p = c + V((math.cos(a) * rr, math.sin(a) * rr, 0.2 + rnd.uniform(0, 0.08)))
        parts.append(rw.ico("flower", 0.05, 1, tuple(p), (0, 0, 0), (1, 1, 0.75), M(colors[i % len(colors)]), None, 0))
    return parts


# --------------------------------------------------------------------------------------
# Props reused inside other assets
# --------------------------------------------------------------------------------------

def crate(size=(0.6, 0.6, 0.6), loc=(0, 0, 0), rotz=0.0, m="M_WoodPlanks", trim="M_WoodDark", bands=True):
    """Low-poly crate (~250 tris); loc is the bottom centre."""
    sx, sy, sz = size
    parts = [cbox("crate", (sx - 0.04, sy - 0.04, sz - 0.04), (0, 0, sz / 2), (0, 0, 0), m, 0.02)]
    t = min(0.07, sx * 0.14)
    if bands:
        for zz in (t / 2 + 0.005, sz - t / 2 - 0.005):
            parts.append(cbox("band", (sx, sy, t), (0, 0, zz), (0, 0, 0), trim, 0.015))
        for xs in (-1, 1):
            for ys in (-1, 1):
                parts.append(rw.box("post", (t, t, sz - 2 * t), (xs * (sx / 2 - t / 2), ys * (sy / 2 - t / 2), sz / 2), mat=mat(trim)))
        d = math.hypot(sx - 2 * t, sz - 2 * t)
        ang = math.degrees(math.atan2(sz - 2 * t, sx - 2 * t))
        parts.append(cbox("diag", (d * 0.96, 0.03, t * 0.9), (0, -sy / 2 - 0.005, sz / 2), (0, -ang, 0), trim, 0.01))
    place(parts, loc, (0, 0, rotz))
    return parts


def barrel(r=0.32, h=0.9, loc=(0, 0, 0), rotz=0.0, seg=14, m="M_WoodDark", hoop="Iron", lying=False, lid=True):
    """Barrel from a single lathe (hoops are part of the profile); loc = bottom centre (or contact point if lying)."""
    bulge = r * 0.14
    rb = r - bulge
    prof = []
    hz = [0.1, 0.13, 0.87, 0.9]

    def rad(t):
        return rb + bulge * math.sin(math.pi * t)

    zs = [0.0, 0.08, 0.1, 0.16, 0.3, 0.5, 0.7, 0.84, 0.9, 0.92, 1.0]
    for t in zs:
        rr = rad(t)
        if 0.085 <= t <= 0.165 or 0.835 <= t <= 0.915:
            rr += 0.018
        prof.append((rr, t * h))
    prof = [(r * 0.86 - bulge * 0.5, 0.0)] + prof[1:-1] + [(rad(1.0), h)]
    o = rw.lathe("barrel", prof, seg, (0, 0, 0), (0, 0, 0), mat(m), None, True, True, 40)
    # hoop material on the raised bands
    rw.set_mat_where(o, mat(hoop), lambda c, n: (0.08 * h <= c.z <= 0.17 * h or 0.83 * h <= c.z <= 0.92 * h) and abs(n.z) < 0.7)
    parts = [o]
    if lid:
        parts.append(rw.cylinder("lid", rad(1.0) * 0.86, 0.03, seg, (0, 0, h - 0.025), (0, 0, 0), mat("M_WoodPlanks")))
        parts.append(rw.cylinder("bung", 0.04, 0.03, 8, (r * 0.35, 0, h - 0.0), (0, 0, 0), mat("M_Brass")))
    if lying:
        place(parts, (0, 0, 0), (0, 90, 0))
        place(parts, (-h / 2, 0, rad(0.5)), (0, 0, 0))
    place(parts, loc, (0, 0, rotz))
    return parts


def sack(loc=(0, 0, 0), h=0.6, r=0.26, rotz=0.0, tilt=0.0, m="M_Fabric__c9a66b", seg=10):
    """Grain sack with a tied neck; loc = bottom centre."""
    prof = [(r * 0.55, 0.0), (r * 0.92, 0.06 * h), (r, 0.3 * h), (r * 0.9, 0.62 * h), (r * 0.5, 0.82 * h),
            (r * 0.22, 0.88 * h), (r * 0.3, 0.95 * h), (r * 0.18, h)]
    o = rw.lathe("sack", prof, seg, (0, 0, 0), (0, 0, 0), mat(m), None, True, True, 70)
    tie = rw.torus("tie", r * 0.24, 0.025, 8, 3, (0, 0, 0.87 * h), (0, 0, 0), mat("Rope"))
    parts = [o, tie]
    place(parts, (0, 0, 0), (tilt, 0, 0))
    place(parts, loc, (0, 0, rotz))
    return parts


# --------------------------------------------------------------------------------------
# Rune glyphs / emblems
# --------------------------------------------------------------------------------------

# Glyph strokes in a unit square [-0.5, 0.5]^2: lines ((x0, y0), (x1, y1)) and circles ('o', cx, cy, r)
GLYPHS = [
    [((0, -0.5), (0, 0.5)), ((0, 0.15), (0.35, 0.45)), ((0, -0.1), (-0.35, 0.2))],
    [((-0.3, -0.5), (-0.3, 0.5)), ((-0.3, 0.5), (0.3, 0.1)), ((0.3, 0.1), (-0.3, -0.1)), ((-0.3, -0.1), (0.3, -0.5))],
    [('o', 0, 0.15, 0.25), ((0, -0.1), (0, -0.5)), ((-0.25, -0.3), (0.25, -0.3))],
    [((-0.35, -0.5), (0, 0.5)), ((0, 0.5), (0.35, -0.5)), ((-0.2, -0.1), (0.2, -0.1))],
    [((0, -0.5), (0, 0.5)), ((-0.35, 0.3), (0.35, 0.3)), ((-0.35, 0.3), (-0.35, 0.0)), ((0.35, 0.3), (0.35, 0.0))],
    [((-0.35, 0.5), (0.35, -0.5)), ((0.35, 0.5), (-0.35, -0.5)), ((-0.35, 0.0), (0.35, 0.0))],
    [('o', 0, 0, 0.32), ((0, 0.5), (0, -0.5))],
    [((-0.3, -0.5), (-0.3, 0.5)), ((0.3, -0.5), (0.3, 0.5)), ((-0.3, 0.2), (0.3, -0.2))],
]


def glyph(idx, size, loc, normal=(0, -1, 0), m="M_RuneGlow", stroke=0.12, depth=0.04, up=(0, 0, 1)):
    """A rune glyph made of chunky strokes, lying in the plane facing `normal` (its 'up' is `up`)."""
    strokes = GLYPHS[idx % len(GLYPHS)]
    parts = []
    w = stroke * size
    for s in strokes:
        if s[0] == 'o':
            _, cx, cy, r = s
            t = rw.torus("gly", r * size, w * 0.5, 16, 4, (cx * size, 0, cy * size), (90, 0, 0), mat(m))
            t.scale = (1, depth / max(w, 1e-4), 1)
            rw.apply_transform(t)
            parts.append(t)
        else:
            (x0, y0), (x1, y1) = s
            parts.append(beam("gly", (x0 * size, 0, y0 * size), (x1 * size, 0, y1 * size), w, depth, m, 0.0, up=(0, -1, 0), extend=w * 0.4))
    # orient: local -Y -> normal, local +Z -> up
    n = V(normal).normalized()
    u = V(up)
    u = (u - n * u.dot(n)).normalized()
    x = u.cross(-n).normalized()
    # local axes: X -> x, Y -> -n, Z -> u
    Mx = Matrix((x, -n, u)).transposed()
    place(parts, loc, deg(Mx.to_euler()))
    return parts


def star_points(n=5, r_out=0.5, r_in=0.22, phase=90.0):
    pts = []
    for i in range(2 * n):
        a = math.radians(phase) + math.pi * i / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def rune_band_glyphs(center, radius, z, n, size, m="M_RuneGlow", start=0, depth=0.04, phase=0.0):
    """Glyphs around a vertical cylinder (radius = cylinder surface)."""
    parts = []
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        nrm = V((math.cos(a), math.sin(a), 0))
        p = V(center) + nrm * (radius + depth * 0.3) + V((0, 0, z))
        parts += glyph(start + i, size, tuple(p), tuple(nrm), m, depth=depth)
    return parts


# --------------------------------------------------------------------------------------
# Roofs
# --------------------------------------------------------------------------------------

def gable_roof(x0, x1, y0, y1, z_eave, z_ridge, t=0.22, sag=0.12, flare=1.25, nu=10, nv=6, m="M_RoofTiles",
               ridge_mat="M_RoofTiles", barge="M_WoodDark", ridge_axis="X", tilt=0.0, ridge_r=0.13, barge_r=0.09,
               barge_off=0.06):
    """Gable roof over the rectangle [x0,x1] x [y0,y1] (eaves included). ridge_axis 'X': slopes face -Y / +Y,
    gables at -X / +X. `sag` drops the middle of the ridge, `flare` > 1 makes bell-cast eaves, `tilt` raises the
    +X/+Y end of the ridge (crooked look). Returns a list of objects."""
    parts = []

    def frame(u, v_side, s):
        # u along the ridge, v from eave (0) to ridge (1), side -1 / +1
        return u, v_side, s

    def make_side(side):
        def P(u, v, s):
            prof = v ** flare
            sg = sag * 4 * u * (1 - u) * (0.35 + 0.65 * v)
            tl = tilt * (u - 0.5)
            if ridge_axis == "X":
                x = lerp(x0, x1, u)
                yc = (y0 + y1) / 2
                ye = y0 if side < 0 else y1
                y = lerp(ye, yc, v)
            else:
                y = lerp(y0, y1, u)
                xc = (x0 + x1) / 2
                xe = x0 if side < 0 else x1
                x = lerp(xe, xc, v)
            z = z_eave + (z_ridge - z_eave) * prof - sg + tl * (0.3 + 0.7 * v) + s * t
            return (x, y, z) if ridge_axis == "X" else (x, y, z)
        return P

    for side in (-1, 1):
        o = param_slab("roof", make_side(side), nu, nv, m)
        parts.append(o)
    # ridge cap along the top
    pts = []
    for i in range(nu + 1):
        u = i / nu
        sg = sag * 4 * u * (1 - u)
        tl = tilt * (u - 0.5)
        z = z_ridge - sg + tl + t * 0.9
        if ridge_axis == "X":
            pts.append((lerp(x0 - 0.05, x1 + 0.05, u), (y0 + y1) / 2, z))
        else:
            pts.append(((x0 + x1) / 2, lerp(y0 - 0.05, y1 + 0.05, u), z))
    parts.append(tube("ridge", pts, ridge_r, ridge_mat, 2, smooth=True, ures=2))
    # barge boards along the two gable edges
    if barge:
        for end in (0, 1):
            for side in (-1, 1):
                P = make_side(side)
                u = end
                bp = []
                for k in range(nv + 1):
                    v = k / nv
                    x, y, z = P(u, v, 1)
                    if ridge_axis == "X":
                        bp.append((x + (-barge_off if end == 0 else barge_off), y, z - t * 0.4))
                    else:
                        bp.append((x, y + (-barge_off if end == 0 else barge_off), z - t * 0.4))
                parts.append(tube("barge", bp, barge_r, barge, 1, smooth=True, ures=2))
    return parts


def roof_z(x0, x1, y0, y1, z_eave, z_ridge, sag, flare, tilt, ridge_axis, x, y):
    """Height of the roof underside at (x, y) for a gable_roof with the same parameters (for gable walls)."""
    if ridge_axis == "X":
        u = (x - x0) / (x1 - x0)
        yc = (y0 + y1) / 2
        half = (y1 - y0) / 2
        v = 1 - abs(y - yc) / half
    else:
        u = (y - y0) / (y1 - y0)
        xc = (x0 + x1) / 2
        half = (x1 - x0) / 2
        v = 1 - abs(x - xc) / half
    v = max(0.0, min(1.0, v))
    u = max(0.0, min(1.0, u))
    sg = sag * 4 * u * (1 - u) * (0.35 + 0.65 * v)
    tl = tilt * (u - 0.5)
    return z_eave + (z_ridge - z_eave) * v ** flare - sg + tl * (0.3 + 0.7 * v)


def cone_roof(r, h, z0, t=0.2, flare=0.35, seg=24, lean=(0.0, 0.0), m="M_RoofTiles", lip=0.12, curl=0.0):
    """Witch-hat cone roof: radius r at the eave (z0), apex at z0 + h. `flare` widens the bell-cast eave,
    `lean` displaces the tip (x, y) and `curl` bends the very tip further. Returns the roof object."""
    prof = []
    n = 10
    for i in range(n + 1):
        tt = i / n
        rr = r * (1 - tt) ** (1 + flare)
        prof.append((max(rr, 0.0), z0 + h * tt))
    # thickness: outer shell + underside
    outer = [(rr, z) for (rr, z) in prof]
    under = [(r - lip, z0 - 0.001), (r, z0 - t * 0.5)]
    full = [(r * 0.55, z0 + 0.02)] + under + outer[1:]
    full[-1] = (0.0, z0 + h)
    o = rw.lathe("cone", full, seg, (0, 0, 0), (0, 0, 0), mat(m), None, True, False, 60)

    def fn(p):
        tt = max(0.0, (p.z - z0) / h)
        k = tt ** 2.2
        k2 = tt ** 5 * curl
        return V((p.x + lean[0] * k + k2 * lean[0], p.y + lean[1] * k + k2 * lean[1], p.z))
    if lean != (0.0, 0.0) or curl:
        deform(o, fn)
        rw.smooth(o, 60)
    return o


# --------------------------------------------------------------------------------------
# Whole-object crooked deformation
# --------------------------------------------------------------------------------------

def wonk_fn(height, lean=(0.15, 0.0), twist=3.0, bulge=0.0, z0=0.0, center=(0.0, 0.0)):
    """Crooked cartoon deformation: lean the top by `lean` metres (quadratic in height), twist by `twist` degrees
    at the top and bulge the middle outwards by `bulge` (fraction). Returns fn(Vector) -> Vector."""
    cx, cy = center

    def fn(p):
        p = V(p)
        t = max(0.0, (p.z - z0) / height)
        a = math.radians(twist) * t
        x, y = p.x - cx, p.y - cy
        ca, sa = math.cos(a), math.sin(a)
        b = 1 + bulge * math.sin(math.pi * min(1.0, t))
        x, y = (x * ca - y * sa) * b, (x * sa + y * ca) * b
        return V((x + cx + lean[0] * t * t, y + cy + lean[1] * t * t, p.z))
    return fn


def wonk(o, height, lean=(0.15, 0.0), twist=3.0, bulge=0.0, z0=0.0, center=(0.0, 0.0)):
    """Deform an object with wonk_fn(...). Returns the function so empties can be mapped with it."""
    fn = wonk_fn(height, lean, twist, bulge, z0, center)
    deform(o, fn)
    return fn


# --------------------------------------------------------------------------------------
# QA
# --------------------------------------------------------------------------------------

def tri_breakdown(objs=None, top=12):
    """Print triangle counts grouped by object base name (call before joining; RW_TRIS=1 to enable)."""
    if not os.environ.get("RW_TRIS"):
        return
    objs = objs or [o for o in rw.all_mesh_objects() if not o.hide_render]
    groups = {}
    for o in objs:
        base = o.name.split(".")[0]
        n = rw.tri_count([o])
        c = groups.setdefault(base, [0, 0])
        c[0] += n
        c[1] += 1
    for k, (n, cnt) in sorted(groups.items(), key=lambda kv: -kv[1][0])[:top]:
        print("RWTRIS %-14s %6d tris in %4d objects (%d each)" % (k, n, cnt, n // max(1, cnt)))


def extremes(objs=None):
    """Print which part defines each bounding-box face (call before joining; RW_TRIS=1 to enable)."""
    if not os.environ.get("RW_TRIS"):
        return
    objs = [o for o in (objs or rw.all_mesh_objects()) if o is not None and not o.hide_render]
    data = [(o.name, rw.bounds([o])) for o in objs]
    for ax, nm in ((0, "x"), (1, "y"), (2, "z")):
        lo = sorted(data, key=lambda d: d[1][0][ax])[:3]
        hi = sorted(data, key=lambda d: -d[1][1][ax])[:3]
        print("RWEXT min %s: %s" % (nm, ", ".join("%s %.3f" % (n, b[0][ax]) for n, b in lo)))
        print("RWEXT max %s: %s" % (nm, ", ".join("%s %.3f" % (n, b[1][ax]) for n, b in hi)))


def check(asset, size, budget, tol=0.05, height_tol=0.12, centre=True, origin_note=""):
    """Print footprint / height / triangle checks (RWCHECK lines) before rw.finish."""
    mn, mx = rw.bounds()
    s = mx - mn
    w, d, h = size
    ok_w = abs(s.x - w) <= w * tol
    ok_d = abs(s.y - d) <= d * tol
    ok_h = abs(s.z - h) <= h * height_tol
    c = (mn + mx) / 2
    tris = rw.tri_count()
    print("RWCHECK %s size %.2f x %.2f x %.2f (spec %.2f x %.2f x %.2f) -> W %s D %s H %s" % (
        asset, s.x, s.y, s.z, w, d, h, "ok" if ok_w else "OFF", "ok" if ok_d else "OFF", "ok" if ok_h else "OFF"))
    print("RWCHECK %s bounds min (%.2f, %.2f, %.2f) max (%.2f, %.2f, %.2f) centre xy (%.2f, %.2f) %s" % (
        asset, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z, c.x, c.y, origin_note))
    print("RWCHECK %s triangles %d / %d %s" % (asset, tris, budget, "ok" if tris <= budget else "OVER BUDGET"))
    for o in collision_objects():
        omn, omx = rw.bounds([o])
        print("RWCHECK %s collision %-32s min (%.2f, %.2f, %.2f) max (%.2f, %.2f, %.2f)" % (
            asset, o.name, omn.x, omn.y, omn.z, omx.x, omx.y, omx.z))
    for o in bpy.context.scene.objects:
        if o.type == 'EMPTY' and not o.get("rw_helper"):
            p = o.matrix_world.translation
            print("RWCHECK %s empty %-20s at (%.2f, %.2f, %.2f)" % (asset, o.name, p.x, p.y, p.z))
    return s, tris


# --------------------------------------------------------------------------------------
# More shapes: pipes, crystals, wheels, cloth, ring/arc blocks
# --------------------------------------------------------------------------------------

def fillet_path(points, radius=0.3, steps=3):
    """Insert arc points at every interior corner of a polyline (industrial pipe bends)."""
    pts = [V(p) for p in points]
    if len(pts) < 3:
        return [tuple(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d0 = (a - b)
        d1 = (c - b)
        r = min(radius, d0.length * 0.45, d1.length * 0.45)
        d0.normalize()
        d1.normalize()
        p0 = b + d0 * r
        p1 = b + d1 * r
        for k in range(steps + 1):
            t = k / steps
            # quadratic bezier p0 -> b -> p1
            q = p0 * (1 - t) ** 2 + b * 2 * (1 - t) * t + p1 * t * t
            out.append(q)
    out.append(pts[-1])
    return [tuple(p) for p in out]


def pipe(name, points, r=0.08, m="M_Copper", bend=0.3, res=2, flanges=True, flange_mat="M_Brass", caps=True):
    """Straight pipe runs with rounded bends and flanges at both ends and at every corner."""
    path = fillet_path(points, bend, 3)
    parts = [tube(name, path, r, m, res, smooth=False, caps=caps)]
    if flanges:
        pts = [V(p) for p in points]
        for i, p in enumerate(pts):
            if i == 0:
                d = pts[1] - pts[0]
            elif i == len(pts) - 1:
                d = pts[-1] - pts[-2]
            else:
                continue
            q = p - d.normalized() * 0.04 if i == len(pts) - 1 else p + d.normalized() * 0.04
            parts.append(rw.cylinder("flange", r * 1.45, 0.07, 10, tuple(q), z_to_euler(d), mat(flange_mat)))
    return parts


def valve_wheel(loc, normal=(0, -1, 0), r=0.2, m="PaintRed", spokes=4, stem=0.12):
    n = V(normal).normalized()
    c = V(loc)
    parts = [ring("vwheel", r, r * 0.2, tuple(c), tuple(n), m, 12, 5)]
    for i in range(spokes):
        a = math.pi * i / spokes
        # spoke direction perpendicular to n
        e = n.orthogonal().normalized()
        f = n.cross(e).normalized()
        d = e * math.cos(a) + f * math.sin(a)
        parts.append(rod("vspoke", tuple(c - d * r), tuple(c + d * r), r * 0.08, 5, m))
    parts.append(rw.cylinder("vhub", r * 0.22, r * 0.4, 8, tuple(c), z_to_euler(n), mat("M_Brass")))
    parts.append(rod("vstem", tuple(c), tuple(c - n * stem), r * 0.12, 6, "M_Steel"))
    return parts


def gauge(loc, normal=(0, -1, 0), r=0.15, angle=35.0):
    """Round pressure gauge: brass bezel, cream dial, red needle."""
    n = V(normal).normalized()
    c = V(loc)
    parts = [rw.cylinder("gbody", r, r * 0.5, 16, tuple(c - n * r * 0.2), z_to_euler(n), mat("M_Brass"))]
    parts.append(rw.cylinder("gdial", r * 0.82, 0.02, 16, tuple(c + n * r * 0.06), z_to_euler(n), mat("Dial")))
    parts.append(ring("gbezel", r * 0.9, r * 0.12, tuple(c + n * r * 0.07), tuple(n), "M_Brass", 16, 6))
    e = n.orthogonal().normalized()
    f = n.cross(e).normalized()
    a = math.radians(angle)
    d = (V((0, 0, 1)) - n * n.z).normalized() if abs(n.z) < 0.9 else f
    side = n.cross(d).normalized()
    tip = c + n * r * 0.1 + (d * math.cos(a) + side * math.sin(a)) * r * 0.7
    parts.append(beam("gneedle", tuple(c + n * r * 0.1), tuple(tip), 0.025, 0.012, "Needle", 0.0, up=tuple(n)))
    return parts


def bipyramid(name, r=0.3, h_top=0.6, h_bot=0.4, sides=6, loc=(0, 0, 0), m="M_Crystal", twist=0.0, mid=0.0):
    """Faceted crystal: a prism band of height `mid` with pyramids above and below (flat shaded)."""
    c = V(loc)
    verts = [(c.x, c.y, c.z + mid / 2 + h_top), (c.x, c.y, c.z - mid / 2 - h_bot)]
    for k, zz in enumerate((mid / 2, -mid / 2)):
        for i in range(sides):
            a = 2 * math.pi * i / sides + math.radians(twist)
            verts.append((c.x + r * math.cos(a), c.y + r * math.sin(a), c.z + zz))
    faces = []
    up0 = 2
    lo0 = 2 + sides
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((0, up0 + i, up0 + j)[::-1])
        faces.append((1, lo0 + j, lo0 + i)[::-1])
        if mid > 0:
            faces.append((up0 + i, lo0 + i, lo0 + j, up0 + j))
    o = rw.mesh_from_data(name, verts, faces, mat=mat(m))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    rw.flat_shade(o)
    return o


def wheel(r=0.6, width=0.12, loc=(0, 0, 0), axis=(0, 1, 0), spokes=8, m="M_WoodDark", tyre="Iron", hub="M_Brass", seg=20):
    """Cartwheel: wooden rim with an iron tyre, spokes and a hub; axis = wheel axle direction."""
    parts = []
    rim = rw.lathe("rim", [(r * 0.82, -width / 2), (r * 0.92, -width / 2), (r * 0.92, width / 2), (r * 0.82, width / 2), (r * 0.82, -width / 2)],
                   seg, (0, 0, 0), (0, 0, 0), mat(m), None, False, False, 30)
    parts.append(rim)
    tyr = rw.lathe("tyre", [(r * 0.92, -width * 0.55), (r, -width * 0.45), (r, width * 0.45), (r * 0.92, width * 0.55), (r * 0.92, -width * 0.55)],
                   seg, (0, 0, 0), (0, 0, 0), mat(tyre), None, False, False, 30)
    parts.append(tyr)
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        p1 = V((r * 0.85 * math.cos(a), r * 0.85 * math.sin(a), 0))
        parts.append(beam("spoke", (0, 0, 0), tuple(p1), 0.07 * r / 0.6, 0.05 * r / 0.6, m, 0.0, up=(0, 0, 1)))
    parts.append(rw.cylinder("hub", r * 0.2, width * 1.5, 10, (0, 0, 0), (0, 0, 0), mat(hub)))
    parts.append(rw.cylinder("hubcap", r * 0.11, width * 1.9, 8, (0, 0, 0), (0, 0, 0), mat("Iron")))
    place(parts, loc, z_to_euler(axis))
    return parts


def cloth(name, w, h, loc=(0, 0, 0), wave=0.05, waves=1.5, tail=0.0, m="M_Fabric__2a6fdb", t=0.025, nu=8, nv=8,
          sway=0.0, normal_rot=0.0):
    """Hanging banner hanging from its top edge at loc (centre of the top edge), facing -Y. `tail` cuts a
    swallowtail notch of that depth into the bottom edge; `sway` bends the lower part forwards."""
    def P(u, v):
        x = (u - 0.5) * w
        depth = h
        if tail > 0:
            depth = h - tail * (1 - abs(2 * u - 1))
        z = -v * depth
        y = wave * math.sin((u * waves + v * 0.6) * 2 * math.pi) * (0.3 + 0.7 * v) - sway * v * v
        return (x, y, z)
    o = sheet(name, P, nu, nv, m)
    solidify(o, t, 0.0)
    rw.smooth(o, 50)
    place([o], loc, (0, 0, normal_rot))
    return o


def ring_point(C, r, theta_deg, z=0.0):
    """Point at radius r and angle theta (degrees, measured from +Y towards +X) around centre C (x, y)."""
    a = math.radians(theta_deg)
    return (C[0] + r * math.sin(a), C[1] + r * math.cos(a), z)


def arc_block(name, C, r0, r1, th0, th1, z0, z1, nu=2, m="M_Stone"):
    """Curved block between radii r0..r1, angles th0..th1 (degrees, from +Y towards +X), heights z0..z1,
    around the vertical axis through C. nu = number of chord facets."""
    def P(u, v, s):
        th = lerp(th0, th1, u)
        r = r0 if s == 0 else r1
        return ring_point(C, r, th, lerp(z0, z1, v))
    return param_slab(name, P, nu, 1, m)


def ring_place(objs, C, theta_deg):
    """Rotate objects built at theta = 0 (facing -Y towards C) to angle theta around C."""
    return place(objs, (0, 0, 0), (0, 0, -theta_deg), pivot=(C[0], C[1], 0))


def stone(name, size, loc, rot=(0, 0, 0), m="M_Stone", b=0.06, seed=0, jitter=0.0):
    """Chunky chamfered stone block with optional random rotation jitter (degrees)."""
    rnd = random.Random(seed)
    rr = (rot[0] + rnd.uniform(-jitter, jitter), rot[1] + rnd.uniform(-jitter, jitter), rot[2] + rnd.uniform(-jitter, jitter))
    return cbox(name, size, loc, rr, m, b, 1)


def pebble(name, r, loc, m="M_StoneRough", seed=0, squash=0.7):
    rnd = random.Random(seed)
    return rw.ico(name, r, 1, loc, (rnd.uniform(0, 60), rnd.uniform(0, 60), rnd.uniform(0, 90)),
                  (1.0 + rnd.uniform(-0.2, 0.2), 1.0 + rnd.uniform(-0.2, 0.2), squash), mat(m), None, 0)


def moss(loc, r=0.25, seed=0, n=3, squash=0.35):
    rnd = random.Random(seed)
    c = V(loc)
    out = []
    for i in range(n):
        p = c + V((rnd.uniform(-r, r) * 0.6, rnd.uniform(-r, r) * 0.6, 0))
        out.append(rw.ico("moss", r * rnd.uniform(0.5, 0.8), 1, tuple(p), (0, 0, rnd.uniform(0, 90)), (1.2, 1.0, squash), M("Moss"), None, 40))
    return out
