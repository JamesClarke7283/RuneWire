"""vm_gauntlet: first-person Grav Gauntlet (the armoured right hand itself).

The right hand is raised in an open "grabbing" pose: palm facing -Y (away from the player), fingers up
and slightly curled toward -Y, thumb out to the player's left (+X). Leather glove under brass/steel
armour: a riveted brass back plate, steel plates on every finger segment, brass fingertip caps, a
glowing teal crystal (M_Crystal) in a brass bezel in the palm, a brass bracer with steel bands and a
little teal power cell, three small rings around the wrist, then the shared blue sleeve.

Nodes (origin = palm centre, the hand's "grip centre"):
  Gauntlet  the whole armoured hand + bracer + sleeve (static).
  Emitter   empty just in front of the palm crystal.
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

LEATHER = glove.LEATHER
LEATHER_DARK = glove.LEATHER_DARK
parts = []

# --- palm + back plate -------------------------------------------------------------------------------------
PW, PT, PH = 0.12, 0.062, 0.115           # palm width (X), thickness (Y), height (Z)
parts.append(pl.superellipsoid("palm", (PW, PT, PH), (0, 0, 0), 0.5, 0.55, 18, 12, LEATHER))
plate = pl.superellipsoid("backplate", (PW * 0.92, 0.024, PH * 0.86), (0, PT / 2 - 0.002, 0.004), 0.4, 0.5, 16, 8,
                          "M_Brass")
parts.append(plate)
for (x, z) in ((-0.038, -0.034), (0.038, -0.034), (-0.038, 0.04), (0.038, 0.04)):
    parts.append(pl.rivet((x, PT / 2 + 0.008, z), (0, 1, 0), 0.008, 0.005, "M_Steel", 6))
# a gear emblem with a teal rune on the back plate
emb = rw.gear("emblem", 0.026, 8, 0.008, 0.006, 0.0, mat="M_Steel", bevel=0.0)
rw.apply_modifiers(emb)
pl.align(emb, (0, 1, 0), (0, PT / 2 + 0.0095, 0.004))
parts.append(emb)
parts.append(pl.disc("emblem_gem", 0.011, 0.006, (0, 1, 0), (0, PT / 2 + 0.013, 0.004), "M_Crystal", 10, 0.4))

# --- fingers -------------------------------------------------------------------------------------------------
# (x at the base, splay in degrees (+ toward +X), length scale, radius)
FINGERS = ((0.04, 9, 0.94, 0.0195), (0.0135, 3, 1.0, 0.0205), (-0.013, -3, 0.96, 0.0198), (-0.039, -10, 0.82, 0.0178))
SEGS = (0.042, 0.032, 0.026)
CURL = (18, 44, 70)                       # cumulative bend toward -Y per segment (degrees from vertical)
for (x0, splay, ls, r) in FINGERS:
    p = V((x0, -0.004, PH / 2 - 0.012))
    pts = [p.copy()]
    joints = []
    sp = math.radians(splay)
    for seg, curl in zip(SEGS, CURL):
        c = math.radians(curl)
        d = V((math.sin(sp) * math.cos(c), -math.sin(c), math.cos(sp) * math.cos(c)))
        p = p + d * seg * ls
        pts.append(p.copy())
        joints.append(d)
    parts.append(pl.sausage("finger", pts, [r, r * 0.97, r * 0.93, r * 0.88], 8, 2, LEATHER, (True, True), 2, True,
                            70))
    # steel plates over the back of the first two segments, brass cap on the tip
    for k in range(2):
        a, b = pts[k], pts[k + 1]
        d = (b - a).normalized()
        back = V((0, 1, 0))
        back = (back - back.dot(d) * d).normalized()
        c = (a + b) / 2 + back * (r * 0.62)
        parts.append(pl.obox("fplate", ((b - a).length * 0.82, r * 2.1, r * 0.75), c, d, back, "M_Steel",
                             rounded=r * 0.35, segments=1))
    tip_d = joints[-1]
    parts.append(pl.lathe_axis("tipcap", [(r * 1.04, -0.012), (r * 1.06, 0.002), (r * 0.8, r * 0.75), (0.0, r * 1.06)],
                               tip_d, pts[-1], 10, "M_Brass", False, False, 60))
    # knuckle stud on the back
    parts.append(pl.rivet(pts[0] + V((0, r * 0.95 + 0.006, -0.004)), (0, 1, 0.3), 0.009, 0.006, "M_Brass", 6))

# --- thumb: out to +X, curling forward ------------------------------------------------------------------------------
tpts = [V((0.04, -0.006, -0.03)), V((0.068, -0.018, -0.01)), V((0.088, -0.038, 0.014)), V((0.094, -0.06, 0.034))]
parts.append(pl.sausage("thumb", tpts, [0.028, 0.025, 0.022, 0.02], 8, 3, LEATHER, (True, True), 2, True, 70))
td = (tpts[2] - tpts[1]).normalized()
parts.append(pl.obox("tplate", (0.032, 0.04, 0.014), (tpts[1] + tpts[2]) / 2 + V((0.006, 0.014, 0.0)), td,
                     V((0.35, 1, -0.2)).normalized(), "M_Steel", rounded=0.006, segments=1))
parts.append(pl.lathe_axis("thumbcap", [(0.021, -0.012), (0.0215, 0.002), (0.016, 0.014), (0.0, 0.02)],
                           (tpts[3] - tpts[2]).normalized(), tpts[3], 10, "M_Brass", False, False, 60))

# --- palm crystal in a brass bezel, facing -Y ------------------------------------------------------------------------
PC = V((0, -PT / 2 + 0.006, -0.004))
parts.append(pl.lathe_axis("bezel", [(0.03, -0.004), (0.036, 0.0), (0.036, 0.008), (0.03, 0.013), (0.024, 0.009),
                                     (0.024, -0.004)], (0, -1, 0), PC, 20, "M_Brass", False, False, 45))
for k in range(4):
    a = math.radians(45 + 90 * k)
    parts.append(pl.rivet(PC + V((math.cos(a) * 0.031, -0.012, math.sin(a) * 0.031)), (0, -1, 0), 0.0055, 0.004,
                          "M_Steel", 6))
gem = [(0.0, -0.004), (0.026, -0.002), (0.026, 0.008), (0.015, 0.02), (0.0, 0.024)]
parts.append(pl.lathe_axis("gem", gem, (0, -1, 0), PC, 8, "M_Crystal", False, False, 20, 22.5))
GEM_TIP = PC + V((0, -0.024, 0))

# --- wrist, rings, bracer --------------------------------------------------------------------------------------------
F = V((0, 1, -0.55)).normalized()
W0 = V((0, 0.006, -PH / 2 + 0.01))
W1 = W0 + F * 0.05
parts.append(pl.sausage("wrist", [W0, W1], [0.043, 0.041], 12, 1, LEATHER, (True, False), 2, False, 60))
for k, t in enumerate((0.012, 0.03, 0.048)):
    ring = rw.torus("wristring", 0.047 - 0.0005 * k, 0.0055, 20, 5, (0, 0, 0), mat="M_Brass")
    pl.align(ring, F, W0 + F * t)
    parts.append(ring)
B0 = W1 - F * 0.004
BL = 0.11
bracer = [(0.046, 0.0), (0.05, 0.004), (0.054, 0.02), (0.058, BL - 0.02), (0.06, BL - 0.006), (0.056, BL),
          (0.05, BL)]
parts.append(pl.lathe_axis("bracer", bracer, F, B0, 22, "M_Brass", False, False, 40))
for t in (0.022, BL - 0.024):
    parts.append(pl.band("bracer_band", 0.06, 0.014, 0.01, F, B0 + F * t, "M_Steel", 22, 0.0))
# teal power-cell window on the left (+X, facing the player) side of the bracer
side = V((1, 0, 0))
cell_c = B0 + F * (BL / 2) + side * 0.056
parts.append(pl.lathe_axis("cell_bezel", [(0.024, -0.006), (0.024, 0.006), (0.019, 0.011), (0.015, 0.008),
                                          (0.015, -0.006)], side, cell_c, 16, "M_Steel", False, False, 45))
parts.append(pl.lathe_axis("cell", [(0.0, -0.004), (0.016, -0.004), (0.016, 0.004), (0.01, 0.012), (0.0, 0.014)],
                           side, cell_c, 12, "M_Crystal", False, False, 50))
# rivets around the bracer
up = F.cross(side).normalized()
for k in range(6):
    a = math.radians(60 * k + 30)
    d = (side * math.cos(a) + up * math.sin(a)).normalized()
    if d.dot(side) > 0.8:
        continue
    parts.append(pl.rivet(B0 + F * (BL / 2) + d * 0.057, d, 0.0075, 0.005, "M_Steel", 6))

# --- the shared blue sleeve -------------------------------------------------------------------------------------------
parts += glove.sleeve(B0 + F * (BL - 0.004), F, (-1, 0, 0), 1.05, 0.03, True, flare=False)

g = rw.join(parts, "Gauntlet", origin=(0, 0, 0))
# chunky cartoon scale: the gauntlet is the whole item, so make it a bit bigger than a plain glove
SCALE = 1.15
g.data.transform(pl.Matrix.Scale(SCALE, 4))
g.data.update()
rw.smooth(g, 55)

rw.empty("Emitter", tuple((GEM_TIP + V((0, -0.045, 0))) * SCALE))
pl.check("vm_gauntlet", (0, 0, 0))
rw.finish("vm_gauntlet", "weapons", icon=True)
