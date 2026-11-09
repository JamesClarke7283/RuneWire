"""detail_helpers: shared detail kit for the first-person weapon viewmodels (vm_*.py).

Chunky cartoon "greebles" that read at viewmodel scale: gears, gauges, indicator lamps, charge pips,
maker's plates, filigree scrolls, rivet rows, wire bundles, valves, knurled knobs, hazard bands,
leather wraps with stitching and capacitor cells, plus a rounded side-profile prism for designed body
silhouettes.

Everything is built in world space (metres) and returns plain mesh objects, or lists of them, ready to
be joined into the weapon body with rw.join(). Angles are in degrees. Surface details take the outward
`normal` of the surface they stand on and an `up` hint that orients them (see basis()).

    import detail_helpers as dh
    parts += dh.gauge("gauge", (0.035, -0.05, 0.13), normal=(1, 0, 0), r=0.022)
"""
import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "parts"))
import partlib as pl  # noqa: E402

rw = pl.rw
V = Vector


def flat_mats():
    """Flat colours shared by the dials and paint details (get-or-create)."""
    rw.flat("DialFace", "f6ead0", 0.5, 0.0)
    rw.flat("DialInk", "2b2233", 0.6, 0.0)
    rw.flat("DialRed", "d8392b", 0.5, 0.0)
    rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)
    rw.flat("WarnYellow", "ffc531", 0.5, 0.0)
    rw.flat("Ceramic", "efe6d2", 0.45, 0.0)


# --------------------------------------------------------------------------------------
# Frames
# --------------------------------------------------------------------------------------

def basis(normal, up=(0, 0, 1)):
    """Right-handed surface frame (u, v, n): n = normal, v = `up` projected onto the surface, u = v x n
    (u is "right" when you look at the surface from outside with v up)."""
    n = V(normal).normalized()
    v = V(up) - V(up).dot(n) * n
    if v.length < 1e-6:
        v = n.orthogonal()
    v.normalize()
    u = v.cross(n).normalized()
    return u, v, n


def place(o, c, u, v, n):
    """Map a mesh built about its origin in local XYZ onto the frame (u, v, n) at world point c."""
    M = Matrix((tuple(u), tuple(v), tuple(n))).transposed().to_4x4()
    o.data.transform(M)
    if M.to_3x3().determinant() < 0:
        o.data.flip_normals()            # a mirroring frame would leave the mesh inside-out
    o.data.update()
    o.location = V(c)
    return o


def at(c, u, v, n, x=0.0, y=0.0, z=0.0):
    return V(c) + u * x + v * y + n * z


def prism(name, pts2d, c, u, v, n, h, mat=None, z0=0.0, bevel=0.0, smooth_angle=35):
    """Extrude a 2D polygon [(x, y), ...] (in the u/v plane) from z0 to z0 + h along n."""
    o = rw.extrude_poly(name, pts2d, h, mat=mat)
    o.data.transform(Matrix.Translation((0, 0, z0 + h / 2)))
    place(o, c, u, v, n)
    if bevel:
        rw.add_bevel(o, bevel, 1, 30)
    if smooth_angle:
        rw.smooth(o, smooth_angle)
    return o


