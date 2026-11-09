"""prop_loom: "Tailor's Loom", a crafting station for the town plaza, about 2.0 x 1.2 x 2.0 m.
Origin at the ground centre; the weaver's side faces -Y.

An upright frame loom in chunky dark wood (M_WoodDark): two square posts on trestle feet with diagonal braces, a
top beam whose ends curl up like a yoke, and an arched crest board (M_WoodPlanks) with a brass medallion carrying
a glowing violet rune. Between the posts, a cream warp roll at the top feeds a sheet of cream warp threads down to
the half-woven cloth: horizontal stripes of red, gold, teal, cream and violet (M_Fabric tinted: Godot multiplies
the woven fabric texture by the tint) with a band of gold diamonds, wound onto a cloth roll at the bottom. A wooden
shuttle with red yarn rests on the weaving edge, a shed rod and a heddle bar cross the warp, and a brass ratchet
wheel with a pawl sits on the cloth beam's right end.

Around it: on the right, a standing thread rack with six chunky spools on slanted pegs (red, gold, blue, violet,
cream and one of glowing teal arcane thread) and a little brass lantern hanging from the beam's right end; on the
left, a wicker basket heaped with golden reed fibre (hanks of it draped over the rim), and two finished pouches
(a teal cloth one with a gold band, a leather one with brass studs) hanging from a brass hook on the beam's left
end. In front, the weaver's three-legged stool with a red cushion, and a ball of violet yarn on the ground.

Nodes: Loom (all static geometry) and the empty LightPoint (in the lantern).
Collision: Col_Loom_0-colonly, one box around the whole station.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "prop_loom"
S.reset()
rnd = random.Random(31)
P = []


def fab(hexcol):
    """Woven-cloth material: M_Fabric tinted so that its in-game colour (texture x tint) is hexcol."""
    return G.tinted("M_Fabric", hexcol)


RED, GOLD, TEAL, CREAM, VIOLET = (fab(h) for h in ("d9473b", "f2b43a", "2fa39a", "f3e6c8", "8a5cc8"))
POUCH_TEAL, CUSHION = fab("2a8f9c"), fab("c8463a")

FY = 0.2            # the warp / cloth plane
PX = 0.62           # post centres
PW = 0.13           # post section
TOPZ = 1.84         # top beam axis
WZ = 1.6            # warp roll axis
CZ = 0.47           # cloth roll axis
CLOTH_BOT = 0.6
HALF = 0.5          # half-width of the cloth and warp

# --- the frame -----------------------------------------------------------------------------------------------------
for sx in (-1, 1):
    x = sx * PX
    P.append(E.cbox("post", (PW, PW, TOPZ - 0.1), (x, FY, (TOPZ + 0.1) / 2), (0, 0, 0), "M_WoodDark", 0.025))
    P.append(E.rbox("foot", (0.15, 0.8, 0.15), (x, FY + 0.03, 0.075), (0, 0, 0), "M_WoodDark", 0.05))
    for (y0, y1) in ((FY - 0.32, FY - 0.06), (FY + 0.36, FY + 0.06)):
        P.append(E.beam("brace", (x, y0, 0.13), (x, y1, 0.5), 0.075, 0.075, "M_WoodDark", 0.015))
    for z in (TOPZ - 0.12, 0.62):     # brass bolt heads on the front of the joints
        P.append(E.rivet("bolt", (x, FY - PW / 2 - 0.004, z), 0.022, "M_Brass", lo=True))
P.append(E.cbox("stretcher", (2 * PX - PW, 0.09, 0.09), (0, FY + 0.03, 0.24), (0, 0, 0), "M_WoodDark", 0.02))


def beam_x(name, x0, x1, hw, hh, zc, m, yc=FY, n=8):
    """Rounded-square beam along X with rounded ends; zc(x) bends it."""
    xs = [x0, x0 + 0.025, x0 + 0.07]
    xs += [x0 + 0.07 + (x1 - x0 - 0.14) * i / 6 for i in range(1, 6)]
    xs += [x1 - 0.07, x1 - 0.025, x1]
    sc = [0.55, 0.88] + [1.0] * (len(xs) - 4) + [0.88, 0.55]
    rings = []
    for x, s in zip(xs, sc):
        pts = S.ring_pts(n, hw * s, hh * s, 0.0, (0, 0), 4.0)
        rings.append([(x, yc + u, zc(x) + v) for (u, v, _) in pts])
    return S.loft(name, rings, m, True, True, 40, fan=True)


P.append(beam_x("topbeam", -0.92, 0.92, 0.085, 0.08, lambda x: TOPZ + 0.07 * (abs(x) / 0.92) ** 3, "M_WoodDark"))
# arched crest board with a brass medallion and a glowing violet rune
P.append(E.upright_prism("crest", E.arch_outline(0.5, 0.0, 0.11, 8, 0.0), 0.06, FY, 0.0, TOPZ + 0.05,
                         "M_WoodPlanks", 0.012))
P.append(S.lathe("medallion", [(0.0, -0.012), (0.05, -0.012), (0.056, 0.0), (0.05, 0.012), (0.0, 0.012)], 12,
                 (0, FY - 0.035, TOPZ + 0.095), "M_Brass", 40, axis=(0, -1, 0)))
P += pl.glyph("ingwaz", V((0, FY - 0.047, TOPZ + 0.095)), (1, 0, 0), (0, 0, 1), 0.06, 0.014, 0.008, M("RuneViolet"),
              "rune")

# --- rollers: the cream warp roll at the top, the cloth roll at the bottom, a brass ratchet --------------------------
WY, CY = FY + 0.07, FY + 0.09
P.append(S.lathe("warp_beam", [(0.0, -0.7), (0.048, -0.7), (0.048, 0.7), (0.0, 0.7)], 10, (0, WY, WZ), "M_WoodPlanks",
                 40, axis=(1, 0, 0)))
P.append(S.lathe("warp_roll", [(0.0, -HALF), (0.072, -HALF), (0.085, -HALF + 0.025), (0.085, HALF - 0.025),
                               (0.072, HALF), (0.0, HALF)], 12, (0, WY, WZ), "Thread", 40, axis=(1, 0, 0)))
P.append(S.lathe("cloth_beam", [(0.0, -0.72), (0.052, -0.72), (0.052, 0.72), (0.0, 0.72)], 10, (0, CY, CZ),
                 "M_WoodPlanks", 40, axis=(1, 0, 0)))
P.append(S.lathe("cloth_roll", [(0.0, -HALF), (0.095, -HALF), (0.11, -HALF + 0.02), (0.11, HALF - 0.02), (0.095, HALF),
                                (0.0, HALF)], 12, (0, CY, CZ), RED, 40, axis=(1, 0, 0)))
for (y, z) in ((WY, WZ), (CY, CZ)):
    for sx in (-1, 1):
        P.append(S.lathe("roller_cap", [(0.0, -0.02), (0.062, -0.02), (0.068, 0.0), (0.062, 0.02), (0.0, 0.025)], 8,
                         (sx * (PX + 0.115), y, z), "M_Brass", 40, axis=(sx, 0, 0)))
GXR = PX + PW / 2 + 0.022                     # ratchet wheel just outside the right post
P.append(E.gear("ratchet", 0.105, 8, 0.032, 0.035, 0.0, (GXR, CY, CZ), (1, 0, 0), "M_Brass"))
P.append(E.beam("pawl", (GXR, FY + 0.02, CZ + 0.21), (GXR, CY - 0.015, CZ + 0.1), 0.03, 0.03, "M_Brass", 0.008))

# --- warp, cloth, shed rod, heddle bar, shuttle ----------------------------------------------------------------------
STRIPES = [(RED, 0.08), (GOLD, 0.035), (TEAL, 0.07), (CREAM, 0.035), (VIOLET, 0.11), (CREAM, 0.035), (TEAL, 0.07),
           (GOLD, 0.035), (RED, 0.06)]
z = CZ                   # the first stripe starts inside the cloth roll
for k, (m, h) in enumerate(STRIPES):
    hh = h + (CLOTH_BOT - CZ if k == 0 else 0.0)
    P.append(rw.box("cloth", (2 * HALF, 0.03, hh), (0, FY, z + hh / 2), mat=S.mat(m)))
    if m == VIOLET:          # a band of gold diamonds on the front
        for i in range(6):
            dx = -HALF + 0.09 + (2 * HALF - 0.18) * i / 5
            P.append(E.poly_prism("diamond", [(0.0, -0.038), (0.036, 0.0), (0.0, 0.038), (-0.036, 0.0)], 0.008,
                                  (dx, FY - 0.016, z + hh / 2), (90, 0, 0), GOLD))
    z += hh
FELL = z
# warp: a cream sheet whose front is painted in thread strips (flat colours, so no outlines between them)
P.append(rw.box("warp", (2 * HALF - 0.02, 0.012, WZ - FELL), (0, FY, (WZ + FELL) / 2), mat=M("Thread")))
NT = 21
warp_face = E.sheet("warp_face", lambda u, v: (-HALF + 0.01 + u * (2 * HALF - 0.02), FY - 0.0075, FELL + v * (WZ - FELL)),
                    NT, 1, "Thread")
bpy.context.view_layer.update()
rw.set_mat_where(warp_face, rw.flat("WarpShade", "d6c49c", 0.9, 0.0),
                 lambda c, n: int((c.x + HALF - 0.01) / ((2 * HALF - 0.02) / NT)) % 2 == 1)
P.append(warp_face)
P.append(E.rod("shed_rod", (-PX + PW / 2, FY + 0.012, 1.44), (PX - PW / 2, FY + 0.012, 1.44), 0.018, 8, "M_WoodPlanks"))
P.append(E.rod("heddle_bar", (-PX - 0.03, FY - 0.1, 1.3), (PX + 0.03, FY - 0.1, 1.3), 0.02, 8, "M_WoodPlanks"))
for sx in (-1, 1):
    P.append(E.cbox("heddle_bracket", (0.06, 0.06, 0.08), (sx * PX, FY - PW / 2 - 0.028, 1.3), (0, 0, 0), "M_Brass",
                    0.012))
# the shuttle resting on the weaving edge, its red yarn running into the cloth
shc = V((0.12, FY - 0.012, FELL + 0.036))
sdir = V((math.cos(math.radians(6)), 0.0, math.sin(math.radians(6))))
P.append(pl.sausage("shuttle", [shc - sdir * 0.25, shc - sdir * 0.14, shc, shc + sdir * 0.14, shc + sdir * 0.25],
                    [0.008, 0.032, 0.038, 0.032, 0.008], 8, 1, S.mat("EndGrain"), (True, True), 1, True, 50,
                    scale_xy=(0.8, 1.0), up_hint=(0, 1, 0)))
P.append(E.rod("shuttle_yarn", tuple(shc - sdir * 0.07 + V((0, 0, 0.022))), tuple(shc + sdir * 0.07 + V((0, 0, 0.022))),
               0.02, 8, "YarnRed"))
P.append(E.tube("weft", [shc - sdir * 0.2, V((-0.2, FY - 0.03, FELL + 0.012)), V((-0.34, FY - 0.017, FELL - 0.006))],
                0.007, "YarnRed", 1, True, 2))

# --- the thread rack (right): six chunky spools on slanted pegs ----------------------------------------------------
RX, RY = 0.84, -0.06
P.append(E.rbox("rack_foot", (0.3, 0.34, 0.07), (RX, RY + 0.06, 0.035), (0, 0, 0), "M_WoodDark", 0.025))
rack = [E.cbox("rack_board", (0.29, 0.05, 1.08), (RX, RY + 0.13, 0.58), (0, 0, 0), "M_WoodPlanks", 0.02),
        S.lathe("rack_cap", [(0.0, 0.0), (0.06, 0.0), (0.075, 0.03), (0.06, 0.06), (0.0, 0.07)], 10,
                (RX, RY + 0.13, 1.12), "M_WoodDark", 40)]
SP_D = V((0.0, -0.58, 0.815)).normalized()
SPOOLS = (("YarnBlue", "YarnViolet"), ("YarnGold", "YarnCream"), ("YarnRed", "TealGlowSoft"))
for row, zr in enumerate((0.38, 0.64, 0.9)):
    for col, dx in enumerate((-0.072, 0.072)):
        root = V((RX + dx, RY + 0.105, zr))
        rack.append(E.rod("peg", tuple(root), tuple(root + SP_D * 0.135), 0.012, 5, "M_WoodDark"))
        sp = S.lathe("spool", [(0.0, 0.0), (0.05, 0.0), (0.05, 0.016), (0.043, 0.02), (0.045, 0.056), (0.043, 0.092),
                               (0.05, 0.096), (0.05, 0.112), (0.0, 0.112)], 6, tuple(root + SP_D * 0.016), "EndGrain",
                     40, axis=tuple(SP_D))
        base_pt = root + SP_D * 0.016
        bpy.context.view_layer.update()
        rw.set_mat_where(sp, S.mat(SPOOLS[row][col]),
                         lambda c, n, b=base_pt: 0.016 < (c - b).dot(SP_D) < 0.096 and abs(n.dot(SP_D)) < 0.75)
        rack.append(sp)
for o in rack:      # lean the board back a little
    E.deform(o, lambda p: V((p.x, p.y + 0.06 * (p.z / 1.2), p.z)))
    rw.smooth(o, 40)
P += rack

# --- the lantern (right end of the beam) ---------------------------------------------------------------------------
LX = 0.8
lan, light_pt = E.lantern((LX, FY, TOPZ - 0.02), kind="hang", scale=0.72)
P += lan

# --- the basket of golden reed fibre (left) --------------------------------------------------------------------------
BX, BY = -0.76, -0.38
bprof = [(0.0, 0.0), (0.135, 0.0), (0.16, 0.02), (0.186, 0.1), (0.205, 0.2), (0.213, 0.27), (0.194, 0.27),
         (0.182, 0.22), (0.0, 0.22)]
basket = S.lathe("basket", bprof, 14, (BX, BY, 0), "Wicker", 40)
bpy.context.view_layer.update()
rw.set_mat_where(basket, M("WickerDark"), lambda c, n: int((c.z + 0.012) / 0.05) % 2 == 1 and abs(n.z) < 0.75
                 and math.hypot(c.x - BX, c.y - BY) > 0.17)
P.append(basket)
P.append(E.ring("basket_rim", 0.205, 0.024, (BX, BY, 0.27), (0, 0, 1), "WickerDark", 14, 4))
# a fluffy heap of golden fibre, and three flat hanks of it draped over the rim
for (dx, dy, r, h) in ((0.0, 0.0, 0.2, 0.13), (-0.05, 0.05, 0.11, 0.19), (0.06, -0.04, 0.1, 0.16)):
    P.append(G.dome("fibre_heap", r, h, (BX + dx, BY + dy, 0.25), (0, 0, 1), "Fibre", 9, 2, 0.3, wall=False))
for k, a in enumerate((230, 300, 120)):
    d = G.radial(a, 1.0)
    pts = [V((BX, BY, 0.0)) + d * 0.13 + V((0, 0, 0.35)), V((BX, BY, 0.0)) + d * 0.215 + V((0, 0, 0.31)),
           V((BX, BY, 0.0)) + d * 0.232 + V((0, 0, 0.22))]
    P.append(G.ribbon("hank", pts, [0.07, 0.065, 0.05], V((0, 0, 1)).cross(d), "YarnGold" if k % 2 else "Fibre",
                      keel=0.15, thick=0.018, res=2))

# --- two finished pouches hanging from a brass hook (left end of the beam) ------------------------------------------
HX = -0.8
hook_bot = V((HX, FY, TOPZ - 0.2))
P.append(E.tube("hook", [(HX, FY, TOPZ - 0.04), (HX, FY, TOPZ - 0.16), hook_bot + V((0.0, -0.035, 0.0)),
                         hook_bot + V((0.0, -0.06, 0.05))], 0.014, "M_Brass", 1, True, 2))
POUCH = [(0.0, 0.0), (0.05, 0.004), (0.088, 0.03), (0.1, 0.085), (0.092, 0.14), (0.06, 0.18), (0.036, 0.195),
         (0.05, 0.218), (0.058, 0.238), (0.0, 0.23)]
for k, (dx, dy, top_z, m) in enumerate(((-0.03, -0.11, 1.42, POUCH_TEAL), (-0.01, 0.11, 1.34, "M_Leather"))):
    c = V((HX + dx, FY + dy, top_z - 0.238))
    pouch = [S.lathe("pouch", POUCH, 9, (0, 0, 0), m, 50)]
    pouch.append(E.ring("pouch_tie", 0.04, 0.012, (0, 0, 0.196), (0, 0, 1), "Twine" if k == 0 else "M_Brass", 8, 3))
    if k == 0:   # teal cloth pouch: gold band and a gold button
        bpy.context.view_layer.update()
        rw.set_mat_where(pouch[0], S.mat(GOLD), lambda cc, n: 0.075 < cc.z < 0.105)
        pouch.append(rw.cylinder("pouch_button", 0.022, 0.014, 8, (0, -0.098, 0.12), (90, 0, 0), S.mat("M_Brass")))
    else:        # leather pouch: a brass clasp and studs
        pouch.append(E.cbox("pouch_clasp", (0.05, 0.02, 0.04), (0, -0.096, 0.13), (0, 0, 0), "M_Brass", 0.006))
        for sx in (-1, 1):
            pouch.append(E.rivet("pouch_stud", (sx * 0.055, -0.08, 0.07), 0.014, "M_Brass", lo=True))
    G.turn(pouch, 0.0, c)
    G.xform(pouch, Matrix.Translation(c) @ Matrix.Rotation(math.radians(rnd.uniform(-8, 8)), 4, 'X')
            @ Matrix.Translation(-c))
    P += pouch
    P.append(E.tube("pouch_cord", [hook_bot + V((0.0, -0.03, 0.0)), c + V((0.0, 0.0, 0.25))], 0.013, "Twine", 1, False))

# --- the weaver's stool and a ball of yarn (front) -----------------------------------------------------------------
SX, SY = 0.04, -0.36
P.append(S.lathe("stool_seat", [(0.0, 0.37), (0.16, 0.37), (0.175, 0.385), (0.175, 0.415), (0.16, 0.43), (0.0, 0.43)], 14,
                 (SX, SY, 0), "M_WoodPlanks", 40))
P.append(S.lathe("stool_cushion", [(0.0, 0.42), (0.148, 0.42), (0.162, 0.44), (0.15, 0.475), (0.09, 0.492),
                                   (0.0, 0.496)], 14, (SX, SY, 0), CUSHION, 60))
P.append(E.ball("cushion_tuft", 0.02, (SX, SY, 0.494), "M_Brass", 8, 4, (1, 1, 0.6)))
for k in range(3):
    a = math.radians(90 + 120 * k + 30)
    d = V((math.cos(a), math.sin(a), 0.0))
    P.append(E.rod("stool_leg", tuple(V((SX, SY, 0.0)) + d * 0.18), tuple(V((SX, SY, 0.38)) + d * 0.1), 0.024, 7,
                   "M_WoodDark"))
YB = V((SX + 0.32, SY - 0.1, 0.075))
P.append(rw.ico("yarn_ball", 0.075, 1, tuple(YB), (0, 0, 0), (1, 1, 0.95), M("YarnViolet"), None, 60))
P.append(rw.torus("yarn_wrap", 0.072, 0.012, 12, 3, tuple(YB), (60, 0, 20), M("YarnViolet")))
P.append(E.tube("yarn_thread", [YB + V((-0.06, 0.02, -0.03)), V((SX + 0.18, SY - 0.02, 0.006)),
                                V((SX + 0.12, SY + 0.12, 0.006))], 0.007, "YarnViolet", 1, True, 3))

loom = E.join(P, "Loom", origin=(0, 0, 0))
rw.smooth(loom, 35)
rw.empty("LightPoint", tuple(light_pt))

# --- collision: one box around the whole station ---------------------------------------------------------------------
mn, mx = rw.bounds([loom])
E.col_box("Loom", (mx.x - mn.x - 0.04, mx.y - mn.y - 0.02, 1.95), ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.975))
S.preview_glass()
S.ground_centre([loom])
G.finish_env(ASSET, (2.0, 1.2, 2.0), 5000, nodes=("Loom", "LightPoint"),
             preview_glows={"LampGlow": ("e0962a", "ffcc66", 0.9), "TealGlowSoft": ("1fae9a", "3ff0d8", 0.6),
                            "RuneViolet": ("7d4fe0", "a066ff", 0.9)})
