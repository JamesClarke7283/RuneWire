"""magiclib: extra character helpers for the Hollow Choir (magic) enemies of RuneWire.

Builds on charlib (shared Batch B helpers) and rwlib; neither is edited. Import it from an enemy
generator script after charlib:

    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    sys.path.insert(0, HERE)
    import rwlib as rw
    import charlib as cl
    import magiclib as ml

Conventions are the same as charlib: metres, +Z up, the front faces -Y, a character's LEFT is +X,
user-facing angles in degrees, and every builder returns an object whose vertices are already in
world space (origin at the world origin), ready to be joined into a node with cl.node().

Contents
  rock()           faceted cartoon boulder (convex hull, merged facets, soft chamfer bevel)
  surface_hit()    ray-cast a direction from a point onto an object's surface
  ribbon()         flattened glowing bead that lies along a surface (cracks, runes, seams)
  crack()          jagged branching glowing crack that follows a rock's surface
  surface_glyph()  a rune glyph (partlib.RUNES) projected onto a curved surface
  moss_tuft()      cluster of soft moss blobs, plus optional dangling strands
  cloth helpers    hood(), sleeve(), robe(), tatter_strip() for the cultist and the wraith
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402

V = Vector


# ======================================================================================
# Rocks
# ======================================================================================

def rock(name, center, radii, rot=None, seed=1, n=24, jitter=0.08, boxy=2.4, wobble=0.12, mat="M_StoneRough",
         bevel=0.03, segs=1, clip_z=None, merge=7.0, bevel_angle=22.0, taper=0.0):
    """Faceted cartoon boulder: convex hull of `n` points spread over a (super)ellipsoid.

    radii   half-sizes along the rock's local X, Y, Z (before `rot`)
    boxy    superellipsoid exponent (2 = ellipsoid, 3-4 = chunky block)
    jitter  random radial in/out of each hull point (fraction)
    wobble  random direction jitter before projection (bigger = more irregular facets)
    clip_z  flatten everything below this world height (flat soles / bases)
    merge   near-coplanar hull triangles within this angle are merged into one facet
    bevel   soft chamfer width on the facet edges (applied when the node is joined)
    taper   widen the top (+) or the bottom (-): local X/Y scale by (1 + taper * local z)
    """
    rnd = random.Random(seed * 7919 + 17)
    golden = math.pi * (3.0 - math.sqrt(5.0))
    off = rnd.random() * 2.0 * math.pi
    R = cl._rotm(rot)
    C = cl.vec(center)
    pts = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = off + golden * i
        d = V((r * math.cos(th), r * math.sin(th), z))
        d += V((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * wobble
        d.normalize()
        s = (abs(d.x) ** boxy + abs(d.y) ** boxy + abs(d.z) ** boxy) ** (-1.0 / boxy)
        d = d * s * (1.0 + rnd.uniform(-jitter, jitter))
        tp = 1.0 + taper * max(-1.0, min(1.0, d.z))
        p = C + R @ V((d.x * radii[0] * tp, d.y * radii[1] * tp, d.z * radii[2]))
        if clip_z is not None and p.z < clip_z:
            p.z = clip_z
        pts.append(p)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    bmesh.ops.convex_hull(bm, input=vs)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    if merge:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(merge), verts=bm.verts[:], edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = cl._new_obj(name, bm, mat, smooth=True)
    if bevel:
        rw.add_bevel(o, bevel, segs, bevel_angle, harden=True)
    return o


# ======================================================================================
# Surface work: ray casting, ribbons, cracks, glyphs
# ======================================================================================

def _dir(d):
    """Direction from a vector or an (azimuth, elevation) pair in degrees (azimuth 0 = front -Y,
    90 = the character's left +X, 180 = back)."""
    if len(d) == 2:
        az, el = math.radians(d[0]), math.radians(d[1])
        return V((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    return cl.vec(d).normalized()


def surface_hit(target, origin, direction):
    """(point, normal) where a ray from `origin` along `direction` leaves `target` (world space).
    Casts from outside back toward the origin so it works from inside a closed mesh too."""
    bpy.context.view_layer.update()
    mw = target.matrix_world
    inv = mw.inverted()
    o = cl.vec(origin)
    d = cl.vec(direction).normalized()
    far = o + d * 50.0
    ok, loc, nrm, idx = target.ray_cast(inv @ far, (inv.to_3x3() @ -d).normalized())
    if not ok:
        return None, None
    n = (inv.to_3x3().transposed() @ nrm).normalized()
    return mw @ loc, n


def ribbon(name, pts, normals, width, height=None, mat="M_RuneGlow", segs=6, sink=0.35, taper=(True, True),
           arch=False):
    """Flattened bead along surface points (each with its surface normal). `width` = half width
    across the surface; `height` = half thickness along the normal (default width * 0.7); the bead
    is pushed `sink` x height into the surface. Ends taper to points when `taper` is set.
    arch=True builds only the upper half (an open arch of `segs` faces whose edges stay buried in the
    surface): cheaper, and its gentle facet angles don't draw crease outlines along the bead."""
    n = len(pts)
    if n < 2:
        return None
    if isinstance(width, (int, float)):
        width = [float(width)] * n
    else:
        width = list(width)
    if taper[0]:
        width[0] = 0.0
    if taper[1]:
        width[-1] = 0.0
    rings = []
    for i in range(n):
        p = cl.vec(pts[i])
        nm = cl.vec(normals[i]).normalized()
        a = cl.vec(pts[max(i - 1, 0)])
        b = cl.vec(pts[min(i + 1, n - 1)])
        t = b - a
        t = (t - nm * t.dot(nm))
        if t.length < 1e-9:
            t = nm.orthogonal()
        t.normalize()
        bn = nm.cross(t).normalized()
        w = width[i]
        h = (height if height is not None else max(w, 1e-4) * 0.7)
        if isinstance(h, (list, tuple)):
            h = h[i]
        c = p - nm * (h * sink)
        if w <= 1e-6:
            rings.append(c + nm * (h * 0.2))
            continue
        ring = []
        if arch:
            for k in range(segs + 1):
                ang = math.pi * k / segs
                ring.append(c + bn * (w * math.cos(ang)) + nm * (h * math.sin(ang)))
        else:
            for k in range(segs):
                ang = 2.0 * math.pi * k / segs
                ring.append(c + bn * (w * math.cos(ang)) + nm * (h * math.sin(ang)))
        rings.append(ring)
    if arch:
        return cl.skin(name, rings, mat, cap_start=False, cap_end=False, smooth=True, closed=False)
    return cl.skin(name, rings, mat, cap_start=True, cap_end=True, smooth=True)


def _slerp_dir(a, b, t):
    a = a.normalized()
    b = b.normalized()
    q = a.rotation_difference(b)
    ang = q.angle
    if ang < 1e-6:
        return a.copy()
    q2 = Matrix.Rotation(ang * t, 3, q.axis)
    return (q2 @ a).normalized()


def surface_path(target, center, ctrl, zig=0.0, kinks=1, step_deg=4.0, seed=1):
    """Path over `target`'s surface through control directions (vectors or (az, el) degree pairs)
    seen from `center`. Each control span gets `kinks` extra corner points pushed sideways by up to
    +-`zig` radians (a jagged crack), then every straight run is sampled every `step_deg` degrees so
    the bead hugs facet edges instead of cutting under them. Returns (points, normals)."""
    rnd = random.Random(seed)
    dirs = [_dir(c) for c in ctrl]
    corners = [dirs[0]]
    for i in range(len(dirs) - 1):
        a, b = dirs[i], dirs[i + 1]
        axis = a.cross(b)
        if axis.length < 1e-6:
            axis = a.orthogonal()
        axis.normalize()
        for k in range(1, kinks + 1):
            d = _slerp_dir(a, b, k / (kinks + 1.0))
            if zig:
                sgn = 1.0 if (k + i) % 2 else -1.0
                d = (d + axis * (zig * sgn * (0.5 + 0.5 * rnd.random()))).normalized()
            corners.append(d)
        corners.append(b)
    samples = []
    for i in range(len(corners) - 1):
        a, b = corners[i], corners[i + 1]
        ang = math.degrees(a.angle(b)) if (a - b).length > 1e-9 else 0.0
        n = max(1, int(math.ceil(ang / step_deg)))
        for k in range(n):
            samples.append(_slerp_dir(a, b, k / n))
    samples.append(corners[-1])
    pts, nrms = [], []
    for d in samples:
        p, nm = surface_hit(target, center, d)
        if p is not None:
            pts.append(p)
            nrms.append(nm)
    return pts, nrms


def crack(name, target, center, ctrl, width=0.035, zig=0.06, kinks=1, seed=1, mat="M_RuneGlow",
          branches=(), height=None, sink=0.25, step_deg=4.0, segs=4, arch=True):
    """Jagged glowing crack following `target`'s surface. `ctrl`: control directions from `center`
    (vectors or (az, el) degree pairs). `branches`: list of (fraction_along, [ctrl...], width_scale)
    for side cracks that start on the main crack and taper away. Returns a list of objects."""
    pts, nrms = surface_path(target, center, ctrl, zig, kinks, step_deg, seed)
    out = []
    if len(pts) >= 2:
        m = len(pts)
        wid = [width * (0.35 + 0.65 * max(0.0, math.sin(math.pi * i / (m - 1))) ** 0.6) for i in range(m)]
        hgt = height if height is not None else [w * 0.45 + 0.004 for w in wid]
        out.append(ribbon(name, pts, nrms, wid, hgt, mat, segs, sink, arch=arch))
    for bi, (frac, bctrl, ws) in enumerate(branches):
        if len(pts) < 2:
            break
        i0 = max(0, min(len(pts) - 1, int(round(frac * (len(pts) - 1)))))
        start = (pts[i0] - cl.vec(center)).normalized()
        bp, bn = surface_path(target, center, [start] + list(bctrl), zig, kinks, step_deg, seed + 31 * (bi + 1))
        if len(bp) >= 2:
            m = len(bp)
            wid = [width * ws * (1.0 - 0.8 * i / (m - 1)) for i in range(m)]
            hgt = height if height is not None else [w * 0.45 + 0.004 for w in wid]
            out.append(ribbon(name + "_b%d" % bi, bp, bn, wid, hgt, mat, segs, sink, taper=(False, True), arch=arch))
    return out


GLYPHS = {
    # cartoon rune strokes in a unit cell [-0.5, 0.5]^2 (u right, v up)
    "algiz": [[(0, -0.5), (0, 0.5)], [(0, 0.08), (-0.34, 0.46)], [(0, 0.08), (0.34, 0.46)]],
    "tiwaz": [[(0, -0.5), (0, 0.5)], [(-0.32, 0.16), (0, 0.5), (0.32, 0.16)]],
    "ingwaz": [[(0, 0.5), (0.32, 0), (0, -0.5), (-0.32, 0), (0, 0.5)]],
    "sowilo": [[(-0.22, 0.5), (0.24, 0.16), (-0.24, -0.16), (0.22, -0.5)]],
    "kenaz": [[(0.3, 0.5), (-0.26, 0), (0.3, -0.5)]],
    "eye": [[(-0.45, 0), (-0.2, 0.26), (0.2, 0.26), (0.45, 0), (0.2, -0.26), (-0.2, -0.26), (-0.45, 0)],
            [(0, -0.12), (0, 0.12)]],
    "hagal": [[(-0.24, -0.5), (-0.24, 0.5)], [(0.24, -0.5), (0.24, 0.5)], [(-0.24, 0.18), (0.24, -0.18)]],
    "othala": [[(-0.36, -0.5), (0.28, 0.12), (0, 0.5), (-0.28, 0.12), (0.36, -0.5)]],
    "dagaz": [[(-0.34, -0.5), (-0.34, 0.5), (0.34, -0.5), (0.34, 0.5), (-0.34, -0.5)]],
    "star": [[(0, 0.5), (0, -0.5)], [(-0.43, 0.25), (0.43, -0.25)], [(-0.43, -0.25), (0.43, 0.25)]],
    "choir": [[(-0.3, 0.45), (0, -0.45), (0.3, 0.45)], [(-0.4, 0.05), (0.4, 0.05)]],
}


def surface_glyph(name, target, center, key, face_dir, size, width=0.02, up=(0, 0, 1), mat="M_RuneGlow",
                  height=None, sink=0.25, per_unit=28, segs=4, arch=True):
    """Rune glyph projected onto `target`: the glyph's cell is centred where the ray from `center`
    along `face_dir` hits, spanning `size` metres; strokes follow the surface."""
    fd = _dir(face_dir)
    hit, nrm = surface_hit(target, center, fd)
    if hit is None:
        return []
    # u runs to the viewer's right when looking at the surface (right = up x normal)
    u = cl.vec(up).cross(nrm)
    if u.length < 1e-5:
        u = V((1, 0, 0))
    u.normalize()
    v = nrm.cross(u).normalized()
    out = []
    for si, stroke in enumerate(GLYPHS[key]):
        pts, nrms = [], []
        for (a, b) in zip(stroke[:-1], stroke[1:]):
            pa = hit + u * (a[0] * size) + v * (a[1] * size)
            pb = hit + u * (b[0] * size) + v * (b[1] * size)
            k = max(2, int((pb - pa).length * per_unit) + 1)
            for j in range(k):
                if pts and j == 0:
                    continue
                q = pa.lerp(pb, j / (k - 1))
                p, nm = surface_hit(target, center, q - cl.vec(center))
                if p is not None:
                    pts.append(p)
                    nrms.append(nm)
        if len(pts) >= 2:
            out.append(ribbon("%s_%d" % (name, si), pts, nrms, [width] * len(pts), height, mat, segs, sink,
                              taper=(False, False), arch=arch))
    return out


# ======================================================================================
# Moss
# ======================================================================================

def moss_tuft(name, target, center, face_dirs, size=0.12, seed=1, mats=("GolemMoss", "GolemMossLight"),
              strands=0, strand_len=0.18):
    """Soft moss cushion: for each direction in `face_dirs` (seen from `center`), a flattened blob
    sits on `target`'s surface, with a lighter cap blob; `strands` dangling drips hang from the
    lowest blobs. Returns a list of objects."""
    rnd = random.Random(seed)
    out = []
    lows = []
    for i, fd in enumerate(face_dirs):
        p, nm = surface_hit(target, center, _dir(fd))
        if p is None:
            continue
        s = size * (0.7 + 0.6 * rnd.random())
        F = V((0, 0, 1)).rotation_difference(nm).to_matrix()
        spin = Matrix.Rotation(rnd.uniform(0, math.pi), 3, 'Z')
        out.append(cl.ellipsoid(name + "_b", p + nm * (s * 0.12), (s, s * 0.85, s * 0.42), 10, 5, mats[0], F @ spin))
        out.append(cl.ellipsoid(name + "_c", p + nm * (s * 0.3) + V((0, 0, s * 0.05)), (s * 0.62, s * 0.55, s * 0.32),
                                8, 4, mats[1], F @ spin))
        lows.append((p, nm, s))
    lows.sort(key=lambda t: t[0].z)
    for k in range(min(strands, len(lows))):
        p, nm, s = lows[k]
        base = p + nm * (s * 0.2)
        tip = base + V((0, 0, -strand_len * (0.7 + 0.6 * rnd.random()))) + nm * 0.03
        out.append(cl.sweep(name + "_drip", cl.bezier(base, base + nm * 0.05 + V((0, 0, -0.04)), tip, 5),
                            [s * 0.32, s * 0.28, s * 0.22, s * 0.14, 0.0], 8, mats[0]))
    return out


def _cap_surface(name, target, center, upv, reach, thick, rings, segs, scallop, lobes, drips, rnd, mat, lump=0.35):
    side = upv.orthogonal().normalized()
    fwd = upv.cross(side).normalized()
    ph0 = rnd.random() * 2 * math.pi
    ph1 = rnd.random() * 2 * math.pi
    pole, pn = surface_hit(target, center, upv)
    if pole is None:
        return None
    ring_pts = [pole + pn * thick * (1.0 + lump * 0.5)]
    for r in range(1, rings + 1):
        t = r / rings
        ring = []
        for k in range(segs):
            a = ph0 + 2 * math.pi * k / segs
            lim = reach * (1.0 + scallop * math.sin(lobes * a + rnd.uniform(-0.35, 0.35)))
            for (daz, extra) in drips:
                da = (a - ph0 - math.radians(daz) + math.pi) % (2 * math.pi) - math.pi
                lim += extra * math.exp(-(da / 0.26) ** 2)
            th = math.radians(lim * t)
            d = upv * math.cos(th) + (side * math.cos(a) + fwd * math.sin(a)) * math.sin(th)
            p, nm = surface_hit(target, center, d)
            if p is None:
                p, nm = cl.vec(center) + d * 0.1, d
            if r < rings:
                bump = 1.0 + lump * math.sin(3 * a + ph1) * math.sin(math.pi * t)
                off = thick * (1.0 - t ** 2.5) * bump + 0.006
            else:
                off = -thick * 0.5
            ring.append(p + nm * off)
        ring_pts.append(ring)
    return cl.skin(name, ring_pts, mat, cap_start=False, cap_end=False, smooth=True)


def moss_cap(name, target, center, up=(0, 0, 1), reach=40.0, thick=0.04, rings=4, segs=20, scallop=0.2,
             lobes=5, drips=(), seed=1, mat="GolemMoss", top_mat="GolemMossLight", top=0.5):
    """Moss blanket draped over the part of `target` facing `up` (seen from `center`): a lumpy cap
    that follows the surface out to `reach` degrees from `up`, with a scalloped edge that tucks into
    the rock and optional drips (list of (azimuth_deg, extra_deg); azimuth measured in the cap's own
    frame). A smaller, lighter top layer (`top` x reach) makes it read as painted, layered moss."""
    rnd = random.Random(seed)
    upv = cl.vec(up).normalized()
    out = [_cap_surface(name, target, center, upv, reach, thick, rings, segs, scallop, lobes, drips, rnd, mat)]
    if top_mat and top > 0:
        out.append(_cap_surface(name + "_top", target, center, upv, reach * top, thick * 1.9, max(2, rings - 1),
                                max(10, segs - 6), scallop * 1.3, lobes - 1, (), rnd, top_mat))
    return [o for o in out if o is not None]


# ======================================================================================
# Cloth: robes, hoods, sleeves, trims (cultist and wraith)
# ======================================================================================

FRONT = 1.5 * math.pi   # ring angle of the front (-Y); 0 = +X (left), pi/2 = +Y (back), pi = -X (right)


def ellipse_ring(center, rx, ry, z, segs, folds=0, amp=0.0, phase=0.0, gap=None, zoff=None, rmod=None):
    """Horizontal (folded) ellipse of points. With `gap` (half-angle, radians) the ring is open at the
    front: it runs from the front-left edge of the opening round the back to the front-right edge
    (segs + 1 points). zoff(a, k) and rmod(a) add per-point height offsets / radius factors."""
    cx, cy = center
    pts = []
    if gap is not None:
        a0, a1 = FRONT + gap, FRONT - gap + 2 * math.pi
        angles = [a0 + (a1 - a0) * k / segs for k in range(segs + 1)]
    else:
        angles = [2 * math.pi * k / segs for k in range(segs)]
    for k, a in enumerate(angles):
        m = 1.0 + amp * math.sin(folds * a + phase)
        if rmod:
            m *= rmod(a)
        dz = zoff(a, k) if zoff else 0.0
        pts.append(V((cx + rx * m * math.cos(a), cy + ry * m * math.sin(a), z + dz)))
    return pts


def ragged(depth=0.08, notch=0.015, every=2, seed=1, var=0.6):
    """zoff function for a tattered hem: every `every`-th point drops into a point."""
    rnd = random.Random(seed)
    cache = {}

    def f(a, k):
        if k not in cache:
            if k % every == 0:
                cache[k] = -depth * (1 - var / 2 + var * rnd.random())
            else:
                cache[k] = notch * rnd.random()
        return cache[k]
    return f


def robe_surface(name, levels, segs=32, folds=9, amp=(0.0, 0.05), gap=None, mat=None, inner=None, thick=0.02,
                 hem=None, phase=0.0, cap_top=False):
    """Folded cloth surface of revolution. levels: [(z, rx, ry, cy), ...] from top to bottom.
    amp: fold amplitude at the top / bottom; gap: (top, bottom) half-angles in degrees of a front
    opening (None = closed); hem: zoff function for the last ring (see ragged()).
    Returns (object, rings)."""
    n = len(levels)
    rings = []
    for i, (z, rx, ry, cy) in enumerate(levels):
        t = i / (n - 1)
        a = amp[0] + (amp[1] - amp[0]) * t
        g = None
        if gap is not None:
            g = math.radians(gap[0] + (gap[1] - gap[0]) * t)
        rings.append(ellipse_ring((0.0, cy), rx, ry, z, segs, folds, a, phase, g, hem if i == n - 1 else None))
    o = cl.skin(name, rings, mat, cap_start=cap_top, cap_end=False, smooth=True, closed=(gap is None))
    if thick:
        cl.cloth_shell(o, thick, inner)
    return o, rings


def loop_tube(name, pts, r, segs=6, mat=None, closed=True, max_pts=26):
    """Round trim tube through a list of points (a closed loop by default), resampled to at most
    `max_pts` points to keep it cheap."""
    pts = [cl.vec(p) for p in pts]
    if len(pts) > max_pts:
        step = len(pts) / float(max_pts)
        pts = [pts[int(i * step)] for i in range(max_pts)]
    if closed:
        pts = pts + [pts[0], pts[1]]
    o = cl.sweep(name, pts, r, segs, mat, cap_start=not closed, cap_end=not closed)
    return o


def hood_surface(name, path, radii, segs=22, mat=None, inner=None, thick=0.025, tilt=0.0, side=(1, 0, 0)):
    """Hood / cowl: rings around a centreline `path` (from the face opening to the tip) with radii
    [(rx, rz), ...] (0 = pointed tip). The first ring is the open face rim; `tilt` pushes the top of
    the rim forward (along -path tangent) so the brim overhangs. Returns (object, rim_points)."""
    pts = [cl.vec(p) for p in path]
    n = len(pts)
    u = cl.vec(side).normalized()
    rings = []
    for i, p in enumerate(pts):
        rx, rz = radii[i]
        if rx <= 1e-6:
            rings.append(p)
            continue
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        v = u.cross(t).normalized()
        uu = t.cross(v).normalized()
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            q = p + uu * (rx * math.cos(a)) + v * (rz * math.sin(a))
            if i == 0 and tilt:
                q = q - t * (tilt * math.sin(a))
            ring.append(q)
        rings.append(ring)
    o = cl.skin(name, rings, mat, cap_start=False, cap_end=False, smooth=True)
    if thick:
        cl.cloth_shell(o, thick, inner)
    return o, rings[0]


def sleeve(name, path, radii, segs=16, mat=None, inner=None, thick=0.02, droop=0.05, droop_from=0.55,
           cap_start=True, n=10):
    """Bell sleeve along a smooth path (open cuff at the end). The lower side of the last part of the
    sleeve hangs down by up to `droop` metres so the cuff drapes like cloth. Returns (object, cuff ring)."""
    ctrl = [cl.vec(p) for p in path]
    pts = cl.bezier(ctrl[0], ctrl[1], ctrl[2], n, ctrl[3] if len(ctrl) > 3 else None)
    m = len(pts)
    if callable(radii):
        rad = [radii(i / (m - 1)) for i in range(m)]
    else:
        rad = [radii[0] + (radii[1] - radii[0]) * (i / (m - 1)) ** 1.6 for i in range(m)]
    fr = cl._frames(pts, (0, 0, 1))
    rings = []
    for i, p in enumerate(pts):
        t = i / (m - 1)
        N, B = fr[i]
        f = max(0.0, (t - droop_from) / (1 - droop_from)) ** 1.5
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            off = N * (rad[i] * math.cos(a)) + B * (rad[i] * math.sin(a))
            q = p + off
            if f > 0 and off.z < 0:
                q = q + V((0, 0, -droop * f * (-off.z / rad[i])))
            ring.append(q)
        rings.append(ring)
    o = cl.skin(name, rings, mat, cap_start=cap_start, cap_end=False, smooth=True)
    if thick:
        cl.cloth_shell(o, thick, inner)
    return o, rings[-1]


def grip_hand(name, center, axis, shaft_r, s=1.0, mat=None, palm_side=(1, 0, 0)):
    """Fist closed around a shaft: four finger rolls stacked along `axis` wrapping the shaft, the
    palm on the `palm_side`, and a thumb lying along the shaft. Returns a list of objects."""
    c = cl.vec(center)
    d = cl.vec(axis).normalized()
    e1 = cl.vec(palm_side)
    e1 = (e1 - d * e1.dot(d)).normalized()
    e2 = d.cross(e1).normalized()
    parts = []
    rr = shaft_r + 0.018 * s
    parts.append(cl.ellipsoid(name + "_palm", c + e1 * (rr + 0.012 * s), (0.034 * s, 0.05 * s, 0.03 * s), 12, 6, mat,
                              cl.axes_matrix(e2, d, e1)))
    for k in range(4):
        off = (k - 1.5) * 0.026 * s
        ring = []
        for j in range(7):
            a = math.radians(-20 + 235 * j / 6)
            ring.append(c + d * off + (e1 * math.cos(a) + e2 * math.sin(a)) * rr)
        parts.append(cl.sweep(name + "_f%d" % k, ring, [0.016 * s] * 6 + [0.014 * s], 8, mat, cap_start=True,
                              cap_end=True))
    tb = c + d * (0.05 * s) + (e1 * math.cos(math.radians(-60)) + e2 * math.sin(math.radians(-60))) * rr
    parts.append(cl.capsule(name + "_thumb", tb, tb + d * (0.045 * s) - e1 * (0.006 * s), 0.016 * s, 0.014 * s, 8, 2,
                            mat))
    return parts
