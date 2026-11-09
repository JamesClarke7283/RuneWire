"""stationlib: shared helpers for the crafting stations and gathering nodes (art/blender/env/).

Used by the crafting stations prop_forge, prop_alchemy_table, prop_arcane_altar and prop_loom, and by the
gathering nodes node_ore_copper, node_ore_iron, node_glowcap, node_sunpetal and node_reeds.

    import os, sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import stationlib as S
    E, rw, pl, V = S.E, S.rw, S.pl, S.V

Builds on rwlib, partlib and envlib, none of which are edited. hull_rock(), surface_hit(), moss_on(),
preview_glow() and preview_glass() are copies of the helpers in art/blender/items/itemlib.py, so these
scripts don't depend on a module that the item artists are editing.

Godot notes that shaped the material names (see scripts/autoload/material_library.gd):
* A flat material whose name contains "grass", "leaf", "leaves", "foliage", "flower" or "petal" gets the
  wind-sway foliage shader, which DROPS emission. The glowing sunpetal petals are therefore called "SunBloom".
* The sway moves each vertex by its height above its node's origin (up to 7 cm for "grass" names), so parts
  that touch must either all sway or none. The reed stalks, leaves and cattail heads all use "ReedGrass*".
* M_<Set>__rrggbb on a textured set multiplies the texture by the tint (used for the darker iron-ore rock).

Conventions (ASSET_SPEC Batch C): metres, +Z up, the front faces -Y, origin at the ground centre, collision
proxies from rw.collision_box / rw.collision_cylinder, an empty "LightPoint" where a warm light goes.
Gathering nodes keep everything that gets gathered in ONE child object named "Harvest".
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, ".."), os.path.join(HERE, "..", "parts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import envlib as E  # noqa: E402
import partlib as pl  # noqa: E402

rw = E.rw
V = Vector
CAT = "env"
QA_DIR = "/tmp/rwqa"


# --------------------------------------------------------------------------------------
# Accent materials (flat colours and glows). Large surfaces use library M_* materials.
# --------------------------------------------------------------------------------------

ACCENTS = {
    # name: ("flat", colour, roughness, metallic) or ("glow", colour, strength)
    # forge
    "Brick": ("flat", "b8523a", 0.85, 0.0),
    "BrickDark": ("flat", "963f2d", 0.85, 0.0),
    "BrickLight": ("flat", "cf6a48", 0.85, 0.0),
    "Coal": ("flat", "3b343a", 0.9, 0.0),
    "FlameGold": ("glow", "ffd35a", 3.0),
    "EndGrain": ("flat", "d9a96a", 0.9, 0.0),
    # alchemy
    "AlchemyGreen": ("glow", "5cf06a", 1.6),
    "AlchemyPurple": ("glow", "b45cff", 1.6),
    "Parchment": ("flat", "f4e4bc", 0.9, 0.0),
    "Twine": ("flat", "c9a46a", 0.9, 0.0),
    "Herb": ("flat", "5d9e3c", 0.85, 0.0),
    "HerbSage": ("flat", "93b86e", 0.85, 0.0),
    "HerbLavender": ("flat", "9a7ad8", 0.85, 0.0),
    "HerbBerry": ("flat", "d9463c", 0.6, 0.0),
    "BookRed": ("flat", "a3312f", 0.7, 0.0),
    "BookTeal": ("flat", "2f7f86", 0.7, 0.0),
    "BookPurple": ("flat", "5d3a8e", 0.7, 0.0),
    "Clay": ("flat", "c27a4a", 0.85, 0.0),
    # altar
    "RuneViolet": ("glow", "a066ff", 3.0),
    "RuneVioletSoft": ("glow", "a066ff", 1.6),
    "Wax": ("flat", "f3e4c4", 0.6, 0.0),
    "CandleFlame": ("glow", "ffc85a", 3.0),
    "StoneDark": ("flat", "4d4858", 0.9, 0.0),
    # loom
    "Thread": ("flat", "efe3c6", 0.9, 0.0),
    "YarnRed": ("flat", "d9473b", 0.9, 0.0),
    "YarnGold": ("flat", "f2b43a", 0.9, 0.0),
    "YarnTeal": ("flat", "2fa39a", 0.9, 0.0),
    "YarnViolet": ("flat", "8a5cc8", 0.9, 0.0),
    "YarnBlue": ("flat", "3f74c4", 0.9, 0.0),
    "YarnCream": ("flat", "f3e6c8", 0.9, 0.0),
    "Wicker": ("flat", "c8954e", 0.9, 0.0),
    "WickerDark": ("flat", "9c6b35", 0.9, 0.0),
    "Fibre": ("flat", "e6c766", 0.9, 0.0),
    # nature
    "Moss": ("flat", "6e9f3a", 0.95, 0.0),
    "MossLight": ("flat", "8cc04a", 0.95, 0.0),
    "RotWood": ("flat", "8a6040", 0.9, 0.0),
    "RotWoodDark": ("flat", "5e3e28", 0.95, 0.0),
    "Mud": ("flat", "5c4431", 0.95, 0.0),
    "MudDark": ("flat", "463324", 0.95, 0.0),
    "GlowcapCap": ("glow", "4fd8ff", 2.2),
    "GlowcapGill": ("glow", "2f9fd6", 1.2),
    "GlowcapSpot": ("flat", "f2fcff", 0.5, 0.0),
    "GlowcapStem": ("flat", "e3efe9", 0.8, 0.0),
    "SunBloom": ("glow", "ffc934", 0.9),
    "SunBloomEye": ("glow", "ff7f1e", 1.0),
    "SunStem": ("flat", "5aa63a", 0.8, 0.0),
    "SunSepal": ("flat", "468f33", 0.8, 0.0),
    "ReedGrass": ("flat", "b7c05a", 0.85, 0.0),
    "ReedGrassGold": ("flat", "d8c463", 0.85, 0.0),
    "ReedGrassGreen": ("flat", "86ad4a", 0.85, 0.0),
    "ReedGrassHead": ("flat", "6b4226", 0.9, 0.0),
    "ReedStub": ("flat", "a29a52", 0.9, 0.0),
}


def M(name):
    """Accent material by name: stationlib ACCENTS first, then envlib's (Soot, Iron, Leaf, Water...)."""
    if name in ACCENTS:
        k = ACCENTS[name]
        if k[0] == "glow":
            return rw.glow(name, k[1], k[2])
        return rw.flat(name, k[1], k[2], k[3])
    return E.M(name)