def slab(name, pts, x0, x1, mat=None, round_r=0.01, segs=3, angle=30.0):
    """Side-profile prism: polygon [(y, z), ...] in the YZ plane extruded along X from x0 to x1, with its
    sharp edges rounded by a bevel modifier (kept live until join/export). For designed silhouettes."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for (y, z) in pts]
    b = [bm.verts.new((x1, y, z)) for (y, z) in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    k = len(pts)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = pl.obj_from_bm(name, bm, mat, 0)
    if round_r:
        m = o.modifiers.new("Round", 'BEVEL')
        m.width = round_r
        m.segments = segs
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(angle)
        m.use_clamp_overlap = True
        m.harden_normals = False
    rw.smooth(o, 35)
    return o


def arc_pts(cy, cz, r, a0, a1, n):
    """Points on a circle arc in the YZ plane (angles in degrees, 0 = +Y, 90 = +Z)."""
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# --------------------------------------------------------------------------------------
# Fasteners
# --------------------------------------------------------------------------------------

def rivet_line(a, b, count, normal, r=0.0065, h=0.0045, mat="M_Steel", segs=6):
    """`count` dome rivets evenly spaced from a to b on a surface with the given normal."""
    out = []
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0.5
        out.append(pl.rivet(V(a).lerp(V(b), t), normal, r, h, mat, segs))
    return out


def bolt_ring(c, axis, radius, count, r=0.0065, h=0.005, mat="M_Steel", phase=0.0):
    """Hex bolt heads in a circle on a flat face whose outward normal is `axis`."""
    n = V(axis).normalized()
    R = pl.frame_matrix(n)
    out = []
    for i in range(count):
        a = math.radians(phase) + 2 * math.pi * i / count
        p = V(c) + R @ V((math.cos(a) * radius, math.sin(a) * radius, 0.0))
        out.append(pl.bolt(p, n, r, h, mat, washer=False, spin=math.degrees(a)))
    return out


def screw(loc, normal, r=0.0065, mat="M_Steel", up=(0, 0, 1), slot_deg=30.0):
    """Cheese-head screw: a flat-topped round head with a dark slot drawn across its top."""
    flat_mats()
    u, v, n = basis(normal, up)
    h = r * 0.55
    head = pl.lathe_axis("screw", [(r, -h * 0.4), (r, h * 0.45), (r * 0.82, h), (0.0, h)], n, loc, 10, mat, False,
                         False, 50)
    a = math.radians(slot_deg)
    d = u * math.cos(a) + v * math.sin(a)
    slot = pl.obox("slot", (r * 1.5, r * 0.36, 0.0012), V(loc) + n * h, d, n, "DialInk")
    return [head, slot]


# --------------------------------------------------------------------------------------
# Mechanisms
# --------------------------------------------------------------------------------------

def gear(name, c, axis, r, teeth=10, depth=None, thick=0.01, mat="M_Brass", holes=0, hole_r=None, hub=True,
         hub_mat="M_Steel", up=(0, 0, 1), spin=0.0, bevel=0.0):
    """Spur gear (axis = `axis`, centred on c) with chunky teeth, optional round lightening holes and a
    raised hub with an axle cap on the +axis side. Returns a list of objects."""
    depth = depth if depth is not None else r * 0.24
    step = 2 * math.pi / teeth
    pts = []
    for i in range(teeth):
        a0 = i * step + math.radians(spin)
        for f, rr in ((0.0, r - depth), (0.12, r), (0.43, r), (0.55, r - depth)):
            a = a0 + f * step
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    u, v, n = basis(axis, up)
    o = rw.extrude_poly(name, pts, thick, mat=mat)
    if holes:
        hr = hole_r if hole_r else (r - depth) * 0.2
        rad = (r - depth) * 0.6
        cut = []
        for k in range(holes):
            a = 2 * math.pi * k / holes + math.radians(spin)
            cut.append(rw.cylinder("hole", hr, thick * 3, 8, (rad * math.cos(a), rad * math.sin(a), 0)))
        pl.carve(o, cut)
    if bevel:
        rw.add_bevel(o, bevel, 1, 30)
    place(o, c, u, v, n)
    rw.smooth(o, 30)
    parts = [o]
    if hub:
        hr = (r - depth) * 0.36
        parts.append(pl.disc(name + "_hub", hr, thick * 1.6, n, V(c), mat, 14, 0.35))
        parts.append(pl.rivet(V(c) + n * (thick * 0.8), n, hr * 0.55, hr * 0.45, hub_mat, 8))
    return parts


def mesh_spin(rA, nA, theta_deg):
    """Spins for two meshing gears made by gear(): gear A (nA teeth) at the origin, gear B in direction
    theta. Returns (spinA, spinB_func(nB))."""
    stepA = 360.0 / nA
    spinA = theta_deg - 0.275 * stepA

    def spinB(nB):
        return theta_deg + 180.0 - 0.775 * (360.0 / nB)
    return spinA, spinB


def valve(name, c, axis, r=0.018, wire=0.0045, spokes=3, mat="M_Copper", hub_mat="M_Brass", stem=0.014,
          stem_mat="M_Steel", up=(0, 0, 1)):
    """Hand wheel valve: rim + spokes + hub on a stem that rises from the surface along `axis`."""
    u, v, n = basis(axis, up)
    ctr = V(c) + n * stem
    parts = [pl.rod(name + "_stem", c, ctr, wire * 1.3, 8, stem_mat)]
    rim = rw.torus(name + "_rim", r, wire, 14, 6, (0, 0, 0), mat=mat)
    pl.align(rim, n, ctr)
    parts.append(rim)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes + 0.4
        d = u * math.cos(a) + v * math.sin(a)
        parts.append(pl.capsule(name + "_spoke", ctr, ctr + d * r, wire * 0.8, 6, 1, mat))
    parts.append(pl.rivet(ctr - n * (wire * 0.6), n, wire * 2.0, wire * 1.8, hub_mat, 8))
    return parts


def knob(name, c, axis, r=0.014, h=0.012, ridges=10, mat="M_Brass", cap_mat=None, up=(0, 0, 1)):
    """Knurled knob standing on a surface: a ridged short prism with a domed cap."""
    u, v, n = basis(axis, up)
    pts = []
    for i in range(ridges * 2):
        a = math.pi * i / ridges
        rr = r if i % 2 == 0 else r * 0.84
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    body = prism(name, pts, c, u, v, n, h, mat, 0.0, 0.0015, 30)
    cap = pl.lathe_axis(name + "_cap", [(r * 0.86, 0.0), (r * 0.78, h * 0.3), (r * 0.45, h * 0.52), (0.0, h * 0.58)],
                        n, V(c) + n * h, 14, cap_mat or mat, False, False, 60)
    return [body, cap]


def spring(name, a, b, r, wire, turns, mat="M_Steel", segs=6):
    a, b = V(a), V(b)
    return pl.helix(name, r, wire, turns, (b - a).length, a, (b - a).normalized(), 12, segs, mat, res=1)


# --------------------------------------------------------------------------------------
# Instruments & lights
# --------------------------------------------------------------------------------------

def gauge(name, c, normal, r=0.022, up=(0, 0, 1), bezel="M_Brass", needle_deg=-35.0, red=(60.0, 125.0),
          ticks=5, depth=0.011, face="DialFace", segs=20):
    """Round pressure gauge standing on a surface (back at c, face toward `normal`): bezel with a raised
    lip, cream face, red danger arc, chunky ticks, red needle with a brass hub.
    Dial angles: 0 = straight up (`up`), positive = clockwise as seen from the front."""
    flat_mats()
    u, v, n = basis(normal, up)
    c = V(c)
    parts = []
    prof = [(r * 0.86, -0.002), (r * 0.98, 0.0), (r, depth * 0.3), (r, depth * 0.72), (r * 0.93, depth),
            (r * 0.83, depth), (r * 0.79, depth * 0.78)]
    parts.append(pl.lathe_axis(name + "_bezel", prof, n, c, segs, bezel, False, False, 40))
    fz = depth * 0.74
    parts.append(pl.disc(name + "_face", r * 0.8, 0.003, n, c + n * (fz - 0.0015), face, segs, 0.0))

    def dial(a_deg, rad):
        a = math.radians(a_deg)
        return u * (math.sin(a) * rad) + v * (math.cos(a) * rad)
    # red danger arc
    if red:
        bm = bmesh.new()
        steps = 6
        rows = []
        for k in range(steps + 1):
            a = red[0] + (red[1] - red[0]) * k / steps
            rows.append([bm.verts.new(c + n * (fz + 0.0006) + dial(a, rr)) for rr in (r * 0.52, r * 0.74)])
        for k in range(steps):
            bm.faces.new((rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        arc = pl.obj_from_bm(name + "_red", bm, "DialRed", 0)
        for p in arc.data.polygons:
            if (arc.matrix_world.to_3x3() @ p.normal).dot(n) < 0:
                p.flip()
        parts.append(arc)
    # ticks
    for k in range(ticks):
        a = -120.0 + 240.0 * k / max(1, ticks - 1)
        d = dial(a, 1.0).normalized()
        parts.append(pl.obox(name + "_tick", (r * 0.12, r * 0.2, 0.0016), c + n * (fz + 0.0008) + d * (r * 0.63),
                             d.cross(n), n, "DialInk"))
    # needle: tapered blade + hub
    d = dial(needle_deg, 1.0).normalized()
    s = d.cross(n).normalized()
    w0, w1, L = r * 0.13, r * 0.03, r * 0.66
    base = c + n * (fz + 0.0016)
    bm = bmesh.new()
    vs = [bm.verts.new(base - d * (r * 0.14) + s * w0 * 0.8), bm.verts.new(base + s * w0),
          bm.verts.new(base + d * L + s * w1), bm.verts.new(base + d * L - s * w1),
          bm.verts.new(base - s * w0), bm.verts.new(base - d * (r * 0.14) - s * w0 * 0.8)]
    top = [bm.verts.new(p.co + n * 0.0014) for p in vs]
    bm.faces.new(vs)
    bm.faces.new(list(reversed(top)))
    for i in range(len(vs)):
        j = (i + 1) % len(vs)
        bm.faces.new((vs[i], vs[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(pl.obj_from_bm(name + "_needle", bm, "DialRed", 0))
    parts.append(pl.rivet(base + n * 0.0012, n, r * 0.15, r * 0.12, bezel, 8))
    return parts


def lamp(name, c, normal, r=0.011, glow="M_TechGlow", up=(0, 0, 1), bezel="M_Brass", cage=0, cage_mat="M_Steel",
         dome=1.0, segs=14):
    """Indicator lamp standing on a surface: a brass bezel cup and a glowing dome, optional wire cage
    (`cage` = number of crossing bars)."""
    u, v, n = basis(normal, up)
    c = V(c)
    parts = []
    prof = [(r * 1.55, -0.002), (r * 1.62, 0.0015), (r * 1.55, r * 0.5), (r * 1.2, r * 0.62), (r * 1.02, r * 0.45)]
    parts.append(pl.lathe_axis(name + "_bezel", prof, n, c, segs, bezel, False, False, 45))
    dprof = [(0.0, 0.0), (r, 0.0), (r * 0.94, r * 0.42 * dome), (r * 0.66, r * 0.82 * dome), (0.0, r * dome)]
    parts.append(pl.lathe_axis(name + "_glow", dprof, n, c + n * (r * 0.3), segs - 2, glow, False, False, 80))
    for k in range(cage):
        a = math.pi * k / max(1, cage) + math.pi / 4
        d = u * math.cos(a) + v * math.sin(a)
        top = c + n * (r * (0.3 + dome) + r * 0.32)
        pts = [c + d * (r * 1.38) + n * (r * 0.5), top + d * (r * 0.75), top - d * (r * 0.75),
               c - d * (r * 1.38) + n * (r * 0.5)]
        parts.append(pl.sausage(name + "_cage", pts, r * 0.16, 6, 2, cage_mat, (True, True), 1, True, 70))
    return parts


def pips(name, c, normal, count=4, lit=None, glow="M_TechGlow", up=(0, 0, 1), size=0.0075, gap=0.0035,
         frame_mat="M_DarkMetal", off_mat="M_Glass", t=0.006):
    """Charge / ammo counter: a dark frame with a row of square glowing pips along u (lit = how many glow)."""
    u, v, n = basis(normal, up)
    lit = count if lit is None else lit
    w = count * size + (count + 1) * gap
    h = size + 2 * gap
    parts = [pl.obox(name + "_frame", (w, h, t), V(c) + n * (t / 2), u, n, frame_mat, rounded=min(0.0025, t * 0.4),
                     segments=2)]
    for i in range(count):
        x = -w / 2 + gap + size / 2 + i * (size + gap)
        parts.append(pl.obox(name + "_pip", (size, size, 0.004), V(c) + u * x + n * (t + 0.0005),
                             u, n, glow if i < lit else off_mat, rounded=0.0015, segments=1))
    return parts


def cell(name, a, b, r, glow, cap_mat="M_Brass", glass="M_Glass", bands=1):
    """Capacitor cell between a and b: glass jacket with a glowing core, domed brass end caps with
    terminal nubs and `bands` brass hoops."""
    a, b = V(a), V(b)
    ax = (b - a).normalized()
    L = (b - a).length
    parts = [pl.rod(name + "_glass", a + ax * (r * 0.4), b - ax * (r * 0.4), r, 14, glass),
             pl.capsule(name + "_core", a + ax * (r * 0.9), b - ax * (r * 0.9), r * 0.5, 10, 2, glow)]
    for p, d in ((a, -ax), (b, ax)):
        parts.append(pl.lathe_axis(name + "_cap", [(r * 1.18, -r * 0.55), (r * 1.18, r * 0.25), (r * 0.95, r * 0.55),
                                                   (r * 0.45, r * 0.72), (0.0, r * 0.74)], d, p, 14, cap_mat,
                                   True, False, 45))
        parts.append(pl.rod(name + "_nub", p + d * (r * 0.7), p + d * (r * 1.05), r * 0.3, 8, "M_Copper"))
    for k in range(bands):
        t = (k + 1) / (bands + 1)
        parts.append(pl.band(name + "_band", r * 1.12, min(0.008, L * 0.08), r * 0.25, ax, a.lerp(b, t), cap_mat, 14,
                             0.0))
    return parts


# --------------------------------------------------------------------------------------
# Plates, panels and ornament
# --------------------------------------------------------------------------------------

def plate(name, c, normal, w, h, t=0.005, up=(0, 0, 1), mat="M_Brass", rivets="M_Steel", rr=0.0045, inset=None,
          rounded=None, bevel_segs=2):
    """Rounded rectangular plate lying on a surface (back at c), with a rivet in each corner."""
    u, v, n = basis(normal, up)
    rounded = rounded if rounded is not None else min(t * 0.45, 0.004)
    parts = [pl.obox(name, (w, h, t), V(c) + n * (t / 2), u, n, mat, rounded=rounded, segments=bevel_segs)]
    if rivets:
        ins = inset if inset is not None else rr * 1.6
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(pl.rivet(V(c) + u * (sx * (w / 2 - ins)) + v * (sy * (h / 2 - ins)) + n * t, n, rr,
                                      rr * 0.7, rivets, 6))
    return parts


def ridge(name, pts, normal, width=0.006, height=0.003, mat="M_Brass", res=2, taper=None, smooth_path=True):
    """Half-round bead lying on a surface (filigree, weld seams, raised piping): a flat-bottomed sweep
    along `pts` whose height points along `normal`. `taper` = per-point scale list."""
    n = V(normal).normalized()
    sc = list(taper) if taper else [1.0] * len(pts)
    Q, S = pl._resample(pts, sc, res, smooth_path)
    prof = [(-0.5, 0.0), (-0.38, 0.6), (0.0, 1.0), (0.38, 0.6), (0.5, 0.0)]
    bm = bmesh.new()
    rings = []
    m = len(Q)
    for i in range(m):
        T = (Q[min(i + 1, m - 1)] - Q[max(i - 1, 0)])
        if T.length < 1e-9:
            T = V((1, 0, 0))
        T.normalize()
        s = T.cross(n).normalized()
        rings.append([bm.verts.new(Q[i] + s * (px * width * S[i]) + n * (pz * height * S[i])) for px, pz in prof])
    for i in range(m - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(len(prof) - 1):
            bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = pl.obj_from_bm(name, bm, mat, 0)
    # make sure the bead's faces point away from the surface it lies on
    up = sum((p.normal.dot(n) * p.area for p in o.data.polygons), 0.0)
    if up < 0:
        for p in o.data.polygons:
            p.flip()
    rw.smooth(o, 50)
    return o


def scroll_2d(a=0.36, R=0.3, turns=1.0, n=9, r_in=0.08):
    """2D S-scroll (unit size ~1.3 x 0.6): a spiral curling one way on the left, joined through the
    centre to a spiral curling the other way on the right. Returns (points, taper)."""
    pts, tap = [], []
    for i in range(n + 1):
        t = i / n
        ang = math.pi / 2 + 2 * math.pi * turns * (1 - t)
        rr = r_in + (R - r_in) * t
        pts.append((-a + rr * math.cos(ang), rr * math.sin(ang)))
        tap.append(0.55 + 0.45 * t)
    pts.append((0.0, 0.0))
    tap.append(1.0)
    for i in range(n + 1):
        t = i / n
        ang = -math.pi / 2 + 2 * math.pi * turns * t
        rr = R - (R - r_in) * t
        pts.append((a + rr * math.cos(ang), rr * math.sin(ang)))
        tap.append(1.0 - 0.45 * t)
    return pts, tap


def scroll(name, c, normal, size, up=(0, 0, 1), width=0.0055, height=0.0028, mat="M_Brass", flip=False, turns=1.0,
           angle=0.0):
    """Raised filigree S-scroll on a surface, `size` = overall length along u."""
    u, v, n = basis(normal, up)
    pts, tap = scroll_2d(turns=turns)
    k = size / 1.32
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    world = []
    for (x, y) in pts:
        if flip:
            y = -y
        xr, yr = x * ca - y * sa, x * sa + y * ca
        world.append(V(c) + u * (xr * k) + v * (yr * k))
    return ridge(name, world, n, width, height, mat, 2, tap)


def curl(name, c, normal, R, up=(0, 0, 1), turns=1.1, start=90.0, cw=True, width=0.0055, height=0.0028,
         mat="M_Brass", tail=None, n=9):
    """Single filigree spiral (centre c, outer radius R), optionally with a straight-ish tail point."""
    u, v, n_ = basis(normal, up)
    pts, tap = [], []
    for i in range(n + 1):
        t = i / n
        sgn = -1 if cw else 1
        ang = math.radians(start) + sgn * 2 * math.pi * turns * (1 - t)
        rr = R * (0.25 + 0.75 * t)
        pts.append(V(c) + u * (rr * math.cos(ang)) + v * (rr * math.sin(ang)))
        tap.append(0.55 + 0.45 * t)
    if tail is not None:
        pts.append(V(tail))
        tap.append(0.6)
    return ridge(name, pts, n_, width, height, mat, 2, tap)


def rune(key, c, normal, size, up=(0, 0, 1), width=0.0055, depth=0.004, mat="M_RuneGlow", name="rune"):
    """Glowing rune glyph inlaid in a surface (strokes half sunk), from partlib's RUNES table."""
    u, v, n = basis(normal, up)
    return pl.glyph(key, V(c), u, v, size, width, depth, mat, name)


