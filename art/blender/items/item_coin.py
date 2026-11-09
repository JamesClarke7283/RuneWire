"""item_coin: gold coin pickup, 0.25 m across x 0.04 m thick (oversized so it reads at a distance).

A chunky coin standing upright, its faces looking along Blender Y (front = -Y): a fat rounded rim, a
recessed field, and on each face a raised gear ring around a rune (algiz on the front, sowilo on the
back), with four little bead dots between the ring and the rim. Everything is
rw.flat("Gold", "ffc93c", 0.3, 1.0). One mesh object "Coin", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_coin"
rw.reset()
GOLD = "Gold"

R, T = 0.125, 0.04
FIELD = 0.0125                     # half-thickness at the recessed field
# rim: inner slope from the field up to a flat top, then a fat rounded outer edge
prof = [(0.0, -FIELD), (0.092, -FIELD), (0.099, -0.02), (0.111, -0.02), (0.119, -0.0185), (0.1238, -0.0145),
        (0.125, -0.008), (0.125, 0.008), (0.1238, 0.0145), (0.119, 0.0185), (0.111, 0.02), (0.099, 0.02),
        (0.092, FIELD), (0.0, FIELD)]
parts = [il.lathe("coin", prof, (0, 1, 0), (0, 0, 0), 40, GOLD, smooth=45)]

for side, key in ((-1, "algiz"), (1, "sowilo")):
    n = V((0, side, 0))
    u = V((-side, 0, 0))           # reads left-to-right from whichever side you look at
    up = V((0, 0, 1))
    # raised gear ring (half sunk into the field: 6 mm proud)
    parts.append(il.gear("ring", 0.08, 12, 0.014, 0.012, 0.054, tuple(n * FIELD), tuple(n), GOLD, spin=7.5))
    # rune in the middle
    parts += pl.glyph(key, n * FIELD, u, up, 0.07, 0.017, 0.014, il.M(GOLD), "rune")
    # four bead dots on the diagonals between the ring and the rim
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p = u * (math.cos(a) * 0.0865) + up * (math.sin(a) * 0.0865) + n * FIELD
        parts.append(pl.rivet(p, n, 0.0075, 0.005, il.M(GOLD), 6, "bead", 0.6))

coin = rw.join(parts, "Coin")
rw.smooth(coin, 40)
il.finish_item(ASSET, (0.25, 0.04, 0.25))
