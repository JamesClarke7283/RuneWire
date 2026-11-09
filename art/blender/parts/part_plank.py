"""part_plank: 2.0 x 0.5 x 0.12 m wooden plank.

Two chunky boards separated by a rounded groove, held together by dark-wood end battens with
nail heads on both faces (the plank can be used either way up), plus a couple of painted knots.
Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
rw.reset()

L, W, H = 2.0, 0.5, 0.12
BAT_W = 0.17          # end batten width (along X)
BAT_IN = 0.07         # battens sit this far in from the board ends
BAT_H = 0.110         # batten height; nail heads add 0.005 per face -> 0.12 overall
BOARD_T = 0.084       # board thickness (recessed between the battens)
GAP = 0.026           # groove between the two boards
BW = (W - 0.03 - GAP) / 2
parts = []
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

# --- two boards (slightly different lengths/heights for a hand-built look) -----------------
for i, sy in enumerate((-1, 1)):
    y = sy * (GAP / 2 + BW / 2)
    length = L - 0.012 * i
    b = rw.rounded_box("board", (length, BW, BOARD_T), 0.024, (-0.006 * i, y, 0.002 * sy), mat="M_WoodPlanks",
                       segments=3)
    parts.append(b)
# a dark spine under the groove so it never reads as see-through
parts.append(rw.box("spine", (L - 0.1, GAP + 0.02, BOARD_T * 0.5), (0, 0, 0), mat="M_WoodDark"))

# painted knots (flat lenses sunk into the board faces)
for (x, y, sz, s) in ((-0.42, -0.12, 1, 1.0), (0.55, 0.13, 1, 0.8), (0.2, -0.1, -1, 0.9), (-0.6, 0.12, -1, 0.7)):
    z = sz * (BOARD_T / 2 + 0.002 * (1 if y < 0 else -1) * sz)
    parts.append(rw.sphere("knot", 0.5, 12, 6, (x, y, z), scale=(0.11 * s, 0.06 * s, 0.006), mat="M_WoodDark"))
    parts.append(rw.sphere("knot_c", 0.5, 8, 4, (x, y, z), scale=(0.045 * s, 0.025 * s, 0.0085), mat="M_WoodDark"))

# --- end battens ---------------------------------------------------------------------------
for sx in (-1, 1):
    x = sx * (L / 2 - BAT_IN - BAT_W / 2)
    parts.append(rw.rounded_box("batten", (BAT_W, W, BAT_H), 0.028, (x, 0, 0), mat="M_WoodDark", segments=3))
    # nail heads: two per board, on both faces
    for sz in (-1, 1):
        for yy in (-0.18, -0.07, 0.07, 0.18):
            parts.append(pl.rivet((x, yy, sz * BAT_H / 2), (0, 0, sz), 0.024, 0.005, "NailHead", 8))

plank = rw.join(parts, "Plank")
rw.smooth(plank, 35)
pl.recentre()
rw.set_origin(plank, (0, 0, 0))
pl.check("part_plank", (L, W, H))
rw.finish("part_plank", "parts", icon=True)
