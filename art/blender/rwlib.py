"""rwlib: shared Blender helpers for RuneWire asset generator scripts.

Every model in the game is built by a Python generator script that runs headless:

    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/blender/parts/crate.py

A generator script looks like this:

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import rwlib as rw

    rw.reset()
    body = rw.rounded_box("Crate", (1, 1, 1), radius=0.04, mat="M_WoodPlanks")
    ...
    rw.finish("part_crate", "parts")   # .blend + .glb + preview renders + report

Conventions (see art/ASSET_SPEC.md):
* Units are metres. Blender +Z is up. The FRONT of every model faces Blender -Y
  (glTF/Godot +Z, Vector3.MODEL_FRONT).
* Library materials are named "M_<Name>" (textured in Godot from assets/textures/).
  Add a tint with "M_<Name>__rrggbb", e.g. "M_Fabric__8a2be2".
  Any other material name is a flat colour: Godot converts its base colour, emission
  and alpha into a toon material.
* Rotations passed to helpers are in DEGREES.
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

PROJECT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ART = os.path.join(PROJECT, "art")
ASSETS = os.path.join(PROJECT, "assets")

# Library materials: name -> (preview base colour hex (sRGB), roughness, metallic, emission hex, emission strength, alpha)
# The Godot side (scripts/autoload/material_library.gd) replaces these with textured toon materials.
LIB = {
    "M_WoodPlanks":   ("b8834d", 0.80, 0.0, None, 0.0, 1.0),
    "M_WoodDark":     ("6e4528", 0.80, 0.0, None, 0.0, 1.0),
    "M_Bark":         ("6a4a35", 0.90, 0.0, None, 0.0, 1.0),
    "M_Leaves":       ("5fae3e", 0.80, 0.0, None, 0.0, 1.0),
    "M_Stone":        ("a8a397", 0.85, 0.0, None, 0.0, 1.0),
    "M_StoneRough":   ("8c877d", 0.90, 0.0, None, 0.0, 1.0),
    "M_Cobble":       ("9c968a", 0.85, 0.0, None, 0.0, 1.0),
    "M_Plaster":      ("efe2c4", 0.90, 0.0, None, 0.0, 1.0),
    "M_RoofTiles":    ("b9533b", 0.80, 0.0, None, 0.0, 1.0),
    "M_Brass":        ("dba843", 0.35, 1.0, None, 0.0, 1.0),
    "M_Copper":       ("cc7743", 0.35, 1.0, None, 0.0, 1.0),
    "M_Steel":        ("a9b0b8", 0.40, 1.0, None, 0.0, 1.0),
    "M_PaintedMetal": ("e8762c", 0.55, 0.3, None, 0.0, 1.0),
    "M_DarkMetal":    ("40454d", 0.50, 0.8, None, 0.0, 1.0),
    "M_Rust":         ("8e4c2d", 0.85, 0.3, None, 0.0, 1.0),
    "M_Rubber":       ("2d2d31", 0.90, 0.0, None, 0.0, 1.0),
    "M_Leather":      ("7c4b2d", 0.70, 0.0, None, 0.0, 1.0),
    "M_Fabric":       ("e8e2d6", 0.95, 0.0, None, 0.0, 1.0),
    "M_Skin":         ("f1c29b", 0.70, 0.0, None, 0.0, 1.0),
    "M_Glass":        ("c4e8ff", 0.05, 0.0, None, 0.0, 0.35),
    "M_RuneGlow":     ("9a66ff", 0.40, 0.0, "a97bff", 4.0, 1.0),
    "M_TechGlow":     ("ff8c2e", 0.40, 0.0, "ff9b3f", 4.0, 1.0),
    "M_EmberGlow":    ("ffb54a", 0.40, 0.0, "ffa841", 4.0, 1.0),
    "M_Crystal":      ("70f0e2", 0.10, 0.0, "5fe9ff", 2.0, 0.85),
}


# --------------------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------------------

def hex_to_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_linear(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _lin(hexcol):
    r, g, b = srgb_to_linear(hex_to_srgb(hexcol))
    return (r, g, b, 1.0)


# --------------------------------------------------------------------------------------
# Scene
# --------------------------------------------------------------------------------------

def reset():
    """Start from an empty factory scene in metres."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


