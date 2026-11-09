"""part_seat: 0.8 x 0.8 x 1.2 m pilot seat facing -Y.

Tufted leather cushion on a brass seat pan and pedestal, a tall tufted leather backrest at +Y in a brass
tube frame with a headrest roll, brass tube armrests with leather pads, two control levers in front
(red and black knobs, slotted lever boxes) and two little dials on the armrest ends plus a glowing
rune button. Empty "SitPoint" sits at the cushion top centre. Origin at the bounding-box centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, D, H = 0.8, 0.8, 1.2
Z0, Z1 = -H / 2, H / 2
LEATHER = "M_Leather"
CUSH_TOP = -0.115
parts = []
rw.flat("DialFace", "f6ead0", 0.5, 0.0)
rw.flat("DialNeedle", "d8392b", 0.5, 0.0)
rw.flat("KnobRed", "d8392b", 0.35, 0.0)
rw.flat("KnobBlack", "26232b", 0.35, 0.0)
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

# --- floor plate + pedestal + seat pan ----------------------------------------------------------------
parts.append(rw.rounded_box("floor", (0.66, 0.8, 0.05), 0.018, (0, 0.0, Z0 + 0.025), mat="M_DarkMetal",
                            segments=2))
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(pl.bolt((sx * 0.28, sy * 0.33, Z0 + 0.05), (0, 0, 1), 0.02, 0.01, "M_Brass", washer=False))
ped = [(0.17, Z0 + 0.05), (0.17, Z0 + 0.075), (0.11, Z0 + 0.1), (0.085, Z0 + 0.14), (0.085, -0.36),
       (0.12, -0.335), (0.15, -0.31), (0.0, -0.31)]
parts.append(pl.lathe_axis("pedestal", ped, (0, 0, 1), (0, -0.02, 0), 24, "M_Brass", False, False, 40))
parts.append(pl.band("ped_ring", 0.098, 0.03, 0.02, (0, 0, 1), (0, -0.02, -0.45), "M_Steel", 20))
parts.append(rw.rounded_box("pan", (0.64, 0.6, 0.06), 0.02, (0, 0.0, -0.29), mat="M_Brass", segments=2))

# --- tufted cushion ------------------------------------------------------------------------------------
cush_h = 0.15
CUSH_C = (0.0, -0.02)
cush = pl.superellipsoid("cushion", (0.6, 0.54, cush_h), (CUSH_C[0], CUSH_C[1], CUSH_TOP - cush_h / 2 + 0.008), 0.28,
                         0.45, 20, 10, LEATHER)
buttons = [(-0.13, -0.15), (0.13, -0.15), (-0.13, 0.11), (0.13, 0.11)]
pl.tuft(cush, [(x, y, 0) for (x, y) in buttons], 0.11, 0.02, axis=2, sign=1)
rw.apply_modifiers(cush)
# cushion top at its centre (no button there), measured before joining
cmw = cush.matrix_world
sit_z = max((cmw @ v.co).z for v in cush.data.vertices
            if abs((cmw @ v.co).x - CUSH_C[0]) < 0.08 and abs((cmw @ v.co).y - CUSH_C[1]) < 0.08)
parts.append(cush)
for (x, y) in buttons:
    near = sorted((cmw @ v.co for v in cush.data.vertices if (cmw @ v.co).z > CUSH_TOP - cush_h / 2),
                  key=lambda w: (w.x - x) ** 2 + (w.y - y) ** 2)[:3]
    bz = sum(w.z for w in near) / len(near)
    parts.append(pl.rivet((x, y, bz - 0.004), (0, 0, 1), 0.02, 0.014, "M_Brass", 6))

# --- backrest: tufted pad in a brass tube frame + headrest roll -----------------------------------------
TILT = math.radians(6)
by, bz0, bz1 = 0.22, -0.26, 0.517          # backrest plane at the bottom, bottom/top heights


def back_pt(x, z, off=0.0):
    """Point on the (tilted) backrest plane; off moves toward the front (-Y)."""
    return V((x, by + (z - bz0) * math.tan(TILT) - off, z))


pad_c = back_pt(0, (bz0 + bz1) / 2 + 0.02, 0.005)
pad = pl.superellipsoid("backpad", (0.54, 0.13, bz1 - bz0 - 0.08), (0, 0, 0), 0.3, 0.3, 20, 12, LEATHER)
pl.tuft(pad, [(x, 0, z) for x in (-0.13, 0.13) for z in (-0.22, 0.02, 0.24)], 0.1, 0.016, axis=1, sign=-1)
pl.xform(pad, pl.Matrix.Rotation(-TILT, 4, 'X'))
pad.location = pad_c
parts.append(pad)
bn = V((0, -math.cos(TILT), math.sin(TILT)))       # backrest front normal
for x in (-0.13, 0.13):
    for z in (-0.22, 0.02, 0.24):
        p = V((x, 0, z))
        p = pl.Matrix.Rotation(-TILT, 3, 'X') @ p + pad_c
        # surface point: walk from the pad centre plane toward the front until outside the mesh volume
        parts.append(pl.rivet(p + bn * 0.047, bn, 0.02, 0.016, "M_Brass", 6))
head = pl.sausage("headroll", [back_pt(-0.2, bz1 - 0.01, 0.03), back_pt(0.2, bz1 - 0.01, 0.03)], 0.07, 12, 1,
                  LEATHER, (True, True), 3, False, 60, scale_xy=(1.0, 0.85))
parts.append(head)
frame_pts = []
fx, fz0, fz1 = 0.3, bz0 + 0.02, bz1 + 0.048
for (x, z) in ((-fx, fz0), (-fx, fz1 - 0.08), (-fx + 0.06, fz1), (fx - 0.06, fz1), (fx, fz1 - 0.08), (fx, fz0)):
    frame_pts.append(back_pt(x, z, -0.03))
parts.append(pl.sausage("backframe", frame_pts, 0.026, 8, 3, "M_Brass", (True, True), 2, True, 50))
# back panel (brass sheet) behind the pad
back_panel = rw.rounded_box("backpanel", (0.58, 0.03, bz1 - bz0), 0.012, (0, 0, 0), mat="M_Brass", segments=1)
rw.apply_modifiers(back_panel)
pl.xform(back_panel, pl.Matrix.Rotation(-TILT, 4, 'X'))
back_panel.location = back_pt(0, (bz0 + bz1) / 2, -0.07)
parts.append(back_panel)
bk = V((0, math.cos(TILT), -math.sin(TILT)))      # back panel outward normal
for z in (-0.17, 0.4):
    for x in (-0.22, 0.22):
        p = back_pt(x, z, -0.085)
        parts.append(pl.rivet(p, bk, 0.016, 0.008, "M_Brass", 8))
# gear emblem with a rune eye on the back panel
gc = back_pt(0, 0.12, -0.085)
g = rw.gear("emblem", 0.13, 10, 0.035, 0.02, 0.0, mat="M_Copper", bevel=0.0)
rw.apply_modifiers(g)
pl.align(g, bk, gc)
parts.append(g)
parts.append(pl.disc("emblem_hub", 0.07, 0.02, bk, gc + bk * 0.012, "M_Brass", 16, 0.4))
parts += pl.glyph("eye", gc + bk * 0.022, (1, 0, 0), bk.cross(V((1, 0, 0))) * -1, 0.11, 0.016, 0.008,
                  "M_RuneGlow")

# --- armrests: brass tube + leather pad -----------------------------------------------------------------
AX_ = 0.354
for s in (-1, 1):
    x = s * AX_
    path = [(x, by + 0.02, 0.01), (x, -0.05, 0.02), (x, -0.2, 0.0), (x, -0.23, -0.12), (x, -0.22, -0.27)]
    parts.append(pl.sausage("armtube", path, 0.024, 8, 3, "M_Brass", (True, True), 2, True, 50))
    parts.append(rw.cylinder("armpost", 0.02, 0.27, 10, (x, 0.12, -0.14), mat="M_Brass"))
    armpad = pl.superellipsoid("armpad", (0.085, 0.36, 0.06), (x - s * 0.0, 0.07, 0.055), 0.4, 0.45, 16, 8,
                               LEATHER)
    parts.append(armpad)
    # dial on the armrest end, tilted toward the pilot
    dc = V((x, -0.2, 0.045))
    nrm = V((0, 0.35, 1)).normalized()
    parts.append(pl.disc("dial", 0.046, 0.03, nrm, dc, "M_Brass", 18, 0.4))
    parts.append(pl.disc("dial_face", 0.035, 0.008, nrm, dc + nrm * 0.013, "DialFace", 18, 0.2))
    needle = pl.obox("needle", (0.006, 0.03, 0.004), dc + nrm * 0.018 + V((0.008 * s, -0.004, 0.0)),
                     (1, 0, 0), nrm, "DialNeedle")
    pl.xform(needle, pl.Matrix.Rotation(math.radians(35 * s), 4, nrm))
    parts.append(needle)
# glowing rune button on the right armrest (pilot's right = -X)
parts.append(pl.disc("button_rim", 0.025, 0.014, (0, 0, 1), (-AX_, 0.1, 0.09), "M_Brass", 16, 0.4))
parts.append(rw.sphere("button", 0.017, 12, 6, (-AX_, 0.1, 0.095), scale=(1, 1, 0.6), mat="M_RuneGlow"))

# --- control levers in front ----------------------------------------------------------------------------
LY = -0.33
for s, knob in ((-1, "KnobRed"), (1, "KnobBlack")):
    x = s * 0.2
    parts.append(rw.rounded_box("leverbox", (0.11, 0.13, 0.12), 0.02, (x, LY, Z0 + 0.11), mat="M_Brass", segments=2))
    parts.append(rw.box("slot", (0.024, 0.09, 0.01), (x, LY, Z0 + 0.172), mat="M_DarkMetal"))
    top = V((x, LY + 0.06, 0.0))
    base = V((x, LY - 0.015, Z0 + 0.15))
    parts.append(pl.rod("lever", base, top, 0.016, 10, "M_Steel"))
    parts.append(rw.sphere("knob", 0.045, 12, 6, top + V((0, 0, 0.03)), mat=knob))
    parts.append(pl.band("knobring", 0.022, 0.02, 0.008, (0, 0, 1), top + V((0, 0, -0.008)), "M_Brass", 12))

seat = rw.join(parts, "Seat")
rw.smooth(seat, 40)

shift = pl.recentre()
rw.set_origin(seat, (0, 0, 0))
# SitPoint: cushion top centre (measured on the cushion before joining), moved with the recentre shift
rw.empty("SitPoint", (CUSH_C[0] - shift.x, CUSH_C[1] - shift.y, round(sit_z - shift.z, 4)))
pl.check("part_seat", (W, D, H))
rw.finish("part_seat", "parts", icon=True)
