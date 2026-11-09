"""QA helper (not an asset): render a saved env .blend with its collision proxies shown in red and the visual
meshes as ghosts, so collision coverage can be checked by eye.

    env -u LD_LIBRARY_PATH blender --background art/blender/env/<asset>.blend \
        --python art/blender/env/qa_col.py -- [out_dir] [views]

Writes <out_dir>/<asset>_col_<view>.png (default out_dir /tmp/rwqa, views front34,back34).
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import rwlib as rw  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if len(argv) > 0 else "/tmp/rwqa"
views = argv[1].split(",") if len(argv) > 1 else ["front34", "back34"]
asset = os.path.splitext(os.path.basename(bpy.data.filepath))[0]

ghost = rw.material("QA_Ghost", "e8e4dc", 0.9, 0.0, None, 0.0, 0.22)
red = rw.material("QA_Col", "ff2a2a", 0.6, 0.0, "ff2a2a", 0.4, 0.6)
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    if "-colonly" in o.name or "-convcolonly" in o.name:
        o.hide_render = False
        o.display_type = 'SOLID'
        o.data.materials.clear()
        o.data.materials.append(red)
    else:
        for i in range(len(o.data.materials)):
            o.data.materials[i] = ghost
        if len(o.data.materials) == 0:
            o.data.materials.append(ghost)
os.makedirs(out_dir, exist_ok=True)
for v in views:
    rw.render_view(os.path.join(out_dir, "%s_col_%s.png" % (asset, v)), v, size=560)
