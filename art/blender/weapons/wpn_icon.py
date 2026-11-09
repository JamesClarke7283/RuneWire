"""wpn_icon: inventory icons for the first-person weapons, showing the weapon alone (no glove).

rwlib.finish(icon=True) frames the whole scene, glove included, from the front. Inventory and shop
cards read better as a clean side-on profile, so weapon scripts end like this instead:

    rw.finish("vm_arc_pistol", "weapons", icon=False)
    import wpn_icon
    wpn_icon.render("vm_arc_pistol")      # -> assets/icons/items/vm_arc_pistol.png

The camera is orthographic and fitted tightly to the visible meshes. It looks at the weapon's right
side (-X) from slightly in front and above, so the muzzle (Blender -Y) points to the RIGHT of the image.
Objects named in `hide` (default: the "Glove") and their children are left out of the render.
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rwlib as rw  # noqa: E402


def _hidden_tree(names):
    out = []
    for o in bpy.context.scene.objects:
        base = o.name.split(".")[0]
        p = o
        while p is not None:
            if p.name.split(".")[0] in names:
                out.append(o)
                break
            p = p.parent
        del base
    return out


def render(asset, hide=("Glove",), size=256, view=(-1.0, -0.38, 0.42), margin=1.1, path=None):
    """Render a transparent square icon of the visible meshes (minus `hide`) and return its path."""
    path = path or os.path.join(rw.ASSETS, "icons", "items", asset + ".png")
    sc = bpy.context.scene
    hidden = [o for o in _hidden_tree(set(hide)) if not o.hide_render]
    for o in hidden:
        o.hide_render = True
    try:
        objs = [o for o in rw.all_mesh_objects() if not o.hide_render]
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        pts = []
        for o in objs:
            ev = o.evaluated_get(dg)
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        d = Vector(view).normalized()             # from the weapon toward the camera
        look = -d
        right = look.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(look).normalized()
        xs = [p.dot(right) for p in pts]
        ys = [p.dot(up) for p in pts]
        zs = [p.dot(look) for p in pts]
        centre = right * ((min(xs) + max(xs)) / 2) + up * ((min(ys) + max(ys)) / 2) + look * ((min(zs) + max(zs)) / 2)
        extent = max(max(xs) - min(xs), max(ys) - min(ys))

        rw._setup_render(size, True, True)
        cam_data = bpy.data.cameras.new("RW_IconCam")
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = extent * margin
        cam_data.clip_start = 0.001
        cam_data.clip_end = 100.0
        cam = bpy.data.objects.new("RW_IconCam", cam_data)
        sc.collection.objects.link(cam)
        cam.location = centre + d * 10.0
        cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        sc.camera = cam
        key = bpy.data.objects.new("RW_IconKey", bpy.data.lights.new("RW_IconKey", 'SUN'))
        key.data.energy = 3.2
        key.rotation_euler = (0.87, -0.17, 0.9)
        sc.collection.objects.link(key)
        fill = bpy.data.objects.new("RW_IconFill", bpy.data.lights.new("RW_IconFill", 'SUN'))
        fill.data.energy = 0.9
        fill.data.color = (0.75, 0.82, 1.0)
        fill.rotation_euler = (1.2, 0.0, -2.2)
        sc.collection.objects.link(fill)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        for o in (cam, key, fill):
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
            else:
                bpy.data.lights.remove(data)
        print("RWREPORT   icon", path)
    finally:
        for o in hidden:
            o.hide_render = False
    return path
