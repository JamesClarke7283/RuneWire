"""enemy_drone: Scout Drone of the Cogwork Legion (origin at the body centre, span 1.4 m).

Hierarchy (spec Batch B):
  Body              round armoured shell: dark-iron hull, rust-orange armour cap, hazard-striped belt, brass
                    rims and rivets, four arms with hazard-striped fan ducts; origin = body centre = (0, 0, 0)
    Eye             big glowing lens facing -Y, under an angry V lid (origin at the lens centre)
    Rotor_0..3      three-blade rotors inside the ducts; origin at each hub, spin about Z.
                    0 = front-left (+X -Y), 1 = back-left, 2 = back-right, 3 = front-right.
    Gun             twin rivet gun hanging under the chin; origin at the centre of its ball mount, pitches
                    about X (positive = muzzle down)
      Muzzle        empty at the barrel tips, on the gun axis
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import techlib as tl  # noqa: E402
from mathutils import Matrix, Vector as V  # noqa: E402

ASSET = "enemy_drone"
rw.reset()
tl.setup()

PAINT, GLOW, GRILLE = tl.PAINT, tl.GLOW, tl.GRILLE
C = V((0, 0, 0))
SR = (0.33, 0.33, 0.28)          # hull radii
ZR = 0.11                         # rotor plane height
HUB = 0.47                        # hub offset along X and Y (diagonals) -> span 2 * (0.47 + 0.23) = 1.4
DUCT_O, DUCT_I = 0.23, 0.196      # duct outer / inner radius
BLADE_R = 0.18
E = V((0, -0.372, 0.02))          # lens centre
G = V((0, -0.19, -0.272))         # gun ball centre (pivot)
FLIP = Matrix.Rotation(math.pi, 3, 'X')
iris_glow = rw.glow("DroneIris", "ff5a14", 2.2)
core_glow = rw.glow("DroneCore", "ffe08a", 4.0)

# ======================================================================== Body
body = []
# dark-iron lower hull (its cut edge hides under the cap) and the rust-orange armour cap with a brass rim
body.append(cl.dome("hull", C, SR, FLIP, 0.72, 24, 7, "M_DarkMetal"))
CAP_COVER = 0.40
body.append(cl.dome("cap", C, (0.338, 0.338, 0.29), None, CAP_COVER, 24, 5, PAINT))
cap_z = 0.29 * (1 - 2 * CAP_COVER)
cap_r = 0.338 * math.sqrt(1 - (1 - 2 * CAP_COVER) ** 2)
body.append(cl.torus("cap_rim", (0, 0, cap_z), cap_r + 0.002, 0.017, None, 24, 4, "M_Brass"))
for k in range(6):
    a = 2 * math.pi * (k + 0.5) / 6
    rd = V((math.cos(a), math.sin(a), 0))
    body.append(cl.rivet(V((0, 0, cap_z + 0.014)) + rd * (cap_r - 0.006), 0.016, rd + V((0, 0, 0.4)), "M_Steel"))
# hazard belt round the equator (stripes outside), brass lower rim
body.append(tl.hazard_ring("belt", (0, 0), 0.342, 0.312, -0.06, cap_z - 0.004, count=8, slant=45, cols=28))
body.append(cl.torus("belt_rim", (0, 0, -0.062), 0.336, 0.015, None, 24, 3, "M_Brass"))
# rust belly plate with a glowing sensor dome
body.append(cl.dome("belly", (0, 0.03, -0.232), (0.235, 0.235, 0.075), FLIP, 0.5, 18, 4, "M_Rust"))
body.append(cl.torus("sensor_ring", (0, 0.07, -0.302), 0.044, 0.014, None, 12, 3, "M_Brass"))
body.append(cl.sphere("sensor", (0, 0.07, -0.304), 0.034, 8, 4, GLOW))
BC, BR = V((0, 0.03, -0.232)), (0.235, 0.235, 0.075)
for k in range(4):
    a = math.radians(45 + 90 * k)
    q = V((0.15 * math.cos(a), 0.15 * math.sin(a), 0))
    q.z = -BR[2] * math.sqrt(1 - (q.x / BR[0]) ** 2 - (q.y / BR[1]) ** 2)
    body.append(cl.rivet(BC + q, 0.016, V((q.x / BR[0] ** 2, q.y / BR[1] ** 2, q.z / BR[2] ** 2)), "M_Steel"))

# ---- eye housing: dark lens barrel, brass bezel with bolts, angry V lid and brow ridge
body.append(cl.cyl("eye_barrel", (0, -0.24, E.z), (0, E.y + 0.005, E.z), 0.156, 24, "M_DarkMetal"))
body.append(cl.torus("eye_bezel", (0, E.y - 0.002, E.z), 0.156, 0.03, tl.RX90, 24, 5, "M_Brass"))
body.extend(tl.bolt_ring((0, E.y - 0.03, E.z), (0, -1, 0), 0.156, 6, 0.017, "M_Steel", 0))
body.append(tl.lid_plate("eye_lid", (0, E.y - 0.02, E.z), 0.138, 0.078, 0.012, 0.056, "M_DarkMetal"))
for sd in (1, -1):
    a = V((0.0, E.y - 0.046, E.z + 0.022))
    b = V((0.122 * sd, E.y - 0.024, E.z + 0.094))
    body.append(cl.sweep("brow", [a, a.lerp(b, 0.5) + V((0, -0.006, 0.006)), b], [0.03, 0.03, 0.024], 10, PAINT,
                         scale=(0.7, 1.0), up=(0, -0.4, 1)))
    body.append(cl.rivet(b + V((0.012 * sd, -0.012, 0.006)), 0.016, (0.3 * sd, -1, 0.3), "M_Brass"))

# ---- top hatch with a glowing grille, antenna with a blinker
body.append(cl.cyl("hatch", (0, 0.04, 0.255), (0, 0.04, 0.305), 0.1, 16, "M_Brass", bevel=0.008))
body.append(cl.cyl("hatch_cap", (0, 0.04, 0.3), (0, 0.04, 0.314), 0.08, 16, GRILLE))
for k in (-1, 0, 1):
    body.append(rw.box("hatch_slot", (0.12 - 0.035 * abs(k), 0.02, 0.02), (0, 0.04 + k * 0.036, 0.314), mat=GLOW))
body.append(cl.cyl("antenna_base", (-0.13, 0.17, 0.2), (-0.13, 0.17, 0.27), 0.03, 10, "M_DarkMetal"))
body.append(cl.sweep("antenna", [(-0.13, 0.17, 0.26), (-0.14, 0.2, 0.36), (-0.165, 0.25, 0.44)], 0.012, 6,
                     "M_Steel"))
body.append(cl.sphere("antenna_bulb", (-0.168, 0.255, 0.455), 0.032, 10, 5, GLOW))

# ---- back power pack with a glowing vent
body.append(cl.rbox("pack", (0.26, 0.14, 0.2), (0, 0.29, -0.02), 0.035, PAINT))
body.append(cl.rbox("pack_grille", (0.19, 0.03, 0.12), (0, 0.36, -0.03), 0.012, GRILLE, segments=1))
for k in (-1, 0, 1):
    body.append(rw.box("pack_slot", (0.15, 0.02, 0.018), (0, 0.372, -0.03 + k * 0.034), mat=GLOW))
for (x, z) in ((-0.105, 0.062), (0.105, 0.062), (-0.105, -0.102), (0.105, -0.102)):
    body.append(cl.rivet((x, 0.36, z), 0.014, (0, 1, 0.3 if z > 0 else -0.3), "M_Brass"))

# ---- gun socket under the chin
body.append(cl.torus("gun_socket", (0, G.y, G.z + 0.042), 0.058, 0.018, None, 14, 4, "M_Brass"))

# ---- four arms, motor pods, stators and hazard ducts on the diagonals
ROTORS = []
for i, az in enumerate((45.0, 135.0, 225.0, 315.0)):
    d = tl.az_dir(az)
    H = V((HUB * math.copysign(1, d.x), HUB * math.copysign(1, d.y), ZR))
    hub_r = (H - V((0, 0, ZR))).length
    ROTORS.append((i, az, d, H))
    # arm: flattened tapering strut from the belt up into the duct wall, brass collar at the hull
    root = d * 0.27 + V((0, 0, -0.01))
    end = d * (hub_r - DUCT_O + 0.017) + V((0, 0, ZR - 0.01))
    mid = root.lerp(end, 0.5) + V((0, 0, 0.012))
    body.append(cl.sweep("arm", cl.bezier(root, mid, end, 5), [0.06, 0.057, 0.053, 0.05, 0.048], 8, PAINT,
                         scale=(0.72, 1.0), up=(0, 0, 1)))
    body.append(cl.torus("arm_collar", d * 0.338, 0.056, 0.016, tl.rot_z_to(end - root), 10, 3, "M_Brass"))
    body.append(cl.rbox("arm_clamp", (0.07, 0.05, 0.09), end - d * 0.006, 0.012, "M_DarkMetal",
                        cl.axes_matrix(d.cross(V((0, 0, 1))), d, V((0, 0, 1))), segments=1))
    # tapered motor pod under the hub, three stators (one in line with the arm), striped duct
    body.append(cl.cyl("pod", H + V((0, 0, -0.105)), H + V((0, 0, -0.018)), 0.034, 12, "M_DarkMetal", r1=0.052))
    for k in range(3):
        sd = tl.az_dir(az + 180.0 + 120.0 * k)
        body.append(cl.cyl("stator", H + sd * 0.04 + V((0, 0, -0.045)), H + sd * (DUCT_I + 0.01) + V((0, 0, -0.045)),
                           0.016, 4, "M_DarkMetal"))
    body.extend(tl.duct("duct", H, DUCT_O, DUCT_I, ZR - 0.04, ZR + 0.03, count=5, slant=45, cols=20,
                        lip_r=0.02))

body_node = tl.node("Body", body, C)

# ======================================================================== Eye
eye = [cl.dome("lens", E, (0.13, 0.13, 0.03), tl.RX90, 0.5, 20, 4, GLOW)]
eye.append(cl.torus("iris", E + V((0, -0.026, -0.016)), 0.06, 0.012, tl.RX90, 16, 3, iris_glow))
eye.append(cl.ellipsoid("pupil", E + V((0, -0.027, -0.016)), (0.038, 0.014, 0.038), 10, 4, core_glow))
eye_node = tl.node("Eye", eye, E, body_node)

# ======================================================================== Rotors
for (i, az, d, H) in ROTORS:
    parts = [cl.cyl("hub", H + V((0, 0, -0.024)), H + V((0, 0, 0.016)), 0.042, 10, "M_Brass"),
             cl.ellipsoid("spinner", H + V((0, 0, 0.016)), (0.036, 0.036, 0.03), 8, 4, "M_DarkMetal")]
    for k in range(3):
        bd = tl.az_dir(az + 30.0 + 120.0 * k)
        parts.append(tl.blade("blade", H, bd, 0.03, BLADE_R, 0.074, 0.02, 18.0, "M_Steel", tl.HAZ_Y, 0.74, 6))
    tl.node("Rotor_%d" % i, parts, H, body_node)

# ======================================================================== Gun
gun = [cl.sphere("gun_ball", G, 0.06, 12, 6, "M_DarkMetal")]
gun.append(cl.capsule("gun_body", G + V((0, -0.025, 0)), G + V((0, -0.14, 0.004)), 0.05, 0.047, 12, 2, PAINT))
gun.append(cl.cyl("gun_jacket", G + V((0, -0.13, 0)), G + V((0, -0.255, 0)), 0.043, 12, "M_DarkMetal"))
gun.append(cl.torus("gun_band", G + V((0, -0.19, 0)), 0.044, 0.011, tl.RX90, 12, 3, "M_Brass"))
for sx in (-1, 1):
    a = G + V((sx * 0.024, -0.24, 0))
    b = G + V((sx * 0.024, -0.31, 0))
    gun.append(cl.cyl("barrel", a, b, 0.018, 8, "M_Steel"))
    gun.append(cl.cyl("muzzle_ring", b, b + V((0, -0.026, 0)), 0.024, 10, "M_Brass"))
    gun.append(cl.cyl("bore", b + V((0, -0.02, 0)), b + V((0, -0.0275, 0)), 0.012, 6, GRILLE))
# ammo drum on the gun's left flank and a little glowing sight on top
gun.append(cl.cyl("drum", G + V((0.04, -0.085, -0.005)), G + V((0.085, -0.085, -0.005)), 0.042, 12, "M_Brass"))
gun.append(cl.cyl("drum_cap", G + V((0.084, -0.085, -0.005)), G + V((0.094, -0.085, -0.005)), 0.026, 10, "M_Steel"))
gun.append(cl.ellipsoid("sight", G + V((0, -0.1, 0.05)), (0.016, 0.02, 0.016), 8, 4, GLOW))
gun_node = tl.node("Gun", gun, G, body_node)
tl.empty("Muzzle", G + V((0, -0.338, 0)), gun_node, 0.05)

rw.finish(ASSET, "enemies", icon=True)
tl.summary(["Body", "Eye", "Rotor_0", "Rotor_1", "Rotor_2", "Rotor_3", "Gun", "Muzzle"], 8000)
cl.render_extra(ASSET, "enemies", ("front", "side", "top"))
tl.render_dir(ASSET, "enemies", "below", (-0.55, -0.9, -0.75))
cl.render_pose(ASSET, "enemies", {"Rotor_0": (0, 0, 40), "Rotor_1": (0, 0, 75), "Rotor_2": (0, 0, 20),
                                  "Rotor_3": (0, 0, 95), "Gun": (55, 0, 0), "Eye": (0, 0, 12)}, "pose")
