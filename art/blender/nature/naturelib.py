"""naturelib: helpers for RuneWire nature (and item) generator scripts.

Builds on rwlib (never edits it). Everything here returns ordinary Blender mesh objects with
clean transforms, so the scripts can keep using rw.join / rw.set_mat / rw.finish.

Main builders
* sweep()        tube along a smooth path with per-ring radii and an optional cross-section
                 shaper (root flares, lobes, twists). Used for trunks, branches, roots, logs.
* fuse()         voxel-remesh + decimate: welds overlapping parts into one clean surface with
                 soft fillets and no hidden interior faces, then trims it to a triangle budget.
* canopy()       puffy cloud-like foliage: rw.blob lumps fused with fuse(), smooth shaded.
* hull_rock()    chunky faceted cartoon rock: convex hull of jittered points, big flat facets,
                 soft bevels (harden normals).
* crystal()      hexagonal crystal prism with a pointed tip (flat shaded).
* blade_bm()     tapered 3-sided grass blade written straight into a bmesh.

Conventions match rwlib: metres, +Z up, front faces -Y, rotations in degrees.
Nature meshes keep their origin at the base centre (0, 0, 0) so model-space height can drive
wind sway in the game shader.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

import rwlib as rw

# --------------------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------------------


def V(p):
    return Vector(p)


def tris(o):
    """Triangle count of one object (modifiers evaluated)."""
    return rw.tri_count([o])


def purge_helpers():
    """Delete rwlib's hidden noise-space empties once their displace modifiers are applied."""
    for o in list(bpy.context.scene.objects):
        if o.get("rw_helper") and o.type == 'EMPTY':
            still_used = any(
                m.type == 'DISPLACE' and m.texture_coords_object == o
                for ob in bpy.context.scene.objects if ob.type == 'MESH' for m in ob.modifiers)
            if not still_used:
                bpy.data.objects.remove(o, do_unlink=True)


