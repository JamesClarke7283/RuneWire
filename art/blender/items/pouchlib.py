"""pouchlib: shared helpers for the pouch items (inventory expanders, item_pouch_*) and the crafted
consumables added with them (greater potions, brews, salves, bombs, jars...) in art/blender/items/.

Import from an item generator script:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pouchlib as pk
    il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V

Builds on rwlib, partlib and itemlib (none of them is edited). Conventions follow art/ASSET_SPEC.md: metres,
+Z up, the front faces -Y, user-facing angles in degrees. Scripts end with il.finish_item(asset, expect)
(origin at the bounding-box centre, rw.finish with icon=True).

Main helpers
* mat(name)          accent materials: pouchlib's ACC table first, then itemlib's ACCENTS; "M_*" names pass
                     through. Tinted library names (M_Leather__rrggbb) get a game-accurate preview colour
                     (lib_tint: texture average x tint, as Godot renders them). Never put leaf/leaves/grass/
                     flower/petal in a flat material name: Godot's material_library makes those wind-swaying foliage.
* Surface(obj), surface_of(objs)   BVH shrink-wrap: hit(origin, dir) / nearest(p) -> (point, smooth normal).
* proj_plane / proj_cyl_x / proj_cyl_z / proj_radial / proj_dirs   map 2D coordinates to rays aimed at a Surface.
* surf_slab()        thick sheet (flap, patch, plate, label) hugging a Surface through a projection.
* surf_prism()       extruded 2D outline (emblem, star) laid onto a Surface.
* surf_marks()       small boxes (stitches) spaced along a 2D path on a Surface.
* surf_strap(), strap()   flat straps along a path (on a Surface, or free with an 'up' function).
* surf_point(), surf_frame()   a point + normal (+ tangents) on a Surface, to stand rivets, studs and buckles on.
* Sack               lumpy drawstring sack (lathe + neck pleats, lumps, a scalloped ruffle) with a dark mouth;
                     neck_ellipse() fits a drawstring round its neck.
* FlapPouch          pouch body (superellipsoid + taper / bulge / round bottom) with flap(), flap_edge() and
                     tongue_edge() / u_edge() flap outlines.
* checker()          basket-weave checker of a second material on a pouchlib.superellipsoid body.
* buckle(), corner_cap(), wrap_cap()   brass hardware.
* loop_tube(), ellipse_loop(), tassel(), knot()   drawstrings, rims, hoops and their ends.
* vial()             little corked potion vial (one object) aimed along any axis.
* wrap_prism_fine()  itemlib.wrap_prism with a well-shaped (CDT) cap: use it for bigger decals bent over curves.
* deform(), transform(), rot()   world-space mesh edits.
* fit()              uniform scale so the largest dimension matches the brief ('about X m').
* tri_report()       debug: triangles per part.
* 2D outlines:       clover_leaves(), leaf_shape_pts(), cloud_pts(), drop_pts(), gear_pts(), rounded_poly(),
                     squircle_outline(), rounded_rect_pts(), spiral_pts().

Preview glows: AgX washes strong emission toward white in the QA renders and icons, losing the hue that makes
a violet rune or a teal ley line readable. Importing pouchlib wraps rw.render_view (at runtime; rwlib.py is not
edited) so the glow materials created through pouchlib (ACC glows and pk.glow) are clamped to
PREVIEW_GLOW_MAX only while a preview or icon renders. The .blend and the exported .glb keep the full strength.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V

# --------------------------------------------------------------------------------------
# Accent materials (library M_* materials are used for anything that gets a texture in game)
# --------------------------------------------------------------------------------------

ACC = {
    # name: ("flat", colour, roughness, metallic) or ("glow", colour, strength)
    "SackThread": ("flat", "4a2c1e", 0.9, 0.0),       # dark-brown cartoon stitches
    "PaleThread": ("flat", "f3e6c4", 0.9, 0.0),       # cream stitches on dark leather
    "Cord": ("flat", "8a5a34", 0.9, 0.0),             # brown drawstring
    "Silver": ("flat", "dfe6ee", 0.25, 1.0),
    "SilverDark": ("flat", "8e9aab", 0.3, 1.0),
    "Bone": ("flat", "efe3c4", 0.6, 0.0),
    "GoldThread": ("flat", "ffcf4a", 0.45, 0.0),      # embroidery (non-metallic so it stays bright)
    "Ore": ("flat", "6b6560", 0.9, 0.0),
    "Nugget": ("flat", "ffcf40", 0.3, 1.0),
    "MagnetRed": ("flat", "d8283a", 0.45, 0.0),
    "OilDrop": ("flat", "3a2410", 0.15, 0.0),
    "OilAmber": ("flat", "c97a12", 0.15, 0.0),
    "Foam": ("flat", "fff1d6", 0.8, 0.0),
    "FoamShade": ("flat", "ffd9a3", 0.8, 0.0),
    "WoodHandle": ("flat", "9c6b3e", 0.8, 0.0),
    "Charcoal": ("flat", "2b2530", 0.9, 0.0),
    "Ice": ("flat", "bfeaff", 0.2, 0.0),
    "IceDeep": ("flat", "6fc3f2", 0.25, 0.0),
    "Snow": ("flat", "f4fbff", 0.5, 0.0),
    "FrostFuse": ("flat", "d9eef8", 0.7, 0.0),          # frozen fuse cord
    "Clover": ("flat", "2f9e3e", 0.6, 0.0),
    "CloverLight": ("flat", "5cc95a", 0.6, 0.0),
    "SalveGreen": ("flat", "62c25a", 0.35, 0.0),
    "SalveLight": ("flat", "a5e88c", 0.35, 0.0),
    "SignalOrange": ("flat", "f0742a", 0.5, 0.2),
    "Feather": ("flat", "fbfbff", 0.7, 0.0),
    "FeatherShade": ("flat", "d6e4f2", 0.7, 0.0),
    "Cloud": ("flat", "ffffff", 0.6, 0.0),
    "SkyString": ("flat", "4d8fd6", 0.8, 0.0),
    # glows
    "RuneViolet": ("glow", "a066ff", 2.4),
    "VoidViolet": ("glow", "a066ff", 2.2),
    "VoidDeep": ("glow", "3a1470", 0.6),
    "StarWhite": ("glow", "f2e8ff", 2.5),
    "LeyTeal": ("glow", "39d5c4", 2.4),
    "ShockCyan": ("glow", "00c8ff", 3.0),
    "ShockCore": ("glow", "e9ffff", 3.0),
    "FrostGlow": ("glow", "1f9dff", 2.2),
    "IncenseViolet": ("glow", "a066ff", 2.0),
    "EmberRed": ("glow", "ff5a1f", 1.5),
}


# Average colour (sRGB) of the library albedo textures. In Godot a tinted library material renders as
# tint x texture (shaders/toon_core.gdshaderinc), so a tinted leather is always darker than the plain leather
# texture, while the near-white fabric weave shows its tint almost as-is.
TEX_AVG = {"M_Fabric": "dbdbdb", "M_Leather": "754a2d", "M_Brass": "c49a47", "M_Steel": "acb3bb",
           "M_WoodPlanks": "a57340", "M_WoodDark": "573622"}


def lib_tint(full):
    """Tinted library material 'M_<Name>__rrggbb' whose Blender preview colour is what Godot will render
    (texture average x tint) instead of rwlib's 25/75 blend, so icons and previews match the game.
    Godot replaces M_* materials by name, so only the previews change."""
    base, tint = full.split("__", 1)
    m = rw.lib(base, tint)
    avg = TEX_AVG.get(base)
    if avg and not m.get("pk_tinted"):
        a, t = rw._lin(avg), rw._lin(tint)
        col = (a[0] * t[0], a[1] * t[1], a[2] * t[2], 1.0)
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = col
        m.diffuse_color = col[:3] + (m.diffuse_color[3],)
        m["pk_tinted"] = True
    return m


PREVIEW_GLOW_MAX = 0.6
_GLOWS = set()


def mat(m):
    """Resolve a material spec: pouchlib ACC names, then itemlib ACCENTS; tinted library names 'M_X__rrggbb'
    get a game-accurate preview colour (lib_tint); Material objects and plain 'M_*' names pass through."""
    if m is None or isinstance(m, bpy.types.Material):
        return m
    if isinstance(m, str) and m.startswith("M_") and "__" in m:
        return lib_tint(m)
    if m in ACC:
        k = ACC[m]
        if k[0] == "glow":
            _GLOWS.add(m)
            return rw.glow(m, k[1], k[2])
        return rw.flat(m, k[1], k[2], k[3])
    return il.mat(m)


def flat(name, color, roughness=0.6, metallic=0.0):
    return rw.flat(name, color, roughness, metallic)


def glow(name, color, strength=2.0):
    _GLOWS.add(name)
    return rw.glow(name, color, strength)


_orig_render_view = rw.render_view


def _render_view_preview_glows(*args, **kwargs):
    saved = []
    for name in _GLOWS:
        m = bpy.data.materials.get(name)
        b = m.node_tree.nodes.get("Principled BSDF") if m is not None and m.node_tree else None
        if b is None:
            continue
        s = b.inputs["Emission Strength"].default_value
        if s > PREVIEW_GLOW_MAX:
            saved.append((b, s))
            b.inputs["Emission Strength"].default_value = PREVIEW_GLOW_MAX
    try:
        return _orig_render_view(*args, **kwargs)
    finally:
        for b, s in saved:
            b.inputs["Emission Strength"].default_value = s


if not getattr(rw.render_view, "_pk_wrapped", False):
    _render_view_preview_glows._pk_wrapped = True
    rw.render_view = _render_view_preview_glows


# --------------------------------------------------------------------------------------
# Small maths
# --------------------------------------------------------------------------------------

def bell(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


def smoothstep(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def scallop(x):
    """Periodic wave in [-1, 1] with rounded crests and creased valleys (period 2 pi)."""
    return 2.0 * abs(math.cos(x / 2.0)) - 1.0


def deform(o, fn):
    """Move every vertex through fn(world Vector) -> world Vector (modifiers are applied first)."""
    rw.apply_modifiers(o)
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    inv = mw.inverted()
    for v in o.data.vertices:
        v.co = inv @ V(fn(mw @ v.co))
    o.data.update()
    return o


def transform(o, M):
    """Apply a 4x4 world-space matrix to an object's mesh (the object keeps its location)."""
    rw.apply_modifiers(o)
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.data.transform(mw.inverted() @ M @ mw)
    o.data.update()
    return o


