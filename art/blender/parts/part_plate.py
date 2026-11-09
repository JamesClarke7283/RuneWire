"""part_plate: 2.0 x 2.0 x 0.08 m riveted steel plate.

Rounded steel slab with a soft inset panel line on both faces, chunky brass rivets all around the
border and brass corner caps (both faces: the plate is symmetric so it can be used either way up).
Origin at the bounding-box centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
rw.reset()

S, T = 2.0, 0.08
RIV_H = 0.011
SLAB = T - 2 * RIV_H        # 0.058: rivet heads make up the rest of the 0.08 envelope
HALF = SLAB / 2
parts = []
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

slab = rw.rounded_box("slab", (S, S, SLAB), 0.022, mat="M_Steel", segments=3)

# --- inset panel line: rounded-rectangle groove on both faces ------------------------------------
A = S / 2 - 0.22            # half-size of the groove rectangle
RC = 0.12                   # corner radius
GR = 0.015                  # groove (cutter) radius


def rounded_rect(a, rc, z, per_corner=6):
    pts = []
    corners = ((a - rc, a - rc, 0), (-(a - rc), a - rc, 90), (-(a - rc), -(a - rc), 180), (a - rc, -(a - rc), 270))
    for (cx, cy, a0) in corners:
        for k in range(per_corner + 1):
            ang = math.radians(a0 + 90 * k / per_corner)
            pts.append((cx + rc * math.cos(ang), cy + rc * math.sin(ang), z))
    # start/end in the middle of the +X side so the overlapping ends sit on a straight run
    mid = (a, 0.0, z)
    return [mid] + pts[:] + [(a, -0.2, z), mid]


cutters = []
for sz in (-1, 1):
    path = rounded_rect(A, RC, sz * HALF)
    cutters.append(pl.sausage("groove", path, GR, 8, 1, None, (True, True), 2, False, 0))
pl.carve(slab, cutters)
parts.append(slab)

# --- brass rivets around the border (both faces) -----------------------------------------------
E = S / 2 - 0.11
n = 8
for sz in (-1, 1):
    for i in range(n):
        t = -E + 2 * E * i / (n - 1)
        for (x, y) in ((t, -E), (t, E), (-E, t), (E, t)):
            if abs(abs(x) - E) < 1e-6 and abs(abs(y) - E) < 1e-6:
                continue          # corners get a cap instead
            parts.append(pl.rivet((x, y, sz * HALF), (0, 0, sz), 0.03, RIV_H, "M_Brass", 10))

# --- brass corner caps with a big dome rivet ----------------------------------------------------
for sx in (-1, 1):
    for sy in (-1, 1):
        c = (sx * (S / 2 - 0.1), sy * (S / 2 - 0.1), 0)
        parts.append(rw.rounded_box("cap", (0.2, 0.2, SLAB + 0.008), 0.026, c, mat="M_Brass", segments=2))
        for sz in (-1, 1):
            parts.append(pl.rivet((c[0], c[1], sz * (SLAB / 2 + 0.004)), (0, 0, sz), 0.036, RIV_H - 0.004,
                                  "NailHead", 12))

plate = rw.join(parts, "Plate")
rw.smooth(plate, 35)
pl.recentre()
rw.set_origin(plate, (0, 0, 0))
pl.check("part_plate", (S, S, T))
rw.finish("part_plate", "parts", icon=True)
