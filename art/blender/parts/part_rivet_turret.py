"""part_rivet_turret: 0.7 x 0.8 x 0.9 m tech gatling turret.

Nodes (origin of the whole model = bounding-box centre = Base origin):
  Base        dark-metal floor plate with a hazard-striped yellow skirt, corner bolts and a steel column.
    Yaw       pivot at the column top (0, 0, YAW_Z); turntable + dark-iron yoke with riveted side plates,
              bearing hubs and an orange warning lamp. Rotates about Z.
      Pitch   pivot on the trunnion axis (0, 0, PITCH_Z); signal-orange receiver with brass trim, a
              riveted brass ammo drum on top, a copper-wound motor at the back. Rotates about X.
        Barrels   six-barrel steel cluster pointing -Y with brass clamp rings; origin on the barrel
                  axis at the cluster's rear hub (0, BARREL_Y0, PITCH_Z); spins about Y.
        Muzzle    empty at the barrel tips on the axis (0, -0.4, PITCH_Z).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, D, H = 0.7, 0.8, 0.9
Z0 = -H / 2
YAW_Z = -0.19
PITCH_Z = 0.125
ORANGE = "M_PaintedMetal__e8762c"
YELLOW = "M_PaintedMetal__f2c12e"
rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)

# --- Base ---------------------------------------------------------------------------------------------
bp = []
bp.append(rw.rounded_box("plate", (W, W, 0.05), 0.016, (0, 0, Z0 + 0.025), mat="M_DarkMetal", segments=2))
SK = 0.56
bp.append(rw.rounded_box("skirt", (SK, SK, 0.1), 0.02, (0, 0, Z0 + 0.1), mat=YELLOW, segments=2))
# hazard stripes on the four skirt sides
for i in range(4):
    a = math.radians(90 * i)
    n = V((math.cos(a), math.sin(a), 0))
    u = V((-math.sin(a), math.cos(a), 0))
    for k in range(-2, 3):
        c = n * (SK / 2 + 0.001) + u * (k * 0.1) + V((0, 0, Z0 + 0.1))
        bp.append(pl.obox("stripe", (0.035, 0.11, 0.006), c, u + V((0, 0, 1)), n, "WarnBlack"))
for sx in (-1, 1):
    for sy in (-1, 1):
        bp.append(pl.bolt((sx * 0.31, sy * 0.31, Z0 + 0.05), (0, 0, 1), 0.024, 0.012, "M_Steel", washer=False,
                          bevel=False))
col = [(0.0, Z0 + 0.15), (0.2, Z0 + 0.15), (0.2, Z0 + 0.17), (0.15, Z0 + 0.19), (0.13, YAW_Z - 0.04),
       (0.16, YAW_Z - 0.025), (0.16, YAW_Z), (0.0, YAW_Z)]
bp.append(pl.lathe_axis("column", col, (0, 0, 1), (0, 0, 0), 20, "M_Steel", False, False, 40))
bp += pl.rivet_face_ring((0, 0, Z0 + 0.155), (0, 0, 1), 0.18, 6, 0.013, 0.006, "M_Steel", 0, 6)
base = rw.join(bp, "Base", origin=(0, 0, 0))
rw.smooth(base, 40)

# --- Yaw ----------------------------------------------------------------------------------------------
yp = []
yp.append(pl.lathe_axis("turntable", [(0.0, YAW_Z), (0.2, YAW_Z), (0.215, YAW_Z + 0.012), (0.215, YAW_Z + 0.04),
                                      (0.2, YAW_Z + 0.05), (0.0, YAW_Z + 0.05)], (0, 0, 1), (0, 0, 0), 24,
                        "M_DarkMetal", False, False, 40))
YK = 0.2                       # yoke plate centre x
yp.append(rw.rounded_box("yoke_floor", (2 * YK + 0.05, 0.2, 0.05), 0.016, (0, 0, YAW_Z + 0.07), mat="M_DarkMetal",
                         segments=2))
for s in (-1, 1):
    x = s * YK
    yp.append(rw.rounded_box("yoke", (0.05, 0.2, PITCH_Z - YAW_Z), 0.018,
                             (x, 0, (YAW_Z + 0.06 + PITCH_Z) / 2), mat="M_DarkMetal", segments=2))
    yp.append(rw.cylinder("yoke_top", 0.1, 0.05, 20, (x, 0, PITCH_Z), (0, 90, 0), mat="M_DarkMetal"))
    rw.add_bevel(yp[-1], 0.014, 1, 40)
    yp.append(pl.disc("hub", 0.065, 0.04, (s, 0, 0), (x + s * 0.035, 0, PITCH_Z), "M_Brass", 16, 0.35))
    yp.append(pl.bolt((x + s * 0.055, 0, PITCH_Z), (s, 0, 0), 0.026, 0.014, "M_Steel", washer=False))
    for (y, z) in ((-0.06, YAW_Z + 0.11), (0.06, YAW_Z + 0.11), (-0.06, PITCH_Z - 0.12), (0.06, PITCH_Z - 0.12)):
        yp.append(pl.rivet((x + s * 0.025, y, z), (s, 0, 0), 0.014, 0.007, "M_Brass", 6))
# warning lamp on a little post behind the gun
lamp_p = V((YK, 0.12, PITCH_Z + 0.13))
yp.append(rw.cylinder("lamp_post", 0.018, 0.12, 10, tuple(lamp_p - V((0, 0, 0.06))), mat="M_Steel"))
yp.append(pl.lathe_axis("lamp_base", [(0.0, 0.0), (0.04, 0.0), (0.04, 0.02), (0.0, 0.02)], (0, 0, 1),
                        tuple(lamp_p), 12, "M_DarkMetal", False, False, 40))
yp.append(rw.sphere("lamp", 0.034, 12, 6, tuple(lamp_p + V((0, 0, 0.03))), scale=(1, 1, 1.15), mat="M_TechGlow"))
yp.append(rw.torus("lamp_cage", 0.036, 0.006, 12, 4, tuple(lamp_p + V((0, 0, 0.035))), mat="M_Steel"))
yaw = rw.join(yp, "Yaw", origin=(0, 0, YAW_Z))
rw.smooth(yaw, 40)
pl.parent_keep(yaw, base)

# --- Pitch --------------------------------------------------------------------------------------------
pp = []
PZ = PITCH_Z
REC_Y0, REC_Y1 = -0.13, 0.17
pp.append(rw.rounded_box("receiver", (0.29, REC_Y1 - REC_Y0, 0.25), 0.04, (0, (REC_Y0 + REC_Y1) / 2, PZ),
                         mat=ORANGE, segments=3))
for y in (REC_Y0 + 0.04, REC_Y1 - 0.04):
    pp.append(rw.rounded_box("trim", (0.305, 0.035, 0.265), 0.012, (0, y, PZ), mat="M_Brass", segments=2))
for s in (-1, 1):
    pp.append(rw.cylinder("trunnion", 0.05, 0.06, 16, (s * 0.16, 0, PZ), (0, 90, 0), mat="M_Steel"))
    for y in (-0.03, 0.07):
        pp.append(pl.rivet((s * 0.145, y, PZ + 0.085), (s, 0, 0), 0.013, 0.006, "M_Brass", 6))
# front bearing collar where the barrels attach
pp.append(pl.lathe_axis("collar", [(0.0, 0.0), (0.1, 0.0), (0.1, 0.025), (0.085, 0.04), (0.0, 0.04)],
                        (0, -1, 0), (0, REC_Y0 + 0.005, PZ), 20, "M_Brass", False, False, 40))
# ammo drum on top (axis X)
DRUM_R = 0.1
dz = H / 2 - DRUM_R - 0.006       # the steel band (r + 0.006) reaches the top of the envelope
dy = 0.03
pp.append(pl.lathe_axis("drum", [(0.0, -0.105), (DRUM_R - 0.02, -0.105), (DRUM_R, -0.09), (DRUM_R, 0.09),
                                 (DRUM_R - 0.02, 0.105), (0.0, 0.105)], (1, 0, 0), (0, dy, dz), 20, "M_Brass",
                        False, False, 40))
pp.append(pl.band("drum_band", DRUM_R + 0.006, 0.03, 0.016, (1, 0, 0), (0, dy, dz), "M_Steel", 20, 0.0))
for s in (-1, 1):
    pp.append(pl.disc("drum_cap", 0.045, 0.02, (s, 0, 0), (s * 0.105, dy, dz), "M_Steel", 12, 0.4))
    pp.append(pl.bolt((s * 0.115, dy, dz), (s, 0, 0), 0.022, 0.01, "M_Brass", washer=False, bevel=False))
pp.append(rw.rounded_box("drum_saddle", (0.15, 0.15, dz - (PZ + 0.125) + 0.02), 0.012,
                         (0, dy, (dz + PZ + 0.125) / 2 - 0.02), mat="M_DarkMetal", segments=1))
# motor at the back: copper windings + domed cap reaching y = +D/2
pp.append(pl.lathe_axis("motor", [(0.0, REC_Y1 - 0.01), (0.095, REC_Y1 - 0.01), (0.095, 0.33), (0.08, 0.36),
                                  (0.05, 0.385), (0.0, D / 2)], (0, 1, 0), (0, 0, PZ), 20, "M_Steel", False,
                        False, 40))
pp.append(pl.band("winding", 0.108, 0.075, 0.02, (0, 1, 0), (0, 0.255, PZ), "M_Copper", 20, 0.0))
pp.append(pl.band("motor_fin", 0.114, 0.016, 0.03, (0, 1, 0), (0, 0.315, PZ), "M_Brass", 20, 0.0))
# sight on top-left of the receiver
pp.append(rw.rounded_box("sight", (0.03, 0.08, 0.05), 0.01, (-0.115, -0.06, PZ + 0.145), mat="M_DarkMetal",
                         segments=1))
pp.append(rw.sphere("sight_lens", 0.014, 10, 5, (-0.115, -0.103, PZ + 0.15), mat="M_TechGlow"))
pitch = rw.join(pp, "Pitch", origin=(0, 0, PZ))
rw.smooth(pitch, 40)
pl.parent_keep(pitch, yaw)

# --- Barrels ------------------------------------------------------------------------------------------
BARREL_Y0 = REC_Y0 - 0.035         # rear hub of the cluster (just in front of the bearing collar)
TIP = -D / 2
brl = []
brl.append(pl.lathe_axis("hub", [(0.0, 0.0), (0.085, 0.0), (0.09, 0.012), (0.09, 0.04), (0.07, 0.055),
                                 (0.0, 0.055)], (0, -1, 0), (0, BARREL_Y0, PZ), 20, "M_DarkMetal", False, False,
                         40))
brl.append(rw.cylinder("spindle", 0.03, abs(TIP - BARREL_Y0) - 0.01, 10,
                       (0, (TIP + BARREL_Y0) / 2 - 0.005, PZ), (90, 0, 0), mat="M_Steel"))
BR = 0.058                          # barrel circle radius
for i in range(6):
    a = math.radians(30 + 60 * i)
    off = V((math.cos(a) * BR, 0, math.sin(a) * BR))
    p1 = V((0, TIP, PZ)) + off
    L = (BARREL_Y0 - 0.03) - TIP
    # profile from the back end (h = L) to the muzzle (h = 0, at the tip) and down into a short bore
    b = pl.lathe_axis("barrel", [(0.023, L), (0.023, 0.03), (0.028, 0.026), (0.028, 0.0), (0.013, 0.0),
                                 (0.013, 0.015), (0.0, 0.015)], (0, 1, 0), tuple(p1), 10, "M_Steel", False, False,
                      40)
    # bore faces (centres within ~1.75 cm of the tip point) are dark; the muzzle ring stays steel
    rw.set_mat_where(b, "M_DarkMetal", lambda c, n, p1=p1: (c - p1).length < 0.019)
    brl.append(b)
for (y, w) in ((BARREL_Y0 - 0.08, 0.03), (TIP + 0.085, 0.035)):
    brl.append(pl.band("clamp", BR + 0.04, w, 0.03, (0, 1, 0), (0, y, PZ), "M_Brass", 20, 0.0))
barrels = rw.join(brl, "Barrels", origin=(0, BARREL_Y0, PZ))
rw.smooth(barrels, 40)
pl.parent_keep(barrels, pitch)

muzzle = pl.empty_at("Muzzle", (0, TIP, PZ), pitch)

pl.check("part_rivet_turret", (W, D, H))
rw.finish("part_rivet_turret", "parts", icon=True)
