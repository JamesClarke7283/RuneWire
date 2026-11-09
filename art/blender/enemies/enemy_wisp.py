"""enemy_wisp: mischievous flame spirit of the Hollow Choir (origin at the core centre, ~0.9 m tall).

Hierarchy (spec Batch B):
  Core            emissive orb (M_EmberGlow, r 0.35), origin = core centre = model origin
    Face          angry dark eyes with bright pupils, brows and a fanged grin on the -Y side
                  (origin at the core centre so it can be turned/tilted as a whole)
    Flame_0..3    teardrop flame shells rising from the core (origin at each flame's base bulb)
  Ember_0..2      small glowing coals on a 0.6 m orbit ring (origin at each coal's centre)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
from mathutils import Vector as V  # noqa: E402

ASSET = "enemy_wisp"
rw.reset()

R = 0.35
C = (0.0, 0.0, 0.0)
RR = (R, R, R)

# ---------------------------------------------------------------- materials
dark = rw.flat("WispDark", "2a0c1c", 0.5)
pupil = rw.glow("WispPupil", "ffe24a", 2.5)
fang = rw.flat("WispFang", "fff1d0", 0.4)
coal = rw.flat("Coal", "3a2420", 0.8)
ember = rw.glow("EmberHot", "ff6a1a", 2.0)
flame_cols = ["ff4410", "ff6a18", "ff7d1e", "ffb02a"]
flame_mats = [rw.glow("Flame%d" % i, c, 1.6) for i, c in enumerate(flame_cols)]
flame_inner = rw.glow("FlameInner", "ffd23c", 1.8)


def sp(az, el, out=0.0):
    """Point on the core surface: azimuth 0 = front (-Y), +az toward the wisp's left (+X)."""
    a, e = math.radians(az), math.radians(el)
    d = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    return d * (R + out), d


def lick(name, pts, r, mat, segs=16, flat=1.0):
    """Flame tongue: round base of radius r at pts[0] (buried in the core), concave taper along an
    S-curved path to a sharp tip."""
    pts = [V(p) for p in pts]
    path = cl.bezier(pts[0], pts[1], pts[2], 9, pts[3]) if len(pts) == 4 else cl.bezier(pts[0], pts[1], pts[2], 9)
    d = (path[1] - path[0]).normalized()
    cap = [path[0] - d * r * math.sin(math.pi / 2 * (1 - k / 3)) for k in range(3)]
    cap_r = [r * math.cos(math.pi / 2 * (1 - k / 3)) for k in range(3)]
    n = len(path)
    rad = [r * (1 - i / (n - 1)) ** 1.1 * (1 + 0.45 * math.sin(math.pi * 0.9 * i / (n - 1))) for i in range(n)]
    rad[-1] = 0.0
    return cl.sweep(name, cap + path, cap_r + rad, segs, mat, scale=(1.0, flat))


# ---------------------------------------------------------------- Core
core_parts = [cl.ellipsoid("core_orb", C, RR, 32, 16, "M_EmberGlow")]
# short trailing flame tail at the lower back so the orb reads as moving fire
core_parts.append(lick("core_tail", [(0, 0.12, -0.14), (0, 0.26, -0.3), (0, 0.4, -0.3), (0, 0.46, -0.16)], 0.15,
                       flame_mats[1]))
core = cl.node("Core", core_parts, C)

# ---------------------------------------------------------------- Face
face = []
for s in (1, -1):  # +1 = the wisp's left (+X)
    p, d = sp(22 * s, 2, -0.014)
    face.append(cl.ellipsoid("eye_socket", p, (0.082, 0.035, 0.08), 18, 10, dark,
                             cl.frame(d) @ cl.Matrix.Rotation(math.radians(-14 * s), 3, 'Y')))
    # bright pupil, pushed toward the nose and down for a glare
    pp, pd = sp(18 * s, -1, 0.012)
    face.append(cl.ellipsoid("eye_pupil", pp, (0.03, 0.016, 0.034), 10, 6, pupil, cl.frame(pd)))
    # angry brow: fat at the inner end, slashing down toward the nose over the eye top
    b_in, _ = sp(6 * s, 8, 0.008)
    b_mid, _ = sp(20 * s, 14, 0.016)
    b_out, _ = sp(38 * s, 17, 0.004)
    face.append(cl.sweep("brow", cl.bezier(b_in, b_mid, b_out, 7),
                         [0.04, 0.042, 0.04, 0.035, 0.028, 0.02, 0.01], 10, dark, scale=(1.0, 0.55), up=(0, 0, 1)))
# grin: corners up, fat in the middle
pts = []
for i in range(13):
    t = i / 12
    pts.append(sp(-40 + 80 * t, -19 + 13 * (2 * t - 1) ** 2, -0.006)[0])
