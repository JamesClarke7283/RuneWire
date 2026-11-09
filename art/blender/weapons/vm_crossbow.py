"""vm_crossbow: first-person "Clockwork Crossbow", a compact repeating crossbow.

Nodes (origin = grip centre; the bolt points -Y):
  Crossbow  a shaped dark-wood tiller with brass bands, a brass butt plate and brass groove rails; a steel prod
            lock at the front (two cheeks) holding chunky steel leaf-spring limbs (span ~0.5 m across X) with
            brass root collars and brass tip knobs, a taut cream string drawn back to a brass latch claw, and a
            steel stirrup; a top-mounted wooden magazine box (brass straps and lid, more bolts poking out: red
            fletched tails at the back, brass heads at the front) with the caged rarity lamp on its +X side; a
            brass string-winding gear on top behind the magazine (pillow blocks, steel pawl), a crank with a
            wooden knob on the +X side, a filigree brass side plate on +X, a clockwork mainspring barrel, a ratchet
            and a maker's plate on -X; a dark-wood pistol grip, brass trigger guard and trigger.
  Bolt      the loaded bolt lying in the groove between the rails (child of Crossbow, origin at its centre): steel
            shaft, brass bodkin head with a collar, brass nock, three red vanes. The game hides it right after
            firing and shows it again after reloading; the weapon reads complete without it.
  Glove     the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle    empty at the bolt tip (child of Crossbow).
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
rw.flat("StringTan", "eadbb2", 0.7, 0.0)
rw.flat("FletchRed", "d8322a", 0.6, 0.0)
BRASS, COPPER, STEEL, DARK = "M_Brass", "M_Copper", "M_Steel", "M_DarkMetal"
WOOD, WOOD_LIGHT = "M_WoodDark", "M_WoodPlanks"
parts = th.Parts()
add = parts.add

ZT = 0.15                 # stock top (groove floor)
SW = 0.025                # stock half width
BOLT_Z = 0.1585           # bolt axis height
NOCK_Y, TIP_Y = -0.073, -0.43
STRING_Z = 0.157
APEX_Y = -0.069           # string centre, drawn back against the latch

# --- tiller (stock) -----------------------------------------------------------------------------------------------
stock = [(-0.405, 0.118), (-0.405, ZT), (0.07, ZT), (0.145, 0.137), (0.156, 0.127), (0.156, 0.072),
         (0.146, 0.062), (0.08, 0.075), (0.02, 0.086), (-0.04, 0.089), (-0.12, 0.099), (-0.3, 0.112)]
add(dh.slab("stock", stock, -SW, SW, WOOD, 0.011, 3))
add(rw.rounded_box("butt_plate", (2 * SW + 0.006, 0.012, 0.074), 0.005, (0, 0.16, 0.0995), mat=BRASS, segments=2))
for z in (0.078, 0.121):
    add(nw.stud((0, 0.166, z), Y, 0.0052, 0.0036, STEEL, 6))
# stitched leather cheek pad on the player side of the butt
PAD = V((SW + 0.0025, 0.112, 0.108))
add(rw.rounded_box("cheek_pad", (0.008, 0.066, 0.042), 0.0035, tuple(PAD), mat="M_Leather__5a3420", segments=2))
sx_ = PAD.x + 0.0042
add(dh.stitches([(sx_, 0.083, 0.124), (sx_, 0.141, 0.124), (sx_, 0.141, 0.092), (sx_, 0.083, 0.092),
                 (sx_, 0.083, 0.124)], X, "M_Leather__d9c08c", 0.002, 0.0072, 0.0046))
for (y, z0, z1) in ((-0.33, 0.111, ZT), (0.055, 0.079, ZT)):
    add(rw.rounded_box("stock_band", (2 * SW + 0.007, 0.014, z1 - z0 + 0.007), 0.004, (0, y, (z0 + z1) / 2), mat=BRASS,
                       segments=1))
    for sx in (-1, 1):
        add(nw.stud((sx * (SW + 0.0035), y, (z0 + z1) / 2), (sx, 0, 0), 0.0045, 0.0032, STEEL, 6))
# brass groove rails the bolt rides between
for sx in (-1, 1):
    add(pl.obox("rail", (0.008, 0.33, 0.007), (sx * 0.0118, -0.215, ZT + 0.0025), Y, Z, BRASS, rounded=0.0025,
                segments=1))
# latch claw holding the string
add(rw.rounded_box("latch", (0.03, 0.016, 0.018), 0.004, (0, -0.052, ZT + 0.009), mat=BRASS, segments=1))
for sx in (-1, 1):
    add(pl.capsule("latch_claw", (sx * 0.0115, -0.058, ZT + 0.013), (sx * 0.012, -0.0655, ZT + 0.0085), 0.0042, 6, 1,
                   STEEL))
add(nw.stud((0, -0.052, ZT + 0.018), Z, 0.0048, 0.0032, STEEL, 6))

# --- pistol grip, guard, trigger -------------------------------------------------------------------------------------
add(th.pistol_grip(A, o, fr))
add(th.trigger_group(-0.104, 0.098))

# --- prod lock, limbs, string, stirrup -----------------------------------------------------------------------------------
PY = -0.382
add(rw.rounded_box("prod_lock", (0.084, 0.05, 0.04), 0.008, (0, PY, 0.131), mat=STEEL, segments=2))
for sx in (-1, 1):
    add(rw.rounded_box("prod_cheek", (0.016, 0.05, 0.034), 0.006, (sx * 0.034, PY, 0.151), mat=STEEL, segments=1))
    add(pl.bolt((sx * 0.042, PY - 0.012, 0.126), (sx, 0, 0), 0.0055, 0.004, BRASS, "lock_bolt", washer=False))
    add(pl.bolt((sx * 0.042, PY + 0.012, 0.126), (sx, 0, 0), 0.0055, 0.004, BRASS, "lock_bolt", washer=False))
    add(nw.stud((sx * 0.034, PY, 0.168), Z, 0.005, 0.0035, BRASS, 6))
LZ = 0.146
limb = [V((0.04, -0.386, LZ)), V((0.1, -0.381, LZ)), V((0.165, -0.362, LZ + 0.001)), V((0.215, -0.33, LZ + 0.002)),
        V((0.245, -0.297, LZ + 0.003))]
tips = []
for sx in (-1, 1):
    pts = [V((sx * p.x, p.y, p.z)) for p in limb]
    add(pl.sausage("limb", pts, [0.018, 0.017, 0.0155, 0.014, 0.0125], 10, 4, STEEL, (True, True), 2, True, 60,
                   scale_xy=(1.0, 0.42), up_hint=(0, 0, 1)))
    T0 = (pts[1] - pts[0]).normalized()
    add(pl.band("limb_collar", 0.0215, 0.014, 0.008, T0, pts[0] + T0 * 0.016, BRASS, 12, 0.4))
    Tt = (pts[4] - pts[3]).normalized()
    tip = pts[4]
    add(pl.capsule("limb_tip", tip - Tt * 0.02, tip + Tt * 0.002, 0.0128, 10, 2, BRASS))
    add(pl.band("tip_groove", 0.0132, 0.004, 0.003, Tt, tip - Tt * 0.004, DARK, 10, 0.0))
    tips.append(V((tip.x, tip.y, STRING_Z)))
add(pl.sausage("string", [tips[1], V((0, APEX_Y, STRING_Z)), tips[0]], 0.0056, 6, 1, "StringTan", (True, True), 1,
               False, 50))
for sx, t in zip((-1, 1), tips):
    Tt = (V((sx * limb[4].x, limb[4].y, 0)) - V((sx * limb[3].x, limb[3].y, 0))).normalized()
    loop = rw.torus("string_loop", 0.0136, 0.0034, 10, 4, (0, 0, 0), mat="StringTan")
    pl.align(loop, Tt, V((sx * limb[4].x, limb[4].y, limb[4].z)) - Tt * 0.009)
    add(loop)
st = [V((-0.026, -0.404, 0.119)), V((-0.044, -0.428, 0.119)), V((-0.033, -0.455, 0.119)), V((0.0, -0.463, 0.119)),
      V((0.033, -0.455, 0.119)), V((0.044, -0.428, 0.119)), V((0.026, -0.404, 0.119))]
add(pl.sausage("stirrup", st, 0.0068, 8, 3, STEEL, (True, True), 2, True, 60))

# --- magazine box on top, with more bolts poking out ------------------------------------------------------------
MY0, MY1 = -0.142, -0.278
MB = V((0, (MY0 + MY1) / 2, 0.191))
MH = 0.082
add(rw.rounded_box("mag_box", (0.054, MY0 - MY1, MH), 0.007, tuple(MB), mat=WOOD_LIGHT, segments=2))
add(rw.rounded_box("mag_lid", (0.06, MY0 - MY1 + 0.006, 0.012), 0.004, tuple(MB + V((0, 0, MH / 2 + 0.002))),
                   mat=BRASS, segments=1))
for y in (MY0 - 0.012, MY1 + 0.012):
    add(rw.rounded_box("mag_strap", (0.06, 0.012, MH + 0.004), 0.004, (0, y, MB.z - 0.002), mat=BRASS, segments=1))
    for sx in (-1, 1):
        add(nw.stud((sx * 0.0302, y, MB.z - 0.022), (sx, 0, 0), 0.0042, 0.003, STEEL, 6))
for y, d in ((MY0, 1), (MY1, -1)):
    add(pl.obox("mag_slot", (0.026, 0.06, 0.004), (0, y + d * 0.0005, MB.z + 0.012), X, Y * d, DARK, rounded=0.0015,
                segments=1))
# bolt tails (red vanes) out of the back and brass heads out of the front
for zz in (0.186, 0.219):
    add(pl.rod("mag_shaft", (0, MY0 + 0.004, zz), (0, MY0 + 0.034, zz), 0.006, 8, STEEL))
    add(pl.lathe_axis("mag_nock", [(0.0075, 0.0), (0.0085, 0.002), (0.0085, 0.009), (0.006, 0.011), (0.0, 0.011)], Y,
                      (0, MY0 + 0.031, zz), 8, BRASS, False, False, 45))
    for ang in (90, 210, 330):
        a = math.radians(ang)
        d = V((math.cos(a), 0, math.sin(a)))
        n = Y.cross(d).normalized()
        vane = [(0.0, 0.0), (0.03, 0.0), (0.027, 0.008), (0.01, 0.0165), (0.0, 0.0145)]
        add(dh.prism("mag_vane", vane, V((0, MY0 + 0.031, zz)) + d * 0.004, -Y, d, n, 0.0045, "FletchRed", -0.00225,
                     0.0, 0))
    add(pl.lathe_axis("mag_head", [(0.0, 0.0), (0.0098, 0.0), (0.0128, 0.006), (0.0118, 0.014), (0.0, 0.036)], -Y,
                      (0, MY1 - 0.002, zz), 4, BRASS, False, False, 20, 45.0))
# windows on both sides showing the stacked bolts inside
for sx in (-1, 1):
    wc = V((sx * 0.027, -0.229, 0.192))
    add(dh.plate("mag_window", wc, X * sx, 0.06, 0.042, 0.003, mat=BRASS, rivets=STEEL, rr=0.003, inset=0.004))
    add(pl.obox("window_hole", (0.048, 0.03, 0.002), wc + X * (sx * 0.0035), Y, X * sx, DARK, rounded=0.0008,
                segments=1))
    for zz in (0.184, 0.2):
        add(pl.rod("window_bolt", wc + V((sx * 0.0045, 0.022, zz - wc.z)), wc + V((sx * 0.0045, -0.016, zz - wc.z)),
                   0.0042, 6, STEEL))
        add(pl.lathe_axis("window_head", [(0.0, 0.0), (0.0058, 0.0), (0.0066, 0.004), (0.0, 0.012)], -Y,
                          wc + V((sx * 0.0045, -0.016, zz - wc.z)), 4, BRASS, False, False, 20, 45.0))
# the caged rarity lamp on the +X face of the magazine, looking back at the player
add(dh.lamp("rarity", (0.027, MY0 - 0.04, MB.z + 0.014), V((1, 0.45, 0.2)).normalized(), 0.0095, RARITY,
            up=(0, 0, 1), bezel=BRASS, cage=2, cage_mat=STEEL, segs=12))

# --- winding gear on top, crank on +X ---------------------------------------------------------------------------------
GC = V((0, 0.026, 0.166))
add(nw.spoked_gear("wind_gear", 0.036, 12, 0.014, X, GC, BRASS, STEEL, spokes=5, spin=7.5, chamfer=0.0015,
                   bolt=False))
for sx in (-1, 1):
    blk = [(GC.y - 0.016, ZT - 0.004), (GC.y + 0.016, ZT - 0.004), (GC.y + 0.016, GC.z), (GC.y + 0.009, GC.z + 0.014),
           (GC.y - 0.009, GC.z + 0.014), (GC.y - 0.016, GC.z)]
    add(dh.slab("pillow_block", blk, sx * 0.0115, sx * 0.0195, BRASS, 0.0025, 1))
add(pl.rod("axle", (-0.024, GC.y, GC.z), (0.04, GC.y, GC.z), 0.0052, 10, STEEL))
CK0 = V((0.04, GC.y, GC.z))
CK1 = V((0.044, 0.068, 0.132))
add(pl.disc("crank_hub", 0.0115, 0.008, X, CK0, BRASS, 12, 0.4))
add(pl.beam_between("crank_arm", CK0 + X * 0.002, CK1, (0.007, 0.013), BRASS, rounded=0.003, segments=1,
                    up=(1, 0, 0)))
add(pl.capsule("crank_knob", CK1 + X * 0.004, CK1 + X * 0.028, 0.0095, 10, 2, WOOD))
add(pl.band("knob_ferrule", 0.0102, 0.006, 0.004, X, CK1 + X * 0.006, BRASS, 10, 0.0))
add(pl.bolt(CK0 + X * 0.004, X, 0.006, 0.0045, STEEL, "crank_nut", washer=False))
# steel pawl riding on the gear teeth (top front), with a little spring
add(pl.beam_between("pawl", (0.0, -0.022, ZT + 0.004), (0.0, -0.008, GC.z + 0.026), (0.008, 0.007), STEEL,
                    rounded=0.002, segments=1, up=(1, 0, 0)))
add(nw.stud((0.004, -0.022, ZT + 0.004), X, 0.0042, 0.003, BRASS, 6))
add(dh.spring("pawl_spring", (0.0, -0.032, ZT + 0.002), (0.0, -0.019, ZT + 0.015), 0.0045, 0.0018, 2.0, STEEL, 4))

# --- +X side plate with filigree (player side) ---------------------------------------------------------------------
add(dh.plate("side_plate", (SW - 0.001, -0.205, 0.128), X, 0.15, 0.03, 0.004, mat=BRASS, rivets=STEEL, rr=0.0036))
add(dh.scroll("filigree", (SW + 0.003, -0.205, 0.128), X, 0.085, width=0.0055, height=0.0026, mat=COPPER))
add(dh.rivet_line((SW, -0.06, 0.103), (SW, 0.03, 0.098), 3, X, 0.0045, 0.0032, BRASS, 6))

# --- -X side: mainspring barrel, ratchet wheel, maker's plate ---------------------------------------------------------
MSC = V((-SW, -0.035, 0.122))
add(pl.lathe_axis("spring_barrel", [(0.0, 0.0), (0.024, 0.0), (0.026, 0.004), (0.026, 0.01), (0.022, 0.013),
                                    (0.0, 0.013)], -X, MSC + X * 0.003, 16, BRASS, False, False, 40))
add(dh.curl("mainspring", MSC - X * 0.0098, -X, 0.018, up=(0, 0, 1), turns=2.2, start=90.0, cw=True, width=0.0042,
            height=0.0022, mat=STEEL, n=14))
add(nw.stud(MSC - X * 0.0102, -X, 0.0042, 0.003, STEEL, 6))
for k in range(4):
    a = math.radians(45 + 90 * k)
    add(nw.stud(MSC - X * 0.0092 + V((0, math.cos(a), math.sin(a))) * 0.021, -X, 0.0032, 0.0024, STEEL, 5))
add(nw.gear("ratchet", 0.017, 10, 0.007, X, (-0.0275, GC.y, GC.z), STEEL, depth=0.0045))
add(pl.bolt((-0.031, GC.y, GC.z), -X, 0.0058, 0.0045, STEEL, "axle_nut", washer=False))
add(dh.plate("maker", (-SW + 0.001, 0.105, 0.108), -X, 0.036, 0.028, 0.004, mat=BRASS, rivets=COPPER, rr=0.0032))
add(dh.gear("maker_gear", (-SW - 0.004, 0.105, 0.108), -X, 0.0085, 8, 0.0026, 0.003, COPPER, hub=False))
add(nw.stud((-SW - 0.006, 0.105, 0.108), -X, 0.0032, 0.0024, BRASS, 6))

bow = rw.join(parts, "Crossbow", origin=(0, 0, 0))
rw.smooth(bow, 45)

# --- the loaded bolt (separate) ------------------------------------------------------------------------------------
bparts = th.Parts()
bparts.add(pl.rod("shaft", (0, NOCK_Y - 0.008, BOLT_Z), (0, TIP_Y + 0.04, BOLT_Z), 0.0062, 8, STEEL))
bparts.add(pl.lathe_axis("nock", [(0.0, 0.0), (0.0068, 0.0), (0.0086, 0.002), (0.0086, 0.01), (0.0068, 0.012),
                                  (0.0068, 0.014)], -Y, (0, NOCK_Y, BOLT_Z), 8, BRASS, False, False, 45))
bparts.add(pl.lathe_axis("collar", [(0.0066, -0.002), (0.0098, 0.0), (0.0102, 0.007), (0.0085, 0.009)], -Y,
                         (0, TIP_Y + 0.045, BOLT_Z), 8, BRASS, False, False, 45))
bparts.add(pl.lathe_axis("head", [(0.0, 0.0), (0.0085, 0.0), (0.0142, 0.007), (0.013, 0.014), (0.0, 0.037)], -Y,
                         (0, TIP_Y + 0.037, BOLT_Z), 4, BRASS, False, False, 20, 45.0))
for ang in (90, 18, 162):
    a = math.radians(ang)
    d = V((math.cos(a), 0, math.sin(a)))
    n = Y.cross(d).normalized()
    vane = [(0.0, 0.0), (0.052, 0.0), (0.049, 0.007), (0.034, 0.0175), (0.008, 0.0185), (0.0, 0.012)]
    bparts.add(dh.prism("vane", vane, V((0, NOCK_Y - 0.011, BOLT_Z)) + d * 0.0045, -Y, d, n, 0.0045, "FletchRed",
                        -0.00225, 0.0, 0))
BOLT_C = V((0, (NOCK_Y + TIP_Y) / 2, BOLT_Z))
bolt = rw.join(bparts, "Bolt", origin=tuple(BOLT_C))
rw.smooth(bolt, 45)
pl.parent_keep(bolt, bow)

# --- glove + empties ------------------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
pl.empty_at("Muzzle", (0, TIP_Y, BOLT_Z), bow)
pl.check("vm_crossbow", (0, 0, 0))
rw.finish("vm_crossbow", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_crossbow")
