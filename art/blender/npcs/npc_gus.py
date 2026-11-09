"""npc_gus: Gus Sprocket, the tinker vendor (origin at the feet, about 1.3 m tall, faces -Y).

A small barrel-bodied brass robot balancing on a single chunky wheel: copper barrel hoops, a chest
dial, a coin slot and three buttons, a big wind-up key on his back, a can-shaped head with one big
round porthole eye (glowing teal iris, brass lids for a friendly squint), a grille smile, and a
tiny top hat worn at a jaunty angle. Spindly steel arms end in three-finger pincers.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the "hips" (barrel bottom); the wheel, fork and mudguard are part of it
    Head  pivot at the neck (inside the head bottom, on the neck axis)
    ArmL  pivot at the left shoulder ball
    ArmR  pivot at the right shoulder ball
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npclib as nl  # noqa: E402
from mathutils import Matrix  # noqa: E402

rw, cl, V = nl.rw, nl.cl, nl.V
ASSET = "npc_gus"
rw.reset()

ORANGE = "M_PaintedMetal__ec7a22"
HAT = "M_Fabric__2c2836"
HAT_BAND = "M_Fabric__e2412f"
BOW = "M_Fabric__d8302c"
EYE_GLOW = rw.glow("GusEyeGlow", "62f2e0", 2.2)
LENS = rw.flat("GusLens", "1d3b45", 0.08)
DIAL = rw.glow("DialGlow", "8ff7d0", 1.6)
SLOT = rw.flat("SlotDark", "1b1820", 0.6)
BTN = [rw.flat("BtnRed", "e2483c", 0.4), rw.flat("BtnYellow", "f2c230", 0.4), rw.flat("BtnGreen", "52c35a", 0.4)]

HIP = V((0, 0, 0.38))
NECK = V((0, 0, 0.9))
SH_L = V((0.288, 0.0, 0.73))
SH_R = V((-0.288, 0.0, 0.73))

# ================================================================== Body: wheel, fork, barrel
body = []
WC = V((0, 0.0, 0.16))           # wheel centre
AX = nl.rot_to((1, 0, 0))        # wheel axis = X
tyre = nl.lathe_z("tyre", [(0.085, -0.055), (0.125, -0.06), (0.145, -0.046), (0.152, -0.02), (0.152, 0.02),
                           (0.145, 0.046), (0.125, 0.06), (0.085, 0.055)], WC, 20, "M_Rubber", AX, 40,
                  (False, False))
body.append(tyre)
for k in range(12):   # chunky tread blocks
    a = 2 * math.pi * (k + 0.5) / 12
    rdir = V((0, math.cos(a), math.sin(a)))
    blk = rw.box("tread", (0.1, 0.032, 0.022), mat="M_Rubber")
    blk.data.transform(cl.Matrix.Translation(WC + rdir * 0.149) @
                       cl.axes_matrix(V((1, 0, 0)), rdir.cross(V((1, 0, 0))), rdir).to_4x4())
    body.append(blk)
for s in (1, -1):
    body.append(nl.lathe_z("hub", [(0.0, 0.0), (0.075, 0.0), (0.082, 0.012), (0.06, 0.03), (0.03, 0.036),
                                   (0.0, 0.036)], WC + V((s * 0.05, 0, 0)), 14, "M_Brass",
                           nl.rot_to((s, 0, 0)), 40, (False, False)))
    for k in range(4):   # hub bolts
        a = 2 * math.pi * (k + 0.5) / 4
        body.append(cl.rivet(WC + V((s * 0.0835, 0.048 * math.cos(a), 0.048 * math.sin(a))), 0.009, (s, 0, 0),
                             "M_Steel", 6))
body.append(cl.cyl("axle", WC + V((-0.12, 0, 0)), WC + V((0.12, 0, 0)), 0.022, 10, "M_Steel"))
for s in (1, -1):
    body.append(cl.sphere("axle_cap", WC + V((s * 0.12, 0, 0)), 0.03, 10, 5, "M_Brass"))
    fork = nl.smooth_path([WC + V((s * 0.12, 0, 0)), V((s * 0.13, 0.0, 0.26)), V((s * 0.115, 0.0, 0.37))], 6)
    body.append(cl.sweep("fork", fork, [0.024, 0.024, 0.022, 0.022, 0.024, 0.026], 8, "M_DarkMetal"))
# signal-orange mudguard over the wheel
guard = [WC + V((0, 0.18 * math.cos(math.radians(a)), 0.18 * math.sin(math.radians(a))))
         for a in range(20, 165, 18)]
body.append(cl.sweep("mudguard", guard, 0.075, 10, ORANGE, scale=(1.0, 0.22), up=(1, 0, 0)))
# barrel: lathe with copper hoops bumped into the profile
prof = [(0.0, 0.36), (0.15, 0.362), (0.212, 0.376), (0.236, 0.395),
        (0.25, 0.402), (0.25, 0.436), (0.24, 0.443),
        (0.262, 0.51), (0.272, 0.575),
        (0.286, 0.58), (0.286, 0.62), (0.272, 0.625),
        (0.266, 0.69), (0.25, 0.758),
        (0.26, 0.764), (0.26, 0.8), (0.247, 0.806),
        (0.224, 0.836), (0.188, 0.86), (0.0, 0.866)]
barrel = nl.lathe_z("barrel", prof, (0, 0, 0), 20, "M_Brass", None, 40, (False, False))
hoops = ((0.398, 0.44), (0.577, 0.623), (0.761, 0.804))
rw.set_mat_where(barrel, "M_Copper", lambda c, n: any(a <= c.z <= b for a, b in hoops))
rw.set_mat_where(barrel, "M_DarkMetal", lambda c, n: c.z < 0.39 and n.z < -0.5)
body.append(barrel)
for z in (0.42, 0.6, 0.783):   # rivets on the hoops (front half only)
    r = 0.25 if z < 0.5 else (0.286 if z < 0.7 else 0.26)
    for a in (232.0, 270.0, 308.0, 110.0, 70.0):
        d = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        body.append(cl.rivet(V((0, 0, z)) + d * r, 0.011, d, "M_Brass", 6))
# chest: glowing dial, coin slot plate, three buttons
fp = lambda x, z, off=0.0: V((x, -math.sqrt(max(0.0, (0.268 + off) ** 2 - x * x)), z))  # noqa: E731
dc = fp(0.105, 0.69, 0.004)
dn = V((dc.x, dc.y, 0)).normalized()
body.append(cl.cyl("dial_bezel", dc - dn * 0.012, dc + dn * 0.018, 0.056, 14, "M_Copper"))
body.append(cl.cyl("dial_face", dc + dn * 0.012, dc + dn * 0.022, 0.044, 14, DIAL))
body.append(cl.rbox("dial_needle", (0.008, 0.006, 0.036), dc + dn * 0.024 + V((0.008, 0, 0.01)), 0.002, SLOT,
                    nl.rot_to((0.45, 0, 1)), segments=1))
sc = fp(-0.1, 0.7, 0.004)
sn = V((sc.x, sc.y, 0)).normalized()
body.append(cl.rbox("slot_plate", (0.09, 0.022, 0.07), sc, 0.012, ORANGE, cl.frame(sn), segments=1))
body.append(cl.rbox("coin_slot", (0.05, 0.02, 0.012), sc + sn * 0.012, 0.004, SLOT, cl.frame(sn), segments=1))
for k, x in enumerate((-0.06, 0.0, 0.06)):
    p = fp(x, 0.51, 0.004)
    n = V((p.x, p.y, 0)).normalized()
    body.append(cl.cyl("btn_ring", p - n * 0.01, p + n * 0.008, 0.022, 10, "M_Steel"))
    body.append(cl.ellipsoid("btn", p + n * 0.008, (0.017, 0.017, 0.011), 8, 4, BTN[k], nl.rot_to(n)))
# back: big wind-up key + a little exhaust stack
kb = V((0, 0.268, 0.62))
body.append(cl.cyl("key_shaft", kb - V((0, 0.02, 0)), kb + V((0, 0.09, 0)), 0.017, 8, "M_Steel"))
body.append(cl.cyl("key_collar", kb + V((0, -0.005, 0)), kb + V((0, 0.025, 0)), 0.035, 12, "M_Copper"))
kc = kb + V((0, 0.1, 0))
for s in (1, -1):
    body.append(cl.ellipsoid("key_wing", kc + V((s * 0.075, 0, 0.0)), (0.07, 0.016, 0.055), 14, 5, "M_Brass"))
body.append(cl.sphere("key_hub", kc, 0.03, 10, 5, "M_Brass"))
body.append(cl.sweep("exhaust", nl.smooth_path([V((0.17, 0.17, 0.76)), V((0.21, 0.21, 0.84)), V((0.215, 0.22, 0.92))], 5),
                     0.026, 8, "M_DarkMetal"))
body.append(cl.cyl("exhaust_cap", V((0.215, 0.22, 0.905)), V((0.215, 0.22, 0.945)), 0.036, 10, "M_Brass"))
# shoulder sockets + neck
for sh, s in ((SH_L, 1), (SH_R, -1)):
    body.append(cl.torus("socket", sh - V((s * 0.025, 0, 0)), 0.058, 0.016, nl.rot_to((1, 0, 0)), 14, 4, "M_Copper"))
body.append(cl.cyl("neck", (0, 0, 0.84), (0, 0, 0.93), 0.068, 12, "M_Steel"))
# a red bow tie at the barrel's collar (he is a shopkeeper, after all)
bt = V((0, -0.226, 0.842))
Rb = Matrix.Rotation(math.radians(-14), 3, 'X')
for s in (1, -1):
    body.append(cl.ellipsoid("bow_wing", bt + V((s * 0.046, 0.006, 0.0)), (0.048, 0.02, 0.034), 10, 5, BOW,
                             Rb @ Matrix.Rotation(math.radians(8 * s), 3, 'Y')))
body.append(cl.ellipsoid("bow_knot", bt + V((0, -0.008, 0)), (0.02, 0.02, 0.022), 8, 4, BOW, Rb))
body.append(cl.torus("neck_ring", (0, 0, 0.868), 0.084, 0.016, None, 16, 4, "M_DarkMetal"))

# ================================================================== Head: can with a porthole eye + top hat
head = []
hprof = [(0.0, 0.878), (0.12, 0.878), (0.175, 0.89), (0.193, 0.912), (0.197, 0.945), (0.197, 1.1),
         (0.188, 1.158), (0.162, 1.203), (0.11, 1.233), (0.0, 1.24)]
head.append(nl.lathe_z("head_can", hprof, (0, 0, 0), 20, "M_Brass", None, 40, (False, False)))
EZ = 1.07
EP = V((0, -0.197, EZ))
FW = V((0, -1, 0))
RE = nl.rot_to(FW)
# porthole housing (brass) with a rolled copper rim, dark lens, glowing iris ring, pupil, highlight
head.append(nl.lathe_z("eye_housing", [(0.112, -0.04), (0.112, 0.012), (0.12, 0.022), (0.114, 0.038),
                                       (0.1, 0.04), (0.094, 0.03)], EP, 22, "M_Copper", RE, 40, (False, False)))
head.append(cl.dome("eye_lens", EP + FW * 0.012, (0.096, 0.096, 0.028), RE, 0.5, 20, 2, LENS))
head.append(cl.torus("eye_iris", EP + FW * 0.034, 0.05, 0.016, RE, 18, 4, EYE_GLOW))
head.append(cl.dome("eye_pupil", EP + FW * 0.03, (0.034, 0.034, 0.012), RE, 0.5, 12, 1, SLOT))
head.append(cl.ellipsoid("eye_shine", EP + V((0.036, -0.046, 0.036)), (0.016, 0.006, 0.016), 6, 3,
                         rw.glow("GusShine", "ffffff", 1.5)))
# brass lids: a friendly squint (upper lid tilted, lower lid pushed up like a smile)
Fe = cl.frame(FW)
head.append(cl.dome("eye_lid", EP + FW * 0.004, (0.117, 0.052, 0.117), Fe, 0.27, 20, 2, "M_DarkMetal", tilt=-9.0))
head.append(cl.dome("eye_llid", EP + FW * 0.004, (0.117, 0.052, 0.117), Fe @ Matrix.Rotation(math.pi, 3, 'Y'), 0.2,
                    20, 2, "M_DarkMetal"))
# grille smile under the eye
MC, MR = V((0, 0, 0.94)), (0.196, 0.196, 0.6)
head.append(nl.face_patch("grille", MC, MR, -1.0, 1.0, 0.0, 1.0, 0.078, 0.94, 0.026, 0.014, 0.003, SLOT, 8, 2))
for x in (-0.042, -0.014, 0.014, 0.042):
    p = cl.head_point(MC, MR, x, 0.94 + 0.014 * (x / 0.078) ** 2 - 0.011, 0.004)
    head.append(cl.rbox("grille_bar", (0.008, 0.012, 0.03), p, 0.003, "M_Brass", segments=1))
# ear bolts with little copper caps
for s in (1, -1):
    head.append(cl.cyl("ear", V((s * 0.19, 0, 1.05)), V((s * 0.225, 0, 1.05)), 0.045, 12, "M_Brass"))
    head.append(cl.sphere("ear_cap", V((s * 0.228, 0, 1.05)), 0.026, 8, 4, "M_Copper"))
# tiny top hat at a jaunty angle (tipped toward his left), with a red band and a little gear
Rh = Matrix.Rotation(math.radians(-14), 3, 'Y') @ Matrix.Rotation(math.radians(-6), 3, 'X')
hb = V((0.03, 0.005, 1.236))
head.append(nl.lathe_z("hat_brim", [(0.0, -0.005), (0.104, -0.005), (0.11, 0.004), (0.1, 0.011), (0.0, 0.011)],
                       hb, 18, HAT, Rh, 40, (False, False)))
head.append(nl.lathe_z("hat_crown", [(0.07, 0.006), (0.067, 0.064), (0.074, 0.122), (0.0, 0.127)], hb, 16, HAT, Rh,
                       40, (True, False)))
head.append(nl.lathe_z("hat_band", [(0.0705, 0.01), (0.0715, 0.013), (0.0705, 0.04), (0.0695, 0.043)], hb, 16,
                       HAT_BAND, Rh, 40, (False, False)))
gpos = hb + Rh @ V((0.0, -0.074, 0.027))
g = rw.gear("hat_gear", 0.025, 6, 0.008, 0.008, 0.0, (0, 0, 0), (0, 0, 0), "M_Brass", 0.0)
g.data.transform(Matrix.Translation(gpos) @ (Rh @ nl.rot_to(FW)).to_4x4())
head.append(g)


# ================================================================== Arms: spindly rods with 3-finger pincers
def robo_arm(side, S):
    A = nl.arm_frame(side, S, 0.2, 0.19, spread=12.0, bend=20.0)
    S, E, W, d1, d2 = A.S, A.E, A.W, A.d1, A.d2
    parts = [cl.sphere("sh_ball", S, 0.05, 12, 6, "M_Brass")]
    parts.append(cl.cyl("upper", S + d1 * 0.03, E, 0.018, 8, "M_Steel"))
    parts.append(cl.cyl("upper_sleeve", S + d1 * 0.04, S + d1 * 0.1, 0.026, 8, "M_Copper"))
    parts.append(cl.sphere("elbow", E, 0.032, 10, 5, "M_Brass"))
    parts.append(cl.cyl("fore", E, W, 0.017, 8, "M_Steel"))
    parts.append(cl.cyl("fore_sleeve", E.lerp(W, 0.55), W - d2 * 0.012, 0.025, 8, "M_Copper"))
    parts.append(cl.sphere("wrist", W, 0.028, 10, 5, "M_Brass"))
    base = W + d2 * 0.035
    parts.append(cl.cyl("palm", W + d2 * 0.008, base, 0.036, 10, "M_Brass"))
    u = (V((0, -1, 0)) - d2 * V((0, -1, 0)).dot(d2)).normalized()
    v = d2.cross(u)
    for k in range(3):
        a = 2 * math.pi * k / 3
        rd = u * math.cos(a) + v * math.sin(a)
        b = base + rd * 0.024
        k1 = b + (d2 * 0.75 + rd * 0.5).normalized() * 0.05
        tip = k1 + (d2 * 0.8 - rd * 0.6).normalized() * 0.048
        parts.append(cl.capsule("f1", b, k1, 0.012, 0.011, 6, 2, "M_Steel"))
        parts.append(cl.sphere("knuckle", k1, 0.0135, 6, 3, "M_Brass"))
        parts.append(cl.capsule("f2", k1, tip, 0.011, 0.007, 6, 2, "M_Steel"))
    return parts


arm_l = robo_arm(1, SH_L)
arm_r = robo_arm(-1, SH_R)

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
