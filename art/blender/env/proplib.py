"""proplib: helpers for the plaza, challenge and shrine props of Batch C (art/blender/env/).

Used by prop_fountain, prop_race_ring, ley_stone, ruin_altar, ruin_pillar, ruin_arch, ruin_wall, prop_target,
prop_challenge_terminal, prop_beacon, prop_goal_pad, prop_bridge (art/blender/env/) and item_ley_cargo
(art/blender/items/).

    import os, sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, <path of art/blender/env>)
    import proplib as PL
    E, rw, V, M = PL.E, PL.rw, PL.V, PL.M

Builds on envlib and rwlib (neither is edited). The rune table, glyph() and sausage() are copies of the helpers in
art/blender/parts/partlib.py, so these scripts don't depend on a module that other artists are editing.

Godot notes (scripts/autoload/material_library.gd) that shaped the accent names below:
* A flat material whose name contains "grass", "leaf", "leaves", "foliage", "flower" or "petal" gets the wind-sway
  foliage shader (which drops emission), so lily pads are "LilyPad" and the lotus is "LotusPink".
* M_* library materials are replaced by name in Godot; flat / glow accents are converted from their base colour,
  emission and alpha, so their Blender values are the real colours.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import envlib as E  # noqa: E402

rw = E.rw
V = Vector

# --------------------------------------------------------------------------------------
# Accent materials (flat colours and glows); envlib's ACCENTS are used as a fallback.
# --------------------------------------------------------------------------------------

ACCENTS = {
    # name: ("flat", colour, roughness, metallic) or ("glow", colour, strength)
    "Moss": ("flat", "6e9f3a", 0.95, 0.0),
    "MossLight": ("flat", "8dbf4e", 0.95, 0.0),
    "WaterLight": ("flat", "8fdcf2", 0.08, 0.0),
    "Foam": ("flat", "eefbff", 0.3, 0.0),
    "LilyPad": ("flat", "4f9e3a", 0.6, 0.0),
    "LilyPadLight": ("flat", "6cbc48", 0.6, 0.0),
    "LotusPink": ("flat", "ff9cc8", 0.6, 0.0),
    "LotusHeart": ("flat", "ffd84a", 0.6, 0.0),
    "Bronze": ("flat", "cd8a48", 0.35, 1.0),
    "Silver": ("flat", "d6dde6", 0.3, 1.0),
    "TealGlow": ("glow", "3ff0d8", 3.0),
    "TealGlowSoft": ("glow", "3ff0d8", 1.5),
    "TealGlowFaint": ("glow", "3ff0d8", 0.9),
    "GoldGlow": ("glow", "ffc94a", 2.0),
    "ScreenGlow": ("glow", "3ee8c8", 1.4),
    "ScreenDark": ("flat", "17323a", 0.25, 0.0),
    "LampGlow": ("glow", "ffcc66", 3.0),
    "Crack": ("flat", "4f4a55", 0.95, 0.0),
}


def reset():
    """rw.reset() plus every accent material created up front, so envlib helpers can take any accent name as a plain
    string. Unused materials have no users: they are neither saved nor exported."""
    sc = rw.reset()
    for name in ACCENTS:
        M(name)
    for name in E.ACCENTS:
        E.M(name)
    E.M("Water")
    return sc


def M(name):
    """Accent material by name (proplib ACCENTS first, then envlib's: Iron, Gold, TargetRed, Water...)."""
    if name in ACCENTS:
        k = ACCENTS[name]
        if k[0] == "glow":
            return rw.glow(name, k[1], k[2])
        return rw.flat(name, k[1], k[2], k[3])
    return E.M(name)


def mat(m):
    """Resolve a material spec: Material objects and 'M_*' library names pass through, accents via M()."""
    if m is None or isinstance(m, bpy.types.Material):
        return m
    if m.startswith("M_"):
        return rw._resolve_mat(m)
    if m in ACCENTS or m in E.ACCENTS or m == "Water":
        return M(m)
    return rw._resolve_mat(m)


def preview_glow(mat_name, base_hex, emit_hex, strength):
    """Previews only: AgX washes bright emission toward white, so a LIBRARY glow (M_RuneGlow, M_Crystal...) gets a
    darker base and a moderate emission to keep its hue in the renders. Godot replaces M_* materials by name, so this
    never changes the game. Don't use it on flat accents: their Blender values ARE the game colours."""
    m = rw._resolve_mat(mat_name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(base_hex)
    b.inputs["Emission Color"].default_value = rw._lin(emit_hex)
    b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = rw._lin(base_hex)[:3] + (m.diffuse_color[3],)
    return m


# --------------------------------------------------------------------------------------
# Orientation helpers
# --------------------------------------------------------------------------------------

def frame_matrix(z_dir, x_hint=None):
    """3x3 rotation whose local Z maps to z_dir (and local X as close as possible to x_hint)."""
    z = V(z_dir).normalized()
    if x_hint is None:
        return V((0, 0, 1)).rotation_difference(z).to_matrix()
    x = V(x_hint)
    x = x - x.dot(z) * z
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
        bpy.context.view_layer.update()      # keep matrix_world current for set_mat_where / bounds
    return o


def obj_from_bm(name, bm, m=None, smooth_angle=60):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m is not None:
        rw.set_mat(o, mat(m))
    if smooth_angle:
        rw.smooth(o, smooth_angle)
    return o


def obox(name, size, loc=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, 0, 1), m=None, bevel=0.0, seg=1, angle=40):
    """Box whose local X runs along x_dir and local Z as close as possible to z_dir (angle-limited chamfer)."""
    o = rw.box(name, size, (0, 0, 0), (0, 0, 0), mat(m))
    x = V(x_dir).normalized()
    z = V(z_dir)
    z = z - z.dot(x) * x
    if z.length < 1e-6:
        z = x.orthogonal()
    z.normalize()
    y = z.cross(x).normalized()
    o.data.transform(Matrix((x, y, z)).transposed().to_4x4())
    o.data.update()
    o.location = loc
    if bevel > 0:
        rw.add_bevel(o, min(bevel, min(size) * 0.45), seg, angle, harden=False)
    return o


def lathe_ax(name, prof, axis=(0, 0, 1), loc=(0, 0, 0), seg=16, m=None, smooth=50, cap_bottom=True, cap_top=True,
             spin=0.0, x_hint=None):
    """rw.lathe of [(r, h), ...] (bottom -> top along local Z), then aimed along `axis` and moved to loc."""
    o = rw.lathe(name, prof, seg, (0, 0, 0), (0, 0, 0), mat(m), None, cap_bottom, cap_top, smooth)
    align(o, axis, loc, x_hint, spin)
    return o


def hoop(name, r_in, r_out, depth, axis=(0, 0, 1), loc=(0, 0, 0), seg=32, m="M_Brass", bevel=0.25, smooth=40):
    """Flat ring (washer / band) with a softly chamfered rectangular section: radii r_in..r_out, `depth` along axis."""
    b = min(r_out - r_in, depth) * bevel
    prof = [(r_in, -depth / 2 + b), (r_in + b, -depth / 2), (r_out - b, -depth / 2), (r_out, -depth / 2 + b),
            (r_out, depth / 2 - b), (r_out - b, depth / 2), (r_in + b, depth / 2), (r_in, depth / 2 - b),
            (r_in, -depth / 2 + b)]
    return lathe_ax(name, prof, axis, loc, seg, m, smooth, False, False)


def place_rel(objs, origin, x_axis, y_axis, z_axis):
    """Move objects built around the world origin into a local frame (columns x_axis, y_axis, z_axis at origin)."""
    R = Matrix((V(x_axis), V(y_axis), V(z_axis))).transposed().to_4x4()
    T = Matrix.Translation(V(origin)) @ R
    for o in objs:
        o.matrix_world = T @ o.matrix_world
        if o.type == 'MESH':
            rw.apply_transform(o)
    return objs


# --------------------------------------------------------------------------------------
# Swept tubes with rounded caps (copied from partlib.sausage)
# --------------------------------------------------------------------------------------

def _perp(d, up):
    d = V(d).normalized()
    up = V(up)
    p = up - up.dot(d) * d
    if p.length < 1e-6:
        p = d.orthogonal()
    return p.normalized()


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


def sausage(name, pts, radius, segs=8, res=3, m=None, caps=(True, True), cap_rings=2, smooth_path=True,
            smooth_angle=70, scale_xy=(1.0, 1.0), up_hint=None):
    """Tube swept along a Catmull-Rom path through `pts`, with round (True), flat (False) or open (None) caps.
    `radius` is a float or a per-point list; scale_xy squashes the section for oval tubes."""
    n = len(pts)
    radii = list(radius) if isinstance(radius, (list, tuple)) else [radius] * n
    Q, Rr = _resample(pts, radii, res, smooth_path)
    k = len(Q)
    T = [(Q[min(i + 1, k - 1)] - Q[max(i - 1, 0)]).normalized() for i in range(k)]
    N = _perp(T[0], up_hint) if up_hint is not None else T[0].orthogonal().normalized()
    bm = bmesh.new()
    rings = []
    sx, sy = scale_xy
    for i in range(k):
        if i > 0:
            N = T[i - 1].rotation_difference(T[i]) @ N
            N = (N - N.dot(T[i]) * T[i]).normalized()
        B = T[i].cross(N).normalized()
        ring = [bm.verts.new(Q[i] + Rr[i] * (math.cos(2 * math.pi * j / segs) * sx * N +
                                              math.sin(2 * math.pi * j / segs) * sy * B)) for j in range(segs)]
        rings.append((ring, N.copy(), B.copy()))
    for i in range(k - 1):
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
        for kk in range(1, cap_rings):
            phi = (math.pi / 2) * kk / cap_rings
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
    cap(k - 1, T[-1], caps[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, m, smooth_angle)


# --------------------------------------------------------------------------------------
# Rune glyphs (cartoon futhark-ish strokes in a unit cell [-0.5, 0.5]^2, u right, v up; copied from partlib)
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
    "star": [[(0, -0.5), (0, 0.5)], [(-0.43, -0.25), (0.43, 0.25)], [(-0.43, 0.25), (0.43, -0.25)]],
    "arrow": [[(0, -0.5), (0, 0.5)], [(-0.3, 0.2), (0, 0.5), (0.3, 0.2)], [(-0.3, -0.2), (0, 0.1), (0.3, -0.2)]],
}
RUNE_KEYS = ("algiz", "sowilo", "ingwaz", "fehu", "tiwaz", "othala", "kenaz", "dagaz", "hagal", "eye")


def glyph(key, center, u_dir, v_dir, size, width, depth, m="M_RuneGlow", name="rune"):
    """Rune made of boxes lying on a surface: u_dir / v_dir span the surface, depth runs along u x v. The strokes
    are centred on the surface (half sunk), so they read as inlaid glowing lines. Returns a list of objects."""
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
            out.append(obox(name, (d.length + width, width, depth), (pa + pb) / 2, d, n, m))
    return out


def glyph_band(center, radius, z, keys, size, width, depth, m="M_RuneGlow", phase=0.0, name="rune"):
    """Upright glyphs around a vertical cylinder of the given surface radius (one per key)."""
    out = []
    c = V(center)
    for i, key in enumerate(keys):
        a = math.radians(phase) + 2 * math.pi * i / len(keys)
        nrm = V((math.cos(a), math.sin(a), 0.0))
        tan = V((-math.sin(a), math.cos(a), 0.0))
        out += glyph(key, c + nrm * radius + V((0, 0, z)), tan, (0, 0, 1), size, width, depth, m, name)
    return out


# --------------------------------------------------------------------------------------
# Lofts (organic stones, cushions)
# --------------------------------------------------------------------------------------

def ring_pts(n, rx, ry, z, c=(0.0, 0.0), p=2.0, phase=0.0, wob=None):
    """n points on a superellipse (p = 2 ellipse, larger p boxier) at height z. wob(angle) -> radial factor offset."""
    pts = []
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(ca) ** (2.0 / p), ca)
        y = ry * math.copysign(abs(sa) ** (2.0 / p), sa)
        f = 1.0 + (wob(a) if wob else 0.0)
        pts.append((c[0] + x * f, c[1] + y * f, z))
    return pts