def rot(axis, deg, center=(0, 0, 0)):
    """World-space rotation matrix about an axis through `center`."""
    c = V(center)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, V(axis).normalized()) @ \
        Matrix.Translation(-c)


def _bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-16:
        return (1 / 3, 1 / 3, 1 / 3)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return (1 - v - w, v, w)


# --------------------------------------------------------------------------------------
# Shrink-wrapping onto surfaces
# --------------------------------------------------------------------------------------

class Surface:
    """BVH of an object's evaluated mesh in world space. hit() returns the first surface point along a ray
    and the smooth (vertex-interpolated) normal there; rays that miss fall back to the nearest surface point
    to the ray, so sheets that run off a rounded edge stay glued to it."""

    def __init__(self, obj):
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()
        bm.from_object(obj, dg)
        bm.transform(obj.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.normal_update()
        bm.faces.ensure_lookup_table()
        self.bm = bm
        self.tree = BVHTree.FromBMesh(bm)

    def _smooth_normal(self, loc, idx, nrm):
        f = self.bm.faces[idx]
        vs = f.verts
        w = _bary(loc, vs[0].co, vs[1].co, vs[2].co)
        n = vs[0].normal * w[0] + vs[1].normal * w[1] + vs[2].normal * w[2]
        if n.length < 1e-6 or n.normalized().dot(nrm) < 0.3:
            return V(nrm).normalized()
        return n.normalized()

    def hit(self, origin, direction, reach=2.0):
        o = V(origin)
        d = V(direction).normalized()
        loc, nrm, idx, _ = self.tree.ray_cast(o, d)
        if loc is None:
            best = None
            for k in range(41):
                q = o + d * (reach * k / 40)
                r = self.tree.find_nearest(q)
                if r[0] is not None and (best is None or r[3] < best[3]):
                    best = r
            loc, nrm, idx, _ = best
        return V(loc), self._smooth_normal(V(loc), idx, V(nrm))

    def nearest(self, p):
        loc, nrm, idx, _ = self.tree.find_nearest(V(p))
        return V(loc), self._smooth_normal(V(loc), idx, V(nrm))


def proj_plane(center, normal, up=(0, 0, 1), dist=1.0):
    """Orthographic projection along -normal: (x, y) -> ray from center + u*x + v*y + normal*dist.
    u is 'right' and v is 'up' as seen from outside (looking against the normal)."""
    c = V(center)
    n = V(normal).normalized()
    u = V(up).cross(n)
    if u.length < 1e-6:
        u = V((0, 1, 0)).cross(n)
    u.normalize()
    v = n.cross(u).normalized()

    def P(x, y):
        return c + u * x + v * y + n * dist, -n
    P.axes = (u, v, n)
    return P


def proj_cyl_x(center, dist=1.0):
    """(x, a): x along +X from center, a in degrees around the X axis: 0 = from above (+Z), 90 = from the
    front (-Y), -90 = from the back (+Y). Rays are aimed at the axis through center."""
    c = V(center)

    def P(x, a):
        t = math.radians(a)
        d = V((0.0, -math.sin(t), math.cos(t)))
        return c + V((x, 0.0, 0.0)) + d * dist, -d
    return P


def proj_cyl_z(center, dist=1.0):
    """(a, z): a = azimuth in degrees (0 = from the front -Y, 90 = from +X), z = height above center.
    Rays are horizontal and aimed at the vertical axis through center."""
    c = V(center)

    def P(a, z):
        t = math.radians(a)
        d = V((math.sin(t), -math.cos(t), 0.0))
        return c + V((0.0, 0.0, z)) + d * dist, -d
    return P


def proj_radial(center, dist=1.0):
    """(az, el) in degrees: rays aimed at `center` from azimuth az (0 = front -Y, 90 = +X), elevation el."""
    c = V(center)

    def P(az, el):
        a, e = math.radians(az), math.radians(el)
        d = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        return c + d * dist, -d
    return P


def surf_point(surf, proj, a, b):
    o, d = proj(a, b)
    return surf.hit(o, d)


def surf_slab(name, surf, proj, uvmap, nu, nv, off=0.001, thick=0.005, m=None, merge=False):
    """Thick sheet hugging `surf`: uvmap(u, v) (u, v in [0, 1]) -> 2D projection coordinates; the sheet's
    inner face sits `off` above the surface and the outer face `off + thick` above it. merge=True welds
    coincident vertices (for uvmaps that clamp rows together)."""
    cache = {}

    def P(u, v, s):
        key = (round(u, 6), round(v, 6))
        if key not in cache:
            a, b = uvmap(u, v)
            cache[key] = surf_point(surf, proj, a, b)
        p, n = cache[key]
        return tuple(p + n * (off + s * thick))
    o = il.param_slab(name, P, nu, nv, mat(m))
    if merge:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-6)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    return o


