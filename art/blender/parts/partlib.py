"""partlib: shape helpers shared by the Batch A build-part generators (art/blender/parts/*.py).

Built on top of rwlib (which must not be edited). Everything works in world space and metres;
user-facing angles are in degrees. Every helper returns the new Blender object (or a list).

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import partlib as pl
    rw = pl.rw
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rwlib as rw  # noqa: E402

V = Vector


# --------------------------------------------------------------------------------------
# Small object utilities
# --------------------------------------------------------------------------------------

def tint_emission(mat_name, hexcol, strength=None):
    """rwlib's tinted library materials (e.g. M_Crystal__a066ff) keep the library's emission colour.
    Make the emission follow the tint so previews (and the .glb fallback colours) match the intent."""
    m = rw._resolve_mat(mat_name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Emission Color"].default_value = rw._lin(hexcol)
    if strength is not None:
        b.inputs["Emission Strength"].default_value = strength
    return m


def obj_from_bm(name, bm, mat=None, smooth_angle=60, loc=(0, 0, 0)):
    """Turn a bmesh (world-space coordinates relative to `loc`) into a linked mesh object."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if mat is not None:
        rw.set_mat(o, mat)
    if smooth_angle:
        rw.smooth(o, smooth_angle)
    return o


def frame_matrix(z_dir, x_hint=None):
    """3x3 rotation whose local Z maps to z_dir (and local X as close as possible to x_hint)."""
    z = V(z_dir).normalized()
    if x_hint is None:
        q = V((0, 0, 1)).rotation_difference(z)
        return q.to_matrix()
    x = V(x_hint)
    x = (x - x.dot(z) * z)
    if x.length < 1e-6:
        x = z.orthogonal()
    x.normalize()
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def align(o, z_dir=(0, 0, 1), loc=None, x_hint=None, spin=0.0):
    """Rotate o's mesh about its own origin so local +Z points along z_dir; optionally move it."""
    R = frame_matrix(z_dir, x_hint).to_4x4() @ Matrix.Rotation(math.radians(spin), 4, 'Z')
    o.data.transform(R)
    o.data.update()
    if loc is not None:
        o.location = loc
    return o


def xform(o, M):
    """Apply a 4x4 matrix to the mesh data (about the object's origin)."""
    o.data.transform(M)
    o.data.update()
    return o


def parent_keep(child, parent):
    """rw.set_parent, but evaluates the depsgraph first so freshly created/moved objects (whose
    matrix_world is not computed yet) keep their intended world position."""
    bpy.context.view_layer.update()
    rw.set_parent(child, parent)
    bpy.context.view_layer.update()
    return child


def empty_at(name, loc, parent=None, size=0.1):
    """Attachment empty at a world-space location, optionally parented (keeping that location)."""
    e = rw.empty(name, loc, None, size)
    if parent is not None:
        parent_keep(e, parent)
    return e


def mirror_copy(o, axis='X', name=None):
    """Mirrored duplicate across the world plane through the origin (axis 'X' mirrors x -> -x)."""
    n = rw.duplicate(o, name or o.name + "_m")
    i = 'XYZ'.index(axis)
    s = [1, 1, 1]
    s[i] = -1
    n.data.transform(Matrix.Diagonal((s[0], s[1], s[2], 1.0)))
    n.data.flip_normals()
    loc = list(n.location)
    loc[i] = -loc[i]
    n.location = loc
    return n


def obox(name, size, loc=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, 0, 1), mat=None, bevel=0.0, bevel_segments=1,
         rounded=0.0, segments=2):
    """Box of `size` (local X, Y, Z) whose local X/Z axes point along x_dir / z_dir."""
    if rounded > 0:
        o = rw.rounded_box(name, size, rounded, mat=mat, segments=segments)
    else:
        o = rw.box(name, size, mat=mat, bevel=bevel, bevel_segments=bevel_segments)
    o.data.transform(frame_matrix(z_dir, x_dir).to_4x4())
    o.location = loc
    return o


