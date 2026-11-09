"""enemy_cultist: Choir Cultist of the Hollow Choir (origin at the feet, ~1.9 m tall).

A hooded cultist in a long crimson robe that opens at the front over a dark under-robe embroidered
with a column of glowing violet runes, a pointed shoulder mantle with brass trim, a deep hood framing
a white porcelain mask (glowing eye slits, a small round "singing" mouth, painted violet lines),
a leather belt with a rune buckle, pouches and a glowing teal vial, pale clawed hands and a rune
staff topped by a violet crystal held in a brass crescent.
The boss "The Hollow Archon" reuses this model scaled x2.3, so the silhouette is kept bold:
broad pointed mantle, tall hood, flared ragged robe, glowing eyes and crystal.

Hierarchy (spec Batch B):
  Body            pivot at the hips (0, 0, 1.0); the robe reaches the ground
    Head          pivot at the neck; hood, mask, eyes
    ArmL          pivot at the left shoulder; sleeve and clawed hand hang down
    ArmR          pivot at the right shoulder; sleeve, hand gripping the staff
      Staff       origin at the grip (centre of the right fist)
        CastPoint empty at the centre of the staff's crystal head

Staff angle: the game rotates only ArmR (rotation.x -0.2 rad idle, about -1.7 rad at the cast
release) and the staff rides along rigidly. A vertical staff would swing its crystal behind the head
when casting, so the staff leans ~48 deg forward at rest: the crystal sits ahead of the face while
idle and sweeps up over the hood at the moment the orb is released (see the RWCAST lines).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "parts"))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import magiclib as ml  # noqa: E402
import partlib as pl  # noqa: E402
from mathutils import Matrix, Vector as V  # noqa: E402

ASSET = "enemy_cultist"
rw.reset()

# ---------------------------------------------------------------- materials
ROBE = "M_Fabric__8c1c2e"
DARK = "M_Fabric__2a2233"
LINING = "M_Fabric__4a1420"          # sleeve linings: crimson in shadow, not a black hole
TRIM = "M_Brass"
LEATHER = "M_Leather__6b3f2a"
SKIN = "M_Skin__b9aecf"
WOOD = "M_WoodDark"
RUNE = "M_RuneGlow"
CRYSTAL = "M_Crystal__b066ff"
pl.tint_emission(CRYSTAL, "b066ff", 2.4)
porcelain = rw.flat("Porcelain", "f4efe6", 0.25)
paint = rw.flat("MaskPaint", "7d2fae", 0.5)
eye_glow = rw.glow("CultistEye", "e57cff", 6.0)
slit_dark = rw.flat("MaskSlit", "1d1024", 0.8)
void = rw.flat("HoodVoid", "120b18", 0.95)
nails = rw.flat("CultistNails", "2b1f36", 0.5)
vial_glow = rw.glow("VialTeal", "4ff0d8", 2.5)

# ---------------------------------------------------------------- pivots
P_BODY = V((0.0, 0.0, 1.0))
P_NECK = V((0.0, 0.0, 1.52))
P_SHO = {1: V((0.24, 0.02, 1.44)), -1: V((-0.24, 0.02, 1.44))}
GRIP = V((-0.33, -0.17, 1.02))
STAFF_DIR = V((0.08, -0.743, 0.669)).normalized()     # toward the crystal head, ~48 deg forward of vertical

# ======================================================================== Body
body = []
# dark under-robe with a ragged hem touching the ground
under, _ = ml.robe_surface("under_robe", [(1.06, 0.19, 0.155, 0.0), (0.85, 0.232, 0.183, 0.0),
                                          (0.6, 0.288, 0.224, 0.005), (0.35, 0.34, 0.262, 0.01),
                                          (0.16, 0.38, 0.29, 0.015), (0.085, 0.395, 0.3, 0.015)],
                           segs=24, folds=10, amp=(0.01, 0.035), mat=DARK, inner=DARK, thick=0.015,
                           hem=ml.ragged(0.07, 0.01, 2, seed=3), phase=0.4)
body.append(under)
# column of glowing runes embroidered down the front of the under-robe
for k, (key, z, sz) in enumerate((("othala", 0.8, 0.13), ("algiz", 0.56, 0.13), ("ingwaz", 0.33, 0.12))):
    body += ml.surface_glyph("robe_rune%d" % k, under, (0.0, 0.0, z), key, (0, 0), sz, 0.011, mat=RUNE,
                             per_unit=40, sink=0.3)
# crimson outer robe, open at the front, ragged hem, brass trim down the opening
skirt, srings = ml.robe_surface("robe", [(1.08, 0.205, 0.168, 0.0), (0.86, 0.25, 0.198, 0.0),
                                         (0.6, 0.305, 0.24, 0.005), (0.35, 0.36, 0.28, 0.01),
                                         (0.16, 0.404, 0.312, 0.015), (0.09, 0.42, 0.322, 0.015)],
                                segs=28, folds=10, amp=(0.012, 0.05), gap=(5, 27), mat=ROBE, inner=DARK,
                                thick=0.022, hem=ml.ragged(0.075, 0.012, 2, seed=5))
body.append(skirt)
for edge in (0, -1):
    pts = [r[edge] + V((0, 0, 0.0)) for r in srings]
    pts[-1] = pts[-1] + V((0, 0, 0.03))
    body.append(cl.sweep("slit_trim", pts, 0.015, 8, TRIM))
# torso under the mantle
body.append(ml.robe_surface("bodice", [(1.5, 0.12, 0.105, 0.01), (1.42, 0.2, 0.15, 0.01), (1.28, 0.228, 0.17, 0.0),
                                       (1.12, 0.215, 0.166, 0.0), (0.98, 0.2, 0.16, 0.0)],
                            segs=24, folds=7, amp=(0.0, 0.015), mat=ROBE, thick=0, cap_top=True)[0])
# belt, rune buckle, pouches and a glowing vial
body.append(cl.torus("belt", (0.0, 0.0, 1.0), 0.218, 0.03, None, 24, 5, LEATHER, scale=(1.0, 0.8)))
buckle = pl.disc("buckle", 0.058, 0.026, (0, -1, 0), (0.0, -0.198, 1.0), TRIM, 20, 0.35)
body.append(buckle)
body += ml.surface_glyph("buckle_rune", buckle, (0.0, -0.19, 1.0), "eye", (0, 0), 0.07, 0.008, per_unit=60,
                         sink=0.2)
for k, (ang, w, h) in enumerate(((330.0, 0.1, 0.11), (25.0, 0.085, 0.1), (130.0, 0.09, 0.1))):
    a = math.radians(ang)
    nrm = V((math.cos(a) / 0.248, math.sin(a) / 0.204, 0.0)).normalized()
    p = V((0.25 * math.cos(a), 0.207 * math.sin(a), 0.935)) + nrm * 0.025
    F = cl.frame(nrm, (0, 0, 1))
    body.append(cl.rbox("pouch", (w, 0.06, h), p, 0.02, LEATHER, F, segments=1))
    body.append(cl.rbox("pouch_flap", (w * 1.04, 0.066, h * 0.42), p + V((0, 0, h * 0.32)) + nrm * 0.006, 0.016,
                        "M_Leather__4a2a1c", F, segments=1))
    body.append(cl.rivet(p + V((0, 0, h * 0.18)) + nrm * 0.04, 0.012, nrm, TRIM))
vial_c = V((-0.27, -0.07, 0.9))
body.append(cl.capsule("vial_glass", vial_c + V((0, 0, -0.05)), vial_c + V((0, 0, 0.03)), 0.034, 0.034, 12, 3,
                       "M_Glass"))
body.append(cl.capsule("vial_liquid", vial_c + V((0, 0, -0.05)), vial_c + V((0, 0, 0.0)), 0.027, 0.027, 10, 2,
                       vial_glow))
body.append(cl.cyl("vial_neck", vial_c + V((0, 0, 0.04)), vial_c + V((0, 0, 0.075)), 0.017, 10, "M_Glass"))
body.append(cl.cyl("vial_cork", vial_c + V((0, 0, 0.068)), vial_c + V((0, 0, 0.1)), 0.02, 10, "M_WoodPlanks",
                   bevel=0.004))
body.append(cl.sweep("vial_strap", [vial_c + V((0.0, 0.0, 0.085)), vial_c + V((0.03, 0.01, 0.1)),
                                    V((-0.235, -0.05, 0.985))], 0.008, 6, LEATHER))
# pointed shoulder mantle (six drapes, notch at the throat), brass trim and a sigil on the back
mhem = lambda a, k: -0.1 * (0.5 + 0.5 * math.cos(6 * a)) ** 2.5  # noqa: E731
mantle, mrings = ml.robe_surface("mantle", [(1.635, 0.135, 0.13, 0.02), (1.575, 0.17, 0.155, 0.02),
                                            (1.5, 0.27, 0.198, 0.02), (1.41, 0.335, 0.232, 0.02),
                                            (1.33, 0.37, 0.256, 0.02)],
                                 segs=36, folds=6, amp=(0.0, 0.03), mat=ROBE, inner=DARK, thick=0.02, hem=mhem)
body.append(mantle)
body.append(ml.loop_tube("mantle_trim", [p + V((0, 0, -0.004)) for p in mrings[-1]], 0.015, 6, TRIM, max_pts=36))
body.append(ml.loop_tube("collar_trim", mrings[0], 0.015, 6, TRIM, max_pts=14))
body += ml.surface_glyph("mantle_sigil", mantle, (0.0, 0.02, 1.47), "eye", (180, -4), 0.2, 0.013, mat=RUNE,
                         per_unit=40)
brooch_c = V((0.0, -0.2, 1.535))
body.append(pl.disc("brooch", 0.034, 0.02, (0, -1, 0.3), brooch_c, TRIM, 16, 0.4))
body.append(cl.sphere("brooch_gem", brooch_c + V((0, -0.012, 0.004)), 0.02, 10, 6, CRYSTAL))
body_node = cl.node("Body", body, P_BODY)

# ======================================================================== Head
head = []
hood_path = [(0.0, -0.165, 1.68), (0.0, -0.075, 1.703), (0.0, 0.025, 1.712), (0.0, 0.115, 1.695), (0.0, 0.195, 1.655),
             (0.0, 0.262, 1.595), (0.0, 0.318, 1.515), (0.0, 0.352, 1.43)]
hood_r = [(0.135, 0.162), (0.164, 0.196), (0.172, 0.192), (0.162, 0.162), (0.132, 0.122), (0.098, 0.086),
          (0.06, 0.052), (0.0, 0.0)]
hood, rim = ml.hood_surface("hood", hood_path, hood_r, segs=20, mat=ROBE, inner=DARK, thick=0.024, tilt=0.035)
head.append(hood)
head.append(ml.loop_tube("hood_trim", rim, 0.018, 6, TRIM, max_pts=18))
head.append(cl.ellipsoid("hood_void", (0.0, -0.02, 1.68), (0.132, 0.12, 0.16), 16, 8, void))
mask_c = V((0.0, -0.1, 1.665))
mask = cl.dome("mask", mask_c, (0.106, 0.134, 0.062), (90, 0, 0), 0.5, 18, 7, porcelain)
head.append(mask)
for s in (1, -1):
    ctrl = [(8 * s, 6), (24 * s, 11), (44 * s, 21)]
    pts, nrms = ml.surface_path(mask, mask_c, ctrl, 0.0, 0, 3.0)
    m = len(pts)
    wid = [0.024 * (0.45 + 0.55 * max(0.0, math.sin(math.pi * (i + 0.5) / m)) ** 0.7) for i in range(m)]
    head.append(ml.ribbon("eye_slit", pts, nrms, wid, 0.009, slit_dark, 4, 0.3, arch=True))
    head.append(ml.ribbon("eye_glow", [p + n * 0.006 for p, n in zip(pts, nrms)], nrms, [w * 0.62 for w in wid], 0.007,
                          eye_glow, 4, 0.1, arch=True))
    # painted tear line under each eye
    tp, tn = ml.surface_path(mask, mask_c, [(27 * s, 2), (26 * s, -14), (24 * s, -30)], 0.0, 0, 4.0)
    head.append(ml.ribbon("tear", tp, tn, 0.0075, 0.004, paint, 3, 0.2, taper=(False, True), arch=True))
# forehead mark and a small round "singing" mouth
fp, fn = ml.surface_path(mask, mask_c, [(0, 66), (0, 50), (0, 34)], 0.0, 0, 4.0)
head.append(ml.ribbon("brow_paint", fp, fn, 0.009, 0.004, paint, 3, 0.2, taper=(True, True), arch=True))
mp, mn = ml.surface_hit(mask, mask_c, ml._dir((0, -36)))
head.append(cl.ellipsoid("mouth", mp, (0.019, 0.025, 0.014), 12, 6, slit_dark,
                         V((0, 0, 1)).rotation_difference(mn).to_matrix()))
head_node = cl.node("Head", head, P_NECK, body_node)

# ======================================================================== Arms
# left: hanging sleeve, pale clawed hand
S = P_SHO[1]
armL = []
sl, cuff = ml.sleeve("sleeve_l", [S + V((-0.03, 0.0, 0.03)), (0.3, 0.04, 1.25), (0.315, 0.03, 1.08),
                                  (0.32, -0.04, 0.95)], (0.078, 0.148), segs=14, mat=ROBE, inner=LINING, thick=0.02,
                     droop=0.06, n=8)
armL.append(sl)
armL.append(ml.loop_tube("cuff_trim_l", cuff, 0.016, 6, TRIM, max_pts=14))
wrist_l = V((0.322, -0.045, 0.99))
armL.append(cl.capsule("wrist_l", wrist_l + V((-0.005, 0.03, 0.12)), wrist_l, 0.036, 0.032, 10, 2, SKIN))
armL += cl.claw_hand("hand_l", wrist_l, down=(0.04, -0.1, -1), palm=(-1, 0.1, 0), thumb=(0, -1, 0), s=0.17,
                     mat=SKIN, claw_mat=nails, fingers=4, curl=0.5)
cl.node("ArmL", armL, S, body_node)

# right: sleeve with the forearm raised forward, hand gripping the staff
S = P_SHO[-1]
armR = []
sr, cuff = ml.sleeve("sleeve_r", [S + V((0.03, 0.0, 0.03)), (-0.31, 0.07, 1.16), (-0.33, 0.01, 1.07),
                                  (-0.335, -0.09, 1.05)], (0.078, 0.135), segs=14, mat=ROBE, inner=LINING,
                     thick=0.02, droop=0.15, droop_from=0.35, n=8)
armR.append(sr)
armR.append(ml.loop_tube("cuff_trim_r", cuff, 0.016, 6, TRIM, max_pts=14))
armR.append(cl.capsule("wrist_r", V((-0.333, -0.06, 1.04)), GRIP + V((0.012, 0.03, 0.0)), 0.035, 0.032, 10, 2, SKIN))
armR += ml.grip_hand("hand_r", GRIP, STAFF_DIR, 0.027, 1.0, SKIN, palm_side=(-1, 0.25, 0))
armR_node = cl.node("ArmR", armR, S, body_node)

# ======================================================================== Staff (origin at the grip)
d = STAFF_DIR
e1 = d.cross(V((0, 0, 1))).normalized()          # across the staff (roughly X)
e2 = d.cross(e1).normalized()
B = GRIP - d * 0.56
H = GRIP + d * 0.62
C = GRIP + d * 0.775
staff = []
shaft_pts = [B.lerp(H, t) + e1 * (0.008 * math.sin(t * 9.0)) + e2 * (0.006 * math.sin(t * 6.0 + 1.0))
             for t in [i / 10 for i in range(11)]]
shaft_r = [0.026, 0.027, 0.029, 0.026, 0.027, 0.028, 0.026, 0.027, 0.029, 0.03, 0.032]
staff.append(cl.sweep("shaft", shaft_pts, shaft_r, 10, WOOD))
staff.append(cl.cyl("ferrule", B - d * 0.005, B + d * 0.08, 0.032, 12, TRIM, bevel=0.005))
staff.append(cl.sweep("ferrule_tip", [B, B - d * 0.04, B - d * 0.07], [0.03, 0.022, 0.0], 10, TRIM))
for k, (t, r, w) in enumerate(((0.1, 0.034, 0.03), (-0.1, 0.034, 0.03), (0.62, 0.042, 0.045))):
    p = GRIP + d * t
    staff.append(pl.band("band", r, w, 0.014, tuple(d), tuple(p), TRIM, 12, 0.0))
for t in (0.44, 0.52):
    staff.append(cl.torus("rune_ring", GRIP + d * t, 0.031, 0.01, cl.Vector((0, 0, 1)).rotation_difference(d).to_matrix(),
                          12, 4, RUNE))
# brass crescent head cradling the crystal, a halo ring and a hanging crimson pennant
staff.append(cl.sweep("head_cup", [H - d * 0.03, H + d * 0.02, H + d * 0.05], [0.036, 0.05, 0.03], 14, TRIM))
for sgn in (1, -1):
    side = e1 * sgn
    prong = cl.bezier(H + d * 0.03 + side * 0.025, H + d * 0.08 + side * 0.12, H + d * 0.26 + side * 0.035, 8,
                      H + d * 0.3 - side * 0.005)
    staff.append(cl.sweep("prong", prong, [0.02, 0.019, 0.018, 0.016, 0.014, 0.011, 0.008, 0.0], 8, TRIM))
staff.append(cl.torus("halo", C, 0.098, 0.012, cl.Vector((0, 0, 1)).rotation_difference(d).to_matrix(), 20, 5, TRIM))
staff.append(pl.crystal("crystal", tuple(C - d * 0.13), tuple(d), 0.26, 0.062, 6, 0.33, 0.12, CRYSTAL, double=True))
top = H - d * 0.02 - e2 * 0.03
staff.append(cl.sweep("pennant", [top, top + V((0.0, 0.01, -0.09)), top + V((0.0, 0.03, -0.19)),
                                  top + V((0.0, 0.04, -0.27))], [0.034, 0.036, 0.032, 0.0], 6, ROBE,
                      scale=(0.3, 1.0), up=(0, 1, 0)))
staff_node = cl.node("Staff", staff, GRIP, armR_node)
cast = pl.empty_at("CastPoint", tuple(C), staff_node, 0.12)

rw.finish(ASSET, "enemies", icon=True)
cl.report_nodes(["Body", "Head", "ArmL", "ArmR", "Staff", "CastPoint"])
cl.budget(15000)
cl.tri_breakdown()


def cast_world(rx_deg):
    o = bpy.data.objects["ArmR"]
    old = o.rotation_euler.copy()
    o.rotation_euler = (math.radians(rx_deg), 0, 0)
    bpy.context.view_layer.update()
    p = bpy.data.objects["CastPoint"].matrix_world.translation.copy()
    o.rotation_euler = old
    bpy.context.view_layer.update()
    return p


for tag, ang in (("rest", 0.0), ("idle", -11.5), ("release", -96.0), ("max", -97.4)):
    p = cast_world(ang)
    print("RWCAST   %-8s ArmR.x=%6.1f deg  CastPoint=(%.3f, %.3f, %.3f)" % (tag, ang, p.x, p.y, p.z))

if os.environ.get("RW_QUICK") != "1":
    cl.render_extra(ASSET, "enemies", ("front", "side"))
    # walking sway + idle arms (Godot: Body roll 0.05 rad, ArmR -0.2, ArmL small)
    cl.render_pose(ASSET, "enemies", {"Body": (0, 3, 0), "ArmR": (-11.5, 0, 0), "ArmL": (-6, 0, 0)}, "pose")
    # cast release: ArmR -1.67 rad, ArmL -0.6 rad
    cl.render_pose(ASSET, "enemies", {"ArmR": (-96, 0, 0), "ArmL": (-34, 0, 0)}, "pose_cast")
    cl.render_pose(ASSET, "enemies", {"ArmR": (-96, 0, 0), "ArmL": (-34, 0, 0)}, "pose_cast_side", view="side")