rad = [0.01 + 0.032 * math.sin(math.pi * i / 12) ** 0.8 for i in range(13)]
face.append(cl.sweep("grin", pts, rad, 10, dark, scale=(1.0, 0.5), up=(0, 0, 1)))
for s, az in ((1, 11), (-1, -11), (1, -2)):
    p, d = sp(az, -12.5 if az != -2 else -14.5, 0.008)
    ln = 0.034 if az != -2 else 0.022
    face.append(cl.sweep("fang", [p, p + V((0, -0.008, -ln))], [0.013 if az != -2 else 0.01, 0.0], 8, fang))
face_node = cl.node("Face", face, C, core)

# ---------------------------------------------------------------- Flames
# Each flame: list of (path ctrl points, base radius, material) tongues; the node pivot is the
# first tongue's base (buried just inside the core surface).
flames = [
    ("Flame_0", [  # big back plume with three tips, leaning back
        ([(0, 0.12, 0.08), (0, 0.2, 0.32), (0.02, 0.32, 0.42), (-0.02, 0.3, 0.64)], 0.25, flame_mats[0]),
        ([(0.07, 0.14, 0.1), (0.14, 0.24, 0.28), (0.2, 0.34, 0.36), (0.18, 0.4, 0.5)], 0.15, flame_mats[0]),
        ([(-0.07, 0.14, 0.1), (-0.14, 0.24, 0.27), (-0.2, 0.33, 0.33), (-0.19, 0.4, 0.46)], 0.15, flame_mats[0]),
        ([(0, 0.06, 0.12), (0, 0.14, 0.3), (0.03, 0.22, 0.36), (0.0, 0.2, 0.52)], 0.15, flame_inner),
    ]),
    ("Flame_1", [  # left licks, swept back and flicking outward
        ([(0.17, 0.03, 0.12), (0.27, 0.1, 0.24), (0.25, 0.2, 0.33), (0.36, 0.26, 0.44)], 0.11, flame_mats[1]),
        ([(0.2, -0.02, 0.06), (0.32, 0.03, 0.12), (0.34, 0.1, 0.2), (0.43, 0.14, 0.24)], 0.08, flame_mats[1]),
        ([(0.15, 0.0, 0.14), (0.23, 0.05, 0.24), (0.22, 0.12, 0.3), (0.29, 0.16, 0.37)], 0.065, flame_inner),
    ]),
    ("Flame_2", [  # right licks
        ([(-0.17, 0.03, 0.11), (-0.27, 0.1, 0.22), (-0.26, 0.2, 0.3), (-0.37, 0.25, 0.4)], 0.11, flame_mats[2]),
        ([(-0.2, -0.02, 0.05), (-0.31, 0.04, 0.1), (-0.33, 0.12, 0.17), (-0.42, 0.16, 0.2)], 0.08, flame_mats[2]),
        ([(-0.15, 0.0, 0.13), (-0.23, 0.05, 0.22), (-0.22, 0.12, 0.28), (-0.29, 0.16, 0.34)], 0.065, flame_inner),
    ]),
    ("Flame_3", [  # front quiff: rises then curls forward over the brow
        ([(0.0, -0.05, 0.25), (0.0, -0.05, 0.45), (0.0, -0.13, 0.56), (0.0, -0.22, 0.53)], 0.075, flame_mats[3]),
        ([(0.06, -0.03, 0.26), (0.08, -0.04, 0.38), (0.1, -0.1, 0.43), (0.13, -0.15, 0.41)], 0.05, flame_mats[3]),
    ]),
]
flame_nodes = []
for nm, tongues in flames:
    parts = [lick(nm.lower() + "_%d" % k, pts, r, m) for k, (pts, r, m) in enumerate(tongues)]
    flame_nodes.append(cl.node(nm, parts, tongues[0][0][0], core))

# ---------------------------------------------------------------- Embers (orbit ring r = 0.6)
ember_nodes = []
for i, (ang, z) in enumerate(((330.0, 0.06), (90.0, -0.08), (210.0, 0.14))):
    a = math.radians(ang)
    p = V((0.6 * math.cos(a), 0.6 * math.sin(a), z))
    glowing = rw.ico("coal_glow", 0.06, 1, tuple(p), (17 * i, 31, 11 * i), mat=ember, smooth_angle=0)
    shell = rw.ico("coal_shell", 0.056, 1, tuple(p), (45 + 9 * i, 12, 60), mat=coal, smooth_angle=0)
    ember_nodes.append(cl.node("Ember_%d" % i, [glowing, shell], p))

rw.finish(ASSET, "enemies", icon=True)
cl.report_nodes(["Core", "Face", "Flame_0", "Flame_1", "Flame_2", "Flame_3", "Ember_0", "Ember_1", "Ember_2"])
cl.budget(15000)
cl.render_extra(ASSET, "enemies", ("front", "side"))
cl.render_pose(ASSET, "enemies", {"Face": (8, 0, 20), "Flame_0": (-12, 0, 0), "Flame_1": (0, 18, 0),
                                   "Flame_2": (0, -18, 0), "Flame_3": (15, 0, 0)}, "pose")