def rect_map(x0, x1, y0, y1):
    """uvmap for a plain rectangle in projection coordinates."""
    return lambda u, v: (x0 + (x1 - x0) * u, y0 + (y1 - y0) * v)


def squircle_map(w, h, p=5.0, cx=0.0, cy=0.0, angle=0.0):
    """uvmap for a rounded rectangle w x h (superellipse power p; p = 2 gives an ellipse), centred on
    (cx, cy) and turned by `angle` degrees."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def f(u, v):
        x, y = il.squircle(u, v, w, h, p)
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    return f


def _resample_edges(pts, max_edge, closed=True):
    out = []
    n = len(pts)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        a = V((pts[i][0], pts[i][1], 0.0))
        b = V((pts[(i + 1) % n][0], pts[(i + 1) % n][1], 0.0))
        k = max(1, int(math.ceil((b - a).length / max_edge)))
        for j in range(k):
            q = a.lerp(b, j / k)
            out.append((q.x, q.y))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def surf_prism(name, pts2d, surf, proj, off=0.001, thick=0.004, m=None, max_edge=None, smooth_angle=30,
               scale=1.0, center=(0.0, 0.0), angle=0.0):
    """Extruded 2D outline (any simple polygon; concave is fine) laid onto `surf` through `proj`.
    The outline is given around (0, 0); it is scaled, turned by `angle` degrees and moved to `center`
    (projection coordinates). max_edge resamples long outline edges so the prism follows curvature better."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    pts = [(center[0] + scale * (x * ca - y * sa), center[1] + scale * (x * sa + y * ca)) for (x, y) in pts2d]
    pts = il.ccw(pts)
    if max_edge:
        pts = _resample_edges(pts, max_edge)
    hits = [surf_point(surf, proj, x, y) for (x, y) in pts]
    tris = geometry.tessellate_polygon([[V((x, y, 0.0)) for (x, y) in pts]])
    bm = bmesh.new()
    bot = [bm.verts.new(tuple(p + n * off)) for (p, n) in hits]
    top = [bm.verts.new(tuple(p + n * (off + thick))) for (p, n) in hits]
    for (a, b, c) in tris:
        for ring, order in ((top, (a, b, c)), (bot, (c, b, a))):
            try:
                bm.faces.new([ring[i] for i in order])
            except ValueError:
                pass
    k = len(pts)
    for i in range(k):
        j = (i + 1) % k
        try:
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)


def resample2d(pts, n, closed=False, start=0.5):
    """n points evenly spaced by arc length along a 2D polyline, each with its unit tangent.
    `start` (0..1) shifts the first sample by that fraction of the spacing."""
    P = [V((x, y)) for (x, y) in pts]
    if closed:
        P = P + [P[0]]
    seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]
    L = sum(seg)
    out = []
    step = L / n if closed else L / max(n - (0 if start else 1), 1)
    for k in range(n):
        s = (k + start) * step if (closed or start) else k * step
        s = min(s, L - 1e-9)
        acc = 0.0
        for i, l in enumerate(seg):
            if acc + l >= s or i == len(seg) - 1:
                t = (s - acc) / l if l > 1e-12 else 0.0
                p = P[i].lerp(P[i + 1], t)
                tan = (P[i + 1] - P[i]).normalized()
                out.append((p, tan))
                break
            acc += l
    return out


