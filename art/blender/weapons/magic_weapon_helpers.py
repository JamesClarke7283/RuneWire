"""magic_weapon_helpers: shape helpers for the magic weapon viewmodels
(vm_wand, vm_tome, vm_orb, vm_scepter, vm_runeblade).

Built on glove.py / partlib.py / rwlib.py / detail_helpers.py / new_weapon_helpers.py, which are shared and
must not be edited. Everything works in world space and metres; user-facing angles are in degrees. Helpers
return a new object or a list of objects ready to be joined with rw.join().

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import magic_weapon_helpers as mh
    glove, pl, rw, V, dh, nw = mh.glove, mh.pl, mh.rw, mh.V, mh.dh, mh.nw

Spell-focus contract (art/ASSET_SPEC.md): the crystal parts use CRYSTAL ("M_Crystal__a066ff", the game swaps
its tint per weapon) and nothing else may use an M_Crystal* material; exactly one small accent uses
rarity_mat() ("RarityGlow", recoloured by item rarity).

Set RW_QA=1 in the environment to also write close-up QA renders to /tmp/rw_magic/ (see qa()).
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402
import detail_helpers as dh  # noqa: E402
import new_weapon_helpers as nw  # noqa: E402

pl = glove.pl
rw = glove.rw
V = Vector

CRYSTAL = "M_Crystal__a066ff"


def crystal_mat():
    """The swappable spell crystal (emission follows the tint so previews match the game)."""
    pl.tint_emission(CRYSTAL, "a066ff", 1.6)
    return CRYSTAL


def rarity_mat():
    return rw.glow("RarityGlow", "ffffff", 3.0)


class Parts(list):
    """A list that also flattens nested lists: parts.add(obj_or_list)."""

    def add(self, x):
        if x is None:
            return x
        if isinstance(x, (list, tuple)):
            for y in x:
                self.add(y)
        else:
            self.append(x)
        return x


# --------------------------------------------------------------------------------------
# Frames
# --------------------------------------------------------------------------------------

class AxisFrame:
    """Frame of a straight focus held like vm_staff: AX runs from the pommel through the grip centre toward
    the business end, forward (-Y) and `tilt` degrees up. radial(0) = +X (the player's side), radial(90) =
    up/back (perpendicular to AX)."""

    def __init__(self, tilt):
        t = math.radians(tilt)
        self.tilt = tilt
        self.AX = V((0, -math.cos(t), math.sin(t)))
        self.side = V((1, 0, 0))
        self.up = self.AX.cross(self.side).normalized()

    def radial(self, ang):
        a = math.radians(ang)
        return self.side * math.cos(a) + self.up * math.sin(a)

    def P(self, d, ang=0.0, r=0.0):
        return self.AX * d + self.radial(ang) * r


# --------------------------------------------------------------------------------------
# Gems & crystals
# --------------------------------------------------------------------------------------

def gem_lathe(name, profile, axis=(0, 0, 1), base=(0, 0, 0), sides=8, mat=None, twist=True, spin=0.0,
              x_hint=None):
    """Faceted gem: a lathe of `profile` [(radius, h), ...] (bottom to top along `axis`) where every other
    ring is turned half a facet, so the bands between rings become zigzag triangle facets (brilliant-cut
    look). Rings with radius 0 are poles. Flat shaded."""
    bm = bmesh.new()
    rings = []
    for k, (r, h) in enumerate(profile):
        off = (math.pi / sides) * (k % 2) if twist else 0.0
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, h))])
            continue
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / sides + off + math.radians(spin)),
                                    r * math.sin(2 * math.pi * i / sides + off + math.radians(spin)), h))
                      for i in range(sides)])
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(sides):
                bm.faces.new((a[0], b[i], b[(i + 1) % sides]))
            continue
        if len(b) == 1:
            for i in range(sides):
                bm.faces.new((a[i], b[0], a[(i + 1) % sides]))
            continue
        a_off = (k % 2) if twist else 0
        for i in range(sides):
            j = (i + 1) % sides
            if not twist:
                bm.faces.new((a[i], a[j], b[j], b[i]))
            elif a_off == 0:
                # ring b is turned +half a facet relative to ring a
                bm.faces.new((a[i], a[j], b[i]))
                bm.faces.new((b[i], a[j], b[j]))
            else:
                # ring a is turned +half a facet relative to ring b
                bm.faces.new((a[i], b[j], b[i]))
                bm.faces.new((a[i], a[j], b[j]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=pl.frame_matrix(axis, x_hint).to_4x4(), verts=bm.verts)
    o = pl.obj_from_bm(name, bm, mat, 0, loc=V(base))
    rw.flat_shade(o)
    return o


# --------------------------------------------------------------------------------------
# Ornament on round shafts
# --------------------------------------------------------------------------------------

def surface_helix(name, F, d0, d1, rfunc, turns, phase, wire_r, mat, sink=0.35, pts_per_turn=10, segs=6, res=2,
                  caps=(True, True)):
    """Wire wound round a tapered shaft (radius rfunc(d)) of an AxisFrame F, from d0 to d1 along F.AX.
    Negative turns wind the other way."""
    n = max(3, int(abs(turns) * pts_per_turn) + 1)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        d = d0 + (d1 - d0) * t
        pts.append(F.P(d, phase + 360.0 * turns * t, rfunc(d) + wire_r * (1.0 - sink)))
    return pl.sausage(name, pts, wire_r, segs, res, mat, caps, 2, True, 60)


def helix_point(F, d0, d1, rfunc, turns, phase, t, lift=0.0):
    d = d0 + (d1 - d0) * t
    return F.P(d, phase + 360.0 * turns * t, rfunc(d) + lift), d


def cyl_ridge(name, F, path2d, rfunc, d0, ang0, wire_r, mat, sink=0.4, taper=None, segs=6, res=2):
    """A filigree wire lying on a round shaft: path2d [(along, around), ...] in metres is wrapped onto the
    shaft surface around (d0, ang0)."""
    pts = []
    for (du, dv) in path2d:
        d = d0 + du
        r = rfunc(d)
        pts.append(F.P(d, ang0 + math.degrees(dv / max(r, 1e-4)), r + wire_r * (1.0 - sink)))
    radii = [wire_r * (taper[i] if taper else 1.0) for i in range(len(pts))]
    return pl.sausage(name, pts, radii, segs, res, mat, (True, True), 2, True, 60)


def spiral2d(R, turns=1.0, start=90.0, cw=True, n=9, r_in=0.28, tail=None):
    """2D filigree curl (centre 0,0, outer radius R), optionally ending in a tail point. Returns (pts, taper)."""
    pts, tap = [], []
    sgn = -1 if cw else 1
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start) + sgn * 2 * math.pi * turns * (1 - t)
        rr = R * (r_in + (1 - r_in) * t)
        pts.append((rr * math.cos(ang), rr * math.sin(ang)))
        tap.append(0.6 + 0.4 * t)
    if tail is not None:
        pts.append(tail)
        tap.append(0.75)
    return pts, tap


def flat_scroll(name, c, u, v, R, half_w, depth, mat, turns=1.0, start=90.0, cw=True, n=10, tail=None,
                taper=(0.6, 1.0)):
    """Cheap filigree scroll: a flat strip (half width half_w) bent into a spiral of outer radius R, lying in
    the (u, v) plane through c (extruded `depth` along u x v). tail: optional (x, y) end point."""
    pts2, _ = spiral2d(R, turns, start, cw, n, 0.3, tail)
    outline = nw.ribbon_poly(pts2, half_w, taper)
    return nw.slab(name, outline, depth, c, u, v, mat, smooth_angle=0)


def inset_poly(pts, d):
    """Offset a simple closed 2D polygon inward by d (mitred corners). Either winding."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2
    sgn = 1.0 if area > 0 else -1.0          # CCW: the inward normal of edge (dx, dy) is (-dy, dx)
    out = []
    for i in range(n):
        p0, p1, p2 = V((*pts[i - 1], 0)), V((*pts[i], 0)), V((*pts[(i + 1) % n], 0))
        e1 = (p1 - p0).normalized()
        e2 = (p2 - p1).normalized()
        n1 = V((-e1.y, e1.x, 0)) * sgn
        n2 = V((-e2.y, e2.x, 0)) * sgn
        k = 1.0 + n1.dot(n2)
        q = p1 + (n1 + n2) * (d / max(k, 0.25))
        out.append((q.x, q.y))
    return out


# --------------------------------------------------------------------------------------
# Glyphs
# --------------------------------------------------------------------------------------

SUN_RAYS = 8


def sun_glyph(name, c, u, v, r, mat, depth=0.004, rays=SUN_RAYS, ray_len=None, ray_w=None, ring=True, segs=14):
    """Little sun rune lying in the (u, v) plane: a disc (or ring) with `rays` pointed rays."""
    u, v, n = nw.uv_frame(u, v)
    c = V(c)
    parts = []
    if ring:
        t = rw.torus(name + "_ring", r * 0.62, r * 0.17, segs, 4, (0, 0, 0), mat=mat)
        pl.align(t, n, c)
        parts.append(t)
        parts.append(pl.disc(name + "_dot", r * 0.24, depth, n, c, mat, 8, 0.3))
    else:
        parts.append(pl.disc(name + "_disc", r * 0.62, depth, n, c, mat, segs, 0.35))
    rl = ray_len if ray_len is not None else r * 0.55
    rwid = ray_w if ray_w is not None else r * 0.36
    for k in range(rays):
        a = 2 * math.pi * k / rays
        d = u * math.cos(a) + v * math.sin(a)
        s = n.cross(d).normalized()
        p0 = c + d * (r * 0.8)
        pts = [(0.0, -rwid / 2), (rl, 0.0), (0.0, rwid / 2)]
        parts.append(nw.slab(name + "_ray", pts, depth, p0, d, s, mat, smooth_angle=0))
    return parts


def star_rune(name, c, u, v, r_out, r_in, points, depth, mat, dot_mat=None, bevel=0.0):
    """Cheap sun/star rune: a `points`-pointed star slab in the (u, v) plane (depth along u x v), optionally
    with a raised round centre dot in `dot_mat`. Returns a list."""
    pts = []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    out = [nw.slab(name, pts, depth, c, u, v, mat, bevel=bevel, segments=1, angle=40, smooth_angle=0)]
    if dot_mat is not None:
        u, v, n = nw.uv_frame(u, v)
        out.append(pl.disc(name + "_dot", r_in * 0.62, depth * 1.6, n, V(c), dot_mat, 10, 0.3))
    return out


def glyph2(key, c, u, v, su, sv, width, depth, mat, name="rune", rounded=0.0):
    """Rune from partlib's RUNES table with separate scales across (su) and along (sv) the glyph: strokes are
    boxes lying in the (u, v) plane, centred on c (half sunk), depth along u x v."""
    c = V(c)
    u = V(u).normalized()
    v = V(v).normalized()
    n = u.cross(v).normalized()
    out = []
    for stroke in pl.RUNES[key]:
        for (a, b) in zip(stroke[:-1], stroke[1:]):
            pa = c + u * (a[0] * su) + v * (a[1] * sv)
            pb = c + u * (b[0] * su) + v * (b[1] * sv)
            d = pb - pa
            if rounded:
                out.append(pl.obox(name, (d.length + width, width, depth), (pa + pb) / 2, d, n, mat,
                                   rounded=rounded, segments=1))
            else:
                out.append(pl.obox(name, (d.length + width, width, depth), (pa + pb) / 2, d, n, mat))
    return out


# --------------------------------------------------------------------------------------
# QA renders (only with RW_QA=1): tight close-ups + an approximate first-person camera
# --------------------------------------------------------------------------------------

QA_DIR = "/tmp/rw_magic"


def _visible_meshes(hide=()):
    out = []
    for o in rw.all_mesh_objects():
        if o.hide_render:
            continue
        p, skip = o, False
        while p is not None:
            if p.name.split(".")[0] in hide:
                skip = True
                break
            p = p.parent
        if not skip:
            out.append(o)
    return out


def _render_ortho(path, objs, view, size, margin=1.08, up_hint=(0, 0, 1)):
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        pts += [ev.matrix_world @ V(c) for c in ev.bound_box]
    d = V(view).normalized()
    look = -d
    right = look.cross(V(up_hint))
    if right.length < 1e-4:
        right = look.cross(V((0, 1, 0)))
    right.normalize()
    up = right.cross(look).normalized()
    xs = [p.dot(right) for p in pts]
    ys = [p.dot(up) for p in pts]
    zs = [p.dot(look) for p in pts]
    centre = right * ((min(xs) + max(xs)) / 2) + up * ((min(ys) + max(ys)) / 2) + look * ((min(zs) + max(zs)) / 2)
    extent = max(max(xs) - min(xs), max(ys) - min(ys))
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = extent * margin
    cam_data.clip_start = 0.001
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = centre + d * 10.0
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)


