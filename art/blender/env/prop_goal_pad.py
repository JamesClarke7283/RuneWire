"""prop_goal_pad: a cargo delivery pad (diameter 8 x 0.3 m) for the Gorge Haul and the watchtower delivery.

A low round stone platform (M_Stone) with a sloped rim, a brass trim band and a ring of twelve dressed stone slabs
around a dark slate deck. Two glowing teal rings mark the zone, four big glowing arrows point in to a central glowing
crate mark (a gold square with brass corner brackets around a teal eye rune) where the cargo goes, and four teal runes
sit between the arrows. Low brass studs ring the slabs. Everything is under 0.3 m and sloped at the rim, so
contraptions can drive straight onto it. The game also places it at 0.6 and 0.75 scale.

Origin at the ground centre. Collision: one thin, low convex disc (0.27 m tall, its rim chamfered like the stone) for
walking and driving over.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_goal_pad"
PL.reset()
P = []
R = 4.0
ZD = 0.24                 # deck height
ZI = ZD + 0.012           # inlay height (just above the deck)

# ---------------------------------------------------------------- base: sloped rim with a brass band, slabs, deck
base = E.lathe("base", [(R - 0.02, 0.0), (R, 0.02), (R, 0.09), (R - 0.18, ZD - 0.01), (R - 0.4, ZD), (0.0, ZD)],
               40, m="M_Stone", smooth=30, cap_bottom=False)
rw.set_mat_where(base, PL.mat("M_Brass"), lambda c, n: c.z < 0.095 and abs(n.z) < 0.3)
P.append(base)
for i in range(12):
    th0 = i * 30.0 + 0.6
    th1 = (i + 1) * 30.0 - 0.6
    blk = E.arc_block("slab", (0, 0), R - 0.75, R - 0.2, th0, th1, ZD - 0.03, ZD + 0.03, nu=3, m="M_Stone")
    rw.add_bevel(blk, 0.025, 1, 30, harden=False)
    rw.smooth(blk, 30)
    P.append(blk)
P.append(PL.flat_disc("deck", R - 0.74, (0, 0, ZD + 0.004), 32, "M_DarkMetal__5a6a7a"))
for i in range(12):
    a = math.radians(i * 30.0 + 15.0)
    d = V((math.cos(a), math.sin(a), 0))
    P.append(PL.lathe_ax("stud", [(0.0, 0.0), (0.09, 0.0), (0.075, 0.04), (0.0, 0.05)], (0, 0, 1),
                         tuple(d * (R - 0.47) + V((0, 0, ZD + 0.02))), 8, "M_Brass", 40, False, False))

# ---------------------------------------------------------------- glowing zone rings, runes, arrows
P.append(PL.flat_ring("zonering", R - 1.02, R - 0.86, (0, 0, ZI), 48, "TealGlow"))
P.append(PL.flat_ring("zonering", 1.12, 1.24, (0, 0, ZI), 32, "TealGlow"))
KEYS = ("algiz", "sowilo", "ingwaz", "othala")
for i in range(4):
    a = math.radians(45 + 90 * i)
    rd = V((math.cos(a), math.sin(a), 0))
    tg = V((-math.sin(a), math.cos(a), 0))
    P += PL.glyph(KEYS[i], rd * 2.12 + V((0, 0, ZI)), tg, rd, 0.62, 0.12, 0.03, "TealGlowSoft")
ARROW = [(0.0, 0.0), (0.58, 0.52), (0.26, 0.52), (0.26, 1.2), (-0.26, 1.2), (-0.26, 0.52), (-0.58, 0.52)]
for i in range(4):
    a = math.radians(90 * i)
    rd = V((math.cos(a), math.sin(a), 0))
    tg = V((-math.sin(a), math.cos(a), 0))
    o = E.poly_prism("arrow", ARROW, 0.03, (0, 0, 0), (0, 0, 0), "TealGlow")
    PL.place_rel([o], rd * 1.42 + V((0, 0, ZI)), tg, rd, (0, 0, 1))      # local y runs outward from the tip
    P.append(o)

# ---------------------------------------------------------------- the crate mark in the middle
for s in (-1, 1):
    P.append(PL.obox("mark", (1.12, 0.11, 0.03), (0, s * 0.62, ZI), (1, 0, 0), (0, 0, 1), "GoldGlow"))
    P.append(PL.obox("mark", (1.12, 0.11, 0.03), (s * 0.62, 0, ZI), (0, 1, 0), (0, 0, 1), "GoldGlow"))
for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    c = V((sx * 0.64, sy * 0.64, ZI + 0.012))
    P.append(rw.box("bracket", (0.3, 0.1, 0.05), tuple(c + V((-sx * 0.1, 0, 0))), mat=PL.mat("M_Brass")))
    P.append(rw.box("bracket", (0.1, 0.3, 0.05), tuple(c + V((0, -sy * 0.1, 0))), mat=PL.mat("M_Brass")))
P += PL.glyph("eye", (0, 0, ZI), (1, 0, 0), (0, 1, 0), 0.8, 0.1, 0.03, "TealGlow")

E.tri_breakdown(P, 16)
E.join(P, "GoalPad")

# ---------------------------------------------------------------- collision: a thin, low disc with a chamfered rim
E.col_frustum("Pad", R, R - 0.3, ZD + 0.03, (0, 0, (ZD + 0.03) / 2), verts=16)

PL.finish(ASSET, (8.0, 8.0, 0.3), 3000)
PL.qa(ASSET, ("top",))