def _active(o):
    for s in bpy.context.selected_objects:
        s.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)


def _finish_new(o, name, mat, parent, bevel, bevel_segments):
    if o.type == 'MESH':
        apply_transform(o)  # bake rotation/scale into the mesh: nodes keep only a location
    o.name = name
    if o.data is not None:
        o.data.name = name
    if mat is not None:
        set_mat(o, mat)
    if bevel and bevel > 0:
        add_bevel(o, bevel, bevel_segments)
    if parent is not None:
        set_parent(o, parent)
    return o


def _rad(rot):
    return tuple(math.radians(a) for a in rot)


def apply_transform(o, location=False, rotation=True, scale=True):
    _active(o)
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
    return o


# --------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------

def material(name, color="cccccc", roughness=0.6, metallic=0.0, emission=None, strength=0.0, alpha=1.0):
    """Get or create a Principled material. Use for flat-coloured (non-library) materials."""
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = _lin(color)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    if emission:
        b.inputs["Emission Color"].default_value = _lin(emission)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = _lin(color)[:3] + (alpha,)
    return m


def lib(name, tint=None):
    """Library material by short or full name, optionally tinted: lib("Fabric", "8a2be2")."""
    full = name if name.startswith("M_") else "M_" + name
    if full not in LIB:
        raise KeyError("Unknown library material %s (known: %s)" % (full, ", ".join(sorted(LIB))))
    base, rough, metal, emi, stren, alpha = LIB[full]
    if tint:
        tint = tint.lstrip("#").lower()
        a = hex_to_srgb(base)
        t = hex_to_srgb(tint)
        mixed = "".join("%02x" % int(max(0, min(255, round(255 * (0.25 * x + 0.75 * y))))) for x, y in zip(a, t))
        return material("%s__%s" % (full, tint), mixed, rough, metal, emi, stren, alpha)
    return material(full, base, rough, metal, emi, stren, alpha)


def flat(name, color, roughness=0.6, metallic=0.0):
    """Flat colour material (no texture in Godot)."""
    return material(name, color, roughness, metallic)


def glow(name, color, strength=3.0):
    """Flat emissive material (eyes, lamps, runes with a custom colour)."""
    return material(name, color, 0.4, 0.0, color, strength)


def _resolve_mat(mat):
    if mat is None or isinstance(mat, bpy.types.Material):
        return mat
    if isinstance(mat, str):
        if mat.startswith("M_"):
            if "__" in mat:
                base, tint = mat.split("__", 1)
                return lib(base, tint)
            return lib(mat)
        m = bpy.data.materials.get(mat)
        if m is None:
            raise KeyError("Material %s does not exist; create it with rw.flat()/rw.glow() first" % mat)
        return m
    raise TypeError(mat)


def set_mat(o, mat, faces=None):
    """Assign a material to all faces (or to the given face indices)."""
    m = _resolve_mat(mat)
    if m.name not in [s.name for s in o.data.materials if s]:
        o.data.materials.append(m)
    idx = [i for i, s in enumerate(o.data.materials) if s and s.name == m.name][0]
    for p in o.data.polygons:
        if faces is None or p.index in faces:
            p.material_index = idx
    return o


def set_mat_where(o, mat, predicate):
    """Assign a material to faces whose (world-space centre, world-space normal) satisfy predicate."""
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    faces = [p.index for p in o.data.polygons if predicate(mw @ p.center, (nm @ p.normal).normalized())]
    return set_mat(o, mat, faces)


# --------------------------------------------------------------------------------------
# Modifiers & shading
# --------------------------------------------------------------------------------------

