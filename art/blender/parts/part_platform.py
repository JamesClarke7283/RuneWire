"""part_platform: 4.0 x 4.0 x 0.2 m wooden deck.

Eight planks (slightly uneven, nailed to three dark-wood joists underneath) set inside a chunky brass
trim frame with big corner caps held by hex bolts and a riveted strap at the middle of every side.
Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
rw.reset()
rnd = pl.seeded(11)

S, H = 4.0, 0.2
FW = 0.16                 # frame rail width
BOT = -H / 2
CAP_TOP = 0.084           # corner caps; their bolts reach +0.1
RAIL_TOP = 0.052
DECK_TOP = 0.03
PLANK_T = 0.075
parts = []
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

# --- brass frame -------------------------------------------------------------------------------
rail_h = RAIL_TOP - BOT
for s in (-1, 1):
    parts.append(rw.rounded_box("rail", (S - 0.2, FW, rail_h), 0.03, (0, s * (S / 2 - FW / 2), BOT + rail_h / 2),
                                mat="M_Brass", segments=2))
    parts.append(rw.rounded_box("rail", (FW, S - 0.2, rail_h), 0.03, (s * (S / 2 - FW / 2), 0, BOT + rail_h / 2),
                                mat="M_Brass", segments=2))
cap_h = CAP_TOP - BOT
CAP = 0.3
for sx in (-1, 1):
    for sy in (-1, 1):
        c = (sx * (S / 2 - CAP / 2), sy * (S / 2 - CAP / 2), BOT + cap_h / 2)
        parts.append(rw.rounded_box("cap", (CAP, CAP, cap_h), 0.04, c, mat="M_Brass", segments=2))
        for dx in (-1, 1):
            for dy in (-1, 1):
                parts.append(pl.bolt((c[0] + dx * 0.075, c[1] + dy * 0.075, CAP_TOP), (0, 0, 1), 0.03, 0.012,
                                     "M_Steel", spin=15 * (dx + dy)))
# mid-side straps
for (x, y, along_x) in ((0, -1, True), (0, 1, True), (-1, 0, False), (1, 0, False)):
    cx, cy = x * (S / 2 - FW / 2), y * (S / 2 - FW / 2)
    size = (0.34, FW - 0.01, 0.016) if along_x else (FW - 0.01, 0.34, 0.016)
    parts.append(rw.rounded_box("strap", size, 0.007, (cx, cy, RAIL_TOP + 0.004), mat="M_Brass", segments=1))
    for k in (-1, 1):
        px, py = (cx + k * 0.11, cy) if along_x else (cx, cy + k * 0.11)
        parts.append(pl.rivet((px, py, RAIL_TOP + 0.012), (0, 0, 1), 0.024, 0.01, "NailHead", 10))

# --- deck planks (run along X) -------------------------------------------------------------------
inner = S - 2 * FW
n = 8
gap = 0.022
pw = (inner - gap * (n - 1)) / n
JOISTS = (-1.25, 0.0, 1.25)
for i in range(n):
    y = -inner / 2 + pw / 2 + i * (pw + gap)
    dz = rnd.uniform(-0.004, 0.003)
    length = inner + 0.06 - rnd.uniform(0, 0.03)
    parts.append(rw.rounded_box("plank", (length, pw, PLANK_T), 0.02, (rnd.uniform(-0.01, 0.01), y,
                                DECK_TOP - PLANK_T / 2 + dz), mat="M_WoodPlanks", segments=2))
    for j, x in enumerate(JOISTS):
        off = 0.1 if (i + j) % 2 else -0.1
        parts.append(pl.rivet((x, y + off, DECK_TOP + dz), (0, 0, 1), 0.022, 0.006, "NailHead", 8))

# --- joists underneath (dark wood) -----------------------------------------------------------------
jt = DECK_TOP - PLANK_T - BOT + 0.01
for x in JOISTS:
    parts.append(rw.rounded_box("joist", (0.16, inner + 0.08, jt), 0.02, (x, 0, BOT + jt / 2), mat="M_WoodDark",
                                segments=1))

deck = rw.join(parts, "Platform")
rw.smooth(deck, 35)
pl.recentre()
rw.set_origin(deck, (0, 0, 0))
pl.check("part_platform", (S, S, H))
rw.finish("part_platform", "parts", icon=True)
