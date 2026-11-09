"""charlib: character-building helpers for RuneWire Batch B (enemies and NPCs).

Import from art/blender/enemies/<asset>.py or art/blender/npcs/<asset>.py:

    import os, sys
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    sys.path.insert(0, os.path.join(HERE, "..", "enemies"))
    import rwlib as rw
    import charlib as cl

Builds on rwlib (which must not be edited). Same conventions: metres, +Z up, front = -Y,
a character's LEFT is +X, angles in degrees.

Mesh builders here return a new object whose vertices are already in world space (origin at the
world origin). `node()` joins a list of parts into one named object, moves its origin to the
joint pivot and parents it, so every animated node has identity rotation and only a location.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import rwlib as rw

V = Vector


# ======================================================================================
# Small math helpers
# ======================================================================================

def vec(p):
    return p.copy() if isinstance(p, Vector) else Vector(p)


def lerp(a, b, t):
    return vec(a).lerp(vec(b), t)


def frame(forward=(0, -1, 0), up=(0, 0, 1)):
    """3x3 rotation whose local -Y points along `forward` and local +Z along `up`.
    The default arguments give the identity (front-facing) frame."""
    f = vec(forward).normalized()
    u = vec(up)
    u = u - f * u.dot(f)
    if u.length < 1e-6:
        u = Vector((0, 1, 0)) if abs(f.z) > 0.9 else Vector((0, 0, 1))
        u = u - f * u.dot(f)
    u.normalize()
    y = -f
    x = y.cross(u)
    return Matrix((x, y, u)).transposed()


def axes_matrix(x, y, z):
    """3x3 matrix with the given column axes."""
    return Matrix((vec(x), vec(y), vec(z))).transposed()


def rotate(v, axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis) @ vec(v)


def _rotm(rot):
    if rot is None:
        return Matrix.Identity(3)
    if isinstance(rot, Matrix):
        return rot.to_3x3()
    return Euler([math.radians(a) for a in rot]).to_matrix()


def bezier(p0, p1, p2, n=6, p3=None):
    """Points on a quadratic (or cubic, if p3 given) Bezier curve."""
    p0, p1, p2 = vec(p0), vec(p1), vec(p2)
    out = []
    for i in range(n):
        t = i / (n - 1)
        if p3 is None:
            out.append(p0 * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + p2 * t * t)
        else:
            q = vec(p3)
            out.append(p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t * t + q * t ** 3)
    return out


def flatten(items):
    out = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, (list, tuple)):
            out.extend(flatten(it))
        else:
            out.append(it)
    return out


# ======================================================================================
# Mesh builders (vertices in world space)
# ======================================================================================

def _new_obj(name, bm, mat=None, smooth=True, smooth_angle=None, mats=None):
    for f in bm.faces:
        f.smooth = bool(smooth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mats:
        # multi-material object: face material_index values were set in bmesh
        for m in mats:
            o.data.materials.append(rw._resolve_mat(m))
    elif mat is not None:
        rw.set_mat(o, mat)
    if smooth_angle:
        rw.smooth(o, smooth_angle)
    return o


def _orient_outward(bm):
    """Flip all faces if, on average, normals point toward the centroid (works for open tubes)."""
    if not bm.faces:
        return
    bm.normal_update()
    c = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    s = 0.0
    for f in bm.faces:
        s += f.normal.dot(f.calc_center_median() - c) * f.calc_area()
    if s < 0:
        for f in bm.faces:
            f.normal_flip()
        bm.normal_update()


def ellipsoid(name, center, radii, segments=20, rings=10, mat=None, rot=None, smooth=True):
    """UV ellipsoid. `rot`: 3x3 Matrix (e.g. frame()) or XYZ euler in degrees."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    M = Matrix.Translation(vec(center)) @ _rotm(rot).to_4x4() @ Matrix.Diagonal(
        (radii[0], radii[1], radii[2], 1.0))
    bm.transform(M)
    if M.to_3x3().determinant() < 0:
        for f in bm.faces:
            f.normal_flip()
    return _new_obj(name, bm, mat, smooth)


def sphere(name, center, r, segments=16, rings=8, mat=None, smooth=True):
    return ellipsoid(name, center, (r, r, r), segments, rings, mat, None, smooth)