def obj_from_bm(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        rw.set_mat(o, mat)
    return o


def shade_smooth_all(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def shade_flat_all(o):
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def finish_extra(asset, category, views=("side", "top"), size=480, focus=None, ground=True):
    """Optional QA renders to /tmp (set RW_QA=1). Never written into the project (runs after
    rw.finish has saved and exported). focus = (suffix, [objs to frame], [objs to hide], view).
    ground=True adds a grass-coloured disc at z=0 (to judge how the base meets the terrain)."""
    if not os.environ.get("RW_QA"):
        return
    vis = [o for o in rw.all_mesh_objects() if not o.hide_render]
    g = None
    if ground:
        mn, mx = rw.bounds(vis)
        rad = max(mx.x - mn.x, mx.y - mn.y) * 1.2 + 1.0
        g = rw.cylinder("QA_Ground", rad, 0.02, 48, (0, 0, -0.01), mat=rw.flat("QA_Grass", "7fb34f"))
    for v in views:
        rw.render_view("/tmp/rwqa/%s/%s_%s.png" % (category, asset, v), v, size, objs=vis)
    for f in (focus or []):
        suffix, objs, hide, view = f
        for o in hide:
            o.hide_render = True
        rw.render_view("/tmp/rwqa/%s/%s_%s.png" % (category, asset, suffix), view, size, objs=objs)
        for o in hide:
            o.hide_render = False
    if g is not None:
        bpy.data.objects.remove(g, do_unlink=True)


# --------------------------------------------------------------------------------------
# Curves
# --------------------------------------------------------------------------------------


def catmull(pts, per_seg=4):
    """Uniform Catmull-Rom through `pts` (Vectors or floats), `per_seg` samples per segment."""
    scalar = not hasattr(pts[0], "__len__")
    P = [float(p) for p in pts] if scalar else [Vector(p) for p in pts]
    if len(P) == 1:
        return P[:]
    ext = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(per_seg):
            t = k / per_seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (3 * p1 - p0 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    return out


def frames(P, up_hint=None):
    """Parallel-transport frames (T, N, B) along polyline P."""
    n = len(P)
    T = []
    for i in range(n):
        if i == 0:
            t = P[1] - P[0]
        elif i == n - 1:
            t = P[-1] - P[-2]
        else:
            t = P[i + 1] - P[i - 1]
        T.append(t.normalized())
    ref = Vector(up_hint) if up_hint is not None else (Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0)))
    N0 = (ref - T[0] * ref.dot(T[0]))
    if N0.length < 1e-6:
        N0 = Vector((0, 1, 0)) - T[0] * T[0].y
    N = [N0.normalized()]
    for i in range(1, n):
        a, b = T[i - 1], T[i]
        axis = a.cross(b)
        if axis.length < 1e-9:
            N.append(N[-1].copy())
        else:
            ang = a.angle(b)
            N.append((Matrix.Rotation(ang, 3, axis.normalized()) @ N[-1]).normalized())
    B = [T[i].cross(N[i]).normalized() for i in range(n)]
    return T, N, B


# --------------------------------------------------------------------------------------
# Sweeps (trunks, branches, roots, logs)
# --------------------------------------------------------------------------------------


def sweep_bm(bm, pts, radii, sides=12, per_seg=4, cap_start=True, cap_end=True, tip=0.0, shaper=None,
             phase=0.0, twist=0.0, up_hint=None):
    """Write a swept tube into `bm`. Returns (rings, tip_vert).

    pts      control points (smooth Catmull-Rom path through them)
    radii    radius at each control point (interpolated the same way)
    tip      >0: close the far end with a pointed tip this far past the last ring
    shaper   f(u, pos, dir, r) -> new radius; u = 0..1 along the path, dir = unit radial direction
    twist    extra rotation of the ring (radians) from start to end (for twisted trunks)
    """
    P = catmull(pts, per_seg)
    R = catmull([float(r) for r in radii], per_seg)
    T, N, B = frames(P, up_hint)
    seg = [0.0]
    for i in range(1, len(P)):
        seg.append(seg[-1] + (P[i] - P[i - 1]).length)
    total = max(seg[-1], 1e-6)
    rings = []
    for i, p in enumerate(P):
        u = seg[i] / total
        ring = []
        for k in range(sides):
            a = phase + twist * u + 2 * math.pi * k / sides
            d = N[i] * math.cos(a) + B[i] * math.sin(a)
            r = max(R[i], 0.002)
            if shaper is not None:
                r = shaper(u, p, d, r)
            ring.append(bm.verts.new(p + d * r))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap_start:
        bm.faces.new(list(reversed(rings[0])))
    tv = None
    if tip > 0:
        tv = bm.verts.new(P[-1] + T[-1] * tip)
        last = rings[-1]
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new((last[k], last[j], tv))
    elif cap_end:
        bm.faces.new(rings[-1])
    return rings, tv


def sweep(name, pts, radii, sides=12, per_seg=4, mat=None, cap_start=True, cap_end=True, tip=0.0, shaper=None,
          phase=0.0, twist=0.0, smooth_angle=None, up_hint=None):
    bm = bmesh.new()
    sweep_bm(bm, pts, radii, sides, per_seg, cap_start, cap_end, tip, shaper, phase, twist, up_hint)
    o = obj_from_bm(name, bm, mat)
    if smooth_angle is None:
        shade_smooth_all(o)
    elif smooth_angle:
        rw.smooth(o, smooth_angle)
    return o


def root_angles(n=5, seed=0, jitter=0.3, a0=None):
    """Evenly spread root headings (radians around Z) with a little jitter."""
    rng = random.Random(seed)
    a0 = rng.uniform(0, 2 * math.pi) if a0 is None else a0
    return [a0 + 2 * math.pi * k / n + rng.uniform(-jitter, jitter) for k in range(n)]


def root_shaper(angles, strength=0.7, height=1.0, seed=0, sharp=4.0, ground=0.0, foot=0.18):
    """Cross-section shaper that flares the base of a trunk into lobes at the given root headings
    (use the same `angles` as root_sweeps so the lobes run into the roots). Works on the world
    angle around Z, so it is independent of the sweep frame."""
    if isinstance(angles, int):
        angles = root_angles(angles, seed)
    rng = random.Random(seed + 101)
    amps = [strength * rng.uniform(0.75, 1.2) for _ in angles]
    hts = [height * rng.uniform(0.8, 1.2) for _ in angles]

    def f(u, p, d, r):
        phi = math.atan2(d.y, d.x)
        h = p.z - ground
        bump = 0.0
        for a, amp, ht in zip(angles, amps, hts):
            fall = max(0.0, 1.0 - max(h, 0.0) / ht)
            fall = fall * fall * (3 - 2 * fall)            # smoothstep
            c = max(0.0, math.cos(phi - a))
            bump += amp * fall * (c ** sharp)
        ft = max(0.0, 1.0 - max(h, 0.0) / (height * 0.8))   # general wider foot
        return r * (1.0 + bump + foot * strength * ft * ft)
    return f


def root_sweeps(n=5, seed=0, top=1.0, reach=1.3, r_top=0.3, r_tip=0.07, start_r=0.12, depth=-0.3, sides=8,
                mat="M_Bark", angle0=None, name="root", reach_jitter=0.25, mid=(0.5, 0.42, 0.8, 0.08),
                taper=(0.82, 0.55)):
    """Buttress roots: tubes that start inside the trunk at height `top`, arch outward and dive into
    the ground at radius `reach`. Fuse them with the trunk (nl.fuse) for soft junctions.
    `n` is a count or a list of headings (radians, e.g. from root_angles()).
    mid = (radial frac 1, height frac 1, radial frac 2, height 2) of the two inner control points."""
    rng = random.Random(seed)
    angles = n if isinstance(n, (list, tuple)) else root_angles(n, seed, 0.3, angle0)
    out = []
    if mid == "fillet":
        # The root's top edge follows a concave curve (top * (1-s)^2) so it melts into the ground
        # like a fillet instead of standing on it like a stilt.
        for k, a in enumerate(angles):
            rc = reach * rng.uniform(1 - reach_jitter, 1 + reach_jitter * 0.6)
            tp = top * rng.uniform(0.85, 1.12)
            rr = r_top * rng.uniform(0.85, 1.1)
            c, s_ = math.cos(a), math.sin(a)
            pts, radii = [], []
            for s in (0.0, 0.25, 0.5, 0.75, 1.0, 1.12):
                rad = start_r + s * (rc - start_r)
                r = max(r_tip, rr * (1 - 0.62 * min(s, 1.0)))
                z = tp * max(0.0, 1 - s) ** 2 - r * (1.0 + 0.6 * max(0.0, s - 0.9))
                pts.append((rad * c, rad * s_, max(z, depth)))
                radii.append(r)
            out.append(sweep("%s%d" % (name, k), pts, radii, sides=sides, per_seg=2, mat=mat, cap_start=True,
                             cap_end=True))
        return out
    for k, a in enumerate(angles):
        rc = reach * rng.uniform(1 - reach_jitter, 1 + reach_jitter * 0.6)
        tp = top * rng.uniform(0.85, 1.12)
        c, s = math.cos(a), math.sin(a)
        pts = [(start_r * c, start_r * s, tp),
               (mid[0] * rc * c, mid[0] * rc * s, tp * mid[1]),
               (mid[2] * rc * c, mid[2] * rc * s, mid[3]),
               (rc * c, rc * s, depth)]
        rr = r_top * rng.uniform(0.85, 1.1)
        out.append(sweep("%s%d" % (name, k), pts, [rr, rr * taper[0], rr * taper[1], r_tip], sides=sides, per_seg=3,
                         mat=mat, cap_start=True, cap_end=True))
    return out


def drop_small_islands(o, min_verts=40):
    """Remove loose fragments (remesh/decimate leftovers) smaller than `min_verts` vertices."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    kill = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, island = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            island.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        if len(island) < min_verts:
            kill.extend(island)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    return len(kill)


def lumpy_shaper(amount=0.08, freq=1.6, seed=0, base=None):
    """Gentle organic wobble on a tube (for gnarled trunks and logs)."""
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))

    def f(u, p, d, r):
        n = noise.noise(p * freq + d * 0.6 + off)
        rr = r * (1.0 + amount * n * 2.0)
        return base(u, p, d, rr) if base else rr
    return f


# --------------------------------------------------------------------------------------
# Remesh / decimate
# --------------------------------------------------------------------------------------


def remesh(o, voxel=0.05, smooth_iters=0, smooth_factor=0.5):
    m = o.modifiers.new("Remesh", 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = voxel
    m.adaptivity = 0.0
    m.use_smooth_shade = True
    rw.apply_modifiers(o)
    if smooth_iters:
        s = o.modifiers.new("Smooth", 'SMOOTH')
        s.factor = smooth_factor
        s.iterations = smooth_iters
        rw.apply_modifiers(o)
    return o


def decimate(o, target_tris):
    cur = tris(o)
    if cur <= target_tris:
        return o
    for _ in range(3):
        m = o.modifiers.new("Decimate", 'DECIMATE')
        m.decimate_type = 'COLLAPSE'
        m.ratio = max(0.0005, target_tris / float(cur))
        m.use_collapse_triangulate = True
        rw.apply_modifiers(o)
        cur = tris(o)
        if cur <= target_tris * 1.02:
            break
    return o


def fuse(o, voxel, target_tris, smooth_iters=2, smooth_factor=0.5):
    """Voxel-remesh `o` into one watertight surface, relax it a little, decimate to budget."""
    remesh(o, voxel, smooth_iters, smooth_factor)
    drop_small_islands(o, 60)
    decimate(o, target_tris)
    drop_small_islands(o, 12)
    shade_smooth_all(o)
    return o


def clip_below(o, z):
    """Delete geometry below height z (world) and leave the cut open (used under ground)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(o.data)
    bm.free()
    return o


# --------------------------------------------------------------------------------------
# Foliage
# --------------------------------------------------------------------------------------


def canopy(name, blobs, mat="M_Leaves", voxel=0.08, target_tris=2400, noise_amt=0.18, noise_size=1.1, seed=1,
           smooth_iters=2, subdiv=3, squash_bottom=None):
    """Puffy cloud foliage. `blobs` = [(center, size), ...] or [(center, size, rot_deg)].
    The lumps are rw.blob()s (low noise), joined and fused into one smooth surface."""
    parts = []
    for i, b in enumerate(blobs):
        c, s = b[0], b[1]
        r = b[2] if len(b) > 2 else (0, 0, (i * 47) % 360)
        parts.append(rw.blob("%s_lump%d" % (name, i), s, c, r, mat, subdiv=subdiv, noise=noise_amt,
                             noise_size=noise_size, seed=seed + i * 3, smooth_angle=0))
    o = rw.join(parts, name, origin=(0, 0, 0))
    purge_helpers()
    if squash_bottom is not None:
        # flatten the underside a little below a height (cartoon trees have a flatter belly)
        zb, k = squash_bottom
        for v in o.data.vertices:
            if v.co.z < zb:
                v.co.z = zb - (zb - v.co.z) * k
    fuse(o, voxel, target_tris, smooth_iters)
    return o


PINE_TOP = [(0.0, 0.0), (0.2, 0.1), (0.42, 0.27), (0.63, 0.49), (0.81, 0.72), (0.93, 0.89), (0.995, 1.0)]
PINE_UNDER = [(0.95, 1.12), (0.72, 1.04), (0.42, 0.88), (0.14, 0.75), (0.0, 0.73)]


def scallop(a, lobes, phase=0.0, roundness=0.55):
    """0..1 lobe profile: wide rounded humps with crisp notches between them."""
    return abs(math.cos((lobes * a + phase) * 0.5)) ** roundness


def pine_tier_bm(bm, center, z_rim, z_apex, radius, lobes=8, droop=0.14, lobe_amp=0.12, phase=0.0,
                 seg_per_lobe=6, apex_offset=(0, 0), tilt=(0.0, 0.0)):
    """One droopy cone tier of a cartoon pine, written into `bm` as a closed surface.
    The rim is scalloped into `lobes` that hang down by `droop` x tier height."""
    H = z_apex - z_rim
    cx, cy = center
    n = lobes * seg_per_lobe
    prof = PINE_TOP + PINE_UNDER
    rings = []
    tip_top = None
    tip_bot = None
    for pi, (rf, df) in enumerate(prof):
        if rf <= 1e-6:
            # collapse to a single vertex on the axis
            z = z_apex - df * H
            off = Vector(apex_offset) * (1 - df) if pi == 0 else Vector((0, 0))
            v = bm.verts.new((cx + off.x, cy + off.y, z))
            if pi == 0:
                tip_top = v
            else:
                tip_bot = v
            rings.append(None)
            continue
        ring = []
        rimness = min(1.0, rf) ** 3                      # lobes only matter near the rim
        for k in range(n):
            a = 2 * math.pi * k / n
            lobe = scallop(a, lobes, phase)
            r = radius * rf * (1 + lobe_amp * (lobe - 0.6) * rimness)
            z = z_apex - df * H - droop * H * lobe * rimness
            off = Vector(apex_offset) * (1 - min(df, 1.0))
            x = cx + off.x + r * math.cos(a)
            y = cy + off.y + r * math.sin(a)
            # tiny tilt so tiers do not look machine-stacked
            z += tilt[0] * (x - cx) + tilt[1] * (y - cy)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    # faces: walk the profile; top part runs outward, underside runs back inward
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if a is None and b is not None:
            for k in range(n):
                bm.faces.new((tip_top, b[k], b[(k + 1) % n]))
        elif a is not None and b is None:
            for k in range(n):
                bm.faces.new((a[k], tip_bot, a[(k + 1) % n]))
        elif a is not None and b is not None:
            for k in range(n):
                j = (k + 1) % n
                bm.faces.new((a[k], b[k], b[j], a[j]))
    return bm


# --------------------------------------------------------------------------------------
# Rocks
# --------------------------------------------------------------------------------------


def _fib_dirs(n, rng, jitter=0.35):
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        th = ga * i
        d = Vector((math.cos(th) * r, math.sin(th) * r, z))
        d += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
        out.append(d.normalized())
    return out


def hull_rock_bm(size=(2.0, 1.6, 1.3), seed=0, n_points=16, jitter=0.35, rmin=0.82, flat_bottom=0.0,
                 dissolve_deg=9.0, top_bias=0.0, center=(0, 0, 0), twist_deg=0.0):
    """Convex-hull rock in a bmesh: big flat facets. `flat_bottom` (0..1) cuts the underside flat at
    that fraction of the half-height below the centre. Returns the bmesh."""
    rng = random.Random(seed)
    sx, sy, sz = (s / 2.0 for s in size)
    bm = bmesh.new()
    for d in _fib_dirs(n_points, rng, jitter):
        if top_bias and d.z > 0:
            d = Vector((d.x * (1 - top_bias * d.z), d.y * (1 - top_bias * d.z), d.z)).normalized()
        r = rng.uniform(rmin, 1.0)
        bm.verts.new((d.x * sx * r, d.y * sy * r, d.z * sz * r))
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    unused = list({v for v in res.get("geom_interior", []) + res.get("geom_unused", [])
                   if isinstance(v, bmesh.types.BMVert) and v.is_valid})
    if unused:
        bmesh.ops.delete(bm, geom=unused, context='VERTS')
    if flat_bottom:
        zc = -sz * flat_bottom
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, zc), plane_no=(0, 0, 1),
                                     clear_inner=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            bmesh.ops.edgeloop_fill(bm, edges=edges)
    if dissolve_deg:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:], edges=bm.edges[:])
    if twist_deg:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(twist_deg), 3, 'Z'))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=Vector(center))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def hull_rock(name, size=(2.0, 1.6, 1.3), loc=(0, 0, 0), seed=0, n_points=16, jitter=0.35, rmin=0.82,
              flat_bottom=0.0, dissolve_deg=9.0, bevel=0.06, segments=2, mat="M_StoneRough", top_bias=0.0,
              twist_deg=0.0, bevel_angle=25.0):
    bm = hull_rock_bm(size, seed, n_points, jitter, rmin, flat_bottom, dissolve_deg, top_bias, loc, twist_deg)
    o = obj_from_bm(name, bm, mat)
    shade_flat_all(o)
    if bevel:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width = bevel
        m.segments = segments
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(bevel_angle)
        m.harden_normals = True
        m.use_clamp_overlap = True
        m.profile = 0.6
    return o


