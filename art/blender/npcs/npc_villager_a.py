"""npc_villager_a: a stout, jolly town baker (origin at the feet, about 1.7 m with his cap, faces -Y).

Round belly, a puffy white baker's cap, a white bib apron with a pocket (wooden spoon) tied at the
back with a bow, a blue-and-white Breton-striped shirt with rolled sleeves, a red neckerchief, brown
trousers and boots. Clean-shaven and blond, rosy chubby cheeks with a smudge of flour, a big grin,
and a fresh baguette in his left hand.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the hips; legs, apron and neckerchief are part of it
    Head  pivot at the neck (inside the head, on the neck axis); cap, hair, moustache
    ArmL  pivot at the left shoulder (rolled sleeve, holds the baguette)
    ArmR  pivot at the right shoulder (rolled sleeve)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npclib as nl  # noqa: E402
from mathutils import Matrix  # noqa: E402

rw, cl, V = nl.rw, nl.cl, nl.V
ASSET = "npc_villager_a"
rw.reset()

SHIRT = "M_Fabric__f4f2ec"
STRIPE = "M_Fabric__3b72c8"
SHIRT_D = "M_Fabric__2e5aa3"
APRON = "M_Fabric__f6f1e6"
CAPW = "M_Fabric__fbf8f2"
TROUSERS = "M_Fabric__6a4a3a"
SCARF = "M_Fabric__d8392c"
HAIR = rw.flat("HairBlond", "e2b04f", 0.7)
FLOUR = rw.flat("Flour", "fbf7ef", 0.9)
IRIS = rw.flat("IrisBlueBaker", "4a8fd6", 0.4)
CRUST = rw.flat("BreadCrust", "d8913f", 0.7)
CRUMB = rw.flat("BreadScore", "f3d08a", 0.7)

HIP = V((0, 0.0, 0.6))
SH_L = V((0.3, 0.01, 1.025))
SH_R = V((-0.3, 0.01, 1.025))
NECK = V((0, 0.012, 1.19))
HC = V((0, 0.0, 1.37))
HR = (0.228, 0.212, 0.215)
JC = V((0, -0.068, 1.278))
JR = (0.172, 0.158, 0.108)

# ================================================================== Body
torso = nl.Profile([
    (0.5, 0.24, 0.2, 0.0),
    (0.58, 0.29, 0.25, -0.01),
    (0.7, 0.33, 0.3, -0.04),
    (0.82, 0.335, 0.305, -0.045),
    (0.93, 0.315, 0.265, -0.025),
    (1.02, 0.29, 0.21, 0.0),
    (1.08, 0.24, 0.17, 0.01),
    (1.12, 0.16, 0.13, 0.01),
    (1.15, 0.09, 0.085, 0.01),
])
body = []
trunk = torso.surface("trunk", 0.5, 1.15, 16, 22, 0.0, SHIRT)
rw.set_mat_where(trunk, STRIPE, lambda c, n: int(round((c.z - 0.5) / 0.040625 - 0.5)) % 2 == 1)
rw.set_mat_where(trunk, TROUSERS, lambda c, n: c.z < 0.62)
body.append(trunk)
for s in (1, -1):
    body.append(nl.leg(s, (s * 0.13, 0.01, 0.55), (s * 0.14, 0.0, 0.14), 0.115, 0.088, TROUSERS, 10,
                       knee=(0, -0.01, 0)))
    body += nl.boot(s * 0.14, 0.0, "M_Leather__6b4127", "M_Rubber", h=0.16, r=0.094, toe=0.155, segs=10, lip=0.026)
body.append(cl.cyl("neck", (0, 0.012, 1.06), (0, 0.012, 1.25), 0.08, 12, "M_Skin"))
# white bib apron over the belly, down to the knees; neck strap; waist ties with a bow at the back
ap = nl.Profile([(0.3, 0.3, 0.27, -0.035), (0.42, 0.31, 0.28, -0.04), (0.55, 0.315, 0.29, -0.04)] +
                list(torso.L[2:7]))


def apron_half(z):
    if z > 0.92:
        return 40.0
    if z > 0.7:
        return 40.0 + (0.92 - z) / 0.22 * 30.0
    return 70.0 - (0.7 - z) / 0.4 * 10.0


azs = [1.06, 0.98, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.31]
apron = nl.arc_panel("apron", ap, azs, apron_half, 270.0, 10, 0.02, APRON,
                     lambda a, z, k: 0.03 * ((a - 270.0) / apron_half(z)) ** 4 if z < 0.32 else 0.0)
nl.thicken(apron, 0.014)
body.append(apron)
pocket = nl.arc_panel("apron_pocket", ap, [0.62, 0.55, 0.48], 26.0, 270.0, 6, 0.032, APRON)
nl.thicken(pocket, 0.01)
body.append(pocket)
sp = ap.point(0.6, 284.0, 0.04)
body.append(cl.cyl("spoon_handle", sp + V((0, 0.0, -0.05)), sp + V((0.012, -0.01, 0.12)), 0.011, 6, "M_WoodPlanks"))
body.append(cl.ellipsoid("spoon_bowl", sp + V((0.016, -0.014, 0.15)), (0.028, 0.012, 0.038), 8, 4, "M_WoodPlanks"))
for s in (1, -1):
    p = ap.point(1.055, 270 + s * 40.0, 0.03)
    strap = [p, V((s * 0.11, -0.1, 1.12)), V((s * 0.1, 0.0, 1.16)), V((0, 0.08, 1.165))]
    body.append(cl.sweep("neck_strap", nl.smooth_path(strap, 6), 0.013, 6, APRON, scale=(1.0, 0.5)))
tie = torso.surface("apron_tie", 0.74, 0.77, 1, 20, 0.022, APRON, a0=-60.0, a1=240.0, caps=(False, False))
nl.thicken(tie, 0.01)
body.append(tie)
bk = torso.point(0.755, 90.0, 0.03)
for s in (1, -1):
    body.append(cl.ellipsoid("bow_loop", bk + V((s * 0.05, 0.012, 0.012)), (0.05, 0.016, 0.03), 8, 4, APRON,
                             Matrix.Rotation(math.radians(-15 * s), 3, 'Y')))
    body.append(cl.sweep("bow_tail", [bk + V((s * 0.01, 0.01, 0)), bk + V((s * 0.04, 0.02, -0.08)),
                                      bk + V((s * 0.05, 0.024, -0.15))], [0.016, 0.014, 0.012], 6, APRON,
                         scale=(1.0, 0.4), up=(0, 1, 0)))
body.append(cl.sphere("bow_knot", bk + V((0, 0.016, 0.004)), 0.022, 8, 4, APRON))
# blue neckerchief with a knot at the front
body.append(cl.torus("scarf", (0, 0.012, 1.13), 0.105, 0.03, None, 16, 5, SCARF, scale=(1.0, 0.95)))
kp = V((0, -0.115, 1.105))
body.append(cl.sphere("scarf_knot", kp, 0.03, 8, 5, SCARF))
for s in (1, -1):
    body.append(cl.sweep("scarf_tail", [kp, kp + V((s * 0.03, -0.02, -0.06)), kp + V((s * 0.045, -0.03, -0.11))],
                         [0.026, 0.024, 0.0], 6, SCARF, scale=(1.0, 0.45), up=(0, -1, 0)))

# ================================================================== Head
head = [nl.head_shape("skull", HC, HR, JC, JR, 24, 13)]
head += nl.eye_pair(HC, HR, 0.086, 1.375, 0.062, IRIS, lid=0.12, lid_mat="M_Skin", lower=0.1, segs=12)
head += nl.brow_pair(HC, HR, 0.035, 0.14, 1.438, 1.44, 0.021, 0.014, HAIR)
head.append(nl.nose(HC, HR, 1.318, (0.04, 0.036, 0.036), mat="M_Skin__ffb4a0"))
head += nl.cheeks(JC, JR, 0.112, 1.3, 0.04)
head += nl.open_smile(JC, JR, 0.07, 1.262, 0.05, 0.016)
# a smudge of flour on his cheek
fp = cl.head_point(JC, JR, -0.128, 1.248, 0.002)
head.append(cl.ellipsoid("flour", fp, (0.03, 0.007, 0.018), 8, 3, FLOUR,
                         cl.frame(cl.head_normal(JC, JR, fp)) @ Matrix.Rotation(math.radians(20), 3, 'Y')))
head += nl.ears(HC, HR, 1.36, (0.032, 0.046, 0.064), segs=8)
# dark hair visible under the cap: back and sides
head.append(cl.dome("hair_back", HC + V((0, 0.02, 0.0)), (HR[0] * 1.04, HR[1] * 1.05, HR[2] * 1.03),
                    Matrix.Rotation(math.radians(-100), 3, 'X'), 0.42, 18, 4, HAIR))
for s in (1, -1):
    head.append(cl.ellipsoid("sideburn", V((s * 0.205, 0.0, 1.405)), (0.04, 0.07, 0.07), 8, 5, HAIR))
# puffy white baker's cap: band + billowing top with puffs
cb = V((0, 0.0, 1.49))
head.append(nl.lathe_z("cap_band", [(0.195, -0.032), (0.212, 0.0), (0.215, 0.07), (0.205, 0.075)], cb, 20, CAPW,
                       None, 40, (False, False)))
head.append(cl.ellipsoid("cap_puff", cb + V((0, 0.0, 0.14)), (0.25, 0.24, 0.1), 18, 8, CAPW))
for k in range(6):
    a = 2 * math.pi * (k + 0.5) / 6
    head.append(cl.ellipsoid("cap_pleat", cb + V((0.17 * math.cos(a), 0.165 * math.sin(a), 0.115)),
                             (0.1, 0.1, 0.075), 8, 5, CAPW))

# ================================================================== Arms (rolled sleeves); a baguette in the left hand
arm_l, AL = nl.soft_arm(1, SH_L, 0.24, 0.21, (0.075, 0.064, 0.054), spread=17.0, bend=14.0, sleeve=SHIRT,
                        sleeve_end=0.18, cuff_mat=SHIRT_D, cuff=0.026, ball_r=0.084, hand_s=0.125, fingers=3,
                        segs=9, ball_segs=12, rows=6)
g0 = AL.W + AL.d2 * 0.05 + V((0.0, -0.02, 0.0))
gd = V((0.08, 0.5, 1.0)).normalized()
bread = [g0 - gd * 0.26, g0 - gd * 0.1, g0 + gd * 0.1, g0 + gd * 0.24]
arm_l.append(cl.sweep("baguette", bread, [0.035, 0.046, 0.046, 0.034], 10, CRUST))
arm_l.append(cl.ellipsoid("baguette_end", g0 + gd * 0.24, (0.034, 0.034, 0.03), 8, 4, CRUST, nl.rot_to(gd)))
arm_l.append(cl.ellipsoid("baguette_end2", g0 - gd * 0.26, (0.035, 0.035, 0.03), 8, 4, CRUST, nl.rot_to(gd)))
vis = V((0.7, -0.7, 0.0))
nrm = (vis - gd * vis.dot(gd)).normalized()
for t in (-0.18, -0.05, 0.08, 0.2):
    c = g0 + gd * t
    arm_l.append(cl.ellipsoid("score", c + nrm * 0.042, (0.012, 0.006, 0.03), 6, 3, CRUMB,
                              cl.axes_matrix(gd.cross(nrm), nrm, gd) @ Matrix.Rotation(math.radians(-35), 3, 'Y')))
arm_r, AR = nl.soft_arm(-1, SH_R, 0.24, 0.21, (0.075, 0.064, 0.054), spread=17.0, bend=14.0, sleeve=SHIRT,
                        sleeve_end=0.18, cuff_mat=SHIRT_D, cuff=0.026, ball_r=0.084, hand_s=0.125, fingers=3,
                        segs=9, ball_segs=12, rows=6)
for parts, A in ((arm_l, AL), (arm_r, AR)):   # Breton stripes on the sleeves (bands along the arm)
    for o in parts[:3]:
        rw.set_mat_where(o, STRIPE, lambda c, n, A=A: int(round((A.S - c).dot(V((0, 0, 1))) / 0.04)) % 2 == 1)

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