def add_bevel(o, width=0.02, segments=2, angle=40.0, harden=True):
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = harden
    m.use_clamp_overlap = True
    return m


def add_subsurf(o, levels=2):
    m = o.modifiers.new("Subsurf", 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    return m


def add_solidify(o, thickness=0.02):
    m = o.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = thickness
    return m


def add_mirror(o, axis="X", merge=True):
    m = o.modifiers.new("Mirror", 'MIRROR')
    m.use_axis = (axis == "X", axis == "Y", axis == "Z")
    m.use_mirror_merge = merge
    return m


def add_displace_noise(o, strength=0.08, size=0.5, seed=0):
    tex = bpy.data.textures.new(o.name + "_noise", 'CLOUDS')
    tex.noise_scale = size
    tex.noise_depth = 2
    m = o.modifiers.new("Displace", 'DISPLACE')
    m.texture = tex
    m.strength = strength
    m.mid_level = 0.5
    m.texture_coords = 'OBJECT'
    if seed:
        # Offset the texture space with a hidden empty so different seeds give different shapes.
        e = bpy.data.objects.new(o.name + "_noise_space", None)
        bpy.context.scene.collection.objects.link(e)
        e.location = (seed * 7.31, seed * 3.17, seed * 5.53)
        e.hide_render = True
        e["rw_helper"] = True
        m.texture_coords_object = e
    return m


def smooth(o, angle=40.0):
    """Smooth shading with sharp edges above `angle` degrees (cartoon-friendly)."""
    _active(o)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle), keep_sharp_edges=True)
    except Exception:
        bpy.ops.object.shade_smooth()
    return o


def flat_shade(o):
    _active(o)
    bpy.ops.object.shade_flat()
    return o


def apply_modifiers(o):
    _active(o)
    for m in list(o.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            print("rwlib: could not apply", m.name, "on", o.name, e)
    return o


# --------------------------------------------------------------------------------------
# Primitives (all return the new object; `rot` is in degrees)
# --------------------------------------------------------------------------------------

def box(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.0, bevel_segments=2, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=_rad(rot))
    o = bpy.context.active_object
    o.scale = size
    apply_transform(o)
    return _finish_new(o, name, mat, parent, bevel, bevel_segments)


def rounded_box(name, size=(1, 1, 1), radius=0.05, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, segments=3, parent=None):
    """Box with soft rounded edges (bevel modifier, kept live until export)."""
    o = box(name, size, loc, rot, mat, 0.0, 2, None)
    m = o.modifiers.new("Round", 'BEVEL')
    m.width = radius
    m.segments = segments
    m.limit_method = 'NONE'
    m.use_clamp_overlap = True
    m.harden_normals = False
    smooth(o, 35)
    if parent is not None:
        set_parent(o, parent)
    return o


def cylinder(name, radius=0.5, depth=1.0, verts=24, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.0,
             bevel_segments=2, parent=None, cap="NGON"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, end_fill_type=cap,
                                        location=loc, rotation=_rad(rot))
    o = bpy.context.active_object
    o = _finish_new(o, name, mat, parent, bevel, bevel_segments)
    smooth(o, 40)
    return o


def cone(name, r1=0.5, r2=0.0, depth=1.0, verts=24, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.0,
         parent=None):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc,
                                    rotation=_rad(rot))
    o = bpy.context.active_object
    o = _finish_new(o, name, mat, parent, bevel, 2)
    smooth(o, 40)
    return o


def sphere(name, radius=0.5, segments=24, rings=12, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat=None,
           parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc,
                                         rotation=_rad(rot))
    o = bpy.context.active_object
    o.scale = scale
    apply_transform(o)
    o = _finish_new(o, name, mat, parent, 0, 2)
    smooth(o, 80)
    return o