def reset():
    """rw.reset() plus every accent material created up front, so envlib / partlib helpers can take the accent
    names as plain strings. Unused materials have no users: they are neither saved nor exported."""
    sc = rw.reset()
    for name in ACCENTS:
        M(name)
    for name in E.ACCENTS:
        E.M(name)
    E.M("Water")
    return sc


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
    """Previews only: AgX washes bright emission toward white, so a library glow (M_EmberGlow...) gets a darker
    base and a moderate emission to keep its hue in the renders. Godot replaces M_* materials by name."""
    m = rw._resolve_mat(mat_name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(base_hex)
    b.inputs["Emission Color"].default_value = rw._lin(emit_hex)
    b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = rw._lin(base_hex)[:3] + (m.diffuse_color[3],)
    return m


def preview_glass(alpha=0.22, base="7f9fb8"):
    """Previews only: rwlib's M_Glass stand-in is a bright film that turns saturated contents pale. Use a
    thinner, darker film so glowing liquids keep their colour (Godot uses its own glass shader by name)."""
    m = bpy.data.materials.get("M_Glass")
    if m is None:
        return
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Base Color"].default_value = rw._lin(base)
    m.diffuse_color = rw._lin(base)[:3] + (alpha,)


# --------------------------------------------------------------------------------------
# Mesh builders
# --------------------------------------------------------------------------------------

def ring_pts(n, rx, ry, z, c=(0.0, 0.0), p=2.0, phase=0.0, wob=None):
    """n points on a superellipse (p = 2 ellipse, larger p boxier) at height z. wob(angle) -> radial factor
    offset (e.g. 0.05 * sin(3a)) for organic outlines."""
    pts = []
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(ca) ** (2.0 / p), ca)
        y = ry * math.copysign(abs(sa) ** (2.0 / p), sa)
        f = 1.0 + (wob(a) if wob else 0.0)
        pts.append((c[0] + x * f, c[1] + y * f, z))
    return pts


