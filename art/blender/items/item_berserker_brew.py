"""item_berserker_brew: a wooden tankard of frothing fiery-red brew, about 0.26 x 0.19 x 0.30 m.

A chunky stave tankard (M_WoodPlanks staves, a dark wood base and rim) bound by three iron hoops
(M_DarkMetal) with a stout wooden handle on its right, a round iron badge on the front bearing a glowing
red flame, and a heaped head of peach-and-cream foam frothing up over the rim and slopping down one side,
with fat drips of glowing fiery-red brew (rw.glow) running down the staves and embers popping out of it.
One mesh object "BerserkerBrew", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_berserker_brew"
rw.reset()

IRON = pk.mat("M_DarkMetal")
brew = pk.glow("BrewRed", "ff3a1a", 1.2)
ember = pk.glow("BrewEmber", "ffb030", 1.6)
pk.flat("FoamFire", "ffac6e", 0.8, 0.0)
pk.flat("FoamLight", "fff0cf", 0.8, 0.0)
rnd = random.Random(4)

R0, R1, H = 0.088, 0.08, 0.205                       # radius at the base / top, height of the staves


def rfun(z):
    return R0 + (R1 - R0) * (z / H) + 0.004 * math.sin(math.pi * z / H)


parts = [pl.stave_surface("staves", 12, 0.012, H, rfun, 5, 0.006, 0.003, pk.mat("M_WoodPlanks"))]
# dark wood base (with a foot ring) and the inside wall at the top
parts.append(il.lathe("base", [(0.0, 0.0), (R0 + 0.006, 0.0), (R0 + 0.008, 0.006), (R0 + 0.004, 0.016),
                               (0.0, 0.016)], segs=20, m="M_WoodDark", smooth=40))
parts.append(il.lathe("rim", [(R1 - 0.012, H - 0.03), (R1 - 0.008, H + 0.002), (R1 + 0.004, H + 0.004),
                              (R1 + 0.004, H - 0.002)], segs=20, m="M_WoodDark", smooth=40))
# iron hoops
for z in (0.032, 0.105, 0.178):
    parts.append(pl.band("hoop", rfun(z) + 0.008, 0.02, 0.012, (0, 0, 1), (0, 0, z), IRON, 20, 0.0))
    if z != 0.032:
        continue
    for k in range(4):
        a = math.radians(-155 + 52 * k)
        d = V((math.cos(a), math.sin(a), 0))
        parts.append(pl.rivet(d * (rfun(z) + 0.008) + V((0, 0, z)), d, 0.006, 0.0045, IRON, 5))

# handle on the right (+X): a fat wooden D with iron caps where it meets the hoops
hp = [V((rfun(0.168) - 0.004, 0, 0.168)), V((0.13, 0, 0.176)), V((0.155, 0, 0.13)), V((0.148, 0, 0.07)),
      V((rfun(0.06) - 0.004, 0, 0.055))]
parts.append(pl.sausage("handle", hp, 0.017, 8, 2, pk.mat("M_WoodDark"), (True, True), 2, True, 50, (1.0, 0.75),
                        (0, 1, 0)))
parts.append(pl.rivet(V((0.118, 0, 0.18)), (0, 0, 1), 0.012, 0.009, IRON, 8))        # thumb rest

# round iron badge on the front with a glowing flame
ang = -26
d = V((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0))
bc = d * (rfun(0.142) + 0.004) + V((0, 0, 0.142))
parts.append(pl.disc("badge", 0.032, 0.008, tuple(d), tuple(bc), IRON, 12, 0.35))
parts.append(il.wrap_prism("flame", il.flame_pts(0.03, 0.04), il.plane_map(bc + d * 0.004 + V((0, 0, 0.001)),
                                                                           d.cross(V((0, 0, 1))) * -1, (0, 0, 1),
                                                                           0.0, 0.004), brew))

# the foam head: heaped puffs over the rim
puffs = [((0, 0, H + 0.03), 0.074)]
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.5
    puffs.append(((0.062 * math.cos(a), 0.062 * math.sin(a), H + 0.014 + rnd.uniform(-0.004, 0.006)),
                  rnd.uniform(0.04, 0.046)))
puffs.append(((-0.012, -0.01, H + 0.072), 0.04))
for i, (p, r) in enumerate(puffs):
    parts.append(rw.sphere("foam", r, 10, 6, p, (0, 0, rnd.uniform(0, 90)), (1, 1, 0.8),
                           pk.mat("FoamLight" if i % 2 == 0 else "FoamFire")))
# fiery-red brew welling over the rim under the foam, dripping down the staves
RB = rfun(H) + 0.006
ring = [V((RB * (1 + 0.04 * math.sin(3 * t + 0.5)) * math.cos(t), RB * (1 + 0.04 * math.sin(3 * t + 0.5)) * math.sin(t),
           H - 0.002 + 0.004 * math.sin(5 * t))) for t in (2 * math.pi * i / 20 for i in range(20))]
parts.append(pk.loop_tube("brew_rim", ring, 0.0105, 6, brew))
for (a, L, r) in ((-122, 0.062, 0.013), (-78, 0.036, 0.011), (-20, 0.05, 0.012), (150, 0.045, 0.012)):
    t = math.radians(a)
    d = V((math.cos(t), math.sin(t), 0))
    top = d * (rfun(H - 0.01) + r * 0.55) + V((0, 0, H - 0.004))
    pts = [top, top + V((0, 0, -L * 0.6)) - d * 0.001, top + V((0, 0, -L))]
    parts.append(pl.sausage("drip", pts, [r * 0.85, r * 0.75, r], 8, 1, brew, (False, True), 2, True, 60))
# embers popping out of the foam
for p in ((0.036, -0.05, H + 0.105), (-0.052, -0.026, H + 0.088)):
    parts.append(rw.ico("ember", 0.0095, 1, p, (0, 0, 0), (1, 1, 1), ember, None, 0))

mug = rw.join(parts, "BerserkerBrew")
pk.fit(mug, 0.30)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.30,))
