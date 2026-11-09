"""techlib: hard-surface helpers for the Cogwork Legion enemies (enemy_drone, enemy_sentry, enemy_ironclad).

Builds on rwlib, charlib and partlib (none of which may be edited). Same conventions: metres, +Z up,
the front faces -Y, a character's LEFT is +X, angles in degrees. Mesh builders return objects whose
vertices are already in world space; `node()` joins them into an animated node (origin on the pivot).

    import os, sys
    sys.dont_write_bytecode = True
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    sys.path.insert(0, HERE)
    import rwlib as rw
    import charlib as cl
    import techlib as tl
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, ".."), os.path.join(HERE, "..", "parts"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import partlib as pl  # noqa: E402

V = Vector

# Legion palette (matches enemy_crawler): rust-orange armour paint, hazard yellow/black, orange glow.
PAINT = "M_PaintedMetal__c8452c"
HAZ_Y = cl.HAZ_Y
GLOW = "M_TechGlow"
GRILLE = "GrilleDark"


def setup():
    """Shared flat materials; call right after rw.reset()."""
    cl.hazard_black()
    rw.flat(GRILLE, "1d1b20", 0.6, 0.3)
    rw.glow("EyeShine", "ffffff", 1.2)


# ======================================================================================
# Math
# ======================================================================================

def az_dir(az, z=0.0):
    """Horizontal unit direction for an azimuth in degrees: 0 = front (-Y), 90 = left (+X)."""
    a = math.radians(az)
    return V((math.sin(a), -math.cos(a), z))


def rot_z_to(axis):
    """3x3 rotation taking +Z onto `axis` (for tori, rivet rings and lathes)."""
    return V((0, 0, 1)).rotation_difference(V(axis).normalized()).to_matrix()


RX90 = Matrix.Rotation(math.radians(90), 3, 'X')   # local +Z -> -Y (faces the front)
RY90 = Matrix.Rotation(math.radians(90), 3, 'Y')   # local +Z -> +X


# ======================================================================================
# Assembly
# ======================================================================================

PART_REPORT = os.environ.get("RW_PARTS") == "1"   # print triangles per part (budget tuning)


def node(name, parts, pivot, parent=None):
    """charlib.node with a depsgraph update first, so parts placed via .location are where they look."""
    bpy.context.view_layer.update()
    if PART_REPORT:
        tally = {}
        for o in cl.flatten(parts):
            k = o.name.split(".")[0]
            n, c = tally.get(k, (0, 0))
            tally[k] = (n + rw.tri_count([o]), c + 1)
        for k, (n, c) in sorted(tally.items(), key=lambda kv: -kv[1][0]):
            print("RWPART   %-10s %-16s %5d tris (%d parts)" % (name, k, n, c))
    o = cl.node(name, parts, V(pivot), parent)
    bpy.context.view_layer.update()
    return o


def empty(name, loc, parent=None, size=0.1):
    """Attachment empty at a world location, parented without moving (charlib.empty parents before the
    depsgraph has computed the new location, which drops the empty at the parent's origin)."""
    e = rw.empty(name, tuple(loc), None, size)
    if e.name != name:
        raise RuntimeError("empty name clash: wanted %s, got %s" % (name, e.name))
    bpy.context.view_layer.update()
    if parent is not None:
        rw.set_parent(e, parent)
        bpy.context.view_layer.update()
    return e


# ======================================================================================
# Parts
# ======================================================================================

def superellipse(a, b, n=24, e=0.5):
    """2D points of a superellipse with half sizes a, b (e = 1: ellipse, smaller e: boxier)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** e, c), b * math.copysign(abs(s) ** e, s)))
    return pts


def loft(name, sections, n=24, e=0.5, mat=None, M=None, cap_start=True, cap_end=True, smooth_angle=50.0):
    """Chunky hull: loft through superellipse cross-sections stacked along local Z, then placed by the
    4x4 matrix M (default: world space). A section is (z, a, b[, cx, cy[, e]]); a or b = 0 makes a pole."""
    rings = []
    for sec in sections:
        z, a, b = sec[0], sec[1], sec[2]
        cx = sec[3] if len(sec) > 3 else 0.0
        cy = sec[4] if len(sec) > 4 else 0.0
        ee = sec[5] if len(sec) > 5 else e
        if a <= 1e-6 or b <= 1e-6:
            rings.append(V((cx, cy, z)))
        else:
            rings.append([V((cx + x, cy + y, z)) for (x, y) in superellipse(a, b, n, ee)])
    if M is not None:
        rings = [(M @ r) if isinstance(r, Vector) else [M @ p for p in r] for r in rings]
    return cl.skin(name, rings, mat, cap_start, cap_end, smooth=True, smooth_angle=smooth_angle)


def limb_frame(top, bottom, pivot=None):
    """4x4 frame for a limb loft: origin at `top` (or `pivot`), local -Z runs from top to bottom, local X
    stays as close to world X as possible."""
    d = (V(top) - V(bottom)).normalized()
    R = pl.frame_matrix(d, (1, 0, 0))
    return Matrix.Translation(V(pivot if pivot is not None else top)) @ R.to_4x4()


def blade(name, hub, direction, r0, r1, width, thick=0.02, pitch=16.0, mat="M_Steel", tip_mat=None, tip_from=0.78,
          segs=8):
    """Cartoon rotor paddle in the horizontal plane through `hub`: root at radius r0, rounded tip at r1,
    `width` = chord, pitched `pitch` degrees about its own radial axis. The outer part can be painted."""
    d = V(direction)
    d.z = 0.0
    d.normalize()
    hub = V(hub)
    nrm = Matrix.Rotation(math.radians(pitch), 3, d) @ V((0, 0, 1))
    ts = [0.0, 0.2, 0.45, 0.66, 0.8, 0.9, 0.96, 1.0]
    pts, rad = [], []
    for t in ts:
        pts.append(hub + d * (r0 + (r1 - r0) * t))
        if t <= 0.8:
            w = 0.58 + 0.42 * math.sin(min(1.0, t / 0.66) * math.pi / 2)
        else:
            w = math.sqrt(max(0.0, 1.0 - ((t - 0.8) / 0.2) ** 2))
        rad.append(width / 2 * w)
    rad[-1] = 0.0
    o = cl.sweep(name, pts, rad, segs, mat, scale=(thick / width, 1.0), up=nrm)
    if tip_mat:
        lim = r0 + (r1 - r0) * tip_from
        rw.set_mat_where(o, tip_mat, lambda c, n: ((c - hub) - nrm * (c - hub).dot(nrm)).length > lim)
    return o


def hazard_ring(name, center, r_out, r_in, z0, z1, count=8, slant=45.0, cols=24, inner_mat="M_DarkMetal"):
    """Thick ring around a vertical axis through `center` (x, y) whose OUTER face carries `count` pairs of
    yellow/black hazard stripes slanted `slant` degrees; the inner, top and bottom faces use `inner_mat`.

    The outer wall is `cols` PLANAR facets and the stripes are clipped into them (like charlib.hazard_panel),
    so stripe borders never fold. (charlib.hazard_band twists its quads, which on a short band folds each
    stripe ~45 degrees and makes the outline pass draw a crease line through every stripe; it also stripes
    the inside, which looks busy inside a fan duct.)"""
    cl.hazard_black()
    cx, cy = center[0], center[1]
    circ = 2 * math.pi * r_out
    W = circ / (2 * count)               # stripe width along the wall (stripes tile the ring exactly)
    k = math.tan(math.radians(slant))    # stripe drift along the wall per metre of height
    du = circ / cols
    bm = bmesh.new()

    def edge_us(c, z):
        """u values along the outer wall edge at height z inside column c (column ends + stripe borders)."""
        u0, u1 = c * du, (c + 1) * du
        off = k * (z - z0)
        out = [u0]
        j = math.floor((u0 - off) / W) + 1
        while j * W + off < u1 - 1e-7:
            if j * W + off > u0 + 1e-7:
                out.append(j * W + off)
            j += 1
        out.append(u1)
        return out

    for c in range(cols):
        u0, u1 = c * du, (c + 1) * du
        quad = [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
        s_lo, s_hi = u0 - k * (z1 - z0), u1
        for j in range(int(math.floor(s_lo / W)), int(math.floor(s_hi / W)) + 1):
            poly = cl._clip(quad, 1.0, -k, j * W - k * z0)
            poly = cl._clip(poly, -1.0, k, -(j + 1) * W + k * z0) if poly else poly
            if len(poly) < 3:
                continue
            f = bm.faces.new([_ring_pt(bm, cx, cy, r_out, cols, c, (u - u0) / du, z) for (u, z) in poly])
            f.material_index = j % 2
        # inner wall, top and bottom annuli for this column (they pick up the stripe border vertices)
        ib0 = _ring_pt(bm, cx, cy, r_in, cols, c, 0.0, z0)
        ib1 = _ring_pt(bm, cx, cy, r_in, cols, c, 1.0, z0)
        it0 = _ring_pt(bm, cx, cy, r_in, cols, c, 0.0, z1)
        it1 = _ring_pt(bm, cx, cy, r_in, cols, c, 1.0, z1)
        bm.faces.new((ib0, it0, it1, ib1)).material_index = 2
        top = [_ring_pt(bm, cx, cy, r_out, cols, c, (u - u0) / du, z1) for u in edge_us(c, z1)]
        bm.faces.new(top + [it1, it0]).material_index = 2
        bot = [_ring_pt(bm, cx, cy, r_out, cols, c, (u - u0) / du, z0) for u in edge_us(c, z0)]
        bm.faces.new(bot + [ib1, ib0]).material_index = 2
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = cl._new_obj(name, bm, None, True, None, (HAZ_Y, "HazardBlack", inner_mat))
    rw.smooth(o, 40)
    return o


def _ring_pt(bm, cx, cy, r, cols, c, t, z):
    """Vertex on the planar facet of column c (t = 0..1 across it) of a `cols`-sided ring of radius r."""
    a0, a1 = 2 * math.pi * c / cols, 2 * math.pi * (c + 1) / cols
    x = (1 - t) * math.cos(a0) + t * math.cos(a1)
    y = (1 - t) * math.sin(a0) + t * math.sin(a1)
    return bm.verts.new((cx + r * x, cy + r * y, z))


def duct(name, center, r_out, r_in, z0, z1, count=5, slant=45.0, cols=20, lip_mat="M_Brass", lip_r=None,
         lip_seg=3):
    """Fan duct around a vertical axis through `center` (x, y), from z0 to z1: hazard stripes outside,
    dark inside, a rounded brass lip on top."""
    cx, cy = center[0], center[1]
    rl = (r_out + r_in) / 2
    rm = lip_r or ((r_out - r_in) / 2 + 0.003)
    return [hazard_ring(name + "_band", (cx, cy), r_out, r_in, z0, z1, count, slant, cols),
            cl.torus(name + "_lip", (cx, cy, z1), rl, rm, None, cols, lip_seg, lip_mat)]


def lid_plate(name, center, radius, side_z, mid_z, depth, mat, bevel=0.006, arc_steps=12):
    """Angry V-shaped upper eyelid for a round lens facing -Y: the part of a disc (radius, centred on
    `center` in the XZ plane) above a V whose ends sit at height side_z on the rim and whose point dips
    to mid_z on the centre line. Extruded `depth` along Y, centred on center.y."""
    xs = math.sqrt(max(0.0, radius * radius - side_z * side_z))
    a0 = math.atan2(side_z, xs)
    a1 = math.pi - a0
    pts = [(0.0, mid_z)]
    for k in range(arc_steps + 1):
        a = a0 + (a1 - a0) * k / arc_steps
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    o = rw.extrude_poly(name, pts, depth, tuple(center), (90, 0, 0), mat=mat)
    if bevel:
        rw.add_bevel(o, bevel, 1, 30.0, harden=False)
    return o


def slots(name, center, u, v, n, length, width, gap, depth=0.02, mat=GLOW, radius=0.008):
    """Row of `n` rounded glowing vent slots on a face: long along u, stacked along v."""
    u, v = V(u).normalized(), V(v).normalized()
    w = u.cross(v).normalized()
    R = cl.axes_matrix(u, w, v)
    out = []
    for k in range(n):
        off = (k - (n - 1) / 2) * gap
        out.append(cl.rbox(name, (length, depth, width), V(center) + v * off, radius, mat, R, segments=1))
    return out


def piston(name, a, b, r, split=0.55, mat="M_DarkMetal", rod_mat="M_Steel", segs=10):
    """Hydraulic piston from a to b: fat cylinder + thinner chrome rod + end eyes."""
    a, b = V(a), V(b)
    m = a.lerp(b, split)
    return [cl.cyl(name + "_cyl", a, m, r, segs, mat),
            cl.cyl(name + "_rod", m.lerp(a, 0.08), b, r * 0.55, segs, rod_mat),
            cl.sphere(name + "_eye_a", a, r * 1.05, 8, 4, "M_Brass"),
            cl.sphere(name + "_eye_b", b, r * 0.9, 8, 4, "M_Brass")]


def bolt_ring(center, axis, radius, count, r=0.02, mat="M_Brass", phase=0.0):
    """Rivet heads in a circle on a flat face whose outward normal is `axis`."""
    return cl.rivet_ring(center, radius, count, r, axis, mat, phase, outward=False)


def plate_rivets(center, u, v, nrm, half_u, half_v, nu, nv, r=0.018, mat="M_Brass"):
    """Rivets around the border of a rectangle (centre, axes u/v, half sizes) on a face with normal nrm."""
    c, u, v = V(center), V(u).normalized(), V(v).normalized()
    out = []
    for i in range(nu):
        t = -1 + 2 * i / (nu - 1) if nu > 1 else 0.0
        for s in (-1, 1):
            out.append(cl.rivet(c + u * (t * half_u) + v * (s * half_v), r, nrm, mat))
    for j in range(1, nv - 1):
        t = -1 + 2 * j / (nv - 1)
        for s in (-1, 1):
            out.append(cl.rivet(c + v * (t * half_v) + u * (s * half_u), r, nrm, mat))
    return out


# ======================================================================================
# QA
# ======================================================================================

def render_dir(asset, category, tag, direction, size=640, fov=35.0, objs=None):
    """rwlib.render_view, but from an arbitrary camera direction (e.g. from below)."""
    path = cl.preview_path(asset, category, tag)
    mn, mx = rw.bounds(objs)
    rw._setup_render(size, False, True)
    sc = bpy.context.scene
    center = (mn + mx) / 2
    radius = max((mx - mn).length / 2, 0.05)
    d = V(direction).normalized()
    cam_data = bpy.data.cameras.new("RW_DirCam")
    cam_data.lens_unit = 'FOV'
    cam_data.angle = math.radians(fov)
    cam_data.clip_start = 0.01
    cam_data.clip_end = 10000
    cam = bpy.data.objects.new("RW_DirCam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = center + d * (radius / math.sin(math.radians(fov) / 2) * 1.08)
    cam.rotation_euler = (center - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    temp = [cam]
    for nm, energy, col, rot in (("RW_DirKey", 3.2, (1, 1, 1), (50, -10, -35)),
                                 ("RW_DirFill", 0.8, (0.75, 0.82, 1.0), (70, 0, 150))):
        li = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        li.data.energy = energy
        li.data.color = col
        li.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(li)
        temp.append(li)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in temp:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
    print("RWREPORT   rendered", path)
    return path


def render_pose_dir(asset, category, pose, tag, direction, size=640):
    """charlib.render_pose with an arbitrary camera direction."""
    saved = {}
    for nm, r in pose.items():
        o = bpy.data.objects[nm]
        saved[nm] = o.rotation_euler.copy()
        o.rotation_euler = tuple(math.radians(a) for a in r)
    bpy.context.view_layer.update()
    render_dir(asset, category, tag, direction, size)
    for nm, r in saved.items():
        bpy.data.objects[nm].rotation_euler = r
    bpy.context.view_layer.update()


def summary(names, target):
    """Node report (world pivot + local offset), overall size and the triangle budget line."""
    cl.report_nodes(names)
    mn, mx = rw.bounds()
    s = mx - mn
    print("RWSIZE   %.3f x %.3f x %.3f m (min %.3f %.3f %.3f, max %.3f %.3f %.3f)" % (
        s.x, s.y, s.z, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z))
    n = rw.tri_count()
    print("RWBUDGET triangles %d / target %d %s" % (n, target, "OK" if n <= target else "OVER TARGET"))
    cl.tri_breakdown()
    return n