def surf_marks(name, surf, proj, path2d, n, size, m=None, across=False, closed=False, start=0.5, sink=0.3,
               tilt=0.0, eps=None):
    """n small boxes of size (length, width, height) spaced along a 2D path (projection coordinates) on
    `surf`. along the path by default; across=True turns them across it (cartoon stitches crossing a seam).
    `sink` = fraction of the height pushed under the surface. tilt (deg) slants every mark."""
    out = []
    for (p2, t2) in resample2d(path2d, n, closed, start):
        e = eps or 0.004
        P, N = surf_point(surf, proj, p2.x, p2.y)
        P2, _ = surf_point(surf, proj, p2.x + t2.x * e, p2.y + t2.y * e)
        T = P2 - P
        T = T - T.dot(N) * N
        if T.length < 1e-9:
            T = N.orthogonal()
        T.normalize()
        X = N.cross(T) if across else T
        if tilt:
            X = Matrix.Rotation(math.radians(tilt), 3, N) @ X
        out.append(pl.obox(name, size, P + N * (size[2] * (0.5 - sink)), X, N, mat(m)))
    return out


def surf_frame(surf, proj, a, b, eps=0.004):
    """(point, normal, tangent_u, tangent_v) on the surface at projection coordinates (a, b): tangents follow
    the projection's first / second coordinate."""
    P, N = surf_point(surf, proj, a, b)
    Pu, _ = surf_point(surf, proj, a + eps, b)
    Pv, _ = surf_point(surf, proj, a, b + eps)
    U = Pu - P
    U = (U - U.dot(N) * N).normalized()
    Vv = N.cross(U).normalized()
    if Vv.dot(Pv - P) < 0:
        Vv = -Vv
    return P, N, U, Vv


# --------------------------------------------------------------------------------------
# Tubes, cords and their ends
# --------------------------------------------------------------------------------------

def loop_tube(name, pts, r, segs=8, m=None, up=(0, 0, 1), smooth_angle=70, scale_xy=(1.0, 1.0)):
    """Closed tube through 3D points (drawstring round a neck, a hoop round a squashed body...).
    The cross-section is oriented with `up` (so a horizontal loop keeps its tube round)."""
    P = [V(p) for p in pts]
    n = len(P)
    bm = bmesh.new()
    rings = []
    upv = V(up).normalized()
    for i in range(n):
        T = (P[(i + 1) % n] - P[i - 1]).normalized()
        N = upv - upv.dot(T) * T
        if N.length < 1e-6:
            N = T.orthogonal()
        N.normalize()
        B = T.cross(N).normalized()
        ring = [bm.verts.new(P[i] + r * (math.cos(2 * math.pi * j / segs) * scale_xy[0] * B +
                                         math.sin(2 * math.pi * j / segs) * scale_xy[1] * N)) for j in range(segs)]
        rings.append(ring)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for j in range(segs):
            jj = (j + 1) % segs
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)


def ellipse_loop(center, rx, ry, n=24, wobble=0.0, waves=0, phase=0.0, z_wave=0.0):
    """Points round a horizontal ellipse (optionally wavy in radius / height)."""
    c = V(center)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        f = 1.0 + (wobble * math.cos(waves * a + phase) if waves else 0.0)
        out.append(c + V((rx * f * math.cos(a), ry * f * math.sin(a),
                          z_wave * math.sin(waves * a + phase) if waves else 0.0)))
    return out


def knot(name, loc, r=0.016, m="Cord", squash=(1.0, 0.85, 0.8), seed=0, segs=10, rings=7):
    """Chunky knot blob (a squashed smooth ball, turned a little by `seed`)."""
    return rw.sphere(name, r, segs, rings, tuple(loc), (0, 0, 17 * seed), tuple(squash), mat(m))


def tassel(name, top, axis=(0, 0, -1), length=0.06, r=0.016, m="Gold", cap_m=None, strands=8, segs=16):
    """Hanging tassel: a ball cap, a collar and a flared skirt of fat strands (fluted lathe). The cap top sits at
    `top` and the tassel hangs along `axis` (default straight down)."""
    L = length
    prof = [(0.0, 0.0), (r * 0.85, 0.0), (r * 1.05, L * 0.06), (r * 1.0, L * 0.22), (r * 0.74, L * 0.55),
            (r * 0.6, L * 0.63), (r * 0.74, L * 0.68), (r * 0.74, L * 0.76), (r * 0.58, L * 0.82), (r * 0.5, L),
            (0.0, L)]
    o = il.lathe(name, prof, (0, 0, 1), (0, 0, 0), segs, mat(m), 50)

    def fl(p):                                    # flute the skirt into fat strands, stronger toward the hem
        rr = math.hypot(p.x, p.y)
        if rr < 1e-6:
            return p
        a = math.atan2(p.y, p.x)
        f = 1.0 + 0.14 * smoothstep(L * 0.6, 0.0, p.z) * math.cos(strands * a)
        return V((p.x * f, p.y * f, p.z))
    deform(o, fl)
    cap_r = r * 0.62
    parts = [o, rw.sphere(name + "_cap", cap_r, 12, 6, (0, 0, L + cap_r * 0.55), mat=mat(cap_m or m))]
    t = rw.join(parts, name, origin=(0, 0, 0))
    up = -V(axis).normalized()
    pl.align(t, up, None)
    t.location = V(top) - up * (L + cap_r * 1.55)
    return t


# --------------------------------------------------------------------------------------
# Sacks
# --------------------------------------------------------------------------------------

