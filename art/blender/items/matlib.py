"""matlib: shared helpers for the RuneWire crafting-material pickups (ores, ingots, plants, cloth, parts).

Import from an item generator script in art/blender/items/:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import matlib as ml
    il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V

Builds on itemlib / partlib / rwlib (none of them is edited). Conventions follow art/ASSET_SPEC.md: metres,
+Z up, the front faces -Y, user-facing angles in degrees. Every item is one joined mesh object and ends with
il.finish_item() (origin at the bounding-box centre, icon=True).

Materials
* M(name) / mat(spec)   accent palette below (flat colours and glows), itemlib accents, or library M_* names.
  Glows are flat emissive materials like rw.glow(), but with a darker base colour under the emission: the Godot
  importer turns any flat material with emission into a toon glow (energy >= 1.0), and the darker base keeps
  the hue saturated in the AgX previews/icons. Never put "leaf", "petal", "flower" or "grass" in a material
  name: Godot turns those into wind-swayed foliage and drops their emission (scripts/autoload/material_library.gd).
* tinted(lib, target)   "M_<Lib>__<tint>" whose in-game colour (texture x tint) is the target colour, with the
  Blender stand-in set to that colour so previews and icons match the game.
* preview_metals()      previews/icons only: metallic library stand-ins reflect the flat grey-blue preview world
  and turn muddy (brass olive, copper brown). This lowers their metallic so the hue reads. Godot swaps M_*
  materials by name, so the game look is unaffected (same idea as itemlib.preview_glow).
* no_outline(obj, mats) previews/icons only: no Freestyle outlines on fine line art (blueprint ink).

Shapes
* ingot(), ingot_stack() trapezoid ingot bar; two bars stacked crosswise with a pressed cartouche (stamp_panel(),
                         paint_floor()) ready for an emblem.
* prism(), deboss()     raise / press a 2D outline on a plane (emblems, cartouches); plane_frame() spans a face.
* gear_pts(), cog_pts(), hammer_pts(), rounded_rect_pts(), rot2()   2D outlines (counter-clockwise) and rotation.
* stroke()              flat line-drawing strip along a 2D polyline (blueprint lines), open or closed.
* on_surface()          ray-cast points + normals on a lump (scatter nuggets / nodules / spots).
* nugget()              small faceted lump aligned to a surface normal.
* vein()                flat mineral vein band inlaid along a lump's surface between two directions.
* pod()                 smooth flattened ellipsoid with a shaped outline (petals, leaves, feathers).
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V

# --------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------

PALETTE = {
    # name: ("flat", colour, roughness, metallic) or ("glow", emission colour, base colour, strength)
    # plants
    "ReedGold": ("flat", "e9b52e", 0.85, 0.0),
    "ReedGreen": ("flat", "a3c437", 0.85, 0.0),
    "ReedTan": ("flat", "f2cf62", 0.85, 0.0),
    "ReedHead": ("flat", "7a4426", 0.9, 0.0),
    "TwineBrown": ("flat", "8c5a33", 0.9, 0.0),
    "Soil": ("flat", "6e4a30", 0.95, 0.0),
    "MushStem": ("flat", "f1e6cc", 0.8, 0.0),
    "CapGlow": ("glow", "4fd8ff", "0a62b0", 0.75),
    "CapGills": ("glow", "2a9fe0", "0d3f6e", 0.5),
    "CapSpot": ("flat", "f7fbff", 0.6, 0.0),
    "SunGold": ("glow", "6a4800", "ffd21a", 0.6),      # golden yellow with a soft warm glow (dark emission)
    "SunGoldDeep": ("glow", "6a3800", "ffad00", 0.6),
    "SunCore": ("flat", "e8641a", 0.7, 0.0),
    "SunCoreDot": ("flat", "a63c0c", 0.7, 0.0),
    "SunGreen": ("flat", "5cb83a", 0.8, 0.0),
    # cloth and thread
    "RibbonBlue": ("flat", "2f6be0", 0.45, 0.0),
    "RibbonBlueDark": ("flat", "2350b0", 0.45, 0.0),
    "ThreadGlow": ("glow", "39d5c4", "0a7c70", 0.8),
    "ThreadGlowHi": ("glow", "8cfff0", "22b8a6", 0.8),
    # ink, runes, cells
    "InkGlow": ("glow", "c060ff", "7a1ad0", 0.3),
    "InkGlowTop": ("glow", "d8a8ff", "a050f0", 0.3),
    "RuneViolet": ("glow", "a066ff", "6a2ee0", 1.6),
    "QuillWhite": ("flat", "f7f2e6", 0.7, 0.0),
    "QuillViolet": ("flat", "7a4fd0", 0.7, 0.0),
    "CellGlow": ("glow", "39d5c4", "087468", 0.6),
    "CellGlowHi": ("glow", "a8fff2", "2fc8b6", 0.6),
    "TerminalRed": ("flat", "d6363c", 0.45, 0.0),
    "LensGlow": ("glow", "39d5c4", "15a092", 1.0),
    # pressed-panel floors on the ingots (an enamel-dark tone of each metal)
    "CopperDeep": ("flat", "6e3418", 0.6, 0.3),
    "BrassDeep": ("flat", "7a5612", 0.6, 0.3),
    "IronDeep": ("flat", "2a2e36", 0.6, 0.3),
    # blueprint
    "SchematicBlue": ("flat", "2f5f9e", 0.9, 0.0),
    "SchematicDeep": ("flat", "1d3f6e", 0.9, 0.0),
    "SchematicPale": ("flat", "8fb4e0", 0.9, 0.0),
    "SchematicInk": ("flat", "eef6ff", 0.8, 0.0),
    "SealRed": ("flat", "c42a3a", 0.45, 0.0),
    "SealDark": ("flat", "8e1a28", 0.45, 0.0),
    "StringCream": ("flat", "ead9b0", 0.9, 0.0),
    "Shadow": ("flat", "2a1a14", 1.0, 0.0),
}


def M(name):
    """Palette material by name (created on first use). Glows get a matte finish so the previews don't pick up
    the bluish sky reflection (Godot's glow kind has no specular anyway)."""
    k = PALETTE[name]
    if k[0] == "glow":
        return rw.material(name, k[2], 0.65, 0.0, k[1], k[3])
    return rw.flat(name, k[1], k[2], k[3])


def mat(m):
    """Resolve a material spec: Material, palette name, itemlib accent name, or library 'M_*' name."""
    if m is None or isinstance(m, bpy.types.Material):
        return m
    if m in PALETTE:
        return M(m)
    return il.mat(m)


# mean colour (sRGB hex) of each library albedo texture, measured from assets/textures/<set>/<set>_albedo.png
TEX_MEAN = {
    "M_StoneRough": "888384",
    "M_Steel": "adb3bc",
    "M_DarkMetal": "454c58",
    "M_Copper": "bd7850",
    "M_Brass": "c49a47",
    "M_Rust": "7a3e1b",
    "M_Fabric": "dcdcdc",
    "M_PaintedMetal": "d5d5d5",
}


def _to_lin(h):
    return rw.srgb_to_linear(rw.hex_to_srgb(h))


def _to_hex(lin):
    out = []
    for x in lin:
        x = max(0.0, min(1.0, x))
        s = x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        out.append("%02x" % int(round(max(0.0, min(1.0, s)) * 255)))
    return "".join(out)


def tinted(lib_name, target):
    """Tinted library material whose in-game colour (Godot multiplies albedo texture x tint in linear space)
    comes out at `target` (sRGB hex). The Blender stand-in is set to `target` so previews match the game.
    Returns the material."""
    tex = _to_lin(TEX_MEAN[lib_name])
    tgt = _to_lin(target)
    tint = _to_hex([min(1.0, t / max(x, 1e-4)) for t, x in zip(tgt, tex)])
    m = rw.lib(lib_name, tint)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(target)
    m.diffuse_color = rw._lin(target)[:3] + (m.diffuse_color[3],)
    return m


def no_outline(o, mats):
    """Previews/icons only: keep the Freestyle outline off faces in the given materials (fine line art such as
    blueprint ink, which would otherwise drown in its own dark outlines). Marks those faces with Freestyle face
    marks and makes the render's line set exclude edges next to marked faces (rwlib reuses the first line set).
    In game the strokes are a millimetre proud, below the screen-space outline's reach."""
    names = {mat(m).name for m in mats}
    idx = {i for i, s in enumerate(o.material_slots) if s.material and s.material.name in names}
    me = o.data
    a = me.attributes.get("freestyle_face") or me.attributes.new("freestyle_face", 'BOOLEAN', 'FACE')
    for p in me.polygons:
        a.data[p.index].value = p.material_index in idx
    fs = bpy.context.view_layer.freestyle_settings
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Lines")
    ls.select_by_face_marks = True
    ls.face_mark_negation = 'EXCLUSIVE'
    ls.face_mark_condition = 'ONE'
    return o


# preview stand-ins for the metals: (base colour, roughness, metallic)
PREVIEW_METALS = {
    "M_Copper": ("d87a45", 0.32, 0.55),
    "M_Brass": ("e2b046", 0.32, 0.55),
    "M_Steel": ("b4bcc8", 0.32, 0.4),
    "M_DarkMetal": ("4a515e", 0.4, 0.55),
}


def preview_metals():
    """Previews/icons only (see the module docstring): soften the metallic library stand-ins in the file.
    Tinted variants (M_Steel__rrggbb from tinted()) keep their target colour and only get the softer finish."""
    for m in bpy.data.materials:
        lib_name = m.name.split("__")[0]
        if lib_name not in PREVIEW_METALS or not m.node_tree:
            continue
        base, rough, metal = PREVIEW_METALS[lib_name]
        b = m.node_tree.nodes.get("Principled BSDF")
        if "__" not in m.name:
            b.inputs["Base Color"].default_value = rw._lin(base)
            m.diffuse_color = rw._lin(base)[:3] + (1.0,)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal


# --------------------------------------------------------------------------------------
# 2D outlines (counter-clockwise, centred on 0)
# --------------------------------------------------------------------------------------

def rounded_rect_pts(w, h, r, n=4):
    """Rounded rectangle w x h with corner radius r (n points per corner)."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for (cx, cy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                         (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return il.ccw(pts)


def gear_pts(r_out, r_root, teeth, spin=0.0, flank=0.22):
    """Gear outline: `teeth` flat-topped teeth from r_root out to r_out."""
    pts = []
    step = 2 * math.pi / teeth
    for t in range(teeth):
        a0 = math.radians(spin) + step * t
        for (f, r) in ((0.0, r_root), (0.5 - flank - 0.06, r_root), (0.5 - flank + 0.06, r_out),
                       (0.5 + flank - 0.06, r_out), (0.5 + flank + 0.06, r_root)):
            a = a0 + step * f
            pts.append((r * math.cos(a), r * math.sin(a)))
    return il.ccw(pts)


def cog_pts(r_out, r_root, teeth=6, spin=0.0):
    """Chunky cog: few wide, tapered teeth with rounded valleys."""
    pts = []
    step = 2 * math.pi / teeth
    for t in range(teeth):
        a0 = math.radians(spin) + step * t
        for (f, r) in ((0.0, r_root), (0.12, r_root * 1.01), (0.26, r_out * 0.97), (0.32, r_out),
                       (0.5, r_out * 1.01), (0.68, r_out), (0.74, r_out * 0.97), (0.88, r_root * 1.01)):
            a = a0 + step * f
            pts.append((r * math.cos(a), r * math.sin(a)))
    return il.ccw(pts)


def hammer_pts(h, w, n_round=4):
    """Cartoon smithing hammer (head on top), h tall, head w wide, centred on its bbox: a flared striking face
    on the right, a wedge peen on the left and a slightly tapered handle with a rounded end."""
    hh = h * 0.3                              # head height
    top, hb = h / 2, h / 2 - hh               # head top / bottom
    sw_top, sw_bot = w * 0.12, w * 0.1        # handle half-widths
    hw = w / 2
    pts = [(sw_top, hb)]
    pts += [(hw * 0.62, hb), (hw * 0.78, hb - hh * 0.08), (hw, hb - hh * 0.1), (hw, top + hh * 0.1),
            (hw * 0.78, top + hh * 0.08), (hw * 0.62, top), (-hw * 0.4, top), (-hw, top - hh * 0.36),
            (-hw, hb + hh * 0.36), (-hw * 0.4, hb), (-sw_top, hb)]
    yb = -h / 2 + sw_bot
    for i in range(n_round + 1):              # rounded handle end
        a = math.pi + math.pi * i / n_round
        pts.append((sw_bot * math.cos(a), yb + sw_bot * math.sin(a)))
    return il.ccw(pts)


def rot2(pts, deg):
    """Rotate 2D points about the origin (counter-clockwise, degrees)."""
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s_, x * s_ + y * c) for (x, y) in pts]


# --------------------------------------------------------------------------------------
# Laying 2D art on surfaces
# --------------------------------------------------------------------------------------

def plane_frame(normal, up=(0, 0, 1)):
    """(u, v, n) for a face with outward normal n: v as close to `up` as possible, u = v x n."""
    n = V(normal).normalized()
    v = V(up) - V(up).dot(n) * n
    if v.length < 1e-5:
        v = V((0, 1, 0)) - V((0, 1, 0)).dot(n) * n
    v.normalize()
    u = v.cross(n).normalized()
    return u, v, n


def prism(name, pts2d, center, u, v, h, m=None, sink=0.0, smooth_angle=30):
    """Extruded 2D outline on the plane through `center` spanned by u (x) and v (y): from `sink` below the
    plane up to h above it, along u x v."""
    n = V(u).cross(V(v)).normalized()
    mp = il.plane_map(V(center) - n * sink, u, v, 0.0, h + sink)
    return il.wrap_prism(name, pts2d, mp, mat(m), smooth_angle)


def deboss(target, pts2d, center, u, v, depth, above=0.01):
    """Press a 2D outline `depth` into target's surface at `center` (u x v points out of the surface)."""
    cutter = prism("cut", pts2d, center, u, v, above, None, sink=depth)
    pl.carve(target, [cutter])
    return target


def stroke(name, pts2d, width, mapper, closed=False, m=None, thick=1.0):
    """Flat strip of constant width along a 2D polyline, laid through a mapper (il.plane_map / lathe_map):
    s = 0 is the underside, s = thick the top. Mitred joints; open strips get square ends."""
    P = [V((x, y, 0.0)) for (x, y) in pts2d]
    n = len(P)
    hw = width / 2
    left, right = [], []
    for i in range(n):
        if closed:
            a, b = P[i - 1], P[(i + 1) % n]
            d0 = (P[i] - a).normalized()
            d1 = (b - P[i]).normalized()
        else:
            d0 = (P[i] - P[max(i - 1, 0)]).normalized() if i > 0 else (P[1] - P[0]).normalized()
            d1 = (P[min(i + 1, n - 1)] - P[i]).normalized() if i < n - 1 else d0
        t = (d0 + d1)
        t = t.normalized() if t.length > 1e-6 else d1
        nrm = V((-t.y, t.x, 0.0))
        cosang = max(0.35, nrm.dot(V((-d1.y, d1.x, 0.0))))
        off = nrm * (hw / cosang)
        left.append(P[i] + off)
        right.append(P[i] - off)
    bm = bmesh.new()
    rows = []
    for (L, R) in zip(left, right):
        rows.append([bm.verts.new(mapper(L.x, L.y, 0.0)), bm.verts.new(mapper(R.x, R.y, 0.0)),
                     bm.verts.new(mapper(R.x, R.y, thick)), bm.verts.new(mapper(L.x, L.y, thick))])
    segs = n if closed else n - 1
    for i in range(segs):
        a, b = rows[i], rows[(i + 1) % n]
        for k in range(4):
            kk = (k + 1) % 4
            bm.faces.new((a[k], a[kk], b[kk], b[k]))
    if not closed:
        bm.faces.new(rows[0])
        bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), 30)


