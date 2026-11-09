"""item_ember_essence: corked glass jar holding a glowing ember, about 0.19 x 0.19 x 0.3 m.

A chunky round-shouldered glass jar (M_Glass) with a rolled lip, a fat cork tied with twine, a little
parchment tag with a flame on it hanging at the front, and inside a lumpy glowing ember (M_EmberGlow)
with a yellow flame (rw.glow) curling up from it and a few floating sparks.
One mesh object "EmberEssence", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_ember_essence"
rw.reset()

body = [(0.0, 0.0), (0.072, 0.0), (0.088, 0.014), (0.093, 0.05), (0.093, 0.16), (0.085, 0.19), (0.064, 0.204),
        (0.058, 0.222)]
lip = [(0.067, 0.226), (0.069, 0.237), (0.063, 0.241), (0.0, 0.241)]
prof = il.curve_profile(body, 2) + lip
parts = [il.lathe("jar", prof, segs=28, m="M_Glass", smooth=60)]
rfun = lambda z: il.prof_radius(prof, z)  # noqa: E731
for (ang, zc, w, h) in ((-62, 0.1, 0.016, 0.075), (-52, 0.168, 0.012, 0.018)):
    parts.append(il.wrap_prism("shine", il.capsule_pts(w, h), il.lathe_map(rfun, ang, zc, 0.0016, 0.0015), "Shine"))

# the ember: a lumpy glowing coal with a curl of flame and floating sparks
ember = "M_EmberGlow"
il.preview_glow(ember, "ff5c0a", "ff4a00", 0.3)    # preview/icon only: Godot swaps M_* materials by name
parts.append(il.blob("coal", (0.11, 0.1, 0.085), (0, 0, 0.082), ember, 2, 1.0, 4, 0.03))
flame = [(0.0, 0.095), (0.044, 0.1), (0.047, 0.122), (0.034, 0.15), (0.016, 0.178), (0.0, 0.2)]
fl = il.lathe("flame", flame, segs=12, m="FlameCore", smooth=60)
T = il.Matrix.Translation
pl.xform(fl, T((0, 0, 0.1)) @ il.Matrix.Shear('XY', 4, (0.3, 0.0)) @ T((0, 0, -0.1)))   # lean the tip a little
parts.append(fl)
for (p, r) in (((0.052, -0.03, 0.16), 0.009), ((-0.058, -0.01, 0.135), 0.008), ((-0.025, 0.045, 0.18), 0.008),
               ((0.045, 0.035, 0.045), 0.008)):
    parts.append(rw.ico("spark", r, 1, p, (0, 0, 0), (1, 1, 1), il.mat("SparkCore"), None, 0))

# cork, twine around the neck and a hanging tag
parts.append(il.cork(0.21, 0.29, 0.056, 0.066, 18))
parts.append(rw.torus("twine", 0.066, 0.0065, 24, 6, (0, 0, 0.216), mat=il.mat("Twine")))
parts.append(rw.torus("twine", 0.067, 0.0065, 24, 6, (0, 0, 0.204), mat=il.mat("Twine")))
a = math.radians(-20)
d = V((math.sin(a), -math.cos(a), 0))
t = V((math.cos(a), math.sin(a), 0))
knot = d * 0.07 + V((0, 0, 0.21))
tag_c = d * 0.0995 + V((0, 0, 0.15))
parts.append(pl.sausage("tagstring", [knot, knot + d * 0.012 + V((0, 0, -0.02)), tag_c + V((0, 0, 0.03))], 0.0045, 6, 2,
                        il.mat("Twine"), (True, True), 1, True, 60))
up = V((0, 0, 1))
parts.append(il.wrap_slab("tag", il.plane_map(tag_c, t, up, -0.002, 0.004), 0.05, 0.062, 3, 4, "Parchment", 4.0,
                          0.002, 3))
parts.append(il.wrap_prism("tagflame", il.flame_pts(0.026, 0.036), il.plane_map(tag_c - up * 0.003, t, up, 0.0018,
                                                                                  0.003), "TonicRed"))

jar = rw.join(parts, "EmberEssence")
il.finish_item(ASSET, (0.19, 0.19, 0.3))
