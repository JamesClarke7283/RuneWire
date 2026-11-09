"""item_ley_key: ornate brass ley key, about 0.35 m long, lying along Blender X (broad faces look along Y).

An ornate brass bow ring at -X with three ball lobes (a trefoil), a faceted teal ley crystal (M_Crystal) set
in its middle with four brass prongs, a double collar, a squared brass shaft with glowing teal rune
engravings on both faces (rw.glow), and a chunky toothed bit hanging down at the +X end with a ball tip.
One mesh object "LeyKey", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_ley_key"
rw.reset()

brass = il.mat("M_Brass")
BX = -0.115                                   # bow ring centre (x)
parts = []
# bow: ring, trefoil balls, crystal with prongs
parts.append(rw.torus("bow", 0.044, 0.0135, 24, 6, (BX, 0, 0), (90, 0, 0), brass))
for a in (90, 180, 270):
    d = V((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
    parts.append(rw.sphere("lobe", 0.019, 10, 6, tuple(V((BX, 0, 0)) + d * 0.06), mat="M_Brass"))
parts.append(rw.ico("gem", 0.031, 1, (BX, 0, 0), (0, 0, 0), (1.0, 0.62, 1.15), "M_Crystal", None, 0))
for k in range(4):
    a = math.radians(45 + 90 * k)
    for sy in (-1, 1):
        n = V((0, sy, 0))
        parts.append(pl.rivet(V((BX + math.cos(a) * 0.03, sy * 0.012, math.sin(a) * 0.03)), n, 0.0075, 0.006, brass, 6))
# collars
for x in (-0.062, -0.047):
    parts.append(pl.band("collar", 0.024, 0.011, 0.012, (1, 0, 0), (x, 0, 0), brass, 14, 0.4))
# shaft with rune engravings on both faces
SX0, SX1 = -0.07, 0.135
parts.append(pl.obox("shaft", (SX1 - SX0, 0.03, 0.036), ((SX0 + SX1) / 2, 0, 0), rounded=0.008, segments=2, mat=brass))
glow = il.mat("RuneTeal")
for sy, keys in ((-1, ("kenaz", "tiwaz", "sowilo")), (1, ("algiz", "ingwaz", "fehu"))):
    for i, k in enumerate(keys):
        x = -0.03 + 0.042 * i
        parts += pl.glyph(k, V((x, sy * 0.015, 0)), (-sy, 0, 0), (0, 0, 1), 0.026, 0.0065, 0.005, glow, "rune")
# bit: toothed plate hanging down at the +X end, and a ball tip
bit = [(0.0, 0.0), (0.0, -0.05), (0.016, -0.05), (0.016, -0.068), (0.034, -0.068), (0.034, -0.084), (0.052, -0.084),
       (0.052, -0.058), (0.064, -0.058), (0.064, 0.0)]
bit = [(x + 0.062, y + 0.006) for (x, y) in bit]
parts.append(il.wrap_prism("bit", bit, il.plane_map((0, 0, 0), (1, 0, 0), (0, 0, 1), -0.013, 0.026), brass, 30))
rw.add_bevel(parts[-1], 0.004, 1, 40, harden=False)
parts.append(rw.sphere("tip", 0.021, 12, 8, (SX1 + 0.004, 0, 0), mat="M_Brass"))

key = rw.join(parts, "LeyKey")
rw.smooth(key, 35)
il.finish_item(ASSET, (0.35, 0.05, 0.16))