# --------------------------------------------------------------------------------------
# Crystals
# --------------------------------------------------------------------------------------


def crystal_bm(bm, base, direction, length, radius, sides=6, tip_frac=0.32, base_frac=0.75, spin=0.0,
               cap_base=True):
    """Hexagonal crystal: slightly flared prism + pointed tip. Written into `bm`."""
    d = Vector(direction).normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
    n = (ref - d * ref.dot(d)).normalized()
    b = d.cross(n)
    base = Vector(base)
    body = length * (1 - tip_frac)
    r0 = radius * base_frac
    ring0, ring1 = [], []
    for k in range(sides):
        a = spin + 2 * math.pi * k / sides
        dirv = n * math.cos(a) + b * math.sin(a)
        ring0.append(bm.verts.new(base + dirv * r0))
        ring1.append(bm.verts.new(base + d * body + dirv * radius))
    tipv = bm.verts.new(base + d * length)
    for k in range(sides):
        j = (k + 1) % sides
        bm.faces.new((ring0[k], ring0[j], ring1[j], ring1[k]))
        bm.faces.new((ring1[k], ring1[j], tipv))
    if cap_base:
        bm.faces.new(list(reversed(ring0)))
    return tipv


# --------------------------------------------------------------------------------------
# Grass blades
# --------------------------------------------------------------------------------------


