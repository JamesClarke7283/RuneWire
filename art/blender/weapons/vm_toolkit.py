"""vm_toolkit: first-person Rune Toolkit (the build/grab tool).

Nodes (origin = grip centre; the lens points -Y):
  Toolkit  a brass tuning-fork multitool on a pistol grip: a riveted brass body wound with copper coils,
           a forked pair of brass tines holding a round teal crystal lens (M_Crystal) in a brass ring at
           the front, a little dial screen with a glowing teal display on top (tilted toward the player),
           a glowing rune on the side, a thumb toggle and a dark-iron grip with a brass pommel.
  Glove    the shared cartoon leather glove gripping the handle (glove.py), wrist toward +Y.
  Emitter  empty at the lens tip.
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
_, o, fr = glove.frame(A, (-1, 0, 0))
SCREEN = rw.glow("ToolScreen", "5ff3d2", 2.5)
rw.flat("ScreenInk", "123b3a", 0.6, 0.0)
parts = []

# --- grip --------------------------------------------------------------------------------------------------
parts.append(glove.oriented_pillow("grip", (0.046, 0.062, 0.2), -fr * 0.004, o, fr, A, 0.6, 0.35, 16, 10,
                                   "M_DarkMetal"))
parts.append(glove.oriented_pillow("pommel", (0.056, 0.072, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16,
                                   8, "M_Brass"))

# --- body: a brass cylinder along Y with copper coil windings ------------------------------------------------
BZ = 0.128
BY0, BY1 = 0.07, -0.13                 # back / front of the body
body = [(0.0, 0.0), (0.03, 0.0), (0.042, 0.012), (0.046, 0.03), (0.046, BY0 - BY1 - 0.03), (0.04, BY0 - BY1 - 0.01),
        (0.03, BY0 - BY1), (0.0, BY0 - BY1)]
parts.append(pl.lathe_axis("body", body, (0, -1, 0), (0, BY0, BZ), 20, "M_Brass", False, False, 45))
parts.append(pl.helix("coil", 0.05, 0.0085, 4.0, 0.075, (0, -0.005, BZ), (0, -1, 0), 12, 6, "M_Copper", res=1))
for y in (0.0, -0.09):
    parts.append(pl.band("collar", 0.056, 0.014, 0.014, (0, 1, 0), (0, y, BZ), "M_Steel", 20, 0.0))
# rivets on the rear part
for k in range(5):
    a = math.radians(30 + 72 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    parts.append(pl.rivet(V((0, 0.035, BZ)) + d * 0.046, d, 0.0075, 0.005, "M_Steel", 6))
# glowing rune on the left (+X) side, facing the player
parts += pl.glyph("algiz", V((0.0465, 0.032, BZ - 0.003)), (0, -1, 0), (0, 0, 1), 0.04, 0.007, 0.006, "M_RuneGlow")
# thumb toggle on the left at the back
parts.append(rw.rounded_box("toggle_base", (0.016, 0.03, 0.02), 0.005, (0.045, 0.06, BZ + 0.02), mat="M_Steel",
                            segments=1))
parts.append(pl.capsule("toggle", (0.05, 0.06, BZ + 0.026), (0.058, 0.075, BZ + 0.046), 0.0055, 6, 2, "M_Copper"))

# --- dial screen on top, tilted toward the player -------------------------------------------------------------
SC = V((0, 0.03, BZ + 0.072))
tilt = V((0, 0.45, 1)).normalized()          # screen normal: up and back toward the player
parts.append(rw.rounded_box("screen_neck", (0.03, 0.03, 0.04), 0.008, tuple(SC - V((0, 0.01, 0.035))),
                            mat="M_Brass", segments=1))
housing = pl.lathe_axis("screen_housing", [(0.0, -0.016), (0.036, -0.016), (0.042, -0.008), (0.042, 0.008),
                                           (0.036, 0.012), (0.03, 0.012), (0.03, 0.004), (0.0, 0.004)], tilt, SC, 24,
                        "M_Brass", False, False, 45)
parts.append(housing)
parts.append(pl.disc("screen", 0.03, 0.006, tilt, SC + tilt * 0.004, SCREEN, 24, 0.1))
# display ink: a gauge arc of ticks and a needle
side_v = V((1, 0, 0))
up_v = tilt.cross(side_v).normalized() * -1
for k in range(5):
    a = math.radians(-60 + 30 * k)
    p = SC + tilt * 0.0075 + (side_v * math.sin(a) + up_v * math.cos(a)) * 0.022
    parts.append(pl.obox("tick", (0.0035, 0.008, 0.002), p, side_v * math.cos(a) - up_v * math.sin(a), tilt,
                         "ScreenInk"))
needle_dir = (side_v * math.sin(math.radians(25)) + up_v * math.cos(math.radians(25))).normalized()
parts.append(pl.obox("needle", (0.003, 0.02, 0.002), SC + tilt * 0.0078 + needle_dir * 0.009,
                     side_v.cross(tilt) * 0 + needle_dir.cross(tilt), tilt, "ScreenInk"))
parts.append(pl.disc("needle_hub", 0.004, 0.003, tilt, SC + tilt * 0.008, "ScreenInk", 8, 0.2))

# --- tuning fork: yoke + two tines + lens ring -------------------------------------------------------------------
yoke = pl.lathe_axis("yoke", [(0.0, 0.0), (0.036, 0.0), (0.04, 0.012), (0.03, 0.03), (0.0, 0.03)], (0, -1, 0),
                     (0, BY1 + 0.004, BZ), 16, "M_Brass", False, False, 45)
parts.append(yoke)
LENS_Y = -0.265
LR = 0.054                                 # lens ring radius
for s in (-1, 1):
    pts = [V((s * 0.018, BY1 - 0.02, BZ)), V((s * 0.058, BY1 - 0.05, BZ)), V((s * 0.07, LENS_Y + 0.055, BZ)),
           V((s * (LR + 0.006), LENS_Y + 0.006, BZ))]
    parts.append(pl.sausage("tine", pts, [0.017, 0.016, 0.014, 0.013], 8, 3, "M_Brass", (True, True), 2, True, 55,
                            scale_xy=(1.0, 0.8), up_hint=(0, 0, 1)))
    # little copper wraps on each tine
    parts.append(pl.band("tine_wrap", 0.021, 0.016, 0.01, (s * 0.15, -1, 0), V((s * 0.066, BY1 - 0.075, BZ)),
                         "M_Copper", 10, 0.0))
lens_ring = rw.torus("lens_ring", LR, 0.013, 24, 6, (0, LENS_Y, BZ), (90, 0, 0), mat="M_Brass")
parts.append(lens_ring)
# biconvex crystal lens + a small pointed tip crystal at the front
lens = [(0.0, -0.02), (0.024, -0.017), (0.042, -0.009), (LR - 0.004, 0.0), (0.042, 0.009), (0.024, 0.017),
        (0.0, 0.02)]
parts.append(pl.lathe_axis("lens", lens, (0, -1, 0), (0, LENS_Y, BZ), 20, "M_Crystal", False, False, 60))
TIP_Y = LENS_Y - 0.014 - 0.045
parts.append(pl.crystal("tip", V((0, LENS_Y - 0.014, BZ)), (0, -1, 0), 0.045, 0.013, 6, 0.5, 0.0, "M_Crystal"))
# a rune bead on top of the ring
parts.append(rw.sphere("bead", 0.013, 10, 5, (0, LENS_Y, BZ + LR + 0.016), mat="M_RuneGlow"))

# --- trigger guard + trigger --------------------------------------------------------------------------------------
guard = [(0, -0.095, BZ - 0.04), (0, -0.11, 0.04), (0, -0.095, 0.006), (0, -0.07, 0.0), (0, -0.055, 0.012)]
parts.append(pl.sausage("guard", guard, 0.0075, 8, 3, "M_Brass", (True, True), 2, True, 60))
parts.append(pl.capsule("trigger", (0, -0.075, BZ - 0.04), (0, -0.085, 0.05), 0.007, 8, 2, "M_Steel"))

tool = rw.join(parts, "Toolkit", origin=(0, 0, 0))
rw.smooth(tool, 45)

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Emitter", (0, TIP_Y, BZ))
pl.check("vm_toolkit", (0, 0, 0))
rw.finish("vm_toolkit", "weapons", icon=True)
