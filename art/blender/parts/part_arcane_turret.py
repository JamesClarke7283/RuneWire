"""part_arcane_turret: 0.7 x 0.7 x 0.9 m arcane crystal turret.

Nodes (origin of the whole model = bounding-box centre = Base origin):
  Base      brass round plinth with a glowing rune ring, rivets and bolted feet.
    Yaw     pivot at the base top centre (0, 0, YAW_Z); turntable + two-armed brass fork with bearing
            hubs, and a little charging crystal cluster between the arms. Rotates about Z.
      Pitch pivot on the fork axis (0, 0, PITCH_Z); brass emitter housing with a glowing rune on the
            back, a teal crystal (M_Crystal) pointing -Y wrapped by three brass focusing rings on
            prongs, and a crest fin with a sight gem on top. Rotates about X.
        Muzzle  empty at the crystal tip.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, H = 0.7, 0.9
Z0 = -H / 2
YAW_Z = -0.13
PITCH_Z = 0.27
TIP_Y = -W / 2
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

# --- Base ---------------------------------------------------------------------------------------------
bp = []
# the column has two brass lips with a glowing rune ring between them (all one lathe)
RZ0, RZ1 = Z0 + 0.165, Z0 + 0.215
base_prof = [(0.0, Z0), (0.35, Z0), (0.35, Z0 + 0.04), (0.335, Z0 + 0.06), (0.28, Z0 + 0.075), (0.25, Z0 + 0.1),
             (0.226, RZ0 - 0.022), (0.236, RZ0 - 0.012), (0.236, RZ0), (0.212, RZ0), (0.212, RZ1),
             (0.232, RZ1), (0.232, RZ1 + 0.012), (0.2, RZ1 + 0.03), (0.188, Z0 + 0.27), (0.185, YAW_Z - 0.03),
             (0.2, YAW_Z - 0.02), (0.2, YAW_Z), (0.0, YAW_Z)]
b = pl.lathe_axis("base", base_prof, (0, 0, 1), (0, 0, 0), 24, "M_Brass", False, False, 40)
rw.set_mat_where(b, "M_RuneGlow", lambda c, n: RZ0 + 0.001 < c.z < RZ1 - 0.001 and abs(n.z) < 0.3 and
                 (c.x ** 2 + c.y ** 2) ** 0.5 < 0.215)
bp.append(b)
bp += pl.rivet_face_ring((0, 0, Z0 + 0.075), (0, 0, 1), 0.3, 8, 0.016, 0.008, "M_Brass", 22.5, 6)
# bolted feet
for i in range(4):
    a = math.radians(45 + 90 * i)
    d = V((math.cos(a), math.sin(a), 0))
    bp.append(pl.rivet(d * 0.315 + V((0, 0, Z0 + 0.04)), (0, 0, 1), 0.024, 0.012, "NailHead", 6))
base = rw.join(bp, "Base", origin=(0, 0, 0))
rw.smooth(base, 40)

# --- Yaw ----------------------------------------------------------------------------------------------
yp = []
yp.append(pl.lathe_axis("turntable", [(0.0, YAW_Z), (0.19, YAW_Z), (0.205, YAW_Z + 0.012), (0.205, YAW_Z + 0.04),
                                      (0.19, YAW_Z + 0.055), (0.0, YAW_Z + 0.055)], (0, 0, 1), (0, 0, 0), 28,
                        "M_Brass", False, False, 40))
yp += pl.rivet_face_ring((0, 0, YAW_Z + 0.055), (0, 0, 1), 0.165, 6, 0.014, 0.007, "M_Steel", 0, 6)
ARM_X = 0.2
for s in (-1, 1):
    x = s * ARM_X
    # arm plate: lower block + rounded top around the axis
    yp.append(rw.rounded_box("arm", (0.06, 0.17, PITCH_Z - YAW_Z - 0.04), 0.02,
                             (x, 0, (YAW_Z + 0.04 + PITCH_Z) / 2), mat="M_Brass", segments=2))
    yp.append(rw.cylinder("arm_top", 0.085, 0.06, 24, (x, 0, PITCH_Z), (0, 90, 0), mat="M_Brass"))
    rw.add_bevel(yp[-1], 0.015, 2, 40)
    # bearing hub on the outside
    yp.append(pl.disc("hub", 0.06, 0.04, (s, 0, 0), (x + s * 0.04, 0, PITCH_Z), "M_Steel", 20, 0.35))
    yp += pl.rivet_face_ring((x + s * 0.03, 0, PITCH_Z), (s, 0, 0), 0.07, 6, 0.011, 0.006, "M_Steel", 30, 6)
    yp.append(pl.rivet((x + s * 0.06, 0, PITCH_Z), (s, 0, 0), 0.025, 0.012, "M_Brass", 10))
# charging crystal cluster between the arms
CR = "M_Crystal"
cz = YAW_Z + 0.05
yp.append(pl.lathe_axis("cradle", [(0.0, cz), (0.07, cz), (0.075, cz + 0.02), (0.05, cz + 0.035), (0.0, cz + 0.035)],
                        (0, 0, 1), (0, 0, 0), 16, "M_Steel", False, False, 40))
yp.append(pl.crystal("charge", (0, 0, cz + 0.02), (0.1, 0.05, 1), 0.15, 0.035, 6, 0.32, 0.1, CR))
yp.append(pl.crystal("charge", (0.03, -0.01, cz + 0.02), (0.7, -0.2, 1), 0.09, 0.022, 6, 0.32, 0.1, CR, 15))
yp.append(pl.crystal("charge", (-0.03, 0.01, cz + 0.02), (-0.6, 0.3, 1), 0.08, 0.02, 6, 0.32, 0.1, CR, 40))
yaw = rw.join(yp, "Yaw", origin=(0, 0, YAW_Z))
rw.smooth(yaw, 40)
pl.parent_keep(yaw, base)

# --- Pitch --------------------------------------------------------------------------------------------
pp = []
PZ = PITCH_Z
RH = 0.12
# housing along Y: rounded back cap at +Y, body, nose narrowing toward -Y (lathe "height" runs along -Y)
house = [(0.0, -0.2), (0.07, -0.195), (0.105, -0.175), (RH, -0.14), (RH, 0.03), (0.105, 0.06), (0.08, 0.1),
         (0.072, 0.12), (0.0, 0.12)]
pp.append(pl.lathe_axis("housing", house, (0, -1, 0), (0, 0, PZ), 28, "M_Brass", False, False, 40))
for y in (0.13, -0.02):
    pp.append(pl.band("house_band", RH + 0.012, 0.03, 0.02, (0, 1, 0), (0, y, PZ), "M_Steel", 24))
# axle stubs into the fork
for s in (-1, 1):
    pp.append(rw.cylinder("axle", 0.04, 0.07, 16, (s * (RH + 0.03), 0, PZ), (0, 90, 0), mat="M_Steel"))
# glowing rune disc on the back cap
pp.append(pl.disc("back_rune_disc", 0.06, 0.02, (0, 1, 0), (0, 0.195, PZ), "M_Brass", 20, 0.4))
pp += pl.glyph("ingwaz", (0, 0.207, PZ), (-1, 0, 0), (0, 0, 1), 0.075, 0.014, 0.01, "M_RuneGlow")
# crystal emitter pointing -Y
crystal_base_y = -0.1
pp.append(pl.crystal("emitter", (0, crystal_base_y, PZ), (0, -1, 0), crystal_base_y - TIP_Y, 0.06, 6, 0.3, 0.08,
                     CR, 0))
# focusing rings on three prongs
rings = ((-0.17, 0.1), (-0.235, 0.085), (-0.295, 0.068))
for (y, r) in rings:
    pp.append(rw.torus("focus_ring", r, 0.015, 20, 6, (0, y, PZ), (90, 0, 0), mat="M_Brass"))
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = V((math.cos(a), 0, math.sin(a)))
    pts = [V((0, -0.13, PZ)) + d * 0.1, V((0, rings[0][0], PZ)) + d * rings[0][1],
           V((0, rings[2][0], PZ)) + d * rings[2][1]]
    pp.append(pl.sausage("prong", pts, [0.016, 0.014, 0.012], 8, 2, "M_Brass", (True, True), 2, False, 50))
# crest fin with a sight gem
top = H / 2
pp.append(rw.rounded_box("crest", (0.04, 0.2, top - (PZ + RH) + 0.03), 0.015,
                         (0, 0.02, (PZ + RH - 0.03 + top) / 2), mat="M_Brass", segments=2))
pp.append(rw.sphere("sight", 0.024, 12, 6, (0, -0.07, top - 0.03), mat="M_RuneGlow"))
pitch = rw.join(pp, "Pitch", origin=(0, 0, PZ))
rw.smooth(pitch, 40)
pl.parent_keep(pitch, yaw)

muzzle = pl.empty_at("Muzzle", (0, TIP_Y, PZ), pitch)

pl.check("part_arcane_turret", (W, W, H))
rw.finish("part_arcane_turret", "parts", icon=True)
