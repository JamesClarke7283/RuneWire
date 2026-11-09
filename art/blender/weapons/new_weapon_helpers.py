"""new_weapon_helpers: extra shape helpers for the second batch of first-person weapons
(vm_scattergun, vm_tesla_lance, vm_thunder_wrench).

Built on glove.py / partlib.py / rwlib.py, which are shared and must not be edited. Everything works in world
space and metres; user-facing angles are in degrees. Every helper returns a new object or a list of objects
ready to be joined with rw.join().

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import new_weapon_helpers as nw
    glove, pl, rw, V = nw.glove, nw.pl, nw.rw, nw.V
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402

pl = glove.pl
rw = glove.rw
V = Vector

# lightning-bolt outline in a unit cell (s across, t along; the bolt points toward -t)
BOLT = [(0.0, 0.5), (-0.2, -0.04), (-0.02, -0.04), (-0.2, -0.5), (0.24, 0.06), (0.06, 0.06), (0.28, 0.5)]


# --------------------------------------------------------------------------------------
# Frames
# --------------------------------------------------------------------------------------

def basis(z_dir, x_hint=None):
    """Orthonormal (x, y, z) with z along z_dir and x as close as possible to x_hint."""
    M = pl.frame_matrix(z_dir, x_hint)
    return V(M.col[0]), V(M.col[1]), V(M.col[2])


def uv_frame(u, v):
    """Orthonormal (u, v, n) from two in-plane directions; n = u x v is the plane normal."""
    u = V(u).normalized()
    v = V(v)
    v = (v - v.dot(u) * u).normalized()
    return u, v, u.cross(v)


def _orient_bm(bm, u, v):
    u, v, n = uv_frame(u, v)
    M = Matrix((u, v, n)).transposed().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)


# --------------------------------------------------------------------------------------
# 2D outlines
# --------------------------------------------------------------------------------------

def rounded_poly(pts, radii, steps=4):
    """Round the corners of a simple polygon. radii: one radius per vertex (or a single float).
    Works for convex and concave corners; radii are clamped to fit the neighbouring edges."""
    n = len(pts)
    P = [V((p[0], p[1], 0.0)) for p in pts]
    R = list(radii) if isinstance(radii, (list, tuple)) else [radii] * n
    out = []
    for i in range(n):
        a, p, b = P[i - 1], P[i], P[(i + 1) % n]
        r = R[i]
        if r <= 0:
            out.append((p.x, p.y))
            continue
        d1 = (a - p)
        d2 = (b - p)
        l1, l2 = d1.length, d2.length
        d1.normalize()
        d2.normalize()
        cosang = max(-1.0, min(1.0, d1.dot(d2)))
        th = math.acos(cosang)
        if th < 1e-3 or th > math.pi - 1e-3:
            out.append((p.x, p.y))
            continue
        t = r / math.tan(th / 2)
        t = min(t, 0.48 * l1, 0.48 * l2)
        r_eff = t * math.tan(th / 2)
        bis = (d1 + d2).normalized()
        c = p + bis * (r_eff / math.sin(th / 2))
        s0 = p + d1 * t
        s1 = p + d2 * t
        a0 = math.atan2(s0.y - c.y, s0.x - c.x)
        a1 = math.atan2(s1.y - c.y, s1.x - c.x)
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(steps + 1):
            aa = a0 + da * k / steps
            out.append((c.x + r_eff * math.cos(aa), c.y + r_eff * math.sin(aa)))
    return out


def ribbon_poly(centre, half_w, taper=(0.3, 0.3)):
    """Outline of a constant-width ribbon following a 2D polyline (mitred corners, narrowed ends):
    zigzag sparks and lightning arcs. Returns [(s, t), ...]."""
    P = [V((p[0], p[1], 0.0)) for p in centre]
    n = len(P)
    left, right = [], []
    for i in range(n):
        if i in (0, n - 1):
            d = (P[1] - P[0]) if i == 0 else (P[-1] - P[-2])
            d.normalize()
            nrm = V((-d.y, d.x, 0.0))
            w = half_w * (taper[0] if i == 0 else taper[1])
        else:
            d0 = (P[i] - P[i - 1]).normalized()
            d1 = (P[i + 1] - P[i]).normalized()
            n0 = V((-d0.y, d0.x, 0.0))
            n1 = V((-d1.y, d1.x, 0.0))
            nrm = (n0 + n1).normalized()
            w = half_w / max(0.35, nrm.dot(n0))
        left.append(P[i] + nrm * w)
        right.append(P[i] - nrm * w)
    return [(p.x, p.y) for p in left + right[::-1]]


def slab(name, pts, depth, center=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0), mat=None, bevel=0.0, segments=2,
         angle=40.0, smooth_angle=35):
    """Extrude a simple 2D outline [(s, t), ...] (s along u, t along v) by `depth` along n = u x v,
    centred on `center`. Optional bevel modifier (kept live until join)."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, -depth / 2)) for (x, y) in pts]
    top = [bm.verts.new((x, y, depth / 2)) for (x, y) in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _orient_bm(bm, u, v)
    o = pl.obj_from_bm(name, bm, mat, 0, loc=center)
    if bevel > 0:
        m = rw.add_bevel(o, bevel, segments, angle)
        m.harden_normals = False
    rw.smooth(o, smooth_angle)
    return o


# --------------------------------------------------------------------------------------
# Mechanical parts
# --------------------------------------------------------------------------------------

def gear(name, r_tip, teeth, thick, axis=(0, 0, 1), center=(0, 0, 0), mat="M_Brass", depth=None, r_hole=0.0,
         chamfer=0.0, spin=0.0, x_hint=None, smooth_angle=30):
    """Chunky gear in the plane perpendicular to `axis`: trapezoid teeth, an optional centre hole (r_hole)
    and an optional chamfer around the toothed rim on both faces."""
    depth = depth if depth is not None else r_tip * 0.18
    r_root = r_tip - depth
    N = teeth * 4
    sp = math.radians(spin)

    def contour(dr):
        pts = []
        for i in range(N):
            a = sp + 2 * math.pi * i / N
            r = (r_tip if i % 4 in (1, 2) else r_root) - dr
            pts.append((r * math.cos(a), r * math.sin(a)))
        return pts

    h = thick / 2
    if chamfer > 0:
        levels = [(contour(chamfer), -h), (contour(0), -h + chamfer), (contour(0), h - chamfer),
                  (contour(chamfer), h)]
    else:
        levels = [(contour(0), -h), (contour(0), h)]
    bm = bmesh.new()
    rings = [[bm.verts.new((x, y, z)) for (x, y) in pts] for (pts, z) in levels]
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(N):
            j = (i + 1) % N
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if r_hole > 0:
        ib = [bm.verts.new((r_hole * math.cos(sp + 2 * math.pi * i / N), r_hole * math.sin(sp + 2 * math.pi * i / N),
                            -h)) for i in range(N)]
        it = [bm.verts.new((v.co.x, v.co.y, h)) for v in ib]
        for i in range(N):
            j = (i + 1) % N
            bm.faces.new((rings[0][j], rings[0][i], ib[i], ib[j]))
            bm.faces.new((rings[-1][i], rings[-1][j], it[j], it[i]))
            bm.faces.new((ib[i], it[i], it[j], ib[j]))
    else:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=pl.frame_matrix(axis, x_hint).to_4x4(), verts=bm.verts)
    return pl.obj_from_bm(name, bm, mat, smooth_angle, loc=center)


