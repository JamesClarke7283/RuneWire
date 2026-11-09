"""bldlib: helpers for the RuneWire buildings (bld_*.py in art/blender/env/).

Import from a building generator script:

    import os, sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bldlib as B
    E, rw, V = B.E, B.rw, B.V
    B.reset()

Builds on envlib (E) and rwlib (rw); neither is edited. Same conventions as envlib: metres, +Z up, the front
faces -Y, rotations in DEGREES, origin at the ground centre.
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

# Extra flat / glow accents used by the buildings (envlib.ACCENTS covers the rest).
EXTRA = {
    "RuneWindow": ("glow", "b58cff", 1.5),      # violet rune-glass (magic shop)
    "TealWindow": ("glow", "5ff0dc", 1.5),      # teal rune-glass
    "StarGold": ("flat", "ffcf4a", 0.35, 0.6),  # banner star, finials
    "PaintViolet": ("flat", "6d3fb0", 0.55, 0.0),
    "PaintNavy": ("flat", "2b3a6b", 0.6, 0.0),
    "PaintOrange": ("flat", "e8762c", 0.55, 0.0),
    "PaintYellow": ("flat", "f2c12e", 0.55, 0.0),
    "Brick": ("flat", "b5583f", 0.85, 0.0),
    "Concrete": ("flat", "9a968e", 0.9, 0.0),
    "Bulb": ("glow", "ffd98a", 3.0),
    "Ember": ("glow", "ff8a3a", 2.5),
}


def reset():
    """rw.reset() plus the EXTRA accent materials (so their names resolve anywhere)."""
    sc = rw.reset()
    for k, v in EXTRA.items():
        if v[0] == "glow":
            rw.glow(k, v[1], v[2])
        else:
            rw.flat(k, v[1], v[2], v[3])
    return sc


def mat(m):
    if isinstance(m, str) and m in EXTRA:
        return bpy.data.materials.get(m) or m
    return E.mat(m)


def _obj(name, bm, m=None, smooth=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m is not None:
        rw.set_mat(o, mat(m))
    if smooth:
        rw.smooth(o, smooth)
    return o


# --------------------------------------------------------------------------------------
# Sweeps, profiles, beams
# --------------------------------------------------------------------------------------

def sweep(name, prof, d, t=0.1, m=None, smooth=None):
    """Thick sheet: the open 3D polyline `prof` swept straight along the vector `d`. The sheet is `t` thick,
    offset from prof towards -(tangent x d) (pass a negative t to thicken the other way). Closed manifold."""
    d = V(d)
    pts = [V(p) for p in prof]
    n = len(pts)
    offs = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        nn = (b - a).normalized().cross(d).normalized()
        k = 1.0
        if 0 < i < n - 1:
            n0 = (pts[i] - pts[i - 1]).normalized().cross(d).normalized()
            k = max(0.5, nn.dot(n0))
        offs.append(nn * (t / k))
    bm = bmesh.new()
    A = [bm.verts.new(p) for p in pts]
    Bv = [bm.verts.new(p + d) for p in pts]
    C = [bm.verts.new(p - o) for p, o in zip(pts, offs)]
    D = [bm.verts.new(p - o + d) for p, o in zip(pts, offs)]
    for i in range(n - 1):
        j = i + 1
        bm.faces.new((A[i], A[j], Bv[j], Bv[i]))
        bm.faces.new((C[i], D[i], D[j], C[j]))
        bm.faces.new((A[i], C[i], C[j], A[j]))
        bm.faces.new((Bv[i], Bv[j], D[j], D[i]))
    bm.faces.new((A[0], Bv[0], D[0], C[0]))
    bm.faces.new((A[-1], C[-1], D[-1], Bv[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, m, smooth)


def loft(name, rings, m=None, cap0=True, cap1=True, smooth=None):
    """Skin a list of closed rings (each a list of 3D points, same count) into a tube; optional end caps."""
    bm = bmesh.new()
    R = [[bm.verts.new(V(p)) for p in r] for r in rings]
    k = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for i in range(k):
            j = (i + 1) % k
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap0:
        bm.faces.new(list(reversed(R[0])))
    if cap1:
        bm.faces.new(R[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, m, smooth)


def _frame(p0, p1, up):
    z = (V(p1) - V(p0)).normalized()
    u = V(up)
    if abs(u.normalized().dot(z)) > 0.999:
        u = V((0, 1, 0)) if abs(z.y) < 0.9 else V((1, 0, 0))
    y = (u - z * u.dot(z)).normalized()
    x = y.cross(z)
    return x, y, z


def prism_along(name, prof2d, p0, p1, up=(0, 0, 1), m=None, bevel=0.0, smooth=None):
    """Extrude a closed 2D profile [(x, y)] from p0 to p1. Profile y points towards `up` (projected),
    profile x = y cross (p1 - p0)."""
    x, y, z = _frame(p0, p1, up)
    L = (V(p1) - V(p0)).length
    bm = bmesh.new()
    a = [bm.verts.new(V(p0) + x * px + y * py) for (px, py) in prof2d]
    b = [bm.verts.new(V(p0) + x * px + y * py + z * L) for (px, py) in prof2d]
    k = len(prof2d)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m, None)
    if bevel > 0:
        rw.add_bevel(o, bevel, 1, 40, harden=False)
    if smooth:
        rw.smooth(o, smooth)
    return o


def ibeam(name, p0, p1, h=0.3, w=0.22, tf=0.05, tw=0.05, m="M_PaintedMetal", up=(0, 0, 1), bevel=0.0):
    """Steel I-beam from p0 to p1: depth h along `up` (the web), flange width w across it."""
    hw, hh = w / 2, h / 2
    prof = [(-hw, -hh), (hw, -hh), (hw, -hh + tf), (tw / 2, -hh + tf), (tw / 2, hh - tf), (hw, hh - tf), (hw, hh),
            (-hw, hh), (-hw, hh - tf), (-tw / 2, hh - tf), (-tw / 2, -hh + tf), (-hw, -hh + tf)]
    return prism_along(name, prof, p0, p1, up, m, bevel)


def bar(name, p0, p1, w=0.1, h=0.1, m="M_Steel", up=(0, 0, 1), extend=0.0):
    """Plain box beam (12 tris) from p0 to p1."""
    return E.beam(name, p0, p1, w, h, mat(m), 0.0, up=up, extend=extend)


def hazard_bar(p0, p1, w=0.2, h=0.2, n=8, up=(0, 0, 1), a="HazardYellow", b="HazardBlack"):
    """Box beam split into n alternating yellow / black bands."""
    p0, p1 = V(p0), V(p1)
    out = []
    for i in range(n):
        q0 = p0.lerp(p1, i / n)
        q1 = p0.lerp(p1, (i + 1) / n)
        out.append(bar("haz", q0, q1, w, h, a if i % 2 == 0 else b, up))
    return out


# --------------------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------------------

def vault_profile(hx, z_spring, rise, n=14, kick=0.45, drop=0.2, lift=0.0):
    """Barrel-vault cross-section [(x, z)] from -x to +x: a half ellipse of half-width hx and height `rise` above
    z_spring, plus a bell-cast eave kick (outwards by `kick`, down by `drop`) at both ends."""
    pts = []
    if kick > 0:
        pts.append((-(hx + kick), z_spring - drop + lift))
    for i in range(n + 1):
        phi = -math.pi / 2 + math.pi * i / n
        pts.append((hx * math.sin(phi), z_spring + lift + rise * math.cos(phi)))
    if kick > 0:
        pts.append((hx + kick, z_spring - drop + lift))
    return pts


def corrugate(p0, p1, normal, amp=0.04, period=0.32, steps=4):
    """Points along p0 -> p1 displaced by a sine wave along `normal` (corrugated sheet cross-section)."""
    p0, p1, nn = V(p0), V(p1), V(normal).normalized()
    L = (p1 - p0).length
    waves = max(1, int(round(L / period)))
    k = waves * steps
    return [tuple(p0.lerp(p1, i / k) + nn * amp * math.sin(2 * math.pi * i / steps)) for i in range(k + 1)]


def scallop_outline(w, h_top, depth, n, bottom_z=0.0, res=4):
    """Outline (x, z) of a valance strip of width w: straight top at h_top, n scallops at the bottom."""
    pts = [(w / 2, h_top), (-w / 2, h_top)]
    for i in range(n):
        x0 = -w / 2 + w * i / n
        for k in range(res + 1):
            if i > 0 and k == 0:
                continue
            t = k / res
            x = x0 + w / n * t
            pts.append((x, bottom_z - depth * math.sin(math.pi * t)))
    return pts


# --------------------------------------------------------------------------------------
# Machine bits
# --------------------------------------------------------------------------------------

def gear_wheel(name, r, teeth, loc, normal=(0, -1, 0), thick=0.15, depth=None, rim=None, spokes=5, hub=None,
               m="M_Brass", hub_m=None, spin=0.0, up=(0, 0, 1), spoke_w=None, bevel=0.0):
    """Spoked cartoon gear: toothed rim + hub + spokes, facing `normal`. Returns a list of parts."""
    depth = r * 0.15 if depth is None else depth
    rim = r * 0.17 if rim is None else rim
    hole = r - depth - rim
    c = V(loc)
    n = V(normal).normalized()
    parts = [E.gear(name, r, teeth, depth, thick, hole, tuple(c), tuple(n), mat(m), bevel=bevel, spin=spin)]
    hub = r * 0.22 if hub is None else hub
    if hub > 0:
        parts.append(rw.cylinder(name + "_hub", hub, thick * 1.5, 12, tuple(c), E.z_to_euler(n), mat(hub_m or m)))
        parts.append(rw.cylinder(name + "_cap", hub * 0.45, thick * 1.9, 8, tuple(c), E.z_to_euler(n), mat("M_Steel")))
    u = V(up)
    e1 = (u - n * u.dot(n)).normalized()
    e2 = n.cross(e1)
    sw = spoke_w or max(0.05, r * 0.13)
    for i in range(spokes):
        a = 2 * math.pi * i / spokes + math.radians(spin) + math.pi / 2
        dv = e1 * math.cos(a) + e2 * math.sin(a)
        parts.append(E.beam(name + "_spk", tuple(c + dv * hub * 0.7), tuple(c + dv * (hole + rim * 0.5)), sw, thick * 0.75,
                            mat(m), 0.0, up=tuple(n)))
    return parts


def pendant_lamp(top, drop=1.2, shade_r=0.32, shade_m="M_PaintedMetal__2e7d5a", glow="Bulb", seg=12):
    """Industrial pendant lamp hanging `drop` below `top`: rod, enamel cone shade, glowing bulb.
    Returns (parts, bulb_location)."""
    t = V(top)
    c = t - V((0, 0, drop))
    parts = [E.rod("lrod", tuple(t), tuple(c + V((0, 0, 0.14))), 0.022, 6, "IronDark")]
    parts.append(rw.cylinder("lcap", 0.07, 0.1, 8, tuple(c + V((0, 0, 0.14))), (0, 0, 0), mat("M_Brass")))
    shade = E.lathe("lshade", [(0.06, 0.12), (shade_r * 0.35, 0.1), (shade_r * 0.8, -0.02), (shade_r, -0.12),
                               (shade_r * 1.02, -0.16), (shade_r * 0.96, -0.16), (shade_r * 0.74, -0.06),
                               (shade_r * 0.3, 0.06)], seg, loc=tuple(c), m=mat(shade_m), cap_bottom=False,
                    cap_top=False, smooth=40)
    parts.append(shade)
    bulb_c = c - V((0, 0, 0.1))
    parts.append(rw.sphere("bulb", 0.1, 8, 5, tuple(bulb_c), (0, 0, 0), (1, 1, 1.15), mat(glow)))
    return parts, tuple(bulb_c)


def ladder(p0, p1, w=0.55, step=0.32, rail_w=0.08, rung_r=0.028, m="M_WoodDark", rung_m=None, side=(1, 0, 0)):
    """Ladder from p0 (bottom centre) to p1 (top centre); rails are separated along `side`."""
    p0, p1 = V(p0), V(p1)
    s = V(side).normalized()
    d = p1 - p0
    parts = []
    for k in (-1, 1):
        parts.append(E.beam("lrail", tuple(p0 + s * k * w / 2), tuple(p1 + s * k * w / 2), rail_w, rail_w * 0.8,
                            mat(m), 0.012, up=tuple(s.cross(d).normalized())))
    n = int(d.length / step)
    for i in range(1, n + 1):
        q = p0 + d * (i * step / d.length)
        if (q - p0).length > d.length - 0.1:
            break
        parts.append(E.rod("rung", tuple(q - s * w / 2), tuple(q + s * w / 2), rung_r, 6, mat(rung_m or m)))
    return parts


def crystal(name, loc, r=0.25, h=0.9, tilt=(0.0, 0.0), m="M_Crystal", sides=6, twist=0.0, mid=None):
    """Single faceted crystal (bipyramid) tilted by (tilt_x, tilt_y) degrees about its centre."""
    mid = h * 0.45 if mid is None else mid
    o = E.bipyramid(name, r, h * 0.35, h * 0.2, sides, (0, 0, 0), mat(m), twist, mid)
    E.place([o], loc, (tilt[0], tilt[1], 0))
    return o


def crystal_cluster(loc, size=1.0, n=5, seed=0, m="M_Crystal", spread=25.0):
    rnd = random.Random(seed)
    out = []
    c = V(loc)
    for i in range(n):
        s = size * (1.0 if i == 0 else rnd.uniform(0.45, 0.75))
        a = 2 * math.pi * i / max(1, n - 1) + rnd.uniform(-0.3, 0.3)
        off = V((math.cos(a), math.sin(a), 0)) * (0 if i == 0 else size * 0.18)
        tilt = (0.0, 0.0) if i == 0 else (-math.sin(a) * spread, math.cos(a) * spread)
        out.append(crystal("cry", tuple(c + off + V((0, 0, s * 0.35))), 0.18 * s, s, tilt, m, 6, rnd.uniform(0, 30)))
    return out


def star_prism(name, r_out, r_in, depth, loc, normal=(0, -1, 0), m="StarGold", n=5, up=(0, 0, 1), rot=0.0):
    pts = E.star_points(n, r_out, r_in, 90.0 + rot)
    nn = V(normal).normalized()
    u = V(up)
    u = (u - nn * u.dot(nn)).normalized()
    x = u.cross(nn)
    # local polygon XY -> (x, u), extrusion along local Z -> nn
    Mx = Matrix((x, u, nn)).transposed()
    o = rw.extrude_poly(name, pts, depth, (0, 0, 0), (0, 0, 0), mat(m), 0.0)
    E.place([o], loc, E.deg(Mx.to_euler()))
    return o


# --------------------------------------------------------------------------------------
# Lights, collision, QA
# --------------------------------------------------------------------------------------

class Lights:
    """Collect LightPoint locations while building, emit the empties after the final deformation."""

    def __init__(self):
        self.pts = []

    def add(self, p):
        self.pts.append(V(p))
        return p

    def emit(self, W=None, prefix="LightPoint"):
        out = []
        for i, p in enumerate(self.pts):
            q = W(p) if W else p
            out.append(rw.empty("%s_%d" % (prefix, i), tuple(q)))
        return out


def col_prism_xz(tag, pts_xz, y0, y1):
    """Convex collision prism from an (x, z) outline extruded between y0 and y1."""
    return E.col_hull(tag, [(x, y, z) for (x, z) in pts_xz for y in (y0, y1)])


def wedge_pts(C, r0, r1, th0, th1, z0, z1):
    """The 8 corners of an annular-sector block (angles in degrees from +Y towards +X about C)."""
    out = []
    for th in (th0, th1):
        for r in (r0, r1):
            for z in (z0, z1):
                out.append(E.ring_point(C, r, th, z))
    return out



def helix_band(dirfn, rfn, th0, th1, z0, z1, h=0.36, proud=0.12, n=48, m="M_StoneRough", inset=0.06, chamfer=0.04):
    """Stone ledge spiralling round a tower: from angle th0 at height z0 to th1 at z1 (degrees, dirfn(theta) gives
    the unit outward direction, rfn(z) the wall radius). Cross-section h tall, standing `proud` off the wall."""
    rings = []
    for i in range(n + 1):
        t = i / n
        th = th0 + (th1 - th0) * t
        z = z0 + (z1 - z0) * t
        dv = dirfn(th)
        r = rfn(z)
        ring = []
        for (rr, zz) in ((r - inset, z - h / 2), (r + proud, z - h / 2 + chamfer), (r + proud, z + h / 2 - chamfer), (r - inset, z + h / 2)):
            ring.append(dv * rr + V((0, 0, zz)))
        rings.append(ring)
    return loft("helix", rings, m, True, True, smooth=40)


# --------------------------------------------------------------------------------------
# Arena ring (bld_arena_wall / bld_arena_gate). 24 segments of 15 degrees; the ring centre is at (0, -30) in a
# segment's frame; the origin is the ground centre of the inner face. Angles: degrees from +Y towards +X about the
# ring centre (envlib.ring_point). Every continuous layer ends exactly on the radial planes at +-7.5 degrees, and
# both segment types build their ends from the same table below, so neighbours close the ring without gaps.
# --------------------------------------------------------------------------------------

ARENA_C = (0.0, -30.0)
AR0, AR1 = 30.0, 32.5          # inner / outer face radius
AHALF = 7.5                    # half angle of one segment
APIL = 1.1                     # angular width of the half pilaster at each end
ARENA_LAYERS = (
    # name, r0, r1, z0, z1, material
    ("aplinth", 29.72, 32.78, -0.2, 0.7, "M_StoneRough"),
    ("awall", 30.0, 32.5, 0.65, 6.22, "M_Stone"),
    ("acornice", 29.8, 30.05, 5.86, 6.2, "M_StoneRough"),
    ("aocornice", 32.45, 32.7, 5.86, 6.2, "M_StoneRough"),
    ("aparapet", 29.95, 30.6, 6.18, 6.62, "M_Stone"),
    ("aoparapet", 32.05, 32.55, 6.18, 6.98, "M_Stone"),
    ("awalk", 30.58, 32.07, 6.18, 6.28, "M_StoneRough"),
    ("aocoping", 32.0, 32.62, 6.96, 7.06, "M_StoneRough"),
    ("arune", 29.765, 29.83, 5.96, 6.09, "M_RuneGlow"),      # glowing rune line round the whole arena
)


def arena_band(th0, th1, layers=ARENA_LAYERS):
    """The wall's layered cross-section swept between angles th0..th1 (chord facets every <= 2.5 degrees)."""
    out = []
    for (name, r0, r1, z0, z1, m) in layers:
        nu = max(1, int(math.ceil((th1 - th0) / 2.5 - 1e-6)))
        out.append(E.arc_block(name, ARENA_C, r0, r1, th0, th1, z0, z1, nu, m))
    return out