def blade_bm(bm, base, heading, height, width, lean=0.25, bend=0.35, segs=3, thick=0.35):
    """Tapered 3-sided blade, curving outward along `heading` (radians around Z).
    `lean` = outward offset of the tip as a fraction of height, `bend` = extra droop at the top."""
    base = Vector(base)
    out = Vector((math.cos(heading), math.sin(heading), 0))
    side = Vector((-out.y, out.x, 0))
    pts = []
    for i in range(segs + 1):
        t = i / (segs + 1)
        # quadratic outward curve that droops near the top
        off = out * (height * (lean * t + bend * t * t * t))
        z = height * (t - 0.18 * bend * t * t * t)
        pts.append(base + off + Vector((0, 0, z)))
    tipt = 1.0
    tip = base + out * (height * (lean + bend)) + Vector((0, 0, height * (1 - 0.18 * bend)))
    rings = []
    for i, p in enumerate(pts):
        t = i / (segs + 1)
        w = width * (1 - t) ** 0.8
        # cross-section: left edge, right edge, ridge (behind, toward the clump centre)
        left = bm.verts.new(p + side * w)
        right = bm.verts.new(p - side * w)
        ridge = bm.verts.new(p - out * (w * thick))
        rings.append((left, right, ridge))
    tv = bm.verts.new(tip)
    # windings give outward normals: front faces +out, the two back faces -out +-side
    for i in range(len(rings) - 1):
        l0, r0, g0 = rings[i]
        l1, r1, g1 = rings[i + 1]
        bm.faces.new((r0, l0, l1, r1))
        bm.faces.new((g0, r0, r1, g1))
        bm.faces.new((l0, g0, g1, l1))
    l, r, g = rings[-1]
    bm.faces.new((r, l, tv))
    bm.faces.new((g, r, tv))
    bm.faces.new((l, g, tv))
    return tv


