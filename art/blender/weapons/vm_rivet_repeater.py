"""vm_rivet_repeater: first-person chunky rivet rifle.

Nodes (origin = grip centre; the muzzle points -Y):
  RivetRepeater  riveted brass receiver with a glowing pressure lamp and a steam valve, a steel barrel
                 with cooling fins and a slotted muzzle brake, a dark-iron drum magazine (brass rim,
                 rivets, winding key) under the receiver, ring sight, a stubby wooden stock and a
                 dark-wood pistol grip.
  Glove          the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle         empty at the muzzle-brake exit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

RAKE = 20.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
parts = []

# --- grip ------------------------------------------------------------------------------------------------
parts.append(glove.oriented_pillow("grip", (0.048, 0.064, 0.2), -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10,
                                   "M_WoodDark"))
parts.append(glove.oriented_pillow("pommel", (0.058, 0.074, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16,
                                   8, "M_Brass"))

# --- receiver ----------------------------------------------------------------------------------------------
RZ = 0.135                      # receiver centre height
RY0, RY1 = -0.205, 0.09
parts.append(rw.rounded_box("receiver", (0.078, RY1 - RY0, 0.1), 0.026, (0, (RY0 + RY1) / 2, RZ), mat="M_Brass",
                            segments=3))
# raised top rail
parts.append(rw.rounded_box("rail", (0.03, RY1 - RY0 - 0.06, 0.02), 0.008, (0, (RY0 + RY1) / 2 + 0.01, RZ + 0.055),
                            mat="M_Steel", segments=1))
# riveted steel straps around the receiver
for y in (RY0 + 0.045, RY1 - 0.05):
    parts.append(rw.rounded_box("strap", (0.086, 0.032, 0.108), 0.01, (0, y, RZ), mat="M_Steel", segments=1))
    for sx in (-1, 1):
        for z in (RZ + 0.03, RZ - 0.03):
            parts.append(pl.rivet((sx * 0.043, y, z), (sx, 0, 0), 0.0095, 0.006, "M_Brass", 6))
# glowing pressure lamp in a cage on the left side (+X, toward the player)
lc = V((0.039, -0.04, RZ))
parts.append(pl.disc("lamp_rim", 0.024, 0.014, (1, 0, 0), lc, "M_Steel", 16, 0.4))
parts.append(rw.sphere("lamp", 0.017, 12, 6, tuple(lc + V((0.008, 0, 0))), scale=(0.7, 1, 1), mat="M_TechGlow"))
for dz in (-0.008, 0.008):
    parts.append(pl.capsule("lamp_bar", lc + V((0.016, -0.018, dz)), lc + V((0.016, 0.018, dz)), 0.003, 4, 1,
                            "M_Steel"))
# steam valve wheel on top behind the sight
vc = V((0.0, 0.05, RZ + 0.08))
parts.append(rw.cylinder("valve_stem", 0.008, 0.03, 8, tuple(vc - V((0, 0, 0.018))), mat="M_Steel"))
parts.append(rw.torus("valve", 0.02, 0.005, 14, 4, tuple(vc), mat="M_Copper"))
parts.append(pl.capsule("valve_spoke", vc - V((0.02, 0, 0)), vc + V((0.02, 0, 0)), 0.004, 4, 1, "M_Copper"))
parts.append(pl.capsule("valve_spoke", vc - V((0, 0.02, 0)), vc + V((0, 0.02, 0)), 0.004, 4, 1, "M_Copper"))

# --- barrel with cooling fins + muzzle brake ----------------------------------------------------------------
BZ = RZ + 0.01
BY0, BY1 = RY0 + 0.01, -0.315
parts.append(pl.rod("barrel", (0, BY0, BZ), (0, BY1, BZ), 0.021, 14, "M_Steel"))
for i in range(5):
    y = RY0 - 0.02 - i * 0.017
    parts.append(pl.disc("fin", 0.042, 0.008, (0, 1, 0), (0, y, BZ), "M_Steel", 18, 0.45))
parts.append(pl.band("barrel_band", 0.03, 0.02, 0.012, (0, 1, 0), (0, RY0 - 0.004, BZ), "M_Brass", 16, 0.0))
brake = pl.lathe_axis("brake", [(0.0, 0.0), (0.03, 0.0), (0.033, 0.005), (0.033, 0.04), (0.03, 0.045),
                                (0.014, 0.045), (0.014, 0.04), (0.0, 0.04)], (0, -1, 0), (0, BY1 + 0.012, BZ), 16,
                      "M_DarkMetal", False, False, 45)
pl.carve(brake, [pl.obox("slot", (0.1, 0.012, 0.016), (0, BY1 - 0.01 - k * 0.016, BZ), (1, 0, 0), (0, 0, 1))
                 for k in range(2)])
parts.append(brake)
TIP_Y = BY1 + 0.012 - 0.045
# front ring sight
parts.append(rw.cylinder("sight_post", 0.006, 0.03, 8, (0, RY0 + 0.02, RZ + 0.075), mat="M_Steel"))
parts.append(rw.torus("sight_ring", 0.016, 0.0045, 14, 4, (0, RY0 + 0.02, RZ + 0.1), (90, 0, 0), mat="M_Brass"))

# --- drum magazine under the receiver front -------------------------------------------------------------------
DC = V((0, -0.15, 0.048))
DR = 0.062
DW = 0.064
parts.append(pl.lathe_axis("drum", [(0.0, -DW / 2), (DR - 0.012, -DW / 2), (DR, -DW / 2 + 0.012),
                                    (DR, DW / 2 - 0.012), (DR - 0.012, DW / 2), (0.0, DW / 2)], (1, 0, 0), DC, 24,
                           "M_DarkMetal", False, False, 40))
parts.append(pl.band("drum_rim", DR + 0.006, 0.026, 0.014, (1, 0, 0), DC, "M_Brass", 24, 0.0))
for sx in (-1, 1):
    face = DC + V((sx * DW / 2, 0, 0))
    parts.append(pl.disc("drum_hub", 0.022, 0.012, (sx, 0, 0), face, "M_Brass", 14, 0.4))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        parts.append(pl.rivet(face + V((0, math.cos(a) * 0.044, math.sin(a) * 0.044)), (sx, 0, 0), 0.007, 0.005,
                              "M_Steel", 6))
# winding key on the left face
kc = DC + V((DW / 2 + 0.012, 0, 0))
parts.append(rw.cylinder("key_stem", 0.006, 0.02, 8, tuple(kc), (0, 90, 0), mat="M_Steel"))
parts.append(rw.rounded_box("key", (0.008, 0.044, 0.016), 0.005, tuple(kc + V((0.012, 0, 0))), mat="M_Brass",
                            segments=1))
# feed neck into the receiver
parts.append(rw.rounded_box("feed", (0.05, 0.045, 0.04), 0.01, (0, DC.y + 0.01, RZ - 0.06), mat="M_Brass",
                            segments=1))

# --- stubby stock ----------------------------------------------------------------------------------------------
stock = rw.rounded_box("stock", (0.06, 0.12, 0.075), 0.022, (0, 0, 0), mat="M_WoodDark", segments=2)
rw.apply_modifiers(stock)
pl.xform(stock, pl.Matrix.Rotation(math.radians(-12), 4, 'X'))
stock.location = (0, RY1 + 0.045, RZ - 0.012)
parts.append(stock)
butt = rw.rounded_box("butt", (0.068, 0.02, 0.085), 0.008, (0, 0, 0), mat="M_Brass", segments=1)
rw.apply_modifiers(butt)
pl.xform(butt, pl.Matrix.Rotation(math.radians(-12), 4, 'X'))
butt.location = (0, RY1 + 0.105, RZ - 0.026)
parts.append(butt)

rifle = rw.join(parts, "RivetRepeater", origin=(0, 0, 0))
rw.smooth(rifle, 45)

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, TIP_Y, BZ))
pl.check("vm_rivet_repeater", (0, 0, 0))
rw.finish("vm_rivet_repeater", "weapons", icon=True)