def beam_between(name, a, b, size_yz, mat=None, rounded=0.0, bevel=0.0, segments=2, up=(0, 0, 1)):
    """Box running from point a to point b (cross-section size_yz = (width, height))."""
    a, b = V(a), V(b)
    d = b - a
    z_dir = V(up)
    o = obox(name, (d.length, size_yz[0], size_yz[1]), (a + b) / 2, d, _perp(d, z_dir), mat, bevel, 1, rounded,
             segments)
    return o


def _perp(d, up):
    d = V(d).normalized()
    up = V(up)
    p = up - up.dot(d) * d
    if p.length < 1e-6:
        p = d.orthogonal()
    return p.normalized()


# --------------------------------------------------------------------------------------
# Swept tubes with rounded caps (fingers, pipes, coils, handles, glyph strokes)
# --------------------------------------------------------------------------------------

def _resample(pts, radii, res, smooth):
    P = [V(p) for p in pts]
    n = len(P)
    out_p, out_r = [], []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else 2 * P[0] - P[1]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < n else 2 * P[-1] - P[-2]
        steps = res if smooth else 1
        for k in range(steps):
            t = k / steps
            if smooth:
                t2, t3 = t * t, t * t * t
                q = 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                           (3 * p1 - p0 - 3 * p2 + p3) * t3)
            else:
                q = p1.lerp(p2, t)
            out_p.append(q)
            out_r.append(radii[i] + (radii[i + 1] - radii[i]) * t)
    out_p.append(P[-1])
    out_r.append(radii[-1])
    return out_p, out_r


