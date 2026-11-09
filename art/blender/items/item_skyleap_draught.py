"""item_skyleap_draught: a pale sky-blue teardrop flask with a feather, about 0.21 x 0.19 x 0.31 m.

A round-bottomed teardrop flask that tapers to a slim neck, its lower part full of softly glowing sky-blue
draught (glass M_Glass above it) with a white cloud on the front, a little softly glowing white cloud
floating inside the glass above the draught, a cork, and a big white feather (with a grey-blue quill) tied to the neck by a sky-blue
string that ends in a knot. White glints on the glass. One mesh object "SkyleapDraught", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_skyleap_draught"
rw.reset()

sky = pk.glow("SkyBlue", "3aa6ff", 0.8)
sky_top = pk.glow("SkyBlueTop", "c4ecff", 0.9)
WHITE = pk.mat("Cloud")

body = [(0.0, 0.0), (0.05, 0.002), (0.086, 0.026), (0.1, 0.066), (0.094, 0.106), (0.071, 0.144), (0.046, 0.173),
        (0.03, 0.198), (0.024, 0.22), (0.024, 0.232)]
lip = [(0.031, 0.236), (0.033, 0.245), (0.028, 0.249), (0.0, 0.249)]
b = il.Bottle(body, lip, fill=0.11, liquid=sky, top=sky_top, segs=24)
b.shine(-70, 0.13, 0.013, 0.05)
b.shine(-52, 0.04, 0.012, 0.03)
parts = list(b.parts)

# a white cloud on the front of the draught
M = b.map(-36, 0.079, 0.0015, 0.0045)
parts.append(pk.wrap_prism_fine("cloud_mark", pk.cloud_pts(0.092, 0.054), M, WHITE, 0.009))

# a little cloud floating inside the glass, above the draught
CLOUD_GLOW = pk.glow("CloudGlow", "ffffff", 0.7)       # a magic cloud: softly glowing white so it stays bright
for (p, s) in (((0.0, 0.0, 0.14), (0.072, 0.062, 0.052)), ((-0.034, -0.008, 0.129), (0.052, 0.045, 0.038)),
               ((0.034, 0.004, 0.13), (0.054, 0.045, 0.04)), ((0.006, -0.012, 0.161), (0.045, 0.04, 0.037))):
    parts.append(rw.sphere("cloud", 0.5, 12, 7, p, (0, 0, 0), s, CLOUD_GLOW))

parts.append(il.cork(0.222, 0.292, 0.02, 0.03, 14))

# sky-blue string round the neck with a knot at the front-left, where the feather is tied
STR = pk.mat("SkyString")
parts.append(rw.torus("string", 0.027, 0.0042, 16, 5, (0, 0, 0.212), mat=STR))
ka = math.radians(-60)
kd = V((math.sin(ka), -math.cos(ka), 0))
knot = kd * 0.031 + V((0, 0, 0.212))
parts.append(pk.knot("knot", knot, 0.009, STR, (1.1, 1.0, 1.0), 3, 8, 5))
for (dz, dx) in ((-0.03, 0.006), (-0.022, -0.01)):
    parts.append(pl.sausage("string_end", [knot, knot + kd * 0.006 + V((dx * 0.5, 0, dz * 0.5)),
                                           knot + kd * 0.008 + V((dx, 0, dz))], 0.0035, 5, 1, STR, (True, True), 1,
                            True, 60))

# the feather: a vane with two little notches and a quill, tied at the knot, sweeping up and out to the left
L, WR, WL = 0.15, 0.032, 0.027
vane = []
n = 12
for i in range(n + 1):                                   # right edge, base -> tip
    t = i / n
    w = WR * math.sin(math.pi * min(1.0, 0.1 + 0.95 * t)) ** 0.75
    if abs(t - 0.55) < 0.05:
        w *= 0.55                                        # notch
    vane.append((w, 0.03 + (L - 0.03) * t))
for i in range(n, -1, -1):                               # left edge, tip -> base
    t = i / n
    w = WL * math.sin(math.pi * min(1.0, 0.1 + 0.95 * t)) ** 0.75
    if abs(t - 0.38) < 0.05:
        w *= 0.5
    vane.append((-w, 0.03 + (L - 0.03) * t))
vane = [p for i, p in enumerate(vane) if i == 0 or (abs(p[0] - vane[i - 1][0]) + abs(p[1] - vane[i - 1][1])) > 1e-5]
feather = il.wrap_prism("feather", vane, il.plane_map((0, 0, 0), (1, 0, 0), (0, 1, 0), -0.003, 0.006),
                        pk.mat("Feather"), 30)
quill = pl.sausage("quill", [V((0, 0.0, 0.0)), V((0, 0.06, 0.0035)), V((0, L * 0.96, 0.002))], [0.0042, 0.0036, 0.0016],
                   6, 2, pk.mat("FeatherShade"), (True, True), 1, True, 60)
fe = rw.join([feather, quill], "feather", origin=(0, 0, 0))
# bend the feather (curl back along its length), then stand it up: local +Y -> up and out to the left


def bend(p):
    return V((p.x + 0.0015 * math.sin(40 * p.y), p.y, p.z + 1.6 * (p.y ** 2) * 0.35))


pk.deform(fe, bend)
up = V((-0.72, -0.12, 1.0)).normalized()
face = V((math.sin(math.radians(-40)), -math.cos(math.radians(-40)), 0.7)).normalized()   # tipped up to the light
xa = up.cross(face).normalized()
za = xa.cross(up).normalized()
R = il.Matrix((xa, up, za)).transposed().to_4x4()
pk.transform(fe, il.Matrix.Translation(knot + V((-0.004, -0.004, -0.004))) @ R)
parts.append(fe)

flask = rw.join(parts, "SkyleapDraught")
pk.fit(flask, 0.31)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.31,))
