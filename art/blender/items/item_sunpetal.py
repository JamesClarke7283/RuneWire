"""item_sunpetal: a bright golden sunpetal flower, about 0.2 x 0.13 x 0.29 m, standing on a short stem.

A big flower head tilted up toward the viewer: eight broad, rounded, gently cupped golden-yellow petals with a soft
warm glow (emissive flat), eight smaller deeper-gold petals between them, and a domed orange centre dotted with
darker seeds, on a short curved green stem with two pointed leaves angling up and out from it. Petals and leaves
are smooth flattened pods (matlib.pod). The materials avoid the words leaf / petal / flower so the Godot importer
keeps them as glows instead of wind-swayed foliage. One mesh object "Sunpetal", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_sunpetal"
rw.reset()

parts = []
HEAD = V((0.0, -0.005, 0.19))                   # centre of the flower head
F = V((-0.12, -0.75, 0.62)).normalized()        # the way the flower faces
U = F.orthogonal().normalized()
W = F.cross(U).normalized()

# stem: from the base up to the back of the head, with a little curve
stem = [V((0.008, 0.02, 0.0)), V((0.014, 0.025, 0.06)), V((0.006, 0.022, 0.12)), HEAD - F * 0.02]
parts.append(pl.sausage("stem", stem, [0.012, 0.0115, 0.011, 0.01], 8, 4, ml.mat("SunGreen"), (True, True), 2, True,
                        60))


def obovate(xn):
    """Petal outline: narrow at the base (xn = -1), broad and round toward the tip."""
    return 0.55 + 0.45 * (xn + 1) / 2 + 0.15 * math.sin(math.pi * (xn + 1) / 2)


def ovate(xn):
    """Leaf outline: broad and round at the base (xn = -1), tapering straight to a point at the tip."""
    return 1.3 * math.sqrt(max(0.0, (1 - xn) / 2))


# two broad leaves angling up and out from the lower stem, their faces turned toward the viewer
CAM = V((-0.5, -0.75, 0.45)).normalized()
for (t, side, L, Wd) in ((0.3, (-1.0, -0.25, 0.55), 0.11, 0.06), (0.12, (1.0, -0.4, 0.38), 0.105, 0.056)):
    p0 = stem[1].lerp(stem[2], t) if t > 0.33 else stem[0].lerp(stem[1], t * 3)
    d = V(side).normalized()
    parts.append(ml.pod("blade", p0 + d * (L * 0.48), d, CAM, L, Wd, 0.013, "SunGreen", 12, 6, ovate, None, 0.0, 0.05))


def petal(ang, r0, L, Wd, T, m, lift, segs, rings):
    d = U * math.cos(ang) + W * math.sin(ang)
    centre = HEAD + d * (r0 + L / 2) + F * lift
    return ml.pod("petal", centre, d + F * 0.18, F, L, Wd, T, m, segs, rings, obovate, None, 0.05)


for k in range(8):                      # broad front petals
    parts.append(petal(math.radians(45 * k + 8), 0.02, 0.085, 0.058, 0.012, "SunGold", 0.004, 12, 6))
for k in range(8):                      # deeper-gold petals tucked behind, between them
    parts.append(petal(math.radians(45 * k + 30.5), 0.018, 0.074, 0.048, 0.01, "SunGoldDeep", -0.006, 10, 5))

# domed orange centre with darker seeds
core = [(0.034, -0.01), (0.036, 0.002), (0.032, 0.012), (0.021, 0.019), (0.0, 0.022)]
core_o = il.lathe("core", core, F, HEAD, 18, ml.mat("SunCore"), 60)
parts.append(core_o)
for (rr, n, ph) in ((0.0, 1, 0.0), (0.0125, 5, 0.0), (0.024, 8, 18.0)):
    for k in range(n):
        a = math.radians(ph + 360.0 * k / n)
        p, nrm = il.surface_hit(core_o, HEAD + (U * math.cos(a) + W * math.sin(a)) * rr + F * 0.05, -F)
        if p is not None:
            parts.append(rw.ico("seed", 0.0042, 1, tuple(p), (0, 0, 0), (1, 1, 1), ml.mat("SunCoreDot"), None, 70))

head = rw.join(parts, "Sunpetal")
il.finish_item(ASSET, (0.2, 0.13, 0.29))