def loft(name, rings, m=None, cap_bottom=True, cap_top=True, smooth_angle=50, top_point=None):
    """Skin rings of 3D points (closed loops, same count, bottom -> top) into one closed mesh. The top is capped
    with a fan to `top_point` (or the ring centre) so non-planar tops stay clean."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for k in range(len(vr) - 1):
        a, b = vr[k], vr[k + 1]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_bottom:
        bm.faces.new(list(reversed(vr[0])))
    if cap_top:
        ring = vr[-1]
        if top_point is None:
            c = V((0, 0, 0))
            for v in ring:
                c += v.co
            top_point = c / n
        cv = bm.verts.new(top_point)
        for i in range(n):
            bm.faces.new((ring[i], ring[(i + 1) % n], cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, m, smooth_angle)


def surface_hit(o, origin, direction):
    """Ray-cast an object (identity transform) -> (location, normal) or None."""
    bpy.context.view_layer.update()
    ok, loc, nrm, _ = o.ray_cast(V(origin), V(direction).normalized())
    return (loc, nrm) if ok else None


def glyph_on(o, key, toward, z, size, width, depth, m="M_RuneGlow", up=(0, 0, 1), name="rune", from_dist=3.0,
             x=0.0):
    """Project a glyph onto object o's surface: cast from (x, 0, z) + toward * from_dist back toward the axis and
    lay the glyph on the hit point, oriented by the surface normal (its 'up' as close to `up` as possible)."""
    t = V(toward).normalized()
    hit = surface_hit(o, V((x, 0, z)) + t * from_dist, -t)
    if hit is None:
        return []
    loc, n = hit
    u = V(up).cross(n)
    if u.length < 1e-4:
        u = V((1, 0, 0))
    u.normalize()
    v = n.cross(u).normalized()
    return glyph(key, loc, u, v, size, width, depth, m, name)


# --------------------------------------------------------------------------------------
# Stone work (ruins, basins)
# --------------------------------------------------------------------------------------

def rough_block(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m="M_Stone", b=0.05, seed=0, amt=0.03, seg=1,
                lean=(0.0, 0.0), smooth=30):
    """Hand-cut stone block: a box whose eight corners are nudged randomly by up to `amt` (so no two blocks are
    alike), with a chamfered bevel. lean=(dx, dy) shears the top face (weathered, settled blocks)."""
    rnd = random.Random(seed)
    sx, sy, sz = size
    bm = bmesh.new()
    vs = {}
    for ix in (-1, 1):
        for iy in (-1, 1):
            for iz in (-1, 1):
                p = V((ix * sx / 2, iy * sy / 2, iz * sz / 2))
                p += V((rnd.uniform(-amt, amt), rnd.uniform(-amt, amt), rnd.uniform(-amt, amt) * 0.6))
                if iz > 0:
                    p += V((lean[0], lean[1], 0.0))
                vs[(ix, iy, iz)] = bm.verts.new(p)
    F = [((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)),
         ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)), ((1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)),
         ((-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)), ((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1))]
    for f in F:
        bm.faces.new([vs[k] for k in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, m, 0)
    if b > 0:
        md = rw.add_bevel(o, min(b, min(size) * 0.4), seg, 30, harden=False)
        md.use_clamp_overlap = True
    E.place([o], loc, rot)
    rw.smooth(o, smooth)
    return o


def broken_column(name, z0, z_break, r_bottom, r_top, flutes=12, per=4, depth=0.035, amp=0.18, seed=0,
                   high=(1.0, 0.0), high_amt=0.3, levels=4, m="M_Stone", m_break="M_StoneRough", smooth=40):
    """Fluted column shaft from z0 up to a jagged break around z_break (one side `high_amt` higher, toward the
    `high` direction), capped by a rough fracture surface (m_break). Straight taper r_bottom -> r_top.
    Returns (object, top_ring_points)."""
    rnd = random.Random(seed)
    n = flutes * per
    hx, hy = high
    hl = math.hypot(hx, hy) or 1.0
    hx, hy = hx / hl, hy / hl
    jag = jag_profile(n, 0.0, amp, seed, 1)
    tops = []
    for i in range(n):
        a = 2 * math.pi * i / n
        tops.append(z_break + jag[i] + high_amt * (math.cos(a) * hx + math.sin(a) * hy))

    def rad(z):
        t = (z - z0) / max(1e-6, (z_break - z0))
        return r_bottom + (r_top - r_bottom) * min(1.0, max(0.0, t))

    def pt(i, z, scale=1.0):
        a = 2 * math.pi * i / n
        f = 0.5 + 0.5 * math.cos(flutes * a)
        r = (rad(z) - depth * (1.0 - f)) * scale
        return V((r * math.cos(a), r * math.sin(a), z))

    bm = bmesh.new()
    rings = []
    zmin = min(tops)
    for k in range(levels):
        z = z0 + (zmin - 0.05 - z0) * k / max(1, levels - 1)
        rings.append([bm.verts.new(pt(i, z)) for i in range(n)])
    rings.append([bm.verts.new(pt(i, tops[i])) for i in range(n)])
    # rough fracture: an inner ring dipping below the rim, then a centre point
    avg = sum(tops) / n
    inner = []
    for i in range(n):
        p = pt(i, tops[i], 0.55)
        p.z = 0.5 * tops[i] + 0.5 * avg - 0.06 + rnd.uniform(-0.03, 0.03)
        inner.append(bm.verts.new(p))
    centre = bm.verts.new(V((0, 0, avg - 0.1)))
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    top = rings[-1]
    brk = []
    for i in range(n):
        j = (i + 1) % n
        brk.append(bm.faces.new((top[i], top[j], inner[j], inner[i])))
        brk.append(bm.faces.new((inner[i], inner[j], centre)))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, m, smooth)
    if m_break:
        rw.set_mat_where(o, mat(m_break), lambda c, nn: c.z > zmin - 0.06 and nn.z > 0.35)
    return o, [pt(i, tops[i]) for i in range(n)]


def crack_cyl(radius, a0, z0, steps=5, seed=0, dz=0.14, da=0.12, width=0.024, depth=0.03, m="Crack",
              branch=True):
    """A painted zigzag crack running down a vertical cylinder of the given surface radius (strokes half sunk)."""
    rnd = random.Random(seed)
    out = []
    a, z = a0, z0
    pts = [(a, z)]
    for _ in range(steps):
        a += rnd.uniform(-da, da)
        z -= dz * rnd.uniform(0.7, 1.3)
        pts.append((a, z))
    if branch and len(pts) > 3:
        ab, zb = pts[2]
        bp = [(ab, zb), (ab + da * 1.4, zb - dz * 0.9), (ab + da * 1.9, zb - dz * 1.6)]
    else:
        bp = []
    for path, w in ((pts, width), (bp, width * 0.7)):
        for (a1, z1), (a2, z2) in zip(path[:-1], path[1:]):
            p1 = V((radius * math.cos(a1), radius * math.sin(a1), z1))
            p2 = V((radius * math.cos(a2), radius * math.sin(a2), z2))
            am = (a1 + a2) / 2
            nrm = V((math.cos(am), math.sin(am), 0.0))
            out.append(obox("crack", ((p2 - p1).length + w, w, depth), (p1 + p2) / 2, p2 - p1, nrm, m))
    return out


def crack_face(origin, u, v, pts2d, width=0.026, depth=0.03, m="Crack"):
    """A painted crack polyline on a flat face: 2D points (a, b) -> origin + a*u + b*v (strokes half sunk)."""
    o = V(origin)
    u = V(u).normalized()
    v = V(v).normalized()
    n = u.cross(v).normalized()
    out = []
    for (a1, b1), (a2, b2) in zip(pts2d[:-1], pts2d[1:]):
        p1 = o + u * a1 + v * b1
        p2 = o + u * a2 + v * b2
        out.append(obox("crack", ((p2 - p1).length + width, width, depth), (p1 + p2) / 2, p2 - p1, n, m))
    return out


def moss(loc, r=0.25, seed=0, n=3, squash=0.35, m=("Moss", "MossLight"), spread=0.6):
    """Soft moss cushions (squashed low-poly blobs) around loc."""
    rnd = random.Random(seed)
    c = V(loc)
    out = []
    for i in range(n):
        p = c + V((rnd.uniform(-r, r) * spread, rnd.uniform(-r, r) * spread, 0))
        out.append(rw.ico("moss", r * rnd.uniform(0.5, 0.85), 1, tuple(p), (0, 0, rnd.uniform(0, 90)),
                          (1.25, 1.0, squash), M(m[i % len(m)]), None, 40))
    return out


def moss_drape(loc, normal, n=3, size=0.13, drop=0.32, seed=0, m=("Moss", "MossLight")):
    """Moss hanging over an edge: a cushion sitting on the top just behind the edge point `loc`, then blobs
    flattened against the face (outward `normal`) trailing down and shrinking. Protrudes ~0.4 * size past the face."""
    rnd = random.Random(seed)
    nv = V(normal).normalized()
    side = V((0, 0, 1)).cross(nv).normalized()
    cush = rw.ico("moss", size, 1, (0, 0, 0), (0, 0, 0), (1.3, 0.9, 0.5), M(m[0]), None, 40)
    align(cush, (0, 0, 1), None, x_hint=tuple(side))
    cush.location = V(loc) - nv * size * 0.5 + V((0, 0, 0.02))
    out = [cush]
    for i in range(1, n + 1):
        t = i / n
        r = size * (1.0 - 0.45 * t)
        o = rw.ico("moss", r, 1, (0, 0, 0), (0, 0, 0), (1.1, 0.32, 1.25), M(m[i % len(m)]), None, 40)
        align(o, (0, 0, 1), None, x_hint=tuple(side))
        o.location = V(loc) + nv * (r * 0.08) - V((0, 0, drop * t)) + side * rnd.uniform(-0.06, 0.06)
        out.append(o)
    return out


def pebble(loc, r=0.12, seed=0, m="M_StoneRough", squash=0.7):
    rnd = random.Random(seed)
    return rw.ico("pebble", r, 1, tuple(loc), (rnd.uniform(0, 60), rnd.uniform(0, 60), rnd.uniform(0, 90)),
                  (1.0 + rnd.uniform(-0.2, 0.25), 1.0 + rnd.uniform(-0.2, 0.2), squash), mat(m), None, 0)


def jag_profile(n, base, amp, seed=0, smooth=1, bias=None):
    """n heights around a loop: base + random jags of up to `amp` (lightly smoothed). bias(i) adds a slope."""
    rnd = random.Random(seed)
    h = [rnd.uniform(-amp, amp) for _ in range(n)]
    for _ in range(smooth):
        h = [0.25 * h[i - 1] + 0.5 * h[i] + 0.25 * h[(i + 1) % n] for i in range(n)]
    return [base + h[i] + (bias(i) if bias else 0.0) for i in range(n)]


# --------------------------------------------------------------------------------------
# Small details
# --------------------------------------------------------------------------------------

def rivet(loc, normal=(0, 0, 1), r=0.025, h=0.014, m="M_Brass", segs=6, name="rivet"):
    """Dome rivet head standing on a surface with the given outward normal (top at loc + normal * h)."""
    prof = [(r, -h * 0.5), (r, 0.0), (r * 0.72, h * 0.78), (0.0, h)]
    return lathe_ax(name, prof, normal, loc, segs, m, 70, False, True)


def rivet_circle(center, axis, radius, count, r=0.025, h=0.014, m="M_Brass", phase=0.0, face=False, segs=6):
    """Rivets around a circle: on a cylinder (heads point radially out) or on a flat face (face=True)."""
    c = V(center)
    R = frame_matrix(axis)
    n = V(axis).normalized()
    out = []
    for i in range(count):
        a = math.radians(phase) + 2 * math.pi * i / count
        d = R @ V((math.cos(a), math.sin(a), 0.0))
        out.append(rivet(c + d * radius, n if face else d, r, h, m, segs))
    return out


def flat_disc(name, r, loc, seg=32, m=None):
    """Single-sided horizontal disc facing up (water surfaces: no hidden sides or bottom)."""
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0.0))
          for i in range(seg)]
    bm.faces.new(vs)
    o = obj_from_bm(name, bm, m, 0)
    o.location = loc
    return o


def flat_ring(name, r_in, r_out, loc, seg=32, m=None):
    """Single-sided horizontal annulus facing up (inlays lying on a deck: only the top is ever seen)."""
    bm = bmesh.new()
    inner = [bm.verts.new((r_in * math.cos(2 * math.pi * i / seg), r_in * math.sin(2 * math.pi * i / seg), 0.0))
             for i in range(seg)]
    outer = [bm.verts.new((r_out * math.cos(2 * math.pi * i / seg), r_out * math.sin(2 * math.pi * i / seg), 0.0))
             for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
    o = obj_from_bm(name, bm, m, 0)
    o.location = loc
    return o


def coin(loc, r=0.06, tilt=(0.0, 0.0), m="Gold"):
    o = lathe_ax("coin", [(0.0, -0.008), (r, -0.008), (r, 0.008), (r * 0.8, 0.012), (0.0, 0.012)], (0, 0, 1),
                 (0, 0, 0), 10, m, 40, False, False)
    E.place([o], loc, (tilt[0], tilt[1], 0))
    return o


# --------------------------------------------------------------------------------------
# Finish / QA
# --------------------------------------------------------------------------------------

def finish(asset, size, budget, category="env", icon=False, tol=0.05, height_tol=0.12, origin_note=""):
    """E.check (RWCHECK lines) + rw.finish (UVs, .blend, .glb, previews, report)."""
    E.check(asset, size, budget, tol, height_tol, origin_note=origin_note)
    rw.finish(asset, category, previews=E.previews(), icon=icon)


def qa(asset, views=("front",), size=480, objs=None, tag=""):
    """Extra QA renders to /tmp/rwqa/<asset>[_tag]_<view>.png when RW_QA=1 (call after finish)."""
    if not os.environ.get("RW_QA"):
        return
    for v in views:
        rw.render_view(os.path.join("/tmp/rwqa", "%s%s_%s.png" % (asset, ("_" + tag) if tag else "", v)), v, size,
                       False, True, objs)