def _render_region(path, centre, extent, view, size):
    """Orthographic close-up of a region (centre, extent in metres) seen from direction `view`."""
    sc = bpy.context.scene
    d = V(view).normalized()
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = extent
    cam_data.clip_start = 0.001
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = V(centre) + d * 10.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)


def qa_closeups(asset, shots, size=420, cols=3):
    """Region close-ups: shots = [(name, centre, extent, view_dir), ...] -> /tmp/rw_magic/<asset>_close.png.
    Names starting with "nog" hide the glove. Only runs when RW_QA=1."""
    if os.environ.get("RW_QA") != "1":
        return
    os.makedirs(QA_DIR, exist_ok=True)
    rw._setup_render(size, False, True)
    lights = _lights()
    paths = []
    for (nm, c, ext, d) in shots:
        hide = ("Glove",) if nm.startswith("nog") else ()
        objs = _visible_meshes(hide)
        hidden = [o for o in rw.all_mesh_objects() if o not in objs and not o.hide_render]
        for o in hidden:
            o.hide_render = True
        p = os.path.join(QA_DIR, "%s_c_%s.png" % (asset, nm))
        try:
            _render_region(p, c, ext, d, size)
        finally:
            for o in hidden:
                o.hide_render = False
        paths.append(p)
    _grid(paths, os.path.join(QA_DIR, "%s_close.png" % asset), cols)
    _remove(lights)