def ico(name, radius=0.5, subdiv=2, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat=None, parent=None,
        smooth_angle=80):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius, location=loc, rotation=_rad(rot))
    o = bpy.context.active_object
    o.scale = scale
    apply_transform(o)
    o = _finish_new(o, name, mat, parent, 0, 2)
    if smooth_angle:
        smooth(o, smooth_angle)
    return o


def torus(name, major=0.5, minor=0.1, major_seg=32, minor_seg=12, loc=(0, 0, 0), rot=(0, 0, 0), mat=None,
          parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=major_seg,
                                     minor_segments=minor_seg, location=loc, rotation=_rad(rot))
    o = bpy.context.active_object
    o = _finish_new(o, name, mat, parent, 0, 2)
    smooth(o, 80)
    return o


def blob(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, subdiv=3, noise=0.12, noise_size=0.6,
         seed=1, parent=None, smooth_angle=70):
    """Organic lump (rocks, canopies, clouds): ico sphere + noise displacement, applied."""
    o = ico(name, 0.5, subdiv, loc, rot, size, mat, None, 0)
    if noise > 0:
        add_displace_noise(o, noise, noise_size, seed)
        apply_modifiers(o)
    if smooth_angle:
        smooth(o, smooth_angle)
    if parent is not None:
        set_parent(o, parent)
    return o


def lathe(name, profile, segments=32, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, cap_bottom=True,
          cap_top=True, smooth_angle=50):
    """Revolve a profile [(radius, z), ...] (bottom to top) around the local Z axis."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            try:
                bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError:
                pass
    if cap_bottom and profile[0][0] > 1e-5:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top and profile[-1][0] > 1e-5:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bmesh(name, bm, loc, rot)
    o = _finish_new(o, name, mat, parent, 0, 2)
    if smooth_angle:
        smooth(o, smooth_angle)
    return o


def extrude_poly(name, points, depth=0.1, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.0, parent=None):
    """Extrude a 2D polygon [(x, y), ...] (counter-clockwise, in the XY plane) along Z by `depth`,
    centred on Z=0. Produces a closed prism."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, -depth / 2)) for (x, y) in points]
    top = [bm.verts.new((x, y, depth / 2)) for (x, y) in points]
    n = len(points)
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bmesh(name, bm, loc, rot)
    return _finish_new(o, name, mat, parent, bevel, 2)


def gear(name, radius=0.5, teeth=12, tooth_depth=0.08, thickness=0.1, hole=0.12, loc=(0, 0, 0), rot=(0, 0, 0),
         mat="M_Brass", bevel=0.01, parent=None):
    """Cartoon gear lying in the XY plane (axis = local Z)."""
    pts = []
    n = teeth * 4
    for i in range(n):
        a = 2 * math.pi * i / n
        phase = i % 4
        r = radius if phase in (1, 2) else radius - tooth_depth
        pts.append((r * math.cos(a), r * math.sin(a)))
    o = extrude_poly(name, pts, thickness, loc, rot, mat, 0.0, None)
    if hole and hole > 0:
        cutter = cylinder(name + "_hole", hole, thickness * 3, 24, loc, rot)
        boolean(o, cutter, 'DIFFERENCE')
    if bevel:
        add_bevel(o, bevel, 2)
    smooth(o, 30)
    if parent is not None:
        set_parent(o, parent)
    return o


def tube(name, points, radius=0.03, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, resolution=6, parent=None,
         taper=None, smooth_curve=True):
    """Tube along a 3D path [(x, y, z), ...] (pipes, cables, handles, branches). Converted to mesh."""
    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.bevel_depth = radius
    cd.bevel_resolution = resolution
    cd.use_fill_caps = True
    sp = cd.splines.new('BEZIER' if smooth_curve else 'POLY')
    if smooth_curve:
        sp.bezier_points.add(len(points) - 1)
        for bp, p in zip(sp.bezier_points, points):
            bp.co = p
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
            if taper is not None:
                pass
    else:
        sp.points.add(len(points) - 1)
        for pt, p in zip(sp.points, points):
            pt.co = (p[0], p[1], p[2], 1.0)
    if taper is not None:
        pts = sp.bezier_points if smooth_curve else sp.points
        for i, pt in enumerate(pts):
            t = i / max(1, len(points) - 1)
            pt.radius = taper[0] + (taper[1] - taper[0]) * t
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = _rad(rot)
    _active(o)
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.active_object
    o = _finish_new(o, name, mat, parent, 0, 2)
    smooth(o, 60)
    return o