class Sack:
    """Lumpy drawstring sack: a lathe of the outer profile (bottom centre -> rim) plus the inner mouth
    (rim -> down inside to the centre), then deformed:
      folds  = (count, amplitude, z_neck, width)      pleats gathered round the neck, fading away from it
      ruffle = (count, amplitude, z_from, z_rim, lift) frilly top flaring above the neck (lift = rim wave height)
      lumps  = [(count, amplitude, phase_deg, z_centre, z_width), ...]   broad lumps on the belly
      squash = front-to-back (Y) scale; lean = sideways slouch of the top (m at the rim)
    The mouth (inward-facing faces above the neck) gets `mouth_m`."""

    def __init__(self, name, outer_ctrl, inner, segs=32, per_seg=3, m=None, mouth_m="PouchShadow",
                 folds=(9, 0.06, 0.2, 0.05), ruffle=(7, 0.1, 0.22, 0.28, 0.008), lumps=(), squash=0.86, lean=0.0,
                 seed=0, fold_jitter=0.35):
        rnd = random.Random(seed)
        prof = il.curve_profile(outer_ctrl, per_seg) + list(inner)
        self.prof = prof
        self.z_top = max(z for (_, z) in prof)
        o = il.lathe(name, prof, (0, 0, 1), (0, 0, 0), segs, mat(m), 60)
        fn, famp, fz, fw = folds
        rn, ramp, rz0, rz1, rlift = ruffle
        fph = [rnd.uniform(-fold_jitter, fold_jitter) for _ in range(64)]
        rph = rnd.uniform(0, 2 * math.pi)
        self.squash = squash
        self.lean = lean
        H = self.z_top

        def f(p):
            r = math.hypot(p.x, p.y)
            if r < 1e-7:
                return V((p.x + lean * (p.z / H) ** 2, p.y * squash, p.z))
            a = math.atan2(p.y, p.x)
            k = 1.0
            for (n, amp, ph, zc, zw) in lumps:
                k += amp * math.cos(n * a + math.radians(ph)) * bell(p.z, zc, zw)
            # neck pleats (a little irregular)
            j = fph[int((a + math.pi) / (2 * math.pi) * fn) % len(fph)]
            k += famp * math.cos(fn * a + j) * bell(p.z, fz, fw)
            # ruffle above the neck: rounded scallops (soft lobes, creased valleys) that also rise and dip
            t = smoothstep(rz0, rz1, p.z)
            sc = scallop(rn * a + rph)
            k += ramp * t * sc
            z = p.z + rlift * t * sc
            x, y = p.x * k, p.y * k * squash
            return V((x + lean * (z / H) ** 2, y, z))
        deform(o, f)
        self.fn = f
        if mouth_m:
            zn = fz

            def inward(c, n):
                cx = c.x - lean * (max(c.z, 0.0) / H) ** 2
                rad = V((cx, c.y / max(squash, 1e-3), 0))
                if rad.length < 1e-6:
                    return n.z > 0.85
                return rad.normalized().dot(V((n.x, n.y, 0))) < -0.05 or (rad.length < 0.03 and n.z > 0.85)
            rw.set_mat_where(o, mat(mouth_m), lambda c, n: c.z > zn and inward(c, n))
        rw.smooth(o, 70)
        self.obj = o
        self.surf = Surface(o)

    def r(self, z):
        return il.prof_radius(self.prof, z)

    def neck_ellipse(self, z, pad=0.0, n=24):
        """(centre, rx, ry): the smallest axis-aligned ellipse round the deformed surface at height z, padded."""
        pts = self.neck_ring(z, 0.0, n)
        c = V((self.lean * (z / self.z_top) ** 2, 0, z))
        rx = max(abs(p.x - c.x) for p in pts) + pad
        ry = max(abs(p.y - c.y) for p in pts) + pad
        return c, rx, ry

    def neck_ring(self, z, pad=0.0, n=28):
        """Points just outside the deformed surface round the sack at height z (for a drawstring)."""
        out = []
        c = V((self.lean * (z / self.z_top) ** 2, 0, z))
        for i in range(n):
            a = 2 * math.pi * i / n
            d = V((math.cos(a), math.sin(a), 0))
            p, nn = self.surf.hit(c + d * 1.0, -d)
            out.append(V((p.x, p.y, z)) + V((d.x, d.y, 0)).normalized() * pad)
        return out


# --------------------------------------------------------------------------------------
# Vials (bandolier, racks)
# --------------------------------------------------------------------------------------

def vial(name, base, axis=(0, 0, 1), h=0.11, r=0.022, liquid="TonicRed", top=None, fill=0.6, cork_m="Cork",
         segs=14, spin=0.0, shine=True, wax=None, cork_segs=None):
    """Little potion vial (one object) standing on `base` and aimed along `axis`: a round-bottomed tube of
    glass filled `fill` of the way with `liquid`, a lip, a cork (optionally sealed with a `wax` cap)."""
    body = [(0.0, 0.0), (r * 0.7, 0.0), (r * 0.98, r * 0.35), (r, r * 1.0), (r, h * 0.72), (r * 0.82, h * 0.8),
            (r * 0.62, h * 0.84), (r * 0.62, h * 0.88)]
    lip = [(r * 0.8, h * 0.9), (r * 0.82, h * 0.93), (r * 0.72, h * 0.945), (0.0, h * 0.945)]
    b = il.Bottle(body, lip, fill=h * 0.72 * fill + r * 0.2, liquid=mat(liquid), top=mat(top or liquid), segs=segs,
                  per_seg=1)
    parts = list(b.parts)
    if shine:
        parts.append(il.wrap_prism("shine", il.capsule_pts(r * 0.45, h * 0.32), b.map(-40, h * 0.42, 0.0012, 0.0012),
                                   "Shine"))
    parts.append(il.cork(h * 0.84, h * 1.08, r * 0.55, r * 0.72, cork_segs or segs, mat(cork_m), 0.3))
    if wax:
        parts.append(il.lathe("wax", [(0.0, h * 1.0), (r * 0.8, h * 1.0), (r * 0.84, h * 1.05), (r * 0.7, h * 1.1),
                                      (0.0, h * 1.11)], segs=cork_segs or segs, m=mat(wax), smooth=50))
    o = rw.join(parts, name, origin=(0, 0, 0))
    pl.align(o, axis, None, spin=spin)
    o.location = V(base)
    return o


# --------------------------------------------------------------------------------------
# 2D outlines (counter-clockwise, centred on 0)
# --------------------------------------------------------------------------------------

def rounded_poly(pts, r, n=4):
    """Round the corners of a convex-ish polygon with arcs of radius r (n points per corner)."""
    P = [V((x, y)) for (x, y) in pts]
    k = len(P)
    out = []
    for i in range(k):
        a, b, c = P[i - 1], P[i], P[(i + 1) % k]
        d1 = (a - b).normalized()
        d2 = (c - b).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        t = r / max(math.tan(ang / 2), 1e-6)
        p1 = b + d1 * t
        p2 = b + d2 * t
        for j in range(n + 1):
            s = j / n
            q = (1 - s) * (1 - s) * p1 + 2 * (1 - s) * s * b + s * s * p2
            out.append((q.x, q.y))
    return il.ccw(out)


def clover_leaves(size):
    """The four heart-shaped leaflets of a four-leaf clover (a list of 4 outlines) with their tips meeting at
    (0, 0), set on the diagonals; `size` ~ overall width."""
    w = size * 0.52
    heart = il.heart_pts(w, 20)                   # lobes up (+y), tip down (-y)
    tip_y = min(y for (_, y) in heart)
    polys = []
    for k in range(4):
        a = math.radians(45 + 90 * k) - math.pi / 2   # turn +y onto the diagonal direction
        ca, sa = math.cos(a), math.sin(a)
        poly = []
        for (x, y) in heart:
            yy = y - tip_y + w * 0.03
            poly.append((x * ca - yy * sa, x * sa + yy * ca))
        polys.append(il.ccw(poly))
    return polys