# --------------------------------------------------------------------------------------
# Ingots
# --------------------------------------------------------------------------------------

def ingot(name, L, W, H, top=(0.8, 0.66), loc=(0, 0, 0), rot_z=0.0, m="M_Copper", bevel=0.012, segs=2):
    """Trapezoid ingot bar: base L x W (along local X / Y), top face L*top[0] x W*top[1], height H.
    loc is the centre of the base; rot_z turns it about Z. Bevelled and applied."""
    tl, tw = L * top[0] / 2, W * top[1] / 2
    bl, bw = L / 2, W / 2
    v = [(-bl, -bw, 0), (bl, -bw, 0), (bl, bw, 0), (-bl, bw, 0), (-tl, -tw, H), (tl, -tw, H), (tl, tw, H), (-tl, tw, H)]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = rw.mesh_from_data(name, v, f, mat=mat(m))
    md = o.modifiers.new("Bevel", 'BEVEL')
    md.width = bevel
    md.segments = segs
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(20)
    md.use_clamp_overlap = True
    rw.apply_modifiers(o)
    pl.xform(o, Matrix.Translation(V(loc)) @ Matrix.Rotation(math.radians(rot_z), 4, 'Z'))
    rw.smooth(o, 35)
    return o


def ingot_top(L, W, H, top=(0.8, 0.66), loc=(0, 0, 0), rot_z=0.0):
    """(centre of the top face, u along the bar, v across it) for an ingot() with the same arguments."""
    R = Matrix.Rotation(math.radians(rot_z), 3, 'Z')
    return V(loc) + V((0, 0, H)), R @ V((1, 0, 0)), R @ V((0, 1, 0))