def ring(center, rx, ry=None, n=24, rmod=None, zmod=None, zlist=None, phase=0.0):
    """Horizontal ellipse of n points around `center`.
    Angle 0 = +X (left), 90 = +Y (back), 270 = -Y (front). rmod(a)/zmod(a) take radians;
    zlist gives a per-vertex z offset list."""
    cx, cy, cz = center
    ry = rx if ry is None else ry
    pts = []
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        m = rmod(a) if rmod else 1.0
        dz = zmod(a) if zmod else 0.0
        if zlist is not None:
            dz += zlist[k]
        pts.append(Vector((cx + rx * m * math.cos(a), cy + ry * m * math.sin(a), cz + dz)))
    return pts


def _is_point(r):
    return isinstance(r, Vector) or (len(r) == 3 and isinstance(r[0], (int, float)))


def skin(name, rings, mat=None, cap_start=True, cap_end=True, smooth=True, smooth_angle=None, closed=True,
         orient=True):
    """Loft through rings (lists of points with equal counts; a single point is a pole)."""
    bm = bmesh.new()
    vr = []
    for r in rings:
        if _is_point(r):
            vr.append([bm.verts.new(vec(r))])
        else:
            vr.append([bm.verts.new(vec(p)) for p in r])
    n = max(len(r) for r in vr)
    for i in range(len(vr) - 1):
        a, b = vr[i], vr[i + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        rng = range(n) if closed else range(n - 1)
        if len(a) == 1:
            for k in rng:
                bm.faces.new((a[0], b[(k + 1) % n], b[k]))
        elif len(b) == 1:
            for k in rng:
                bm.faces.new((a[k], a[(k + 1) % n], b[0]))
        else:
            for k in rng:
                j = (k + 1) % n
                bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap_start and len(vr[0]) > 2:
        bm.faces.new(list(reversed(vr[0])))
    if cap_end and len(vr[-1]) > 2:
        bm.faces.new(vr[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if orient:
        _orient_outward(bm)
    return _new_obj(name, bm, mat, smooth, smooth_angle)


def _frames(pts, up=None):
    n = len(pts)
    T = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            a = pts[i] - pts[i - 1]
            b = pts[i + 1] - pts[i]
            t = (a.normalized() if a.length > 1e-9 else a) + (b.normalized() if b.length > 1e-9 else b)
        if t.length < 1e-9:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        T.append(t.normalized())
    frames = []
    if up is not None:
        u0 = vec(up)
        for t in T:
            N = u0 - t * u0.dot(t)
            if N.length < 1e-6:
                alt = Vector((0, -1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
                N = alt - t * alt.dot(t)
            N.normalize()
            frames.append((N, t.cross(N)))
        return frames
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.95 else Vector((0, -1, 0))
    N = (ref - T[0] * ref.dot(T[0])).normalized()
    for i, t in enumerate(T):
        if i > 0:
            N = T[i - 1].rotation_difference(t) @ N
            N = (N - t * N.dot(t)).normalized()
        frames.append((N, t.cross(N)))
    return frames


def sweep(name, pts, radii, segments=12, mat=None, scale=None, up=None, cap_start=True, cap_end=True,
          smooth=True, smooth_angle=None, twist=0.0):
    """Tube through `pts` with per-point radius (list, number or f(t)); a radius of 0 makes a
    pointed end. `scale` = (sx, sy) or a list/f(t) of them: sx scales along `up` (the ring's N
    axis), sy along N x tangent. Without `up`, frames are parallel-transported."""
    pts = [vec(p) for p in pts]
    n = len(pts)
    if callable(radii):
        radii = [radii(i / (n - 1)) for i in range(n)]
    elif isinstance(radii, (int, float)):
        radii = [float(radii)] * n
    if scale is None:
        scale = [(1.0, 1.0)] * n
    elif callable(scale):
        scale = [scale(i / (n - 1)) for i in range(n)]
    elif isinstance(scale[0], (int, float)):
        scale = [tuple(scale)] * n
    fr = _frames(pts, up)
    rings = []
    for i, p in enumerate(pts):
        r = radii[i]
        if r <= 1e-6:
            rings.append(p)
            continue
        N, B = fr[i]
        sx, sy = scale[i]
        rings.append([p + N * (r * sx * math.cos(2 * math.pi * k / segments + twist))
                      + B * (r * sy * math.sin(2 * math.pi * k / segments + twist)) for k in range(segments)])
    return skin(name, rings, mat, cap_start, cap_end, smooth, smooth_angle)


def capsule(name, p0, p1, r0, r1=None, segments=16, cap_rings=4, mat=None, scale=None, up=None, smooth=True):
    """Tapered capsule between two points (round ends of radius r0 at p0 and r1 at p1)."""
    r1 = r0 if r1 is None else r1
    p0, p1 = vec(p0), vec(p1)
    d = p1 - p0
    if d.length < 1e-6:
        d = Vector((0, 0, 1e-4))
    d.normalize()
    pts, rad = [], []
    for k in range(cap_rings + 1):
        phi = math.pi / 2 * (1 - k / cap_rings)
        pts.append(p0 - d * (r0 * math.sin(phi)))
        rad.append(r0 * math.cos(phi))
    for k in range(1, cap_rings + 1) if (p1 - p0).length < 1e-6 else range(cap_rings + 1):
        phi = math.pi / 2 * (k / cap_rings)
        pts.append(p1 + d * (r1 * math.sin(phi)))
        rad.append(r1 * math.cos(phi))
    rad = [0.0 if r < 1e-6 else r for r in rad]
    return sweep(name, pts, rad, segments, mat, scale=scale, up=up, smooth=smooth)


def dome(name, center, radii, rot=None, cover=0.5, segments=16, rings=6, mat=None, smooth=True, tilt=0.0):
    """Closed cap of an ellipsoid: the top `cover` fraction (0..1 of the height) along local +Z.
    `tilt` (deg) rolls the cut line about local Y. Used for eyelids, helmets, hair caps."""
    th_max = math.acos(max(-1.0, min(1.0, 1 - 2 * cover)))
    rs = [Vector((0, 0, 1))]
    for i in range(1, rings + 1):
        th = th_max * i / rings
        rs.append([Vector((math.sin(th) * math.cos(2 * math.pi * k / segments),
                           math.sin(th) * math.sin(2 * math.pi * k / segments), math.cos(th)))
                   for k in range(segments)])
    M = Matrix.Translation(vec(center)) @ _rotm(rot).to_4x4() @ Matrix.Rotation(math.radians(tilt), 4, 'Y') \
        @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1.0))
    rs = [(M @ r) if isinstance(r, Vector) else [M @ p for p in r] for r in rs]
    return skin(name, rs, mat, cap_start=False, cap_end=True, smooth=smooth)


def teardrop(name, base, tip, r, bend=(0, 0, 0), segments=16, mat=None, bulb=0.55, steps=9):
    """Flame/drop shape: a round bulb of radius r at `base` tapering to a point at `tip`,
    with the upper half bent by `bend` (offset added at the tip, eased in)."""
    base, tip, bend = vec(base), vec(tip), vec(bend)
    axis = tip - base
    L = axis.length
    d = axis.normalized()
    pts, rad = [], []
    # bottom hemisphere
    for k in range(4):
        phi = math.pi / 2 * (1 - k / 4)
        pts.append(base - d * (r * math.sin(phi)))
        rad.append(r * math.cos(phi))
    for i in range(1, steps + 1):
        t = i / steps
        p = base + axis * t + bend * (t ** 2)
        pts.append(p)
        # radius: hold near r for the bulb, then taper to 0 with a soft curve
        u = max(0.0, (t - bulb * 0.2) / (1 - bulb * 0.2))
        rad.append(r * max(0.0, (1 - u ** 1.6)) ** 0.9 if i < steps else 0.0)
    return sweep(name, pts, rad, segments, mat)


def torus(name, center, major, minor, rot=None, major_seg=24, minor_seg=8, mat=None, scale=(1, 1)):
    """Torus in the local XY plane (axis local Z); `scale` stretches the ring (x, y)."""
    bm = bmesh.new()
    rings = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        c = Vector((math.cos(a) * major * scale[0], math.sin(a) * major * scale[1], 0))
        radial = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + radial * (minor * math.cos(2 * math.pi * k / minor_seg))
                                   + Vector((0, 0, minor * math.sin(2 * math.pi * k / minor_seg))))
                      for k in range(minor_seg)])
    for i in range(major_seg):
        a, b = rings[i], rings[(i + 1) % major_seg]
        for k in range(minor_seg):
            j = (k + 1) % minor_seg
            bm.faces.new((a[k], b[k], b[j], a[j]))
    bm.transform(Matrix.Translation(vec(center)) @ _rotm(rot).to_4x4())
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _new_obj(name, bm, mat, True)


