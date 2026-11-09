#!/usr/bin/env python3
"""Force correct import settings for 3D / VFX textures (VRAM compression + mipmaps).

Textures are applied to materials in code at runtime, so Godot's import never detects them as
3D textures and would keep them uncompressed without mipmaps, which is very slow on iGPUs.
UI textures (assets/textures/ui) and icons stay lossless. Prints the files it changed.
Usage: python3 tools/fix_imports.py   (then run the Godot import again)
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX = os.path.join(ROOT, "assets", "textures")


def want_params(path):
    name = os.path.basename(path)[: -len(".import")]
    rel = os.path.relpath(path, TEX).replace(os.sep, "/")
    if rel.startswith("ui/"):
        return None
    p = {"compress/mode": "2", "mipmaps/generate": "true"}
    p["compress/normal_map"] = "1" if name.endswith("_normal.png") else "0"
    if rel.startswith("fx/vfx_"):
        p["compress/high_quality"] = "true"
    return p


changed = 0
for dirpath, _dirs, files in os.walk(TEX):
    for f in files:
        if not f.endswith(".png.import"):
            continue
        path = os.path.join(dirpath, f)
        want = want_params(path)
        if not want:
            continue
        s = open(path).read()
        orig = s
        for k, v in want.items():
            pat = re.compile("^" + re.escape(k) + "=.*$", re.M)
            if pat.search(s):
                s = pat.sub(k + "=" + v, s)
            else:
                s = s.replace("[params]\n", "[params]\n\n" + k + "=" + v + "\n", 1)
        if s != orig:
            open(path, "w").write(s)
            changed += 1
            print("fixed", os.path.relpath(path, ROOT))
print("fix_imports: %d files updated" % changed, file=sys.stderr)