def _obj_from_bmesh(name, bm, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = _rad(rot)
    return o


def mesh_from_data(name, verts, faces, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = _rad(rot)
    return _finish_new(o, name, mat, parent, 0, 2)


# --------------------------------------------------------------------------------------
# Object operations
# --------------------------------------------------------------------------------------

def boolean(target, cutter, op='DIFFERENCE', apply=True, keep_cutter=False):
    m = target.modifiers.new("Bool", 'BOOLEAN')
    m.operation = op
    m.object = cutter
    m.solver = 'EXACT'
    if apply:
        _active(target)
        bpy.ops.object.modifier_apply(modifier=m.name)
        if not keep_cutter:
            bpy.data.objects.remove(cutter, do_unlink=True)
    else:
        cutter.hide_render = True
        cutter.hide_viewport = True
    return target


def duplicate(o, name=None, loc=None, rot=None, linked=False):
    n = o.copy()
    if not linked and o.data is not None:
        n.data = o.data.copy()
    for c in o.users_collection:
        c.objects.link(n)
    n.name = name or (o.name + "_dup")
    if loc is not None:
        n.location = loc
    if rot is not None:
        n.rotation_euler = _rad(rot)
    return n


def join(objs, name=None, origin=(0, 0, 0)):
    """Join meshes into one object (modifiers are applied first). The origin is moved to `origin`
    (world space; pass None to keep the first object's origin). Returns the joined object."""
    objs = [o for o in objs if o is not None]
    for o in objs:
        if o.type != 'MESH':
            _active(o)
            bpy.ops.object.convert(target='MESH')
        apply_modifiers(o)
    for s in bpy.context.selected_objects:
        s.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    if name:
        o.name = name
        o.data.name = name
    if origin is not None:
        set_origin(o, origin)
    return o


def center_origin(o):
    """Move the origin to the centre of the object's bounding box."""
    mn, mx = bounds([o])
    return set_origin(o, (mn + mx) / 2)


def set_parent(child, parent):
    """Parent while keeping the child's world transform."""
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw
    return child


def set_origin(o, point):
    """Move the object's origin to a world-space point without moving the geometry."""
    point = Vector(point)
    mw = o.matrix_world.copy()
    local = mw.inverted() @ point
    if o.type == 'MESH':
        o.data.transform(Matrix.Translation(-local))
    for c in o.children:
        c.matrix_parent_inverse = Matrix.Translation(-local) @ c.matrix_parent_inverse
    o.matrix_world = mw @ Matrix.Translation(local)
    return o


def empty(name, loc=(0, 0, 0), parent=None, size=0.1, rot=(0, 0, 0)):
    """Attachment point / pivot (exported to Godot as a Node3D with this name)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = _rad(rot)
    if parent is not None:
        set_parent(e, parent)
    return e


def radial_copies(o, count, axis="Z", center=(0, 0, 0), name_fmt=None, include_original=True):
    """Duplicate an object `count` times around an axis through `center`. Returns the list."""
    out = [o] if include_original else []
    c = Vector(center)
    ax = {"X": 'X', "Y": 'Y', "Z": 'Z'}[axis]
    for i in range(1, count):
        n = duplicate(o, (name_fmt % i) if name_fmt else "%s_%d" % (o.name, i))
        R = Matrix.Translation(c) @ Matrix.Rotation(2 * math.pi * i / count, 4, ax) @ Matrix.Translation(-c)
        n.matrix_world = R @ o.matrix_world
        out.append(n)
    if not include_original:
        bpy.data.objects.remove(o, do_unlink=True)
    return out


def box_uv(o, tile=2.0):
    """World-scale box-projected UVs: 1 UV unit = `tile` metres (library textures tile every 2 m).
    Call after the shape is final; modifiers are applied first."""
    apply_modifiers(o)
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = (nm @ f.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            p = mw @ loop.vert.co
            if ax == 0:
                u, v = (p.y if n.x > 0 else -p.y), p.z
            elif ax == 1:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            else:
                u, v = p.x, (p.y if n.z > 0 else -p.y)
            loop[uv].uv = (u / tile, v / tile)
    bm.to_mesh(o.data)
    bm.free()
    return o


def all_mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.get("rw_helper")]


def uv_all(tile=2.0):
    """Box-UV every mesh in the scene (skips collision proxies)."""
    for o in all_mesh_objects():
        if "-col" in o.name or "-convcol" in o.name:
            continue
        box_uv(o, tile)


def collision_box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, convex=False):
    """Invisible collision proxy for environment models (Godot import suffix -colonly / -convcolonly)."""
    suffix = "-convcolonly" if convex else "-colonly"
    o = box(name + suffix, size, loc, rot, None, 0, 2, parent)
    o.display_type = 'WIRE'
    o.hide_render = True
    return o


def collision_cylinder(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, verts=12):
    o = cylinder(name + "-convcolonly", radius, depth, verts, loc, rot, None, 0, 2, parent)
    o.display_type = 'WIRE'
    o.hide_render = True
    return o


# --------------------------------------------------------------------------------------
# Inspection
# --------------------------------------------------------------------------------------

def bounds(objs=None):
    objs = objs or [o for o in all_mesh_objects() if not o.hide_render]
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            w = ev.matrix_world @ Vector(c)
            mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
            mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
    return mn, mx


def tri_count(objs=None):
    objs = objs or [o for o in all_mesh_objects() if not o.hide_render]
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


def report(asset):
    mn, mx = bounds()
    size = mx - mn
    print("RWREPORT %s" % asset)
    print("RWREPORT   size Blender XYZ (w, d, h) = %.3f x %.3f x %.3f m" % (size.x, size.y, size.z))
    print("RWREPORT   bounds min %s max %s" % (tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx)))
    print("RWREPORT   triangles %d" % tri_count())
    for o in sorted(bpy.context.scene.objects, key=lambda x: x.name):
        if o.get("rw_helper"):
            continue
        par = o.parent.name if o.parent else "-"
        mats = ",".join(s.material.name for s in o.material_slots if s.material) if o.type == 'MESH' else ""
        print("RWREPORT   node %-28s type=%-6s parent=%-18s origin=%s mats=%s" % (
            o.name, o.type, par, tuple(round(v, 3) for v in o.matrix_world.translation), mats))


# --------------------------------------------------------------------------------------
# Rendering (previews for QA, icons for the UI)
# --------------------------------------------------------------------------------------

def _setup_render(size, transparent, outline=True):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
    except Exception:
        try:
            sc.view_settings.view_transform = 'Standard'
        except Exception:
            pass
    sc.render.use_freestyle = outline
    if outline:
        sc.render.line_thickness_mode = 'ABSOLUTE'
        sc.render.line_thickness = max(1.0, size / 300.0)
        vl = bpy.context.view_layer
        vl.use_freestyle = True
        fs = vl.freestyle_settings
        if not fs.linesets:
            fs.linesets.new("Lines")
        ls = fs.linesets[0]
        ls.select_by_visibility = True
        ls.select_by_edge_types = True
        ls.select_silhouette = True
        ls.select_border = True
        ls.select_crease = True
        if ls.linestyle is None:
            ls.linestyle = bpy.data.linestyles.get("RWLines") or bpy.data.linestyles.new("RWLines")
        ls.linestyle.color = (0.08, 0.06, 0.1)
        ls.linestyle.thickness = max(1.0, size / 300.0)
    world = bpy.data.worlds.get("RW_World") or bpy.data.worlds.new("RW_World")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.52, 0.62, 0.78, 1.0)
    bg.inputs[1].default_value = 0.9
    sc.world = world


def _temp_rig(target_min, target_max, view="front34", fov=35.0):
    sc = bpy.context.scene
    center = (target_min + target_max) / 2
    radius = max((target_max - target_min).length / 2, 0.05)
    dirs = {
        "front34": Vector((-0.75, -1.0, 0.55)),
        "back34": Vector((0.8, 1.0, 0.5)),
        "front": Vector((0, -1, 0.12)),
        "side": Vector((-1, 0, 0.12)),
        "top": Vector((0.001, -0.25, 1)),
        "icon": Vector((-0.8, -1.0, 0.7)),
    }
    d = dirs.get(view, dirs["front34"]).normalized()
    cam_data = bpy.data.cameras.new("RW_PreviewCam")
    cam_data.lens_unit = 'FOV'
    cam_data.angle = math.radians(fov)
    cam_data.clip_start = 0.01
    cam_data.clip_end = 10000
    cam = bpy.data.objects.new("RW_PreviewCam", cam_data)
    sc.collection.objects.link(cam)
    dist = radius / math.sin(math.radians(fov) / 2) * 1.08
    cam.location = center + d * dist
    look = (center - cam.location).normalized()
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    key = bpy.data.objects.new("RW_Key", bpy.data.lights.new("RW_Key", 'SUN'))
    key.data.energy = 3.2
    key.data.angle = math.radians(8)
    key.rotation_euler = (math.radians(50), math.radians(-10), math.radians(-35))
    sc.collection.objects.link(key)
    fill = bpy.data.objects.new("RW_Fill", bpy.data.lights.new("RW_Fill", 'SUN'))
    fill.data.energy = 0.8
    fill.data.color = (0.75, 0.82, 1.0)
    fill.rotation_euler = (math.radians(70), 0, math.radians(150))
    sc.collection.objects.link(fill)
    return [cam, key, fill]


def render_view(path, view="front34", size=640, transparent=False, outline=True, objs=None):
    mn, mx = bounds(objs)
    _setup_render(size, transparent, outline)
    temp = _temp_rig(mn, mx, view)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
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


def render_icon(path, size=256):
    """Transparent 3/4 icon for UI menus (shop / build catalogue)."""
    return render_view(path, "icon", size, transparent=True, outline=True)


# --------------------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------------------

def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for s in bpy.context.selected_objects:
        s.select_set(False)
    for o in bpy.context.scene.objects:
        if o.get("rw_helper") or o.type in ('CAMERA', 'LIGHT'):
            continue
        o.hide_set(False)
        o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_tangents=True,
        export_normals=True,
        export_texcoords=True,
        export_materials='EXPORT',
        export_image_format='NONE',
        export_vertex_color='ACTIVE',
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )
    print("RWREPORT   exported", path)
    return path


def finish(asset, category, previews=("front34", "back34"), icon=False, uv=True, uv_tile=2.0):
    """Standard ending for a generator script:
    world-scale UVs, save .blend, export .glb, render previews (+ optional UI icon), print a report."""
    if uv:
        uv_all(uv_tile)
    blend_dir = os.path.join(ART, "blender", category)
    os.makedirs(blend_dir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, asset + ".blend"))
    export_glb(os.path.join(ASSETS, "models", category, asset + ".glb"))
    report(asset)
    for v in previews:
        render_view(os.path.join(ART, "previews", category, "%s_%s.png" % (asset, v)), v)
    if icon:
        render_icon(os.path.join(ASSETS, "icons", "parts" if category == "parts" else "items", asset + ".png"))
