"""prop_bridge: an arched wooden bridge / pier with rails (12 x 4 x 2 m), the little pier on the lake's east shore.

The deck runs along X and rises in a gentle arch (0.35 m at the ends to 0.85 m at the crown, top of the planks).
Twenty-four cross planks (M_WoodPlanks, slightly varied, iron nails) lie on two curved stringers (M_WoodDark) that
rest on a bark sill log at each end and on two strapped pile bents with knee braces in the middle. Both sides get a
chunky rail: five posts with brass caps, a curved handrail and a plank brace in each bay, with a brass lantern on
two diagonal end posts (LightPoint_0 / LightPoint_1), a mooring ring and a coil of rope. The front faces -Y.

The game places it at the lake shore, yawed 90 degrees and lowered 0.6 m, so the end piles stand in the water.

Origin at the ground centre. Collision: the deck as eight box segments following the arch (walkable), plus a thin box
for each rail.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_bridge"
PL.reset()
rnd = random.Random(9)
P = []
L = 6.0                   # half length along X
Z_END, Z_TOP = 0.35, 0.85
PT = 0.09                 # plank thickness
DW = 1.7                  # deck half width (planks)
RY = 1.82                 # rail centre-line y


def deck_z(x):
    """Top of the planks at x (a circular-ish arch)."""
    t = x / L
    return Z_END + (Z_TOP - Z_END) * (1 - t * t)


def deck_slope(x):
    return -2 * (Z_TOP - Z_END) * x / (L * L)


# ---------------------------------------------------------------- planks
NP = 24
pw = 2 * L / NP
for i in range(NP):
    x = -L + pw * (i + 0.5)
    ang = math.degrees(math.atan(deck_slope(x)))
    w = DW * 2 + rnd.uniform(-0.06, 0.04)
    yo = rnd.uniform(-0.04, 0.04)
    P.append(E.cbox("plank", (pw - 0.035, w, PT), (x, yo, deck_z(x) - PT / 2), (0, -ang + rnd.uniform(-0.8, 0.8),
                                                                                 rnd.uniform(-1.2, 1.2)),
                    "M_WoodPlanks", 0.015))
    # nail heads over the stringers on every other plank
    if i % 2 == 0:
        for sy in (-1, 1):
            P.append(rw.box("nail", (0.04, 0.04, 0.02), (x, sy * 1.2 + yo, deck_z(x) + 0.004), (0, -ang, 45),
                            PL.mat("Iron")))

# ---------------------------------------------------------------- stringers (curved beams under the planks)
for sy in (-1, 1):
    pts = [(x, sy * 1.2, deck_z(x) - PT - 0.12) for x in [-L + 0.05 + (2 * L - 0.1) * k / 8 for k in range(9)]]
    P.append(PL.sausage("stringer", pts, 0.13, 6, 1, "M_WoodDark", (False, False), 1, smooth_path=True,
                        scale_xy=(1.0, 0.75), up_hint=(0, 0, 1)))

# ---------------------------------------------------------------- supports: sill logs at the ends, piles in the middle
for sx in (-1, 1):
    x = sx * (L - 0.45)
    P.append(PL.lathe_ax("sill", [(0.0, -1.85), (0.17, -1.85), (0.2, -1.8), (0.2, 1.8), (0.17, 1.85), (0.0, 1.85)],
                         (0, 1, 0), (x, 0, deck_z(x) - PT - 0.27), 10, "M_Bark", 40, False, False))
    for sy in (-1, 1):
        P.append(PL.lathe_ax("endgrain", [(0.0, 0.0), (0.15, 0.0), (0.0, 0.01)], (0, sy, 0),
                             (x, sy * 1.85, deck_z(x) - PT - 0.27), 10, "M_WoodPlanks", 40, False, False))
for x in (-2.4, 2.4):
    zt = deck_z(x) - PT - 0.25
    for sy in (-1, 1):
        y = sy * 1.2
        P.append(E.lathe("pile", [(0.0, -0.1), (0.19, -0.1), (0.18, zt - 0.02), (0.0, zt - 0.02)], 10,
                         loc=(x, y, 0), m="M_WoodDark", smooth=40))
        P.append(PL.hoop("strap", 0.17, 0.205, 0.07, (0, 0, 1), (x, y, zt * 0.45), 10, "Iron", 0.0))
    P.append(E.rbox("crossbeam", (0.26, 2.9, 0.2), (x, 0, zt + 0.02), m="M_WoodDark", r=0.03))
    for sy in (-1, 1):
        P.append(PL.rivet((x - 0.135, sy * 1.2, zt + 0.02), (-1, 0, 0), 0.032, 0.018, "M_Brass", 6))
    # knee braces from the piles up to the stringers
    for sx in (-1, 1):
        for sy in (-1, 1):
            p0 = V((x, sy * 1.2, zt * 0.35))
            p1 = V((x + sx * 0.75, sy * 1.2, deck_z(x + sx * 0.75) - PT - 0.2))
            P.append(E.beam("knee", tuple(p0), tuple(p1), 0.09, 0.08, "M_WoodDark", 0.02, up=(0, sy, 0)))

# ---------------------------------------------------------------- rails: chunky posts, handrail, plank braces
POSTS = (-L + 0.18, -2.9, 0.0, 2.9, L - 0.18)
RH = 0.95                 # handrail height above the deck
for sy in (-1, 1):
    y = sy * RY
    for x in POSTS:
        zb = deck_z(x) - PT - 0.22
        zt = deck_z(x) + RH + 0.06
        P.append(E.rbox("post", (0.21, 0.21, zt - zb), (x, y, (zb + zt) / 2), m="M_WoodDark", r=0.04))
        P.append(PL.lathe_ax("postcap", [(0.0, 0.0), (0.15, 0.0), (0.15, 0.035), (0.1, 0.08), (0.0, 0.1)],
                             (0, 0, 1), (x, y, zt), 8, "M_Brass", 40, False, False, spin=22.5))
        P.append(rw.box("bolt", (0.05, 0.03, 0.05), (x, y - sy * 0.11, deck_z(x) - 0.06), mat=PL.mat("Iron")))
    hand = [(x, y, deck_z(x) + RH) for x in [-L + 0.18 + (2 * L - 0.36) * k / 8 for k in range(9)]]
    P.append(PL.sausage("handrail", hand, 0.085, 6, 1, "M_WoodPlanks", (True, True), 2, smooth_path=True,
                        scale_xy=(0.85, 1.0), up_hint=(0, 0, 1)))
    # a chunky plank brace in each bay, alternating directions
    for k, (x0, x1) in enumerate(zip(POSTS[:-1], POSTS[1:])):
        xa, xb = (x0 + 0.12, x1 - 0.12) if k % 2 == 0 else (x1 - 0.12, x0 + 0.12)
        p0 = V((xa, y, deck_z(xa) + 0.08))
        p1 = V((xb, y, deck_z(xb) + RH - 0.1))
        P.append(E.beam("railbrace", tuple(p0), tuple(p1), 0.07, 0.15, "M_WoodPlanks", 0.02, up=(0, sy, 0)))

# ---------------------------------------------------------------- lanterns on the end posts (diagonal corners)
LP = []
for (x, sy) in ((-L + 0.18, -1), (L - 0.18, 1)):
    top = V((x, sy * RY, deck_z(x) + RH + 0.16))
    parts, c = E.lantern(tuple(top), "post", scale=0.9)
    P += parts
    LP.append(c)
# a mooring ring on the -X end post and a coil of rope by it
P.append(E.ring("mooring", 0.11, 0.025, (-L + 0.18, -RY - 0.12, deck_z(-L) + 0.4), (0, 1, 0), "M_Brass", 12, 5))
cx, cy = -L + 0.85, -1.25
for k, r in enumerate((0.26, 0.19, 0.12)):
    P.append(E.ring("coil", r, 0.04, (cx, cy, deck_z(cx) + 0.04 + 0.06 * k), (0, 0, 1), "Rope", 14, 5))

E.tri_breakdown(P, 18)
E.join(P, "Bridge")
for i, c in enumerate(LP):
    rw.empty("LightPoint_%d" % i, c)

# ---------------------------------------------------------------- collision: deck segments following the arch, rails
NS = 8
for k in range(NS):
    x0 = -L + 2 * L * k / NS
    x1 = x0 + 2 * L / NS
    p0 = (x0, 0, deck_z(x0) - 0.11)
    p1 = (x1, 0, deck_z(x1) - 0.11)
    E.col_beam("Deck", p0, p1, 2 * RY + 0.1, 0.22, extend=0.04)
for sy in (-1, 1):
    for k in range(4):
        x0 = -L + 2 * L * k / 4
        x1 = x0 + 2 * L / 4
        E.col_beam("Rail", (x0, sy * RY, deck_z(x0) + 0.5), (x1, sy * RY, deck_z(x1) + 0.5), 0.2, 1.0, extend=0.02)

PL.finish(ASSET, (12.0, 4.0, 2.0), 8000)
PL.qa(ASSET, ("front", "side"))