def cyl(name, p0, p1, r, segments=20, mat=None, bevel=0.0, r1=None, smooth_angle=40):
    """Cylinder (or truncated cone with r1) between two points, flat caps, optional bevel."""
    p0, p1 = vec(p0), vec(p1)
    d = (p1 - p0)
    L = d.length
    r1 = r if r1 is None else r1
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r, radius2=r1, depth=L)
    R = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bm.transform(Matrix.Translation((p0 + p1) / 2) @ R)
    o = _new_obj(name, bm, mat, False)
    if bevel > 0:
        rw.add_bevel(o, bevel, 2, 40.0, harden=False)
    rw.smooth(o, smooth_angle)
    return o


def rbox(name, size, center, radius=0.03, mat=None, rot=None, segments=2):
    """Rounded box (rwlib rounded_box) with an optional rotation matrix/euler."""
    if rot is None or isinstance(rot, tuple):
        return rw.rounded_box(name, size, radius, tuple(center), rot or (0, 0, 0), mat=mat, segments=segments)
    o = rw.rounded_box(name, size, radius, (0, 0, 0), (0, 0, 0), mat=mat, segments=segments)
    o.data.transform(rot.to_4x4())
    o.location = vec(center)
    return o


# ======================================================================================
# Assembly
# ======================================================================================

