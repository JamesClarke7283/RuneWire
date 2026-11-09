"""vm_flamer: first-person "Bellows Flamethrower".

Nodes (origin = grip centre; the nozzle points -Y):
  Flamer  a riveted brass valve block (steel top plate, copper air line with a hand-wheel valve and an air dial on
          the +X side, a maker's plate on -X) between a leather accordion bellows at the back (brass end plate with
          the caged rarity lamp, steel guide rods) and a copper fuel pipe running forward inside a perforated steel
          heat shield (brass end rings) to a flared steel nozzle with a dark mouth; a riveted brass fuel tank hangs
          vertically in front of the trigger guard (domed ends, a yellow/black hazard band, a fuel gauge facing
          the player, a filler cap, a brass coupling and valve up into the pipe); a copper pilot line runs under
          the shield to a little brass burner whose glowing orange pilot flame licks up just under the nozzle tip;
          a dark-wood pistol grip, brass trigger guard and trigger.
  Glove   the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle  empty at the centre of the nozzle exit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_weapon_helpers as th  # noqa: E402

nw, dh, glove, pl, rw, V = th.nw, th.dh, th.glove, th.pl, th.rw, th.V
X, Y, Z = th.X, th.Y, th.Z
rw.reset()

A, o, fr = th.grip_frame(18.0)
RARITY = th.std_mats()
FLAME = rw.glow("PilotFlame", "ff7a22", 1.4)
FLAME_CORE = rw.glow("PilotCore", "ffc43a", 1.8)
BRASS, COPPER, STEEL, DARK = "M_Brass", "M_Copper", "M_Steel", "M_DarkMetal"
parts = th.Parts()
add = parts.add

NZ = 0.145                        # nozzle axis height
RB0, RB1 = -0.105, 0.035          # valve block front / back
RX = 0.035                        # valve block half width
RZ0, RZ1 = 0.0875, 0.1725         # valve block bottom / top
NOZ_Y = -0.479                    # nozzle exit

# --- valve block (receiver) --------------------------------------------------------------------------------------
add(rw.rounded_box("valve_block", (2 * RX, RB1 - RB0, RZ1 - RZ0), 0.014, (0, (RB0 + RB1) / 2, (RZ0 + RZ1) / 2),
                   mat=BRASS, segments=2))
add(rw.rounded_box("top_plate", (0.05, 0.11, 0.008), 0.003, (0, -0.035, RZ1 + 0.002), mat=STEEL, segments=1))
for sx in (-1, 1):
    for y in (-0.08, 0.01):
        add(nw.stud((sx * 0.02, y, RZ1 + 0.006), Z, 0.0045, 0.0032, BRASS, 6))
    add(nw.rivet_line((sx * RX, -0.092, RZ0 + 0.0085), (sx * RX, 0.022, RZ0 + 0.0085), 4, (sx, 0, 0), 0.0045,
                      0.0032, STEEL, 6))
# +X side: copper air line from the bellows to the nozzle collar, a hand-wheel valve and a little air dial
air = [V((0.03, RB1 - 0.004, 0.158)), V((0.046, 0.0, 0.162)), V((0.047, -0.07, 0.16)), V((0.022, RB0 - 0.007, NZ + 0.007))]
add(pl.sausage("air_line", air, 0.0062, 8, 3, COPPER, (True, True), 2, True, 60))
add(dh.valve("air_valve", V((0.0475, -0.036, 0.161)), X, 0.0125, 0.0036, 3, BRASS, COPPER, 0.01, STEEL, up=(0, 0, 1)))
add(nw.gauge(V((RX, -0.02, 0.122)), V((1, 0.2, 0.15)).normalized(), Z, 0.017, BRASS,
             zones=(("DialTeal", -120, 0), ("DialRed", 60, 120)), needle_deg=-30.0, ticks=5, depth=0.009, segs=14,
             name="air_dial"))
# -X side: maker's plate with a flame badge
add(dh.plate("maker", (-RX, -0.035, 0.132), -X, 0.05, 0.034, 0.004, mat=COPPER, rivets=BRASS, rr=0.0034))
badge = [(0.0, -0.013), (0.009, -0.006), (0.01, 0.003), (0.004, 0.013), (0.003, 0.004), (-0.002, 0.008),
         (-0.01, 0.0), (-0.008, -0.009)]
add(dh.prism("maker_flame", badge, V((-RX - 0.004, -0.035, 0.132)), -Y, Z, -X, 0.003, "DialYellow", 0.0, 0.0005, 30))

# --- bellows at the back ------------------------------------------------------------------------------------------
BZ_ = 0.132
BY0, BY1 = RB1 - 0.002, 0.124
add(pl.band("bellows_ring", 0.049, 0.012, 0.016, Y, (0, BY0 + 0.004, BZ_), BRASS, 24, 0.3))
add(th.bellows("bellows", (0, BY0 + 0.008, BZ_), (0, BY1, BZ_), 0.034, 0.047, 5, "M_Leather", 22))
EP = BY1 + 0.006
add(pl.disc("end_plate", 0.052, 0.012, Y, (0, EP, BZ_), BRASS, 24, 0.35))
add(pl.disc("end_hub", 0.018, 0.008, Y, (0, EP + 0.008, BZ_), STEEL, 14, 0.4))
add(pl.bolt((0, EP + 0.012, BZ_), Y, 0.008, 0.006, BRASS, "end_bolt", washer=False))
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    if k in (0, 4):
        continue
    add(nw.stud(V((0, EP + 0.006, BZ_)) + V((math.cos(a), 0, math.sin(a))) * 0.042, Y, 0.0045, 0.0032, STEEL, 6))
la = math.radians(18.0)
add(dh.lamp("rarity", V((0, EP + 0.006, BZ_)) + V((math.cos(la), 0, math.sin(la))) * 0.034,
            V((0.3, 1, 0.25)).normalized(), 0.0095, RARITY, up=(0, 0, 1), bezel=STEEL, cage=2, cage_mat=BRASS,
            segs=12))
# guide rods on both sides, with lugs on the block and the end plate
for sx in (-1, 1):
    add(pl.rod("guide_rod", (sx * 0.055, RB1 - 0.012, BZ_), (sx * 0.055, EP + 0.004, BZ_), 0.0045, 8, STEEL))
    add(rw.rounded_box("rod_lug", (0.026, 0.014, 0.016), 0.004, (sx * 0.046, RB1 - 0.012, BZ_), mat=BRASS,
                       segments=1))
    add(rw.rounded_box("rod_lug", (0.014, 0.014, 0.016), 0.004, (sx * 0.053, EP, BZ_), mat=BRASS, segments=1))
    add(pl.bolt((sx * 0.055, EP + 0.008, BZ_), Y, 0.005, 0.004, STEEL, "rod_nut", washer=False))

# --- copper pipe, perforated heat shield, flared nozzle --------------------------------------------------------------
add(pl.band("nozzle_collar", 0.027, 0.018, 0.012, Y, (0, RB0 - 0.006, NZ), BRASS, 20, 0.4))
add(pl.rod("fuel_pipe", (0, RB0, NZ), (0, -0.41, NZ), 0.0172, 16, COPPER))
SH0, SH1 = -0.128, -0.362
shield = th.arc_shell("heat_shield", (0, SH0, NZ), (0, SH1, NZ), 0.031, 0.0035, -128.0, 128.0, Z, 32, STEEL)
th.perforate(shield, (0, SH0, NZ), (0, SH1, NZ), 0.031, 4, 5, 0.0068, -108.0, 108.0, Z, 0.03, True, 0.02, 8)
add(shield)
for y in (SH0, SH1):
    add(pl.band("shield_ring", 0.0345, 0.011, 0.0175, Y, (0, y, NZ), BRASS, 20, 0.0))
    add(th.ring_studs((0, y, NZ), Y, 0.0345, 4, 0.0042, 0.003, STEEL, -105.0, 105.0))
flare = [(0.0172, 0.0), (0.019, 0.01), (0.0225, 0.032), (0.0295, 0.055), (0.037, 0.069), (0.0395, 0.075),
         (0.036, 0.079), (0.028, 0.072), (0.019, 0.055), (0.013, 0.036), (0.0, 0.036)]
NF0 = NOZ_Y + 0.079
flare_o = pl.lathe_axis("nozzle", flare, -Y, (0, NF0, NZ), 24, STEEL, False, False, 40)
nw.mat_where(flare_o, DARK, nw.inner_faces((0, 0, NZ), Y, -0.2))
nw.mat_where(flare_o, DARK, lambda p, n: p.y < NF0 - 0.03 and n.y < -0.5 and (p - V((0, p.y, NZ))).length < 0.0135)
add(flare_o)
add(pl.band("flare_band", 0.022, 0.01, 0.006, Y, (0, NF0 - 0.006, NZ), BRASS, 20, 0.3))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    add(nw.stud(V((0, NOZ_Y + 0.016, NZ)) + d * 0.0335, (d + V((0, -0.55, 0))).normalized(), 0.0042, 0.003, BRASS, 6))

# --- fuel tank hanging in front of the trigger guard ------------------------------------------------------------------
TC = V((0, -0.177, -0.046))                # tank bottom pole
TR = 0.045
tank = [(0.0, 0.0), (0.019, 0.003), (0.033, 0.012), (0.041, 0.024), (TR, 0.04), (TR, 0.118), (0.041, 0.134),
        (0.033, 0.146), (0.019, 0.155), (0.0, 0.158)]
add(pl.lathe_axis("fuel_tank", tank, Z, TC, 22, BRASS, False, False, 40))
add(th.hazard_ring("tank_hazard", TR + 0.0015, 0.03, Z, TC + Z * 0.063, stripes=9, slant=30, half_w=9.0, segs=22))
add(th.ring_studs(TC + Z * 0.042, Z, TR, 8, 0.0045, 0.0032, STEEL, 0.0, 360.0, up=(1, 0, 0)))
add(th.ring_studs(TC + Z * 0.113, Z, TR, 5, 0.0045, 0.0032, STEEL, 85.0, 315.0, up=(1, 0, 0)))
# fuel gauge on the tank, looking back at the player's side
gd = V((0.82, 0.5, 0.0)).normalized()
gc = TC + Z * 0.1 + gd * (TR - 0.002)
add(pl.rod("gauge_stem", gc - gd * 0.004, gc + gd * 0.006, 0.0085, 10, BRASS))
add(nw.gauge(gc + gd * 0.006, (gd + Z * 0.2).normalized(), Z, 0.019, BRASS,
             zones=(("DialRed", -120, -70), ("DialYellow", -70, -15), ("DialTeal", -15, 120)), needle_deg=52.0,
             ticks=5, depth=0.011, segs=16, glass=True, name="fuel_gauge"))
# filler cap on the upper -X shoulder
fd = V((-0.75, -0.25, 0.62)).normalized()
fc = TC + Z * 0.136 + V((fd.x, fd.y, 0)).normalized() * 0.036
add(pl.lathe_axis("filler", [(0.0, 0.0), (0.011, 0.0), (0.012, 0.006), (0.0105, 0.01), (0.006, 0.013),
                             (0.0, 0.014)], fd, fc, 12, BRASS, False, False, 45))
add(pl.capsule("filler_tab", fc + fd * 0.013 + V((0, 0.008, 0)), fc + fd * 0.013 - V((0, 0.008, 0)), 0.0032, 6, 1,
               BRASS))
# coupling + valve up into the fuel pipe, and the hanging strap to the valve block
TT = TC + Z * 0.158
add(pl.rod("coupling", TT - Z * 0.006, V((0, TC.y, NZ - 0.012)), 0.0095, 12, BRASS))
add(pl.band("coupling_nut", 0.0125, 0.008, 0.005, Z, TT + Z * 0.004, STEEL, 6, 0.0))
add(dh.valve("tank_valve", TT + Z * 0.006 + X * 0.009, X, 0.0098, 0.0032, 3, COPPER, BRASS, 0.006, STEEL))
add(pl.band("tank_strap", TR + 0.004, 0.014, 0.007, Z, TC + Z * 0.127, BRASS, 22, 0.3))
add(pl.beam_between("tank_arm", TC + V((0, TR - 0.002, 0.127)), V((0, RB0 + 0.008, RZ0 + 0.008)), (0.022, 0.012),
                    BRASS, rounded=0.004, segments=1, up=(0, 0, 1)))

# --- pilot line, burner and the glowing pilot flame under the nozzle tip --------------------------------------------
BUR = V((0, NOZ_Y - 0.002, NZ - 0.05))
pil = [V((0.012, TC.y + 0.01, NZ - 0.014)), V((0.016, -0.25, NZ - 0.03)), V((0.012, -0.38, NZ - 0.037)),
       V((0.004, BUR.y + 0.03, BUR.z - 0.002)), V((0, BUR.y + 0.006, BUR.z - 0.004))]
add(pl.sausage("pilot_line", pil, 0.0042, 6, 3, COPPER, (True, True), 2, True, 60))
for y in (-0.25, -0.33):
    add(pl.obox("pilot_clip", (0.008, 0.006, 0.017), V((0.0145, y, NZ - 0.022)), X, Z, BRASS, rounded=0.002,
                segments=1))
FD = V((0, -0.55, 1)).normalized()
add(pl.lathe_axis("burner", [(0.0, -0.006), (0.0055, -0.006), (0.0085, 0.0), (0.0095, 0.006), (0.0075, 0.008),
                             (0.006, 0.004), (0.0, 0.004)], FD, BUR, 10, BRASS, False, False, 45))
add(th.flame("pilot_flame", BUR + FD * 0.004, FD, 0.046, 0.0125, FLAME, 10, lean=V((0, -0.008, 0.003))))
add(th.flame("pilot_core", BUR + FD * 0.005, FD, 0.026, 0.0072, FLAME_CORE, 8, lean=V((0, -0.005, 0.002))))

# --- pistol grip, guard, trigger -------------------------------------------------------------------------------------
add(th.pistol_grip(A, o, fr))
add(th.trigger_group(-0.1, RZ0))

flamer = rw.join(parts, "Flamer", origin=(0, 0, 0))
rw.smooth(flamer, 45)

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
pl.empty_at("Muzzle", (0, NOZ_Y, NZ), flamer)
pl.check("vm_flamer", (0, 0, 0))
rw.finish("vm_flamer", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_flamer")