def spoked_gear(name, r_tip, teeth, thick, axis, center, mat="M_Brass", hub_mat="M_Steel", spokes=5, rim=None,
                depth=None, spin=0.0, x_hint=None, bolt=True, chamfer=0.0, spoke_w=None, back_nut=False):
    """Gear wheel with a toothed rim, a raised hub, `spokes` flat spokes and a hex bolt on the front face
    (the face pointing along `axis`). Returns a list of objects."""
    depth = depth if depth is not None else r_tip * 0.18
    rim = rim if rim is not None else max(0.007, r_tip * 0.2)
    r_hole = r_tip - depth - rim
    ax = V(axis).normalized()
    c = V(center)
    parts = [gear(name, r_tip, teeth, thick, ax, c, mat, depth, r_hole, chamfer, spin, x_hint)]
    hub_r = max(0.009, r_hole * 0.4)
    parts.append(pl.disc(name + "_hub", hub_r, thick * 1.25, ax, c, mat, 16, 0.35))
    x, y, _ = basis(ax, x_hint)
    sw = spoke_w if spoke_w is not None else max(0.008, r_tip * 0.17)
    for k in range(spokes):
        a = math.radians(spin + 90 + 360.0 * k / spokes)
        d = x * math.cos(a) + y * math.sin(a)
        p0 = c + d * (hub_r * 0.5)
        p1 = c + d * (r_hole + rim * 0.5)
        parts.append(pl.obox(name + "_spoke", ((p1 - p0).length, sw, thick * 0.7), (p0 + p1) / 2, d, ax, mat,
                             rounded=min(0.003, sw * 0.3), segments=1))
    if bolt:
        parts.append(pl.bolt(c + ax * (thick * 0.62), ax, hub_r * 0.55, hub_r * 0.42, hub_mat, name + "_bolt"))
    if back_nut:
        parts.append(pl.bolt(c - ax * (thick * 0.62), -ax, hub_r * 0.55, hub_r * 0.42, hub_mat, name + "_nut"))
    return parts


