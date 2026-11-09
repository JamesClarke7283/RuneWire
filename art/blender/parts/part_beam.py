"""part_beam: 3.0 x 0.3 x 0.3 m riveted steel I-beam (long axis X).

Orange-painted flanges and web with round lightening holes (grommet rims), riveted bare-steel fish
plates and straps at both ends and rows of chunky steel rivets along the flanges. (Paint chipping
comes from the painted_metal texture.) Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
rw.reset()

L, S = 3.0, 0.3
PAINT = "M_PaintedMetal__e8762c"   # signal orange
RIV_H = 0.008                      # rivet head height (rivets define the outer 0.3 envelope)
OUT = S / 2 - RIV_H                # flange outer face
FT = 0.05                          # flange thickness
WT = 0.05                          # web thickness
parts = []

# --- flanges + web --------------------------------------------------------------------------
for sz in (-1, 1):
    parts.append(rw.rounded_box("flange", (L, S, FT), 0.016, (0, 0, sz * (OUT - FT / 2)), mat=PAINT, segments=2))
web_h = 2 * (OUT - FT) + 0.02
web = rw.rounded_box("web", (L - 0.004, WT, web_h), 0.008, (0, 0, 0), mat=PAINT, segments=1)

# lightening holes through the web, each with a thick grommet rim
HOLES = (-0.84, -0.28, 0.28, 0.84)
HR = 0.06
cutters = [rw.cylinder("hole", HR, 0.2, 20, (x, 0, 0), (90, 0, 0)) for x in HOLES]
pl.carve(web, cutters)
parts.append(web)
for x in HOLES:
    prof = [(HR - 0.002, -0.036), (HR + 0.016, -0.036), (HR + 0.022, -0.03), (HR + 0.022, 0.03), (HR + 0.016, 0.036),
            (HR - 0.002, 0.036), (HR - 0.002, -0.036)]
    parts.append(pl.lathe_axis("grommet", prof, (0, 1, 0), (x, 0, 0), 20, PAINT, False, False, 50))

# --- fish plates at both ends (bare steel, riveted) -------------------------------------------
for sx in (-1, 1):
    x = sx * (L / 2 - 0.11)
    for sy in (-1, 1):
        y = sy * (WT / 2 + 0.008)
        parts.append(rw.rounded_box("fishplate", (0.2, 0.016, web_h - 0.03), 0.006, (x, y, 0), mat="M_Steel",
                                    segments=1))
        for dx in (-0.05, 0.05):
            for dz in (-0.05, 0.05):
                parts.append(pl.rivet((x + dx, y + sy * 0.008, dz), (0, sy, 0), 0.015, 0.009, "M_Steel", 8))
    # a steel strap across each end of the top/bottom flanges
    for sz in (-1, 1):
        parts.append(rw.rounded_box("endstrap", (0.12, S - 0.02, 0.012), 0.004, (x, 0, sz * (OUT - 0.003)),
                                    mat="M_Steel", segments=1))

# --- rivet rows along both flanges (top and bottom faces) ---------------------------------------
n = 9
for sz in (-1, 1):
    for sy in (-1, 1):
        for i in range(n):
            x = -1.2 + 2.4 * i / (n - 1)
            parts.append(pl.rivet((x, sy * 0.095, sz * OUT), (0, 0, sz), 0.022, RIV_H, "M_Steel", 10))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(pl.rivet((sx * (L / 2 - 0.11), sy * 0.095, sz * (OUT + 0.003)), (0, 0, sz), 0.017,
                                  RIV_H - 0.003, "M_Steel", 10))

beam = rw.join(parts, "Beam")
rw.smooth(beam, 35)
pl.recentre()
rw.set_origin(beam, (0, 0, 0))
pl.check("part_beam", (L, S, S))
rw.finish("part_beam", "parts", icon=True)
