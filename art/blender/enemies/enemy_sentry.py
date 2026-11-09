"""enemy_sentry: Sentry Turret of the Cogwork Legion (origin on the ground, ~1.8 m tall).

Hierarchy (spec Batch B):
  Base              heavy tripod: three splayed rust-orange legs with piston braces and rubber-soled feet
                    around a dark pedestal with a hazard-striped band; origin on the ground (0, 0, 0)
    Yaw             pivot at the top of the base (0, 0, YAW_Z): turntable with a hazard-striped rim, two
                    yoke arms with bearings and hazard plates, the lamp post; turns about Z
      Lamp          glowing orange warning bulb in a steel cage above the right bearing (origin at the
                    bulb centre; the game blinks it by toggling visibility, so it is only the bulb)
      Pitch         pivot on the trunnion axis (0, 0, PITCH_Z): armoured gun housing with an angry sensor
                    eye on top and a brass ammo drum behind; tilts about X (game range -0.8 .. +0.6 rad)
        Barrels     six-barrel gatling cluster pointing -Y; origin on the barrel axis at its rear hub;
                    spins about Y
        Muzzle      empty at the barrel tips, on the barrel axis
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
pl = tl.pl
from mathutils import Vector as V  # noqa: E402

ASSET = "enemy_sentry"
rw.reset()
tl.setup()

PAINT, GLOW, GRILLE = tl.PAINT, tl.GLOW, tl.GRILLE
UP = V((0, 0, 1))
YAW_Z, PITCH_Z = 0.80, 1.30
DECK = YAW_Z + 0.12               # top of the turntable deck
ARM_X = 0.345                     # yoke arm centre x
HOUSE = (0.46, 0.56, 0.34)        # gun housing size
HOUSE_C = V((0, 0.02, PITCH_Z))
BAR_Y0, TIP_Y = -0.335, -0.98     # barrel cluster rear hub / barrel tips
EYE_C = V((0, -0.255, PITCH_Z + 0.215))
DRUM_C = V((0, 0.34, PITCH_Z + 0.06))
LAMP_C = V((-ARM_X, 0.0, PITCH_Z + 0.4))

# ======================================================================== Base
base = []
ped = [(0.0, 0.2), (0.1, 0.205), (0.19, 0.235), (0.245, 0.28), (0.27, 0.33), (0.27, YAW_Z - 0.09),
       (0.235, YAW_Z - 0.06), (0.215, YAW_Z - 0.035), (0.215, YAW_Z), (0.0, YAW_Z)]
base.append(pl.lathe_axis("pedestal", ped, (0, 0, 1), (0, 0, 0), 24, "M_DarkMetal", False, False, 40))
base.append(tl.hazard_ring("ped_band", (0, 0), 0.287, 0.255, 0.43, 0.6, count=7, slant=45, cols=24))
for z in (0.43, 0.6):
    base.append(cl.torus("ped_rim", (0, 0, z), 0.28, 0.018, None, 24, 3, "M_Brass"))
base.append(cl.torus("bearing", (0, 0, YAW_Z - 0.012), 0.232, 0.026, None, 24, 4, "M_Steel"))
base.extend(cl.rivet_ring((0, 0, 0.68), 0.27, 6, 0.017, UP, "M_Brass", 30.0, outward=True))

LEGS = []
for i, az in enumerate((180.0, 60.0, 300.0)):          # one leg behind, two splayed forward
    d = tl.az_dir(az)
    side = UP.cross(d).normalized()
    hip = d * 0.27 + V((0, 0, 0.4))
    ank = d * 0.7 + V((0, 0, 0.12))
    LEGS.append((d, hip, ank))
    ax = (ank - hip).normalized()
    nrm = side.cross(ax).normalized()                   # leg "top" normal (up and outward)
    # hinge lug on the pedestal with a steel pin
    base.append(cl.rbox("hip_lug", (0.17, 0.12, 0.15), d * 0.25 + V((0, 0, 0.4)), 0.025, "M_DarkMetal",
                        cl.axes_matrix(side, d, UP), segments=1))
    base.append(cl.cyl("hip_pin", hip - side * 0.1, hip + side * 0.1, 0.045, 10, "M_Steel"))
    # chunky box-section leg, painted, with brass rivets on top
    base.append(pl.beam_between("leg", hip, ank, (0.13, 0.11), PAINT, rounded=0.03, up=nrm))
    base.append(cl.rivet(hip.lerp(ank, 0.45) + nrm * 0.056, 0.017, nrm, "M_Brass"))
    # piston brace from high on the pedestal to the leg's middle
    base.extend(tl.piston("brace", d * 0.24 + V((0, 0, 0.7)), hip.lerp(ank, 0.62) - nrm * 0.04, 0.03))
    # foot: ankle ball and a domed pad with a rubber sole and bolts
    base.append(cl.sphere("ankle", ank, 0.07, 10, 5, "M_Brass"))
    foot_c = V((ank.x, ank.y, 0.0))
    pad = pl.lathe_axis("foot", [(0.0, 0.0), (0.155, 0.0), (0.165, 0.014), (0.165, 0.04), (0.15, 0.06),
                                 (0.1, 0.085), (0.0, 0.092)], (0, 0, 1), tuple(foot_c), 16, "M_DarkMetal",
                        False, False, 40)
    rw.set_mat_where(pad, "M_Rubber", lambda c, n: c.z < 0.03 and n.z < 0.5)
    base.append(pad)
    for k in range(2):
        a = math.radians(az + 90 + 180 * k)
        q = foot_c + V((math.sin(a), -math.cos(a), 0)) * 0.118 + V((0, 0, 0.066))
        base.append(cl.rivet(q, 0.017, V((math.sin(a) * 0.5, -math.cos(a) * 0.5, 1)), "M_Steel"))

base_node = tl.node("Base", base, (0, 0, 0))

# ======================================================================== Yaw
yaw = []
yaw.append(tl.hazard_ring("rim", (0, 0), 0.37, 0.31, YAW_Z + 0.005, YAW_Z + 0.1, count=9, slant=45, cols=32))
yaw.append(pl.lathe_axis("deck", [(0.0, YAW_Z), (0.322, YAW_Z), (0.322, DECK - 0.022), (0.3, DECK), (0.0, DECK)],
                         (0, 0, 1), (0, 0, 0), 32, "M_DarkMetal", False, False, 40))
yaw.append(cl.torus("deck_rim", (0, 0, YAW_Z + 0.1), 0.34, 0.022, None, 32, 3, "M_Brass"))
for sx in (1, -1):
    x = sx * ARM_X
    out = V((sx, 0, 0))
    yaw.append(cl.rbox("yoke", (0.1, 0.3, PITCH_Z - DECK + 0.02), (x, 0, (DECK + PITCH_Z) / 2 - 0.01), 0.03, PAINT))
    yaw.append(cl.cyl("bearing", (x - 0.05, 0, PITCH_Z), (x + 0.05, 0, PITCH_Z), 0.15, 16, PAINT, bevel=0.02))
    yaw.append(cl.cyl("hub", (x + sx * 0.045, 0, PITCH_Z), (x + sx * 0.075, 0, PITCH_Z), 0.1, 14, "M_Brass"))
    yaw.append(cl.cyl("hub_cap", (x + sx * 0.07, 0, PITCH_Z), (x + sx * 0.095, 0, PITCH_Z), 0.045, 10, "M_Steel"))
    yaw.extend(tl.bolt_ring((x + sx * 0.075, 0, PITCH_Z), out, 0.074, 4, 0.015, "M_Steel", 45))
    yaw.append(cl.hazard_panel("arm_haz", 0.24, 0.17, 0.014, (x + sx * 0.053, 0, DECK + 0.115),
                               (0, 0, 90 * sx), stripe=0.075))
    yaw.extend(cl.rivet_line((x + sx * 0.052, -0.12, DECK + 0.02), (x + sx * 0.052, 0.12, DECK + 0.02), 2, 0.015,
                             out, "M_Brass"))
# lamp post and cage above the right bearing (the bulb itself is the Lamp node)
yaw.append(cl.cyl("lamp_post", (-ARM_X, 0, PITCH_Z + 0.12), (-ARM_X, 0, LAMP_C.z - 0.07), 0.028, 10, "M_Steel"))
yaw.append(pl.lathe_axis("lamp_cup", [(0.0, 0.0), (0.05, 0.0), (0.075, 0.025), (0.072, 0.04), (0.0, 0.04)],
                         (0, 0, 1), (LAMP_C.x, LAMP_C.y, LAMP_C.z - 0.085), 14, "M_DarkMetal", False, False, 40))
for k in range(3):                                   # open three-bar cage so the bulb reads from every side
    a = math.radians(90 + 120 * k)
    rr = V((math.cos(a), math.sin(a), 0))
    yaw.append(cl.sweep("cage_bar", [LAMP_C + rr * 0.062 + V((0, 0, -0.06)), LAMP_C + rr * 0.08 + V((0, 0, 0.0)),
                                     LAMP_C + rr * 0.03 + V((0, 0, 0.082))], 0.009, 6, "M_Steel"))
yaw.append(cl.ellipsoid("lamp_cap", LAMP_C + V((0, 0, 0.084)), (0.036, 0.036, 0.022), 10, 4, "M_DarkMetal"))
yaw_node = tl.node("Yaw", yaw, (0, 0, YAW_Z), base_node)

# ======================================================================== Lamp
tl.node("Lamp", [cl.ellipsoid("bulb", LAMP_C, (0.064, 0.064, 0.078), 12, 6, GLOW)], LAMP_C, yaw_node)

# ======================================================================== Pitch
pitch = []
pitch.append(cl.rbox("housing", HOUSE, HOUSE_C, 0.06, PAINT))
for y in (-0.2, 0.235):
    pitch.append(cl.rbox("trim", (HOUSE[0] + 0.02, 0.045, HOUSE[2] + 0.02), (0, y, PITCH_Z), 0.015, "M_Brass",
                         segments=1))
for sx in (1, -1):
    pitch.append(cl.cyl("trunnion", (sx * 0.22, 0, PITCH_Z), (sx * 0.3, 0, PITCH_Z), 0.075, 16, "M_Steel"))
    pitch.append(cl.rivet((sx * 0.232, 0.08, PITCH_Z + 0.12), 0.016, (sx, 0, 0), "M_Brass"))
# front mantlet and the brass collar the barrels turn in
pitch.append(cl.rbox("mantlet", (0.38, 0.05, 0.27), (0, -0.265, PITCH_Z - 0.01), 0.02, "M_DarkMetal", segments=1))
pitch.append(pl.lathe_axis("collar", [(0.0, 0.0), (0.14, 0.0), (0.14, 0.028), (0.12, 0.045), (0.0, 0.045)],
                           (0, -1, 0), (0, -0.29, PITCH_Z), 24, "M_Brass", False, False, 40))
# sensor eye pod on top: dark barrel, brass bezel, glowing lens under an angry V lid
pitch.append(cl.rbox("pod_saddle", (0.13, 0.24, 0.08), (0, -0.08, PITCH_Z + 0.165), 0.02, "M_DarkMetal", segments=1))
pitch.append(cl.cyl("eye_pod", (0, 0.05, EYE_C.z), (0, EYE_C.y + 0.01, EYE_C.z), 0.104, 16, "M_DarkMetal",
                    bevel=0.012))
pitch.append(cl.torus("eye_bezel", (0, EYE_C.y + 0.004, EYE_C.z), 0.097, 0.022, tl.RX90, 20, 4, "M_Brass"))
pitch.append(cl.dome("eye_lens", EYE_C, (0.08, 0.08, 0.028), tl.RX90, 0.5, 16, 4, GLOW))
pitch.append(tl.lid_plate("eye_lid", (0, EYE_C.y - 0.01, EYE_C.z), 0.086, 0.048, 0.006, 0.036, "M_DarkMetal",
                          bevel=0.004))
for sd in (1, -1):                                   # angry V brow ridge along the lid edge (as on the drone)
    a = V((0.0, EYE_C.y - 0.032, EYE_C.z + 0.012))
    b = V((0.072 * sd, EYE_C.y - 0.018, EYE_C.z + 0.058))
    pitch.append(cl.sweep("brow", [a, a.lerp(b, 0.5) + V((0, -0.004, 0.004)), b], [0.02, 0.02, 0.016], 8, PAINT,
                          scale=(0.7, 1.0), up=(0, -0.4, 1)))
pitch.append(cl.sweep("antenna", [EYE_C + V((0.05, 0.25, 0.06)), EYE_C + V((0.06, 0.28, 0.16)),
                                  EYE_C + V((0.08, 0.33, 0.22))], 0.011, 6, "M_Steel"))
pitch.append(cl.sphere("antenna_tip", EYE_C + V((0.081, 0.335, 0.23)), 0.022, 8, 4, GLOW))
# ammo drum behind (sits high enough to clear the deck at full elevation), hazard plate below it
pitch.append(pl.lathe_axis("drum", [(0.0, -0.13), (0.115, -0.13), (0.14, -0.11), (0.14, 0.11), (0.115, 0.13),
                                    (0.0, 0.13)], (1, 0, 0), tuple(DRUM_C), 24, "M_Brass", False, False, 40))
pitch.append(pl.band("drum_band", 0.148, 0.05, 0.02, (1, 0, 0), tuple(DRUM_C), "M_DarkMetal", 24, 0.0))
for sx in (1, -1):
    pitch.append(cl.cyl("drum_cap", DRUM_C + V((sx * 0.125, 0, 0)), DRUM_C + V((sx * 0.14, 0, 0)), 0.07, 12,
                        "M_Steel"))
    pitch.append(cl.rivet(DRUM_C + V((sx * 0.142, 0, 0)), 0.02, (sx, 0, 0), "M_Brass"))
pitch.append(cl.hazard_panel("haz_back", 0.3, 0.11, 0.014, (0, HOUSE_C.y + HOUSE[1] / 2 + 0.004, PITCH_Z - 0.105),
                             (0, 0, 180), stripe=0.07))
pitch_node = tl.node("Pitch", pitch, (0, 0, PITCH_Z), yaw_node)

# ======================================================================== Barrels
AX = V((0, 0, PITCH_Z))
brl = []
brl.append(pl.lathe_axis("hub", [(0.0, 0.0), (0.12, 0.0), (0.126, 0.015), (0.126, 0.05), (0.1, 0.066),
                                 (0.0, 0.066)], (0, -1, 0), (0, BAR_Y0, PITCH_Z), 20, "M_DarkMetal", False, False, 40))
brl.append(cl.cyl("spindle", AX + V((0, BAR_Y0 - 0.06, 0)), AX + V((0, TIP_Y + 0.012, 0)), 0.034, 10, "M_Steel"))
BR = 0.07
for i in range(6):
    a = math.radians(30 + 60 * i)
    off = V((math.cos(a) * BR, 0, math.sin(a) * BR))
    p1 = AX + V((0, TIP_Y, 0)) + off
    brl.append(cl.cyl("barrel", AX + V((0, BAR_Y0 - 0.05, 0)) + off, p1, 0.026, 10, "M_Steel"))
    brl.append(cl.cyl("bore", p1 + V((0, 0.006, 0)), p1 + V((0, -0.003, 0)), 0.014, 6, GRILLE))
for (y, w) in ((-0.56, 0.045), (TIP_Y + 0.09, 0.055)):
    brl.append(pl.disc("clamp", 0.112, w, (0, 1, 0), (0, y, PITCH_Z), "M_Brass", 16, 0.3))
tl.node("Barrels", brl, (0, BAR_Y0, PITCH_Z), pitch_node)
tl.empty("Muzzle", (0, TIP_Y - 0.02, PITCH_Z), pitch_node, 0.06)

rw.finish(ASSET, "enemies", icon=True)
tl.summary(["Base", "Yaw", "Lamp", "Pitch", "Barrels", "Muzzle"], 9000)
cl.render_extra(ASSET, "enemies", ("front", "side"))
cl.render_pose(ASSET, "enemies", {"Yaw": (0, 0, 35), "Pitch": (-46, 0, 0), "Barrels": (0, 30, 0)}, "pose")
cl.render_pose(ASSET, "enemies", {"Yaw": (0, 0, -30), "Pitch": (34, 0, 0)}, "pose_down", "side")
cl.render_pose(ASSET, "enemies", {"Pitch": (-46, 0, 0)}, "pose_up", "side")