def rack(name, length, height, thick, teeth, tooth_h, center, along, up, mat="M_Steel", bevel=0.002):
    """Toothed rack bar: `length` along `along`, flat bottom, teeth on the `up` side."""
    L, H = length, height
    p = L / teeth
    pts = [(-L / 2, -H / 2), (L / 2, -H / 2), (L / 2, H / 2)]
    for k in range(teeth):
        x0 = L / 2 - k * p
        pts += [(x0 - p * 0.18, H / 2 + tooth_h), (x0 - p * 0.52, H / 2 + tooth_h), (x0 - p * 0.7, H / 2)]
    pts.append((-L / 2, H / 2))
    return slab(name, pts, thick, center, along, up, mat, bevel, 1, 40, 30)


def stud(loc, normal, r=0.0065, h=0.0045, mat="M_Brass", segs=6, name="stud"):
    """Low-poly dome rivet head (open, slightly sunk base): 18 triangles with 6 segments."""
    prof = [(r, -0.0015), (r * 0.82, h * 0.6), (0.0, h)]
    return pl.lathe_axis(name, prof, normal, loc, segs, mat, False, True, 70)


def screw(loc, normal, r=0.007, mat="M_Steel", slot_dir=None, slot_mat="ScrewSlot", name="screw"):
    """Slotted dome screw head standing on a surface (a dark slot bar across the dome)."""
    n = V(normal).normalized()
    head = stud(loc, n, r, r * 0.55, mat, 8, name)
    sd = V(slot_dir) if slot_dir is not None else n.orthogonal()
    sd = (sd - sd.dot(n) * n).normalized()
    slot = pl.obox(name + "_slot", (r * 1.9, r * 0.34, r * 0.3), V(loc) + n * (r * 0.42), sd, n, slot_mat)
    return [head, slot]


def rivet_line(p0, p1, count, normal, r=0.0065, h=0.0045, mat="M_Brass", segs=6):
    p0, p1 = V(p0), V(p1)
    out = []
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0.5
        out.append(stud(p0.lerp(p1, t), normal, r, h, mat, segs))
    return out


def lamp(center, normal, r, glow_mat, bezel_mat="M_Steel", cage=True, cage_dir=None, segs=12, name="lamp"):
    """Indicator lamp: a bezel ring with a glowing dome, optionally a two-bar cage over it."""
    n = V(normal).normalized()
    c = V(center)
    parts = [pl.lathe_axis(name + "_bezel", [(0.0, 0.0), (r * 1.45, 0.0), (r * 1.5, r * 0.25), (r * 1.4, r * 0.55),
                                             (r * 1.05, r * 0.6), (r * 1.0, r * 0.35), (0.0, r * 0.35)], n, c, segs,
                           bezel_mat, False, False, 40)]
    dome = pl.lathe_axis(name + "_dome", [(0.0, r * 0.2), (r, r * 0.2), (r * 0.92, r * 0.62), (r * 0.62, r * 0.95),
                                          (0.0, r * 1.08)], n, c, segs, glow_mat, False, False, 60)
    parts.append(dome)
    if cage:
        cd = V(cage_dir) if cage_dir is not None else n.orthogonal()
        cd = (cd - cd.dot(n) * n).normalized()
        side = n.cross(cd)
        for k in (-1, 1):
            q = c + side * (k * r * 0.45)
            pts = [q - cd * (r * 1.3) + n * (r * 0.45), q - cd * (r * 0.8) + n * (r * 1.12),
                   q + cd * (r * 0.8) + n * (r * 1.12), q + cd * (r * 1.3) + n * (r * 0.45)]
            parts.append(pl.sausage(name + "_cage", pts, r * 0.16, 6, 3, bezel_mat, (True, True), 2, True, 60))
    return parts