def bolt_emblem(name, c, normal, size, up=(0, 0, 1), t=0.003, mat="M_Copper"):
    """Chunky lightning-bolt emblem (for maker's plates)."""
    u, v, n = basis(normal, up)
    pts = [(-0.12, 0.5), (0.3, 0.5), (0.06, 0.1), (0.3, 0.1), (-0.2, -0.5), (-0.02, -0.06), (-0.26, -0.06)]
    pts = [(x * size, y * size) for x, y in pts]
    return prism(name, list(reversed(pts)), c, u, v, n, t, mat, 0.0, 0.0008, 30)


# --------------------------------------------------------------------------------------
# Cables, wraps and paint
# --------------------------------------------------------------------------------------

def wires(name, pts, count=2, r=0.0045, gap=0.0008, mats=("M_Copper",), up=(0, 0, 1), segs=6, res=3):
    """A flat bundle of `count` parallel cables along a path (side by side across path x up)."""
    P = [V(p) for p in pts]
    out = []
    for k in range(count):
        off = (k - (count - 1) / 2) * (2 * r + gap)
        Q = []
        for i in range(len(P)):
            T = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            s = T.cross(V(up))
            if s.length < 1e-6:
                s = T.orthogonal()
            Q.append(P[i] + s.normalized() * off)
        out.append(pl.sausage(name, Q, r, segs, res, mats[k % len(mats)], (True, True), 2, True, 70))
    return out


