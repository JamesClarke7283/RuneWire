"""vm_staff: first-person spell focus, a short gnarled wand.

Nodes (origin = grip centre; the crystal points -Y):
  Staff    a twisty, knobbly dark-wood wand (M_WoodDark) held like a sword, angled forward and up, with
           a leather grip wrap, brass ferrules, a brass pommel and a brass claw setting holding a violet
           crystal head (M_Crystal__a066ff) with two small side shards; a few glowing rune rings
           float around the wood.
  Glove    the shared cartoon leather glove wrapped around the wand (glove.py), wrist toward +Y.
  Emitter  empty at the crystal tip.
"""
import math
import os
import sys

from mathutils import noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

CRYSTAL = "M_Crystal__a066ff"
pl.tint_emission(CRYSTAL, "a066ff", 1.6)

# The wand axis runs from the pommel (behind/below the hand) through the grip to the head (in front/up).
TILT = 32.0                                       # degrees up from -Y
AX = V((0, -math.cos(math.radians(TILT)), math.sin(math.radians(TILT))))
L_BACK, L_FRONT = 0.085, 0.35                     # wand extent behind / in front of the grip centre
parts = []

# --- gnarled shaft: a sausage along a wobbly path with knots ----------------------------------------------
side = V((1, 0, 0))
upv = AX.cross(side).normalized()
pts, rad = [], []
N = 12
for i in range(N + 1):
    t = i / N
    d = -L_BACK + (L_BACK + L_FRONT - 0.06) * t
    w = noise.noise_vector(V((t * 3.1, 1.7, 0.3)))
    wob = side * (w.x * 0.012) + upv * (w.y * 0.012) if 0.12 < t < 0.97 else V((0, 0, 0))
    pts.append(AX * d + wob)
    r = 0.027 + 0.005 * math.sin(t * 9.0) - 0.004 * t
    rad.append(r)
shaft = pl.sausage("shaft", pts, rad, 10, 3, "M_WoodDark", (True, True), 2, True, 50)
parts.append(shaft)
# knots: little knobbly bumps along the shaft
for (t, ang, s) in ((0.48, 40, 1.0), (0.62, 200, 0.85), (0.78, 110, 0.9), (0.3, 290, 0.7)):
    d = -L_BACK + (L_BACK + L_FRONT) * t
    nrm = (side * math.cos(math.radians(ang)) + upv * math.sin(math.radians(ang)))
    parts.append(rw.sphere("knot", 0.016 * s, 8, 5, tuple(AX * d + nrm * 0.023), scale=(1, 1, 1), mat="M_WoodDark"))
# a little twig stub with a leaf-shaped crystal bud
tw0 = AX * 0.17 + upv * 0.015
tw1 = tw0 + (upv * 0.8 + AX * 0.6 + side * 0.25).normalized() * 0.05
parts.append(pl.capsule("twig", tw0, tw1, 0.0085, 6, 2, "M_WoodDark"))
parts.append(pl.crystal("bud", tw1 - (tw1 - tw0).normalized() * 0.004, tw1 - tw0, 0.03, 0.009, 5, 0.45, 0.15,
                        CRYSTAL))

# --- grip wrap, ferrules and pommel -----------------------------------------------------------------------
parts.append(pl.lathe_axis("wrap", [(0.031, -0.075), (0.033, -0.06), (0.033, 0.06), (0.031, 0.075)], AX, (0, 0, 0), 14,
                           "M_Leather__4a2a17", False, False, 50))
for (d, w) in ((-0.08, 0.02), (0.085, 0.022), (L_FRONT - 0.095, 0.026)):
    parts.append(pl.band("ferrule", 0.036 if d < L_FRONT - 0.1 else 0.033, w, 0.016, AX, AX * d, "M_Brass", 16, 0.0))
pommel = pl.lathe_axis("pommel", [(0.0, -0.028), (0.02, -0.025), (0.035, -0.012), (0.035, 0.006), (0.026, 0.016),
                                  (0.0, 0.016)], AX, AX * (-L_BACK - 0.012), 16, "M_Brass", False, False, 50)
parts.append(pommel)

# --- crystal head in a brass claw setting ------------------------------------------------------------------
HEAD = AX * (L_FRONT - 0.07)
parts.append(pl.lathe_axis("setting", [(0.028, -0.02), (0.04, -0.005), (0.048, 0.01), (0.044, 0.02), (0.0, 0.022)],
                           AX, HEAD, 16, "M_Brass", True, False, 45))
CL = 0.14
parts.append(pl.crystal("head", HEAD + AX * 0.004, AX, CL, 0.05, 6, 0.36, 0.12, CRYSTAL, 0))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = side * math.cos(a) + upv * math.sin(a)
    p0 = HEAD + d * 0.04 + AX * 0.012
    p1 = HEAD + d * 0.056 + AX * 0.05
    p2 = HEAD + d * 0.04 + AX * 0.08
    parts.append(pl.sausage("claw", [p0, p1, p2], [0.01, 0.009, 0.0075], 6, 3, "M_Brass", (True, True), 2, True, 60))
for (a, ln) in ((100, 0.05), (250, 0.045)):
    d = side * math.cos(math.radians(a)) + upv * math.sin(math.radians(a))
    parts.append(pl.crystal("shard", HEAD + d * 0.02 + AX * 0.012, (AX * 0.8 + d * 0.6).normalized(), ln, 0.014, 5,
                            0.4, 0.12, CRYSTAL, 20))
TIP = HEAD + AX * (0.004 + CL)

# --- floating glowing rune rings around the upper shaft ----------------------------------------------------
for (d, r) in ((0.19, 0.052), (0.235, 0.045)):
    ring = rw.torus("runering", r, 0.0075, 24, 6, (0, 0, 0), mat="M_RuneGlow")
    pl.align(ring, AX, AX * d)
    parts.append(ring)

staff = rw.join(parts, "Staff", origin=(0, 0, 0))
rw.smooth(staff, 50)

# --- glove: a hammer grip around the wand axis, fingers wrapping from below ----------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Emitter", tuple(TIP))
pl.check("vm_staff", (0, 0, 0))
rw.finish("vm_staff", "weapons", icon=True)