def gem(center, normal, r, glow_mat, bezel_mat="M_Brass", sides=8, name="gem"):
    """Faceted cabochon gem in a raised bezel with four claws."""
    n = V(normal).normalized()
    c = V(center)
    parts = [pl.lathe_axis(name + "_bezel", [(0.0, 0.0), (r * 1.55, 0.0), (r * 1.6, r * 0.3), (r * 1.4, r * 0.62),
                                             (r * 1.1, r * 0.55), (0.0, r * 0.55)], n, c, 16, bezel_mat, False,
                           False, 40)]
    parts.append(pl.lathe_axis(name, [(0.0, r * 0.25), (r, r * 0.25), (r * 1.02, r * 0.6), (r * 0.7, r * 1.0),
                                      (0.0, r * 1.16)], n, c, sides, glow_mat, False, False, 20))
    x, y, _ = basis(n)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = x * math.cos(a) + y * math.sin(a)
        parts.append(pl.capsule(name + "_claw", c + d * (r * 1.36) + n * (r * 0.42), c + d * (r * 1.08) + n * (r * 0.72),
                                r * 0.2, 5, 1, bezel_mat))
    return parts


def ellipse(rx, ry, n=20):
    """Closed ellipse outline [(s, t), ...] for slab()."""
    return [(rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


# --------------------------------------------------------------------------------------
# Ammo, wraps, dials, stripes
# --------------------------------------------------------------------------------------

def shell(base, axis, length, r, hull_mat, head_mat="M_Brass", primer_mat="M_Copper", segs=12, name="shell"):
    """Fat cartoon shotgun shell standing on `base`, growing along `axis`: a rimmed brass head, a hull with
    a rounded crimp and a dimpled top, and a primer cap on the base."""
    L = length
    ax = V(axis).normalized()
    b = V(base)
    head = pl.lathe_axis(name + "_head", [(0.0, 0.0), (r * 1.13, 0.0), (r * 1.16, 0.035 * L), (r * 1.13, 0.075 * L),
                                          (r * 1.03, 0.095 * L), (r * 1.03, 0.3 * L), (r * 0.98, 0.315 * L),
                                          (0.0, 0.315 * L)], ax, b, segs, head_mat, False, False, 40)
    hull = pl.lathe_axis(name + "_hull", [(0.0, 0.3 * L), (r, 0.3 * L), (r, 0.88 * L), (r * 0.94, 0.955 * L),
                                          (r * 0.72, 0.995 * L), (r * 0.3, 0.985 * L), (0.0, 0.965 * L)], ax, b, segs,
                          hull_mat, False, False, 45)
    primer = pl.disc(name + "_primer", r * 0.36, 0.004, ax, b - ax * 0.0012, primer_mat, 8, 0.3)
    return [head, hull, primer]


def spiral_wrap(name, base, axis, length, r0, ridge, turns, mat, segs=14, steps_per_turn=7, x_hint=None,
                caps=True):
    """Leather/cord wrap: a tube of radius r0 with a raised spiral overlap ridge (`ridge` high, `turns`
    turns) running along `axis` from `base`. Closed with flat caps by default."""
    pitch = length / turns
    steps = max(2, int(round(turns * steps_per_turn)))
    bm = bmesh.new()
    rings = []
    for i in range(steps + 1):
        hgt = length * i / steps
        ring = []
        for j in range(segs):
            th = 2 * math.pi * j / segs
            f = (hgt / pitch - th / (2 * math.pi)) % 1.0
            # overlapping strip: rises quickly to the lip, then slopes back down
            bump = (f / 0.2) if f < 0.2 else (1.0 - (f - 0.2) / 0.8)
            r = r0 + ridge * bump
            ring.append(bm.verts.new((r * math.cos(th), r * math.sin(th), hgt)))
        rings.append(ring)
    for i in range(steps):
        a, b = rings[i], rings[i + 1]
        for j in range(segs):
            jj = (j + 1) % segs
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=pl.frame_matrix(axis, x_hint).to_4x4(), verts=bm.verts)
    return pl.obj_from_bm(name, bm, mat, 50, loc=base)


def arc_strip(name, center, normal, up, r0, r1, a0, a1, thick, mat, steps=6):
    """Flat annular sector lying on a dial face. Angles in degrees from `up`, clockwise as seen from the
    front of the face (the side `normal` points to)."""
    n = V(normal).normalized()
    up = V(up)
    up = (up - up.dot(n) * n).normalized()
    side = up.cross(n)
    c = V(center)
    bm = bmesh.new()
    rows = []
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        d = up * math.cos(a) + side * math.sin(a)
        rows.append([bm.verts.new(c + d * rr + n * z) for (rr, z) in ((r0, 0.0), (r1, 0.0), (r1, thick),
                                                                      (r0, thick))])
    for k in range(steps):
        a, b = rows[k], rows[k + 1]
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat, 30)


