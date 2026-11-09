"""part_crate: 1 x 1 x 1 m wooden crate (reference example for generator scripts).

Chunky dark-wood frame, inset planks, a diagonal brace on four sides, brass corner caps with
nail heads. Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rwlib as rw  # noqa: E402

rw.reset()

S = 1.0          # crate size
F = 0.12         # frame beam thickness
H = S / 2
parts = []

# --- frame: 12 rounded edge beams -------------------------------------------------------
for sx in (-1, 1):
    for sy in (-1, 1):
        # vertical posts
        parts.append(rw.rounded_box("post", (F, F, S), 0.02, (sx * (H - F / 2), sy * (H - F / 2), 0), mat="M_WoodDark"))
        # beams along X (top & bottom)
        parts.append(rw.rounded_box("bx", (S - 2 * F + 0.01, F, F), 0.02, (0, sx * (H - F / 2), sy * (H - F / 2)), mat="M_WoodDark"))
        # beams along Y (top & bottom)
        parts.append(rw.rounded_box("by", (F, S - 2 * F + 0.01, F), 0.02, (sx * (H - F / 2), 0, sy * (H - F / 2)), mat="M_WoodDark"))

# --- planks on the 6 faces --------------------------------------------------------------
inner = S - 2 * F
n_planks = 3
gap = 0.018
pw = (inner - gap * (n_planks - 1)) / n_planks
inset = 0.035
pt = 0.05
for axis in range(3):
    for sgn in (-1, 1):
        for i in range(n_planks):
            off = -inner / 2 + pw / 2 + i * (pw + gap)
            if axis == 0:   # +-X faces, planks run along Y
                size, loc = (pt, inner, pw), (sgn * (H - inset - pt / 2), 0, off)
            elif axis == 1:  # +-Y faces, planks run along X
                size, loc = (inner, pt, pw), (0, sgn * (H - inset - pt / 2), off)
            else:            # +-Z faces, planks run along X
                size, loc = (inner, pw, pt), (0, off, sgn * (H - inset - pt / 2))
            parts.append(rw.box("plank", size, loc, mat="M_WoodPlanks", bevel=0.008, bevel_segments=1))

# --- diagonal braces on the four side faces ----------------------------------------------
import math  # noqa: E402
diag_len = math.sqrt(2) * inner * 0.98
for axis, sgn in ((0, -1), (0, 1), (1, -1), (1, 1)):
    if axis == 0:
        b = rw.rounded_box("brace", (0.06, diag_len, 0.11), 0.015, (sgn * (H - 0.03), 0, 0), rot=(45 * sgn, 0, 0), mat="M_WoodDark")
    else:
        b = rw.rounded_box("brace", (diag_len, 0.06, 0.11), 0.015, (0, sgn * (H - 0.03), 0), rot=(0, 45 * sgn, 0), mat="M_WoodDark")
    parts.append(b)

# --- brass corner caps with nail heads ---------------------------------------------------
nail = rw.flat("NailHead", "4a4f57", 0.4, 1.0)
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            c = (sx * (H - 0.085), sy * (H - 0.085), sz * (H - 0.085))
            parts.append(rw.rounded_box("cap", (0.18, 0.18, 0.18), 0.025, c, mat="M_Brass", segments=2))
            for (dx, dy, dz) in ((sx, 0, 0), (0, sy, 0), (0, 0, sz)):
                p = (c[0] + dx * 0.088, c[1] + dy * 0.088, c[2] + dz * 0.088)
                parts.append(rw.sphere("nail", 0.016, 6, 4, p, mat=nail))

crate = rw.join(parts, "Crate")
rw.smooth(crate, 35)
rw.finish("part_crate", "parts", icon=True)
