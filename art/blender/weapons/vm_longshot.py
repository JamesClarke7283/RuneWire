"""vm_longshot: first-person "Brass Longshot", a long brass-and-walnut marksman rifle.

The scope must stay low (its top no more than ~0.13 m above the grip origin), so the action sits in front of
the hand with the bore low (BZ), and the walnut wrist of the stock arches over the hand to the butt stub.

Nodes (origin = grip centre; the muzzle points -Y):
  Longshot  a brass receiver with steel side screws, engraved filigree and an ejection port; a bolt handle with a
            ball knob and a cocking piece on the +X side; a long octagonal steel barrel with brass bands and a
            chunky slotted muzzle brake; a walnut fore-end with a brass cap, a brass barrel band and a front sling
            swivel with a leather loop; a big brass telescopic scope low on top (steel rings and bases, rubber
            eyecup, knurled focus ring, windage turret on +X, elevation turret on top, glass lenses with a soft
            teal glint); a walnut wrist and butt with a stitched leather cheek rest, the rarity gem on the +X top
            edge of the wrist, brass filigree on the +X side of the butt, a slanted brass butt plate, a leather
            cartridge cuff with three fat rounds on the -X side, a rear sling swivel with a leather loop; a walnut
            pistol grip, brass trigger guard, trigger and a small brass magazine.
  Glove     the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle    empty at the muzzle-brake exit.
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
GLINT = rw.glow("LensGlint", "6ff2e2", 1.2)
BRASS, COPPER, STEEL, DARK = "M_Brass", "M_Copper", "M_Steel", "M_DarkMetal"
WALNUT = "M_WoodDark"
parts = th.Parts()
add = parts.add

BZ = 0.061                     # bore axis height
RY0, RY1 = -0.092, -0.218      # receiver back / front
RW = 0.025                     # receiver half width
RZ0, RZ1 = 0.034, 0.086        # receiver bottom / top
ZS = 0.106                     # scope axis height (scope top stays <= ~0.13)
MUZZLE_Y = -0.703

# --- receiver ------------------------------------------------------------------------------------------------------
rec = [(RY1, RZ1 - 0.006), (RY1, RZ0 + 0.004), (RY1 + 0.012, RZ0), (RY0 - 0.004, RZ0), (RY0, RZ0 + 0.01),
       (RY0, RZ1), (RY1 + 0.01, RZ1)]
add(dh.slab("receiver", rec, -RW, RW, BRASS, 0.007, 2))
for sx in (-1, 1):
    for (y, z) in ((RY0 - 0.016, 0.052), (RY1 + 0.014, 0.052)):
        add(nw.screw(V((sx * RW, y, z)), (sx, 0, 0), 0.0048, STEEL, (0, 1, 1)))
    add(th.scroll_lite("filigree", (sx * (RW + 0.0005), -0.153, 0.062), (sx, 0, 0), 0.068, width=0.0048,
                       height=0.0024, mat=COPPER, flip=sx < 0))
# ejection port on the +X side, behind the bolt handle slot
add(dh.plate("eject_port", (RW - 0.001, -0.165, 0.074), X, 0.042, 0.014, 0.003, mat=DARK, rivets=None,
             rounded=0.0012))
# dovetail rail on top
add(pl.obox("rail", (0.018, 0.1, 0.005), (0, -0.155, RZ1 + 0.002), Y, Z, STEEL, rounded=0.0015, segments=1))
# bolt: body visible at the back of the receiver, handle + ball knob out to +X, cocking piece at the back
add(pl.rod("bolt_body", (0.0, RY0 + 0.012, 0.07), (0.0, RY0 - 0.004, 0.07), 0.0105, 12, STEEL))
add(pl.lathe_axis("cocking_piece", [(0.0, 0.0), (0.009, 0.0), (0.0095, 0.006), (0.007, 0.012), (0.0, 0.013)], Y,
                  (0, RY0 + 0.01, 0.07), 10, STEEL, False, False, 45))
BH0 = V((RW - 0.004, RY0 - 0.012, 0.072))
BH1 = V((0.05, RY0 - 0.004, 0.058))
add(pl.sausage("bolt_handle", [BH0, V((0.036, RY0 - 0.01, 0.07)), BH1], 0.0052, 8, 3, STEEL, (True, True), 2, True,
               60))
add(rw.sphere("bolt_knob", 0.0115, 12, 7, tuple(BH1 + V((0.006, 0.002, -0.004))), mat=BRASS))
add(pl.band("bolt_collar", 0.0085, 0.008, 0.004, (BH1 - BH0).normalized(), BH0 + (BH1 - BH0) * 0.18, BRASS, 8, 0.0))

# --- barrel, bands, muzzle brake ---------------------------------------------------------------------------------
BR = 0.0158                    # barrel flat radius
add(th.octo_bar("barrel", (0, RY1 + 0.008, BZ), (0, MUZZLE_Y + 0.062, BZ), BR, STEEL, Z, 0.003))
add(pl.band("barrel_collar", 0.024, 0.018, 0.01, Y, (0, RY1 - 0.007, BZ), BRASS, 16, 0.0))
for y in (-0.53, -0.6):
    add(pl.band("barrel_band", 0.0212, 0.013, 0.006, Y, (0, y, BZ), BRASS, 16, 0.0))
    add(nw.stud((0, y, BZ + 0.0212), Z, 0.0038, 0.0028, STEEL, 6))
BRK0 = MUZZLE_Y + 0.066
brake = [(0.0, 0.0), (0.022, 0.0), (0.0262, 0.004), (0.0275, 0.013), (0.0275, 0.057), (0.0252, 0.064),
         (0.0118, 0.066), (0.0108, 0.061), (0.0, 0.061)]
brake_o = pl.lathe_axis("brake", brake, -Y, (0, BRK0, BZ), 16, DARK, False, False, 40)
pl.carve(brake_o, [pl.obox("port", (0.09, 0.0115, 0.019), (0, BRK0 - 0.022 - k * 0.0158, BZ), X, Z)
                   for k in range(3)])
add(brake_o)
add(pl.band("brake_ring", 0.0295, 0.009, 0.007, Y, (0, BRK0 - 0.005, BZ), BRASS, 16, 0.0))
add(pl.band("brake_ring", 0.0288, 0.007, 0.006, Y, (0, BRK0 - 0.059, BZ), BRASS, 16, 0.0))

# --- walnut fore-end with cap, bipod and front sling loop ---------------------------------------------------------------
FY0, FY1 = RY1 + 0.004, -0.465
FW = 0.024
fore = [(FY0, 0.069), (FY0, 0.03), (FY0 - 0.03, 0.024), (FY1 + 0.035, 0.03), (FY1, 0.04), (FY1, 0.069)]
add(dh.slab("fore_end", fore, -FW, FW, WALNUT, 0.009, 2))
add(rw.rounded_box("fore_cap", (2 * FW + 0.004, 0.014, 0.05), 0.006, (0, FY1 - 0.004, 0.056), mat=BRASS, segments=2))
add(rw.rounded_box("fore_band", (2 * FW + 0.006, 0.013, 0.06), 0.005, (0, -0.335, 0.054), mat=BRASS, segments=2))
for sx in (-1, 1):
    add(nw.screw(V((sx * (FW + 0.003), -0.335, 0.054)), (sx, 0, 0), 0.0048, STEEL, (0, 0, 1)))
    add(nw.stud((sx * (FW + 0.002), FY1 - 0.004, 0.056), (sx, 0, 0), 0.0042, 0.003, STEEL, 6))
    add(dh.rivet_line((sx * FW, -0.25, 0.048), (sx * FW, -0.31, 0.046), 2, (sx, 0, 0), 0.0042, 0.003, BRASS, 6))
# front sling swivel with a leather loop
add(dh.sling_ring("front_swivel", (0, -0.4, 0.029), -Z, 0.011, 0.0036, STEEL, up=(0, -1, 0)))
add(th.strap_loop("front_sling", V((0, -0.4, 0.003)), Y, Z, 0.016, 0.017, 0.014, 0.0048, "M_Leather"))
add(rw.rounded_box("sling_buckle", (0.019, 0.007, 0.015), 0.002, (0, -0.4, -0.0145), mat=BRASS, segments=1))

# --- the big scope -----------------------------------------------------------------------------------------------
SY0, SY1 = -0.128, -0.33        # tube back / front
add(pl.rod("scope_tube", (0, SY0 + 0.002, ZS), (0, SY1 - 0.002, ZS), 0.0152, 16, BRASS))
eyep = [(0.0152, 0.0), (0.0178, 0.01), (0.0192, 0.024), (0.0192, 0.031), (0.0172, 0.033), (0.015, 0.031),
        (0.0, 0.031)]
eye_o = pl.lathe_axis("eyepiece", eyep, Y, (0, SY0, ZS), 16, BRASS, False, False, 40)
add(eye_o)
add(pl.band("eyecup", 0.0198, 0.008, 0.005, Y, (0, SY0 + 0.029, ZS), "M_Rubber", 16, 0.0))
add(pl.disc("eye_glint", 0.0125, 0.002, Y, (0, SY0 + 0.0305, ZS), GLINT, 14, 0.0))
add(pl.disc("eye_lens", 0.0145, 0.003, Y, (0, SY0 + 0.0322, ZS), "M_Glass", 14, 0.3))
add(nw.gear("focus_ring", 0.0188, 12, 0.009, Y, (0, SY0 + 0.012, ZS), BRASS, depth=0.0018))
obj = [(0.0152, 0.0), (0.0182, 0.008), (0.0222, 0.024), (0.0235, 0.03), (0.0235, 0.044), (0.0216, 0.048),
       (0.018, 0.047), (0.0, 0.047)]
add(pl.lathe_axis("objective", obj, -Y, (0, SY1, ZS), 18, BRASS, False, False, 40))
add(pl.band("objective_ring", 0.0242, 0.006, 0.004, Y, (0, SY1 - 0.04, ZS), STEEL, 18, 0.0))
add(pl.disc("obj_glint", 0.0162, 0.002, -Y, (0, SY1 - 0.045, ZS), GLINT, 16, 0.0))
add(pl.disc("obj_lens", 0.0184, 0.003, -Y, (0, SY1 - 0.0465, ZS), "M_Glass", 16, 0.3))
# rings and bases
for y, zb in ((-0.153, RZ1 + 0.0045), (-0.3, BZ + BR)):
    add(pl.band("scope_ring", 0.0178, 0.012, 0.004, Y, (0, y, ZS), STEEL, 16, 0.0))
    add(rw.rounded_box("ring_base", (0.022, 0.015, ZS - 0.0152 - zb + 0.004), 0.003,
                       (0, y, (ZS - 0.0152 + zb) / 2), mat=STEEL, segments=1))
    add(nw.screw(V((0.0178, y, ZS)), X, 0.0038, STEEL, (0, 0, 1)))
# turret saddle with a windage turret on +X (player side) and a low elevation turret on top
TY = -0.226
add(rw.rounded_box("turret_saddle", (0.034, 0.03, 0.027), 0.008, (0, TY, ZS), mat=BRASS, segments=2))
add(rw.cylinder("windage_base", 0.0095, 0.008, 12, (0.019, TY, ZS), (0, 90, 0), mat=STEEL))
add(dh.knob("windage", (0.022, TY, ZS), X, 0.0125, 0.012, 12, BRASS, STEEL))
add(dh.knob("elevation", (0, TY, ZS + 0.0135), Z, 0.0102, 0.0052, 10, BRASS, STEEL))
add(dh.knob("parallax", (-0.017, TY, ZS), -X, 0.0085, 0.008, 8, BRASS, STEEL))

# --- stock: walnut wrist arching over the hand, butt stub, cheek rest, butt plate ---------------------------------------
SW = 0.024
stock = [(RY0 - 0.002, RZ1), (-0.06, 0.098), (-0.02, 0.111), (0.03, 0.119), (0.13, 0.123), (0.151, 0.121),
         (0.163, 0.044), (0.146, 0.039), (0.11, 0.05), (0.075, 0.064), (0.045, 0.083), (0.0, 0.0895),
         (-0.06, 0.088), (RY0 - 0.002, RZ0 + 0.026)]
stock_r = [0.004, 0.012, 0.02, 0.02, 0.012, 0.005, 0.005, 0.008, 0.03, 0.03, 0.02, 0.012, 0.01, 0.003]
add(dh.slab("stock", nw.rounded_poly(stock, stock_r, 3), -SW, SW, WALNUT, 0.01, 3))
# slanted brass butt plate following the back edge of the butt
bp_a, bp_b = V((0, 0.151, 0.121)), V((0, 0.163, 0.044))
bp_n = V((0, bp_a.z - bp_b.z, bp_b.y - bp_a.y)).normalized()
add(pl.obox("butt_plate", (2 * SW + 0.006, (bp_a - bp_b).length + 0.006, 0.012), (bp_a + bp_b) / 2 + bp_n * 0.003, X,
            bp_n, BRASS, rounded=0.005, segments=2))
for t in (0.25, 0.75):
    add(nw.stud(bp_a.lerp(bp_b, t) + bp_n * 0.009, bp_n, 0.0048, 0.0034, STEEL, 6))
# leather cheek rest on top of the comb, leaning to the player's (+X) side
CR = V((0.006, 0.093, 0.1235))
add(rw.rounded_box("cheek_rest", (0.04, 0.084, 0.013), 0.005, tuple(CR), mat="M_Leather__5a3420", segments=2))
add(dh.stitches([(CR.x - 0.0155, 0.058, 0.1305), (CR.x - 0.0155, 0.128, 0.1305), (CR.x + 0.0155, 0.128, 0.1305),
                 (CR.x + 0.0155, 0.058, 0.1305), (CR.x - 0.0155, 0.058, 0.1305)], Z, "M_Leather__d9c08c", 0.0019,
                0.0068, 0.0044))
for y in (0.064, 0.122):
    add(nw.stud((SW + 0.0005, y, 0.112), X, 0.0042, 0.003, BRASS, 6))
# brass wrist band where the stock meets the receiver, and the rarity gem on the +X top edge of the wrist
add(rw.rounded_box("wrist_band", (2 * SW + 0.004, 0.013, 0.046), 0.005, (0, RY0 + 0.008, 0.07), mat=BRASS,
                   segments=2))
add(nw.gem(V((0.0165, -0.02, 0.1065)), V((0.55, 0.15, 0.82)).normalized(), 0.0074, RARITY, BRASS, 8, "rarity_gem"))
# rear sling swivel + leather loop under the butt
add(dh.sling_ring("rear_swivel", (0, 0.124, 0.046), V((0, 0.25, -1)).normalized(), 0.011, 0.0036, STEEL,
                  up=(0, -1, 0)))
add(th.strap_loop("rear_sling", V((0, 0.13, 0.02)), Y, Z, 0.016, 0.017, 0.014, 0.0048, "M_Leather"))
add(rw.rounded_box("sling_buckle", (0.019, 0.007, 0.015), 0.002, (0, 0.13, 0.0025), mat=BRASS, segments=1))
# leather cartridge cuff with three fat rounds on the -X side of the butt (icon side)
CU = V((-SW - 0.001, 0.098, 0.084))
add(rw.rounded_box("ammo_cuff", (0.008, 0.068, 0.05), 0.003, tuple(CU), mat="M_Leather__5a3420", segments=2))
for y in (0.0755, 0.098, 0.1205):
    add(th.round_lite(V((CU.x - 0.0108, y, 0.057)), Z, 0.056, 0.0068, BRASS, COPPER, 8))
add(rw.rounded_box("cuff_strap", (0.006, 0.072, 0.012), 0.003, tuple(CU + V((-0.0165, 0, -0.003))), mat="M_Leather",
                   segments=1))
for y in (0.068, 0.128):
    add(nw.stud((CU.x - 0.0195, y, CU.z - 0.003), -X, 0.0036, 0.0026, BRASS, 6))
# filigree on the +X side of the butt (player side)
add(th.scroll_lite("butt_filigree", (SW + 0.0005, 0.1, 0.084), X, 0.072, width=0.0052, height=0.0026, mat=BRASS))

# --- pistol grip, guard, trigger, magazine -----------------------------------------------------------------------------
add(th.pistol_grip(A, o, fr))
guard = [(0, -0.152, RZ0 + 0.002), (0, -0.162, 0.012), (0, -0.144, -0.01), (0, -0.104, -0.015), (0, -0.066, -0.01),
         (0, -0.04, 0.0)]
add(pl.sausage("guard", guard, 0.0082, 8, 3, BRASS, (True, True), 2, True, 60))
add(pl.capsule("trigger", (0, -0.106, RZ0 + 0.002), (0, -0.114, 0.01), 0.007, 8, 2, STEEL))
add(rw.rounded_box("magazine", (0.034, 0.038, 0.03), 0.006, (0, -0.192, RZ0 - 0.013), mat=BRASS, segments=2))
add(rw.rounded_box("mag_base", (0.038, 0.042, 0.007), 0.0025, (0, -0.192, RZ0 - 0.029), mat=STEEL, segments=1))
for sx in (-1, 1):
    add(nw.stud((sx * 0.017, -0.192, RZ0 - 0.013), (sx, 0, 0), 0.004, 0.003, STEEL, 6))

rifle = rw.join(parts, "Longshot", origin=(0, 0, 0))
rw.smooth(rifle, 45)

# --- glove + empties ---------------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))
pl.empty_at("Muzzle", (0, MUZZLE_Y, BZ), rifle)
bpy_scope_top = max((rifle.matrix_world @ v.co).z for v in rifle.data.vertices if (rifle.matrix_world @ v.co).y < -0.08)
print("RWREPORT   CHECK scope/top height in front of the hand %.4f (limit ~0.13)" % bpy_scope_top)
pl.check("vm_longshot", (0, 0, 0))
rw.finish("vm_longshot", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_longshot")
