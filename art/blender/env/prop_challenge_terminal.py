"""prop_challenge_terminal: the console that starts a challenge and shows its medals (1.2 x 1.2 x 1.6 m).

An octagonal stone plinth with a brass trim, a dark-iron pedestal with brass collars, and a slanted brass console
facing -Y: a glowing teal display behind a brass bezel, a big glowing crystal start button (M_Crystal) in a riveted
bezel, two toggle switches, a little pressure gauge and a red-knobbed lever on the side. A brass medal board rises
from the back edge with bronze, silver and gold medals on ribbons, so the player can tell what it is from afar.

Origin at the ground centre; the console faces -Y. No collision: the game adds its own 1.4 x 1.8 x 1.4 box (and a
light at 1.8 m).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "prop_challenge_terminal"
PL.reset()
P = []
C8 = math.cos(math.radians(22.5))

# ---------------------------------------------------------------- plinth and pedestal
P.append(E.lathe("plinth", [(0.0, 0.0), (0.575 / C8, 0.0), (0.575 / C8, 0.15), (0.55 / C8, 0.19), (0.46 / C8, 0.21),
                            (0.46 / C8, 0.27), (0.0, 0.27)], 8, m="M_Stone", smooth=0, rot=(0, 0, 22.5)))
P.append(E.lathe("trim", [(0.57 / C8, 0.1), (0.59 / C8, 0.11), (0.59 / C8, 0.14), (0.57 / C8, 0.15)], 8,
                 m="M_Brass", smooth=0, rot=(0, 0, 22.5), cap_bottom=False, cap_top=False))
for k in range(8):
    a = math.radians(45 * k)
    P.append(PL.rivet((0.59 * math.cos(a), 0.59 * math.sin(a), 0.125), (math.cos(a), math.sin(a), 0), 0.02, 0.01,
                      "M_Copper", 6))
P.append(E.lathe("pedestal", [(0.36, 0.26), (0.36, 0.32), (0.3, 0.38), (0.25, 0.46), (0.22, 0.85), (0.27, 0.92),
                              (0.33, 0.98), (0.0, 0.98)], 14, m="M_DarkMetal", smooth=40, cap_bottom=False))
P.append(E.ring("collar", 0.255, 0.03, (0, 0, 0.46), (0, 0, 1), "M_Brass", 16, 5))
P.append(E.ring("collar", 0.235, 0.028, (0, 0, 0.84), (0, 0, 1), "M_Brass", 16, 5))

# ---------------------------------------------------------------- slanted console housing (panel frame u, v, w)
TILT = math.radians(28)
U = V((1, 0, 0))
W = V((0, -math.sin(TILT), math.cos(TILT)))          # panel normal: up and toward the front
Vv = W.cross(U)                                      # up the slope (back and up)
CC = V((0, 0.04, 1.06))                              # housing centre
HD = 0.13                                            # half thickness of the housing


def pp(u, v, w=0.0):
    """Point on the panel: u across, v up the slope, w out of the top face."""
    return CC + U * u + Vv * v + W * (HD + w)


P.append(PL.obox("console", (1.02, 0.66, 2 * HD), tuple(CC), tuple(U), tuple(W), "M_Brass", 0.05, 2))
P.append(PL.obox("panel", (0.9, 0.54, 0.03), tuple(pp(0, 0.0, -0.005)), tuple(U), tuple(W), "M_DarkMetal", 0.012))
for (u, v) in ((-0.47, -0.29), (0.47, -0.29), (-0.47, 0.29), (0.47, 0.29)):
    P.append(PL.rivet(tuple(pp(u, v, 0.0)), tuple(W), 0.024, 0.014, "M_Copper", 6))
# display
P.append(PL.obox("bezel", (0.46, 0.3, 0.04), tuple(pp(-0.16, 0.06, 0.02)), tuple(U), tuple(W), "M_Brass", 0.015))
P.append(PL.obox("screen", (0.38, 0.22, 0.02), tuple(pp(-0.16, 0.06, 0.035)), tuple(U), tuple(W), "ScreenGlow", 0.0))
P += PL.glyph("star", pp(-0.16, 0.06, 0.045), U, Vv, 0.15, 0.022, 0.01, "TealGlow", "screenrune")
for i in range(3):
    P.append(PL.obox("bar", (0.04, 0.03 + 0.03 * i, 0.012), tuple(pp(-0.3 + 0.04 * i, 0.02 + 0.015 * i - 0.06, 0.045)),
                     tuple(U), tuple(W), "TealGlow", 0.0))
# the big crystal start button
bc = pp(0.25, 0.04, 0.0)
P.append(PL.lathe_ax("btnbezel", [(0.0, 0.0), (0.15, 0.0), (0.155, 0.03), (0.13, 0.05), (0.11, 0.035), (0.0, 0.035)],
                     tuple(W), tuple(bc), 16, "M_Brass", 40, False, False))
P.append(PL.lathe_ax("button", [(0.0, 0.0), (0.105, 0.0), (0.1, 0.04), (0.075, 0.075), (0.04, 0.095), (0.0, 0.1)],
                     tuple(W), tuple(bc + W * 0.03), 12, "M_Crystal", 30, False, False))
P += PL.rivet_circle(bc + W * 0.03, tuple(W), 0.135, 6, 0.014, 0.01, "M_Copper", 15.0, face=True)
# toggles and gauge on the lower lip
for i, x in enumerate((-0.3, -0.18)):
    b = pp(x, -0.2, 0.0)
    P.append(PL.lathe_ax("tbase", [(0.0, 0.0), (0.035, 0.0), (0.03, 0.02), (0.0, 0.02)], tuple(W), tuple(b), 8, "M_Steel",
                         40, False, False))
    tip = b + W * 0.08 + Vv * (0.03 if i else -0.03)
    P.append(PL.sausage("toggle", [b + W * 0.015, tip], 0.01, 6, 1, "M_Steel", (False, True), 2))
    P.append(rw.sphere("tknob", 0.022, 8, 6, tuple(tip), (0, 0, 0), (1, 1, 1), M("PaintRed" if i else "PaintCream")))
P += E.gauge(tuple(pp(0.05, -0.19, 0.03)), tuple(W), 0.075, 40.0)
# side lever
lp = CC + U * 0.505 + Vv * 0.0
P.append(PL.lathe_ax("pivot", [(0.0, 0.0), (0.06, 0.0), (0.06, 0.03), (0.04, 0.045), (0.0, 0.045)], (1, 0, 0), tuple(lp),
                     12, "M_Brass", 40, False, False))
lt = lp + V((0.04, -0.12, 0.24))
P.append(PL.sausage("lever", [lp + V((0.035, 0, 0)), lt], 0.018, 6, 1, "M_Steel", (False, False), 2))
P.append(rw.sphere("leverknob", 0.045, 10, 7, tuple(lt), (0, 0, 0), (1, 1, 1), M("PaintRed")))

# the housing's back face (+v side): a glowing ley stripe and a row of rivets
bc0 = CC + Vv * 0.33
P.append(PL.obox("backstripe", (0.86, 0.035, 0.02), tuple(bc0 + Vv * 0.006), tuple(U), tuple(Vv), "TealGlowSoft"))
for u in (-0.4, -0.2, 0.0, 0.2, 0.4):
    P.append(PL.rivet(tuple(bc0 + Vv * 0.004 + W * 0.075 + U * u), tuple(Vv), 0.018, 0.01, "M_Copper", 6))

# ---------------------------------------------------------------- medal board on the back edge
mb = pp(0.0, 0.33, 0.0) + V((0, 0.04, 0.0))
board = PL.obox("board", (0.74, 0.27, 0.05), tuple(mb + V((0, 0.0, 0.1))), (1, 0, 0), (0, -1, 0), "M_Brass", 0.025, 2)
P.append(board)
P.append(PL.obox("boardface", (0.64, 0.2, 0.02), tuple(mb + V((0, -0.025, 0.1))), (1, 0, 0), (0, -1, 0),
                 "M_DarkMetal", 0.008))
for i, (m, rib) in enumerate((("Bronze", "PaintRed"), ("Silver", "PaintBlue"), ("Gold", "PaintTeal"))):
    x = -0.2 + 0.2 * i
    c = mb + V((x, -0.04, 0.075))
    for sx in (-1, 1):
        P.append(PL.obox("ribbon", (0.1, 0.045, 0.012), tuple(c + V((sx * 0.02, 0.005, 0.065))), (-sx * 0.2, 0, 1),
                         (0, -1, 0), rib))
    P.append(PL.lathe_ax("medal", [(0.0, 0.0), (0.06, 0.0), (0.065, 0.01), (0.06, 0.022), (0.045, 0.018), (0.0, 0.02)],
                         (0, -1, 0), tuple(c), 12, m, 40, False, False))
    P += PL.glyph("star", c + V((0, -0.022, 0)), (1, 0, 0), (0, 0, 1), 0.06, 0.012, 0.008, m, "medalstar")
# a small finial on the board
P.append(rw.sphere("finial", 0.04, 10, 7, tuple(mb + V((0, 0.0, 0.265))), (0, 0, 0), (1, 1, 1), M("TealGlow")))
P.append(PL.lathe_ax("finialcup", [(0.0, 0.0), (0.035, 0.0), (0.05, 0.03), (0.04, 0.04), (0.0, 0.035)], (0, 0, 1),
                     tuple(mb + V((0, 0.0, 0.225))), 10, "M_Brass", 40, False, False))

E.tri_breakdown(P, 16)
E.join(P, "Terminal")
PL.finish(ASSET, (1.2, 1.2, 1.6), 4000)
PL.qa(ASSET, ("front", "side"))