def leaf_shape_pts(w, h, n=10):
    """Pointed almond leaf shape (vertical, tip up), centred."""
    pts = []
    for i in range(n + 1):
        t = i / n
        y = -h / 2 + h * t
        x = w / 2 * math.sin(math.pi * t) ** 0.8
        pts.append((x, y))
    for i in range(n - 1, 0, -1):
        t = i / n
        y = -h / 2 + h * t
        x = -w / 2 * math.sin(math.pi * t) ** 0.8
        pts.append((x, y))
    return il.ccw(pts)


def cloud_pts(w, h, bumps=((-0.3, 0.0, 0.28), (0.0, 0.18, 0.36), (0.32, 0.02, 0.28)), n=48):
    """Cartoon cloud: the union outline of a few circles (cx, cy, r in units of w) over a flat base."""
    circles = [(cx * w, cy * w, r * w) for (cx, cy, r) in bumps]
    base_y = min(cy - r * 0.6 for (cx, cy, r) in circles)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = V((math.cos(a), math.sin(a)))
        best = 0.0
        for (cx, cy, r) in circles:
            # distance along d from origin to the far side of circle
            c = V((cx, cy))
            b = d.dot(c)
            disc = b * b - (c.dot(c) - r * r)
            if disc >= 0:
                best = max(best, b + math.sqrt(disc))
        p = d * best
        if p.y < base_y:
            p = d * (base_y / d.y) if d.y < -1e-6 else p
        pts.append((p.x, p.y))
    ys = [y for (_, y) in pts]
    cy = (max(ys) + min(ys)) / 2
    sc = h / max(1e-6, (max(ys) - min(ys)))
    return il.ccw([(x, (y - cy) * sc) for (x, y) in pts])


def drop_pts(w, h, n=16):
    """Teardrop (point up), centred on its bbox."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 0.5 * w * math.sin(t) * (1 - 0.5 * (1 + math.cos(t)) / 2) * 1.15
        y = -0.5 * h * math.cos(t)
        pts.append((x, y))
    return il.ccw(pts)


def gear_pts(r_out, r_in, teeth=8):
    """Gear outline (for flat emblems)."""
    pts = []
    for t in range(teeth):
        a0 = 2 * math.pi * t / teeth
        step = 2 * math.pi / teeth
        for (f, rr) in ((0.0, r_in), (0.15, r_in), (0.25, r_out), (0.5, r_out), (0.6, r_in)):
            a = a0 + step * f
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return il.ccw(pts)


def spiral_pts(r0, r1, turns, n=40):
    """Points along an Archimedean spiral (2D), from radius r0 to r1."""
    out = []
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        out.append((r * math.cos(a), r * math.sin(a)))
    return out


def squircle_outline(w, h, p=5.0, n=24, cx=0.0, cy=0.0, angle=0.0, inset=0.0):
    """Closed outline of the rounded rectangle that squircle_map() fills (same superellipse), optionally inset."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = (w / 2 - inset) * math.copysign(abs(c) ** (2 / p), c)
        y = (h / 2 - inset) * math.copysign(abs(s) ** (2 / p), s)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


# --------------------------------------------------------------------------------------
# Straps and flap pouches
# --------------------------------------------------------------------------------------

def strap(name, pts, width, thick, up=(0, 0, 1), m=None, res=4, smooth_path=True, caps=True, taper=None):
    """Flat strap (cross-section width x thick) swept along a 3D path. Its flat face looks along `up`, which
    may be a vector or a function point -> vector (e.g. the normal of the surface it lies on).
    taper = (w0, w1) scales the width from start to end."""
    n = len(pts)
    Q, _ = pl._resample(pts, [1.0] * n, res, smooth_path)
    m_ = len(Q)
    bm = bmesh.new()
    rings = []
    for i in range(m_):
        a = Q[max(i - 1, 0)]
        b = Q[min(i + 1, m_ - 1)]
        T = (b - a).normalized()
        u = V(up(Q[i]) if callable(up) else up)
        N = u - u.dot(T) * T
        if N.length < 1e-6:
            N = T.orthogonal()
        N.normalize()
        B = T.cross(N).normalized()
        w = width
        if taper:
            t = i / max(m_ - 1, 1)
            w = width * (taper[0] + (taper[1] - taper[0]) * t)
        ring = [bm.verts.new(Q[i] + B * (sx * w / 2) + N * (sy * thick / 2))
                for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        rings.append(ring)
    for i in range(m_ - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), 40)


def surf_strap(name, surf, proj, path2d, width, thick, off=0.0005, m=None, res=3, n=None, smooth_path=True,
               caps=True, taper=None):
    """Strap lying on a surface along a 2D path in projection coordinates (resampled to `n` points).
    taper = (w0, w1) scales the width from start to end."""
    if n:
        path2d = [(p.x, p.y) for (p, _) in resample2d(path2d, n, False, 0.0)]
    hits = [surf_point(surf, proj, a, b) for (a, b) in path2d]
    pts = [p + nn * (off + thick / 2) for (p, nn) in hits]
    normals = [nn for (_, nn) in hits]

    def up(q):
        best = min(range(len(pts)), key=lambda i: (pts[i] - q).length)
        return normals[best]
    return strap(name, pts, width, thick, up, m, res, smooth_path, caps, taper)


