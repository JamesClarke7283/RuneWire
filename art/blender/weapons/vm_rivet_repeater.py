"""vm_rivet_repeater: first-person chunky rivet rifle.

Nodes (origin = grip centre; the muzzle points -Y):
  RivetRepeater  a stepped brass receiver with steel straps and rivet rows, a top strap with a rear ring
                 sight and a front blade sight, a caged rarity lamp on the top-left edge, a strapped brass
                 pressure tank with a hand-wheel valve and a copper feed pipe plus a pressure gauge (left/+X,
                 toward the player), an ejection port with a rivet round poking out, a cocking knob and a
                 maker's plate (right/-X), a rivet-round ammo window, a concave brass feed saddle over the drum, a steel barrel with
                 chunky cooling fins, brass bands, a sling ring and a slotted muzzle brake, a shaped wooden
                 stock with a stitched leather cheek pad, a riveted brass butt plate and a sling ring, and a
                 dark-wood pistol grip with a brass pommel.
  Drum           the drum magazine (child of RivetRepeater). Its origin is ON the spin axis, which runs
                 along Blender X: the game spins it about local X while firing. Everything on it (rim bands,
                 rim rivets, face ribs, face rivets, hubs, winding key) is symmetric around that axis and
                 stays within DRUM_RMAX of it; the receiver keeps clear of that radius. Signal-orange painted
                 faces with steel stiffener rings, brass rivet rings and hubs, a dark-iron rim with brass bands
                 and a row of rim rivets, a brass winding key on the player's (+X) face, an axle nut on -X.
  Glove          the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle         empty at the muzzle-brake exit.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402
import detail_helpers as dh  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

RAKE = 20.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
dh.flat_mats()
X_POS, X_NEG, Y_POS, Y_NEG, Z_POS, Z_NEG = (V((1, 0, 0)), V((-1, 0, 0)), V((0, 1, 0)), V((0, -1, 0)), V((0, 0, 1)),
                                            V((0, 0, -1)))
parts = []


def add(x, into=None):
    tgt = parts if into is None else into
    if isinstance(x, (list, tuple)):
        tgt.extend(x)
    else:
        tgt.append(x)


# --- grip ------------------------------------------------------------------------------------------------
add(glove.oriented_pillow("grip", (0.048, 0.064, 0.2), -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10, "M_WoodDark"))
add(glove.oriented_pillow("pommel", (0.058, 0.074, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16, 8,
                          "M_Brass"))

# --- receiver: stepped side profile (shallow front section over the drum) ---------------------------------------
RZ = 0.135
HW = 0.039
RY0, RY1 = -0.207, 0.093
rec_prof = [(-0.205, 0.12), (-0.13, 0.116), (-0.1, 0.116), (-0.092, 0.11), (-0.086, 0.094), (-0.078, 0.087),
            (0.0, 0.085), (0.06, 0.086), (0.082, 0.09), (0.09, 0.1), (0.093, 0.12), (0.093, 0.165), (0.088, 0.178),
            (0.075, 0.185), (0.0, 0.187), (-0.12, 0.187), (-0.185, 0.185), (-0.2, 0.179), (-0.207, 0.166),
            (-0.208, 0.14)]
add(dh.slab("receiver", rec_prof, -HW, HW, "M_Brass", 0.012, 3))
# riveted steel straps around the receiver
for (y, z0, z1) in ((-0.175, 0.112, 0.191), (0.07, 0.081, 0.191)):
    add(rw.rounded_box("strap", (2 * HW + 0.008, 0.024, z1 - z0), 0.007, (0, y, (z0 + z1) / 2), mat="M_Steel",
                       segments=1))
    for sx in (-1, 1):
        for z in ((z0 + 0.016, z1 - 0.016) if z1 - z0 > 0.09 else ((z0 + z1) / 2,)):
            add(pl.rivet((sx * (HW + 0.004), y, z), (sx, 0, 0), 0.0055, 0.004, "M_Brass", 6))
# top strap with rivets, rear ring sight, front blade sight
add(rw.rounded_box("top_strap", (0.03, 0.24, 0.012), 0.005, (0, -0.065, 0.189), mat="M_Steel", segments=1))
add(dh.rivet_line((0, -0.168, 0.195), (0, -0.052, 0.195), 3, Z_POS, 0.005, 0.0035, "M_Brass", 6))
add(rw.rounded_box("rsight_post", (0.012, 0.014, 0.034), 0.004, (0, 0.06, 0.199), mat="M_Steel", segments=1))
rs = rw.torus("rsight_ring", 0.0125, 0.0042, 14, 6, (0, 0, 0), mat="M_Brass")
pl.align(rs, Y_POS, (0, 0.06, 0.224))
add(rs)
add(rw.rounded_box("fsight", (0.008, 0.014, 0.036), 0.003, (0, -0.193, 0.2), mat="M_Steel", segments=1))
add(rw.sphere("fsight_bead", 0.0065, 8, 4, (0, -0.193, 0.219), mat="M_Brass"))
# rarity lamp, caged, on the top strap (tilted toward the player)
add(dh.lamp("rarity", (0, 0.008, 0.1945), (0.3, 0.15, 1), 0.0095, RARITY, up=(0, 1, 0), bezel="M_Brass", cage=2,
            cage_mat="M_Steel"))

# --- left (+X) side: strapped pressure tank with valve + feed pipe, pressure gauge -------------------------------
TX, TZ = 0.045, 0.124
TY0, TY1 = -0.135, -0.03
L = TY1 - TY0
tank = [(0.0, 0.0), (0.011, 0.0), (0.016, 0.004), (0.018, 0.012), (0.018, L - 0.012), (0.016, L - 0.004),
        (0.011, L), (0.0, L)]
add(pl.lathe_axis("tank", tank, Y_POS, (TX, TY0, TZ), 18, "M_Copper", False, False, 40))
for y in (TY0 + 0.022, TY1 - 0.022):
    add(pl.band("tank_strap", 0.0205, 0.009, 0.006, Y_POS, (TX, y, TZ), "M_Steel", 16, 0.0))
    add(pl.rivet((TX, y, TZ + 0.0205), Z_POS, 0.0045, 0.003, "M_Brass", 6))
add(dh.valve("tank_valve", (TX + 0.006, TY0 + 0.013, TZ + 0.016), Z_POS, 0.0095, 0.003, 3, "M_Brass", "M_Copper",
             0.012))
pipe = [V((TX, TY0 - 0.002, TZ)), V((TX + 0.004, -0.158, TZ + 0.002)), V((0.046, -0.19, 0.132)),
        V((0.028, -0.213, 0.143))]
add(pl.sausage("pipe", pipe, 0.0048, 8, 3, "M_Copper", (True, True), 2, True, 60))
add(pl.band("pipe_flange", 0.0075, 0.006, 0.004, (pipe[1] - pipe[0]).normalized(), pipe[0] + V((0, -0.004, 0)),
            "M_Brass", 10, 0.0))
add(dh.gauge("gauge", (HW, 0.03, 0.137), X_POS, 0.021, needle_deg=25.0, depth=0.012))
# ammo window: rivet rounds peeking through a dark framed slot
add(dh.plate("ammo_win", (HW - 0.001, -0.149, 0.161), X_POS, 0.026, 0.03, 0.004, mat="M_Steel", rivets=None,
             rounded=0.0016))
add(dh.plate("ammo_slot", (HW + 0.002, -0.149, 0.161), X_POS, 0.016, 0.022, 0.002, mat="M_DarkMetal", rivets=None,
             rounded=0.0008))
for z in (0.155, 0.167):
    add(pl.rivet((HW + 0.003, -0.149, z), X_POS, 0.0055, 0.0042, "M_Copper", 8))
add(dh.rivet_line((HW + 0.002, -0.012, 0.102), (HW + 0.002, 0.045, 0.102), 3, X_POS, 0.005, 0.0035, "M_Brass", 6))

# --- right (-X) side: ejection port, cocking knob, maker's plate --------------------------------------------------
add(dh.plate("port", (-HW + 0.001, -0.06, 0.157), X_NEG, 0.052, 0.026, 0.004, mat="M_DarkMetal", rivets=None,
             rounded=0.0018))
add(pl.capsule("port_round", (-HW - 0.002, -0.06, 0.157), (-HW - 0.013, -0.064, 0.159), 0.0068, 8, 2, "M_Copper"))
add(pl.rivet((-HW - 0.013, -0.064, 0.159), (-1, -0.2, 0.1), 0.0098, 0.005, "M_Copper", 8))
add(dh.plate("cock_slot", (-HW + 0.001, -0.125, 0.137), X_NEG, 0.07, 0.013, 0.004, mat="M_Steel", rivets=None,
             rounded=0.0016))
add(pl.rod("cock_stem", (-HW - 0.002, -0.106, 0.137), (-HW - 0.01, -0.106, 0.137), 0.0042, 8, "M_Steel"))
add(rw.sphere("cock_knob", 0.0086, 12, 6, (-HW - 0.0118, -0.106, 0.137), mat="M_Copper"))
add(dh.plate("maker", (-HW + 0.001, 0.025, 0.142), X_NEG, 0.04, 0.032, 0.004, mat="M_Brass", rivets="M_Copper",
             rr=0.0036))
add(dh.gear("maker_gear", (-HW - 0.0045, 0.025, 0.142), X_NEG, 0.0095, 8, 0.0028, 0.003, "M_Copper", hub=False))
add(pl.rivet((-HW - 0.0065, 0.025, 0.142), X_NEG, 0.0035, 0.0025, "M_Brass", 6))

# --- barrel with cooling fins, bands, sling ring and the slotted muzzle brake --------------------------------------
BZ = RZ + 0.01
BY0, BY1 = RY0 + 0.01, -0.315
add(pl.rod("barrel", (0, BY0, BZ), (0, BY1, BZ), 0.021, 14, "M_Steel"))
for i in range(5):
    add(pl.disc("fin", 0.044, 0.009, Y_POS, (0, -0.2245 - i * 0.0145, BZ), "M_Steel", 18, 0.45))
add(pl.band("barrel_band", 0.031, 0.016, 0.012, Y_POS, (0, RY0 - 0.006, BZ), "M_Brass", 18, 0.0))
add(pl.band("barrel_band", 0.029, 0.011, 0.01, Y_POS, (0, -0.2945, BZ), "M_Brass", 18, 0.0))
add(dh.sling_ring("barrel_sling", (0, -0.2945, BZ - 0.0275), Z_NEG, 0.0105, 0.0034, "M_Steel", up=(0, -1, 0)))
brake = pl.lathe_axis("brake", [(0.0, 0.0), (0.03, 0.0), (0.033, 0.005), (0.033, 0.04), (0.03, 0.045),
                                (0.014, 0.045), (0.014, 0.04), (0.0, 0.04)], Y_NEG, (0, BY1 + 0.012, BZ), 16,
                      "M_DarkMetal", False, False, 45)
pl.carve(brake, [pl.obox("slot", (0.1, 0.012, 0.016), (0, BY1 - 0.01 - k * 0.016, BZ), X_POS, Z_POS)
                 for k in range(2)])
add(brake)
TIP_Y = BY1 + 0.012 - 0.045

# --- feed saddle over the drum (concave, clears the spinning drum) ----------------------------------------------
DC = V((0, -0.158, 0.04))           # drum centre: its spin axis runs along X through here
DRUM_R = 0.058                       # drum body radius
DRUM_W = 0.062
DRUM_RMAX = 0.0625                   # nothing on the drum reaches further from the axis than this
DRUM_PAINT = "M_PaintedMetal__e8762c"  # signal orange
saddle = rw.rounded_box("saddle", (0.07, 0.104, 0.06), 0.008, (0, DC.y, 0.098), mat="M_Brass", segments=2)
rw.apply_modifiers(saddle)
pl.carve(saddle, [rw.cylinder("saddle_cut", DRUM_RMAX + 0.0055, 0.2, 40, tuple(DC), (0, 90, 0))])
add(saddle)
for sx in (-1, 1):
    add(pl.rivet((sx * 0.035, DC.y - 0.03, 0.111), (sx, 0, 0), 0.0045, 0.003, "M_Steel", 6))
    add(pl.rivet((sx * 0.035, DC.y + 0.026, 0.111), (sx, 0, 0), 0.0045, 0.003, "M_Steel", 6))

# --- stock: shaped wood, stitched leather cheek pad, riveted butt plate, sling ring --------------------------------
SW = 0.029
stock_prof = [(0.08, 0.1), (0.1, 0.094), (0.14, 0.082), (0.185, 0.07), (0.203, 0.072), (0.207, 0.09),
              (0.207, 0.142), (0.2, 0.153), (0.15, 0.158), (0.08, 0.166)]
add(dh.slab("stock", stock_prof, -SW, SW, "M_WoodDark", 0.011, 3))
add(rw.rounded_box("butt", (2 * SW + 0.006, 0.014, 0.092), 0.005, (0, 0.211, 0.112), mat="M_Brass", segments=2))
for z in (0.084, 0.14):
    add(pl.rivet((0, 0.218, z), Y_POS, 0.0055, 0.004, "M_Steel", 6))
pad_c = V((SW + 0.001, 0.15, 0.123))
add(rw.rounded_box("cheek_pad", (0.008, 0.074, 0.046), 0.0035, tuple(pad_c + V((0.002, 0, 0))),
                   mat="M_Leather__5a3420", segments=2))
sx_ = pad_c.x + 0.006
add(dh.stitches([(sx_, 0.119, 0.141), (sx_, 0.181, 0.141), (sx_, 0.181, 0.105), (sx_, 0.119, 0.105),
                 (sx_, 0.119, 0.141)], X_POS, "M_Leather__d9c08c", 0.0021, 0.0075, 0.0045))
add(dh.sling_ring("stock_sling", (0, 0.168, 0.0755), V((0, -0.25, -1)).normalized(), 0.0105, 0.0034, "M_Steel",
                  up=(0, -1, 0)))

rifle = rw.join(parts, "RivetRepeater", origin=(0, 0, 0))
rw.smooth(rifle, 45)

# --- the drum magazine: a separate object spinning about its local X axis ------------------------------------------
dparts = []
prof = [(0.0, -DRUM_W / 2), (DRUM_R - 0.012, -DRUM_W / 2), (DRUM_R, -DRUM_W / 2 + 0.012), (DRUM_R, DRUM_W / 2 - 0.012),
        (DRUM_R - 0.012, DRUM_W / 2), (0.0, DRUM_W / 2)]
add(pl.lathe_axis("drum_body", prof, X_POS, DC, 28, "M_DarkMetal", False, False, 40), dparts)
for sx in (-1, 1):
    add(pl.band("drum_rim", DRUM_RMAX, 0.01, 0.009, X_POS, DC + V((sx * 0.0135, 0, 0)), "M_Brass", 24, 0.0), dparts)
add(pl.rivet_ring(DC, X_POS, DRUM_R, 10, 0.0052, 0.0042, "M_Steel", 0, 6), dparts)
for sx in (-1, 1):
    n = V((sx, 0, 0))
    fc = DC + n * (DRUM_W / 2)
    # signal-orange painted face with a raised steel stiffener ring, a ring of brass rivets and a brass hub
    add(pl.disc("drum_face", 0.047, 0.006, n, fc, DRUM_PAINT, 24, 0.35), dparts)
    add(pl.band("drum_ring", 0.035, 0.007, 0.007, n, fc + n * 0.003, "M_Steel", 20, 0.0), dparts)
    add(pl.rivet_face_ring(fc + n * 0.003, n, 0.0415, 6, 0.0047, 0.0034, "M_Brass", 30, 6), dparts)
    add(pl.disc("drum_hub", 0.017, 0.012, n, fc + n * 0.004, "M_Brass", 16, 0.4), dparts)
# winding key on the player's (+X) face: stem + butterfly paddle on the spin axis
kx = DC.x + DRUM_W / 2 + 0.01
add(pl.rod("key_stem", (kx, DC.y, DC.z), (kx + 0.014, DC.y, DC.z), 0.0052, 10, "M_Steel"), dparts)
for s in (-1, 1):
    add(pl.disc("key_lobe", 0.0105, 0.006, X_POS, (kx + 0.017, DC.y, DC.z + s * 0.012), "M_Brass", 12, 0.45), dparts)
add(pl.obox("key_web", (0.006, 0.012, 0.022), (kx + 0.017, DC.y, DC.z), X_POS, Z_POS, "M_Brass", rounded=0.002,
            segments=1), dparts)
# axle nut on the -X face
add(pl.bolt(DC + V((-DRUM_W / 2 - 0.01, 0, 0)), X_NEG, 0.0085, 0.006, "M_Steel", "axle_nut"), dparts)
drum = rw.join(dparts, "Drum", origin=tuple(DC))
rw.smooth(drum, 45)
bpy.context.view_layer.update()
rw.set_parent(drum, rifle)
bpy.context.view_layer.update()

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, TIP_Y, BZ))
pl.check("vm_rivet_repeater", (0, 0, 0))
rw.finish("vm_rivet_repeater", "weapons", icon=False)
import wpn_icon  # noqa: E402
wpn_icon.render("vm_rivet_repeater")
