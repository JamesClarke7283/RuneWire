"""item_shock_jar: "Lightning Jar", a glass jar of crackling cyan lightning, about 0.19 x 0.19 x 0.28 m.

A chunky round-shouldered glass jar (M_Glass) with a ribbed brass screw cap carrying two brass electrode posts
with ball tops and a crackling arc between them, a copper coil wound round the jar's foot between two copper
rings, and inside a glowing white-cyan core orb throwing chunky zig-zag cyan lightning bolts (rw.glow) out to
the glass. One mesh object "ShockJar", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_shock_jar"
rw.reset()

BRASS = pk.mat("M_Brass")
COPPER = pk.mat("M_Copper")
BOLT = pk.mat("ShockCyan")
CORE = pk.mat("ShockCore")
rnd = random.Random(12)

body = [(0.0, 0.0), (0.072, 0.0), (0.086, 0.012), (0.089, 0.045), (0.089, 0.158), (0.081, 0.182), (0.063, 0.196),
        (0.058, 0.206)]
prof = il.curve_profile(body, 2) + [(0.06, 0.208), (0.0, 0.208)]
parts = [il.lathe("jar", prof, segs=26, m="M_Glass", smooth=60)]
rfun = lambda z: il.prof_radius(prof, z)  # noqa: E731
for (ang, zc, w, h) in ((-62, 0.11, 0.016, 0.08), (-50, 0.172, 0.012, 0.02)):
    parts.append(il.wrap_prism("shine", il.capsule_pts(w, h), il.lathe_map(rfun, ang, zc, 0.0016, 0.0015), "Shine"))

# copper coil round the lower half, with terminal tabs
parts.append(pl.helix("coil", 0.094, 0.0058, 2.5, 0.036, (0, 0, 0.016), (0, 0, 1), 12, 6, COPPER, 0.0, res=1))
for z in (0.012, 0.058):
    parts.append(pl.band("coil_ring", 0.097, 0.012, 0.008, (0, 0, 1), (0, 0, z), COPPER, 24, 0.0))

# ribbed brass screw cap with two electrode posts
cap = [(0.0, 0.194), (0.066, 0.194), (0.07, 0.198), (0.07, 0.232), (0.066, 0.236), (0.05, 0.24), (0.0, 0.24)]
cp = il.lathe("cap", cap, segs=24, m=BRASS, smooth=30)


def ribs(p):
    r = math.hypot(p.x, p.y)
    if r < 0.065 or p.z > 0.233 or p.z < 0.197:
        return p
    a = math.atan2(p.y, p.x)
    f = 1.0 + 0.045 * (1 if math.cos(12 * a) > 0 else -0.2)
    return V((p.x * f, p.y * f, p.z))


pk.deform(cp, ribs)
parts.append(cp)
POSTS = (V((-0.03, -0.01, 0.24)), V((0.03, 0.01, 0.24)))
for p in POSTS:
    parts.append(il.lathe("post", [(0.0, 0.0), (0.012, 0.0), (0.012, 0.006), (0.006, 0.01), (0.006, 0.034),
                                   (0.0, 0.034)], loc=tuple(p), segs=10, m=BRASS, smooth=40))
    parts.append(rw.sphere("ball", 0.012, 10, 6, tuple(p + V((0, 0, 0.04))), mat=BRASS))


def zigzag(a, b, n, amp, seed):
    r = random.Random(seed)
    a, b = V(a), V(b)
    d = (b - a)
    side = d.cross(V((0, 0, 1)))
    if side.length < 1e-6:
        side = V((1, 0, 0))
    side.normalize()
    up = d.cross(side).normalized()
    pts = [a]
    for i in range(1, n):
        t = i / n
        off = (amp if i % 2 else -amp) * r.uniform(0.6, 1.0)
        pts.append(a + d * t + side * off + up * r.uniform(-amp, amp) * 0.4)
    pts.append(b)
    return pts


# a crackling arc between the electrode balls
view = V((math.sin(math.radians(-36)), -math.cos(math.radians(-36)), 0.35)).normalized()   # face the 3/4 view
pa, pb = POSTS[0] + V((0.006, 0.002, 0.042)), POSTS[1] + V((-0.006, -0.002, 0.042))
parts.append(pl.sausage("arc", zigzag(pa + V((0, 0, 0.004)), pb + V((0, 0, 0.004)), 5, 0.011, 3), 0.0055, 5, 1, BOLT,
                        (True, True), 1, False, 30))


def bolt(center, up_dir, h, thick=0.009):
    """Flat cartoon lightning bolt (itemlib.bolt_pts) standing at center, its long axis along up_dir, facing the view."""
    u = V(up_dir).normalized()
    x = u.cross(view).normalized()
    return il.wrap_prism("bolt", il.bolt_pts(h), il.plane_map(center, x, u, -thick / 2, thick), BOLT, 30)


# the glowing core and chunky lightning bolts crackling out from it to the glass
C = V((0, 0, 0.11))
parts.append(rw.sphere("core", 0.027, 12, 7, tuple(C), mat=CORE))
right = V((0, 0, 1)).cross(view).normalized()           # screen-plane axes as seen from the 3/4 view
upv = view.cross(right).normalized()
for (t, h) in ((40, 0.078), (150, 0.074), (235, 0.07), (315, 0.07)):
    d = right * math.cos(math.radians(t)) + upv * math.sin(math.radians(t))
    parts.append(bolt(C + d * (0.022 + h * 0.4), d, h, 0.011))

jar = rw.join(parts, "ShockJar")
pk.fit(jar, 0.28)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.28,), glass_alpha=0.12)