def loft(name, rings, m=None, cap_bottom=True, cap_top=True, smooth_angle=50, fan=False):
    """Skin rings of 3D points (closed loops, same count, bottom -> top) into one closed mesh.
    fan=True caps with a fan to the ring centre (better for non-planar rings) instead of an n-gon."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for k in range(len(vr) - 1):
        a, b = vr[k], vr[k + 1]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))

    def cap(ring, top):
        if fan:
            c = V((0, 0, 0))
            for v in ring:
                c += v.co
            cv = bm.verts.new(c / len(ring))
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((ring[i], ring[j], cv) if top else (ring[j], ring[i], cv))
        else:
            bm.faces.new(ring if top else list(reversed(ring)))
    if cap_bottom:
        cap(vr[0], False)
    if cap_top:
        cap(vr[-1], True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat(m), smooth_angle)


def lathe(name, prof, segs=16, loc=(0, 0, 0), m=None, smooth=50, cap_bottom=False, cap_top=False, axis=(0, 0, 1),
          spin=0.0):
    """Revolve [(r, h), ...] (bottom -> top) about local Z, aim local Z along `axis`, move to loc.
    Start/end the profile at r = 0 for closed solids."""
    return pl.lathe_axis(name, prof, axis, loc, segs, mat(m), cap_bottom, cap_top, smooth, spin)


def flame(name, base, h, r, m="FlameGold", segs=8, lean=(0.0, 0.0)):
    """Cartoon teardrop flame standing on `base`, height h, max radius r; `lean` bends the tip (x, y)."""
    prof = [(0.0, 0.0), (r * 0.7, h * 0.1), (r, h * 0.28), (r * 0.82, h * 0.52), (r * 0.42, h * 0.78), (0.0, h)]
    o = lathe(name, prof, segs, (0, 0, 0), m, 70)
    if lean != (0.0, 0.0):
        E.deform(o, lambda p: V((p.x + lean[0] * (p.z / h) ** 2, p.y + lean[1] * (p.z / h) ** 2, p.z)))
        rw.smooth(o, 70)
    o.location = base
    return o


def carve(target, cutters, transfer=True):
    """Boolean-subtract cutters (joined first) from target. With transfer=True the new faces take the
    cutter's material (so a recess can be given its own material by giving the cutter one)."""
    cutters = [c for c in cutters if c is not None]
    if not cutters:
        return target
    for c in cutters:
        rw.apply_modifiers(c)
    cut = rw.join(cutters, "cutter", origin=None) if len(cutters) > 1 else cutters[0]
    rw.apply_modifiers(target)
    md = target.modifiers.new("Carve", 'BOOLEAN')
    md.operation = 'DIFFERENCE'
    md.object = cut
    md.solver = 'EXACT'
    try:
        md.material_mode = 'TRANSFER' if transfer else 'INDEX'
    except Exception:
        pass
    rw._active(target)
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cut, do_unlink=True)
    return target


def oriented(o, z_dir, loc, x_hint=None, spin=0.0):
    """Rotate o's mesh so its local +Z points along z_dir, then move it to loc (partlib.align)."""
    return pl.align(o, z_dir, loc, x_hint, spin)


# --------------------------------------------------------------------------------------
# Rocks and surfaces (copies of the itemlib helpers)
# --------------------------------------------------------------------------------------

def _fib_dirs(n, rng, jitter=0.35):
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        th = ga * i
        d = V((math.cos(th) * r, math.sin(th) * r, z))
        d += V((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
        out.append(d.normalized())
    return out


def hull_rock(name, size, loc=(0, 0, 0), seed=0, n_points=16, jitter=0.35, rmin=0.8, flat_bottom=0.0,
              flat_top=0.0, dissolve_deg=8.0, bevel=0.02, m="M_StoneRough", rot_z=0.0, bevel_segments=1, cuts=()):
    """Chunky faceted cartoon rock: convex hull of jittered points on an ellipsoid of `size`, big flat facets.
    flat_bottom / flat_top (0..1) slice the bottom / top flat at that fraction of the half-height.
    cuts = [(point, outward_normal), ...] slice off everything beyond each plane (relative to the centre,
    before rot_z)."""
    rng = random.Random(seed)
    sx, sy, sz = (s / 2.0 for s in size)
    bm = bmesh.new()
    for d in _fib_dirs(n_points, rng, jitter):
        r = rng.uniform(rmin, 1.0)
        bm.verts.new((d.x * sx * r, d.y * sy * r, d.z * sz * r))
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    unused = list({v for v in res.get("geom_interior", []) + res.get("geom_unused", [])
                   if isinstance(v, bmesh.types.BMVert) and v.is_valid})
    if unused:
        bmesh.ops.delete(bm, geom=unused, context='VERTS')
    planes = [((0, 0, sign * sz * amount), (0, 0, sign)) for (amount, sign) in ((flat_bottom, -1), (flat_top, 1))
              if amount]
    planes += [(tuple(c), tuple(n)) for (c, n) in cuts]
    for (co, no) in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r2 = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no, clear_outer=True)
        edges = [e for e in r2["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            try:
                bmesh.ops.edgeloop_fill(bm, edges=edges)
            except Exception:
                bmesh.ops.holes_fill(bm, edges=edges)
    if dissolve_deg:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:], edges=bm.edges[:])
    if rot_z:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(rot_z), 3, 'Z'))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=V(loc))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = pl.obj_from_bm(name, bm, mat(m), 0)
    rw.flat_shade(o)
    if bevel:
        md = o.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel
        md.segments = bevel_segments
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(25)
        md.harden_normals = True
        md.use_clamp_overlap = True
        rw.apply_modifiers(o)
    return o