def arena_half_pilasters(th_a, th_b):
    """Half pilasters (inner and outer face) between th_a..th_b; two halves meet at each segment joint."""
    C = ARENA_C
    out = [E.arc_block("pil", C, 29.66, 30.02, th_a, th_b, 0.68, 5.88, 1, "M_Stone"),
           E.arc_block("pilbase", C, 29.58, 30.02, th_a, th_b, 0.66, 1.05, 1, "M_StoneRough"),
           E.arc_block("pilcap", C, 29.56, 30.02, th_a, th_b, 5.5, 5.86, 1, "M_StoneRough"),
           E.arc_block("opil", C, 32.48, 32.84, th_a, th_b, 0.68, 5.88, 1, "M_Stone"),
           E.arc_block("opilbase", C, 32.48, 32.92, th_a, th_b, 0.66, 1.05, 1, "M_StoneRough"),
           E.arc_block("opilcap", C, 32.48, 32.94, th_a, th_b, 5.5, 5.86, 1, "M_StoneRough")]
    return out


def ring_bend(objs, R, C=ARENA_C):
    """Wrap details built flat onto a ring face: local x = arc length along the face (radius R), local y = offset
    along the ring normal (negative = towards the ring centre), z unchanged. A detail at x = 0, y = 0 sits at the
    face's mid point (theta = 0)."""
    def fn(p):
        return V(E.ring_point(C, R + p.y, math.degrees(p.x / R), p.z))
    for o in objs:
        if o is not None and o.type == 'MESH':
            E.deform(o, fn)
    return objs