def stamp_panel(target, center, u, v, w, h, depth=0.004, r=None):
    """Press a rounded cartouche (w along u, h along v) `depth` into a flat face; returns the floor centre."""
    n = V(u).cross(V(v)).normalized()
    deboss(target, rounded_rect_pts(w, h, r if r is not None else min(w, h) * 0.3, 3), center, u, v, depth)
    return V(center) - n * depth


def ingot_stack(m, L=0.25, W=0.105, H=0.058, top=(0.8, 0.66), spin=0.0, panel=(0.13, 0.05), depth=0.004,
                floor_mat=None):
    """Two ingots stacked crosswise (the bottom one along X turned by `spin`, the top one across it), with a
    rounded cartouche pressed into the top bar (its floor optionally in `floor_mat`, a darker enamel-like tone
    that makes the emblem pop). Returns (parts, floor centre, u, v): u/v span the cartouche floor, v running
    along the top bar away from the viewer, u x v = +Z. Build the emblem on that floor."""
    low = ingot("ingot", L, W, H, top, (0, 0, 0), spin, m)
    hi = ingot("ingot", L, W, H, top, (0, 0, H - 0.002), spin + 90.0, m)
    c, along, _across = ingot_top(L, W, H, top, (0, 0, H - 0.002), spin + 90.0)
    v = along
    u = v.cross(V((0, 0, 1))).normalized()
    floor = stamp_panel(hi, c, u, v, panel[1], panel[0], depth)
    if floor_mat is not None:
        paint_floor(hi, floor, floor_mat)
    return [low, hi], floor, u, v