def clamp(name, c, along, size, up=(0, 0, 1), mat="M_Brass"):
    """Small rounded strap block wrapped across a cable bundle (`along` = cable direction)."""
    a = V(along).normalized()
    x = V(up).cross(a)
    if x.length < 1e-6:
        x = a.orthogonal()
    return pl.obox(name, (size[0], size[1], size[2]), c, x.normalized(), a.cross(x).normalized(), mat,
                   rounded=min(size) * 0.3, segments=1)


def wrap(name, c0, c1, r, n, mat="M_Leather__5a3420", thick=0.004, tilt=9.0, side=(1, 0, 0), segs=14):
    """Spiral leather wrap from c0 to c1 around a round handle of radius r: n overlapping tilted bands."""
    c0, c1 = V(c0), V(c1)
    ax = (c1 - c0).normalized()
    L = (c1 - c0).length
    w = L / n * 1.18
    q = Matrix.Rotation(math.radians(tilt), 3, V(side).cross(ax).normalized() if V(side).cross(ax).length > 1e-6
                        else ax.orthogonal())
    out = []
    for i in range(n):
        p = c0.lerp(c1, (i + 0.5) / n)
        out.append(pl.band(name, r + thick, w, thick * 1.6, q @ ax, p, mat, segs, 0.45))
    return out