def crystal_cluster_bm(bm, center, main_dir, n=6, length=(0.5, 1.2), radius=(0.1, 0.2), spread=0.55, seed=0,
                       sink=0.15, sides=6, min_z=-1.0):
    """A burst of hexagonal crystals growing from `center` around `main_dir` (biggest one first,
    pointing closest to main_dir). Bases are sunk `sink` x length back into the anchor."""
    rng = random.Random(seed)
    md = Vector(main_dir).normalized()
    c = Vector(center)
    for i in range(n):
        if i == 0:
            d = md.copy()
            L = length[1]
            R = radius[1]
        else:
            jit = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            d = (md + jit * spread * (1.0 + 0.4 * rng.random())).normalized()
            if d.z < min_z:
                d.z = min_z
                d.normalize()
            t = rng.random()
            L = length[0] + (length[1] - length[0]) * t * 0.85
            R = radius[0] + (radius[1] - radius[0]) * t
        crystal_bm(bm, c - d * L * sink, d, L, R, sides=sides, tip_frac=rng.uniform(0.26, 0.36),
                   base_frac=0.7, spin=rng.uniform(0, 1.0))
    return bm


def chisel_bm(bm, n_cuts=6, seed=0, depth=(0.12, 0.3), size=(1, 1, 1), keep_bottom=True, min_up=-0.3):
    """Slice `n_cuts` random planes off a convex bmesh (each leaves one big flat facet).
    depth = fraction of the half-size cut away along each plane normal."""
    rng = random.Random(seed)
    sx, sy, sz = (s / 2.0 for s in size)
    for _ in range(n_cuts):
        nrm = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(min_up, 1.0)))
        if nrm.length < 0.2:
            continue
        nrm.normalize()
        # support distance of an ellipsoid along nrm, then cut a fraction of it away
        sup = math.sqrt((nrm.x * sx) ** 2 + (nrm.y * sy) ** 2 + (nrm.z * sz) ** 2)
        co = nrm * sup * (1 - rng.uniform(*depth))
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=nrm, clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            try:
                bmesh.ops.edgeloop_fill(bm, edges=edges)
            except Exception:
                bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def rock(name, size=(2.0, 1.6, 1.3), loc=(0, 0, 0), seed=0, n_points=40, jitter=0.3, rmin=0.9, cuts=7,
         cut_depth=(0.1, 0.28), sink=0.15, dissolve_deg=4.0, bevel=0.06, segments=2, mat="M_StoneRough",
         twist_deg=0.0, min_up=-0.3, top_flat=0.0):
    """Chunky cartoon rock: round-ish hull, chiselled by random planes into big flat facets, bottom
    cut flat `sink` below the origin height, soft bevels with hardened normals (flat facets)."""
    bm = hull_rock_bm(size, seed, n_points, jitter, rmin, 0.0, 0.0, 0.0, (0, 0, 0), 0.0)
    chisel_bm(bm, cuts, seed + 1000, cut_depth, size, min_up=min_up)
    if top_flat:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, size[2] / 2 * (1 - top_flat)),
                                     plane_no=(0.08, -0.05, 1.0), clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            bmesh.ops.edgeloop_fill(bm, edges=edges)
    if dissolve_deg:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:], edges=bm.edges[:])
    if twist_deg:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(twist_deg), 3, 'Z'))
    # sit the rock on the ground: lowest point at -sink after trimming a flat base
    zmin = min(v.co.z for v in bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=Vector((loc[0], loc[1], loc[2] - zmin - size[2] * 0.12 - sink)))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, loc[2] - sink), plane_no=(0, 0, 1),
                                 clear_inner=True)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges:
        bmesh.ops.edgeloop_fill(bm, edges=edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj_from_bm(name, bm, mat)
    shade_flat_all(o)
    if bevel:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width = bevel
        m.segments = segments
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(20)
        m.harden_normals = True
        m.use_clamp_overlap = True
    return o
