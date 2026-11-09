"""vm_thunder_wrench: first-person "Thunder Wrench", an oversized cartoon adjustable wrench swung like a club.

Nodes (origin = grip centre; the wrench runs forward (-Y) and up at 35 degrees, like vm_staff's wand):
  ThunderWrench  a fat steel crescent head with a thick open jaw (copper contact pads on both inner faces), a
                 riveted brass sliding jaw, a knurled brass worm wheel, brass-rimmed badges with a yellow
                 lightning bolt on both faces; a riveted dark-iron handle with a brass window
                 frame holding a glass lightning capacitor (a glowing cyan arc jumps between two electrodes),
                 a copper coil winding under the head with copper feed wires into the head, a spiral
                 leather-wrapped grip between brass ferrules, a brass hex-nut pommel and the rarity gem on the
                 handle face that looks at the player. The whole wrench is rolled 45 degrees about its axis so
                 the jaw silhouette reads both in first person (+X side) and on the inventory icon (-X side).
  Glove          the shared cartoon leather glove gripping the handle near the bottom (glove.py).
  Tip            empty at the centre of the striking face: the jaw mouth, level with the jaw tips.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import new_weapon_helpers as nw  # noqa: E402

glove, pl, rw, V = nw.glove, nw.pl, nw.rw, nw.V
rw.reset()

TILT, ROLL = 35.0, 45.0
X = V((1, 0, 0))
AX = V((0, -math.cos(math.radians(TILT)), math.sin(math.radians(TILT))))    # handle axis, toward the head
UPW = V((0, math.sin(math.radians(TILT)), math.cos(math.radians(TILT))))    # perpendicular to AX, up and back
NF = (X * math.cos(math.radians(ROLL)) + UPW * math.sin(math.radians(ROLL))).normalized()  # face normal (player)
WD = AX.cross(NF).normalized()                                              # across the wrench face

ARC = rw.glow("ArcGlow", "5ff3ff", 5.0)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
rw.flat("BoltYellow", "ffc531", 0.5, 0.0)
GRIP_LEATHER = "M_Leather__5a321c"
parts = []


def P(a, w=0.0, n=0.0):
    """Point in the wrench frame: a along the handle, w across the face, n out of the player-side face."""
    return AX * a + WD * w + NF * n


def box(name, a, w, size, mat, rounded=0.006, segments=2):
    """Rounded box in the wrench frame; size = (along AX, along WD, along NF)."""
    return pl.obox(name, size, P(a, w), AX, NF, mat, rounded=rounded, segments=segments)


# --- grip: spiral leather wrap, brass ferrules, hex-nut pommel -------------------------------------------------
G0, G1 = -0.08, 0.12
parts.append(nw.spiral_wrap("grip_wrap", P(G0), AX, G1 - G0, 0.027, 0.0034, 6.5, GRIP_LEATHER, segs=14,
                            steps_per_turn=7, x_hint=WD))
parts.append(pl.band("ferrule_top", 0.033, 0.022, 0.012, AX, P(G1 + 0.008), "M_Brass", 18, 0.4))
parts.append(pl.band("ferrule_bottom", 0.032, 0.014, 0.01, AX, P(G0 - 0.004), "M_Brass", 18, 0.4))
nut = rw.cylinder("pommel_nut", 0.033, 0.024, 6, (0, 0, 0), mat="M_Brass")
rw.add_bevel(nut, 0.0035, 1, 30).harden_normals = False
pl.align(nut, AX, P(G0 - 0.022), x_hint=WD)
parts.append(nut)
parts.append(pl.lathe_axis("pommel_cap", [(0.0, 0.0), (0.025, 0.0), (0.0235, 0.008), (0.015, 0.0145), (0.0, 0.0165)],
                           -AX, P(G0 - 0.033), 16, "M_Brass", False, False, 45))

# --- handle: dark-iron bar, capacitor window, coil -------------------------------------------------------------
A_HEAD = 0.47                         # head centre along the axis
NECK = A_HEAD - 0.125                 # where the bar enters the head
WA0, WA1 = 0.18, 0.292                # capacitor window frame
BAR_W, BAR_T = 0.058, 0.03
parts.append(box("bar", (G1 + 0.005 + WA0 + 0.01) / 2, 0.0, (WA0 + 0.005 - G1, BAR_W, BAR_T), "M_DarkMetal", 0.009))
parts.append(box("bar", (WA1 - 0.01 + NECK + 0.012) / 2, 0.0, (NECK + 0.022 - WA1, BAR_W, BAR_T), "M_DarkMetal",
                 0.009))
# the rarity gem on the lower bar, on the face that looks at the player
parts += nw.gem(P(0.1595, 0.0, BAR_T / 2 - 0.001), NF, 0.0088, RARITY, "M_Brass", 8, "rarity_gem")
for s in (-1, 1):
    parts.append(nw.stud(P(0.1595, s * 0.0225, BAR_T / 2), NF, 0.005, 0.0035, "M_Brass", 6))
    parts.append(nw.stud(P(0.1595, s * 0.0225, -BAR_T / 2), -NF, 0.005, 0.0035, "M_Brass", 6))
# window frame: brass end blocks and two dark rails around a glass cell
for a in (WA0 + 0.012, WA1 - 0.012):
    parts.append(box("frame_block", a, 0.0, (0.024, 0.104, 0.038), "M_Brass", 0.008))
    for s in (-1, 1):
        for nn in (-1, 1):
            parts.append(nw.stud(P(a, s * 0.038, nn * 0.019), NF * nn, 0.0052, 0.0036, "M_Steel", 6))
for s in (-1, 1):
    parts.append(box("frame_rail", (WA0 + WA1) / 2, s * 0.042, (WA1 - WA0 - 0.022, 0.016, 0.028), "M_DarkMetal",
                     0.006))
CELL_R = 0.0255
CL = WA1 - WA0 - 0.026
parts.append(pl.lathe_axis("cell_glass", [(0.0, 0.0), (CELL_R * 0.9, 0.0), (CELL_R, 0.006), (CELL_R, CL - 0.006),
                                          (CELL_R * 0.9, CL), (0.0, CL)], AX, P(WA0 + 0.013), 18, "M_Glass", False,
                           False, 50))
E0, E1 = WA0 + 0.032, WA1 - 0.032     # electrode tips
for a, d in ((E0, AX), (E1, -AX)):
    parts.append(pl.rod("electrode", P(a) - d * 0.014, P(a) - d * 0.004, 0.0045, 8, "M_Copper"))
    parts.append(rw.sphere("electrode_ball", 0.007, 10, 5, tuple(P(a)), mat="M_Copper"))
# the cyan arc: a flat zigzag ribbon facing the player, plus a thinner strand at right angles
half = (E1 - E0) / 2 - 0.005
zz = [(-half, 0.0), (-half * 0.6, 0.0115), (-half * 0.18, -0.0105), (half * 0.22, 0.0115), (half * 0.62, -0.0095),
      (half, 0.0)]
parts.append(nw.slab("arc", nw.ribbon_poly(zz, 0.005, (0.45, 0.45)), 0.008, P((E0 + E1) / 2), AX, WD, ARC,
                     smooth_angle=0))
zz2 = [(-half, 0.0), (-half * 0.45, -0.0095), (half * 0.05, 0.01), (half * 0.5, -0.0085), (half, 0.0)]
parts.append(nw.slab("arc2", nw.ribbon_poly(zz2, 0.0032, (0.5, 0.5)), 0.006, P((E0 + E1) / 2), AX, NF, ARC,
                     smooth_angle=0))
# copper coil wound round the bar between brass collars, right under the head
CO0, CO1 = WA1 + 0.008, NECK + 0.01
for a in (CO0, CO1):
    parts.append(box("coil_collar", a, 0.0, (0.01, 0.086, 0.05), "M_Brass", 0.0045))
parts.append(nw.oval_helix("coil", P(CO0 + 0.007), AX, WD, 0.036, 0.0215, 0.006, 4.0, CO1 - CO0 - 0.014,
                           "M_Copper", 12, 6))
# copper feed wires from the window frame round the coil into the head
for s in (-1, 1):
    pts = [P(WA1 - 0.006, s * 0.05, 0.0), P(CO0 + 0.012, s * 0.056, 0.005), P(CO1 - 0.004, s * 0.055, 0.005),
           P(NECK + 0.03, s * 0.044, 0.0)]
    parts.append(nw.cable("feed_wire", pts, 0.005, "M_Copper", 6, 3))

# --- head: a fat crescent with an open jaw ------------------------------------------------------------------------
HC = P(A_HEAD)
head_pts = [(-0.125, -0.031), (-0.095, -0.037), (-0.085, -0.076), (-0.052, -0.1), (-0.052, -0.048),
            (0.028, -0.048), (0.028, 0.03), (0.118, 0.03), (0.122, 0.078), (0.07, 0.106), (-0.03, 0.105),
            (-0.088, 0.07), (-0.098, 0.037), (-0.125, 0.031)]
head_r = [0.0, 0.02, 0.03, 0.006, 0.005, 0.004, 0.01, 0.008, 0.02, 0.045, 0.045, 0.03, 0.02, 0.0]
parts.append(nw.slab("head", nw.rounded_poly(head_pts, head_r, 4), 0.058, HC, AX, WD, "M_Steel", bevel=0.005,
                     segments=2))
jaw_pts = [(0.0, -0.1), (0.095, -0.1), (0.12, -0.075), (0.12, -0.03), (0.03, -0.03), (0.03, -0.05), (0.0, -0.05)]
jaw_r = [0.006, 0.02, 0.016, 0.006, 0.005, 0.004, 0.004]
parts.append(nw.slab("sliding_jaw", nw.rounded_poly(jaw_pts, jaw_r, 3), 0.05, HC, AX, WD, "M_Brass", bevel=0.0045,
                     segments=2))
# rack teeth on the sliding jaw's shank, meshing with the knurled worm wheel in the notch behind it
for k in range(4):
    w = -0.056 - k * 0.011
    parts.append(pl.obox("jaw_rack", (0.006, 0.006, 0.04), HC + AX * -0.0015 + WD * w, AX, NF, "M_Brass",
                         rounded=0.0015, segments=1))
WC = HC + AX * -0.026 + WD * -0.075
parts.append(nw.gear("worm", 0.021, 14, 0.044, WD, WC, "M_Brass", depth=0.0035, x_hint=AX))
for k in (-1, 1):
    parts.append(pl.band("worm_thread", 0.0215, 0.005, 0.006, WD, WC + WD * (k * 0.011), "M_Copper", 14, 0.4))
parts.append(pl.rod("worm_pin", HC + AX * -0.026 + WD * -0.046, HC + AX * -0.026 + WD * -0.104, 0.0055, 8,
                    "M_Steel"))
# copper contact pads on both inner jaw faces: the jaws double as electrodes
for w, s in ((0.03, -1), (-0.03, 1)):
    parts.append(pl.obox("jaw_pad", (0.066, 0.005, 0.042), HC + AX * 0.079 + WD * (w + s * 0.0015), AX, NF,
                         "M_Copper", rounded=0.0018, segments=1))
    for a in (0.056, 0.102):
        parts.append(nw.stud(HC + AX * a + WD * (w + s * 0.004), WD * s, 0.0042, 0.003, "M_Steel", 6))
# steel rivets tying the brass sliding jaw in
for nn in (-1, 1):
    for (a, w) in ((0.052, -0.068), (0.094, -0.078)):
        parts.append(nw.stud(HC + AX * a + WD * w + NF * (nn * 0.025), NF * nn, 0.0058, 0.004, "M_Steel", 6))
# brass-rimmed badges with a big lightning bolt on both faces of the head, rivets round them
BADGE = (-0.036, 0.034)
for nn in (-1, 1):
    bc = HC + AX * BADGE[0] + WD * BADGE[1]
    parts.append(nw.slab("badge_rim", nw.ellipse(0.051, 0.043, 20), 0.004, bc + NF * (nn * 0.0295), AX, WD, "M_Brass",
                         smooth_angle=40))
    parts.append(nw.slab("badge", nw.ellipse(0.044, 0.036, 20), 0.004, bc + NF * (nn * 0.031), AX, WD, "M_DarkMetal",
                         smooth_angle=40))
    parts.append(nw.bolt_emblem("bolt_emblem", bc + AX * 0.002 + NF * (nn * 0.0325), WD, -AX, 0.066, 0.004,
                                "BoltYellow"))
    for (a, w) in ((-0.106, 0.0), (-0.07, -0.054), (0.008, -0.03), (0.082, 0.074)):
        parts.append(nw.stud(HC + AX * a + WD * w + NF * (nn * 0.029), NF * nn, 0.0065, 0.0045, "M_Brass", 6))

wrench = rw.join(parts, "ThunderWrench", origin=(0, 0, 0))
rw.smooth(wrench, 45)

# --- glove: a hammer grip around the handle, fingers wrapping from below ------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Tip", tuple(HC + AX * 0.121))
pl.check("vm_thunder_wrench", (0, 0, 0))
rw.finish("vm_thunder_wrench", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_thunder_wrench")
