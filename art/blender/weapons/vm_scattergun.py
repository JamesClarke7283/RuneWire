"""vm_scattergun: first-person "Cogburst Scattergun", a chunky brass blunderbuss pump-shotgun.

Nodes (origin = grip centre; the muzzle points -Y):
  Scattergun  riveted steel receiver with a hazard-orange top cover, a big brass drive gear and a copper
              idler gear on the +X side (player view), a leather shell-holder strip with four fat
              red/brass shells on the -X side, a fat brass barrel with steel bands and a hazard-striped
              collar, a clamp block, a flared bell-mouth with a dark bore, a steel magazine tube, a short
              dark-wood stock stub (kept low so it doesn't fill the first-person view) with a brass butt
              plate, a copper cog and gear medallions, a dark-wood pistol grip with a brass pommel and a
              lanyard ring, a brass trigger guard and the rarity indicator lamp on the top cover.
  Pump        the wooden pump grip with brass cog rims and a toothed steel rack (child of Scattergun, origin
              at its rest centre). The game slides it 0.06 m toward +Y and back: the rack then runs just
              under the big drive gear (0.5 mm clear) and nothing else is in its way; only the magazine
              tube passes through the pump, hidden inside it.
  Glove       the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle      empty at the centre of the bell mouth.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import new_weapon_helpers as nw  # noqa: E402

glove, pl, rw, V = nw.glove, nw.pl, nw.rw, nw.V
rw.reset()

RAKE = 18.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))

ORANGE = "M_PaintedMetal__f26b1d"
rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)
rw.flat("ShellRed", "d8322a", 0.45, 0.0)
rw.flat("ScrewSlot", "1e1a22", 0.6, 0.0)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
parts = []
pump_parts = []

# --- receiver ---------------------------------------------------------------------------------------------
RX = 0.043                      # half width
RY0, RY1 = -0.115, 0.075        # front / back
RZ0, RZ1 = 0.085, 0.205         # bottom / top
RZ = (RZ0 + RZ1) / 2
RYC = (RY0 + RY1) / 2
parts.append(rw.rounded_box("receiver", (2 * RX, RY1 - RY0, RZ1 - RZ0), 0.02, (0, RYC, RZ), mat="M_Steel",
                            segments=2))
# brass strap around the back end, riveted
parts.append(rw.rounded_box("rear_strap", (2 * RX + 0.008, 0.02, RZ1 - RZ0 + 0.008), 0.008, (0, RY1 - 0.016, RZ),
                            mat="M_Brass", segments=2))
for sx in (-1, 1):
    for z in (RZ0 + 0.022, RZ1 - 0.022):
        parts.append(nw.stud((sx * (RX + 0.004), RY1 - 0.016, z), (sx, 0, 0), 0.0065, 0.0045, "M_Steel", 6))
# hazard-orange top cover with corner rivets and a rear notch sight
CY = RYC - 0.004
parts.append(rw.rounded_box("top_cover", (0.072, 0.168, 0.018), 0.007, (0, CY, RZ1 + 0.001), mat=ORANGE,
                            segments=2))
for sx in (-1, 1):
    for dy in (-0.07, 0.07):
        parts.append(nw.stud((sx * 0.026, CY + dy, RZ1 + 0.01), (0, 0, 1), 0.006, 0.004, "M_Brass", 6))
for sx in (-1, 1):
    parts.append(rw.rounded_box("rear_sight", (0.009, 0.012, 0.018), 0.003, (sx * 0.0095, RY1 - 0.03, RZ1 + 0.018),
                                mat="M_Steel", segments=1))
# rarity indicator lamp on the top cover, toward the player (+X, back)
parts += nw.lamp(V((0.021, 0.03, RZ1 + 0.009)), V((0.25, 0.1, 1.0)), 0.0105, RARITY, "M_Steel", cage=False,
                 name="rarity_lamp")

# --- +X side: big drive gear + copper idler gear + orange plate -------------------------------------------
GC = V((RX + 0.006, -0.07, 0.155))
parts += nw.spoked_gear("drive_gear", 0.046, 12, 0.012, X, GC, "M_Brass", "M_Steel", spokes=5, spin=13.75,
                        chamfer=0.0018)
IC = GC + V((0, 0.906, 0.423)) * 0.0637
IC.x = RX + 0.005
parts += nw.spoked_gear("idler_gear", 0.024, 8, 0.01, X, IC, "M_Copper", "M_Steel", spokes=4, spin=30.625)
parts.append(rw.rounded_box("side_plate", (0.008, 0.034, 0.084), 0.004, (RX + 0.001, 0.035, RZ - 0.002),
                            mat=ORANGE, segments=1))
for dy in (-0.01, 0.01):
    for z in (RZ - 0.034, RZ + 0.03):
        parts.append(nw.stud((RX + 0.005, 0.035 + dy, z), (1, 0, 0), 0.0055, 0.004, "M_Brass", 6))
parts.append(rw.rounded_box("warn_stripe", (0.004, 0.01, 0.05), 0.002, (RX + 0.0045, 0.035, RZ - 0.002),
                            rot=(35, 0, 0), mat="WarnBlack", segments=1))

# --- -X side: shell holder with four fat shells ----------------------------------------------------------
SHELL_R, SHELL_L = 0.0125, 0.064
SX = -RX - 0.0045 - SHELL_R
shell_ys = [-0.087, -0.055, -0.023, 0.009]
for y in shell_ys:
    parts += nw.shell(V((SX, y, 0.103)), Z, SHELL_L, SHELL_R, "ShellRed", "M_Brass", "M_Copper", 10)
parts.append(rw.rounded_box("holder_back", (0.006, 0.132, 0.03), 0.003, (-RX - 0.002, -0.039, 0.137),
                            mat="M_Leather", segments=1))
loop = [V((-RX - 0.003, 0.026, 0.137))]
for i, y in enumerate(shell_ys[::-1]):
    loop.append(V((SX - SHELL_R - 0.0032, y, 0.137)))
    if i < 3:
        loop.append(V((SX + 0.003, y - 0.016, 0.137)))
loop.append(V((-RX - 0.003, -0.104, 0.137)))
parts.append(pl.sausage("holder_loops", loop, 0.0125, 6, 3, "M_Leather", (False, False), 1, True, 50,
                        scale_xy=(1.0, 0.26), up_hint=(0, 0, 1)))
for y in (0.026, -0.104):
    parts.append(nw.stud((-RX - 0.006, y, 0.137), (-1, 0, 0), 0.0065, 0.0045, "M_Brass", 6))
# rivet rows along the -X top and bottom edges, and a brass maker's plate at the back
parts += nw.rivet_line((-RX, -0.098, RZ1 - 0.012), (-RX, 0.04, RZ1 - 0.012), 6, (-1, 0, 0), 0.0058, 0.004,
                       "M_Brass")
parts += nw.rivet_line((-RX, -0.098, RZ0 + 0.011), (-RX, 0.0, RZ0 + 0.011), 4, (-1, 0, 0), 0.0058, 0.004,
                       "M_Brass")
parts.append(rw.rounded_box("maker_plate", (0.006, 0.03, 0.05), 0.004, (-RX - 0.001, 0.039, RZ), mat="M_Brass",
                            segments=1))
for z in (RZ - 0.015, RZ + 0.015):
    parts += nw.screw(V((-RX - 0.004, 0.039, z)), (-1, 0, 0), 0.0055, "M_Steel", (0, 1, 1))

# --- barrel, bands, clamp and bell ------------------------------------------------------------------------
BZ, BR = 0.172, 0.025
TZ, TR = 0.112, 0.0145          # magazine tube under the barrel
Y_BELL = -0.29
parts.append(pl.rod("barrel", (0, RY0 + 0.01, BZ), (0, Y_BELL - 0.012, BZ), BR, 20, "M_Brass"))
parts.append(pl.band("barrel_collar", 0.033, 0.014, 0.008, Y, (0, RY0 - 0.006, BZ), "M_Brass", 20, 0.4))
for y in (-0.152, -0.212):
    parts.append(pl.band("barrel_band", 0.031, 0.013, 0.008, Y, (0, y, BZ), "M_Steel", 20, 0.4))
    for k in range(3):
        a = math.radians(45 + 45 * k)
        d = V((math.cos(a), 0, math.sin(a)))
        parts.append(nw.stud(V((0, y, BZ)) + d * 0.031, d, 0.0045, 0.0035, "M_Brass", 6))
parts += nw.hazard_band("hazard", 0.0305, 0.03, Y, (0, -0.252, BZ), ORANGE, "WarnBlack", stripes=6, slant=28,
                         half_w=14.0)
# clamp block joining barrel and magazine tube, with side screws and a bead sight
CLY = -0.279
parts.append(rw.rounded_box("clamp", (0.058, 0.014, 0.108), 0.005, (0, CLY, 0.1465), mat="M_Steel", segments=2))
for sx in (-1, 1):
    parts += nw.screw(V((sx * 0.029, CLY, BZ)), (sx, 0, 0), 0.0055, "M_Steel", (0, 0, 1))
    parts += nw.screw(V((sx * 0.029, CLY, TZ)), (sx, 0, 0), 0.0055, "M_Steel", (0, 1, 1))
parts.append(rw.rounded_box("bead_post", (0.012, 0.012, 0.012), 0.003, (0, CLY, 0.204), mat="M_Steel", segments=1))
parts.append(rw.sphere("bead", 0.0075, 10, 5, (0, CLY, 0.213), mat="M_Brass"))
# the bell-mouth: one closed lathe, the inside painted dark
bell = [(0.0, 0.04), (0.02, 0.046), (0.029, 0.058), (0.039, 0.072), (0.049, 0.084), (0.057, 0.093),
        (0.064, 0.0965), (0.07, 0.0955), (0.0735, 0.091), (0.073, 0.086), (0.068, 0.081), (0.059, 0.074),
        (0.047, 0.061), (0.037, 0.045), (0.031, 0.028), (0.0285, 0.012), (0.028, 0.0), (0.0, 0.0)]
bell_o = pl.lathe_axis("bell", bell, (0, -1, 0), (0, Y_BELL, BZ), 24, "M_Brass", False, False, 40)
nw.mat_where(bell_o, "M_DarkMetal", nw.inner_faces((0, Y_BELL, BZ), (0, 1, 0), -0.2))
parts.append(bell_o)
parts.append(pl.band("bell_ring", 0.0325, 0.012, 0.007, Y, (0, Y_BELL - 0.008, BZ), "M_Steel", 20, 0.4))
for k in range(6):
    a = math.radians(30 + 60 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    parts.append(nw.stud(V((0, Y_BELL - 0.075, BZ)) + d * 0.0575, (d + V((0, -0.9, 0))).normalized(), 0.0055, 0.004,
                          "M_Steel", 6))
MOUTH_Y = Y_BELL - 0.0965
# magazine tube with a knurled end cap and a brass collar at the receiver
parts.append(pl.rod("mag_tube", (0, RY0 + 0.01, TZ), (0, -0.288, TZ), TR, 14, "M_Steel"))
parts.append(pl.band("tube_collar", 0.0195, 0.01, 0.005, Y, (0, RY0 - 0.004, TZ), "M_Brass", 14, 0.4))
parts.append(nw.gear("tube_cap", 0.0175, 10, 0.012, Y, (0, -0.293, TZ), "M_Steel", depth=0.0022))
parts.append(rw.sphere("tube_cap_dome", 0.0115, 10, 4, (0, -0.298, TZ), scale=(1, 0.6, 1), mat="M_Brass"))

# --- stock stub: short and dropped, so it stays out of the first-person view ------------------------------
SY0, SY1 = RY1 - 0.008, 0.138
stock = nw.slab("stock", [(SY0, 0.176), (SY0, 0.094), (SY1, 0.07), (SY1, 0.156)], 0.056, (0, 0, 0), Y, Z,
                "M_WoodDark", bevel=0.013, segments=3)
parts.append(stock)
BUTT = V((0, SY1 + 0.004, 0.113))
parts.append(rw.rounded_box("butt_plate", (0.062, 0.012, 0.092), 0.005, tuple(BUTT), mat="M_Brass", segments=2))
parts.append(nw.gear("butt_cog", 0.022, 8, 0.006, Y, BUTT + V((0, 0.008, 0)), "M_Copper", depth=0.0045,
                     spin=11.25))
parts.append(nw.stud(BUTT + V((0, 0.011, 0)), Y, 0.007, 0.004, "M_Brass", 8))
for sx in (-1, 1):
    for dz in (-0.034, 0.034):
        parts.append(nw.stud(BUTT + V((sx * 0.022, 0.006, dz)), Y, 0.0048, 0.0032, "M_Steel", 6))
    parts.append(nw.gear("medallion", 0.017, 8, 0.006, (sx, 0, 0), (sx * 0.0285, 0.103, 0.124), "M_Brass",
                         depth=0.004, spin=11.25))
    parts.append(nw.stud((sx * 0.0315, 0.103, 0.124), (sx, 0, 0), 0.0062, 0.004, "M_Copper", 8))

# --- pistol grip, trigger guard, trigger ------------------------------------------------------------------
parts.append(glove.oriented_pillow("grip", (0.05, 0.066, 0.2), -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10,
                                   "M_WoodDark"))
parts.append(glove.oriented_pillow("pommel", (0.06, 0.076, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16,
                                   8, "M_Brass"))
ring = rw.torus("lanyard_ring", 0.011, 0.0042, 14, 5, (0, 0, 0), mat="M_Steel")
pl.align(ring, X, A * -0.122 - fr * -0.014)
parts.append(ring)
guard = [(0, -0.106, RZ0 + 0.006), (0, -0.121, 0.04), (0, -0.104, 0.006), (0, -0.074, -0.006), (0, -0.036, -0.004)]
parts.append(pl.sausage("guard", guard, 0.0085, 8, 3, "M_Brass", (True, True), 2, True, 60))
parts.append(pl.capsule("trigger", (0, -0.08, RZ0 + 0.004), (0, -0.092, 0.05), 0.0072, 8, 2, "M_Steel"))

gun = rw.join(parts, "Scattergun", origin=(0, 0, 0))
rw.smooth(gun, 45)

# --- pump (separate, slides +0.06 Y) ----------------------------------------------------------------------
PZ = 0.105
PY0, PY1 = -0.1925, -0.2675     # rear / front at rest
PC = V((0, (PY0 + PY1) / 2, PZ))
pump_prof = [(0.0, 0.0), (0.024, 0.0), (0.0285, 0.006), (0.029, 0.014), (0.025, 0.02), (0.025, 0.025),
             (0.029, 0.031), (0.029, 0.044), (0.025, 0.05), (0.025, 0.055), (0.029, 0.061), (0.0285, 0.069),
             (0.024, 0.075), (0.0, 0.075)]
pump_parts.append(pl.lathe_axis("pump_body", pump_prof, (0, -1, 0), (0, PY0, PZ), 20, "M_WoodDark", False, False,
                                40))
for y in (PY0 - 0.005, PY1 + 0.005):
    pump_parts.append(nw.gear("pump_cog", 0.033, 12, 0.01, Y, (0, y, PZ), "M_Brass", depth=0.005))
for sx in (-1, 1):
    pump_parts.append(nw.stud((sx * 0.029, PC.y, PZ), (sx, 0, 0), 0.0065, 0.0045, "M_Brass", 6))
# toothed rack on the +X side; at rest its back end sits under the drive gear
RK_Y0, RK_Y1 = -0.07, -0.232
pump_parts.append(nw.rack("pump_rack", RK_Y0 - RK_Y1, 0.009, 0.01, 8, 0.0055,
                          ((RX + 0.006), (RK_Y0 + RK_Y1) / 2, 0.0985), Y, Z, "M_Steel"))
for y in (-0.212, -0.226):
    pump_parts.append(rw.rounded_box("rack_bracket", (0.03, 0.01, 0.012), 0.003, (0.033, y, 0.0985),
                                     mat="M_Steel", segments=1))
pump = rw.join(pump_parts, "Pump", origin=tuple(PC))
rw.smooth(pump, 45)
pl.parent_keep(pump, gun)

# --- glove + empties --------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
rw.empty("Muzzle", (0, MOUTH_Y, BZ))
pl.check("vm_scattergun", (0, 0, 0))
rw.finish("vm_scattergun", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_scattergun")