def superellipsoid(name, size, loc=(0, 0, 0), e_xy=0.35, e_z=0.45, segs=24, rings=14, m=None, smooth_angle=80):
    """partlib.superellipsoid, but each face also remembers its cell in the original UV-sphere grid (face
    attributes 'pk_seg' / 'pk_ring'), so patterns such as a basket weave can be painted per face later."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=1.0, location=(0, 0, 0))
    o = bpy.context.active_object
    me = o.data
    a_seg = me.attributes.new("pk_seg", 'INT', 'FACE')
    a_ring = me.attributes.new("pk_ring", 'INT', 'FACE')
    for f in me.polygons:
        c = f.center
        th = math.atan2(c.y, c.x) % (2 * math.pi)
        ph = math.asin(max(-1.0, min(1.0, c.z / max(c.length, 1e-9))))
        a_seg.data[f.index].value = int(th / (2 * math.pi) * segs) % segs
        a_ring.data[f.index].value = int((ph + math.pi / 2) / math.pi * rings) % rings
    a, b, cc = size[0] / 2, size[1] / 2, size[2] / 2

    def sp(v, e):
        return math.copysign(abs(v) ** e, v)

    for v in me.vertices:
        x, y, z = v.co
        phi = math.asin(max(-1.0, min(1.0, z)))
        th = math.atan2(y, x)
        hs = abs(math.cos(phi)) ** e_z
        v.co = (a * sp(math.cos(th), e_xy) * hs, b * sp(math.sin(th), e_xy) * hs, cc * sp(math.sin(phi), e_z))
    o.name = name
    me.name = name
    o.location = loc
    if m is not None:
        rw.set_mat(o, mat(m))
    rw.smooth(o, smooth_angle)
    return o


def checker(o, m_b, block_seg=1, block_ring=1, phase=0, where=None):
    """Paint every other grid cell (pk_seg / pk_ring face attributes from pouchlib.superellipsoid) with m_b.
    where(face_centre, normal) can limit it (e.g. only below a flap)."""
    me = o.data
    sa, ra = me.attributes.get("pk_seg"), me.attributes.get("pk_ring")
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    faces = []
    for f in me.polygons:
        k = sa.data[f.index].value // block_seg + ra.data[f.index].value // block_ring + phase
        if k % 2 and (where is None or where(mw @ f.center, (nm @ f.normal).normalized())):
            faces.append(f.index)
    return rw.set_mat(o, mat(m_b), faces)


class FlapPouch:
    """Pouch body (rounded box from pl.superellipsoid) standing on z = 0, with helpers to wrap a flap over its
    top and down its front. size = (W, D, H). taper > 0 narrows the top (x); bulge > 0 pushes the front
    and back out in the middle (a stuffed pouch); round_bottom > 0 rounds the lower corners into a U."""

    def __init__(self, name, size, m, e_xy=0.35, e_z=0.5, segs=24, rings=12, taper=0.0, bulge=0.0,
                 round_bottom=0.0, axis_z=0.62):
        W, D, H = size
        self.W, self.D, self.H = W, D, H
        o = superellipsoid(name, size, (0, 0, H / 2), e_xy, e_z, segs, rings, m)

        def f(p):
            t = p.z / H                                   # 0 bottom .. 1 top
            x = p.x * (1.0 - taper * (t - 0.5))
            y = p.y * (1.0 + bulge * math.sin(math.pi * max(0.0, min(1.0, t))) * (1 - (2 * p.x / W) ** 2))
            z = p.z
            if round_bottom:
                k = max(0.0, abs(2 * p.x / W) - 0.35) / 0.65  # 0 in the middle, 1 at the sides
                z = p.z + round_bottom * H * (1 - t) ** 2 * k * k
            return V((x, y, z))
        deform(o, f)
        rw.smooth(o, 80)
        self.body = o
        self.surf = Surface(o)
        self.axis = V((0, 0, H * axis_z))
        self.proj = proj_cyl_x(self.axis)

    @staticmethod
    def u_edge(width, a_mid, a_side, p=2.0):
        """Flap edge: a U (p = 2), V (p = 1) or flatter (p > 2) curve from a_side at the sides to a_mid."""
        hw = width / 2
        return lambda x: a_mid - (a_mid - a_side) * min(1.0, abs(x) / hw) ** p

    @staticmethod
    def tongue_edge(a_side, a_tip, tongue_w, shape=0.8):
        """Flap edge: straight at a_side, dipping into a rounded tongue (half-width tongue_w) down to a_tip."""
        def f(x):
            t = abs(x) / tongue_w
            if t >= 1.0:
                return a_side
            return a_side + (a_tip - a_side) * math.cos(t * math.pi / 2) ** shape
        return f

    def flap(self, name, width, a_back, edge, thick=0.01, m=None, nu=8, nv=10, off=0.0008, x_off=0.0):
        """Flap from angle a_back (behind the top) over the top and down the front to the edge curve
        edge(x) -> angle. Angles are about the pouch's flap axis (0 = straight up, 90 = straight at the
        front, more than 90 = lower on the front). x_off slides the flap sideways."""
        hw = width / 2
        a_max = max(edge(-hw + width * i / 64) for i in range(65))

        def uv(u, v):                             # rows at shared angles, each column clamped at its edge
            x = -hw + width * u
            return (x + x_off, min(a_back + (a_max - a_back) * v, edge(x)))
        self.flap_spec = (width, a_back, edge)
        self.flap_x = x_off
        return surf_slab(name, self.surf, self.proj, uv, nu, nv, off, thick, m, merge=True)

    def flap_edge(self, inset_x=0.012, inset_a=5.0, n=40, a_top=None):
        """2D path (projection coordinates) running just inside the flap's sides and front edge."""
        width, a_back, edge = self.flap_spec
        hw = width / 2 - inset_x
        top = a_top if a_top is not None else 10.0
        pts = []
        side_n = 4
        e0 = edge(-hw) - inset_a
        for i in range(side_n):
            pts.append((-hw, top + (e0 - top) * i / side_n))
        for i in range(n + 1):
            x = -hw + 2 * hw * i / n
            pts.append((x, edge(x) - inset_a))
        e1 = edge(hw) - inset_a
        for i in range(1, side_n + 1):
            pts.append((hw, e1 + (top - e1) * i / side_n))
        return pts

    def flap_tip(self, a_off=0.0, x=0.0):
        """(point, normal) on the body surface at the flap's front edge (at x), a_off degrees above it."""
        width, a_back, edge = self.flap_spec
        return surf_point(self.surf, self.proj, x, edge(x) - a_off)


def surface_of(objs):
    """One Surface over several objects (temporary joined copies; the originals are untouched)."""
    bpy.context.view_layer.update()
    copies = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        copies.append(c)
    j = rw.join(copies, "_surf_tmp", origin=None)
    s = Surface(j)
    me = j.data
    bpy.data.objects.remove(j, do_unlink=True)
    bpy.data.meshes.remove(me)
    return s


def corner_cap(name, surf, corner, normal, size, thick=0.006, m="M_Brass", p=2.6, off=0.0006, nu=5, nv=5):
    """Metal cap wrapped over a rounded corner: a rounded square `size` across, projected along -normal from
    just outside `corner`."""
    proj = proj_plane(corner, normal, (0, 0, 1), 0.5)
    return surf_slab(name, surf, proj, squircle_map(size, size, p), nu, nv, off, thick, m), proj


