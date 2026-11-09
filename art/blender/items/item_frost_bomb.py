"""item_frost_bomb: "Rime Bomb", a round icy-blue bomb furred with frost crystals, about 0.21 x 0.18 x 0.27 m.

A pale icy-blue metal ball (flat FrostShell) strapped with silver bands (equator and over the top, riveted),
a round silver-rimmed core window on the front glowing frost-blue (rw.glow) with a white snowflake in it, a snowy
frost cap with icicle drips over its top, clusters of chunky ice crystals (M_Crystal__aee8ff) growing out of
the shell, and a silver fuse cap on top with a short
frozen fuse fizzing with a cold blue-white spark. One mesh object "FrostBomb", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_frost_bomb"
rw.reset()

SILVER = pk.mat("Silver")
SHELL = pk.flat("FrostShell", "52b4f2", 0.3, 0.0)
CORE = pk.mat("FrostGlow")
ICE = "M_Crystal__aee8ff"
pl.tint_emission(ICE, "aee8ff", 0.35)               # previews: let the ice glow its own pale tint
SNOW = pk.mat("Snow")

R = 0.086
parts = [rw.sphere("ball", R, 20, 10, (0, 0, 0), mat=SHELL)]
# a snowy frost cap over the top, its edge hanging in icicle drips


def drips(p):
    r = math.hypot(p.x, p.y)
    if r < 1e-6 or p.z > R * 0.74:
        return p
    a = math.atan2(p.y, p.x)
    k = pk.smoothstep(R * 0.74, R * 0.56, p.z)
    return V((p.x, p.y, p.z - k * 0.016 * max(0.0, math.cos(7 * a)) ** 3))


cap_prof = [(math.sqrt(max(0.0, (R + 0.004) ** 2 - z * z)), z) for z in (R * 0.56, R * 0.68, R * 0.8, R * 0.9)]
cap_prof = [(cap_prof[0][0] - 0.004, R * 0.56)] + cap_prof + [(0.03, R + 0.002), (0.0, R + 0.004)]
snow = il.lathe("frost", cap_prof, segs=28, m=pk.mat("Snow"), smooth=60)
pk.deform(snow, drips)
parts.append(snow)
# silver bands, riveted
parts.append(pl.band("equator", R + 0.007, 0.024, 0.013, (0, 0, 1), (0, 0, 0), SILVER, 22, 0.0))
parts.append(pl.band("over", R + 0.007, 0.022, 0.013, (1, 0, 0), (0, 0, 0), SILVER, 22, 0.0))
for a in (35, 145, 215, 325):
    t = math.radians(a)
    d = V((math.cos(t), math.sin(t), 0))
    parts.append(pl.rivet(d * (R + 0.007), d, 0.0085, 0.006, SILVER, 5))

# core window on the front: silver bezel, glowing frost lens, white snowflake
el = math.radians(16)
az = math.radians(-24)
d = V((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
c = d * (R - 0.003)
bez = rw.torus("bezel", 0.036, 0.0095, 18, 6, (0, 0, 0), mat=SILVER)
pl.align(bez, d, c + d * 0.004)
parts.append(bez)
lens = rw.sphere("lens", 0.033, 16, 8, (0, 0, 0), (0, 0, 0), (1, 1, 0.45), CORE)
pl.align(lens, d, c + d * 0.003)
parts.append(lens)
u = d.cross(V((0, 0, 1))).normalized()
v = u.cross(d).normalized() * -1
for k in range(3):
    a = math.radians(90 + 60 * k)
    ax = u * math.cos(a) + v * math.sin(a)
    parts.append(pl.obox("flake", (0.044, 0.0055, 0.004), c + d * 0.017, ax, d, SNOW))
    for s_ in (-1, 1):
        tip = c + d * 0.0172 + ax * (s_ * 0.013)
        for side in (-1, 1):
            br = ax * s_ * 0.7 + (d.cross(ax)) * side * 0.7
            parts.append(pl.obox("flake_twig", (0.012, 0.004, 0.0035), tip + br.normalized() * 0.005, br, d, SNOW))

# ice crystals growing out of the shell
CLUSTERS = (((-110, 35), [(0.0, 0.07, 0.016), (25, 0.052, 0.012), (-30, 0.048, 0.012)]),
            ((60, 10), [(0.0, 0.062, 0.014), (35, 0.046, 0.011), (-20, 0.04, 0.01)]),
            ((-60, -45), [(0.0, 0.05, 0.013), (30, 0.04, 0.01)]),
            ((150, 40), [(0.0, 0.055, 0.013), (-30, 0.042, 0.011)]))
for (azd, eld), specs in CLUSTERS:
    a, e = math.radians(azd), math.radians(eld)
    n = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    base = n * (R - 0.004)
    t1 = n.orthogonal().normalized()
    out = []
    for i, (tilt, L, r) in enumerate(specs):
        rot = il.Matrix.Rotation(math.radians(tilt), 3, n.cross(t1).normalized() if i % 2 else t1)
        out.append((rot @ n, L, r, 15 * i))
    parts += il.crystal_cluster(base, out, ICE, 6)

# silver fuse cap on top, a short frozen fuse and a cold spark
parts.append(il.lathe("cap", [(0.0, R - 0.02), (0.033, R - 0.02), (0.035, R - 0.004), (0.03, R + 0.01),
                               (0.022, R + 0.014), (0.022, R + 0.022), (0.027, R + 0.025), (0.027, R + 0.034),
                               (0.0, R + 0.034)], segs=14, m=SILVER, smooth=40))
fuse = [V((0, 0, R + 0.025)), V((0.004, -0.002, R + 0.046)), V((-0.008, -0.006, R + 0.062)),
        V((-0.022, -0.01, R + 0.07))]
parts.append(pl.sausage("fuse", fuse, [0.0095, 0.009, 0.0085, 0.008], 8, 2, pk.mat("FrostFuse"), (False, True), 2,
                        True, 60))
parts += il.spark("spark", fuse[-1] + V((-0.012, -0.004, 0.008)), 0.03, 8, pk.mat("FrostGlow"), 5, pk.mat("ShockCore"))

bomb = rw.join(parts, "FrostBomb")
pk.fit(bomb, 0.27)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.27,))
