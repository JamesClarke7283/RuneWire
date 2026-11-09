"""vm_arc_pistol: first-person retro-futuristic arc pistol.

Nodes (origin = grip centre; the muzzle points -Y):
  ArcPistol  brass body with rivets and a side pressure gauge, a copper-coiled barrel ending in a
             flared ray-gun emitter, a glass tube with a glowing cyan core on top, a dark-wood grip
             with a brass pommel, a brass trigger guard and a cocking knob.
  Glove      the shared cartoon leather glove gripping the handle (glove.py), wrist toward +Y.
  Muzzle     empty at the emitter tip.
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

RAKE = 15.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
CYAN = rw.glow("ArcCore", "5ff3ff", 4.0)
rw.flat("DialFace", "f6ead0", 0.5, 0.0)
rw.flat("DialNeedle", "d8392b", 0.5, 0.0)
parts = []

# --- grip ------------------------------------------------------------------------------------------------
_, o, fr = glove.frame(A, (-1, 0, 0))
grip = glove.oriented_pillow("grip", (0.046, 0.062, 0.2), A * 0.0 + fr * (-0.004), o, fr, A, 0.6, 0.35, 16, 10,
                             "M_WoodDark")
parts.append(grip)
parts.append(glove.oriented_pillow("pommel", (0.056, 0.072, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16, 8,
                                   "M_Brass"))

# --- body ----------------------------------------------------------------------------------------------------
BZ = 0.128                     # body centre height
parts.append(rw.rounded_box("body", (0.064, 0.23, 0.082), 0.024, (0, -0.045, BZ), mat="M_Brass", segments=3))
# rear dome + cocking knob
parts.append(rw.sphere("rear", 0.041, 16, 8, (0, 0.06, BZ), scale=(0.78, 1.0, 1.0), mat="M_Brass"))
parts.append(pl.rod("knob_stem", (0, 0.09, BZ + 0.012), (0, 0.112, BZ + 0.02), 0.008, 8, "M_Steel"))
parts.append(rw.sphere("knob", 0.017, 12, 6, (0, 0.118, BZ + 0.024), mat="M_Copper"))
# side rivets
for sx in (-1, 1):
    for (y, z) in ((-0.14, BZ + 0.025), (-0.14, BZ - 0.025), (0.035, BZ + 0.025), (0.035, BZ - 0.025)):
        parts.append(pl.rivet((sx * 0.032, y, z), (sx, 0, 0), 0.008, 0.005, "M_Copper", 6))
# pressure gauge on the left side (+X, faces the player)
gc = V((0.034, -0.055, BZ + 0.004))
parts.append(pl.disc("gauge", 0.028, 0.014, (1, 0, 0), gc, "M_Copper", 18, 0.4))
parts.append(pl.disc("gauge_face", 0.021, 0.004, (1, 0, 0), gc + V((0.007, 0, 0)), "DialFace", 18, 0.2))
needle = pl.obox("needle", (0.004, 0.018, 0.004), gc + V((0.0095, -0.004, 0.004)), (0, 1, 0.8), (1, 0, 0),
                 "DialNeedle")
parts.append(needle)

# --- barrel + coil + flared emitter ----------------------------------------------------------------------------
BY0, BY1 = -0.155, -0.275
parts.append(pl.rod("barrel", (0, BY0 + 0.01, BZ), (0, BY1, BZ), 0.022, 16, "M_Steel"))
parts.append(pl.helix("coil", 0.029, 0.0085, 4.5, BY0 - BY1 - 0.03, (0, BY0 - 0.012, BZ), (0, -1, 0), 12, 6,
                      "M_Copper", res=1))
for y in (BY0 - 0.006, BY1 + 0.014):
    parts.append(pl.band("barrel_band", 0.036, 0.016, 0.016, (0, 1, 0), (0, y, BZ), "M_Brass", 18, 0.0))
flare = [(0.024, 0.0), (0.026, 0.012), (0.034, 0.03), (0.05, 0.05), (0.054, 0.056), (0.05, 0.06),
         (0.036, 0.046), (0.02, 0.038), (0.0, 0.036)]
parts.append(pl.lathe_axis("emitter", flare, (0, -1, 0), (0, BY1 + 0.004, BZ), 20, "M_Brass", False, False, 45))
TIP_Y = BY1 + 0.004 - 0.06
parts.append(rw.sphere("tip_glow", 0.018, 12, 6, (0, BY1 - 0.034, BZ), mat=CYAN))
# a little ring held ahead of the flare on three prongs
ring_y = TIP_Y - 0.01
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = V((math.cos(a), 0, math.sin(a)))
    parts.append(pl.capsule("prong", V((0, BY1 - 0.05, BZ)) + d * 0.043, V((0, ring_y, BZ)) + d * 0.03, 0.006, 6, 2,
                            "M_Brass"))
parts.append(rw.torus("ring", 0.03, 0.007, 20, 6, (0, ring_y, BZ), (90, 0, 0), mat="M_Brass"))

# --- glass tube with the glowing cyan core on top --------------------------------------------------------------
TZ = BZ + 0.041 + 0.03
ty0, ty1 = -0.13, 0.045
parts.append(pl.rod("tube", (0, ty0, TZ), (0, ty1, TZ), 0.025, 16, "M_Glass"))
parts.append(pl.capsule("core", (0, ty0 + 0.01, TZ), (0, ty1 - 0.01, TZ), 0.011, 10, 2, CYAN))
for y, d in ((ty0, -1), (ty1, 1)):
    parts.append(pl.lathe_axis("tube_cap", [(0.03, -0.012), (0.03, 0.01), (0.024, 0.018), (0.012, 0.022),
                                            (0.0, 0.023)], (0, d, 0), (0, y, TZ), 16, "M_Brass", True, False, 45))
    parts.append(rw.rounded_box("tube_clip", (0.03, 0.02, 0.032), 0.008, (0, y, TZ - 0.03), mat="M_Brass",
                                segments=1))
# coil spark wire from the tube to the barrel
parts.append(pl.sausage("wire", [(0.0, ty0 - 0.014, TZ), (0.0, ty0 - 0.03, TZ - 0.005), (0, BY0 - 0.01, BZ + 0.035)],
                        0.006, 6, 3, "M_Copper", (True, True), 2, True, 60))

# --- trigger guard + trigger ---------------------------------------------------------------------------------------
guard = [(0, -0.13, BZ - 0.035), (0, -0.135, 0.04), (0, -0.118, 0.008), (0, -0.088, 0.0), (0, -0.064, 0.012)]
parts.append(pl.sausage("guard", guard, 0.008, 8, 3, "M_Brass", (True, True), 2, True, 60))
parts.append(pl.capsule("trigger", (0, -0.088, BZ - 0.04), (0, -0.098, 0.05), 0.007, 8, 2, "M_Steel"))

pistol = rw.join(parts, "ArcPistol", origin=(0, 0, 0))
rw.smooth(pistol, 45)

# --- glove ----------------------------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, TIP_Y - 0.008, BZ))
pl.check("vm_arc_pistol", (0, 0, 0))
rw.finish("vm_arc_pistol", "weapons", icon=True)
