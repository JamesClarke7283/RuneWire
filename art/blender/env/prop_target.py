"""prop_target: a pop-up range target (1.6 x 0.4 x 2.2 m) for the Target Range challenge.

A round painted target (white / red rings and a raised gold bullseye) on a wooden backing disc, radius 0.75 and
centred 1.45 m up, facing -Y, held in a riveted brass frame ring. Two brass uprights and a centre strut carry it on a
big steel-and-brass hinge whose barrel (radius 7 cm) lies along X on the ground right over the origin, with a bolted
ground plate and a fat copper return spring BEHIND the hinge (+Y).

The game adds a disc-shaped hit collider (radius 0.75 at 1.45 m, facing -Y) and tips the WHOLE model back about its
origin (rotation about X to -1.4 rad) when the target is down: then the top swings to +Y and everything behind the
hinge (ground plate, spring foot) sinks below the ground, while nothing sits in front of the hinge at ground level.

Origin at the ground centre, under the hinge barrel (so the tip-back pivots at the hinge's foot). Collision: one box
around the stand below the disc only (the game's own collider covers the disc, so shots aren't stopped by the
stand's proxy).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_target"
PL.reset()
P = []
CZ = 1.45                 # disc centre height
R = 0.75                  # disc radius
YF = -0.1                 # front face of the painted disc
HZ = 0.07                 # hinge barrel axis height (radius 0.07: the barrel touches the ground)
AXX = (1, 0, 0)

# ---------------------------------------------------------------- the painted disc (lathe along -Y)
prof = [(0.0, 0.0), (R - 0.02, 0.0), (R, 0.02), (R, 0.075), (R - 0.01, 0.08)]
for r in (0.6, 0.45, 0.3, 0.16):
    prof += [(r + 0.006, 0.08), (r - 0.006, 0.08)]
prof += [(0.15, 0.09), (0.13, 0.11), (0.08, 0.125), (0.0, 0.128)]
disc = PL.lathe_ax("disc", prof, (0, -1, 0), (0, YF + 0.08, CZ), 32, "M_WoodPlanks", 35, False, False)


def band(c, n):
    r = math.hypot(c.x, c.z - CZ)
    if c.y > YF + 0.005:
        return None
    if r < 0.155:
        return "Gold"
    if n.y > -0.5:
        return None
    for (lo, hi, m) in ((0.155, 0.3, "TargetRed"), (0.3, 0.45, "TargetWhite"), (0.45, 0.6, "TargetRed"),
                        (0.6, R + 0.01, "TargetWhite")):
        if lo <= r < hi:
            return m
    return None


for m in ("Gold", "TargetRed", "TargetWhite"):
    rw.set_mat_where(disc, M(m), lambda c, n, m=m: band(c, n) == m)
P.append(disc)

# ---------------------------------------------------------------- brass frame ring, rivets, back bracing
P.append(E.ring("frame", R + 0.01, 0.034, (0, YF + 0.045, CZ), (0, 1, 0), "M_Brass", 32, 6))
for i in range(8):
    a = math.radians(22.5 + 45 * i)
    P.append(PL.rivet(((R + 0.01) * math.cos(a), YF + 0.045 - 0.03, CZ + (R + 0.01) * math.sin(a)), (0, -1, 0), 0.026,
                      0.016, "M_Brass", 6))
for a in (45, -45):
    P.append(PL.obox("brace", (2 * R - 0.08, 0.1, 0.05), (0, YF + 0.105, CZ), (math.cos(math.radians(a)), 0,
                                                                             math.sin(math.radians(a))), (0, 1, 0),
                     "M_WoodDark", 0.015))
P.append(PL.lathe_ax("hub", [(0.0, 0.0), (0.13, 0.0), (0.13, 0.03), (0.09, 0.06), (0.0, 0.06)], (0, 1, 0),
                     (0, YF + 0.13, CZ), 12, "M_Brass", 40, False, False))

# ---------------------------------------------------------------- uprights and centre strut down to the hinge
UY = YF + 0.11
for sx in (-1, 1):
    top = V((sx * (R + 0.005), UY, CZ))
    foot = V((sx * 0.21, UY, HZ + 0.05))
    P.append(PL.sausage("upright", [foot, foot.lerp(top, 0.5) + V((sx * 0.05, 0, 0)), top], 0.038, 8, 3, "M_Brass",
                        (True, True), 2))
    P.append(rw.sphere("joint", 0.045, 8, 6, tuple(top), (0, 0, 0), (1, 1, 1), PL.mat("M_Brass")))
P.append(PL.obox("strut", (CZ - R - HZ, 0.1, 0.06), (0, UY, (HZ + CZ - R) / 2 + 0.02), (0, 0, 1), (0, 1, 0), "M_Brass",
                 0.02))
P.append(PL.obox("crossbar", (0.8, 0.07, 0.09), (0, UY, 0.5), (1, 0, 0), (0, 0, 1), "M_Brass", 0.02))
for sx in (-1, 1, 0):
    P.append(PL.rivet((sx * 0.33, UY - 0.035, 0.5), (0, -1, 0), 0.022, 0.012, "M_Steel", 6))

# ---------------------------------------------------------------- the hinge: knuckles along X on the origin
KN = [(-0.52, -0.33, "M_Steel"), (-0.31, -0.11, "M_Brass"), (-0.09, 0.09, "M_Steel"), (0.11, 0.31, "M_Brass"),
      (0.33, 0.52, "M_Steel")]
for (x0, x1, m) in KN:
    L = x1 - x0
    P.append(PL.lathe_ax("knuckle", [(0.0, 0.0), (0.06, 0.0), (0.07, 0.012), (0.07, L - 0.012), (0.06, L), (0.0, L)],
                         AXX, (x0, 0, HZ), 14, m, 40, False, False))
    # leaves: the brass knuckles carry the target (up into the uprights), the steel ones hold the ground plate
    if m == "M_Brass":
        P.append(PL.obox("leaf", (L - 0.02, 0.05, 0.16), ((x0 + x1) / 2, UY * 0.6, HZ + 0.08), (1, 0, 0), (0, 0, 1),
                         "M_Brass", 0.012))
    else:
        P.append(PL.obox("leaf", (L - 0.02, 0.2, 0.035), ((x0 + x1) / 2, 0.1, 0.0175), (1, 0, 0), (0, 0, 1), "M_Steel",
                         0.01))
for sx in (-1, 1):
    P.append(PL.lathe_ax("pincap", [(0.0, 0.0), (0.05, 0.0), (0.045, 0.025), (0.0, 0.035)], (sx, 0, 0),
                         (sx * 0.525, 0, HZ), 10, "M_Brass", 50, False, False))
# the bolted ground plate behind the hinge, and the return spring
P.append(PL.obox("plate", (1.06, 0.2, 0.04), (0, 0.17, 0.02), (1, 0, 0), (0, 0, 1), "M_DarkMetal", 0.012))
for sx in (-1, 1):
    for yy in (0.12, 0.22):
        P.append(PL.rivet((sx * 0.46, yy, 0.04), (0, 0, 1), 0.024, 0.014, "M_Steel", 6))
spring_foot = V((0.0, 0.2, 0.04))
spring_top = V((0.0, UY + 0.05, 0.62))
d = (spring_top - spring_foot)
pts = []
turns, rr = 5, 0.055
side = d.normalized().cross(V((1, 0, 0))).normalized()
for i in range(turns * 6 + 1):
    t = i / (turns * 6)
    a = 2 * math.pi * turns * t
    pts.append(spring_foot + d * t + V((rr * math.cos(a), 0, 0)) + side * (rr * math.sin(a)))
P.append(PL.sausage("spring", pts, 0.017, 6, 1, "M_Copper", (True, True), 2, smooth_path=False))
P.append(PL.obox("springcap", (0.12, 0.06, 0.04), tuple(spring_foot + V((0, 0, 0.0))), (1, 0, 0), (0, 0, 1),
                 "M_Brass", 0.01))
P.append(PL.obox("springcap", (0.12, 0.05, 0.05), tuple(spring_top), (1, 0, 0), tuple(-d.normalized()), "M_Brass", 0.01))

E.tri_breakdown(P, 16)
E.join(P, "Target")

# ---------------------------------------------------------------- collision: the stand below the disc only
E.col_box("Stand", (1.12, 0.36, CZ - R - 0.05), (0, 0.05, (CZ - R - 0.05) / 2))

PL.finish(ASSET, (1.6, 0.4, 2.2), 4000, origin_note="(origin = ground under the hinge barrel)")
PL.qa(ASSET, ("side", "front"))
