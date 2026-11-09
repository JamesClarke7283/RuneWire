"""vm_tesla_lance: first-person "Tesla Lance", a long charge-up shock rifle.

Nodes (origin = grip centre; the muzzle points -Y):
  TeslaLance  brass receiver with riveted steel side plates, a charge dial on the +X side (player view) and
              a dynamo crank on the -X side; three glass capacitor jars along the top (brass cups and caps,
              terminal knobs, copper jumper wires; the two small jars hold copper coils); a side-mounted
              brass scope; a slim steel barrel on a wooden fore-end with a brass band, an exposed copper
              coil winding between brass flanges, rubber cables on both sides, and a muzzle collar
              carrying three forward-pointing copper tesla prongs around a glowing emitter bead; a
              dark-wood stock with a brass butt plate and the rarity gem, and a dark-wood pistol grip.
  ChargeCore  glowing cyan spark-core floating in the largest (rear) jar (child of TeslaLance, origin at its
              centre). The game scales it 0.3-1.0 while charging; at 1.0 it still clears the glass.
  Glove       the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle      empty on the barrel axis, level with the prong tips (where the arc forms).
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

CYAN = "5ff3ff"
CORE = rw.glow("ChargeCoreGlow", CYAN, 5.0)
EMIT = rw.glow("LanceGlow", CYAN, 4.0)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
rw.flat("DialFace", "f6ead0", 0.5, 0.0)
rw.flat("DialInk", "2a2230", 0.6, 0.0)
rw.flat("DialNeedle", "d8392b", 0.5, 0.0)
rw.flat("DialTeal", "2fb5b0", 0.5, 0.0)
rw.flat("DialYellow", "ffc531", 0.5, 0.0)
rw.flat("DialRed", "e0452f", 0.5, 0.0)
rw.flat("ScrewSlot", "1e1a22", 0.6, 0.0)
parts = []

# --- receiver -------------------------------------------------------------------------------------------
RX = 0.039
RY0, RY1 = -0.125, 0.085
RZ0, RZ1 = 0.085, 0.185
RZ = (RZ0 + RZ1) / 2
RYC = (RY0 + RY1) / 2
parts.append(rw.rounded_box("receiver", (2 * RX, RY1 - RY0, RZ1 - RZ0), 0.02, (0, RYC, RZ), mat="M_Brass",
                            segments=2))
for sx in (-1, 1):
    parts.append(rw.rounded_box("side_plate", (0.006, 0.158, 0.068), 0.004, (sx * (RX + 0.001), RYC - 0.004, RZ),
                                mat="M_Steel", segments=1))
    for y in (RYC - 0.074, RYC + 0.066):
        for z in (RZ - 0.025, RZ + 0.025):
            parts.append(nw.stud((sx * (RX + 0.004), y, z), (sx, 0, 0), 0.0058, 0.004, "M_Brass", 6))
# brass collar where the barrel leaves the receiver
BZ, BR = 0.15, 0.0155
parts.append(pl.band("barrel_collar", 0.025, 0.014, 0.01, Y, (0, RY0 - 0.004, BZ), "M_Brass", 18, 0.4))

# charge dial on the +X side, facing the player
DC = V((RX + 0.004, -0.068, RZ + 0.002))
parts += nw.gauge(DC, X, Z, 0.027, "M_Brass", "DialFace", "DialInk", "DialNeedle",
                  zones=(("DialTeal", -120, -25), ("DialYellow", -25, 45), ("DialRed", 45, 120)),
                  needle_deg=-62.0, ticks=7, depth=0.012, segs=16, name="charge_dial")

# dynamo crank on the -X side (hub, arm, wooden knob)
HC = V((-RX - 0.006, 0.03, RZ + 0.006))
parts.append(pl.disc("crank_hub", 0.017, 0.01, -X, HC, "M_Brass", 16, 0.4))
parts.append(pl.bolt(HC - X * 0.006, -X, 0.007, 0.006, "M_Steel", "crank_bolt"))
arm_end = HC + V((-0.012, 0.03, -0.028))
parts.append(pl.capsule("crank_arm", HC - X * 0.008, arm_end, 0.0055, 8, 2, "M_Brass"))
parts.append(pl.capsule("crank_knob", arm_end + V((-0.004, 0, 0)), arm_end + V((-0.026, 0, 0)), 0.0085, 10, 2,
                        "M_WoodDark"))
parts.append(rw.rounded_box("name_plate", (0.005, 0.044, 0.022), 0.003, (-RX - 0.003, -0.07, RZ + 0.02),
                            mat="M_Brass", segments=1))
for y in (-0.088, -0.052):
    parts += nw.screw(V((-RX - 0.0055, y, RZ + 0.02)), -X, 0.0042, "M_Steel", (0, 1, 1))

# --- capacitor jars along the top ---------------------------------------------------------------------------
# (centre Y, glass radius, glass height); jar 0 is the largest and holds the ChargeCore
JARS = [(-0.03, 0.031, 0.057), (-0.122, 0.025, 0.046), (-0.2, 0.021, 0.038)]
JZ0 = RZ1 + 0.001                          # cups stand on the receiver top / the barrel rail
parts.append(rw.rounded_box("jar_rail", (0.034, 0.172, 0.022), 0.008, (0, -0.164, RZ1 - 0.008), mat="M_Brass",
                            segments=2))
for y in (-0.168, -0.232):
    parts.append(rw.rounded_box("rail_post", (0.018, 0.012, 0.03), 0.004, (0, y, BZ + 0.016), mat="M_Brass",
                                segments=1))
knobs = []
core_c = None
for i, (jy, r, h) in enumerate(JARS):
    base = V((0, jy, JZ0))
    cup = [(0.0, 0.0), (r + 0.005, 0.0), (r + 0.0065, 0.005), (r + 0.005, 0.012), (r + 0.002, 0.0145),
           (0.0, 0.0145)]
    parts.append(pl.lathe_axis("jar_cup", cup, Z, base, 16, "M_Brass", False, False, 40))
    g0 = base + Z * 0.012
    glass = [(0.0, 0.0), (r * 0.94, 0.0), (r, 0.006), (r, h - 0.007), (r * 0.93, h), (0.0, h)]
    parts.append(pl.lathe_axis("jar_glass", glass, Z, g0, 18, "M_Glass", False, False, 50))
    cap_b = g0 + Z * (h - 0.004)
    cap = [(0.0, 0.0), (r + 0.004, 0.0), (r + 0.0055, 0.005), (r + 0.003, 0.0105), (r * 0.55, 0.0145),
           (0.0, 0.0155)]
    parts.append(pl.lathe_axis("jar_cap", cap, Z, cap_b, 16, "M_Brass", False, False, 40))
    post_b = cap_b + Z * 0.014
    parts.append(pl.rod("jar_post", post_b, post_b + Z * 0.011, 0.0042, 8, "M_Steel"))
    knob = post_b + Z * (0.011 + 0.006)
    parts.append(rw.sphere("jar_knob", 0.0085, 10, 5, tuple(knob), mat="M_Brass"))
    knobs.append(knob)
    # four little screws around each cup
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = V((math.cos(a), math.sin(a), 0))
        parts.append(nw.stud(base + d * (r + 0.0035) + Z * 0.0115, (d + Z).normalized(), 0.0032, 0.0024, "M_Steel",
                             5))
    if i == 0:
        core_c = g0 + Z * (h / 2)
    else:
        # small jars: a copper coil on a centre rod inside the glass
        parts.append(pl.rod("jar_rod", g0 + Z * 0.002, g0 + Z * (h - 0.002), 0.0035, 6, "M_Copper"))
        parts.append(pl.helix("jar_coil", r * 0.55, 0.0034, 3.0, h * 0.6, g0 + Z * (h * 0.2), Z, 8, 4,
                              "M_Copper", res=1))
# copper jumper wires between the terminal knobs, then down to the coil
for a, b in zip(knobs[:-1], knobs[1:]):
    m = (a + b) / 2 + Z * 0.012
    parts.append(nw.cable("jumper", [a, m, b], 0.0042, "M_Copper", 6, 3))
COIL_Y0, COIL_Y1 = -0.291, -0.402
w_end = V((0, COIL_Y0 + 0.004, BZ + 0.031))
parts.append(nw.cable("jumper", [knobs[-1], knobs[-1] + V((0, -0.04, 0.006)), w_end + V((0, 0.02, 0.02)), w_end],
                      0.0042, "M_Copper", 6, 3))

# --- side scope (+X) --------------------------------------------------------------------------------------
SC_X, SC_Z = 0.061, RZ1 - 0.008
SY0, SY1 = 0.074, 0.0
parts.append(pl.rod("scope_tube", (SC_X, SY0, SC_Z), (SC_X, SY1, SC_Z), 0.0125, 12, "M_Brass"))
parts.append(pl.lathe_axis("scope_objective", [(0.0, 0.0), (0.0128, 0.0), (0.017, 0.012), (0.0175, 0.022),
                                               (0.014, 0.024), (0.0, 0.021)], (0, -1, 0), (SC_X, SY1 + 0.002, SC_Z),
                           12, "M_Brass", False, False, 40))
parts.append(pl.disc("scope_lens", 0.0128, 0.003, (0, -1, 0), (SC_X, SY1 - 0.0205, SC_Z), "M_Glass", 14, 0.3))
parts.append(pl.lathe_axis("scope_eyecup", [(0.0, 0.0), (0.0135, 0.0), (0.016, 0.01), (0.016, 0.016),
                                            (0.012, 0.017), (0.0, 0.012)], (0, 1, 0), (SC_X, SY0 - 0.002, SC_Z), 14,
                           "M_Rubber", False, False, 40))
for y in (SY0 - 0.026, SY1 + 0.026):
    parts.append(pl.band("scope_ring", 0.0158, 0.01, 0.004, Y, (SC_X, y, SC_Z), "M_Steel", 14, 0.4))
    parts.append(pl.beam_between("scope_mount", (SC_X - 0.008, y, SC_Z - 0.006), (RX - 0.006, y, SC_Z - 0.012),
                                 (0.009, 0.014), "M_Steel", rounded=0.003, segments=1))
parts.append(rw.cylinder("scope_turret", 0.0075, 0.012, 10, (SC_X, (SY0 + SY1) / 2, SC_Z + 0.016), mat="M_Brass"))
parts.append(rw.cylinder("scope_turret2", 0.0075, 0.012, 10, (SC_X + 0.016, (SY0 + SY1) / 2, SC_Z), (0, 90, 0),
                         mat="M_Brass"))

# --- barrel, fore-end, coil, muzzle ------------------------------------------------------------------------
parts.append(pl.rod("barrel", (0, RY0 + 0.01, BZ), (0, -0.432, BZ), BR, 14, "M_Steel"))
FY0, FY1 = RY0 - 0.003, -0.27
parts.append(nw.slab("fore_end", [(FY0, BZ - 0.004), (FY0, 0.096), (FY1, 0.108), (FY1, BZ - 0.004)], 0.044,
                     (0, 0, 0), Y, Z, "M_WoodDark", bevel=0.01, segments=2))
parts.append(rw.rounded_box("fore_cap", (0.049, 0.012, 0.05), 0.005, (0, FY1 + 0.004, 0.124), mat="M_Brass",
                            segments=2))
parts.append(rw.rounded_box("fore_band", (0.05, 0.012, 0.074), 0.005, (0, -0.205, 0.128), mat="M_Brass",
                            segments=2))
for sx in (-1, 1):
    parts.append(nw.stud((sx * 0.025, -0.205, 0.128), (sx, 0, 0), 0.0055, 0.0038, "M_Steel", 6))
    parts.append(nw.stud((sx * 0.022, -0.165, 0.118), (sx, 0, 0), 0.006, 0.004, "M_Brass", 6))
# exposed copper coil between brass flanges
parts.append(pl.rod("coil_core", (0, COIL_Y0, BZ), (0, COIL_Y1, BZ), 0.02, 14, "M_Brass"))
for y in (COIL_Y0, COIL_Y1):
    parts.append(pl.disc("coil_flange", 0.034, 0.008, Y, (0, y, BZ), "M_Brass", 16, 0.4))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = V((math.cos(a), 0, math.sin(a)))
        parts.append(nw.stud(V((0, y, BZ)) + d * 0.026 + V((0, 0.004 if y == COIL_Y0 else -0.004, 0)),
                             V((0, 1 if y == COIL_Y0 else -1, 0)), 0.0042, 0.003, "M_Steel", 5))
parts.append(pl.helix("coil", 0.0255, 0.006, 8.0, COIL_Y0 - COIL_Y1 - 0.014, (0, COIL_Y0 - 0.007, BZ), (0, -1, 0),
                      9, 6, "M_Copper", res=1))
# muzzle collar with three copper tesla prongs around a glowing emitter bead
MC_Y = -0.418
parts.append(pl.lathe_axis("muzzle_collar", [(0.0, 0.0), (0.024, 0.0), (0.029, 0.006), (0.031, 0.016),
                                             (0.028, 0.024), (0.016, 0.028), (0.0, 0.028)], (0, -1, 0),
                           (0, MC_Y + 0.012, BZ), 20, "M_Brass", False, False, 40))
parts.append(pl.lathe_axis("nozzle", [(0.0, 0.0), (0.013, 0.0), (0.012, 0.012), (0.0085, 0.02), (0.0, 0.02)],
                           (0, -1, 0), (0, MC_Y - 0.014, BZ), 14, "M_Steel", False, False, 40))
parts.append(rw.sphere("emitter", 0.0095, 12, 6, (0, MC_Y - 0.036, BZ), mat=EMIT))
TIP_Y = -0.528
for k in range(3):
    a = math.radians(90 + 120 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    c0 = V((0, MC_Y + 0.004, BZ))
    p0 = c0 + d * 0.026
    p1 = c0 + d * 0.036 + V((0, -0.04, 0))
    p2 = c0 + d * 0.028 + V((0, -0.078, 0))
    p3 = V((0, TIP_Y + 0.0085, BZ)) + d * 0.017
    parts.append(pl.sausage("prong", [p0, p1, p2, p3], [0.0078, 0.0072, 0.0064, 0.0058], 7, 3, "M_Copper",
                            (True, True), 2, True, 60))
    parts.append(rw.sphere("prong_ball", 0.0092, 10, 5, tuple(p3), mat="M_Copper"))
    parts.append(pl.band("prong_clamp", 0.0108, 0.01, 0.0045, (p1 - p0).normalized(), p0 + (p1 - p0) * 0.25,
                         "M_Brass", 8, 0.0))

# rubber cables from the receiver front down both sides of the fore-end to the coil flange
for sx in (-1, 1):
    pts = [V((sx * 0.03, RY0 + 0.012, 0.112)), V((sx * 0.033, RY0 - 0.02, 0.104)), V((sx * 0.029, -0.215, 0.098)),
           V((sx * 0.024, -0.268, 0.108)), V((sx * 0.017, COIL_Y0 + 0.006, BZ - 0.02))]
    parts.append(nw.cable("cable", pts, 0.0058, "M_Rubber", 6, 3))
    parts.append(pl.band("cable_plug", 0.009, 0.012, 0.004, (pts[1] - pts[0]).normalized(), pts[0], "M_Brass", 8,
                         0.0))
    parts.append(pl.band("cable_plug", 0.009, 0.01, 0.004, (pts[4] - pts[3]).normalized(), pts[4] - (pts[4] - pts[3])
                         .normalized() * 0.004, "M_Brass", 8, 0.0))

# --- stock -----------------------------------------------------------------------------------------------
SY0_, SY1_ = RY1 - 0.008, 0.155
parts.append(nw.slab("stock", [(SY0_, RZ1 - 0.014), (SY0_, 0.094), (SY1_, 0.068), (SY1_, 0.146)], 0.052,
                     (0, 0, 0), Y, Z, "M_WoodDark", bevel=0.012, segments=3))
BUTT = V((0, SY1_ + 0.004, 0.107))
parts.append(rw.rounded_box("butt_plate", (0.058, 0.012, 0.086), 0.005, tuple(BUTT), mat="M_Brass", segments=2))
for dz in (-0.03, 0.03):
    parts.append(nw.stud(BUTT + V((0, 0.006, dz)), Y, 0.0055, 0.0035, "M_Steel", 6))
parts.append(rw.rounded_box("stock_band", (0.056, 0.014, 0.1), 0.005, (0, RY1 + 0.006, 0.133), mat="M_Brass",
                            segments=2))
# the rarity gem, set into the +X side of the stock (faces the player)
parts += nw.gem(V((0.026, 0.122, 0.118)), X, 0.0085, RARITY, "M_Brass", 8, "rarity_gem")

# --- pistol grip, trigger guard, trigger ---------------------------------------------------------------------
parts.append(glove.oriented_pillow("grip", (0.048, 0.064, 0.2), -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10,
                                   "M_WoodDark"))
parts.append(glove.oriented_pillow("pommel", (0.058, 0.074, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16,
                                   8, "M_Brass"))
guard = [(0, -0.106, RZ0 + 0.006), (0, -0.121, 0.04), (0, -0.104, 0.006), (0, -0.074, -0.006), (0, -0.036, -0.004)]
parts.append(pl.sausage("guard", guard, 0.0085, 8, 3, "M_Brass", (True, True), 2, True, 60))
parts.append(pl.capsule("trigger", (0, -0.08, RZ0 + 0.004), (0, -0.092, 0.05), 0.0072, 8, 2, "M_Steel"))

lance = rw.join(parts, "TeslaLance", origin=(0, 0, 0))
rw.smooth(lance, 45)

# --- ChargeCore: a spiky glowing spark-ball, radius 0.0235 at scale 1 (glass radius 0.031) ---------------
cparts = [rw.ico("core_orb", 0.0145, 2, tuple(core_c), mat=CORE, smooth_angle=0)]
dirs = [V((1, 1, 1)), V((-1, -1, 1)), V((1, -1, -1)), V((-1, 1, -1)), V((0, 0, 1)), V((0, 0, -1)), V((1, 0, 0)),
        V((-1, 0, 0)), V((0, 1, 0)), V((0, -1, 0))]
for d in dirs:
    d = d.normalized()
    cparts.append(pl.crystal("core_spike", core_c + d * 0.009, d, 0.0145, 0.0062, 4, 0.55, 0.0, CORE))
core = rw.join(cparts, "ChargeCore", origin=tuple(core_c))
rw.smooth(core, 30)
pl.parent_keep(core, lance)

# --- glove + empties ------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
rw.empty("Muzzle", (0, TIP_Y, BZ))
pl.check("vm_tesla_lance", (0, 0, 0))
rw.finish("vm_tesla_lance", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_tesla_lance")