def rounded_rect_pts(w, h, r, n=3):
    """Closed rounded rectangle outline (w x h, corner radius r), centred on 0, counter-clockwise."""
    pts = []
    for (cx, cy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                         (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def buckle(name, center, normal, along, w, h, r=0.0045, m="M_Brass", bar=True, prong=True):
    """Cartoon strap buckle: a rounded rectangular frame (w across the strap, h along it) standing on a surface,
    with a centre bar and a prong lying along the strap."""
    c = V(center)
    n = V(normal).normalized()
    a = V(along)
    a = (a - a.dot(n) * n).normalized()
    x = a.cross(n).normalized()
    pts = [c + x * px + a * py + n * (r * 0.9) for (px, py) in rounded_rect_pts(w, h, min(w, h) * 0.3, 2)]
    parts = [loop_tube(name, pts, r, 6, m, up=tuple(n))]
    if bar:
        parts.append(pl.rod(name + "_bar", c - x * (w / 2) + n * (r * 0.9), c + x * (w / 2) + n * (r * 0.9), r * 0.8,
                            6, mat(m)))
    if prong:
        parts.append(pl.capsule(name + "_prong", c + n * (r * 1.6), c - a * (h * 0.48) + n * (r * 1.6), r * 0.6, 5, 1,
                                mat(m)))
    return parts


def tri_report(objs, label=""):
    """Debug: print the triangle count of each object (modifiers included), largest first, summed by name."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    acc = {}
    for o in objs:
        if o is None or o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        key = o.name.split(".")[0]
        acc[key] = acc.get(key, 0) + len(me.loop_triangles)
        ev.to_mesh_clear()
    tot = sum(acc.values())
    print("RWTRIS %s total %d: %s" % (label, tot, ", ".join("%s=%d" % kv for kv in sorted(acc.items(), key=lambda kv: -kv[1]))))
    return acc


def proj_dirs(center, normal, up=(0, 0, 1)):
    """Projection from INSIDE a body: (a, b) in degrees tilt `normal` sideways (a) and up (b); the ray starts at
    `center` (a point inside the body) and goes outward, so it always hits the body's skin. Good for caps that
    wrap rounded corners."""
    c = V(center)
    n = V(normal).normalized()
    side = V(up).cross(n)
    if side.length < 1e-6:
        side = n.orthogonal()
    side.normalize()
    upv = n.cross(side).normalized()

    def P(a, b):
        d = Matrix.Rotation(math.radians(b), 3, side) @ (Matrix.Rotation(math.radians(a), 3, upv) @ n)
        return c, d.normalized()
    return P


def wrap_cap(name, surf, inner, normal, size_deg, thick=0.006, m="M_Brass", p=2.4, off=0.0006, nu=5, nv=5):
    """Cap wrapped over a rounded corner of `surf`, cast outward from the interior point `inner` within a rounded
    square of directions size_deg wide around `normal`. Returns (cap, projection)."""
    proj = proj_dirs(inner, normal)
    return surf_slab(name, surf, proj, squircle_map(size_deg, size_deg, p), nu, nv, off, thick, m), proj


# --------------------------------------------------------------------------------------
# Well-shaped decal caps (no long slivers: they shade badly once bent over a curved surface)
# --------------------------------------------------------------------------------------

def _inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-30) + x0:
            c = not c
    return c


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L < 1e-18 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


def fill2d(pts, step):
    """Triangulate a simple 2D polygon with interior points about `step` apart (constrained Delaunay).
    Returns (verts, tris); the first len(outline) verts are the (resampled, counter-clockwise) outline in order."""
    outline = _resample_edges(il.ccw([(float(x), float(y)) for (x, y) in pts]), step)
    n = len(outline)
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    inner = []
    y = min(ys) + step * 0.5
    row = 0
    while y < max(ys):
        x = min(xs) + step * (0.5 + 0.5 * (row % 2))
        while x < max(xs):
            if _inside((x, y), outline) and min(_seg_dist((x, y), outline[i], outline[(i + 1) % n])
                                                for i in range(n)) > step * 0.45:
                inner.append((x, y))
            x += step
        y += step * 0.866
        row += 1
    verts = outline + inner
    coords = [V((x, y)) for (x, y) in verts]
    edges = [(i, (i + 1) % n) for i in range(n)]
    out = geometry.delaunay_2d_cdt(coords, edges, [list(range(n))], 1, 1e-7)
    ov, oe, of, orig_v = out[0], out[1], out[2], out[3]
    # map output verts back to input indices (CDT may reorder); keep only triangles inside the outline
    idx = []
    for k, o in enumerate(orig_v):
        idx.append(o[0] if o else None)
    tris = []
    for f in of:
        if len(f) != 3 or any(idx[i] is None for i in f):
            continue
        a, b, c = (idx[i] for i in f)
        cx = (verts[a][0] + verts[b][0] + verts[c][0]) / 3
        cy = (verts[a][1] + verts[b][1] + verts[c][1]) / 3
        if _inside((cx, cy), outline):
            # counter-clockwise in 2D
            (x0, y0), (x1, y1), (x2, y2) = verts[a], verts[b], verts[c]
            if (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0) < 0:
                b, c = c, b
            tris.append((a, b, c))
    return verts, tris, n


def wrap_prism_fine(name, pts2d, mapper, m=None, step=0.01, smooth_angle=30):
    """itemlib.wrap_prism with a well-shaped cap triangulation (fill2d), for decals bent over curved surfaces."""
    verts, tris, n = fill2d(pts2d, step)
    bm = bmesh.new()
    bot = [bm.verts.new(mapper(x, y, 0.0)) for (x, y) in verts]
    top = [bm.verts.new(mapper(x, y, 1.0)) for (x, y) in verts]
    for (a, b, c) in tris:
        for ring, order in ((top, (a, b, c)), (bot, (c, b, a))):
            try:
                bm.faces.new([ring[i] for i in order])
            except ValueError:
                pass
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)


def fit(o, target):
    """Uniformly scale a (joined) object about its origin so its largest bounding-box dimension is `target` m
    (the briefs give item sizes as 'about X m'). Returns the scale factor."""
    rw.apply_modifiers(o)
    bpy.context.view_layer.update()
    mn, mx = rw.bounds([o])
    s = target / max(mx - mn)
    o.data.transform(Matrix.Scale(s, 4))
    o.data.update()
    bpy.context.view_layer.update()
    return s
