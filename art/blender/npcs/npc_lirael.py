"""npc_lirael: Maven Lirael, the spell vendor (origin at the feet, about 1.9 m tall plus the hat, faces -Y).

Tall and slender in a flowing violet robe: lavender front panel edged in gold, a gold hem band with
gold stars and glowing teal runes, wide bell sleeves with gold cuffs and a teal-brooched sash. A very
tall floppy pointed hat (gold band, crescent moon, little stars), silver hair with a long silver braid
down her back, small pointed ears, and a glowing orb hovering over her raised left palm.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the hips; robe, curled shoe tips and the long braid (tucked under her hair at the
         nape so head turns never open a gap) are part of it
    Head  pivot at the neck (inside the head, on the neck axis); hair, ears and hat
    ArmL  pivot at the left shoulder; forearm raised palm-up, with the hovering orb
    ArmR  pivot at the right shoulder; hanging bell sleeve
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
ASSET = "npc_lirael"
rw.reset()

ROBE = "M_Fabric__7d4fdc"
ROBE_IN = "M_Fabric__46288f"
PANEL = "M_Fabric__c3a6ff"
HATC = "M_Fabric__4b2c9e"
SHOE = "M_Leather__3d2a66"
GOLD = rw.flat("TrimGold", "f2c443", 0.35, 0.6)
RUNE = rw.glow("RuneTeal", "5ff2e2", 2.6)
HAIR = rw.flat("HairSilver", "dfe5f1", 0.6)
HAIR_D = rw.flat("HairSilverShade", "aeb7cc", 0.6)
BROW = rw.flat("BrowSilver", "b9bfd4", 0.6)
IRIS = rw.flat("IrisViolet", "9a62ff", 0.35)
LINER = rw.flat("EyeLiner", "2a1d40", 0.5)
LIPS = rw.flat("Lips", "c8466e", 0.5)
ORB = rw.glow("OrbCore", "f1d4ff", 3.2)
SPARK = rw.glow("OrbSpark", "c6f9ff", 3.0)

HIP = V((0, 0.0, 1.0))
SH_L = V((0.21, 0.01, 1.355))
SH_R = V((-0.21, 0.01, 1.355))
NECK = V((0, 0.01, 1.49))
HC = V((0, 0.0, 1.67))
HR = (0.21, 0.2, 0.23)
JC = V((0, -0.058, 1.555))      # softer, narrower lower face (mouth sits on it)
JR = (0.142, 0.142, 0.112)

# ================================================================== Body: robe
prof = nl.Profile([
    (0.02, 0.41, 0.37, 0.02),
    (0.25, 0.35, 0.31, 0.015),
    (0.5, 0.29, 0.25, 0.01),
    (0.75, 0.23, 0.19, 0.005),
    (0.92, 0.18, 0.145, 0.0),
    (1.02, 0.152, 0.122, 0.0),
    (1.12, 0.166, 0.13, -0.005),
    (1.22, 0.186, 0.14, -0.012),
    (1.3, 0.2, 0.135, 0.0),
    (1.36, 0.19, 0.12, 0.01),
    (1.41, 0.12, 0.09, 0.01),
    (1.445, 0.07, 0.065, 0.01),
])
NF = 8   # skirt folds


def folds(a, z):
    f = max(0.0, min(1.0, (0.95 - z) / 0.6))
    return 1.0 + 0.035 * math.sin(math.radians(a) * NF) * f


def hem(a, z):
    return 0.016 * math.sin(math.radians(a) * NF + 0.6) if z < 0.03 else 0.0


body = []
zs = [0.02, 0.12, 0.25, 0.4, 0.55, 0.7, 0.83, 0.93, 1.02, 1.12, 1.22, 1.3, 1.36, 1.41, 1.445]
robe = prof.surface("robe", 0, 0, n=32, mat=ROBE, rmod=folds, zmod=hem, zs=zs, caps=(True, True))
rw.set_mat_where(robe, PANEL, lambda c, n: c.z < 0.97 and c.y < 0 and abs(math.degrees(math.atan2(c.y, c.x)) + 90)
                 < 21)
body.append(robe)
# gold edging down the front panel, gold hem band, stars + runes above it
for s in (1, -1):
    pts = [prof.point(z, 270 + s * 23, 0.006, folds(270 + s * 23, z)) for z in (0.94, 0.75, 0.55, 0.35, 0.15, 0.06)]
    body.append(cl.sweep("panel_edge", pts, 0.011, 6, GOLD, scale=(1.0, 0.6)))
band = prof.surface("hem_band", 0, 0, n=32, off=0.006, mat=GOLD, rmod=folds, zmod=hem, zs=[0.02, 0.07],
                    caps=(False, False))
nl.thicken(band, 0.01)
body.append(band)
RUNES = ["algiz", "sowilo", "ingwaz", "kenaz", "tiwaz", "othala"]
for k in range(12):
    a = 270.0 + 30.0 * k + 15.0
    if abs(((a - 270.0 + 180.0) % 360.0) - 180.0) < 22:
        continue   # keep the front panel clean
    z = 0.17
    p = prof.point(z, a, 0.004, folds(a, z))
    n = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0.12)).normalized()
    if k % 2 == 0:
        body.append(nl.star("hem_star", p, n, (0, 0, 1), 0.05, 0.022, 0.012, 5, GOLD))
    else:
        u = V((0, 0, 1)).cross(n).normalized()
        body += pl.glyph(RUNES[k % len(RUNES)], p + n * 0.004, -u, V((0, 0, 1)), 0.11, 0.024, 0.014, RUNE,
                         "hem_rune")
# sash at the waist with a teal crystal brooch
sash = prof.surface("sash", 0.975, 1.06, 1, 24, 0.014, "M_Fabric__2fb7a8", caps=(False, False))
nl.thicken(sash, 0.016)
body.append(sash)
bp = V((0, prof.front_y(1.02, 0, 0.03), 1.02))
body.append(cl.ellipsoid("brooch_gold", bp, (0.04, 0.016, 0.045), 12, 5, GOLD))
body.append(pl.crystal("brooch_gem", bp + V((0, -0.006, -0.025)), (0, -0.2, 1), 0.05, 0.022, 6, 0.3, 0.12,
                       "M_Crystal"))
# standing collar with a gold rim
body.append(nl.lathe_z("collar", [(0.072, 1.39), (0.088, 1.42), (0.1, 1.448), (0.093, 1.454), (0.078, 1.43),
                                  (0.068, 1.395)], (0, 0.012, 0), 18, ROBE_IN, None, 40, (False, False)))
body.append(cl.torus("collar_rim", (0, 0.012, 1.45), 0.097, 0.008, None, 18, 4, GOLD))
body.append(cl.cyl("neck", (0, 0.01, 1.38), (0, 0.01, 1.58), 0.058, 12, "M_Skin"))
# curled shoe tips peeking out under the hem
for s in (1, -1):
    tip = nl.smooth_path([V((s * 0.09, -0.26, 0.04)), V((s * 0.1, -0.38, 0.045)), V((s * 0.105, -0.45, 0.075)),
                          V((s * 0.1, -0.455, 0.11))], 7)
    body.append(cl.sweep("shoe", tip, [0.06, 0.055, 0.045, 0.035, 0.026, 0.018, 0.0], 10, SHOE,
                         scale=(0.65, 1.0), up=(0, 0, 1)))
    body.append(cl.sphere("shoe_bead", tip[-1] + V((0, 0.004, 0.012)), 0.015, 8, 4, GOLD))
# long silver braid down her back (Body: top tucked under the hair at the nape)
body += nl.braid("braid", [V((0, 0.15, 1.535)), V((0, 0.166, 1.42)), V((0, 0.17, 1.3)), V((0, 0.165, 1.15)),
                           V((0, 0.165, 1.02)), V((0, 0.192, 0.92)), V((0, 0.234, 0.81))], 0.056, 0.04, 11, HAIR,
                 8, 5, 26.0, 0.8, 1.55)
body.append(cl.cyl("braid_cuff", V((0, 0.24, 0.8)), V((0, 0.252, 0.762)), 0.04, 10, GOLD))
body.append(cl.sweep("braid_tuft", [V((0, 0.252, 0.768)), V((0, 0.26, 0.725)), V((0, 0.27, 0.68))],
                     [0.036, 0.044, 0.0], 8, HAIR))

# ================================================================== Head
head = [nl.head_shape("skull", HC, HR, JC, JR, 24, 13)]
head += nl.eye_pair(HC, HR, 0.082, 1.655, 0.066, IRIS, lid=0.1, lid_mat=LINER, lid_tilt=-8.0, segs=12,
                    shape=(0.78, 0.5, 1.0))
for s in (1, -1):   # lash flicks at the outer corners
    a = cl.head_point(HC, HR, s * 0.122, 1.69, 0.004)
    b = a + V((s * 0.03, 0.012, 0.022))
    head.append(cl.sweep("lash", [a, a.lerp(b, 0.5) + V((0, -0.004, 0.002)), b], [0.009, 0.007, 0.0], 6, LINER))
head += nl.brow_pair(HC, HR, 0.04, 0.13, 1.75, 1.755, 0.011, 0.016, BROW, flat=0.5)
head.append(nl.nose(HC, HR, 1.6, (0.024, 0.024, 0.028)))
head += nl.cheeks(JC, JR, 0.09, 1.57, 0.03, rw.flat("BlushSoft", "f2a0b8", 0.7))
head.append(nl.smile(JC, JR, 0.05, 1.53, 0.012, 0.0095, embed=0.2, mat=LIPS))
head.append(cl.ellipsoid("lower_lip", cl.head_point(JC, JR, 0.0, 1.517, -0.002), (0.022, 0.008, 0.008), 8, 4, LIPS))
# small pointed ears
for s in (1, -1):
    ec = V((s * 0.222, 0.02, 1.645))
    head.append(cl.ellipsoid("ear", ec, (0.024, 0.042, 0.06), 8, 5, "M_Skin",
                             Matrix.Rotation(math.radians(-28 * s), 3, 'Y')))
    head.append(cl.sweep("ear_tip", [ec + V((s * 0.008, 0.004, 0.028)), ec + V((s * 0.05, 0.03, 0.095))],
                         [0.024, 0.0], 8, "M_Skin", scale=(0.45, 1.0), up=(s, 0, 0)))
# silver hair: cap tilted back, middle-parted bangs, side locks framing the face
head.append(cl.dome("hair_cap", HC + V((0, 0.012, 0.01)), (HR[0] * 1.06, HR[1] * 1.08, HR[2] * 1.06),
                    Matrix.Rotation(math.radians(-38), 3, 'X'), 0.62, 20, 6, HAIR))
for s in (1, -1):
    a = cl.head_point(HC, HR, s * 0.012, 1.86, 0.012)
    m = cl.head_point(HC, HR, s * 0.11, 1.8, 0.024)
    b = cl.head_point(HC, HR, s * 0.175, 1.69, 0.012)
    head.append(cl.sweep("bang", cl.bezier(a, m, b, 6), [0.03, 0.038, 0.036, 0.03, 0.02, 0.0], 8, HAIR,
                         scale=(1.0, 0.55), up=(0, 0, 1)))
    lk = [cl.head_point(HC, HR, s * 0.17, 1.72, 0.02), V((s * 0.205, -0.07, 1.6)), V((s * 0.19, -0.075, 1.5)),
          V((s * 0.165, -0.06, 1.43))]
    head.append(cl.sweep("side_lock", nl.smooth_path(lk, 7), [0.034, 0.038, 0.036, 0.032, 0.026, 0.018, 0.0], 8,
                         HAIR))
# very tall floppy pointed hat
Rb = Matrix.Rotation(math.radians(-7), 3, 'X')
hb = V((0, 0.012, 1.835))
head.append(nl.lathe_z("hat_brim", [(0.13, -0.012), (0.27, -0.01), (0.315, 0.0), (0.33, 0.018), (0.322, 0.026),
                                    (0.27, 0.008), (0.13, 0.012)], hb, 20, HATC, Rb, 40, (False, False)))
cone = nl.smooth_path([hb + V((0, 0, -0.03)), hb + V((0, 0.0, 0.14)), hb + V((0.006, 0.03, 0.3)),
                       hb + V((-0.004, 0.08, 0.44)), hb + V((-0.04, 0.17, 0.53)), hb + V((-0.09, 0.27, 0.53)),
                       hb + V((-0.13, 0.33, 0.47))], 14)
crad = [0.178, 0.17, 0.153, 0.136, 0.12, 0.104, 0.089, 0.075, 0.062, 0.05, 0.038, 0.026, 0.014, 0.0]
crad = [r * (1.0 + (0.06 * math.sin(i * 1.7) if i > 2 else 0.0)) for i, r in enumerate(crad)]
head.append(cl.sweep("hat_cone", cone, crad, 12, HATC))
head.append(nl.lathe_z("hat_band", [(0.176, -0.004), (0.192, 0.006), (0.19, 0.056), (0.172, 0.064)], hb, 18, GOLD,
                       Rb, 40, (False, False)))
# crescent moon on the band, little stars on the cone
i = 3
c = cone[i]
mc = V((c.x, c.y - crad[i] - 0.004, c.z + 0.01))
arc = [mc + V((0.042 * math.cos(math.radians(a)), -0.006 * math.sin(math.radians(a - 180)) * 0,
              0.042 * math.sin(math.radians(a)))) for a in range(60, 301, 30)]
head.append(cl.sweep("moon", arc, [0.0, 0.01, 0.016, 0.019, 0.02, 0.019, 0.016, 0.01, 0.0], 6, GOLD,
                     scale=(1.0, 0.5), up=(0, -1, 0)))
for (t, a, sz) in ((0.32, 200.0, 0.032), (0.52, 300.0, 0.026), (0.7, 240.0, 0.02)):
    i = int(t * (len(cone) - 1))
    c = cone[i]
    tan = (cone[i + 1] - cone[i - 1]).normalized()
    side = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
    side = (side - tan * side.dot(tan)).normalized()
    head.append(nl.star("hat_star", c + side * (crad[i] + 0.002), side, tan, sz, sz * 0.45, 0.01, 5, GOLD))

# ================================================================== ArmL: forearm raised palm-up, hovering orb
A = nl.arm_frame(1, SH_L, 0.29, 0.25, spread=10.0, bend=78.0)
S, E, W, d1, d2 = A.S, A.E, A.W, A.d1, A.d2
arm_l = [cl.sphere("shoulder", S, 0.072, 12, 6, ROBE)]
arm_l.append(cl.sweep("upper", [S, E], [0.066, 0.062], 10, ROBE, cap_start=False, cap_end=False))
arm_l.append(cl.sphere("elbow", E, 0.064, 10, 5, ROBE))
# drooping bell sleeve along the forearm
bell = [E + d2 * 0.0, E + d2 * 0.07 + V((0, 0, -0.012)), E + d2 * 0.14 + V((0, 0, -0.03)),
        E + d2 * 0.2 + V((0, 0, -0.052))]
bl = cl.sweep("bell", bell, [0.064, 0.078, 0.098, 0.118], 14, ROBE, scale=[(1.0, 1.0), (1.15, 1.0), (1.3, 1.0),
                                                                          (1.4, 1.0)], up=(0, 0, 1),
              cap_start=False, cap_end=False)
nl.thicken(bl, 0.012, ROBE_IN)
arm_l.append(bl)
arm_l.append(cl.torus("cuff", bell[-1], 0.118, 0.014, nl.rot_to(d2), 14, 4, GOLD, scale=(1.0, 1.4)))
arm_l.append(cl.sweep("forearm", [E + d2 * 0.1, W + d2 * 0.005], [0.04, 0.034], 8, "M_Skin", cap_start=False))
arm_l += nl.hand("hand", W, d2, (0, 0, 1), (1, 0, 0), 0.105, "M_Skin", 3, curl=0.25, spread=1.1)
OC = W + d2 * 0.055 + V((0, 0, 0.15))
arm_l.append(cl.sphere("orb_core", OC, 0.052, 10, 5, ORB))
arm_l.append(cl.sphere("orb_shell", OC, 0.078, 12, 6, "M_Crystal__c08cff"))
pl.tint_emission("M_Crystal__c08cff", "c08cff")
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.4
    sp = OC + V((0.115 * math.cos(a), 0.115 * math.sin(a), 0.03 * math.sin(3 * a)))
    arm_l.append(rw.ico("spark", 0.018, 0, tuple(sp), (20 * k, 35, 10), mat=SPARK, smooth_angle=0))

# ================================================================== ArmR: hanging bell sleeve
B = nl.arm_frame(-1, SH_R, 0.29, 0.25, spread=8.0, bend=12.0)
S, E, W, d1, d2 = B.S, B.E, B.W, B.d1, B.d2
arm_r = [cl.sphere("shoulder", S, 0.072, 12, 6, ROBE)]
arm_r.append(cl.sweep("upper", [S, E], [0.066, 0.062], 10, ROBE, cap_start=False, cap_end=False))
arm_r.append(cl.sphere("elbow", E, 0.063, 10, 5, ROBE))
cuff_p = W - d2 * 0.04
bell = [E, E.lerp(cuff_p, 0.4), E.lerp(cuff_p, 0.75), cuff_p]
br = cl.sweep("bell", bell, [0.064, 0.074, 0.095, 0.122], 14, ROBE, cap_start=False, cap_end=False)
nl.thicken(br, 0.012, ROBE_IN)
arm_r.append(br)
arm_r.append(cl.torus("cuff", cuff_p, 0.122, 0.014, nl.rot_to(d2), 14, 4, GOLD))
arm_r.append(cl.sweep("forearm", [E.lerp(W, 0.3), W + d2 * 0.005], [0.04, 0.034], 8, "M_Skin", cap_start=False))
arm_r += nl.hand("hand", W - d2 * 0.005, (d2 + V((0, -0.05, 0))).normalized(), (1, 0, 0), (0, -1, 0), 0.105,
                 "M_Skin", 3, curl=0.4)

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
