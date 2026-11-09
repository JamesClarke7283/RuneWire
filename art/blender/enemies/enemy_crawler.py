"""enemy_crawler: "Clank" spider-bot of the Cogwork Legion (origin on the ground under the body).

Hierarchy (spec Batch B):
  Body                pivot at the body centre (0, 0, 0.55)
    Head              front; three glowing eyes + mandibles (pivot at the neck)
    Leg{i}_Hip        socket ball, pivot at the socket
      Leg{i}_Upper    pivot at the socket, runs outward and up at 35 deg, length 0.55 (socket -> knee)
        Leg{i}_Lower  pivot at the knee, runs down to a pointed foot on the ground, length 0.75

Legs: i = 0, 1, 2 on the LEFT (+X) at body angles 30, 90, 150 deg (measured from the front, -Y);
      i = 3, 4, 5 on the RIGHT (-X) at 30, 90, 150 deg. So 0/3 are the front pair, 2/5 the back.
Sockets sit on the lower flank (radius 0.38 from the body axis, z = 0.40) so that a 0.55 upper
segment at +35 deg and a 0.75 lower segment reach the ground with the foot ~17.5 deg out from vertical.
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

ASSET = "enemy_crawler"
rw.reset()

BODY_C = V((0.0, 0.0, 0.55))
SOCK_R, SOCK_Z = 0.38, 0.40
UPPER_LEN, UPPER_ANG = 0.55, 35.0
LOWER_LEN = 0.75

eye_glow = "M_TechGlow"
dark_rubber = "M_Rubber"
cl.hazard_black()
grille = rw.flat("GrilleDark", "1d1b20", 0.6, 0.3)

# ======================================================================== Body
body = []
# main dome shell (dark iron) and lower belly (rusty)
body.append(cl.ellipsoid("shell", (0, 0.05, 0.58), (0.44, 0.48, 0.31), 28, 14, "M_DarkMetal"))
body.append(cl.ellipsoid("belly", (0, 0.04, 0.47), (0.4, 0.43, 0.2), 24, 10, "M_Rust"))
# brass equator trim with rivets
body.append(cl.torus("trim", (0, 0.05, 0.5), 0.425, 0.035, None, 36, 6, "M_Brass", scale=(1.0, 1.09)))
for k in range(12):
    a = 2 * math.pi * (k + 0.5) / 12
    p = V((0.455 * math.cos(a), 0.05 + 0.455 * 1.09 * math.sin(a), 0.5))
    body.append(cl.rivet(p, 0.017, V((math.cos(a), math.sin(a), 0)), "M_Steel"))
# segmented armour plates (beetle-ish): front cowl, back plate with hazard stripes
body.append(cl.ellipsoid("plate_front", (0, -0.2, 0.74), (0.36, 0.24, 0.17), 22, 10, "M_PaintedMetal__c8452c"))
body.append(cl.ellipsoid("plate_back", (0, 0.33, 0.73), (0.35, 0.2, 0.16), 22, 10, "M_PaintedMetal__c8452c"))
body.append(cl.hazard_panel("haz", 0.24, 0.2, 0.03, (0, 0.42, 0.79), (-58, 0, 0), stripe=0.07))
body.extend(cl.rivet_line((-0.26, -0.28, 0.76), (0.26, -0.28, 0.76), 5, 0.016, (0, -0.6, 0.8), "M_Brass"))
# top hatch with glowing furnace grille
body.append(cl.cyl("hatch_ring", (0, 0.06, 0.82), (0, 0.06, 0.92), 0.17, 24, "M_Brass", bevel=0.012))
body.append(cl.cyl("hatch_cap", (0, 0.06, 0.9), (0, 0.06, 0.95), 0.14, 24, grille, bevel=0.01))
for k in (-1, 0, 1):
    body.append(cl.rbox("grille_slot", (0.2 - 0.06 * abs(k), 0.035, 0.03), (0, 0.06 + k * 0.06, 0.955), 0.012, eye_glow))
body.extend(cl.rivet_ring((0, 0.06, 0.895), 0.165, 8, 0.014, (0, 0, 1), "M_Steel", outward=True))
# exhaust pipe at the back
body.append(cl.sweep("exhaust", [(0.18, 0.38, 0.7), (0.2, 0.5, 0.82), (0.2, 0.52, 0.98)], 0.045, 12, "M_DarkMetal"))
body.append(cl.cyl("exhaust_lip", (0.2, 0.52, 0.95), (0.2, 0.52, 1.02), 0.06, 14, "M_Brass", bevel=0.01))
body.append(cl.cyl("exhaust_hole", (0.2, 0.52, 1.0), (0.2, 0.52, 1.025), 0.04, 14, grille))
# little warning lamp antenna
body.append(cl.cyl("antenna", (-0.2, 0.3, 0.8), (-0.24, 0.36, 1.04), 0.012, 8, "M_Steel"))
body.append(cl.sphere("antenna_bulb", (-0.24, 0.36, 1.06), 0.035, 10, 6, eye_glow))
# underside dark plate
body.append(cl.ellipsoid("under", (0, 0.04, 0.33), (0.28, 0.3, 0.07), 20, 6, "M_DarkMetal"))

LEGS = []
for i in range(6):
    side = 1 if i < 3 else -1
    ang = (30.0, 90.0, 150.0)[i % 3]
    a = math.radians(ang)
    h = V((side * math.sin(a), -math.cos(a), 0.0))
    S = V((0, 0, SOCK_Z)) + h * SOCK_R
    u = (h * math.cos(math.radians(UPPER_ANG)) + V((0, 0, 1)) * math.sin(math.radians(UPPER_ANG))).normalized()
    K = S + u * UPPER_LEN
    drop = K.z
    out = math.sqrt(max(0.0, LOWER_LEN ** 2 - drop ** 2))
    Fp = V((K.x, K.y, 0.0)) + h * out
    LEGS.append((i, side, h, S, K, Fp))
    # collar on the body around each socket
    body.append(cl.torus("collar", S - h * 0.03, 0.085, 0.022, cl.Vector((0, 0, 1)).rotation_difference(h).to_matrix(),
                         12, 4, "M_Brass"))

body_node = cl.node("Body", body, BODY_C)

# ======================================================================== Head
head = []
HC = V((0, -0.53, 0.53))
HR = (0.2, 0.18, 0.2)
head.append(cl.ellipsoid("head_shell", HC, HR, 24, 12, "M_DarkMetal"))
head.append(cl.torus("neck_ring", (0, -0.36, 0.52), 0.14, 0.032, cl.Matrix.Rotation(math.radians(90), 3, 'X'),
                     16, 5, "M_Brass"))
# three eyes: big centre, two smaller lower-sides; each glowing lens in a dark bezel + brass rim
for (x, z, r) in ((0.0, 0.045, 0.085), (0.122, -0.035, 0.058), (-0.122, -0.035, 0.058)):
    p = cl.head_point(HC, HR, x, HC.z + z, 0.0)
    n = cl.head_normal(HC, HR, p)
    R = cl.Vector((0, 0, 1)).rotation_difference(n).to_matrix()
    head.append(cl.torus("eye_rim", p + n * 0.006, r * 1.06, r * 0.26, R, 18, 5, "M_Brass"))
    head.append(cl.ellipsoid("eye_bezel", p, (r * 1.02, r * 1.02, r * 0.42), 16, 6, grille, R))
    head.append(cl.ellipsoid("eye_lens", p + n * 0.012, (r * 0.78, r * 0.78, r * 0.5), 16, 6, eye_glow, R))
# angry V brow plates over the eyes
for sd in (1, -1):
    a = cl.head_point(HC, HR, 0.02 * sd, HC.z + 0.095, 0.012)
    b = cl.head_point(HC, HR, 0.19 * sd, HC.z + 0.15, 0.0)
    head.append(cl.sweep("brow_plate", [a, a.lerp(b, 0.5) + V((0, -0.012, 0.012)), b], [0.034, 0.036, 0.026], 10,
                         "M_PaintedMetal__c8452c", scale=(0.75, 1.0), up=(0, 0, 1)))
# mandibles: curved pincers sweeping forward and inward
for sd in (1, -1):
    base = V((0.1 * sd, -0.6, 0.43))
    pts = cl.bezier(base, base + V((0.08 * sd, -0.13, -0.03)), base + V((0.02 * sd, -0.25, -0.07)), 7,
                    base + V((-0.06 * sd, -0.27, -0.05)))
    head.append(cl.sweep("mandible", pts, [0.046, 0.044, 0.04, 0.033, 0.024, 0.013, 0.0], 10, "M_Steel",
                         scale=(0.75, 1.0), up=(0, 0, 1)))
    head.append(cl.sphere("mandible_hinge", base, 0.05, 10, 6, "M_Brass"))
    for t in (0.35, 0.6):
        q = pts[int(t * 6)]
        head.append(cl.sweep("tooth", [q, q + V((-0.04 * sd, -0.01, 0))], [0.013, 0.0], 6, "M_Steel"))
head_node = cl.node("Head", head, V((0, -0.34, 0.52)), body_node)

# ======================================================================== Legs
upper_mat = "M_PaintedMetal__c8452c"
for (i, side, h, S, K, Fp) in LEGS:
    u = (K - S).normalized()
    sidev = h.cross(V((0, 0, 1))).normalized()
    nrm = u.cross(sidev).normalized()
    if nrm.z < 0:
        nrm = -nrm
        sidev = -sidev
    Rm = cl.axes_matrix(sidev, nrm, u)
    # --- hip socket ball
    hip = [cl.sphere("hip_ball", S, 0.085, 16, 8, "M_Brass")]
    hip_node = cl.node("Leg%d_Hip" % i, hip, S, body_node)
    # --- upper segment: dark strut + painted armour plate + piston
    up = [cl.capsule("upper_strut", S, K, 0.05, 0.042, 12, 2, "M_DarkMetal")]
    mid = S.lerp(K, 0.5)
    up.append(cl.rbox("upper_plate", (0.1, 0.06, UPPER_LEN * 0.72), mid + nrm * 0.035, 0.025, upper_mat, Rm))
    up.append(cl.rivet(mid + nrm * 0.066 + u * 0.12, 0.013, nrm, "M_Brass"))
    up.append(cl.rivet(mid + nrm * 0.066 - u * 0.12, 0.013, nrm, "M_Brass"))
    pa, pb = S.lerp(K, 0.18) - nrm * 0.055, S.lerp(K, 0.82) - nrm * 0.05
    up.append(cl.cyl("piston", pa, pa.lerp(pb, 0.55), 0.022, 10, "M_DarkMetal"))
    up.append(cl.cyl("piston_rod", pa.lerp(pb, 0.5), pb, 0.012, 8, "M_Steel"))
    up_node = cl.node("Leg%d_Upper" % i, up, S, hip_node)
    # --- lower segment: knee ball, tapering shin bowed slightly outward, pointed foot
    lo = [cl.sphere("knee_ball", K, 0.066, 12, 8, "M_Steel"),
          cl.torus("knee_band", K, 0.062, 0.016, cl.Vector((0, 0, 1)).rotation_difference(sidev).to_matrix(), 14, 4,
                   "M_Brass")]
    bow = h * 0.06
    shin = cl.bezier(K, K.lerp(Fp, 0.45) + bow, Fp + V((0, 0, 0.16)), 8)
    lo.append(cl.sweep("shin", shin, [0.052, 0.054, 0.05, 0.046, 0.042, 0.038, 0.034, 0.03], 10, upper_mat))
    lo.append(cl.cyl("ankle_band", Fp + V((0, 0, 0.13)), Fp + V((0, 0, 0.2)), 0.04, 12, "M_Brass"))
    lo.append(cl.sweep("foot_spike", [Fp + V((0, 0, 0.17)), Fp + V((0, 0, 0.07)) + h * 0.004, Fp], [0.036, 0.024, 0.0], 10,
                       "M_DarkMetal"))
    lo_node = cl.node("Leg%d_Lower" % i, lo, K, up_node)

rw.finish(ASSET, "enemies", icon=True)
names = ["Body", "Head"]
for i in range(6):
    names += ["Leg%d_Hip" % i, "Leg%d_Upper" % i, "Leg%d_Lower" % i]
cl.report_nodes(names)
for (i, side, h, S, K, Fp) in LEGS:
    print("RWLEG %d side=%s socket=(%.3f, %.3f, %.3f) knee=(%.3f, %.3f, %.3f) foot=(%.3f, %.3f, %.3f) upper=%.3f lower=%.3f" % (
        i, "L" if side > 0 else "R", S.x, S.y, S.z, K.x, K.y, K.z, Fp.x, Fp.y, Fp.z, (K - S).length, (Fp - K).length))
cl.budget(15000)
cl.tri_breakdown()
cl.render_extra(ASSET, "enemies", ("front", "side", "top"))
pose = {"Head": (10, 0, 25)}
for i in range(6):
    pose["Leg%d_Hip" % i] = (0, 0, 25 if i % 2 else -25)
    pose["Leg%d_Upper" % i] = (30 if i in (0, 4) else 0, 0, 0)
    pose["Leg%d_Lower" % i] = (-35 if i in (1, 3) else 20, 0, 0)
cl.render_pose(ASSET, "enemies", pose, "pose")