def paint_floor(o, floor, m, tol=0.0008):
    """Give the upward faces lying on the plane z = floor.z (a pressed panel's floor) material m."""
    z = V(floor).z
    rw.set_mat_where(o, mat(m), lambda c, nrm: nrm.z > 0.9 and abs(c.z - z) < tol)


# --------------------------------------------------------------------------------------
# Lumps: scatter on a surface
# --------------------------------------------------------------------------------------

def on_surface(target, center, dirs):
    """Ray-cast from outside along each direction back toward `center`; returns [(point, normal), ...]."""
    c = V(center)
    out = []
    for d in dirs:
        d = V(d).normalized()
        p, nrm = il.surface_hit(target, c + d * 5.0, -d)
        if p is not None:
            out.append((p, nrm))
    return out


def nugget(name, size, point, normal, seed=0, m="M_Copper", sink=0.45, n_points=9, jitter=0.3, spin=0.0,
           bevel=0.004):
    """Small faceted lump (hull rock) whose local Z follows `normal`, sunk `sink` of its height into the surface."""
    o = il.hull_rock(name, size, (0, 0, 0), seed=seed, n_points=n_points, jitter=jitter, rmin=0.78,
                     bevel=bevel, m=mat(m), dissolve_deg=6, rot_z=spin)
    pl.align(o, normal)
    o.location = V(point) - V(normal).normalized() * (size[2] * (sink - 0.5))
    return o