def _lights():
    sc = bpy.context.scene
    key = bpy.data.objects.new("QA_Key", bpy.data.lights.new("QA_Key", 'SUN'))
    key.data.energy = 3.2
    key.data.angle = math.radians(8)
    key.rotation_euler = (math.radians(50), math.radians(-10), math.radians(-35))
    sc.collection.objects.link(key)
    fill = bpy.data.objects.new("QA_Fill", bpy.data.lights.new("QA_Fill", 'SUN'))
    fill.data.energy = 0.8
    fill.data.color = (0.75, 0.82, 1.0)
    fill.rotation_euler = (math.radians(70), 0, math.radians(150))
    sc.collection.objects.link(fill)
    return [key, fill]


def _remove(objs):
    for o in objs:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)


def _grid(paths, out_path, cols):
    import numpy as np
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        w, h = im.size
        a = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        imgs.append(a.reshape(h, w, 4))
        bpy.data.images.remove(im)
    h, w = imgs[0].shape[:2]
    rows = (len(imgs) + cols - 1) // cols
    grid = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    grid[..., 3] = 1.0
    for i, a in enumerate(imgs):
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h          # image rows run bottom to top
        grid[y0:y0 + h, c * w:(c + 1) * w] = a
    out = bpy.data.images.new("qa_grid", cols * w, rows * h, alpha=True)
    out.pixels.foreach_set(grid.ravel())
    out.filepath_raw = out_path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)


