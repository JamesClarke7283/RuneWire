"""item_runesteel_ingot: one big dark runesteel ingot, about 0.3 x 0.13 x 0.08 m.

A single chunky trapezoid bar of dark steel (M_DarkMetal), bigger than the stacked copper / iron / brass ingots,
engraved along its top, both long slopes and both ends with glowing violet runes (rw.glow a066ff strokes inlaid
half-sunk into the faces). One mesh object "RunesteelIngot", origin at the centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_runesteel_ingot"
rw.reset()

GLOW = ml.mat("RuneViolet")
L, W, H, TOP = 0.3, 0.13, 0.078, (0.8, 0.64)
bar = ml.ingot("ingot", L, W, H, TOP, (0, 0, 0), 0.0, "M_DarkMetal", bevel=0.014, segs=2)
parts = [bar]


def rune(key, origin, direction, size, width=0.0085):
    """Glowing rune strokes inlaid (half-sunk) into the bar where a ray from `origin` hits it."""
    p, n = il.surface_hit(bar, origin, direction)
    u, v = il.face_frame(n)
    return pl.glyph(key, p, u, v, size, width, 0.005, GLOW)


for (x, key) in ((-0.07, "kenaz"), (0.0, "ingwaz"), (0.07, "algiz")):          # along the top
    parts += rune(key, (x, 0.0, 1.0), (0, 0, -1), 0.05)
for (x, key) in ((-0.09, "sowilo"), (-0.03, "tiwaz"), (0.03, "othala"), (0.09, "fehu")):   # front slope
    parts += rune(key, (x, -1.0, H * 0.5), (0, 1, 0), 0.042)
for (x, key) in ((-0.06, "eye"), (0.0, "hagal"), (0.06, "kenaz")):                         # back slope
    parts += rune(key, (x, 1.0, H * 0.5), (0, -1, 0), 0.042)
for (sx, key) in ((-1, "dagaz"), (1, "hagal")):                                   # both ends
    parts += rune(key, (sx * 1.0, 0.0, H * 0.48), (-sx, 0, 0), 0.04)

ingot = rw.join(parts, "RunesteelIngot")
ml.preview_metals()
il.finish_item(ASSET, (0.3, 0.13, 0.08))