def vein(name, target, center, d0, d1, width=0.02, height=0.006, n=7, m="M_Copper", wobble=0.0, seed=0, segs=6,
         res=2):
    """Flat mineral vein inlaid in target's surface, running from direction d0 to d1 (both seen from `center`):
    a lens-section band centred on the surface (raised `height`, sunk as much), tapering at both ends."""
    rnd = random.Random(seed)
    a, b = V(d0).normalized(), V(d1).normalized()
    side = a.cross(b)
    side = side.normalized() if side.length > 1e-5 else a.orthogonal().normalized()
    phase = rnd.uniform(0, 2 * math.pi)
    pts, raw = [], []
    for i in range(n):
        t = i / (n - 1)
        d = a.slerp(b, t) if (a - b).length > 1e-4 else a
        if wobble:   # smooth meander sideways, zero at both ends
            d = (d + side * (wobble * math.sin(math.pi * t) * math.sin(3 * math.pi * t + phase))).normalized()
        hit = on_surface(target, center, [d])
        if hit:
            pts.append(hit[0][0])
            raw.append((hit[0][1] + (hit[0][0] - V(center)).normalized()).normalized())
    # smooth the facet normals along the path so the band does not twist at facet edges
    nrms = []
    for i in range(len(raw)):
        acc = V((0, 0, 0))
        for k in range(max(0, i - 2), min(len(raw), i + 3)):
            acc += raw[k]
        nrms.append(acc.normalized())
    Q, _ = pl._resample(pts, [0.0] * len(pts), res, True)
    m_ = len(Q)
    bm = bmesh.new()
    rings = []
    for i in range(m_):
        t = i / (m_ - 1)
        k = min(int(t * (len(nrms) - 1)), len(nrms) - 2)
        f = t * (len(nrms) - 1) - k
        nr = nrms[k].lerp(nrms[k + 1], f).normalized()
        T = (Q[min(i + 1, m_ - 1)] - Q[max(i - 1, 0)]).normalized()
        N = (nr - nr.dot(T) * T).normalized()
        B = T.cross(N).normalized()
        taper = 0.25 + 0.75 * math.sin(math.pi * t) ** 0.6
        ring = [bm.verts.new(Q[i] + B * (width / 2 * taper * math.cos(2 * math.pi * j / segs)) +
                             N * (height * taper * math.sin(2 * math.pi * j / segs))) for j in range(segs)]
        rings.append(ring)
    for i in range(m_ - 1):
        for j in range(segs):
            jj = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), 50)


