"""item_focus_incense: "Arcane Incense", a little brass censer with violet smoke, about 0.17 x 0.17 x 0.29 m.

A small round brass censer (M_Brass) standing on three curled feet: a bowl with a rolled rim and a band of
violet glowing rune slots, a domed lid pierced with glowing holes and a little finial, and rising from it a
column of stylised, solid violet smoke (rw.glow a066ff): a bulging S-shaped plume that splits at the top into two
spiral curls, with a couple of small puffs drifting off. One mesh object "FocusIncense", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_focus_incense"
rw.reset()

BRASS = pk.mat("M_Brass")
SMOKE = pk.glow("IncenseSmoke", "a066ff", 2.0)
SMOKE_LT = pk.glow("IncenseSmokeLight", "c8a6ff", 2.0)

# bowl: from the foot up to a rolled rim
bowl = [(0.0, 0.03), (0.03, 0.03), (0.056, 0.038), (0.07, 0.054), (0.074, 0.074), (0.072, 0.088), (0.078, 0.092),
        (0.078, 0.098), (0.07, 0.1), (0.0, 0.1)]
parts = [il.lathe("bowl", bowl, segs=24, m=BRASS, smooth=40)]
# glowing rune slots round the bowl
for k in range(6):
    a = 2 * math.pi * k / 6 + math.radians(-24)
    d = V((math.sin(a), -math.cos(a), 0))
    p = d * 0.0735 + V((0, 0, 0.068))
    parts.append(pl.obox("slot", (0.009, 0.006, 0.02), p, d.cross(V((0, 0, 1))), d, SMOKE))
# three curled feet
for k in range(3):
    a = 2 * math.pi * k / 3 + math.radians(-24 + 60)
    d = V((math.sin(a), -math.cos(a), 0))
    foot = [d * 0.04 + V((0, 0, 0.036)), d * 0.066 + V((0, 0, 0.024)), d * 0.075 + V((0, 0, 0.006)),
            d * 0.084 + V((0, 0, 0.004))]
    parts.append(pl.sausage("foot", foot, [0.0105, 0.0095, 0.009, 0.0095], 6, 2, BRASS, (True, False), 1, True, 50))
    parts.append(rw.sphere("toe", 0.0115, 8, 5, tuple(d * 0.088 + V((0, 0, 0.007))), mat=BRASS))

# pierced domed lid with a finial
lid = [(0.0, 0.098), (0.074, 0.098), (0.074, 0.104), (0.066, 0.112), (0.05, 0.128), (0.03, 0.14), (0.016, 0.144),
       (0.0, 0.145)]
parts.append(il.lathe("lid", lid, segs=24, m=BRASS, smooth=40))
for k in range(6):
    a = 2 * math.pi * k / 6 + math.radians(-24)
    d = V((math.sin(a), -math.cos(a), 0))
    p = d * 0.052 + V((0, 0, 0.129))
    nrm = (d * 0.6 + V((0, 0, 1))).normalized()
    parts.append(pl.disc("hole", 0.0085, 0.004, tuple(nrm), tuple(p), SMOKE, 6, 0.0))
parts.append(il.lathe("finial", [(0.0, 0.142), (0.014, 0.142), (0.016, 0.148), (0.01, 0.154), (0.012, 0.162),
                                 (0.006, 0.17), (0.0, 0.172)], segs=10, m=BRASS, smooth=40))

# the smoke: a bulging S-shaped plume (in the screen plane of the 3/4 view) that splits into two spiral curls
view = V((math.sin(math.radians(-38)), -math.cos(math.radians(-38)), 0.0)).normalized()
rt = V((0, 0, 1)).cross(view).normalized() * -1          # screen right


def P(x, z, y=0.0):
    return rt * x + view * y + V((0, 0, z))


plume = [P(0.0, 0.166), P(-0.014, 0.19), P(0.0, 0.212), P(0.016, 0.232), P(0.004, 0.252)]
parts.append(pl.sausage("smoke", plume, [0.011, 0.019, 0.016, 0.02, 0.017], 10, 3, SMOKE, (True, False), 2, True,
                        70))


top = plume[-1]
for (sign, r0, rad0, m) in ((-1, 0.024, 0.016, SMOKE), (1, 0.019, 0.013, SMOKE_LT)):
    c = top + rt * (sign * r0) + V((0, 0, 0.012))
    pts = [top]
    n = 10
    for i in range(1, n + 1):
        t = i / n
        ang = math.radians(180 - 330 * t) if sign > 0 else math.radians(330 * t)   # sweep up and over, inward
        r = r0 * (1 - 0.62 * t)
        pts.append(c + rt * (r * math.cos(ang)) + V((0, 0, r * math.sin(ang))))
    radii = [rad0 * (1 - 0.6 * i / n) + 0.003 for i in range(n + 1)]
    parts.append(pl.sausage("smoke_curl", pts, radii, 10, 2, m, (False, True), 2, True, 70))
for (x, z, r) in ((0.036, 0.205, 0.0115), (-0.04, 0.24, 0.009)):
    parts.append(rw.sphere("puff", r, 10, 6, tuple(P(x, z)), mat=SMOKE_LT))

censer = rw.join(parts, "FocusIncense")
pk.fit(censer, 0.29)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.29,))
