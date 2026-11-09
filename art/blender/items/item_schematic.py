"""item_schematic: a blueprint scroll, partly unrolled, about 0.33 x 0.27 x 0.1 m (shared by every schematic).

A single fat roll of blueprint paper (flat 2f5f9e, with paler rolled ends showing a dark spiral) lying along
Blender X, its sheet unrolled toward the viewer, the free end curling up in a small lip. The flat part carries a white
technical drawing: a border, a big gear outline with its hub and centre lines, a dimension line with arrows, a side
view of the gear and a title block. A cream string is tied round the roll, with a red wax seal (stamped with a cog)
over the knot and two loose ends. Its single blue roll keeps it apart from item_treasure_map (a parchment
sheet between two rolls). One mesh object "Schematic", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_schematic"
rw.reset()

BLUE, INK = ml.mat("SchematicBlue"), ml.mat("SchematicInk")
W = 0.33                          # sheet width = roll length (along X)
RR = 0.04                         # roll radius
RY, RZ = 0.06, 0.04               # roll axis position (y, z): the roll rests on the sheet
T = 0.003                         # paper thickness
Y_START, Y_FLAT = 0.05, -0.15     # the sheet runs from under the roll (hidden) out to the lip
RC, CURL = 0.013, math.radians(125)   # the free end curls up in a small lip
ZS = T / 2                        # sheet mid-plane height
parts = []

# --- the roll, with paler ends and a dark spiral of paper layers on each end -----------------------------------
prof = [(0.0, -W / 2), (RR - 0.006, -W / 2), (RR, -W / 2 + 0.006), (RR, W / 2 - 0.006), (RR - 0.006, W / 2),
        (0.0, W / 2)]
roll = il.lathe("roll", prof, (1, 0, 0), (0, RY, RZ), 24, BLUE, 40)
rw.set_mat_where(roll, ml.mat("SchematicPale"), lambda c, n: abs(n.x) > 0.7)
parts.append(roll)
spiral = []
for i in range(23):
    t = i / 22
    a = 2 * math.pi * 2.3 * t
    r = 0.007 + (RR - 0.013) * t
    spiral.append((r * math.cos(a), r * math.sin(a)))
for sx in (-1, 1):
    mp_end = il.plane_map((sx * W / 2, RY, RZ), (0, -sx, 0), (0, 0, 1), -0.0004, 0.0012)
    parts.append(ml.stroke("spiral", spiral, 0.0042, mp_end, False, "SchematicDeep"))

# --- the unrolled sheet: flat, then curling up at the free end ------------------------------------------------
LF = Y_START - Y_FLAT


def sheet_pt(v):
    """(point (y, z), top normal (ny, nz)) at fraction v along the sheet: v < 0.25 is the flat run."""
    if v <= 0.25:
        return (Y_START - LF * v / 0.25, ZS), (0.0, 1.0)
    a = CURL * (v - 0.25) / 0.75
    return (Y_FLAT - RC * math.sin(a), ZS + RC - RC * math.cos(a)), (math.sin(a), math.cos(a))


def P(u, v, s):
    (y, z), (ny, nz) = sheet_pt(v)
    k = (s - 0.5) * T
    return ((u - 0.5) * W, y + ny * k, z + nz * k)


parts.append(il.param_slab("sheet", P, 2, 16, BLUE))

# --- the white drawing on the flat part -----------------------------------------------------------------------
Y0 = RY - RR * 0.55                     # where the roll stops hiding the sheet (seen from the front, above)
YC = (Y0 + Y_FLAT) / 2                  # centre and depth of the visible flat run
H = Y0 - Y_FLAT
mp = il.plane_map((0.0, YC, T), (1, 0, 0), (0, 1, 0), -0.0003, 0.0013)


def line(pts, w=0.005, closed=False):
    parts.append(ml.stroke("ink", pts, w, mp, closed, INK))


def at(pts, dx, dy=0.0):
    return [(x + dx, y + dy) for (x, y) in pts]


line(ml.rounded_rect_pts(W - 0.028, H - 0.016, 0.006, 1), 0.0045, True)             # border
GX, GR = -0.06, 0.052                                                                # gear, front view
line(at(ml.gear_pts(GR, GR - 0.013, 10, 9), GX), 0.0068, True)
line(at([(0.017 * math.cos(2 * math.pi * i / 14), 0.017 * math.sin(2 * math.pi * i / 14)) for i in range(14)], GX),
     0.0055, True)                                                                   # hub
line([(GX - GR - 0.01, 0.0), (GX + GR + 0.01, 0.0)], 0.003)                          # centre lines
line([(GX, -GR - 0.008), (GX, GR + 0.008)], 0.003)
DX = GX - GR - 0.022                                                                 # dimension line + arrows
line([(DX, -GR + 0.004), (DX, GR - 0.004)], 0.003)
for sy in (-1, 1):
    line([(DX - 0.006, sy * (GR - 0.012)), (DX, sy * GR), (DX + 0.006, sy * (GR - 0.012))], 0.003)
    line([(DX - 0.004, sy * GR), (GX - 0.006, sy * GR)], 0.0022)
SX = 0.035                                                                           # side view of the gear
line(at(ml.rounded_rect_pts(0.02, 2 * GR, 0.002, 1), SX), 0.0045, True)
line([(SX - 0.016, 0.0), (SX + 0.016, 0.0)], 0.0026)
TX, TY = 0.105, -0.022                                                               # title block
line(at(ml.rounded_rect_pts(0.075, 0.05, 0.002, 1), TX, TY), 0.004, True)
line([(TX - 0.0375, TY + 0.008), (TX + 0.0375, TY + 0.008)], 0.003)
for (k, L) in ((0, 0.05), (1, 0.034)):
    line([(TX - 0.03, TY - 0.004 - 0.011 * k), (TX - 0.03 + L, TY - 0.004 - 0.011 * k)], 0.004)
line([(TX - 0.03, TY + 0.016), (TX + 0.012, TY + 0.016)], 0.005)

# --- string tie round the roll, wax seal over the knot, two loose ends ------------------------------------------
STR = ml.mat("StringCream")
XT = 0.075
for dx in (-0.0055, 0.0055):
    parts.append(rw.torus("string", RR + 0.002, 0.0042, 18, 5, (XT + dx, RY, RZ), (0, 90, 0), STR))
N = V((0.0, -0.78, 0.62)).normalized()                                               # seal faces front-up
SP = V((XT, RY, RZ)) + N * (RR + 0.004)
for (sx, end) in ((-1, V((XT - 0.03, RY - RR - 0.02, 0.012))), (1, V((XT + 0.026, RY - RR - 0.03, 0.006)))):
    mid = SP + V((sx * 0.014, -0.022, -0.02))
    parts.append(pl.sausage("string_end", [SP, mid, end], 0.0042, 6, 3, STR, (True, True), 1, True, 60))
seal = [(0.0, -0.006), (0.027, -0.006), (0.029, -0.001), (0.026, 0.004), (0.02, 0.0065), (0.0, 0.007)]
parts.append(il.lathe("seal", seal, N, SP, 16, ml.mat("SealRed"), 50))
parts.append(il.gear("seal_cog", 0.0155, 7, 0.0045, 0.004, 0.005, SP + N * 0.0075, N, ml.mat("SealDark")))

scroll = rw.join(parts, "Schematic")
ml.no_outline(scroll, [INK])          # icon/preview only: crisp white line art without dark Freestyle outlines
il.finish_item(ASSET, (0.33, 0.27, 0.1))
