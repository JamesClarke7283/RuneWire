"""tech_weapon_helpers: extra shape helpers for the tech-weapon viewmodels
(vm_gatling, vm_crossbow, vm_longshot, vm_flamer, vm_steam_hammer).

Built on glove.py / partlib.py / rwlib.py / detail_helpers.py / new_weapon_helpers.py, which are shared and must
not be edited. Everything works in world space and metres; user-facing angles are in degrees. Every helper returns
a new mesh object or a list of them, ready to be joined with rw.join().

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tech_weapon_helpers as th
    nw, dh, glove, pl, rw, V = th.nw, th.dh, th.glove, th.pl, th.rw, th.V
"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import new_weapon_helpers as nw  # noqa: E402
import detail_helpers as dh  # noqa: E402

glove = nw.glove
pl = nw.pl
rw = nw.rw
V = Vector
X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))


class Parts(list):
    """Objects waiting to be joined; add() takes one object or a list of them and returns its argument."""

    def add(self, x):
        if x is None:
            return x
        if isinstance(x, (list, tuple)):
            self.extend(i for i in x if i is not None)
        else:
            self.append(x)
        return x


# --------------------------------------------------------------------------------------
# Shared setup
# --------------------------------------------------------------------------------------

def std_mats():
    """Flat colours used by the dials, screws and paint details; returns the RarityGlow material."""
    dh.flat_mats()                       # DialFace DialInk DialRed WarnBlack WarnYellow Ceramic
    rw.flat("DialNeedle", "d8392b", 0.5, 0.0)
    rw.flat("DialTeal", "2fb5b0", 0.5, 0.0)
    rw.flat("DialYellow", "ffc531", 0.5, 0.0)
    rw.flat("ScrewSlot", "1e1a22", 0.6, 0.0)
    return rw.glow("RarityGlow", "ffffff", 3.0)


def grip_frame(rake=18.0):
    """(A, out, front) for a pistol grip through the origin raked `rake` degrees forward (glove.fist frame)."""
    A = V((0, -math.sin(math.radians(rake)), math.cos(math.radians(rake))))
    _, o, fr = glove.frame(A, (-1, 0, 0))
    return A, o, fr


def pistol_grip(A, o, fr, mat="M_WoodDark", pommel="M_Brass", size=(0.048, 0.064, 0.2), medallion="M_Brass"):
    """Wooden pistol grip around the origin (the glove's grip axis A), a brass pommel cap and a brass
    escutcheon screw on each side."""
    parts = [glove.oriented_pillow("grip", size, -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10, mat),
             glove.oriented_pillow("pommel", (size[0] + 0.01, size[1] + 0.01, 0.03), A * -0.1 - fr * 0.004, o, fr, A,
                                   0.6, 0.6, 16, 8, pommel)]
    if medallion:
        for s in (-1, 1):
            p = A * 0.006 - fr * 0.004 + X * (s * (size[0] / 2 - 0.0005))
            parts.append(pl.disc("grip_medallion", 0.0085, 0.003, X * s, p, medallion, 10, 0.3))
            parts += nw.screw(p + X * (s * 0.0012), X * s, 0.0045, "M_Steel", (0, 1, 1))
    return parts


def trigger_group(front_y=-0.106, top_z=0.09, mat="M_Brass", trig="M_Steel"):
    """Brass trigger guard loop from under the body (front_y, top_z) back to the grip, and a steel trigger."""
    guard = [(0, front_y, top_z + 0.004), (0, front_y - 0.015, 0.04), (0, -0.104, 0.006), (0, -0.074, -0.006),
             (0, -0.036, -0.004)]
    return [pl.sausage("guard", guard, 0.0085, 8, 3, mat, (True, True), 2, True, 60),
            pl.capsule("trigger", (0, -0.08, top_z - 0.002), (0, -0.092, 0.05), 0.0072, 8, 2, trig)]


# --------------------------------------------------------------------------------------
# Bars, shells and soft mechanical shapes
# --------------------------------------------------------------------------------------

def octo_bar(name, a, b, r_flat, mat="M_Steel", up=(0, 0, 1), bevel=0.003):
    """Octagonal bar (rifle barrel) from a to b; r_flat = axis-to-flat distance, one flat faces `up`, softly
    bevelled edges (modifier kept live until join)."""
    a, b = V(a), V(b)
    ax = (b - a).normalized()
    u = V(up) - V(up).dot(ax) * ax
    u.normalize()
    side = ax.cross(u).normalized()
    rv = r_flat / math.cos(math.pi / 8)
    pts = [(rv * math.cos(math.radians(22.5 + 45 * k)), rv * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    return nw.slab(name, pts, (b - a).length, (a + b) / 2, side, u, mat, bevel, 2, 30, 35)


def bellows(name, a, b, r_in, r_out, folds, mat="M_Leather", segs=24, crest=0.18):
    """Round accordion bellows from a to b: `folds` pleats between r_in (valleys) and r_out (crests)."""
    a, b = V(a), V(b)
    L = (b - a).length
    p = L / folds
    prof = []
    for k in range(folds):
        h = k * p
        prof += [(r_in, h), (r_out, h + p * (0.5 - crest / 2)), (r_out, h + p * (0.5 + crest / 2))]
    prof.append((r_in, L))
    return pl.lathe_axis(name, prof, (b - a).normalized(), a, segs, mat, False, False, 40)


def arc_shell(name, a, b, r_out, thick, a0, a1, up=(0, 0, 1), segs=24, mat=None, smooth_angle=40):
    """Partial thick-walled tube from a to b covering angles a0..a1 (degrees around the axis, 0 = `up`)."""
    a, b = V(a), V(b)
    ax = (b - a).normalized()
    u = V(up) - V(up).dot(ax) * ax
    u.normalize()
    s = ax.cross(u).normalized()
    n = max(2, int(round(segs * abs(a1 - a0) / 360.0)))
    bm = bmesh.new()
    grid = []                                  # grid[end][radius][k]
    for p in (a, b):
        layer = []
        for rr in (r_out, r_out - thick):
            ring = []
            for k in range(n + 1):
                t = math.radians(a0 + (a1 - a0) * k / n)
                ring.append(bm.verts.new(p + (u * math.cos(t) + s * math.sin(t)) * rr))
            layer.append(ring)
        grid.append(layer)
    (o0, i0), (o1, i1) = grid
    for k in range(n):
        bm.faces.new((o0[k], o0[k + 1], o1[k + 1], o1[k]))
        bm.faces.new((i0[k], i1[k], i1[k + 1], i0[k + 1]))
        bm.faces.new((o0[k], i0[k], i0[k + 1], o0[k + 1]))
        bm.faces.new((o1[k], o1[k + 1], i1[k + 1], i1[k]))
    for k in (0, n):
        bm.faces.new((o0[k], o1[k], i1[k], i0[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat, smooth_angle)


def perforate(shell, a, b, r, rows, per_row, hole_r, a0=-180.0, a1=180.0, up=(0, 0, 1), margin=0.012,
              stagger=True, depth=0.03, segs=8):
    """Punch `rows` x `per_row` round holes radially through a shell around the axis a->b (radius r)."""
    a, b = V(a), V(b)
    ax = (b - a).normalized()
    L = (b - a).length
    u = V(up) - V(up).dot(ax) * ax
    u.normalize()
    s = ax.cross(u).normalized()
    cut = []
    for i in range(rows):
        h = margin + (L - 2 * margin) * (i / max(1, rows - 1))
        off = 0.5 if (stagger and i % 2) else 0.0
        for k in range(per_row):
            f = (k + 0.5 + off) / per_row if a1 - a0 < 359.0 else (k + off) / per_row
            if f > 1.0:
                continue
            t = math.radians(a0 + (a1 - a0) * f)
            d = u * math.cos(t) + s * math.sin(t)
            c = a + ax * h + d * r
            cut.append(pl.rod("hole", c - d * depth, c + d * depth, hole_r, segs))
    return pl.carve(shell, cut)


def strap_loop(name, c, u, v, ru, rv, width=0.013, thick=0.0045, mat="M_Leather", n=16, bevel=0.0012):
    """Closed flat strap loop: an ellipse (radii ru along u, rv along v) in the u/v plane; the strap's width runs
    along u x v (leather sling loops, belts)."""
    c, u, v = V(c), V(u).normalized(), V(v).normalized()
    w = u.cross(v).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        t = 2 * math.pi * i / n
        p = c + u * (ru * math.cos(t)) + v * (rv * math.sin(t))
        nr = (u * (rv * math.cos(t)) + v * (ru * math.sin(t))).normalized()
        rings.append([bm.verts.new(p + nr * (dt * thick / 2) + w * (dw * width / 2))
                      for (dt, dw) in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    for i in range(n):
        A_, B_ = rings[i], rings[(i + 1) % n]
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((A_[j], A_[jj], B_[jj], B_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = pl.obj_from_bm(name, bm, mat, 0)
    if bevel:
        rw.add_bevel(o, bevel, 1, 50).harden_normals = False
    rw.smooth(o, 50)
    return o


def strap_path(name, pts, width=0.014, thick=0.0045, normal=(0, 0, 1), mat="M_Leather", res=3, closed=False):
    """Flat strap swept along `pts` with its width lying in the surface whose normal is `normal`."""
    if closed:
        pts = list(pts) + [pts[0], pts[1]]
    Q, _ = pl._resample(pts, [1.0] * len(pts), res, True)
    if closed:
        Q = Q[:-res]
    nn = V(normal).normalized()
    bm = bmesh.new()
    rings = []
    m = len(Q)
    for i in range(m):
        T = (Q[min(i + 1, m - 1)] - Q[max(i - 1, 0)]).normalized()
        wv = T.cross(nn).normalized()
        nv = wv.cross(T).normalized()
        rings.append([bm.verts.new(Q[i] + nv * (dt * thick / 2) + wv * (dw * width / 2))
                      for (dt, dw) in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    for i in range(m - 1):
        A_, B_ = rings[i], rings[i + 1]
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((A_[j], A_[jj], B_[jj], B_[j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = pl.obj_from_bm(name, bm, mat, 0)
    rw.add_bevel(o, min(0.0012, thick * 0.3), 1, 50).harden_normals = False
    rw.smooth(o, 50)
    return o


def flywheel(name, c, axis, r, rim_w=0.009, rim_t=0.007, spokes=5, mat="M_Steel", hub_mat="M_Brass", up=(0, 0, 1),
             spin=0.0, segs=24, spoke_round=0.0):
    """Spoked flywheel (axis `axis`, centred on c): a plain rim, flat spokes, a hub and an axle nut."""
    ax = V(axis).normalized()
    c = V(c)
    u, v, _ = dh.basis(ax, up)
    parts = [pl.band(name + "_rim", r, rim_w, rim_t, ax, c, mat, segs, 0.35)]
    hub_r = max(0.0075, r * 0.26)
    parts.append(pl.disc(name + "_hub", hub_r, rim_w * 1.3, ax, c, hub_mat, 14, 0.35))
    for k in range(spokes):
        t = math.radians(spin + 360.0 * k / spokes)
        d = u * math.cos(t) + v * math.sin(t)
        p0, p1 = c + d * (hub_r * 0.6), c + d * (r - rim_t * 0.6)
        parts.append(pl.obox(name + "_spoke", ((p1 - p0).length, max(0.006, r * 0.17), rim_w * 0.6), (p0 + p1) / 2, d,
                             ax, mat, rounded=spoke_round, segments=1))
    parts.append(pl.bolt(c + ax * (rim_w * 0.62), ax, hub_r * 0.55, hub_r * 0.42, "M_Steel", name + "_nut"))
    return parts


def ring_studs(c, axis, radius, count, r=0.0048, h=0.0035, mat="M_Steel", a0=0.0, a1=360.0, up=(0, 0, 1),
               segs=6):
    """Studs around a circle of `radius` on a cylinder about `axis` through c (heads point radially out), spread
    over angles a0..a1 (0 = `up`)."""
    ax = V(axis).normalized()
    u = V(up) - V(up).dot(ax) * ax
    u.normalize()
    s = ax.cross(u).normalized()
    full = abs(a1 - a0) >= 359.9
    out = []
    for k in range(count):
        f = k / count if full else (k / max(1, count - 1))
        t = math.radians(a0 + (a1 - a0) * f)
        d = u * math.cos(t) + s * math.sin(t)
        out.append(nw.stud(V(c) + d * radius, d, r, h, mat, segs))
    return out


# --------------------------------------------------------------------------------------
# Ammo, flames, paint
# --------------------------------------------------------------------------------------

def cartridge(base, axis, length=0.04, r=0.0075, case="M_Brass", tip="M_Copper", segs=8, name="round"):
    """Chunky cartoon rifle round standing on `base` along `axis`: rimmed brass case, necked shoulder, copper tip."""
    L = length
    ax = V(axis).normalized()
    cp = [(0.0, 0.0), (r * 1.14, 0.0), (r * 1.14, 0.06 * L), (r * 0.93, 0.09 * L), (r, 0.12 * L), (r, 0.56 * L),
          (r * 0.8, 0.64 * L), (r * 0.78, 0.7 * L), (0.0, 0.7 * L)]
    tp = [(0.0, 0.66 * L), (r * 0.8, 0.66 * L), (r * 0.78, 0.76 * L), (r * 0.6, 0.88 * L), (r * 0.28, 0.97 * L),
          (0.0, L)]
    return [pl.lathe_axis(name + "_case", cp, ax, base, segs, case, False, False, 50),
            pl.lathe_axis(name + "_tip", tp, ax, base, segs, tip, False, False, 60)]


def path_frames(pts, spacing, start=0.0, res=10, count=None):
    """Evenly spaced (point, tangent) samples along a smooth Catmull-Rom path through pts."""
    Q, _ = pl._resample(pts, [1.0] * len(pts), res, True)
    seg = [(Q[i + 1] - Q[i]).length for i in range(len(Q) - 1)]
    total = sum(seg)
    out = []
    s = start
    while s <= total + 1e-9 and (count is None or len(out) < count):
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= s or i == len(seg) - 1:
                t = 0.0 if L < 1e-9 else max(0.0, min(1.0, (s - acc) / L))
                p = Q[i].lerp(Q[i + 1], t)
                T = (Q[min(i + 1, len(Q) - 1)] - Q[i]).normalized()
                out.append((p, T))
                break
            acc += L
        s += spacing
    return out


def round_lite(base, axis, length=0.038, r=0.0072, case="M_Brass", tip="M_Copper", segs=6, name="round"):
    """Low-poly cartridge in one lathe (rimmed case, shoulder, pointed tip); the tip faces get `tip`."""
    L = length
    ax = V(axis).normalized()
    prof = [(0.0, 0.0), (r * 1.15, 0.0), (r * 1.15, 0.07 * L), (r, 0.1 * L), (r, 0.6 * L), (r * 0.74, 0.78 * L),
            (r * 0.32, 0.95 * L), (0.0, L)]
    o = pl.lathe_axis(name, prof, ax, base, segs, case, False, False, 50)
    b = V(base)
    nw.mat_where(o, tip, lambda p, n: (p - b).dot(ax) > 0.62 * L)
    return o


def ammo_belt(pts, spacing, round_dir, length=0.038, r=0.0072, case="M_Brass", tip="M_Copper", link="M_Steel",
              segs=6, start=0.004, count=None, strap_w=0.012):
    """Belt of cartridges along a path: each round lies across the path along round_dir (tip toward +round_dir),
    centred on the path, on a flat steel link strap that runs under their cases."""
    parts = []
    frames = path_frames(pts, spacing, start, 10, count)
    for (p, T) in frames:
        d = V(round_dir) - V(round_dir).dot(T) * T
        d.normalize()
        parts.append(round_lite(p - d * (length * 0.5), d, length, r, case, tip, segs))
    d0 = V(round_dir).normalized()
    sp = [p - d0 * (length * 0.18) for (p, _) in frames]
    if len(sp) >= 2:
        # the strap lies flat across the rounds: its width runs along round_dir
        Q, _ = pl._resample(sp, [1.0] * len(sp), 2, True)
        bm = bmesh.new()
        rings = []
        m = len(Q)
        for i in range(m):
            T = (Q[min(i + 1, m - 1)] - Q[max(i - 1, 0)]).normalized()
            wv = d0 - d0.dot(T) * T
            wv.normalize()
            nv = T.cross(wv).normalized()
            rings.append([bm.verts.new(Q[i] + nv * (dt * r * 1.2) + wv * (dw * strap_w / 2))
                          for (dt, dw) in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
        for i in range(m - 1):
            A_, B_ = rings[i], rings[i + 1]
            for j in range(4):
                jj = (j + 1) % 4
                bm.faces.new((A_[j], A_[jj], B_[jj], B_[j]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(pl.obj_from_bm("belt_link", bm, link, 40))
    return parts


def hazard_ring(name, r, width, axis, center, base="WarnYellow", ink="WarnBlack", stripes=8, slant=30.0,
                half_w=10.0, segs=24, thick=0.01):
    """Cheaper hazard band than nw.hazard_band: a plain painted ring (`segs` sides) with slanted stripe shells
    (outer face + side walls only) hugging its surface."""
    dh.flat_mats()
    ax = V(axis).normalized()
    c = V(center)
    band = pl.band(name, r, width, thick, ax, c, base, segs, 0.0)
    x, y, _ = nw.basis(ax)
    bm = bmesh.new()
    steps, cols = 2, 1
    for k in range(stripes):
        a0 = 360.0 * k / stripes
        grids = []
        for rr in (r + 0.0012, r - 0.003):
            grid = []
            for j in range(steps + 1):
                t = j / steps
                hh = -width / 2 + 0.0015 + (width - 0.003) * t
                row = []
                for cc in range(cols + 1):
                    a = math.radians(a0 + slant * t + half_w * (2 * cc / cols - 1))
                    row.append(bm.verts.new(c + ax * hh + (x * math.cos(a) + y * math.sin(a)) * rr))
                grid.append(row)
            grids.append(grid)
        out, inn = grids
        # (x, y, ax) is right-handed, so these windings face out of each stripe shell
        for j in range(steps):
            for cc in range(cols):
                bm.faces.new((out[j][cc], out[j][cc + 1], out[j + 1][cc + 1], out[j + 1][cc]))
            bm.faces.new((out[j][0], out[j + 1][0], inn[j + 1][0], inn[j][0]))
            bm.faces.new((out[j][cols], inn[j][cols], inn[j + 1][cols], out[j + 1][cols]))
        for cc in range(cols):
            bm.faces.new((out[0][cc], inn[0][cc], inn[0][cc + 1], out[0][cc + 1]))
            bm.faces.new((out[steps][cc], out[steps][cc + 1], inn[steps][cc + 1], inn[steps][cc]))
    return [band, pl.obj_from_bm(name + "_stripes", bm, ink, 0)]


def flame(name, base, up, h, r, mat, segs=10, lean=None, twist=0.0):
    """Cartoon teardrop flame standing on `base`, pointing along `up`; `lean` bends the tip (a world vector
    added in proportion to height squared)."""
    prof = [(0.0, 0.0), (r * 0.55, 0.05 * h), (r * 0.92, 0.18 * h), (r, 0.32 * h), (r * 0.82, 0.52 * h),
            (r * 0.5, 0.74 * h), (r * 0.18, 0.92 * h), (0.0, h)]
    o = pl.lathe_axis(name, prof, up, base, segs, mat, False, False, 80, twist)
    if lean is not None:
        upn = V(up).normalized()
        L = V(lean)
        for vtx in o.data.vertices:
            f = max(0.0, vtx.co.dot(upn) / h)
            vtx.co = vtx.co + L * (f * f)
        o.data.update()
    return o


def _clip(poly, x0, x1, y0, y1):
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            cur, prev = pts[i], pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
        return out

    def ix(xc):
        return lambda p, q: (xc, p[1] + (q[1] - p[1]) * (xc - p[0]) / (q[0] - p[0]))

    def iy(yc):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (yc - p[1]) / (q[1] - p[1]), yc)

    pts = list(poly)
    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            break
        pts = clip(pts, inside, inter)
    return pts


def hazard_panel(name, c, normal, up, w, h, t=0.003, stripe=0.009, slant=40.0, base="WarnYellow",
                 ink="WarnBlack", inset=0.0025, rounded=0.0012):
    """Flat yellow plate (back at c, facing `normal`) with slanted black stripes clipped to its border."""
    dh.flat_mats()
    u, v, n = dh.basis(normal, up)
    c = V(c)
    parts = [pl.obox(name, (w, h, t), c + n * (t / 2), u, n, base, rounded=rounded, segments=1)]
    k = math.tan(math.radians(slant))
    x0, x1, y0, y1 = -w / 2 + inset, w / 2 - inset, -h / 2 + inset, h / 2 - inset
    step = stripe * 2
    j = -int((w + h * abs(k)) / step) - 2
    while j * step < w + h * abs(k):
        xa = j * step
        poly = [(xa - h * k, -h), (xa + stripe - h * k, -h), (xa + stripe + h * k, h), (xa + h * k, h)]
        cl = _clip(poly, x0, x1, y0, y1)
        if len(cl) >= 3:
            area = sum(cl[i][0] * cl[(i + 1) % len(cl)][1] - cl[(i + 1) % len(cl)][0] * cl[i][1]
                       for i in range(len(cl))) / 2
            if abs(area) > 1e-6:
                parts.append(dh.prism(name + "_stripe", cl if area > 0 else cl[::-1], c, u, v, n, 0.0012, ink,
                                      t - 0.0003, 0.0, 0))
        j += 1
    return parts


def scroll_lite(name, c, normal, size, up=(0, 0, 1), width=0.0052, height=0.0026, mat="M_Brass", flip=False,
                turns=1.0, angle=0.0, n=8):
    """Cheaper dh.scroll: the same raised S-scroll bead with fewer path samples (~150 triangles)."""
    u, v, nn = dh.basis(normal, up)
    pts, tap = dh.scroll_2d(turns=turns, n=n)
    k = size / 1.32
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    world = []
    for (x, y) in pts:
        if flip:
            y = -y
        world.append(V(c) + u * ((x * ca - y * sa) * k) + v * ((x * sa + y * ca) * k))
    return dh.ridge(name, world, nn, width, height, mat, 1, tap)


def mark_bore(o, centre, axis, r_bore, mat="M_DarkMetal", depth_from=None):
    """Paint the faces of a lathed muzzle that lie within r_bore of its axis (the bore / bore floor) dark."""
    c = V(centre)
    ax = V(axis).normalized()

    def pred(p, nrm):
        rel = p - c
        radial = rel - rel.dot(ax) * ax
        if radial.length > r_bore:
            return False
        return depth_from is None or rel.dot(ax) >= depth_from
    return nw.mat_where(o, mat, pred)