def node(name, parts, pivot, parent=None):
    """Join `parts` into one object called `name`, origin at world `pivot`, parented to `parent`."""
    parts = flatten(parts)
    if not parts:
        raise ValueError("node %s has no parts" % name)
    if len(parts) == 1:
        o = parts[0]
        if o.type != 'MESH':
            rw._active(o)
            bpy.ops.object.convert(target='MESH')
            o = bpy.context.active_object
        rw.apply_modifiers(o)
        o.name = name
        o.data.name = name
        rw.set_origin(o, pivot)
    else:
        o = rw.join(parts, name, pivot)
    if o.name != name:
        raise RuntimeError("node name clash: wanted %s, got %s" % (name, o.name))
    if parent is not None:
        rw.set_parent(o, parent)
    return o


def empty(name, loc, parent=None, size=0.1):
    e = rw.empty(name, tuple(loc), parent, size)
    if e.name != name:
        raise RuntimeError("empty name clash: wanted %s, got %s" % (name, e.name))
    return e


# ======================================================================================
# Hard-surface details
# ======================================================================================

def rivet(p, r=0.018, normal=(0, 0, 1), mat="M_Brass", segs=6):
    """Domed rivet head sitting on a surface with the given outward normal."""
    n = vec(normal).normalized()
    R = Vector((0, 0, 1)).rotation_difference(n).to_matrix()
    return ellipsoid("rivet", vec(p), (r, r, r * 0.6), segs, 3, mat, R)


def rivet_ring(center, radius, count, r=0.018, axis=(0, 0, 1), mat="M_Brass", phase=0.0, outward=True):
    """Rivets on a circle around `axis`. outward=True: heads face radially out (on a cylinder side);
    False: heads face along the axis (on a flat disc)."""
    ax = vec(axis).normalized()
    R = Vector((0, 0, 1)).rotation_difference(ax).to_matrix()
    out = []
    for i in range(count):
        a = math.radians(phase) + 2 * math.pi * i / count
        radial = R @ Vector((math.cos(a), math.sin(a), 0))
        p = vec(center) + radial * radius
        out.append(rivet(p, r, radial if outward else ax, mat))
    return out


def rivet_line(p0, p1, count, r=0.018, normal=(0, -1, 0), mat="M_Brass"):
    return [rivet(lerp(p0, p1, (i / (count - 1)) if count > 1 else 0.5), r, normal, mat) for i in range(count)]


HAZ_Y = "M_PaintedMetal__f2c12e"


def hazard_black():
    return rw.flat("HazardBlack", "24232a", 0.6, 0.2)