def stitches(pts, normal, mat="M_Leather__d9c08c", r=0.0022, dash=0.008, gap=0.005):
    """Running stitches (small capsules) along a polyline on a surface."""
    P = [V(p) for p in pts]
    n = V(normal).normalized()
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        L = (b - a).length
        d = (b - a).normalized()
        t = 0.0
        while t + dash <= L + 1e-6:
            p0 = a + d * t + n * (r * 0.4)
            out.append(pl.capsule("stitch", p0, p0 + d * dash, r, 4, 1, mat))
            t += dash + gap
    return out


def hazard_band(name, c, axis, radius, width, count=8, slant=30.0, half_w=11.0, thick=0.012, steps=4, cols=4,
                segs=32, inner=False):
    """Yellow band with `count` black slanted stripes hugging its surface (around `axis` through c).
    The stripes are thin shells sunk into the band (inner=False skips their buried inner faces)."""
    flat_mats()
    parts = [pl.band(name, radius, width, thick, (0, 0, 1), (0, 0, 0), "WarnYellow", segs, 0.0)]
    bm = bmesh.new()
    for k in range(count):
        a0 = 360.0 * k / count
        grids = []
        for rr in (radius + 0.0016, radius - 0.004):
            grid = []
            for j in range(steps + 1):
                t = j / steps
                z = -width / 2 + 0.003 + (width - 0.006) * t
                row = []
                for cc in range(cols + 1):
                    a = math.radians(a0 + slant * t + half_w * (2 * cc / cols - 1))
                    row.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z)))
                grid.append(row)
            grids.append(grid)
        out, inn = grids
        for j in range(steps):
            for cc in range(cols):
                bm.faces.new((out[j][cc], out[j][cc + 1], out[j + 1][cc + 1], out[j + 1][cc]))
                if inner:
                    bm.faces.new((inn[j][cc], inn[j + 1][cc], inn[j + 1][cc + 1], inn[j][cc + 1]))
        # side walls, wound so their normals face away from the stripe
        for j in range(steps):
            bm.faces.new((out[j][0], out[j + 1][0], inn[j + 1][0], inn[j][0]))
            bm.faces.new((out[j][cols], inn[j][cols], inn[j + 1][cols], out[j + 1][cols]))
        for cc in range(cols):
            bm.faces.new((out[0][cc], inn[0][cc], inn[0][cc + 1], out[0][cc + 1]))
            bm.faces.new((out[steps][cc], out[steps][cc + 1], inn[steps][cc + 1], inn[steps][cc]))
    if inner:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(pl.obj_from_bm(name + "_stripes", bm, "WarnBlack", 0))
    for o in parts:
        pl.align(o, axis, V(c))
    return parts


def sling_ring(name, c, normal, r=0.011, wire=0.0035, mat="M_Steel", up=(0, 0, 1), base_mat="M_Brass"):
    """Sling / lanyard ring hanging from a small eye stud on a surface (ring plane contains normal & v)."""
    u, v, n = basis(normal, up)
    c = V(c)
    stud = pl.lathe_axis(name + "_stud", [(wire * 2.4, -0.002), (wire * 2.4, wire * 0.8), (wire * 1.6, wire * 2.2),
                                          (0.0, wire * 2.4)], n, c, 10, base_mat, False, False, 50)
    ring = rw.torus(name, r, wire, 12, 6, (0, 0, 0), mat=mat)
    pl.align(ring, u, c + n * (wire * 2.2 + r - wire * 0.5))
    return [stud, ring]
