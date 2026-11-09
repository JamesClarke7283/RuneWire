"""prop_workbench: "Artificer's Workbench", about 2.4 (X) x 1.2 (Y) x 2.1 (Z) m. Origin at the ground centre,
the working side faces -Y.

A sturdy bench (M_WoodPlanks top planks on M_WoodDark legs, aprons and a lower shelf holding a crate and
spare plates) with brass corner caps; a teal-painted iron vise with a T-screw handle on the left end; a little
brass rune-anvil with a glowing teal rune; a brass desk lamp on the back-right holding a glowing warm crystal
(empty "LightPoint" at the crystal); a blueprint sheet with a rolled end, brass/copper gears, bolts and a hammer
scattered on top. Behind it (+Y) a pegboard between two posts, with a little shelf of jars, hung with
wrenches, hammers and copper wire coils on brass pegs.

Collision: Col_Bench_0 (bench body) and Col_Pegboard_0 (pegboard and posts), both -colonly boxes.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "items"))
import envlib as E  # noqa: E402
import itemlib as il  # noqa: E402

rw, pl, V = E.rw, il.pl, il.V
ASSET = "prop_workbench"
rw.reset()
P = []
TOP = 0.95                     # bench top height
TX, Y0, Y1 = 1.15, -0.5, 0.36  # top half-width, front and back edge
YC = (Y0 + Y1) / 2
DEPTH = Y1 - Y0

# --- bench -----------------------------------------------------------------------------------------------------
n_pl, gap = 4, 0.012
pw = (DEPTH - gap * (n_pl - 1)) / n_pl
for i in range(n_pl):
    y = Y0 + pw / 2 + i * (pw + gap)
    P.append(E.rbox("topplank", (2 * TX, pw, 0.09), (0, y, TOP - 0.045), m="M_WoodPlanks", r=0.016))
P.append(rw.box("topcore", (2 * TX - 0.04, DEPTH - 0.04, 0.05), (0, YC, TOP - 0.065), mat=E.M("Soot")))
for sx in (-1, 1):
    for y in (Y0 + 0.08, Y1 - 0.08):
        P.append(E.rbox("leg", (0.13, 0.13, TOP - 0.09), (sx * (TX - 0.1), y, (TOP - 0.09) / 2), m="M_WoodDark", r=0.02))
    P.append(E.rbox("apron", (0.06, DEPTH - 0.1, 0.14), (sx * (TX - 0.1), YC, TOP - 0.16), m="M_WoodDark", r=0.015))
    P.append(E.rbox("stretcher", (0.07, DEPTH - 0.1, 0.07), (sx * (TX - 0.1), YC, 0.2), m="M_WoodDark", r=0.015))
for y in (Y0 + 0.08, Y1 - 0.08):
    P.append(E.rbox("apron", (2 * TX - 0.24, 0.06, 0.14), (0, y, TOP - 0.16), m="M_WoodDark", r=0.015))
P.append(E.rbox("shelf", (2 * TX - 0.26, DEPTH - 0.2, 0.05), (0, YC, 0.25), m="M_WoodPlanks", r=0.012))
# brass corner caps on the top
for sx in (-1, 1):
    for y in (Y0, Y1):
        c = (sx * (TX - 0.045), y - math.copysign(0.045, y - YC), TOP - 0.045)
        P.append(E.rbox("cap", (0.12, 0.12, 0.115), c, m="M_Brass", r=0.02))
        P.append(E.rivet("nail", (c[0], c[1] + math.copysign(0.062, y - YC), c[2]), 0.014, "Iron", lo=True))
# lower shelf: a crate and a stack of spare plates
P += E.crate((0.42, 0.42, 0.38), (0.55, YC + 0.02, 0.275), 8)
for k, (dx, rz) in enumerate(((0.0, 4), (0.02, -6), (-0.01, 11))):
    P.append(E.cbox("spareplate", (0.42, 0.3, 0.025), (-0.55 + dx, YC, 0.29 + 0.027 * k), (0, 0, rz),
                    "M_PaintedMetal__e8762c" if k == 1 else "M_Steel", 0.008))

# --- vise (left end, front) --------------------------------------------------------------------------------------
VX = -0.82
vpaint = "M_PaintedMetal__2e8f8a"
P.append(E.rbox("vise_base", (0.24, 0.28, 0.06), (VX, Y0 + 0.2, TOP + 0.03), m=vpaint, r=0.015))
P.append(E.rbox("vise_body", (0.16, 0.24, 0.1), (VX, Y0 + 0.16, TOP + 0.1), m=vpaint, r=0.02))
for (y, nm) in ((Y0 + 0.17, "fixed"), (Y0 + 0.02, "moving")):
    P.append(E.rbox("vise_" + nm, (0.27, 0.07, 0.14), (VX, y, TOP + 0.2), m=vpaint, r=0.018))
    P.append(E.cbox("jawplate", (0.25, 0.02, 0.06), (VX, y + (-0.045 if nm == "fixed" else 0.045), TOP + 0.24), (0, 0, 0),
                    "M_Steel", 0.005))
for dx in (-0.08, 0.08):
    P.append(E.rod("vise_slide", (VX + dx, Y0 - 0.02, TOP + 0.16), (VX + dx, Y0 + 0.2, TOP + 0.16), 0.014, 8, "M_Steel"))
P.append(E.rod("vise_screw", (VX, Y0 - 0.1, TOP + 0.18), (VX, Y0 + 0.1, TOP + 0.18), 0.02, 8, "M_Steel"))
P.append(E.rod("vise_handle", (VX - 0.16, Y0 - 0.1, TOP + 0.18), (VX + 0.16, Y0 - 0.1, TOP + 0.18), 0.012, 8, "M_Steel"))
for sx in (-1, 1):
    P.append(E.ball("vise_knob", 0.026, (VX + sx * 0.17, Y0 - 0.1, TOP + 0.18), "M_Brass", 8, 6))

# --- rune anvil (right of centre) ---------------------------------------------------------------------------------
AX, AY = 0.32, Y0 + 0.3
P.append(E.rbox("anvil_foot", (0.22, 0.16, 0.06), (AX, AY, TOP + 0.03), m="M_Brass", r=0.015))
P.append(E.rbox("anvil_waist", (0.12, 0.1, 0.08), (AX, AY, TOP + 0.1), m="M_Brass", r=0.012))
P.append(E.rbox("anvil_face", (0.26, 0.14, 0.07), (AX, AY, TOP + 0.17), m="M_Brass", r=0.015))
horn = rw.cone("anvil_horn", 0.055, 0.008, 0.16, 10, (0, 0, 0), (0, 90, 0), il.mat("M_Brass"))
horn.location = (AX + 0.2, AY, TOP + 0.175)
P.append(horn)
P += pl.glyph("algiz", V((AX, AY - 0.07, TOP + 0.17)), (1, 0, 0), (0, 0, 1), 0.06, 0.012, 0.008, E.M("TealGlow"), "rune")
P += pl.glyph("algiz", V((AX, AY + 0.07, TOP + 0.17)), (-1, 0, 0), (0, 0, 1), 0.06, 0.012, 0.008, E.M("TealGlow"), "rune")
# a hammer resting by the anvil
hh = V((AX + 0.05, AY - 0.18, TOP + 0.025))
P.append(E.rod("hammer_handle", hh, hh + V((0.28, 0.06, 0)), 0.016, 8, "M_WoodDark"))
P.append(E.rbox("hammer_head", (0.05, 0.12, 0.05), tuple(hh + V((0.28, 0.06, 0.005))), (0, 0, 12), "M_Steel", 0.012))

# --- crystal desk lamp (back right) -----------------------------------------------------------------------------
LX, LY = 0.85, Y1 - 0.14
P.append(E.lathe("lamp_base", [(0.0, TOP), (0.1, TOP), (0.104, TOP + 0.012), (0.07, TOP + 0.04), (0.03, TOP + 0.05),
                               (0.0, TOP + 0.05)], 16, (LX, LY, 0), "M_Brass", 40))
arm = [(LX, LY, TOP + 0.04), (LX, LY + 0.02, TOP + 0.3), (LX - 0.02, LY - 0.05, TOP + 0.48), (LX - 0.05, LY - 0.2, TOP + 0.52)]
P.append(E.tube("lamp_arm", arm, 0.018, "M_Brass", 1, smooth=True, ures=4))
P.append(E.ball("lamp_joint", 0.03, arm[1], "M_Copper", 8, 6))
HEAD = V((LX - 0.06, LY - 0.25, TOP + 0.47))
AIM = V((0.0, 0.4, 1.0)).normalized()          # shade axis; the opening looks down and forward (-AIM)
shade = E.lathe("lamp_shade", [(0.035, 0.1), (0.05, 0.085), (0.1, 0.0), (0.112, -0.012), (0.1, -0.016)], 12, (0, 0, 0),
                "M_Brass", 40, cap_bottom=False, cap_top=True)
pl.align(shade, AIM, HEAD)
P.append(shade)
LIGHT = HEAD - AIM * 0.04
bulb = E.bipyramid("lamp_crystal", 0.048, 0.05, 0.075, 6, (0, 0, 0), "LampGlow", mid=0.03)
pl.align(bulb, AIM, LIGHT)
P.append(bulb)

# --- scattered on the top: blueprint, gears, bolts ---------------------------------------------------------------
BP = V((-0.28, Y0 + 0.32, TOP + 0.004))
rot = 8.0
sheet = rw.box("blueprint", (0.56, 0.38, 0.006), (0, 0, 0), mat=il.M("Blueprint"))
lines = [rw.box("bpline", (0.44, 0.012, 0.004), (0.0, 0.13, 0.004), mat=il.M("BlueprintInk")),
         rw.box("bpline", (0.012, 0.22, 0.004), (-0.18, 0.0, 0.004), mat=il.M("BlueprintInk")),
         rw.box("bpline", (0.18, 0.012, 0.004), (0.06, -0.12, 0.004), mat=il.M("BlueprintInk"))]
ring = rw.torus("bpgear", 0.08, 0.007, 16, 3, (0.04, 0.02, 0.004), (0, 0, 0), il.M("BlueprintInk"))
pl.xform(ring, il.Matrix.Diagonal((1.0, 1.0, 0.4, 1.0)))
roll = rw.cylinder("bproll", 0.035, 0.4, 10, (0.3, 0.0, 0.035), (90, 0, 0), il.M("Blueprint"))
bp = [sheet, ring, roll] + lines
E.place(bp, tuple(BP), (0, 0, rot))
P += bp
P.append(E.gear("gear", 0.11, 10, 0.03, 0.035, 0.03, (0.05, Y0 + 0.2, TOP + 0.018), (0, 0, 1), "M_Brass", spin=5))
P.append(E.gear("gear", 0.075, 8, 0.024, 0.03, 0.0, (0.16, Y0 + 0.12, TOP + 0.016), (0, 0, 1), "M_Copper", spin=12))
P.append(E.gear("gear", 0.09, 9, 0.026, 0.03, 0.022, (-0.6, Y1 - 0.18, TOP + 0.08), (0.2, -1, 0.2), "M_Brass", spin=3))
for k, (p, a) in enumerate((((-0.02, Y0 + 0.08, TOP + 0.02), 20), ((0.6, Y0 + 0.12, TOP + 0.02), -40),
                            ((0.66, Y0 + 0.2, TOP + 0.02), 75))):
    b = pl.bolt(V(p), (math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0), 0.022, 0.016, il.mat("M_Steel"),
                "bolt", True, 0, False)
    P.append(b)
    P.append(E.rod("bolt_shaft", p, (p[0] - 0.08 * math.cos(math.radians(a)), p[1] - 0.08 * math.sin(math.radians(a)), p[2]),
                   0.011, 6, "M_Steel"))

# --- pegboard (back, +Y) ------------------------------------------------------------------------------------------
PY = 0.5
for sx in (-1, 1):
    P.append(E.rbox("post", (0.1, 0.1, 2.1), (sx * 1.12, PY, 1.05), m="M_WoodDark", r=0.02))
P.append(E.rbox("board", (2.16, 0.04, 1.02), (0, PY, 1.52), m="M_WoodPlanks__d7a46a", r=0.01))
P.append(E.rbox("header", (2.34, 0.12, 0.1), (0, PY, 2.05), m="M_WoodDark", r=0.02))
P.append(E.rbox("rail", (2.2, 0.08, 0.06), (0, PY, 1.0), m="M_WoodDark", r=0.015))
# peg holes: one flat mesh of small dark squares on the board face
verts, faces = [], []
for i in range(13):
    for j in range(6):
        x, z = -0.96 + 0.16 * i, 1.1 + 0.15 * j
        k = len(verts)
        s = 0.012
        verts += [(x - s, PY - 0.0205, z - s), (x + s, PY - 0.0205, z - s), (x + s, PY - 0.0205, z + s), (x - s, PY - 0.0205, z + s)]
        faces.append((k, k + 1, k + 2, k + 3))
P.append(rw.mesh_from_data("pegholes", verts, faces, mat=E.M("Soot")))
# shelf with jars
P.append(E.rbox("pshelf", (0.9, 0.16, 0.035), (0.55, PY - 0.1, 1.8), m="M_WoodDark", r=0.01))
for k, (x, h, m) in enumerate(((0.25, 0.14, "BottleGreen"), (0.42, 0.11, "BottleBlue"), (0.58, 0.16, "Orange"), (0.8, 0.12, "BottleGreen"))):
    P.append(E.lathe("jar", [(0.0, 0.0), (0.045, 0.0), (0.05, 0.02), (0.05, h - 0.03), (0.03, h - 0.01), (0.03, h), (0.0, h)],
                     8, (x, PY - 0.1, 1.818), m, 40))
    P.append(E.lathe("jarcap", [(0.0, h - 0.005), (0.034, h - 0.005), (0.034, h + 0.02), (0.0, h + 0.02)], 8,
                     (x, PY - 0.1, 1.818), "M_Brass", 40))


def peg(x, z):
    return E.rod("peg", (x, PY - 0.02, z), (x, PY - 0.09, z + 0.01), 0.011, 6, "M_Brass")


# wrenches (head up)
for (x, z, L, s) in ((-0.9, 1.25, 0.42, 1.0), (-0.72, 1.3, 0.34, 0.85)):
    P.append(peg(x, z + L + 0.02))
    P.append(E.rbox("wrench", (0.04 * s, 0.018, L), (x, PY - 0.05, z + L / 2), m="M_Steel", r=0.008))
    head = il.wrap_prism("wrench_head", il.wrench_head_pts(0.055 * s, 0.045 * s, 0.05 * s),
                         il.plane_map((x, PY - 0.05, z + L + 0.02), (1, 0, 0), (0, 0, 1), -0.009, 0.018), "M_Steel")
    P.append(head)
    P.append(E.ball("wrench_ring", 0.03 * s, (x, PY - 0.05, z), "M_Steel", 8, 4, (1, 0.35, 1)))
# hammers (head up, hung by the head on two pegs)
for (x, L, m) in ((-0.42, 0.42, "M_WoodDark"), (-0.22, 0.34, "M_WoodPlanks")):
    zt = 1.82
    P.append(peg(x - 0.05, zt - 0.06))
    P.append(peg(x + 0.05, zt - 0.06))
    P.append(E.rod("hammer_handle", (x, PY - 0.06, zt - L), (x, PY - 0.06, zt), 0.02, 8, m))
    P.append(E.rbox("hammer_head", (0.2, 0.06, 0.07), (x + 0.02, PY - 0.06, zt + 0.02), m="M_Steel", r=0.015))
# copper wire coils
for (x, z, r) in ((0.2, 1.42, 0.13), (0.5, 1.35, 0.1)):
    P.append(peg(x, z + r * 0.9))
    for k in range(2):
        P.append(E.ring("coil", r - 0.016 * k, 0.017, (x + 0.005 * k, PY - 0.055 - 0.018 * k, z), (0, 1, 0.12), "M_Copper", 14, 4))
# saw-toothed ruler / caliper: a brass caliper
P.append(peg(0.85, 1.6))
P.append(E.rbox("caliper", (0.04, 0.016, 0.42), (0.85, PY - 0.05, 1.38), m="M_Brass", r=0.006))
P.append(E.rbox("caliper_jaw", (0.12, 0.016, 0.03), (0.89, PY - 0.05, 1.2), m="M_Brass", r=0.006))
P.append(E.rbox("caliper_jaw", (0.1, 0.016, 0.03), (0.88, PY - 0.05, 1.28), m="M_Brass", r=0.006))
# brass sign on the header
P.append(E.rbox("sign", (0.5, 0.03, 0.14), (0, PY - 0.07, 2.05), m="M_Brass", r=0.012))
P.append(E.gear("sign_gear", 0.045, 8, 0.012, 0.014, 0.0, (0, PY - 0.09, 2.05), (0, -1, 0), "M_DarkMetal"))

bench = E.join(P, "Workbench", origin=(0, 0, 0))
rw.smooth(bench, 35)
rw.empty("LightPoint", tuple(LIGHT))
E.col_box("Bench", (2 * TX + 0.04, DEPTH + 0.04, TOP + 0.05), (0, YC, (TOP + 0.05) / 2))
E.col_box("Pegboard", (2.36, 0.14, 2.1), (0, PY, 1.05))
E.check(ASSET, (2.4, 1.2, 2.1), 6000)
rw.finish(ASSET, "env", previews=E.previews())