def gauge(center, normal, up, r, rim_mat="M_Brass", face_mat="DialFace", ink_mat="DialInk", needle_mat="DialNeedle",
          zones=None, needle_deg=-35.0, ticks=7, sweep=(-120.0, 120.0), depth=0.012, segs=20, glass=False,
          name="gauge"):
    """Round dial: a bezel ring, a cream face, coloured zone arcs, tick marks, a needle and a hub.
    `zones` is a list of (material, from_deg, to_deg). Returns a list of objects."""
    n = V(normal).normalized()
    up = V(up)
    up = (up - up.dot(n) * n).normalized()
    side = up.cross(n)
    c = V(center)
    parts = []
    # bezel: a thick ring with a rounded lip, standing on the surface (back at c)
    parts.append(pl.lathe_axis(name + "_bezel", [(0.0, 0.0), (r, 0.0), (r * 1.04, depth * 0.45), (r, depth * 0.9),
                                                 (r * 0.9, depth), (r * 0.82, depth * 0.8), (r * 0.82, depth * 0.55),
                                                 (0.0, depth * 0.55)], n, c, segs, rim_mat, False, False, 40))
    fz = depth * 0.55
    parts.append(pl.disc(name + "_face", r * 0.84, 0.002, n, c + n * fz, face_mat, segs, 0.2))
    top = fz + 0.001
    for (m, za0, za1) in (zones or []):
        parts.append(arc_strip(name + "_zone", c + n * top, n, up, r * 0.5, r * 0.7, za0, za1, 0.0015, m,
                               max(2, int(abs(za1 - za0) / 20))))
    for k in range(ticks):
        a = math.radians(sweep[0] + (sweep[1] - sweep[0]) * k / max(1, ticks - 1))
        d = up * math.cos(a) + side * math.sin(a)
        parts.append(pl.obox(name + "_tick", (r * 0.07, r * 0.18, 0.002), c + n * (top + 0.001) + d * (r * 0.66),
                             d.cross(n), n, ink_mat))
    a = math.radians(needle_deg)
    d = up * math.cos(a) + side * math.sin(a)
    parts.append(pl.obox(name + "_needle", (r * 0.62, r * 0.09, 0.0025), c + n * (top + 0.003) + d * (r * 0.27), d,
                         n, needle_mat))
    parts.append(pl.disc(name + "_hub", r * 0.13, 0.004, n, c + n * (top + 0.003), ink_mat, 10, 0.3))
    if glass:
        parts.append(pl.lathe_axis(name + "_glass", [(0.0, fz), (r * 0.84, fz), (r * 0.82, depth * 0.85),
                                                     (r * 0.5, depth * 1.05), (0.0, depth * 1.1)], n, c, segs,
                                   "M_Glass", False, False, 60))
    return parts