def surface_hit(o, origin, direction):
    """Ray-cast onto object o (world space). Returns (point, normal) or (None, None)."""
    bpy.context.view_layer.update()
    mw = o.matrix_world
    inv = mw.inverted()
    lo = inv @ V(origin)
    ld = (inv.to_3x3() @ V(direction)).normalized()
    ok, loc, nrm, _ = o.ray_cast(lo, ld)
    if not ok:
        return None, None
    return mw @ loc, (mw.to_3x3().inverted().transposed() @ nrm).normalized()


def hit_toward(o, centre, direction, dist=20.0):
    """Surface point of o seen from far out along `direction` from `centre` (ray cast back toward centre)."""
    d = V(direction).normalized()
    return surface_hit(o, V(centre) + d * dist, -d)


def moss_on(target, points, size=0.07, seed=0, m=("Moss", "MossLight"), squash=0.45, sink=0.35, subdiv=2):
    """Soft flattened moss cushions dropped onto target's surface from above at the given (x, y) points."""
    rnd = random.Random(seed)
    out = []
    for i, (x, y) in enumerate(points):
        p, n = surface_hit(target, (x, y, 50.0), (0, 0, -1))
        if p is None:
            continue
        s = size * rnd.uniform(0.75, 1.2)
        o = rw.ico("moss", 0.5, subdiv, (0, 0, 0), (0, 0, rnd.uniform(0, 90)), (s * 1.2, s, s * squash),
                   mat(m[i % len(m)]), None, 70)
        pl.align(o, n, p - n * (s * squash * 0.5 * sink))
        out.append(o)
    return out


def surface_path(target, centre, dirs, lift=0.0):
    """Project a list of directions (from `centre`) onto target's surface: returns [(point, normal), ...]."""
    out = []
    for d in dirs:
        p, n = hit_toward(target, centre, d)
        if p is not None:
            out.append((p + n * lift, n))
    return out


def sph(az_deg, el_deg):
    """Unit direction from azimuth (degrees, 0 = +X, 90 = +Y) and elevation (degrees above the horizon)."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return V((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))


# --------------------------------------------------------------------------------------
# Finishing and QA
# --------------------------------------------------------------------------------------

def ground_centre(mains=()):
    """Shift every root (meshes, empties, collision proxies) so the visible bounding box is centred on X/Y = 0
    and sits on z = 0, then put the origin of each object in `mains` back at the world origin."""
    bpy.context.view_layer.update()
    mn, mx = rw.bounds()
    shift = V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in pl.roots():
        o.location -= shift
    bpy.context.view_layer.update()
    for o in mains:
        rw.set_origin(o, (0, 0, 0))
    bpy.context.view_layer.update()
    return shift


def node_report(asset, names):
    """Print where the load-bearing nodes are (world origin) and who their parent is."""
    bpy.context.view_layer.update()
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            print("RWCHECK %s MISSING node %s" % (asset, nm))
            continue
        p = o.matrix_world.translation
        print("RWCHECK %s node %-12s origin (%.3f, %.3f, %.3f) parent=%s type=%s" % (
            asset, nm, p.x, p.y, p.z, o.parent.name if o.parent else "-", o.type))


def finish(asset, size, budget, nodes=(), height_tol=0.12):
    """E.check + node report + rw.finish (env category, no icon)."""
    E.check(asset, size, budget, height_tol=height_tol)
    node_report(asset, nodes)
    rw.finish(asset, CAT, previews=E.previews(), icon=False)


def qa_on():
    return bool(os.environ.get("RW_QA"))


def qa_render(asset, tag, view="front34", size=480):
    os.makedirs(QA_DIR, exist_ok=True)
    return rw.render_view(os.path.join(QA_DIR, "%s_%s_%s.png" % (asset, tag, view)), view, size)


def qa_harvested(asset, harvest, scale=0.05, views=("front34",)):
    """QA (after rw.finish has saved and exported): render the node with its Harvest object shrunk, so the
    depleted node can be checked for still looking like a natural rock / stump / clump."""
    harvest.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    for v in views:
        qa_render(asset, "harvested", v)
    harvest.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