def sausage(name, pts, radius, segs=12, res=6, mat=None, caps=(True, True), cap_rings=3, smooth_path=True,
            smooth_angle=80, scale_xy=(1.0, 1.0), up_hint=None):
    """Tube swept along a Catmull-Rom path through `pts`, with hemispherical end caps.
    `radius` is a float or a per-point list. caps=(start, end): True = round cap, False = flat cap,
    None = open. scale_xy squashes the cross-section (local N, B axes) for oval tubes."""
    n = len(pts)
    radii = list(radius) if isinstance(radius, (list, tuple)) else [radius] * n
    Q, Rr = _resample(pts, radii, res, smooth_path)
    m = len(Q)
    T = []
    for i in range(m):
        a = Q[max(i - 1, 0)]
        b = Q[min(i + 1, m - 1)]
        T.append((b - a).normalized())
    if up_hint is not None:
        N = _perp(T[0], up_hint)
    else:
        N = T[0].orthogonal().normalized()
    bm = bmesh.new()
    rings = []
    sx, sy = scale_xy
    for i in range(m):
        if i > 0:
            q = T[i - 1].rotation_difference(T[i])
            N = q @ N
            N = (N - N.dot(T[i]) * T[i]).normalized()
        B = T[i].cross(N).normalized()
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            ring.append(bm.verts.new(Q[i] + Rr[i] * (math.cos(a) * sx * N + math.sin(a) * sy * B)))
        rings.append((ring, N.copy(), B.copy()))
    for i in range(m - 1):
        a, b = rings[i][0], rings[i + 1][0]
        for j in range(segs):
            jj = (j + 1) % segs
            bm.faces.new((a[j], a[jj], b[jj], b[j]))

    def cap(idx, d, kind):
        ring, N_, B_ = rings[idx]
        if kind is None:
            return
        if not kind:
            bm.faces.new(ring)
            return
        c = Q[idx]
        r = Rr[idx]
        prev = ring
        for k in range(1, cap_rings):
            phi = (math.pi / 2) * k / cap_rings
            cc = c + d * (r * math.sin(phi))
            rr = r * math.cos(phi)
            nr = [bm.verts.new(cc + rr * (math.cos(2 * math.pi * j / segs) * sx * N_ +
                                          math.sin(2 * math.pi * j / segs) * sy * B_)) for j in range(segs)]
            for j in range(segs):
                jj = (j + 1) % segs
                bm.faces.new((prev[j], prev[jj], nr[jj], nr[j]))
            prev = nr
        pole = bm.verts.new(c + d * r)
        for j in range(segs):
            jj = (j + 1) % segs
            bm.faces.new((prev[j], prev[jj], pole))

    cap(0, -T[0], caps[0])
    cap(m - 1, T[-1], caps[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, mat, smooth_angle)


def capsule(name, a, b, r, segs=8, cap_rings=2, mat=None, smooth_angle=80):
    return sausage(name, [a, b], r, segs, 1, mat, (True, True), cap_rings, False, smooth_angle)


def rod(name, a, b, r, segs=12, mat=None, smooth_angle=50):
    """Straight cylinder between two points with flat caps."""
    return sausage(name, [a, b], r, segs, 1, mat, (False, False), 1, False, smooth_angle)


def helix(name, radius, wire_r, turns, height, base=(0, 0, 0), axis=(0, 0, 1), pts_per_turn=16, segs=8, mat=None,
          phase=0.0, end_caps=(True, True), res=2):
    """Coil spring / wound wire along `axis`, starting at `base`."""
    pts = []
    n = int(turns * pts_per_turn) + 1
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(phase) + 2 * math.pi * turns * t
        pts.append((radius * math.cos(a), radius * math.sin(a), height * t))
    o = sausage(name, pts, wire_r, segs, res, mat, end_caps, 2, True, 80)
    align(o, axis, base)
    return o


# --------------------------------------------------------------------------------------
# Lathed shapes along any axis
# --------------------------------------------------------------------------------------

def lathe_axis(name, profile, axis=(0, 0, 1), loc=(0, 0, 0), segments=32, mat=None, cap_bottom=True, cap_top=True,
               smooth_angle=50, spin=0.0):
    """rw.lathe (profile [(radius, h), ...] bottom->top along local Z) then aimed along `axis`."""
    o = rw.lathe(name, profile, segments, mat=mat, cap_bottom=cap_bottom, cap_top=cap_top,
                 smooth_angle=smooth_angle)
    align(o, axis, loc, spin=spin)
    return o


def band(name, r_out, width, thick, axis=(0, 0, 1), loc=(0, 0, 0), mat=None, segs=32, round_=0.4, smooth_angle=50):
    """Flat hoop / ferrule: ring with a rectangular, softly rounded cross-section (centred on loc)."""
    r_in = r_out - thick
    b = min(width, thick) * round_
    if round_ <= 0:
        # plain rectangular section (cheaper: 4 quads per segment)
        prof = [(r_in, -width / 2), (r_out, -width / 2), (r_out, width / 2), (r_in, width / 2), (r_in, -width / 2)]
        return lathe_axis(name, prof, axis, loc, segs, mat, False, False, smooth_angle)
    prof = [(r_in, -width / 2), (r_out - b, -width / 2), (r_out, -width / 2 + b), (r_out, width / 2 - b),
            (r_out - b, width / 2), (r_in, width / 2), (r_in, -width / 2)]
    return lathe_axis(name, prof, axis, loc, segs, mat, False, False, smooth_angle)


def disc(name, r, thick, axis=(0, 0, 1), loc=(0, 0, 0), mat=None, segs=32, bevel=0.3, smooth_angle=50):
    """Solid round slab with rounded rim, centred on loc."""
    b = min(r, thick) * bevel
    prof = [(0.0, -thick / 2), (r - b, -thick / 2), (r, -thick / 2 + b), (r, thick / 2 - b), (r - b, thick / 2),
            (0.0, thick / 2)]
    return lathe_axis(name, prof, axis, loc, segs, mat, False, False, smooth_angle)


# --------------------------------------------------------------------------------------
# Fasteners
# --------------------------------------------------------------------------------------

def rivet(loc, normal=(0, 0, 1), r=0.018, h=0.01, mat="M_Brass", segs=8, name="rivet", sink=0.5):
    """Dome rivet head standing on a surface with the given outward normal (top at loc + normal*h)."""
    prof = [(r, -h * sink), (r, 0.0), (r * 0.72, h * 0.78), (0.0, h)]
    return lathe_axis(name, prof, normal, loc, segs, mat, False, True, 70)


def bolt(loc, normal=(0, 0, 1), r=0.025, h=0.016, mat="M_Steel", name="bolt", washer=True, spin=0.0, bevel=True):
    """Hex bolt head (with a round washer) standing on a surface; top at loc + normal*(h + washer)."""
    parts = []
    wh = h * 0.3 if washer else 0.0
    if washer:
        parts.append(rw.cylinder(name + "_w", r * 1.35, wh * 2, 10, (0, 0, 0), mat=mat))
    # hex head from z = wh * 0.5 (sunk into the washer) up to z = wh + h
    hexo = rw.cylinder(name, r, h + wh * 0.5, 6, (0, 0, (wh * 0.5 + wh + h) / 2), mat=mat)
    if bevel:
        rw.add_bevel(hexo, min(0.004, r * 0.15), 1, 30)
    parts.append(hexo)
    o = rw.join(parts, name, origin=(0, 0, 0)) if len(parts) > 1 else hexo
    align(o, normal, loc, spin=spin)
    return o


def rivet_ring(center, axis, radius, count, r=0.016, h=0.009, mat="M_Brass", phase=0.0, segs=8):
    """Rivets spaced around a circle on a cylinder (heads point radially outward)."""
    c = V(center)
    R = frame_matrix(axis)
    out = []
    for i in range(count):
        a = math.radians(phase) + 2 * math.pi * i / count
        d = R @ V((math.cos(a), math.sin(a), 0.0))
        out.append(rivet(c + d * radius, d, r, h, mat, segs))
    return out


def rivet_face_ring(center, axis, radius, count, r=0.016, h=0.009, mat="M_Brass", phase=0.0, segs=8):
    """Rivets in a circle on a flat face whose normal is `axis`."""
    c = V(center)
    R = frame_matrix(axis)
    n = V(axis).normalized()
    out = []
    for i in range(count):
        a = math.radians(phase) + 2 * math.pi * i / count
        p = c + R @ V((math.cos(a) * radius, math.sin(a) * radius, 0.0))
        out.append(rivet(p, n, r, h, mat, segs))
    return out


def crystal(name, base, axis=(0, 0, 1), length=0.3, radius=0.06, sides=6, tip=0.32, foot=0.12, mat="M_Crystal",
            spin=0.0, double=False):
    """Faceted gem crystal: a `sides`-sided prism with a pointed tip (and a short pointed foot, or a
    full second point when double=True). Starts at `base` and grows along `axis`."""
    L = length
    if double:
        prof = [(0.0, 0.0), (radius, tip * L), (radius, (1 - tip) * L), (0.0, L)]
    else:
        prof = [(0.0, 0.0), (radius * 0.8, foot * L), (radius, foot * L + 0.25 * radius), (radius, (1 - tip) * L),
                (0.0, L)]
    return lathe_axis(name, prof, axis, base, sides, mat, False, False, 20, spin)


def stave_surface(name, n_staves, z0, z1, rfunc, levels=9, groove=0.012, crown=0.004, mat=None):
    """Open barrel-like surface of revolution around Z made of convex staves separated by grooves.
    rfunc(z) gives the radius at height z."""
    bm = bmesh.new()
    rings = []
    w = 2 * math.pi / n_staves
    fr = ((0.0, -groove), (0.1, 0.0), (0.5, crown), (0.9, 0.0))
    for k in range(levels):
        t = k / (levels - 1)
        z = z0 + (z1 - z0) * t
        r = rfunc(z)
        ring = []
        for s in range(n_staves):
            for (f, dr) in fr:
                a = (s + f) * w
                ring.append(bm.verts.new(((r + dr) * math.cos(a), (r + dr) * math.sin(a), z)))
        rings.append(ring)
    m = len(rings[0])
    for k in range(levels - 1):
        for j in range(m):
            jj = (j + 1) % m
            bm.faces.new((rings[k][j], rings[k][jj], rings[k + 1][jj], rings[k + 1][j]))
    return obj_from_bm(name, bm, mat, 50)


# --------------------------------------------------------------------------------------
# Soft shapes
# --------------------------------------------------------------------------------------

def superellipsoid(name, size, loc=(0, 0, 0), e_xy=0.35, e_z=0.45, segs=24, rings=14, mat=None, smooth_angle=80):
    """Pillow / puck / rounded-box shape. e=1 is round, small e is boxy. e_xy=1 gives a round puck."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=1.0, location=(0, 0, 0))
    o = bpy.context.active_object
    a, b, c = size[0] / 2, size[1] / 2, size[2] / 2

    def sp(v, e):
        return math.copysign(abs(v) ** e, v)

    for v in o.data.vertices:
        x, y, z = v.co
        phi = math.asin(max(-1.0, min(1.0, z)))
        th = math.atan2(y, x)
        hs = abs(math.cos(phi)) ** e_z
        v.co = (a * sp(math.cos(th), e_xy) * hs, b * sp(math.sin(th), e_xy) * hs, c * sp(math.sin(phi), e_z))
    o.name = name
    o.data.name = name
    o.location = loc
    if mat is not None:
        rw.set_mat(o, mat)
    rw.smooth(o, smooth_angle)
    return o


def tuft(o, points, radius, depth, axis=2, sign=1):
    """Pinch a pillow's surface toward its centre around world points (button tufting)."""
    mw = o.matrix_world
    inv = mw.inverted()
    for v in o.data.vertices:
        w = mw @ v.co
        if (w[axis] - o.location[axis]) * sign <= 0:
            continue
        for p in points:
            d = math.sqrt(sum((w[i] - p[i]) ** 2 for i in range(3) if i != axis))
            if d < radius:
                f = (1 - d / radius) ** 2 * depth
                w = V(w)
                w[axis] -= f * sign
        v.co = inv @ w
    o.data.update()
    return o


# --------------------------------------------------------------------------------------
# Rune glyphs (cartoon futhark-ish), as strokes in a unit cell [-0.5, 0.5]^2 (u right, v up)
# --------------------------------------------------------------------------------------

RUNES = {
    "algiz": [[(0, -0.5), (0, 0.5)], [(0, 0.08), (-0.34, 0.46)], [(0, 0.08), (0.34, 0.46)]],
    "fehu": [[(-0.18, -0.5), (-0.18, 0.5)], [(-0.18, 0.12), (0.3, 0.48)], [(-0.18, -0.18), (0.3, 0.16)]],
    "tiwaz": [[(0, -0.5), (0, 0.5)], [(-0.32, 0.16), (0, 0.5), (0.32, 0.16)]],
    "ingwaz": [[(0, 0.5), (0.32, 0), (0, -0.5), (-0.32, 0), (0, 0.5)]],
    "dagaz": [[(-0.34, -0.5), (-0.34, 0.5), (0.34, -0.5), (0.34, 0.5), (-0.34, -0.5)]],
    "sowilo": [[(-0.22, 0.5), (0.24, 0.16), (-0.24, -0.16), (0.22, -0.5)]],
    "othala": [[(-0.36, -0.5), (0.28, 0.12), (0, 0.5), (-0.28, 0.12), (0.36, -0.5)]],
    "kenaz": [[(0.3, 0.5), (-0.26, 0), (0.3, -0.5)]],
    "eye": [[(-0.4, 0), (0, 0.32), (0.4, 0), (0, -0.32), (-0.4, 0)], [(0, -0.1), (0, 0.1)]],
    "hagal": [[(-0.24, -0.5), (-0.24, 0.5)], [(0.24, -0.5), (0.24, 0.5)], [(-0.24, 0.18), (0.24, -0.18)]],
}


def glyph(key, center, u_dir, v_dir, size, width, depth, mat="M_RuneGlow", name="rune"):
    """Rune made of boxes lying on a surface: u_dir/v_dir span the surface, depth runs along u x v.
    The strokes are centred on the surface (half sunk) so they read as inlaid glowing lines."""
    c = V(center)
    u = V(u_dir).normalized()
    v = V(v_dir).normalized()
    n = u.cross(v).normalized()
    out = []
    for stroke in RUNES[key]:
        for (a, b) in zip(stroke[:-1], stroke[1:]):
            pa = c + u * (a[0] * size) + v * (a[1] * size)
            pb = c + u * (b[0] * size) + v * (b[1] * size)
            d = pb - pa
            L = d.length + width
            out.append(obox(name, (L, width, depth), (pa + pb) / 2, d, n, mat))
    return out


def glyph_cutters(key, center, u_dir, v_dir, size, width, depth):
    return glyph(key, center, u_dir, v_dir, size, width, depth, None, "cut")


# --------------------------------------------------------------------------------------
# Booleans
# --------------------------------------------------------------------------------------

def carve(target, cutters, solver='EXACT'):
    """Subtract several cutter objects (joined first) from target; cutters are removed."""
    cutters = [c for c in cutters if c is not None]
    if not cutters:
        return target
    for c in cutters:
        rw.apply_modifiers(c)
    cut = rw.join(cutters, "cutter", origin=None) if len(cutters) > 1 else cutters[0]
    rw.apply_modifiers(target)
    m = target.modifiers.new("Carve", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.object = cut
    m.solver = solver
    if solver == 'EXACT':
        m.use_self = True
    rw._active(target)
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cut, do_unlink=True)
    return target


# --------------------------------------------------------------------------------------
# Whole-model checks
# --------------------------------------------------------------------------------------

def roots():
    return [o for o in bpy.context.scene.objects if o.parent is None and not o.get("rw_helper")
            and o.type in ('MESH', 'EMPTY')]


def recentre(axes="XYZ"):
    """Shift every root object so the bounding box of the visible meshes is centred on the origin."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    c = (mn + mx) / 2
    shift = V((c.x if "X" in axes else 0.0, c.y if "Y" in axes else 0.0, c.z if "Z" in axes else 0.0))
    for o in roots():
        o.location -= shift
    bpy.context.view_layer.update()
    return shift


def fit_scale(objs, target, axes="XYZ"):
    """Scale meshes (about the world origin) so the overall bbox matches `target` on the given axes."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    size = mx - mn
    s = [target[i] / size[i] if ("XYZ"[i] in axes and size[i] > 1e-6) else 1.0 for i in range(3)]
    S = Matrix.Diagonal((s[0], s[1], s[2], 1.0))
    for o in objs:
        rw.apply_modifiers(o)
        o.data.transform(o.matrix_world.inverted() @ S @ o.matrix_world)
        o.data.update()
    return s


def check(asset, size, tol=0.03):
    """Print a pass/fail line for the overall size (Blender X, Y, Z) and the triangle count."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    got = mx - mn
    ok = all(abs(got[i] - size[i]) <= tol * size[i] for i in range(3) if size[i])
    cen = (mn + mx) / 2
    print("RWREPORT   CHECK %s size %.3f x %.3f x %.3f (spec %s) -> %s; bbox centre (%.3f, %.3f, %.3f); tris %d" % (
        asset, got.x, got.y, got.z, "x".join(str(s) for s in size), "OK" if ok else "OUT OF TOLERANCE",
        cen.x, cen.y, cen.z, rw.tri_count()))
    return ok


def seeded(seed):
    random.seed(seed)
    return random