def qa(asset, placement=(0.25, -0.27, -0.42), fov=80.0, size=420,
       views=(("plusX", (1, 0.12, 0.25)), ("minusX", (-1, -0.2, 0.3)), ("top", (0.12, 0.3, 1.0)),
              ("back", (0.35, 1, 0.55)), ("front", (-0.3, -1, 0.35)), ("nog_icon", (-1.0, -0.38, 0.42))),
       sub_views=()):
    """Close-up QA renders of the finished scene into /tmp/rw_magic/<asset>_grid.png and an approximate
    first-person shot <asset>_fp.png (camera placed from the viewmodel PLACEMENT, 80 degree vertical FOV).
    Views whose name starts with "nog" hide the glove. Only runs when RW_QA=1."""
    if os.environ.get("RW_QA") != "1":
        return
    os.makedirs(QA_DIR, exist_ok=True)
    sc = bpy.context.scene
    rw._setup_render(size, False, True)
    lights = _lights()
    paths = []
    for (nm, d) in tuple(views) + tuple(sub_views):
        hide = ("Glove",) if nm.startswith("nog") else ()
        objs = _visible_meshes(hide)
        hidden = [o for o in rw.all_mesh_objects() if o not in objs and not o.hide_render]
        for o in hidden:
            o.hide_render = True
        p = os.path.join(QA_DIR, "%s_%s.png" % (asset, nm))
        try:
            _render_ortho(p, objs, d, size)
        finally:
            for o in hidden:
                o.hide_render = False
        paths.append(p)
    _grid(paths, os.path.join(QA_DIR, "%s_grid.png" % asset), 3)
    # first-person: Godot places the model at `placement` turned 180 degrees about Y, so the camera sits at
    # Blender (px, -pz, -py) relative to the model origin, looking along -Y with +Z up.
    px, py, pz = placement
    cam_data = bpy.data.cameras.new("QA_FP")
    cam_data.lens_unit = 'FOV'
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.angle = math.radians(fov)
    cam_data.clip_start = 0.01
    cam = bpy.data.objects.new("QA_FP", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (px, -pz, -py)
    cam.rotation_euler = V((0, -1, 0)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x = 960
    sc.render.resolution_y = 540
    sc.render.filepath = os.path.join(QA_DIR, "%s_fp.png" % asset)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)
    _remove(lights)
    print("RWREPORT   QA renders in", QA_DIR)


def report_nodes(names):
    """Print world positions of named nodes (empties / sub-objects) for the final report."""
    bpy.context.view_layer.update()
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            print("RWREPORT   MISSING node", nm)
            continue
        p = o.matrix_world.translation
        print("RWREPORT   node-pos %-10s (%.4f, %.4f, %.4f) parent=%s" % (nm, p.x, p.y, p.z,
                                                                        o.parent.name if o.parent else "-"))


def crystal_audit():
    """List which objects use M_Crystal* and RarityGlow materials (the tint contract)."""
    for o in rw.all_mesh_objects():
        mats = [s.material.name for s in o.material_slots if s.material]
        cr = [m for m in mats if m.startswith("M_Crystal")]
        ra = [m for m in mats if m.startswith("RarityGlow")]
        if cr or ra:
            # count faces per material
            cnt = {}
            for p in o.data.polygons:
                m = o.material_slots[p.material_index].material.name
                if m in cr or m in ra:
                    cnt[m] = cnt.get(m, 0) + 1
            print("RWREPORT   tint-slots %-10s %s" % (o.name, cnt))
