"""npc_villager_b: a lanky young farmer (origin at the feet, about 1.8 m with her straw hat, faces -Y).

Tall and thin with long legs: a wide yellow straw hat (red band, a daisy) pushed back on her head, two
puffy dark-brown pigtails with red ribbons, rosy cheeks and a wheat stalk at the corner of her grin, a green shirt with
rolled sleeves under blue denim overalls (crossed straps at the back, brass buttons, a bib pocket and
a red knee patch), a red neckerchief, brown work boots, and a little basket of apples in her right hand.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the hips; legs, overalls, neckerchief are part of it
    Head  pivot at the neck (inside the head, on the neck axis); hair, pigtails, hat
    ArmL  pivot at the left shoulder (rolled sleeve)
    ArmR  pivot at the right shoulder (rolled sleeve, carries the basket)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npclib as nl  # noqa: E402
from mathutils import Matrix  # noqa: E402

rw, cl, V = nl.rw, nl.cl, nl.V
ASSET = "npc_villager_b"
rw.reset()

SHIRT = "M_Fabric__5cb14b"
SHIRT_D = "M_Fabric__3f8a35"
DENIM = "M_Fabric__3d6cc0"
DENIM_D = "M_Fabric__2c5296"
PATCH = "M_Fabric__e2553a"
RED = "M_Fabric__dc3a32"
STRAW = "M_Fabric__ebc55a"
STRAW_D = "M_Fabric__c99a3a"
HAIR = rw.flat("HairBrown", "5b3522", 0.7)
IRIS = rw.flat("IrisGreenBright", "6cbf45", 0.4)
WHEAT = rw.flat("Wheat", "f0cf6a", 0.6)
APPLE = rw.flat("AppleRed", "e23b32", 0.4)
LEAF = rw.flat("LeafGreen", "4caf3a", 0.6)
DAISY = rw.flat("DaisyWhite", "fbfaf2", 0.6)
DAISY_C = rw.flat("DaisyCentre", "f5b828", 0.6)

HIP = V((0, 0.0, 0.95))
SH_L = V((0.205, 0.01, 1.35))
SH_R = V((-0.205, 0.01, 1.35))
NECK = V((0, 0.01, 1.43))
HC = V((0, 0.0, 1.535))
HR = (0.19, 0.18, 0.205)
JC = V((0, -0.052, 1.425))
JR = (0.136, 0.13, 0.1)

# ================================================================== Body
torso = nl.Profile([
    (0.86, 0.17, 0.14, 0.01),
    (0.95, 0.18, 0.145, 0.005),
    (1.05, 0.162, 0.128, 0.0),
    (1.15, 0.168, 0.13, -0.005),
    (1.25, 0.185, 0.136, -0.01),
    (1.32, 0.19, 0.13, 0.0),
    (1.37, 0.162, 0.11, 0.005),
    (1.41, 0.1, 0.08, 0.01),
    (1.44, 0.06, 0.055, 0.01),
])
body = []
trunk = torso.surface("trunk", 0.86, 1.44, 9, 20, 0.0, SHIRT)
rw.set_mat_where(trunk, DENIM, lambda c, n: c.z < 1.08)
body.append(trunk)
for s in (1, -1):
    body.append(nl.leg(s, (s * 0.1, 0.01, 0.92), (s * 0.11, 0.0, 0.13), 0.092, 0.08, DENIM, 10,
                       knee=(0, -0.012, 0), bulge=1.04))
    body.append(cl.torus("cuff", (s * 0.11, 0.0, 0.2), 0.082, 0.022, None, 12, 4, DENIM_D))
    body += nl.boot(s * 0.11, 0.0, "M_Leather__7a4a2a", "M_Rubber", h=0.18, r=0.078, toe=0.15, segs=10, lip=0.024)
# red patch on her left knee
kp = V((0.11, -0.085, 0.53))
body.append(cl.rbox("knee_patch", (0.085, 0.02, 0.09), kp, 0.008, PATCH,
                    Matrix.Rotation(math.radians(8), 3, 'Y'), segments=1))
for (dx, dz) in ((-0.035, 0.038), (0.035, 0.038), (-0.035, -0.038), (0.035, -0.038)):
    body.append(cl.sphere("stitch", kp + V((dx, -0.01, dz)), 0.007, 6, 3, rw.flat("Stitch", "fff3d6", 0.6)))
# overalls: bib with a pocket and brass buttons, a back panel, straps crossing at the back
bib = nl.arc_panel("bib", torso, [1.285, 1.22, 1.15, 1.08, 1.04], lambda z: 34.0 if z > 1.1 else 40.0, 270.0, 8,
                   0.012, DENIM)
nl.thicken(bib, 0.012)
body.append(bib)
pocket = nl.arc_panel("bib_pocket", torso, [1.23, 1.18, 1.13], 16.0, 270.0, 4, 0.024, DENIM_D)
nl.thicken(pocket, 0.008)
body.append(pocket)
back = nl.arc_panel("back_panel", torso, [1.17, 1.1, 1.04], 40.0, 90.0, 8, 0.012, DENIM)
nl.thicken(back, 0.012)
body.append(back)
for s in (1, -1):
    bp = torso.point(1.27, 270 + s * 30.0, 0.026)
    body.append(cl.cyl("button", bp, bp + (bp - V((0, 0, bp.z))).normalized() * 0.012, 0.02, 10, "M_Brass"))
    strap = [bp, V((s * 0.115, -0.07, 1.385)), V((s * 0.11, 0.04, 1.405)), V((s * 0.05, 0.12, 1.3)),
             V((-s * 0.06, 0.142, 1.19)), torso.point(1.16, 90 - s * 22.0, 0.016)]
    body.append(cl.sweep("strap", nl.smooth_path(strap, 9), 0.024, 6, DENIM_D, scale=(0.35, 1.0)))
# red neckerchief knotted at her left
body.append(cl.torus("kerchief", (0, 0.01, 1.4), 0.075, 0.025, None, 14, 4, RED))
kn = V((0.07, -0.05, 1.38))
body.append(cl.sphere("kerchief_knot", kn, 0.026, 8, 4, RED))
body.append(cl.sweep("kerchief_tail", [kn, kn + V((0.035, -0.025, -0.05)), kn + V((0.04, -0.03, -0.1))],
                     [0.024, 0.02, 0.0], 6, RED, scale=(1.0, 0.4), up=(0, -1, 0)))
body.append(cl.cyl("neck", (0, 0.01, 1.36), (0, 0.01, 1.5), 0.052, 12, "M_Skin"))

# ================================================================== Head
head = [nl.head_shape("skull", HC, HR, JC, JR, 24, 13)]
head += nl.eye_pair(HC, HR, 0.078, 1.528, 0.064, IRIS, lid=0.1, lid_mat="M_Skin", segs=12)
head += nl.brow_pair(HC, HR, 0.035, 0.125, 1.606, 1.614, 0.013, 0.016, HAIR)
head.append(nl.nose(HC, HR, 1.488, (0.028, 0.027, 0.025)))
head += nl.cheeks(JC, JR, 0.088, 1.44, 0.03)
head += nl.open_smile(JC, JR, 0.05, 1.416, 0.036, 0.008, tongue=True, teeth=True, nu=6,
                      inside=("MouthRose", "a8364c"))
head += nl.ears(HC, HR, 1.52, (0.026, 0.04, 0.055), segs=8)
# wheat stalk from the corner of her grin
w0 = cl.head_point(JC, JR, -0.05, 1.41, -0.004)
w1 = w0 + V((-0.085, -0.075, -0.035))
head.append(cl.cyl("wheat_stalk", w0, w1, 0.0065, 6, WHEAT))
wd = (w1 - w0).normalized()
head.append(cl.ellipsoid("wheat_ear", w1 + wd * 0.03, (0.013, 0.013, 0.035), 8, 4, WHEAT, nl.rot_to(wd)))
for k in range(2):
    sp = w1 + wd * (0.014 + 0.022 * k)
    for s in (1, -1):
        head.append(cl.ellipsoid("grain", sp + V((0, 0, s * 0.012)), (0.009, 0.008, 0.014), 6, 3, WHEAT,
                                 nl.rot_to(wd + V((0, 0, s * 0.8)))))
# dark-brown hair: cap, a straight fringe, two puffy pigtails with red ribbons
head.append(cl.dome("hair_cap", HC + V((0, 0.012, 0.012)), (HR[0] * 1.07, HR[1] * 1.08, HR[2] * 1.06),
                    Matrix.Rotation(math.radians(-36), 3, 'X'), 0.6, 20, 6, HAIR))
fr = [cl.head_point(HC, HR, x, 1.645 - 0.004 * abs(x) / 0.13, 0.016) for x in (-0.13, -0.065, 0.0, 0.065, 0.13)]
head.append(cl.sweep("fringe", fr, 0.03, 8, HAIR, scale=(1.0, 0.55), up=(0, 0, 1)))
for s in (1, -1):
    root = V((s * 0.17, 0.07, 1.47))
    tail = [root, root + V((s * 0.06, 0.03, -0.04)), root + V((s * 0.1, 0.05, -0.11)), root + V((s * 0.11, 0.06, -0.17))]
    head.append(cl.sweep("pigtail", nl.smooth_path(tail, 7), [0.045, 0.058, 0.062, 0.056, 0.046, 0.03, 0.0], 8, HAIR))
    for t in (-1, 1):
        head.append(cl.ellipsoid("ribbon", root + V((s * 0.02, -0.005 + 0.03 * t, 0.012)), (0.018, 0.032, 0.022), 8, 4,
                                 RED, Matrix.Rotation(math.radians(25 * t), 3, 'X')))
    head.append(cl.sphere("ribbon_knot", root + V((s * 0.022, 0, 0.01)), 0.017, 6, 3, RED))
# wide straw hat pushed back on her head: rounded crown, drooping brim, red band, a daisy
Rh = Matrix.Rotation(math.radians(-12), 3, 'X')
hb = V((0, 0.03, 1.655))
head.append(nl.lathe_z("hat_crown", [(0.16, -0.01), (0.158, 0.06), (0.15, 0.115), (0.128, 0.142), (0.08, 0.152),
                                     (0.0, 0.142)], hb, 18, STRAW, Rh, 40, (False, False)))
head.append(nl.lathe_z("hat_brim", [(0.14, 0.006), (0.25, -0.005), (0.33, -0.028), (0.36, -0.045), (0.352, -0.052),
                                    (0.32, -0.04), (0.24, -0.016), (0.14, -0.006)], hb, 22, STRAW, Rh, 40,
                       (False, False)))
head.append(nl.lathe_z("hat_band", [(0.161, 0.0), (0.166, 0.006), (0.163, 0.045), (0.157, 0.05)], hb, 18, RED, Rh, 40,
                       (False, False)))
dc = hb + Rh @ V((0.122, -0.117, 0.03))
dn = (Rh @ V((0.72, -0.69, 0.0))).normalized()
for k in range(6):
    a = 2 * math.pi * k / 6
    u = dn.cross(V((0, 0, 1))).normalized()
    v = dn.cross(u)
    off = u * math.cos(a) + v * math.sin(a)
    head.append(cl.ellipsoid("petal", dc + off * 0.028, (0.021, 0.007, 0.013), 6, 3, DAISY,
                             cl.axes_matrix(off, dn.cross(off), dn) @ Matrix.Rotation(math.radians(90), 3, 'Z')))
head.append(cl.sphere("daisy_centre", dc + dn * 0.005, 0.014, 6, 3, DAISY_C))

# ================================================================== Arms (rolled sleeves); basket of apples in her right hand
arm_l, AL = nl.soft_arm(1, SH_L, 0.29, 0.26, (0.058, 0.05, 0.042), spread=8.0, bend=12.0, sleeve=SHIRT,
                        sleeve_end=0.0, cuff_mat=SHIRT_D, cuff=0.022, ball_r=0.064, hand_s=0.11, fingers=3, segs=9,
                        ball_segs=12)
arm_r, AR = nl.soft_arm(-1, SH_R, 0.29, 0.26, (0.058, 0.05, 0.042), spread=13.0, bend=12.0, sleeve=SHIRT,
                        sleeve_end=0.0, cuff_mat=SHIRT_D, cuff=0.022, ball_r=0.064, hand_s=0.11, fingers=3, segs=9,
                        ball_segs=12)
grip = AR.W + AR.d2 * 0.075
bc = grip + V((-0.015, 0.0, -0.17))
arm_r.append(nl.lathe_z("basket", [(0.0, -0.06), (0.07, -0.06), (0.088, -0.05), (0.1, 0.02), (0.108, 0.05),
                                   (0.1, 0.055), (0.092, 0.03)], bc, 12, "M_WoodPlanks", None, 30, (False, False)))
arm_r.append(cl.torus("basket_rim", bc + V((0, 0, 0.052)), 0.104, 0.011, None, 12, 4, "M_WoodDark"))
handle = [bc + V((0, 0.095 * math.cos(math.radians(a)), 0.05 + 0.17 * math.sin(math.radians(a)))) for a in
          range(0, 181, 30)]
arm_r.append(cl.sweep("basket_handle", handle, 0.011, 6, "M_WoodDark"))
for (dx, dy, dz) in ((0.03, -0.035, 0.055), (-0.035, -0.01, 0.06), (0.01, 0.04, 0.05)):
    ap = bc + V((dx, dy, dz))
    arm_r.append(cl.sphere("apple", ap, 0.04, 8, 5, APPLE))
    arm_r.append(cl.cyl("apple_stem", ap + V((0, 0, 0.03)), ap + V((0.004, 0, 0.055)), 0.005, 5, "M_WoodDark"))
arm_r.append(cl.ellipsoid("apple_leaf", bc + V((0.04, -0.03, 0.1)), (0.022, 0.006, 0.012), 6, 3, LEAF,
                          Matrix.Rotation(math.radians(30), 3, 'Y')))

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