# --------------------------------------------------------------------------------------
# Pods: smooth flattened ellipsoids (cartoon petals, leaves, feathers, pebbles)
# --------------------------------------------------------------------------------------

def pod(name, center, d, f, L, W, T, m=None, segs=12, rings=6, shape=None, thick_shape=None, bend=0.0, arch=0.0,
        smooth_angle=80, sweep=0.0):
    """Smooth flattened ellipsoid: length L along d (base end at xn = -1, tip at xn = +1), thickness T along f,
    width W across. shape(xn) / thick_shape(xn) scale the width / thickness at xn (default: plain ellipse).
    bend curls both ends toward f by bend * L * xn^2 (a cupped petal); arch lifts the middle along f by
    arch * L * (1 - xn^2) (an arched leaf); sweep bends the whole pod sideways (across, in its own plane) by
    sweep * L * xn^2 (a curved feather). Round ends, no degenerate tips, so the outline stays clean."""
    dx = V(d).normalized()
    df = V(f) - V(f).dot(dx) * dx
    df = df.normalized() if df.length > 1e-6 else dx.orthogonal().normalized()
    dy = df.cross(dx).normalized()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    c = V(center)
    for v in bm.verts:
        xn = max(-1.0, min(1.0, v.co.z))
        k = shape(xn) if shape else 1.0
        kt = thick_shape(xn) if thick_shape else 1.0
        lz = v.co.x * T / 2 * kt + bend * L * xn * xn + arch * L * (1 - xn * xn)
        ly = v.co.y * W / 2 * k + sweep * L * xn * xn
        v.co = c + dx * (xn * L / 2) + dy * ly + df * lz
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)