def ley_pylon(theta, r, z, s=1.0, C=ARENA_C, cs=1.4):
    """Brass ley pylon on a stone pedestal with copper coils, three prongs and a floating teal crystal.
    Base at (theta, r, z). Returns (parts, crystal_centre)."""
    c = V(E.ring_point(C, r, theta, z))
    parts = [E.cbox("pyped", (0.9 * s, 0.9 * s, 0.42 * s), tuple(c + V((0, 0, 0.21 * s))), (0, 0, -theta), "M_StoneRough", 0.05)]
    parts.append(E.lathe("pycol", [(0.3 * s, 0.4 * s), (0.3 * s, 0.5 * s), (0.22 * s, 0.62 * s), (0.17 * s, 1.35 * s),
                                   (0.22 * s, 1.42 * s), (0.22 * s, 1.5 * s), (0.12 * s, 1.56 * s)], 10,
                         loc=tuple(c), m="M_Brass", smooth=40))
    for zz in (0.78, 1.05):
        parts.append(E.ring("pycoil", 0.205 * s, 0.045 * s, tuple(c + V((0, 0, zz * s))), (0, 0, 1), "M_Copper", 12, 5))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.radians(theta)
        dv = V((math.cos(a), math.sin(a), 0))
        parts.append(E.tube("pyprong", [tuple(c + dv * 0.12 * s + V((0, 0, 1.5 * s))), tuple(c + dv * 0.34 * s + V((0, 0, 1.72 * s))),
                                        tuple(c + dv * 0.3 * s + V((0, 0, 1.95 * s)))], 0.045 * s, "M_Brass", 1, smooth=True, ures=2))
    cc = c + V((0, 0, 1.86 * s))
    parts.append(crystal("pycrystal", tuple(cc), 0.17 * s * cs, 0.62 * s * cs, (0, 0), "M_Crystal", 6, theta))
    parts.append(E.ring("pyglow", 0.3 * s, 0.03 * s, tuple(c + V((0, 0, 1.6 * s))), (0, 0, 1), "TealGlow", 14, 4))
    return parts, tuple(cc)


def arena_hulls(tag, th0, th1, r0, r1, z0, z1, n=3, C=ARENA_C):
    """Convex collision wedges covering an annular sector (n sub-wedges keep the concave inner face accurate)."""
    out = []
    for i in range(n):
        a = th0 + (th1 - th0) * i / n
        b = th0 + (th1 - th0) * (i + 1) / n
        out.append(E.col_hull(tag, wedge_pts(C, r0, r1, a, b, z0, z1)))
    return out
