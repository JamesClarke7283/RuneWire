"""vm_gatling: first-person "Steamroller Gatling", a chunky hand-held six-barrel steam rotary gun.

Nodes (origin = grip centre; the barrels point -Y):
  Gatling  a hazard-orange round motor drum with brass flanges, studs and a yellow/black hazard band, a domed
           steel rear cap carrying the caged rarity lamp, and a steel nose the barrel cluster spins in; a copper
           boiler on brass-strapped saddles on top (backhead pressure gauge facing the player, a water sight
           glass and a hand-wheel valve on the +X side, a safety valve and a whistle on top, a feed pipe down to
           the nose); a little steam engine on the +X side (brass cylinder, crosshead, connecting rod and a
           spoked flywheel); a steel ammo box hanging on the -X side (orange lid, brass straps, hazard panel)
           whose leather belt of brass rounds arcs up into a feed port; a copper exhaust stack and a maker's
           plate on -X; a wooden vertical front grip on a clamp band under the nose; a dark-wood pistol grip,
           brass trigger guard and trigger.
  Barrels  six evenly spaced steel barrels (60 degrees apart) with three brass clamp rings (the front one on a
           dark clamp disc), muzzle collars with dark bores, a centre spindle and a rear hub (child of Gatling).
           Origin ON the spin axis at the rear hub, (0, BARREL_Y0, BZ); the axis runs along Blender Y. Everything
           on it stays within BARREL_RMAX of the axis and the body keeps clear of that radius in front of the nose.
  Glove    the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle   empty at the centre of the barrel tips (child of Gatling).
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
rw.flat("SightWater", "4fd6e8", 0.3, 0.0)
ORANGE = "M_PaintedMetal__f26b1d"
BRASS, COPPER, STEEL, DARK = "M_Brass", "M_Copper", "M_Steel", "M_DarkMetal"
parts = th.Parts()
add = parts.add

# --- motor drum ------------------------------------------------------------------------------------------------
BZ = 0.148                       # spin axis height
HR = 0.06                        # drum radius
YB0, YB1 = 0.08, -0.107          # drum back / front seam


def drum_pt(y, ang, r=HR):
    """Point on a circle round the spin axis at y; ang 0 = +X, 90 = +Z. Returns (point, radial direction)."""
    a = math.radians(ang)
    d = V((math.cos(a), 0, math.sin(a)))
    return V((0, y, BZ)) + d * r, d


add(pl.rod("drum", (0, YB0 + 0.004, BZ), (0, YB1 - 0.002, BZ), HR, 24, ORANGE))
rear = [(HR - 0.002, -0.004), (HR, 0.0), (0.057, 0.012), (0.049, 0.024), (0.036, 0.033), (0.0, 0.038)]
add(pl.lathe_axis("rear_dome", rear, Y, (0, YB0, BZ), 24, STEEL, False, False, 40))
nose = [(0.058, -0.004), (0.058, 0.0), (0.054, 0.04), (0.052, 0.058), (0.0505, 0.063), (0.047, 0.063),
        (0.046, 0.05), (0.0, 0.05)]
nose_o = pl.lathe_axis("nose", nose, -Y, (0, YB1 + 0.002, BZ), 24, STEEL, False, False, 40)
nw.mat_where(nose_o, DARK, lambda p, n: p.y < YB1 - 0.045 and (p - V((0, p.y, BZ))).length < 0.0468)
add(nose_o)
for y in (YB0 + 0.002, YB1):
    add(pl.band("flange", HR + 0.0075, 0.016, 0.012, Y, (0, y, BZ), BRASS, 24, 0.0))
    add(th.ring_studs((0, y, BZ), Y, HR + 0.0075, 7, 0.0048, 0.0035, STEEL, -150.0, 150.0, up=(0, 0, 1)))
add(th.hazard_ring("hazard", HR + 0.0015, 0.026, Y, (0, -0.083, BZ), stripes=9, slant=28, half_w=8.0, segs=24))
# rear cap: hex bolt, a ring of studs and the caged rarity lamp looking back at the player
add(pl.disc("rear_hub", 0.021, 0.01, Y, (0, YB0 + 0.035, BZ), BRASS, 16, 0.4))
add(pl.bolt((0, YB0 + 0.039, BZ), Y, 0.0095, 0.007, STEEL, "rear_bolt", washer=False))
for k in range(2, 7):
    p, d = drum_pt(YB0 + 0.012, 60 * k + 30, 0.057)
    add(nw.stud(p, (d + Y * 0.5).normalized(), 0.0048, 0.0035, BRASS, 6))
lp, ld = drum_pt(YB0 + 0.02, 30, 0.0515)
add(dh.lamp("rarity", lp, (ld + Y * 0.9).normalized(), 0.0105, RARITY, up=(0, 0, 1), bezel=BRASS, cage=2,
            cage_mat=STEEL, segs=12))

# grip mount under the drum, pistol grip, guard, trigger
add(rw.rounded_box("grip_mount", (0.046, 0.074, 0.026), 0.008, (0, -0.032, 0.09), mat=STEEL, segments=1))
for sx in (-1, 1):
    add(nw.stud((sx * 0.023, -0.032, 0.09), (sx, 0, 0), 0.0045, 0.0032, BRASS, 6))
add(th.pistol_grip(A, o, fr, medallion=None))
add(th.trigger_group(-0.1, 0.09))

# --- boiler on top ----------------------------------------------------------------------------------------------
RB = 0.037
ZB = BZ + HR + RB - 0.003
BY_BACK = 0.074
boiler = [(0.0, 0.0), (0.027, 0.002), (0.035, 0.007), (RB, 0.013), (RB, 0.15), (0.034, 0.159), (0.027, 0.167),
          (0.015, 0.172), (0.0, 0.174)]
boiler_o = pl.lathe_axis("boiler", boiler, -Y, (0, BY_BACK, ZB), 20, COPPER, False, False, 40)
nw.mat_where(boiler_o, BRASS, lambda p, n: p.y > BY_BACK - 0.011)
add(boiler_o)
for y in (0.034, -0.058):
    add(pl.band("boiler_strap", RB + 0.0035, 0.012, 0.006, Y, (0, y, ZB), BRASS, 18, 0.0))
    add(rw.rounded_box("saddle", (0.072, 0.018, 0.036), 0.006, (0, y, BZ + HR - 0.005), mat=STEEL, segments=1))
for y in (BY_BACK - 0.021, -0.083):
    add(th.ring_studs((0, y, ZB), Y, RB, 5, 0.0042, 0.003, BRASS, -100.0, 100.0))
# backhead: big pressure gauge facing the player
add(nw.gauge(V((0.0, BY_BACK + 0.0005, ZB + 0.002)), V((0.12, 1.0, 0.15)).normalized(), Z, 0.0225, BRASS,
             zones=(("DialTeal", -120, -30), ("DialYellow", -30, 50), ("DialRed", 50, 120)), needle_deg=58.0,
             ticks=5, depth=0.011, segs=14, glass=True, name="boiler_gauge"))
# water sight glass on the +X side of the backhead end
SG_X, SG_Y = 0.044, 0.052
add(pl.rod("sight_glass", (SG_X, SG_Y, ZB - 0.017), (SG_X, SG_Y, ZB + 0.017), 0.0068, 8, "M_Glass"))
add(pl.rod("sight_water", (SG_X, SG_Y, ZB - 0.015), (SG_X, SG_Y, ZB + 0.002), 0.0048, 6, "SightWater"))
for zz in (ZB - 0.0195, ZB + 0.0195):
    add(pl.rod("sight_cap", (SG_X, SG_Y, zz - 0.0045), (SG_X, SG_Y, zz + 0.0045), 0.009, 8, BRASS))
    add(pl.rod("sight_arm", (0.026, SG_Y, zz), (SG_X, SG_Y, zz), 0.0045, 6, BRASS))
# hand-wheel valve on the upper +X side
vd = V((0.76, 0.0, 0.65))
add(dh.valve("valve", V((0, -0.012, ZB)) + vd * RB, vd, 0.013, 0.0038, 3, BRASS, COPPER, 0.011, STEEL,
             up=(0, 1, 0)))
# safety valve (front) and steam whistle (back) on top
add(pl.lathe_axis("safety_valve", [(0.0075, -0.004), (0.0075, 0.008), (0.012, 0.0095), (0.0125, 0.0135),
                                   (0.008, 0.017), (0.0, 0.018)], Z, (0, -0.074, ZB + RB - 0.001), 10, BRASS, False,
                  False, 45))
add(pl.lathe_axis("whistle", [(0.0045, -0.004), (0.0045, 0.008), (0.0078, 0.009), (0.0078, 0.027), (0.0058, 0.03),
                              (0.0, 0.031)], Z, (0, 0.051, ZB + RB - 0.001), 10, BRASS, False, False, 45))
add(pl.capsule("whistle_lever", (0.0, 0.051, ZB + RB + 0.02), (0.017, 0.06, ZB + RB + 0.017), 0.0036, 6, 1, STEEL))
# feed pipe from the front of the boiler down into the nose, with brass flanges
pp = [V((0, -0.088, ZB - 0.012)), V((0, -0.108, ZB - 0.008)), V((0, -0.122, BZ + 0.072)), V((0, -0.125, BZ + 0.05))]
add(pl.sausage("feed_pipe", pp, 0.0068, 8, 3, COPPER, (True, True), 2, True, 60))
add(pl.band("pipe_flange", 0.0105, 0.006, 0.005, (pp[1] - pp[0]).normalized(), pp[0], BRASS, 8, 0.0))
add(pl.band("pipe_flange", 0.0105, 0.006, 0.005, Z, pp[3] + V((0, 0, 0.004)), BRASS, 8, 0.0))

# --- +X side: a little steam engine turning a flywheel -------------------------------------------------------------
CY0, CY1, CZ, CX = 0.012, 0.062, BZ + 0.02, 0.072        # steam cylinder (axis Y)
cyl = [(0.0, 0.0), (0.0178, 0.0), (0.0178, 0.007), (0.0148, 0.009), (0.0148, CY1 - CY0 - 0.009),
       (0.0178, CY1 - CY0 - 0.007), (0.0178, CY1 - CY0), (0.0, CY1 - CY0)]
add(pl.lathe_axis("steam_cyl", cyl, Y, (CX, CY0, CZ), 14, BRASS, False, False, 40))
add(rw.rounded_box("valve_chest", (0.02, 0.028, 0.014), 0.004, (CX, (CY0 + CY1) / 2, CZ + 0.019), mat=COPPER,
                   segments=1))
add(rw.rounded_box("cyl_foot", (0.016, 0.04, 0.012), 0.004, (CX - 0.011, (CY0 + CY1) / 2, CZ - 0.01), mat=STEEL,
                   segments=1))
for y in (CY0 + 0.0035, CY1 - 0.0035):
    add(nw.stud((CX + 0.0178, y, CZ), X, 0.0034, 0.0026, STEEL, 6))
sp = [V((0.027, 0.018, ZB - 0.02)), V((0.05, 0.022, ZB - 0.03)), V((CX, 0.03, CZ + 0.04)), V((CX, 0.037, CZ + 0.026))]
add(pl.sausage("steam_pipe", sp, 0.0058, 6, 3, COPPER, (True, True), 2, True, 60))
add(pl.band("pipe_flange", 0.0092, 0.005, 0.0045, Z, (CX, 0.037, CZ + 0.027), BRASS, 8, 0.0))
FW = V((0.074, -0.03, BZ - 0.012))
FR = 0.031
add(rw.cylinder("fly_boss", 0.012, 0.022, 10, (0.061, FW.y, FW.z), (0, 90, 0), mat=BRASS))
add(th.flywheel("flywheel", FW, X, FR, 0.009, 0.007, 5, STEEL, BRASS, spin=18.0, segs=20))
pin = FW + V((0.009, 0.0185 * math.cos(math.radians(55)), 0.0185 * math.sin(math.radians(55))))
add(pl.capsule("crank_pin", pin - X * 0.006, pin + X * 0.002, 0.0048, 6, 1, BRASS))
XH = V((CX + 0.004, CY0 - 0.012, CZ))
add(pl.rod("piston_rod", V((CX, CY0 + 0.002, CZ)), XH, 0.005, 6, STEEL))
add(rw.rounded_box("crosshead", (0.014, 0.014, 0.014), 0.003, tuple(XH), mat=BRASS, segments=1))
add(pl.beam_between("con_rod", XH + X * 0.008, pin + X * 0.001, (0.007, 0.011), STEEL, rounded=0.0025, segments=1,
                    up=(1, 0, 0)))

# --- -X side: feed port, maker's plate, exhaust stack, stud row ----------------------------------------------------
FPC = V((-0.064, -0.076, BZ + 0.019))
add(rw.rounded_box("feed_port", (0.03, 0.046, 0.032), 0.006, tuple(FPC), mat=STEEL, segments=1))
add(rw.rounded_box("feed_lip", (0.006, 0.054, 0.04), 0.0025, tuple(FPC + V((-0.016, 0, 0))), mat=BRASS, segments=1))
add(pl.obox("feed_mouth", (0.004, 0.04, 0.02), FPC + V((-0.0185, 0, 0.0)), Y, X, DARK))
add(dh.plate("maker", (-0.0585, 0.032, BZ + 0.004), -X, 0.044, 0.03, 0.004, mat=BRASS, rivets=None))
for y in (0.016, 0.048):
    add(nw.stud((-0.0625, y, BZ + 0.004), -X, 0.0034, 0.0025, STEEL, 6))
add(dh.gear("maker_gear", (-0.0625, 0.032, BZ + 0.004), -X, 0.0095, 8, 0.0028, 0.003, COPPER, hub=False))
add(nw.stud((-0.0645, 0.032, BZ + 0.004), -X, 0.0034, 0.0025, BRASS, 6))
for k in range(4):
    p, d = drum_pt(0.06 - k * 0.03, 212)
    add(nw.stud(p, d, 0.0045, 0.0033, BRASS, 6))
ex = [V((-0.052, 0.052, BZ + 0.03)), V((-0.074, 0.058, BZ + 0.05)), V((-0.08, 0.068, BZ + 0.09)),
      V((-0.075, 0.078, BZ + 0.118))]
add(pl.sausage("exhaust", ex, 0.0085, 8, 3, COPPER, (True, False), 2, True, 60))
add(pl.lathe_axis("exhaust_bell", [(0.0075, 0.0), (0.0105, 0.004), (0.0135, 0.014), (0.0148, 0.019), (0.0128, 0.02),
                                   (0.009, 0.012)], (ex[3] - ex[2]).normalized(), ex[3], 10, BRASS, False, False, 45))
add(pl.band("exhaust_flange", 0.013, 0.007, 0.006, (ex[1] - ex[0]).normalized(), ex[0], BRASS, 10, 0.0))

# --- ammo box hanging on the -X side, belt arcing up into the feed port --------------------------------------------
BOX = V((-0.113, -0.172, 0.03))
BW, BL, BH = 0.064, 0.108, 0.08
add(rw.rounded_box("ammo_box", (BW, BL, BH), 0.008, tuple(BOX), mat=STEEL, segments=1))
add(rw.rounded_box("ammo_lid", (BW + 0.005, BL + 0.005, 0.016), 0.006, tuple(BOX + V((0, 0, BH / 2 + 0.002))),
                   mat=ORANGE, segments=1))
add(pl.obox("lid_slot", (0.044, 0.026, 0.005), BOX + V((0, BL / 2 - 0.02, BH / 2 + 0.009)), X, Z, "DialInk"))
for y in (BOX.y - BL / 2 + 0.013, BOX.y + BL / 2 - 0.045):
    add(rw.rounded_box("box_strap", (BW + 0.006, 0.012, BH + 0.004), 0.004, (BOX.x, y, BOX.z - 0.004), mat=BRASS,
                       segments=1))
    add(nw.stud((BOX.x - BW / 2 - 0.003, y, BOX.z - 0.004), -X, 0.0042, 0.003, STEEL, 6))
add(th.hazard_panel("box_hazard", BOX + V((-BW / 2, -0.016, -0.004)), -X, Z, 0.044, 0.05, 0.003, 0.0075, 40.0))
add(rw.rounded_box("box_latch", (0.016, 0.008, 0.016), 0.003, tuple(BOX + V((0, -BL / 2 - 0.003, BH / 2 - 0.006))),
                   mat=BRASS, segments=1))
add(pl.beam_between("box_bracket", (-0.086, -0.158, BOX.z + BH / 2 - 0.004), (-0.036, -0.151, 0.1), (0.022, 0.011),
                    STEEL, rounded=0.003, segments=1, up=(0, 1, 0)))
belt = [V((-0.112, -0.134, BOX.z + BH / 2 - 0.004)), V((-0.122, -0.124, 0.1)), V((-0.123, -0.11, 0.138)),
        V((-0.111, -0.096, 0.172)), V((-0.093, -0.085, 0.188)), V((-0.078, -0.079, 0.181)),
        V((-0.07, -0.077, 0.17))]
add(th.ammo_belt(belt, 0.0158, (0, -1, 0), 0.038, 0.0072, BRASS, COPPER, "M_Leather__5a3420", 6, 0.006, 10))

# --- front grip on a clamp band under the nose -------------------------------------------------------------------
FG_Y = -0.151
add(pl.band("grip_clamp", 0.0615, 0.02, 0.0095, Y, (0, FG_Y, BZ), BRASS, 20, 0.0))
add(rw.rounded_box("grip_lug", (0.028, 0.026, 0.024), 0.006, (0, FG_Y, 0.084), mat=STEEL, segments=1))
add(nw.stud((0.014, FG_Y, 0.084), X, 0.0042, 0.003, BRASS, 6))
FGD = V((0, -0.2, -1)).normalized()
FGT = V((0, FG_Y, 0.074))
wood = [(0.0175, 0.0), (0.02, 0.012), (0.0215, 0.026), (0.0185, 0.037), (0.0215, 0.05), (0.0185, 0.062),
        (0.0215, 0.075), (0.0185, 0.087), (0.021, 0.1), (0.0205, 0.118), (0.0, 0.12)]
add(pl.lathe_axis("front_grip", wood, FGD, FGT, 12, "M_WoodDark", False, False, 50))
add(pl.band("fg_ferrule", 0.0205, 0.012, 0.007, FGD, FGT + FGD * 0.006, BRASS, 12, 0.0))
add(pl.lathe_axis("fg_cap", [(0.0, 0.0), (0.0225, 0.0), (0.0235, 0.007), (0.019, 0.015), (0.0, 0.017)], FGD,
                  FGT + FGD * 0.115, 12, BRASS, False, False, 45))

gun = rw.join(parts, "Gatling", origin=(0, 0, 0))
rw.smooth(gun, 45)

# --- the barrel cluster: a separate object spinning about its local Y axis -----------------------------------------
BARREL_Y0 = -0.155              # rear hub face, on the axis: the Barrels origin
TIP_Y = -0.575                  # barrel tips
BRC, BRR = 0.032, 0.0125        # barrel circle radius, barrel radius
BARREL_RMAX = 0.0555            # nothing on Barrels reaches further from the axis than this
bp = th.Parts()
bp.add(pl.disc("hub", 0.0435, 0.012, Y, (0, BARREL_Y0 - 0.006, BZ), DARK, 16, 0.3))
bp.add(pl.rod("spindle", (0, BARREL_Y0 - 0.01, BZ), (0, -0.5, BZ), 0.012, 6, STEEL))
for i in range(6):
    a = math.radians(30 + 60 * i)
    off = V((math.cos(a) * BRC, 0, math.sin(a) * BRC))
    bp.add(pl.rod("barrel", V((0, BARREL_Y0 - 0.008, BZ)) + off, V((0, TIP_Y + 0.016, BZ)) + off, BRR, 8, STEEL))
    mz_c = V((0, TIP_Y + 0.019, BZ)) + off
    mz = pl.lathe_axis("muzzle", [(0.0146, 0.0), (0.0154, 0.004), (0.0154, 0.015), (0.0142, 0.019),
                                  (0.0072, 0.019), (0.0068, 0.013), (0.0, 0.013)], -Y, mz_c, 8, STEEL, False, False,
                       45)
    th.mark_bore(mz, mz_c, -Y, 0.0074, DARK, 0.012)
    bp.add(mz)
for y in (-0.215, -0.36):
    bp.add(pl.band("clamp_ring", 0.051, 0.016, 0.0125, Y, (0, y, BZ), BRASS, 20, 0.0))
    bp.add(th.ring_studs((0, y, BZ), Y, 0.051, 4, 0.0042, 0.0032, STEEL, 0.0, 360.0))
FCY = -0.495
clamp = [(0.0, -0.008), (0.046, -0.008), (0.046, -0.0065), (0.051, -0.0065), (0.051, 0.0065), (0.046, 0.0065),
         (0.046, 0.008), (0.0, 0.008)]
clamp_o = pl.lathe_axis("front_clamp", clamp, -Y, (0, FCY, BZ), 20, DARK, False, False, 40)
nw.mat_where(clamp_o, BRASS, lambda p, n: (p - V((0, p.y, BZ))).length > 0.0462)
bp.add(clamp_o)
bp.add(th.ring_studs((0, FCY, BZ), Y, 0.051, 4, 0.0042, 0.0032, STEEL, 0.0, 360.0))
bp.add(pl.lathe_axis("spindle_cap", [(0.0, 0.0), (0.016, 0.0), (0.0165, 0.004), (0.012, 0.011), (0.0, 0.013)], -Y,
                     (0, FCY - 0.008, BZ), 10, BRASS, False, False, 45))
barrels = rw.join(bp, "Barrels", origin=(0, BARREL_Y0, BZ))
rw.smooth(barrels, 45)
pl.parent_keep(barrels, gun)

# --- glove + empties ---------------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
pl.empty_at("Muzzle", (0, TIP_Y, BZ), gun)


def _radial_max(obj):
    mw = obj.matrix_world
    return max(math.hypot((mw @ v.co).x, (mw @ v.co).z - BZ) for v in obj.data.vertices)


print("RWREPORT   CHECK Barrels max radius from spin axis %.4f (limit %.4f)" % (_radial_max(barrels), BARREL_RMAX))
pl.check("vm_gatling", (0, 0, 0))
rw.finish("vm_gatling", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_gatling")
