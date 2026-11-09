"""npc_brannoc: Captain Brannoc, the guard captain (origin at the feet, about 1.95 m tall, faces -Y).

Burly, in rune-etched steel plate: a breastplate with glowing violet rune channels and a central
algiz (protection) sigil, brass trims, tassets over navy trousers, greaves and armoured boots. Big
round pauldrons and vambraces, steel gauntlets. A big auburn beard with a long central braid and two
side braids (brass rings), a handlebar moustache, bushy brows. A crimson cape from the shoulders,
and a sword in its scabbard at his left hip.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the hips; legs, armour, cape and sword are part of it
    Head  pivot at the neck (inside the head, on the neck axis); beard and braids turn with it
    ArmL  pivot at the left shoulder (pauldron, gambeson sleeve, vambrace, gauntlet)
    ArmR  pivot at the right shoulder
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "parts"))
import npclib as nl  # noqa: E402
import partlib as pl  # noqa: E402
from mathutils import Matrix  # noqa: E402

rw, cl, V = nl.rw, nl.cl, nl.V
ASSET = "npc_brannoc"
rw.reset()

NAVY = "M_Fabric__2c3f72"
CAPE = "M_Fabric__c8292b"
CAPE_IN = "M_Fabric__7a1820"
RUNE = "M_RuneGlow"
HAIR = rw.flat("HairAuburn", "b4552a", 0.7)
HAIR_L = rw.flat("HairAuburnLight", "cf6d36", 0.7)
IRIS = rw.flat("IrisBlue", "3d86d8", 0.4)

HIP = V((0, 0.0, 0.95))
SH_L = V((0.355, 0.0, 1.385))
SH_R = V((-0.355, 0.0, 1.385))
NECK = V((0, 0.01, 1.56))
HC = V((0, 0.0, 1.72))
HR = (0.212, 0.205, 0.222)

# ================================================================== Body
torso = nl.Profile([
    (0.84, 0.25, 0.2, 0.01),
    (0.95, 0.27, 0.215, 0.005),
    (1.05, 0.28, 0.225, -0.005),
    (1.16, 0.31, 0.245, -0.015),
    (1.28, 0.33, 0.255, -0.02),
    (1.38, 0.322, 0.235, -0.01),
    (1.45, 0.27, 0.19, 0.0),
    (1.5, 0.17, 0.13, 0.005),
    (1.535, 0.1, 0.09, 0.01),
])
body = []
trunk = torso.surface("trunk", 0.84, 1.535, 8, 20, 0.0, NAVY)
body.append(trunk)
# legs: navy trousers, steel greaves, armoured boots
for s in (1, -1):
    body.append(nl.leg(s, (s * 0.15, 0.01, 0.9), (s * 0.165, 0.0, 0.2), 0.125, 0.095, NAVY, 10,
                       knee=(s * 0.006, -0.01, 0)))
    kn = V((s * 0.163, -0.075, 0.52))
    body.append(cl.ellipsoid("knee_cop", kn, (0.075, 0.05, 0.07), 10, 5, "M_Steel"))
    body.append(nl.lathe_z("greave", [(0.098, 0.2), (0.106, 0.3), (0.112, 0.44), (0.104, 0.47), (0.09, 0.46)],
                           (s * 0.165, 0.0, 0.0), 12, "M_Steel", None, 40, (False, False)))
    body += nl.boot(s * 0.165, 0.0, "M_Steel", "M_Leather__4a3020", h=0.21, r=0.1, toe=0.17, toe_cap=None,
                    lip_mat="M_Brass", segs=10)
# breastplate: steel shell wrapped on the chest with a scooped neckline
plate_zs = [1.455, 1.4, 1.33, 1.25, 1.17, 1.09, 1.02]


def plate_half(z):
    return 74.0 if z < 1.38 else 74.0 - (z - 1.38) * 160.0


def neckline(a, z, k):
    if z < 1.45:
        return 0.0
    u = (a - 270.0) / plate_half(z)
    return -0.05 * (1 - u * u)


plate = nl.arc_panel("breastplate", torso, plate_zs, plate_half, 270.0, 12, 0.03, "M_Steel", neckline)
nl.thicken(plate, 0.022)
body.append(plate)
# brass trim along the neckline and the bottom edge
top = [torso.point(1.455, 270 - plate_half(1.455) + 2 * plate_half(1.455) * k / 10, 0.032) for k in range(11)]
for p, k in zip(top, range(11)):
    p.z += neckline(270 - plate_half(1.455) + 2 * plate_half(1.455) * k / 10, 1.455, k)
body.append(cl.sweep("plate_trim_top", top, 0.014, 5, "M_Brass"))
bot = [torso.point(1.02, 270 - 74 + 148 * k / 10, 0.033) for k in range(11)]
body.append(cl.sweep("plate_trim_bot", bot, 0.014, 5, "M_Brass"))
# glowing rune channels: chevrons over the pecs + a central algiz sigil
for s in (1, -1):
    pts = [torso.point(z, 270 + s * a, 0.031) for (z, a) in ((1.41, 52), (1.34, 40), (1.27, 27), (1.2, 16),
                                                              (1.13, 9))]
    body.append(cl.sweep("rune_line", pts, 0.009, 6, RUNE))
    pts = [torso.point(z, 270 + s * a, 0.031) for (z, a) in ((1.3, 66), (1.2, 56), (1.1, 46))]
    body.append(cl.sweep("rune_line2", pts, 0.008, 6, RUNE))
sc = torso.point(1.122, 270.0, 0.03)
body += pl.glyph("algiz", sc, (-1, 0, 0), (0, 0, 1), 0.115, 0.024, 0.014, RUNE, "sigil")
ring = [V((0.078 * math.cos(t), 0, 1.122 + 0.078 * math.sin(t))) for t in [2 * math.pi * k / 16 for k in range(17)]]
ring = [V((q.x, torso.front_y(q.z, q.x, 0.034), q.z)) for q in ring]
body.append(cl.sweep("sigil_ring", ring, 0.01, 5, "M_Brass", cap_start=False, cap_end=False))
# belt with a big brass buckle and a rune gem
belt = torso.surface("belt", 0.93, 1.0, 1, 20, 0.038, "M_Leather__4a3020", caps=(False, False))
nl.thicken(belt, 0.024)
body.append(belt)
fy = torso.front_y(0.965, 0.0, 0.04)
body.append(cl.rbox("buckle", (0.13, 0.03, 0.1), (0, fy - 0.006, 0.965), 0.018, "M_Brass", segments=1))
body.append(cl.ellipsoid("buckle_gem", (0, fy - 0.024, 0.965), (0.025, 0.012, 0.025), 10, 4, RUNE))
# tassets: overlapping steel plates hanging over the hips
tas = nl.Profile([(0.68, 0.33, 0.27, 0.0), (0.82, 0.31, 0.25, 0.0), (0.93, 0.29, 0.235, 0.0)])
# red tabard down the front, between the tassets, with a brass rune medallion
tab = nl.arc_panel("tabard", tas, [0.93, 0.8, 0.66, 0.55], lambda z: 17.0 + (0.93 - z) * 8.0, 270.0, 4, 0.034, CAPE,
                   lambda a, z, k: (0.025 * (1 - ((a - 270.0) / 20.0) ** 2) if z < 0.56 else 0.0))
nl.thicken(tab, 0.014, CAPE_IN)
body.append(tab)
mp = tas.point(0.79, 270.0, 0.05)
body.append(cl.cyl("medallion", mp + V((0, 0.012, 0)), mp + V((0, -0.006, 0)), 0.045, 12, "M_Brass"))
body.append(cl.ellipsoid("medallion_gem", mp + V((0, -0.008, 0)), (0.02, 0.01, 0.026), 8, 4, RUNE))
for (c, h) in ((236.0, 26.0), (304.0, 26.0), (200.0, 18.0), (340.0, 18.0)):
    t = nl.arc_panel("tasset", tas, [0.93, 0.82, 0.7], h, c, 6, 0.012, "M_Steel")
    nl.thicken(t, 0.016)
    body.append(t)
# neck + crimson cape: a rolled collar around the back of the neck, brass clasps, the cape down the back
body.append(cl.cyl("neck", (0, 0.01, 1.42), (0, 0.01, 1.64), 0.092, 14, "M_Skin"))
cape_prof = nl.Profile([(1.5, 0.25, 0.2, 0.02), (1.43, 0.36, 0.27, 0.02), (1.32, 0.375, 0.29, 0.03),
                        (1.0, 0.37, 0.31, 0.05), (0.7, 0.385, 0.34, 0.08), (0.42, 0.4, 0.37, 0.1)])


def cape_fold(a, z):
    f = max(0.0, min(1.0, (1.3 - z) / 0.6))
    return 1.0 + 0.04 * math.sin(math.radians(a - 90) * 7) * f


def cape_hem(a, z, k):
    return 0.02 * math.sin(math.radians(a) * 7) if z < 0.43 else 0.0


cape_rings = []
for z in (1.5, 1.43, 1.34, 1.15, 0.9, 0.66, 0.42):
    ring = []
    for k in range(15):
        a = 6.0 + 168.0 * k / 14
        p = cape_prof.point(z, a, 0.0, cape_fold(a, z))
        p.z += cape_hem(a, z, k)
        ring.append(p)
    cape_rings.append(ring)
cape = cl.skin("cape", cape_rings, CAPE, False, False, True, None, closed=False)
nl.thicken(cape, 0.02, CAPE_IN)
body.append(cape)
collar = [V((0.24 * math.cos(math.radians(a)), 0.02 + 0.2 * math.sin(math.radians(a)), 1.5)) for a in
          range(-30, 211, 30)]
body.append(cl.sweep("cape_collar", collar, 0.038, 6, CAPE))
for s in (1, -1):
    cp = V((s * 0.205, -0.115, 1.46))
    cn = V((s * 0.35, -1, 0.5)).normalized()
    body.append(cl.cyl("clasp", cp - cn * 0.01, cp + cn * 0.012, 0.042, 10, "M_Brass"))
    body.append(cl.ellipsoid("clasp_gem", cp + V((s * 0.004, -0.012, 0.006)), (0.018, 0.01, 0.018), 8, 4, RUNE))
# sword at the left hip: scabbard angled back, hilt forward
sa, sb = V((0.335, -0.07, 0.9)), V((0.4, 0.27, 0.3))
sd = (sb - sa).normalized()
body.append(cl.sweep("scabbard", [sa, sa.lerp(sb, 0.5), sb], [0.036, 0.034, 0.026], 8, "M_Leather__3a2418",
                     scale=(1.0, 0.45), up=(1, 0, 0)))
body.append(cl.ellipsoid("scabbard_tip", sb, (0.034, 0.03, 0.03), 8, 4, "M_Brass"))
body.append(cl.cyl("scabbard_mouth", sa - sd * 0.01, sa + sd * 0.05, 0.042, 10, "M_Brass"))
hd = -sd
xg = (V((1, 0, 0)) - hd * hd.x).normalized()
body.append(cl.rbox("crossguard", (0.2, 0.036, 0.034), sa - sd * 0.02, 0.012, "M_Brass",
                    cl.axes_matrix(xg, hd.cross(xg), hd), segments=1))
body.append(cl.cyl("grip", sa - sd * 0.03, sa - sd * 0.17, 0.02, 8, "M_Leather__3a2418"))
body.append(cl.sphere("pommel", sa - sd * 0.19, 0.034, 10, 5, "M_Brass"))
body.append(cl.sphere("pommel_gem", sa - sd * 0.19 + V((0.0, -0.028, 0.012)), 0.014, 6, 3, RUNE))

# ================================================================== Head
head = [cl.ellipsoid("skull", HC, HR, 20, 11, "M_Skin")]
head += nl.eye_pair(HC, HR, 0.08, 1.735, 0.054, IRIS, lid=0.2, lid_mat="M_Skin", lid_tilt=-4.0, segs=10)
head += nl.brow_pair(HC, HR, 0.03, 0.14, 1.79, 1.812, 0.027, 0.01, HAIR, flat=0.6)
head.append(nl.nose(HC, HR, 1.672, (0.05, 0.045, 0.05)))
head += nl.cheeks(HC, HR, 0.13, 1.68, 0.032)
head += nl.ears(HC, HR, 1.71, (0.03, 0.045, 0.062), segs=8)
# short auburn hair: cropped cap tilted back + a little quiff
head.append(cl.dome("hair_cap", HC + V((0, 0.012, 0.012)), (HR[0] * 1.05, HR[1] * 1.06, HR[2] * 1.05),
                    Matrix.Rotation(math.radians(-32), 3, 'X'), 0.52, 20, 5, HAIR))
# big beard: mass over the jaw, sideburns, handlebar moustache, a grin peeking out
BC, BR = V((0, -0.105, 1.555)), (0.2, 0.145, 0.165)
head.append(cl.ellipsoid("beard", BC, BR, 16, 8, HAIR))
for s in (1, -1):
    head.append(cl.ellipsoid("sideburn", V((s * 0.175, -0.02, 1.64)), (0.05, 0.085, 0.1), 8, 5, HAIR,
                             Matrix.Rotation(math.radians(-10 * s), 3, 'Y')))
head += nl.open_smile(BC, BR, 0.06, 1.625, 0.04, 0.008, tongue=True, teeth=True, nu=6)
for s in (1, -1):
    m = [V((s * 0.012, -0.235, 1.648)), V((s * 0.075, -0.225, 1.636)), V((s * 0.13, -0.19, 1.618)),
         V((s * 0.17, -0.16, 1.645)), V((s * 0.175, -0.155, 1.68))]
    head.append(cl.sweep("moustache", nl.smooth_path(m, 8), [0.026, 0.034, 0.033, 0.029, 0.024, 0.018, 0.012, 0.0], 6,
                         HAIR_L, scale=(0.75, 1.0), up=(0, 0, 1)))
# braids: a long central one and two shorter side braids, with brass rings
for s in (1, -1):
    head += nl.braid("side_braid", [V((s * 0.13, -0.17, 1.44)), V((s * 0.14, -0.21, 1.37))], 0.034, 0.028, 2, HAIR, 7,
                     4, 24.0, 0.8, 1.6)
    head.append(cl.sphere("bead", V((s * 0.141, -0.215, 1.335)), 0.027, 8, 4, "M_Brass"))

# a bigger cartoon head on the burly body: scale it about the neck pivot and sink it a little
nl.scale_parts(head, NECK, 1.08, (0, 0, -0.035))
# the long central beard braid rests on the breastplate (built after the scale, in final coordinates)
head += nl.braid("braid", [V((0, -0.27, 1.4)), V((0, -0.345, 1.33)), V((0, -0.352, 1.262))], 0.054, 0.042, 5, HAIR,
                 8, 4, 24.0, 0.8, 1.5)
for p, r, d in ((V((0, -0.34, 1.345)), 0.053, (0, -0.55, -0.85)), (V((0, -0.351, 1.272)), 0.048, (0, -0.05, -1))):
    head.append(cl.torus("braid_ring", p, r, 0.013, nl.rot_to(d), 10, 4, "M_Brass"))

# ================================================================== Arms: pauldron, gambeson sleeve, vambrace, gauntlet


def armored_arm(side, S):
    A = nl.arm_frame(side, S, 0.31, 0.29, spread=13.0, bend=14.0)
    S, E, W, d1, d2 = A.S, A.E, A.W, A.d1, A.d2
    out = V((side, 0, 0))
    parts = [cl.sphere("shoulder", S, 0.1, 12, 6, NAVY)]
    parts.append(cl.sweep("upper", [S, E], [0.09, 0.08], 10, NAVY, cap_start=False, cap_end=False))
    # pauldron: two stacked lames + brass rim + glowing rune line
    Rp = nl.rot_to((side * 0.5, 0.0, 1.0))
    pc = S + V((side * 0.012, 0, 0.018))
    parts.append(cl.dome("pauldron", pc, (0.14, 0.132, 0.12), Rp, 0.55, 18, 4, "M_Steel"))
    parts.append(cl.dome("pauldron2", pc + Rp @ V((0, 0, -0.04)), (0.158, 0.15, 0.13), Rp, 0.4, 18, 2, "M_Steel"))
    rim = [pc + Rp @ V((0.155 * math.cos(math.radians(a)), 0.147 * math.sin(math.radians(a)), -0.014))
           for a in range(0, 361, 30)]
    parts.append(cl.sweep("pauldron_rim", rim, 0.013, 5, "M_Brass", cap_start=False, cap_end=False))
    a0 = 0.0 if side > 0 else 180.0
    ph = math.radians(52)
    rl = [pc + Rp @ V((0.141 * math.sin(ph) * math.cos(math.radians(a0 + a)),
                       0.133 * math.sin(ph) * math.sin(math.radians(a0 + a)), 0.121 * math.cos(ph)))
          for a in range(-70, 71, 20)]
    parts.append(cl.sweep("pauldron_rune", rl, 0.008, 6, RUNE))
    # elbow cop, vambrace, gauntlet
    parts.append(cl.sphere("elbow", E, 0.082, 10, 5, NAVY))
    parts.append(cl.dome("elbow_cop", E, (0.09, 0.09, 0.085), nl.rot_to(V((0, 0.9, 0)) - d1 * 0.2 + out * 0.3), 0.5,
                         12, 3, "M_Steel"))
    parts.append(nl.lathe_z("vambrace", [(0.074, 0.0), (0.082, 0.06), (0.09, 0.2), (0.098, 0.235), (0.088, 0.24)],
                            E + d2 * 0.04, 12, "M_Steel", nl.rot_to(d2), 40, (False, False)))
    vr = E + d2 * 0.16
    parts.append(cl.sweep("vambrace_rune", [vr + out * 0.088 + V((0, -0.03, 0.03)), vr + out * 0.092,
                                            vr + out * 0.088 + V((0, 0.03, -0.03))], 0.007, 6, RUNE))
    parts.append(cl.torus("vambrace_band", E + d2 * 0.27, 0.095, 0.012, nl.rot_to(d2), 12, 4, "M_Brass"))
    hdn = (d2 + V((0, -0.05, 0))).normalized()
    parts += nl.hand("gauntlet", W, hdn, V((-side, 0, 0)), V((0, -1, 0)), 0.135, "M_Steel", 3, curl=0.5)
    return parts


arm_l = armored_arm(1, SH_L)
arm_r = armored_arm(-1, SH_R)

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
