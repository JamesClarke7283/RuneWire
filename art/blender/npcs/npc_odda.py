"""npc_odda: Master Artificer Odda (origin at the feet, about 1.6 m tall, faces -Y).

A stout older woman: big round brass goggles pushed up on her forehead, a grey hair bun (with a
pencil stuck through it), a leather apron over a teal shirt, a brass mechanical RIGHT arm fed by a
little copper boiler on her back, and a tool belt with wrenches, a hammer and pouches.

Nodes (ASSET_SPEC "NPCs"):
  Body   pivot at the hips; legs, boots, apron, tool belt and boiler are part of it
    Head  pivot at the neck (inside the head, on the neck axis)
    ArmL  pivot at the left shoulder (teal sleeve rolled to the elbow, bare forearm, mitten hand)
    ArmR  pivot at the right shoulder (brass mechanical arm with a claw hand)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npclib as nl  # noqa: E402
from mathutils import Matrix  # noqa: E402

rw, cl, V = nl.rw, nl.cl, nl.V
ASSET = "npc_odda"
rw.reset()

# ------------------------------------------------------------------ palette
TEAL = "M_Fabric__1fa898"
TEAL_D = "M_Fabric__157a73"
TROUSERS = "M_Fabric__4a3d63"
APRON = "M_Leather__8a5230"
STRAP = "M_Leather__5c3520"
HAIR = rw.flat("HairGrey", "cfd4df", 0.7)
HAIR_D = rw.flat("HairGreyShade", "a9b0c0", 0.7)
BROW = rw.flat("BrowGrey", "9aa1b2", 0.7)
IRIS = rw.flat("IrisGreen", "4fb866", 0.4)
LENS = rw.flat("GoggleLens", "8eeaf0", 0.06)
GAUGE = rw.glow("GaugeGlow", "5ff0d8", 2.5)
PENCIL = rw.flat("PencilYellow", "f4c430", 0.6)
ERASER = rw.flat("PencilEraser", "f07c8c", 0.7)
GRIP = rw.flat("GripRed", "d8433a", 0.5)

HIP = V((0, 0.0, 0.56))
SH_L = V((0.29, 0.012, 0.955))
SH_R = V((-0.29, 0.012, 0.955))
NECK = V((0, 0.012, 1.11))
HC = V((0, 0.0, 1.296))        # head centre
HR = (0.234, 0.216, 0.224)     # head radii
JC = V((0, -0.072, 1.205))     # chubby lower face (cheeks + mouth area)
JR = (0.168, 0.152, 0.102)

# ================================================================== Body
torso = nl.Profile([
    (0.46, 0.22, 0.19, 0.01),
    (0.52, 0.27, 0.225, 0.005),
    (0.60, 0.295, 0.245, 0.0),
    (0.70, 0.305, 0.255, -0.008),
    (0.80, 0.30, 0.25, -0.012),
    (0.88, 0.295, 0.235, -0.008),
    (0.94, 0.282, 0.21, 0.0),
    (0.99, 0.252, 0.18, 0.008),
    (1.03, 0.19, 0.14, 0.01),
    (1.065, 0.10, 0.09, 0.01),
])
body = []
trunk = torso.surface("trunk", 0.46, 1.065, 10, 20, 0.0, TEAL)
rw.set_mat_where(trunk, TROUSERS, lambda c, n: c.z < 0.64)
body.append(trunk)

# legs + boots with brass toe caps (safety first in the workshop)
for s in (1, -1):
    body.append(nl.leg(s, (s * 0.125, 0.01, 0.53), (s * 0.135, 0.0, 0.15), 0.112, 0.086, TROUSERS, 10,
                       knee=(s * 0.004, -0.008, 0)))
    body += nl.boot(s * 0.135, 0.0, "M_Leather", "M_Rubber", h=0.2, r=0.092, toe=0.155, toe_cap="M_Brass",
                    lip_mat=STRAP, segs=12)

# neck + rolled shirt collar
body.append(cl.cyl("neck", (0, 0.012, 0.98), (0, 0.012, 1.17), 0.075, 14, "M_Skin"))
body.append(cl.torus("collar", (0, 0.012, 1.055), 0.099, 0.031, None, 14, 4, TEAL_D, scale=(1.0, 0.95)))

# leather apron: bib + skirt wrapped on the torso, continuing straight down in front of the legs
apron_prof = nl.Profile(list(torso.L[3:]) + [
    (0.60, 0.298, 0.248, -0.002), (0.5, 0.292, 0.246, -0.008), (0.38, 0.288, 0.242, -0.014),
    (0.24, 0.29, 0.24, -0.02)])


def apron_half(z):
    if z > 0.8:
        return 36.0 + (0.96 - z) / 0.16 * 10.0
    if z > 0.62:
        return 46.0 + (0.8 - z) / 0.18 * 26.0
    return 72.0 - (0.62 - z) / 0.38 * 12.0


zs = [0.965, 0.9, 0.82, 0.74, 0.66, 0.58, 0.48, 0.38, 0.31, 0.25]


def hem(a, z, k):
    if z > zs[-1] + 1e-6:
        return 0.0
    u = (a - 270.0) / apron_half(z)
    return 0.045 * u ** 4


apron = nl.arc_panel("apron", apron_prof, zs, apron_half, 270.0, 10, 0.022, APRON, hem)
nl.thicken(apron, 0.016)
body.append(apron)
# pocket on the apron skirt, with a screwdriver poking out
pocket = nl.arc_panel("pocket", apron_prof, [0.47, 0.41, 0.35], lambda z: 19.0, 258.0, 5, 0.036, STRAP)
nl.thicken(pocket, 0.012)
body.append(pocket)
pk = apron_prof.point(0.46, 252.0, 0.042)
body.append(cl.cyl("screwdriver_grip", pk + V((0, 0.0, -0.03)), pk + V((0.0, -0.006, 0.07)), 0.017, 8, GRIP))
body.append(cl.cyl("screwdriver_shaft", pk + V((0, -0.006, 0.07)), pk + V((0, -0.01, 0.13)), 0.007, 6, "M_Steel"))
# bib rivets + straps up around the back of the neck
for s in (1, -1):
    a = 270.0 + s * 36.0
    p = apron_prof.point(0.95, a, 0.04)
    body.append(cl.rivet(p, 0.014, V((0.2 * s, -1, 0.2)), "M_Brass", 6))
    strap = [p + V((0, 0.01, 0.0)), V((s * 0.135, -0.095, 1.03)), V((s * 0.125, 0.0, 1.088)),
             V((s * 0.075, 0.09, 1.092)), V((0.0, 0.106, 1.088))]
    body.append(cl.sweep("strap", nl.smooth_path(strap, 7), 0.015, 6, STRAP, scale=(1.0, 0.55)))

# tool belt (over the apron) with a big brass buckle
belt = torso.surface("belt", 0.615, 0.69, 1, 20, 0.042, STRAP, caps=(False, False))
nl.thicken(belt, 0.022)
body.append(belt)
fy = torso.front_y(0.652, 0.0, 0.042)
body.append(cl.rbox("buckle", (0.11, 0.03, 0.088), (0, fy - 0.006, 0.652), 0.014, "M_Brass", segments=1))
body.append(cl.rbox("buckle_bar", (0.07, 0.03, 0.03), (0, fy - 0.014, 0.652), 0.008, STRAP, segments=1))


def wrench(origin, ring_r=0.024, length=0.17, mat="M_Steel", tilt=0.0):
    """Ring spanner hanging head-down from `origin` (the top ring hooks on the belt)."""
    o = V(origin)
    R = Matrix.Rotation(math.radians(tilt), 3, 'Y')
    parts = [cl.torus("wr_ring", o, ring_r, 0.0095, Matrix.Rotation(math.radians(90), 3, 'X'), 8, 4, mat)]
    bot = o + R @ V((0, 0, -length))
    parts.append(cl.rbox("wr_handle", (0.026, 0.012, length - ring_r * 1.6), o.lerp(bot, 0.5), 0.004, mat, R,
                         segments=1))
    jc = bot + R @ V((0, 0, -0.012))
    pts = [jc + R @ V((0.03 * math.sin(math.radians(-60 + 300 * k / 6)), 0, 0.03 * math.cos(math.radians(
        -60 + 300 * k / 6)))) for k in range(7)]
    parts.append(cl.sweep("wr_jaw", pts, 0.011, 6, mat, scale=(1.0, 0.55), up=(0, -1, 0)))
    return parts


# wrenches hanging at her front-right; a hammer at the front-left; pouches on the hips
for k, (a, ln, tilt) in enumerate(((236.0, 0.17, 8.0), (221.0, 0.14, -6.0))):
    body += wrench(torso.point(0.645, a, 0.072), 0.022 if k else 0.025, ln, "M_Steel", tilt)
hp = torso.point(0.66, 306.0, 0.07)
body.append(cl.cyl("hammer_handle", hp + V((0, 0, 0.03)), hp + V((0.01, -0.01, -0.2)), 0.014, 8, "M_WoodDark"))
body.append(cl.rbox("hammer_head", (0.11, 0.042, 0.042), hp + V((0.0, -0.005, 0.045)), 0.01, "M_Steel",
                    Matrix.Rotation(math.radians(-28), 3, 'Z'), segments=1))
for (a, w) in ((337.0, 0.09), (150.0, 0.1)):
    p = torso.point(0.6, a, 0.065)
    n = (p - V((0, 0, 0.6))).normalized()
    Rm = cl.frame(n)
    body.append(cl.rbox("pouch", (w, 0.055, 0.09), p, 0.02, STRAP, Rm, segments=1))
    body.append(cl.rbox("pouch_flap", (w * 1.04, 0.06, 0.035), p + V((0, 0, 0.035)) + n * 0.006, 0.01, APRON, Rm,
                        segments=1))
    body.append(cl.rivet(p + n * 0.034 + V((0, 0, 0.022)), 0.009, n, "M_Brass", 6))

# right shoulder socket (the mechanical arm plugs in here) + little copper boiler on her back feeding it
body.append(cl.torus("socket", SH_R + V((0.03, 0, 0)), 0.088, 0.02, nl.rot_to((1, 0, 0)), 12, 4, "M_Brass"))
bc = V((0.0, 0.31, 0.83))
body.append(cl.rbox("boiler_bracket", (0.16, 0.08, 0.2), (0, 0.235, 0.83), 0.02, "M_DarkMetal", segments=1))
body.append(nl.lathe_z("boiler", [(0.0, -0.17), (0.085, -0.155), (0.118, -0.09), (0.118, -0.06), (0.106, -0.05),
                                  (0.106, 0.05), (0.118, 0.06), (0.118, 0.09), (0.085, 0.155), (0.0, 0.17)],
                       bc, 12, "M_Copper", None, 40, (False, False)))
rw.set_mat_where(body[-1], "M_Brass", lambda c, n: abs(c.z - bc.z) > 0.055)
body.append(cl.cyl("boiler_stack", bc + V((0.04, 0.0, 0.15)), bc + V((0.05, 0.02, 0.27)), 0.022, 8, "M_DarkMetal"))
body.append(cl.cyl("boiler_stack_lip", bc + V((0.05, 0.02, 0.255)), bc + V((0.052, 0.022, 0.285)), 0.031, 8,
                   "M_Brass"))
gp = bc + V((0.0, 0.112, 0.0))
body.append(cl.cyl("gauge_back", gp - V((0, 0.01, 0)), gp + V((0, 0.006, 0)), 0.042, 10, "M_Brass"))
body.append(cl.cyl("gauge_face", gp, gp + V((0, 0.01, 0)), 0.032, 10, GAUGE))
body.append(cl.sweep("steam_pipe", nl.smooth_path([bc + V((-0.08, -0.05, 0.08)), V((-0.2, 0.2, 0.98)),
                                                   V((-0.25, 0.14, 0.99)), V((-0.26, 0.1, 0.955))], 9),
                     0.018, 8, "M_Copper"))

# ================================================================== Head
head = [nl.head_shape("skull", HC, HR, JC, JR, 24, 13)]
head += nl.eye_pair(HC, HR, 0.088, 1.29, 0.066, IRIS, lid=0.12, lid_mat="M_Skin", lid_tilt=-4.0, segs=12)
head += nl.brow_pair(HC, HR, 0.038, 0.145, 1.37, 1.366, 0.021, 0.02, BROW)
head.append(nl.nose(HC, HR, 1.245, (0.04, 0.035, 0.036)))
head += nl.cheeks(JC, JR, 0.112, 1.222, 0.036)
head += nl.open_smile(JC, JR, 0.066, 1.198, 0.058, 0.01)
# grey hair: cap tilted back, side puffs over the ears, a big bun with a pencil through it
head.append(cl.dome("hair_cap", HC + V((0, 0.012, 0.012)), (HR[0] * 1.06, HR[1] * 1.07, HR[2] * 1.07),
                    Matrix.Rotation(math.radians(-40), 3, 'X'), 0.6, 20, 6, HAIR))
for s in (1, -1):
    head.append(cl.ellipsoid("hair_puff", HC + V((s * 0.2, 0.05, 0.02)), (0.062, 0.105, 0.105), 8, 5, HAIR,
                             Matrix.Rotation(math.radians(-15 * s), 3, 'Y')))
head.append(cl.ellipsoid("bun", V((0, 0.05, 1.512)), (0.095, 0.09, 0.08), 14, 8, HAIR))
# a few swoopy locks peeking out under the goggle strap
for s in (1, -1):
    for (x0, x1, z0, z1) in ((0.06, 0.14, 1.392, 1.35), (0.15, 0.2, 1.37, 1.31)):
        a = cl.head_point(HC, HR, s * x0, z0, 0.004)
        b = cl.head_point(HC, HR, s * x1, z1, 0.004)
        m = cl.head_point(HC, HR, s * (x0 + x1) / 2, (z0 + z1) / 2 + 0.006, 0.014)
        head.append(cl.sweep("lock", cl.bezier(a, m, b, 5), [0.02, 0.022, 0.017, 0.01, 0.0], 6, HAIR,
                             scale=(1.0, 0.6), up=(0, 0, 1)))
p0, p1 = V((-0.13, 0.08, 1.47)), V((0.12, 0.0, 1.57))
d = (p1 - p0).normalized()
head.append(cl.cyl("pencil", p0, p1, 0.012, 6, PENCIL, smooth_angle=20))
head.append(cl.sweep("pencil_tip", [p1, p1 + d * 0.032], [0.012, 0.0], 6, "M_WoodPlanks"))
head.append(cl.cyl("pencil_band", p0 - d * 0.006, p0 + d * 0.012, 0.0135, 6, "M_Brass"))
head.append(cl.cyl("pencil_eraser", p0 - d * 0.024, p0 - d * 0.005, 0.0125, 6, ERASER))

# big brass goggles pushed up on the forehead, tilted up; leather strap around the head
GZ = 1.43
for s in (1, -1):
    c = cl.head_point(HC, HR, s * 0.084, GZ, 0.012)
    n = (cl.head_normal(HC, HR, c) + V((0, -0.25, 0.3))).normalized()
    Rg = nl.rot_to(n)
    head.append(nl.lathe_z("goggle_cup", [(0.05, -0.022), (0.062, -0.012), (0.068, 0.01), (0.07, 0.024),
                                          (0.063, 0.034), (0.052, 0.032)], c, 14, "M_Brass", Rg, 40, (True, False)))
    head.append(cl.dome("goggle_lens", c + n * 0.006, (0.054, 0.054, 0.03), Rg, 0.42, 14, 2, LENS))
head.append(cl.sweep("goggle_bridge", [cl.head_point(HC, HR, 0.032, GZ - 0.012, 0.042),
                                        cl.head_point(HC, HR, 0.0, GZ - 0.006, 0.05),
                                        cl.head_point(HC, HR, -0.032, GZ - 0.012, 0.042)], 0.012, 6, "M_Brass"))
band = []
for k in range(13):
    a = math.radians(-90 + 360 * k / 12)
    band.append(V((HC.x + (HR[0] + 0.013) * math.cos(a) * 1.03, HC.y + (HR[1] + 0.016) * math.sin(a) * 1.05,
                   1.41 - 0.06 * (math.sin(a) + 1) * 0.5)))
head.append(cl.sweep("goggle_strap", band, 0.021, 6, STRAP, scale=(1.0, 0.45), up=(0, 0, 1)))

# ================================================================== ArmL (fleshy, rolled sleeve, leather bracer)
arm_l, AL = nl.soft_arm(1, SH_L, 0.25, 0.215, (0.07, 0.06, 0.05), spread=15.0, bend=16.0, sleeve=TEAL,
                        sleeve_end=0.12, cuff_mat=TEAL_D, cuff=0.024, ball_r=0.082, hand_s=0.122, fingers=3, segs=9,
                        ball_segs=12)
arm_l.append(cl.torus("bracer", AL.W - AL.d2 * 0.05, 0.054, 0.017, nl.rot_to(AL.d2), 12, 4, STRAP))

# ================================================================== ArmR (brass mechanical arm)
A = nl.arm_frame(-1, SH_R, 0.25, 0.215, spread=15.0, bend=16.0)
S, E, W, d1, d2 = A.S, A.E, A.W, A.d1, A.d2
out = V((-1, 0.15, 0.0)).normalized()   # outward side of the right arm
arm_r = [cl.sphere("m_ball", S, 0.082, 14, 7, "M_Brass")]
Rp = nl.rot_to((-0.45, 0, 1))
pc = S + V((-0.006, 0.0, 0.012))
arm_r.append(cl.dome("m_pauldron", pc, (0.106, 0.102, 0.1), Rp, 0.5, 16, 4, "M_Brass"))
for k in range(4):
    a = math.radians(-70 + 140 * k / 3)
    rp = pc + Rp @ V((0.1 * math.cos(a), 0.096 * math.sin(a), 0.012))
    arm_r.append(cl.rivet(rp, 0.01, (rp - pc).normalized(), "M_Copper", 6))
arm_r.append(cl.cyl("m_upper", S + d1 * 0.05, E, 0.05, 14, "M_Brass"))
arm_r.append(cl.torus("m_band", S.lerp(E, 0.62), 0.054, 0.013, nl.rot_to(d1), 14, 4, "M_Copper"))
pa, pb = S + d1 * 0.08 + out * 0.058, E - d1 * 0.03 + out * 0.05
arm_r.append(cl.cyl("m_piston", pa, pa.lerp(pb, 0.55), 0.021, 8, "M_Copper"))
arm_r.append(cl.cyl("m_piston_rod", pa.lerp(pb, 0.5), pb, 0.0105, 6, "M_Steel"))
arm_r.append(cl.sphere("m_piston_pin", pb, 0.016, 6, 3, "M_Brass"))
arm_r.append(cl.sphere("m_elbow", E, 0.06, 12, 6, "M_Steel"))
g = rw.gear("m_elbow_gear", 0.054, 7, 0.016, 0.02, 0.0, (0, 0, 0), (0, 0, 0), "M_Brass", 0.0)
g.data.transform(Matrix.Translation(E + out * 0.052) @ nl.rot_to(out).to_4x4())
arm_r.append(g)
arm_r.append(cl.sphere("m_gear_cap", E + out * 0.064, 0.017, 6, 3, "M_Copper"))
arm_r.append(cl.sweep("m_fore", [E + d2 * 0.03, E + d2 * 0.1, E + d2 * 0.17, W - d2 * 0.015],
                      [0.05, 0.058, 0.066, 0.068], 14, "M_Brass"))
fwd = (V((0, -1, 0)) - d2 * V((0, -1, 0)).dot(d2)).normalized()
gpos = E.lerp(W, 0.55) + fwd * 0.058 + out * 0.01
arm_r.append(cl.cyl("m_gauge_rim", gpos - fwd * 0.006, gpos + fwd * 0.008, 0.027, 12, "M_Copper"))
arm_r.append(cl.cyl("m_gauge", gpos + fwd * 0.004, gpos + fwd * 0.012, 0.02, 12, GAUGE))
for v in (out, -out):
    arm_r.append(cl.rivet(E.lerp(W, 0.35) + v * 0.062, 0.01, v, "M_Copper", 6))
arm_r.append(cl.torus("m_wrist", W, 0.066, 0.016, nl.rot_to(d2), 14, 4, "M_Steel"))
# claw hand: brass palm block, three jointed steel fingers and a thumb, curled slightly inward
hd, hn, ht = cl._hand_axes(d2, (1, 0, 0), (0, -1, 0))
Mh = cl.axes_matrix(ht, hn, hd)
hc = W + hd * 0.055
arm_r.append(cl.rbox("m_palm", (0.088, 0.062, 0.085), hc, 0.022, "M_Brass", Mh, segments=1))
for k in range(3):
    off = (k - 1) * 0.029
    b = hc + hd * 0.04 + ht * off
    k1 = b + hd * 0.046 + hn * 0.01
    tip = k1 + (hd * 0.65 + hn * 0.6).normalized() * 0.042
    arm_r.append(cl.capsule("m_f1", b, k1, 0.0155, 0.014, 6, 2, "M_Steel"))
    arm_r.append(cl.capsule("m_f2", k1, tip, 0.0135, 0.009, 6, 2, "M_Steel"))
tb = hc + ht * 0.048 - hd * 0.01 + hn * 0.006
tk = tb + (ht * 0.55 + hd * 0.7).normalized() * 0.042
arm_r.append(cl.capsule("m_t1", tb, tk, 0.016, 0.013, 6, 2, "M_Steel"))
arm_r.append(cl.capsule("m_t2", tk, tk + (hd + hn * 0.7).normalized() * 0.034, 0.013, 0.009, 6, 2, "M_Steel"))

# ================================================================== assemble + QA
nl.assemble(body, HIP, head, NECK, arm_l, SH_L, arm_r, SH_R)
nl.finish(ASSET)