def hazard_band(name, r, width, axis, center, base_mat, stripe_mat, stripes=8, slant=30.0, half_w=11.0, steps=3,
                cols=2):
    """Painted band around a cylinder (radius r) with slanted contrasting stripes hugging its surface.
    Returns [band, stripes]."""
    ax = V(axis).normalized()
    c = V(center)
    band = pl.band(name, r, width, 0.012, ax, c, base_mat, 32, 0.0)
    x, y, _ = basis(ax)
    bm = bmesh.new()
    STEPS, COLS = steps, cols
    for k in range(stripes):
        a0 = 360.0 * k / stripes
        grids = []
        for rr in (r + 0.0014, r - 0.004):
            grid = []
            for j in range(STEPS + 1):
                t = j / STEPS
                hh = -width / 2 + 0.002 + (width - 0.004) * t
                row = []
                for cc in range(COLS + 1):
                    a = math.radians(a0 + slant * t + half_w * (2 * cc / COLS - 1))
                    row.append(bm.verts.new(c + ax * hh + (x * math.cos(a) + y * math.sin(a)) * rr))
                grid.append(row)
            grids.append(grid)
        out, inn = grids
        for j in range(STEPS):
            for cc in range(COLS):
                bm.faces.new((out[j][cc], out[j][cc + 1], out[j + 1][cc + 1], out[j + 1][cc]))
                bm.faces.new((inn[j][cc], inn[j + 1][cc], inn[j + 1][cc + 1], inn[j][cc + 1]))
        for j in range(STEPS):
            for cc in (0, COLS):
                bm.faces.new((out[j][cc], out[j + 1][cc], inn[j + 1][cc], inn[j][cc]))
        for cc in range(COLS):
            for j in (0, STEPS):
                bm.faces.new((out[j][cc], inn[j][cc], inn[j][cc + 1], out[j][cc + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return [band, pl.obj_from_bm(name + "_stripes", bm, stripe_mat, 0)]


def cable(name, pts, r, mat="M_Rubber", segs=7, res=4):
    """Soft cable / wire along a smooth path with rounded ends."""
    return pl.sausage(name, pts, r, segs, res, mat, (True, True), 2, True, 70)


def oval_helix(name, base, axis, w_dir, rw_, rn, wire_r, turns, length, mat="M_Copper", pts_per_turn=12,
               segs=6):
    """Wire wound around a flat bar: an elliptical helix (semi-axes rw_ along w_dir, rn across)."""
    ax = V(axis).normalized()
    w = V(w_dir)
    w = (w - w.dot(ax) * ax).normalized()
    nn = ax.cross(w)
    b = V(base)
    n = int(turns * pts_per_turn) + 1
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = 2 * math.pi * turns * t
        pts.append(b + ax * (length * t) + w * (rw_ * math.cos(a)) + nn * (rn * math.sin(a)))
    return pl.sausage(name, pts, wire_r, segs, 2, mat, (True, True), 2, True, 80)


def bolt_emblem(name, center, s_dir, t_dir, size, depth, mat, bevel=0.0):
    """Cartoon lightning-bolt emblem (flat slab) lying in the (s, t) plane; the bolt points toward -t."""
    pts = [(x * size, y * size) for (x, y) in BOLT]
    return slab(name, pts, depth, center, s_dir, t_dir, mat, bevel, 1, 40, 30)


# --------------------------------------------------------------------------------------
# Material helpers
# --------------------------------------------------------------------------------------

def mat_where(o, mat, predicate):
    """rw.set_mat_where, after making sure the object's world matrix is current."""
    bpy.context.view_layer.update()
    return rw.set_mat_where(o, mat, predicate)


def inner_faces(axis_point, axis_dir, limit=-0.25):
    """Predicate for rw.set_mat_where: faces whose normal points toward a cylinder axis (bores, mouths)."""
    p0 = V(axis_point)
    d = V(axis_dir).normalized()

    def pred(c, nrm):
        rel = c - p0
        radial = rel - rel.dot(d) * d
        if radial.length < 1e-6:
            return False
        return nrm.dot(radial.normalized()) < limit
    return pred