def hazard_band(name, center, radius, z0, z1, count=8, skew=28.0, thickness=0.025, segs_per=3, mats=None):
    """Cylindrical band (axis Z) with `count` yellow/black diagonal stripe pairs."""
    hazard_black()
    mats = mats or (HAZ_Y, "HazardBlack")
    cx, cy = center[0], center[1]
    bm = bmesh.new()
    N = 2 * count * segs_per
    sk = math.radians(skew)
    ro, ri = radius, radius - thickness
    cols = []
    for k in range(N):
        a = 2 * math.pi * k / N
        b = a + sk
        cols.append((bm.verts.new((cx + ro * math.cos(a), cy + ro * math.sin(a), z0)),
                     bm.verts.new((cx + ro * math.cos(b), cy + ro * math.sin(b), z1)),
                     bm.verts.new((cx + ri * math.cos(a), cy + ri * math.sin(a), z0)),
                     bm.verts.new((cx + ri * math.cos(b), cy + ri * math.sin(b), z1))))
    for k in range(N):
        j = (k + 1) % N
        ob0, ot0, ib0, it0 = cols[k]
        ob1, ot1, ib1, it1 = cols[j]
        mi = (k // segs_per) % 2
        for f in ((ob0, ob1, ot1, ot0), (ib0, it0, it1, ib1), (ot0, ot1, it1, it0), (ob0, ib0, ib1, ob1)):
            face = bm.faces.new(f)
            face.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _new_obj(name, bm, None, True, None, mats)
    rw.smooth(o, 40)
    return o


def _clip(poly, a, b, c):
    """Keep the part of convex polygon `poly` (2D) where a*x + b*y >= c."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def hazard_panel(name, w, h, depth, center, rot=None, stripe=0.09, mats=None, bevel=0.004, flip=False):
    """Flat yellow/black diagonal-striped plate. Built in the local XZ plane, front face toward
    local -Y, then rotated by `rot` (3x3 Matrix or XYZ euler deg) and moved to `center`."""
    hazard_black()
    mats = mats or (HAZ_Y, "HazardBlack")
    rect = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    sgn = -1.0 if flip else 1.0
    lo = -(w + h) / 2
    bm = bmesh.new()
    s = 0
    while lo + s * stripe < (w + h) / 2:
        a0, a1 = lo + s * stripe, lo + (s + 1) * stripe
        poly = _clip(_clip(rect, sgn, 1.0, a0), -sgn, -1.0, -a1)
        if len(poly) >= 3:
            front = [bm.verts.new((x, -depth / 2, z)) for (x, z) in poly]
            back = [bm.verts.new((x, depth / 2, z)) for (x, z) in poly]
            fs = [bm.faces.new(front), bm.faces.new(list(reversed(back)))]
            m = len(poly)
            for i in range(m):
                j = (i + 1) % m
                fs.append(bm.faces.new((front[i], back[i], back[j], front[j])))
            for f in fs:
                f.material_index = s % 2
        s += 1
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.transform(Matrix.Translation(vec(center)) @ _rotm(rot).to_4x4())
    o = _new_obj(name, bm, None, False, None, mats)
    if bevel:
        rw.add_bevel(o, bevel, 1, 40.0, harden=False)
    return o


def surface_points(target, center, dirs, inset=0.0):
    """Ray-cast from `center` outward along each direction to `target`'s surface (world space).
    Directions may be vectors or (azimuth, elevation) pairs in degrees (azimuth 0 = -Y front,
    90 = +X left)."""
    mw = target.matrix_world
    inv = mw.inverted()
    c_l = inv @ vec(center)
    out = []
    for d in dirs:
        if len(d) == 2:
            az, el = math.radians(d[0]), math.radians(d[1])
            d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        d = vec(d).normalized()
        d_l = (inv.to_3x3() @ d).normalized()
        ok, loc, nrm, idx = target.ray_cast(c_l, d_l)
        if ok:
            out.append(mw @ loc - d * inset)
    return out


def surface_crack(name, target, center, dirs, radius=0.025, inset=0.006, mat="M_RuneGlow"):
    """Glowing crack/rune line that follows `target`'s surface (half-embedded tube)."""
    pts = surface_points(target, center, dirs, inset)
    if len(pts) < 2:
        return None
    return rw.tube(name, [tuple(p) for p in pts], radius, mat=mat, resolution=1, smooth_curve=False)


def cloth_shell(o, thickness=0.02, inner_mat=None, offset=-1.0):
    """Give an open cloth surface thickness (solidify, applied when joined); the inner shell gets
    `inner_mat`."""
    mod = o.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = offset
    mod.use_even_offset = True
    mod.use_quality_normals = True
    if inner_mat is not None:
        m = rw._resolve_mat(inner_mat)
        if m.name not in [s.name for s in o.data.materials if s]:
            o.data.materials.append(m)
        idx = [i for i, s in enumerate(o.data.materials) if s and s.name == m.name][0]
        mod.material_offset = idx
        mod.material_offset_rim = 0
    return o


def tatters(n, long=0.12, short=0.02, var=0.5, seed=1):
    """Per-vertex z offsets for a tattered hem: even vertices drop into points, odd ones notch up."""
    rnd = random.Random(seed)
    out = []
    for k in range(n):
        if k % 2 == 0:
            out.append(-long * (1 - var / 2 + var * rnd.random()))
        else:
            out.append(short * rnd.random())
    return out


# ======================================================================================
# Faces
# ======================================================================================

def head_point(C, R, x, z, out=0.0):
    """Point on the front (-Y) surface of an axis-aligned ellipsoid (centre C, radii R) at (x, z),
    pushed `out` metres along the surface normal."""
    cx, cy, cz = C
    a, b, c = R
    u = (x - cx) / a
    w = (z - cz) / c
    t = max(0.0, 1 - u * u - w * w)
    y = cy - b * math.sqrt(t)
    p = Vector((x, y, z))
    if out:
        p += head_normal(C, R, p) * out
    return p


def head_normal(C, R, p):
    cx, cy, cz = C
    a, b, c = R
    return Vector(((p[0] - cx) / (a * a), (p[1] - cy) / (b * b), (p[2] - cz) / (c * c))).normalized()


def cartoon_eye(name, c, r, look=(0, -1, 0), up=(0, 0, 1), shape=(0.8, 0.55, 1.0), iris=None, iris_r=0.62,
                pupil_r=0.36, white="EyeWhite", pupil="Pupil", shine="EyeShine", segs=16, shine_x=0.22,
                lid=None, lid_mat=None, lid_tilt=0.0, lower_lid=None, look_offset=(0.0, 0.0)):
    """Cartoon eye: white ellipsoid + optional coloured iris + dark pupil + tiny highlight,
    optional upper/lower lids (cover fraction 0..1). Returns a list of parts."""
    rw.flat("EyeWhite", "fbf8f0", 0.35)
    rw.flat("Pupil", "1b1622", 0.3)
    rw.glow("EyeShine", "ffffff", 1.2)
    F = frame(look, up)
    c = vec(c)
    rx, ry, rz = r * shape[0], r * shape[1], r * shape[2]
    lx, lz = look_offset
    parts = [ellipsoid(name + "_white", c, (rx, ry, rz), segs, max(6, segs // 2 + 2), white, F)]
    if iris:
        parts.append(ellipsoid(name + "_iris", c + F @ Vector((rx * lx, -ry * 0.84, rz * (lz - 0.04))),
                               (rx * iris_r, ry * 0.34, rz * iris_r * 1.04), 14, 8, iris, F))
        parts.append(ellipsoid(name + "_pupil", c + F @ Vector((rx * lx, -ry * 0.98, rz * (lz - 0.04))),
                               (rx * pupil_r, ry * 0.24, rz * pupil_r * 1.08), 12, 6, pupil, F))
        sh = c + F @ Vector((rx * (lx + shine_x), -ry * 1.12, rz * (lz + 0.26)))
    else:
        parts.append(ellipsoid(name + "_pupil", c + F @ Vector((rx * lx, -ry * 0.9, rz * (lz - 0.04))),
                               (rx * 0.5, ry * 0.3, rz * 0.56), 12, 8, pupil, F))
        sh = c + F @ Vector((rx * (lx + shine_x), -ry * 1.1, rz * (lz + 0.26)))
    parts.append(ellipsoid(name + "_shine", sh, (r * 0.12, r * 0.08, r * 0.12), 8, 4, shine, F))
    if lid:
        parts.append(dome(name + "_lid", c, (rx * 1.1, ry * 1.18, rz * 1.08), F, lid, segs, 5, lid_mat,
                          tilt=lid_tilt))
    if lower_lid:
        Fl = F @ Matrix.Rotation(math.pi, 3, 'Y')
        parts.append(dome(name + "_llid", c, (rx * 1.08, ry * 1.12, rz * 1.06), Fl, lower_lid, segs, 4,
                          lid_mat))
    return parts


def brow(name, p_in, p_out, r=0.018, lift=0.012, mat=None, fwd=(0, -1, 0), flat=0.55, steps=7):
    """Arched eyebrow from the inner to the outer end (thick in the middle)."""
    p_in, p_out = vec(p_in), vec(p_out)
    mid = (p_in + p_out) / 2 + Vector((0, 0, lift))
    pts = bezier(p_in, mid, p_out, steps)
    rad = [r * (0.75 + 0.35 * math.sin(math.pi * i / (steps - 1))) for i in range(steps)]
    rad[0] *= 0.9
    rad[-1] *= 0.55
    return sweep(name, pts, rad, 10, mat, scale=(1.0, flat), up=(0, 0, 1))


def mouth_arc(name, C, R, x0, x1, z, curve=0.02, r=0.012, mat="Mouth", steps=9, embed=0.3, flat=0.6):
    """Smile (curve > 0: corners up) or frown along the front of an ellipsoid head."""
    rw.flat("Mouth", "5a2430", 0.6)
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        x = x0 + (x1 - x0) * t
        zz = z + curve * (2 * t - 1) ** 2
        pts.append(head_point(C, R, x, zz, -r * embed))
    rad = [r * (0.55 + 0.45 * math.sin(math.pi * i / (steps - 1))) for i in range(steps)]
    return sweep(name, pts, rad, 8, mat, scale=(1.0, flat), up=(0, 0, 1))


# ======================================================================================
# Hands
# ======================================================================================

def _hand_axes(down, palm, thumb):
    d = vec(down).normalized()
    n = vec(palm)
    n = (n - d * n.dot(d)).normalized()
    t = vec(thumb)
    t = t - d * t.dot(d) - n * t.dot(n)
    t = t.normalized() if t.length > 1e-6 else d.cross(n)
    return d, n, t


def mitten(name, wrist, down=(0, 0, -1), palm=(-1, 0, 0), thumb=(0, -1, 0), s=0.12, mat="M_Skin",
           fingers=3, curl=0.35, spread=1.0, segs=10):
    """Chunky cartoon hand: palm, `fingers` sausage fingers and a thumb.
    down = wrist->fingertips direction, palm = palm normal, thumb = side the thumb is on."""
    d, n, t = _hand_axes(down, palm, thumb)
    W = vec(wrist)
    parts = []
    M = axes_matrix(t, n, d)
    parts.append(ellipsoid(name + "_palm", W + d * (0.42 * s), (0.42 * s, 0.24 * s, 0.46 * s), segs + 2, 8,
                           mat, M))
    for k in range(fingers):
        off = (k - (fingers - 1) / 2) * 0.27 * s * spread
        b = W + d * (0.66 * s) + t * off
        tip = b + d * (0.36 * s) + n * (0.16 * s * curl) - t * (off * 0.1)
        parts.append(capsule(name + "_f%d" % k, b, tip, 0.13 * s, 0.12 * s, segs, 3, mat))
    b = W + d * (0.3 * s) + t * (0.32 * s) + n * (0.06 * s)
    tip = b + t * (0.2 * s) + d * (0.26 * s) + n * (0.1 * s)
    parts.append(capsule(name + "_thumb", b, tip, 0.13 * s, 0.12 * s, segs, 3, mat))
    return parts


def claw_hand(name, wrist, down=(0, 0, -1), palm=(-1, 0, 0), thumb=(0, -1, 0), s=0.2, mat=None,
              claw_mat=None, fingers=4, curl=0.6, segs=8):
    """Bony clawed hand with long tapering fingers that end in sharp claws."""
    d, n, t = _hand_axes(down, palm, thumb)
    W = vec(wrist)
    parts = [ellipsoid(name + "_palm", W + d * (0.28 * s), (0.3 * s, 0.14 * s, 0.32 * s), 12, 8, mat,
                       axes_matrix(t, n, d))]
    for k in range(fingers):
        u = (k - (fingers - 1) / 2) / max(1, (fingers - 1) / 2)
        base = W + d * (0.5 * s) + t * (u * 0.22 * s)
        fdir = (d + t * (u * 0.35)).normalized()
        L = s * (0.62 - 0.12 * abs(u))
        p1 = base + fdir * (L * 0.45)
        p2 = p1 + fdir * (L * 0.35) + n * (L * 0.25 * curl)
        p3 = p2 + (fdir * 0.4 + n * 0.9 * curl).normalized() * (L * 0.3)
        parts.append(sweep(name + "_f%d" % k, [base, p1, p2], [0.075 * s, 0.065 * s, 0.05 * s], segs, mat))
        parts.append(sweep(name + "_c%d" % k, [p2, (p2 + p3) / 2, p3], [0.055 * s, 0.035 * s, 0.0], segs,
                           claw_mat or mat))
    # thumb claw
    base = W + d * (0.25 * s) + t * (0.3 * s)
    p1 = base + (t * 0.7 + d * 0.5).normalized() * (0.25 * s)
    p2 = p1 + (d + n * curl).normalized() * (0.2 * s)
    parts.append(sweep(name + "_tf", [base, p1], [0.07 * s, 0.055 * s], segs, mat))
    parts.append(sweep(name + "_tc", [p1, (p1 + p2) / 2, p2], [0.055 * s, 0.035 * s, 0.0], segs, claw_mat or mat))
    return parts


# ======================================================================================
# Arms for humanoids (single node from the shoulder: upper arm, elbow, forearm, hand)
# ======================================================================================

def arm_dirs(side, spread=8.0, bend=12.0, swing=0.0):
    """Upper-arm and forearm unit directions for a hanging arm.
    side +1 = left (+X), -1 = right. spread tilts outward, bend tilts the forearm forward,
    swing rotates the whole arm forward (negative = back)."""
    d1 = Vector((side * math.sin(math.radians(spread)), 0.0, -math.cos(math.radians(spread))))
    d1 = Matrix.Rotation(math.radians(-swing), 3, 'X') @ d1
    d2 = Matrix.Rotation(math.radians(-bend), 3, 'X') @ d1
    return d1.normalized(), d2.normalized()


# ======================================================================================
# QA helpers
# ======================================================================================

def preview_path(asset, category, tag):
    return os.path.join(rw.ART, "previews", category, "%s_%s.png" % (asset, tag))


def render_extra(asset, category, views=("front", "side"), size=640):
    for v in views:
        rw.render_view(preview_path(asset, category, v), v, size)


def render_pose(asset, category, pose, tag="pose", view="front34", size=640):
    """Temporarily rotate nodes (name -> XYZ euler degrees), render, then restore the rest pose."""
    saved = {}
    for nm, r in pose.items():
        o = bpy.data.objects[nm]
        saved[nm] = o.rotation_euler.copy()
        o.rotation_euler = tuple(math.radians(a) for a in r)
    bpy.context.view_layer.update()
    rw.render_view(preview_path(asset, category, tag), view, size)
    for nm, r in saved.items():
        bpy.data.objects[nm].rotation_euler = r
    bpy.context.view_layer.update()


def report_nodes(names):
    """Print each node's world pivot and its offset from its parent (for the asset report)."""
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            print("RWNODE   MISSING %s" % nm)
            continue
        w = o.matrix_world.translation
        p = o.parent
        loc = (w - p.matrix_world.translation) if p else w
        rot_ok = all(abs(a) < 1e-6 for a in o.rotation_euler) and all(abs(s - 1) < 1e-6 for s in o.scale)
        print("RWNODE   %-14s parent=%-12s pivot=(%7.3f, %7.3f, %7.3f) local=(%7.3f, %7.3f, %7.3f)%s" % (
            nm, p.name if p else "-", w.x, w.y, w.z, loc.x, loc.y, loc.z, "" if rot_ok else "  !ROT/SCALE"))


def budget(limit):
    n = rw.tri_count()
    print("RWBUDGET triangles %d / %d %s" % (n, limit, "OK" if n <= limit else "OVER BUDGET"))
    return n


def tri_breakdown():
    """Print triangles per mesh node (largest first)."""
    rows = []
    for o in rw.all_mesh_objects():
        if o.hide_render:
            continue
        rows.append((rw.tri_count([o]), o.name))
    for n, nm in sorted(rows, reverse=True):
        print("RWTRIS   %-16s %6d" % (nm, n))
