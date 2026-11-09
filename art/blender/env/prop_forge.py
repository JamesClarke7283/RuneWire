"""prop_forge: "Emberwick Forge", a crafting station for the town plaza, about 2.6 (X) x 2.0 (Y) x 3.2 (Z) m.
Origin at the ground centre; the furnace mouth faces -Y.

A round stone furnace: an M_Stone drum (with a few proud M_StoneRough ashlar blocks) on a ring of chunky
M_StoneRough plinth stones, under a stepped brick-red dome. On the front is a big arched mouth framed by
brick voussoirs and jamb bricks, with a brass keystone carrying a glowing ember rune. Inside are a
soot-black recess with a glowing back wall (M_EmberGlow), a heap of glowing coals and three cartoon flames,
above a stone sill. A riveted brass hood crowns the dome, round at the bottom and squared at the top. It
carries a squared, slightly leaning brick chimney with a brass band, a corbelled soot-dark crown and a brass
pyramid cap on four corner posts (top at 3.2 m). A brass pressure gauge on a copper pipe sits on the drum.

Around it: on the left (-X), a big leather bellows (two plank boards with a pleated leather wedge, brass
studs, handles and a brass nozzle into the drum) on a plank stand. In front on the left, an anvil (dark
iron with a steel face and a horn) on a tree stump, with a hammer lying on it. In front on the right, a
wooden quench bucket with iron hoops, a bail handle, water and a pair of tongs. A coal heap sits at the back
right.

Nodes: Forge (all static geometry) and the empty LightPoint (in the furnace mouth, above the coals).
Collision (-colonly boxes): Col_Furnace_0 (drum, dome and hood), Col_Chimney_0, Col_Anvil_0 (stump and
anvil), Col_Bellows_0 and Col_Bucket_0.
"""
import math
import os
import random
import sys

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stationlib as S  # noqa: E402

E, rw, pl, V, M = S.E, S.rw, S.pl, S.V, S.M
ASSET = "prop_forge"
S.reset()
rnd = random.Random(11)
S.preview_glow("M_EmberGlow", "c8661c", "ff8a2a", 1.6)   # preview renders only; Godot uses its own glow

P = []
FX, FY = 0.24, 0.12        # furnace axis
R = 0.72                   # drum radius
Y_FRONT = FY - R           # front of the drum
SILL, SPRING, MW = 0.32, 0.66, 0.72    # mouth: sill height, arch spring height, width (rise = MW / 2)
BELT = 1.17                # belt course bottom
COURSES = [(0.70, 1.29, 1.41), (0.59, 1.41, 1.53), (0.47, 1.53, 1.65)]   # brick dome: radius, z0, z1
HOOD_Z = 1.58


def drum_pt(x, z, out=0.0):
    """Point on the drum's front surface at (x, z), pushed `out` along the outward normal; and that normal."""
    dx = x - FX
    dy = -math.sqrt(max(R * R - dx * dx, 1e-6))
    n = V((dx / R, dy / R, 0.0))
    return V((FX + dx, FY + dy, z)) + n * out, n


# --- furnace: stone drum + stepped brick dome (one lathe), arched mouth carved in ------------------------------
prof = [(0.0, 0.0), (R, 0.0), (R, BELT + 0.06)]
for (r, z0, z1) in COURSES:
    prof += [(r, z0), (r, z1 - 0.035), (r - 0.035, z1)]
prof.append((0.0, COURSES[-1][2]))
furnace = S.lathe("furnace", prof, 20, (FX, FY, 0), "M_Stone", 40)
bpy.context.view_layer.update()
rw.set_mat_where(furnace, M("Brick"), lambda c, n: c.z > BELT + 0.07)
rw.set_mat_where(furnace, M("BrickDark"), lambda c, n: c.z > COURSES[2][1] - 0.01)
cut = E.upright_prism("mouthcut", E.arch_outline(MW, SPRING, MW / 2, 10, SILL), 0.74, Y_FRONT + 0.06, FX, 0,
                      M("Soot"))
S.carve(furnace, [cut])
bpy.context.view_layer.update()
BACK = Y_FRONT + 0.43      # back wall of the recess


def in_mouth(c):
    if abs(c.x - FX) > MW / 2 + 0.006 or c.z < SILL - 0.01 or c.z > SPRING + MW / 2 + 0.01:
        return False
    ys = FY - math.sqrt(max(R * R - (c.x - FX) ** 2, 1e-6))
    return ys + 0.02 < c.y < BACK + 0.01


rw.set_mat_where(furnace, M("Soot"), lambda c, n: in_mouth(c))
rw.set_mat_where(furnace, "M_EmberGlow", lambda c, n: in_mouth(c) and n.y < -0.7 and c.y > BACK - 0.05)
rw.smooth(furnace, 40)
P.append(furnace)

# chunky plinth stones around the foot of the drum
NP = 11
for i in range(NP):
    a = 2 * math.pi * (i + rnd.uniform(-0.1, 0.1)) / NP + 0.2
    h = rnd.uniform(0.24, 0.29)
    w = 2 * math.pi * (R + 0.05) / NP * rnd.uniform(0.86, 0.94)
    dep = rnd.uniform(0.22, 0.27)
    c = (FX + math.cos(a) * (R + 0.03), FY + math.sin(a) * (R + 0.03), h / 2)
    P.append(E.cbox("plinth", (w, dep, h), c, (0, 0, math.degrees(a) + 90 + rnd.uniform(-4, 4)), "M_StoneRough", 0.035))
# a few big ashlar blocks set proud of the drum (cartoon masonry hints), away from the mouth
for (deg_, z, w, h) in ((-160, 0.62, 0.3, 0.17), (-20, 0.5, 0.26, 0.15), (-55, 0.98, 0.28, 0.15), (40, 0.75, 0.3, 0.17),
                        (95, 0.95, 0.26, 0.15), (150, 0.86, 0.28, 0.16), (-115, 1.0, 0.24, 0.14)):
    a = math.radians(deg_)
    n = V((math.cos(a), math.sin(a), 0.0))
    P.append(pl.obox("ashlar", (w, 0.06, h), tuple(V((FX, FY, z)) + n * (R + 0.005)), (-n.y, n.x, 0.0), (0, 0, 1),
                     "M_StoneRough"))
# belt course between the drum and the dome
P.append(S.lathe("belt", [(R - 0.03, BELT), (R + 0.07, BELT + 0.01), (R + 0.08, BELT + 0.11), (R - 0.03, BELT + 0.12)],
                 20, (FX, FY, 0), "M_StoneRough", 40))

# --- the mouth: sill, jamb bricks, voussoirs, brass keystone with an ember rune -----------------------------------
P.append(E.cbox("sill", (MW + 0.3, 0.26, 0.08), (FX, Y_FRONT - 0.06, SILL - 0.035), (0, 0, 0), "M_StoneRough", 0.025))
for sx in (-1, 1):
    zc = SILL + 0.005
    for k, (w, h) in enumerate(((0.17, 0.165), (0.12, 0.165))):
        if sx > 0:
            w = 0.29 - w
        x = FX + sx * (MW / 2 + w / 2 + 0.006)
        z = zc + h / 2
        zc += h + 0.008
        p, n = drum_pt(x, z, 0.06 - 0.08)
        t = V((-n.y, n.x, 0.0))
        P.append(pl.obox("jamb", (w, 0.16, h), tuple(p), tuple(t), (0, 0, 1), M("Brick" if (k + sx) % 2 else "BrickLight"),
                         bevel=0.018, bevel_segments=1))
NV = 9
for i in range(NV):
    a = math.pi * (i + 0.5) / NV
    d = V((math.cos(a), 0.0, math.sin(a)))
    key = i == NV // 2
    ri = MW / 2 + 0.006
    ro = ri + (0.2 if key else 0.15 + rnd.uniform(-0.012, 0.012))
    mid = V((FX, 0.0, SPRING)) + d * ((ri + ro) / 2)
    proud = 0.1 if key else 0.06
    D = 0.16
    p, n = drum_pt(mid.x, mid.z, proud - D / 2)
    w = (math.pi * (ri + ro) / 2 / NV) * (1.15 if key else 0.86)
    m = "M_Brass" if key else M("Brick" if i % 2 else "BrickLight")
    P.append(pl.obox("voussoir", (ro - ri, w, D), tuple(p), tuple(d), tuple(n), S.mat(m), bevel=0.018,
                     bevel_segments=1))
    if key:
        face = p + n * (D / 2)
        P += E.glyph(0, 0.13, tuple(face - n * 0.002), tuple(n), M("ForgeGlow"), stroke=0.16, depth=0.014)
# glowing coals heaped on the hearth, a few spilling onto the sill
for i in range(12):
    x = FX + rnd.uniform(-0.28, 0.28)
    y = rnd.uniform(Y_FRONT + 0.07, BACK - 0.06)
    r = rnd.uniform(0.05, 0.08)
    heap = 0.07 * (1 - abs(x - FX) / 0.36) * (y - Y_FRONT) / 0.43
    m = ("M_EmberGlow", "ForgeGlow", "Coal")[i % 3]
    P.append(rw.ico("coal", r, 1, (x, y, SILL + r * 0.45 + heap), (rnd.uniform(0, 90), rnd.uniform(0, 90), 0),
                    (1.0, 1.0, 0.75), S.mat(m), None, 0))
for (x, y) in ((-0.2, Y_FRONT - 0.1), (0.15, Y_FRONT - 0.13)):
    P.append(rw.ico("coal", 0.042, 1, (FX + x, y, SILL + 0.02), (20, 40, 0), (1.0, 1.0, 0.7), M("Coal"), None, 0))
for (x, y, h, r, m) in ((-0.15, BACK - 0.1, 0.34, 0.08, "ForgeGlow"), (0.02, BACK - 0.07, 0.46, 0.095, "FlameGold"),
                        (0.18, BACK - 0.12, 0.28, 0.07, "ForgeGlow")):
    P.append(S.flame("flame", (FX + x, y, SILL + 0.03), h, r, m, 8, lean=(0.0, -0.05)))

# --- brass pressure gauge on the drum (front left), fed by a copper pipe -----------------------------------------
ga = math.radians(-128)
gn = V((math.cos(ga), math.sin(ga), 0.0))
gp = V((FX, FY, 0.9)) + gn * R
P.append(S.lathe("gauge", [(0.0, -0.02), (0.1, -0.02), (0.11, 0.0), (0.11, 0.05), (0.095, 0.065), (0.0, 0.065)], 12,
                 tuple(gp), "M_Brass", 40, axis=tuple(gn)))
P.append(S.lathe("dial", [(0.0, 0.0), (0.085, 0.0), (0.085, 0.012), (0.0, 0.012)], 12, tuple(gp + gn * 0.056), "Dial",
                 40, axis=tuple(gn)))
tip = gp + gn * 0.072 + V((0, 0, 1)) * 0.06 + V((-gn.y, gn.x, 0)) * 0.03
P.append(E.beam("needle", tuple(gp + gn * 0.072), tuple(tip), 0.018, 0.01, "Needle", 0.0, up=tuple(gn)))
P.append(E.rod("gauge_pipe", tuple(gp + V((0, 0, -0.1)) + gn * 0.02), tuple(gp + V((0, 0, -0.36)) + gn * 0.02), 0.022,
               8, "M_Copper"))

# --- brass hood on the dome: round at the bottom, squared at the top to carry the chimney ------------------------
HOOD = [(0.4, 0.0, 2.0), (0.52, 0.0, 2.0), (0.555, 0.03, 2.0), (0.535, 0.065, 2.0), (0.44, 0.13, 2.6), (0.35, 0.24, 3.4),
        (0.3, 0.33, 5.0), (0.295, 0.38, 5.0), (0.32, 0.39, 5.0), (0.32, 0.46, 5.0), (0.27, 0.47, 5.0)]
P.append(S.loft("hood", [S.ring_pts(16, r, r, HOOD_Z + z, (FX, FY), p) for (r, z, p) in HOOD], "M_Brass", False, False,
                40))
for i in range(6):
    a = 2 * math.pi * (i + 0.5) / 6
    P.append(E.rivet("rivet", (FX + math.cos(a) * 0.55, FY + math.sin(a) * 0.55, HOOD_Z + 0.035), 0.026, "M_Copper",
                     lo=True))

# --- chimney: squared brick stack, brass band, corbelled soot-dark crown, brass pyramid cap on corner posts --------
CZ = HOOD_Z + 0.4
SQ = 5.0
CH = [S.loft("chimney", [S.ring_pts(16, h, h, z, (FX, FY), SQ) for (h, z) in ((0.27, CZ), (0.262, 2.3), (0.255, 2.55),
                                                                               (0.25, 2.76))], M("Brick"), False, False, 40)]
CH.append(S.loft("band", [S.ring_pts(16, h, h, z, (FX, FY), SQ) for (h, z) in ((0.25, 2.33), (0.282, 2.33), (0.282, 2.41),
                                                                               (0.25, 2.41))], "M_Brass", False, False, 40))
crown = S.loft("crown", [S.ring_pts(16, h, h, z, (FX, FY), SQ) for (h, z) in ((0.245, 2.72), (0.3, 2.74), (0.3, 2.82),
                                                                             (0.33, 2.83), (0.33, 2.93), (0.21, 2.94))],
               M("BrickDark"), False, True, 30, fan=True)
bpy.context.view_layer.update()
rw.set_mat_where(crown, M("Soot"), lambda c, n: n.z > 0.9 and c.z < 2.945 and max(abs(c.x - FX), abs(c.y - FY)) < 0.215)
CH.append(crown)
for sx in (-1, 1):
    for sy in (-1, 1):
        CH.append(E.cbox("cap_post", (0.05, 0.05, 0.1), (FX + sx * 0.25, FY + sy * 0.25, 2.985), (0, 0, 0), "M_Brass",
                         0.012))
cap = rw.cone("cap", 0.55, 0.0, 0.17, 4, (FX, FY, 3.115), (0, 0, 45), S.mat("M_Brass"))
CH.append(cap)
CH.append(E.cbox("cap_rim", (0.76, 0.76, 0.04), (FX, FY, 3.03), (0, 0, 0), "M_Brass", 0.012))


def lean(p):
    t = max(0.0, (p.z - CZ) / (3.2 - CZ))
    return V((p.x - 0.03 * t * t, p.y + 0.07 * t * t, p.z))


for o in CH:
    E.deform(o, lean)
    rw.smooth(o, 30)
P += CH

# --- bellows on a low stand (-X): a wedge of two boards and pleated leather, nozzle into the drum ----------------
BX0, BL, BW, BY = FX - R - 0.07, 0.72, 0.54, FY + 0.14     # narrow (nozzle) end x, length toward -X, width, centre y
BZ0, TH, G0, LIFT = 0.5, 0.055, 0.07, 0.36                # bottom board z, board thickness, gap at hinge, extra gap at the end


def pear(n=20):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        cx, cy = math.cos(t), math.sin(t)
        s = 0.24 + 0.76 * ((cx + 1) / 2) ** 0.6
        pts.append(((cx + 1) / 2 * BL, cy * BW / 2 * s))   # u = distance from the narrow end
    return pts


OL = pear()
UC = 0.58 * BL
ZB, ZT = BZ0 + TH, BZ0 + TH + G0      # bag bottom / top board bottom (at the hinge)


def bx(u):
    return BX0 - u


def bellows_lift(p):
    u = max(0.0, (BX0 - p.x) / BL)
    f = min(1.0, max(0.0, (p.z - ZB) / G0))
    return V((p.x, p.y, p.z + LIFT * u * f))


BEL = []
for z0 in (BZ0, ZT):
    BEL.append(S.loft("board", [[(bx(u), BY + v, z0) for (u, v) in OL], [(bx(u), BY + v, z0 + TH) for (u, v) in OL]],
                      "M_WoodPlanks", True, True, 30))
rings = []
for (f, s) in ((0.0, 0.9), (0.17, 0.82), (0.33, 1.0), (0.5, 0.82), (0.67, 1.0), (0.83, 0.82), (1.0, 0.9)):
    z = ZB + G0 * f
    rings.append([(bx(UC + (u - UC) * s), BY + v * s, z) for (u, v) in OL])
BEL.append(S.loft("bag", rings, "M_Leather", False, False, 25))
for i in (2, 5, 8, 12, 15, 18):
    u, v = OL[i]
    BEL.append(E.rivet("stud", (bx(UC + (u - UC) * 0.82), BY + v * 0.82, ZT + TH + 0.004), 0.024, "M_Brass", lo=True))
BEL.append(E.ball("valve", 0.07, (bx(BL * 0.6), BY, ZT + TH), "M_Brass", 10, 4, (1, 1, 0.3)))
for (z, dz) in ((ZT + TH * 0.5, 0.02), (BZ0 + TH * 0.5, -0.02)):
    BEL.append(E.rod("handle", (bx(BL - 0.04), BY, z), (bx(BL + 0.08), BY, z + dz), 0.026, 8, "M_WoodDark"))
    BEL.append(E.ball("knob", 0.042, (bx(BL + 0.09), BY, z + dz), "M_Brass", 8, 6))
for o in BEL:
    E.deform(o, bellows_lift)
    rw.smooth(o, 30)
P += BEL
ZN = BZ0 + TH + G0 * 0.5
P.append(S.lathe("nozzle", [(0.07, -0.03), (0.07, 0.02), (0.042, 0.09), (0.034, 0.13), (0.046, 0.14), (0.046, 0.17),
                            (0.0, 0.17)], 12, (BX0 - 0.03, BY, ZN), "M_Brass", 40, axis=(1, 0, 0)))
P.append(S.lathe("tuyere", [(0.0, -0.02), (0.1, -0.02), (0.1, 0.01), (0.08, 0.025), (0.0, 0.025)], 12,
                 (FX - math.sqrt(R * R - (BY - FY) ** 2) + 0.005, BY, ZN), "M_Brass", 40, axis=(-1, 0, 0)))
for u in (0.22, 0.8):
    half = BW / 2 * (0.24 + 0.76 * u ** 0.6) * 0.8
    P.append(E.cbox("stand", (0.11, 2 * half, BZ0 - 0.07), (bx(u * BL), BY, (BZ0 + 0.07) / 2), (0, 0, 0), "M_WoodDark",
                    0.02))
    P.append(E.cbox("stand_foot", (0.2, 2 * half + 0.14, 0.07), (bx(u * BL), BY, 0.035), (0, 0, 0), "M_WoodDark", 0.02))
P.append(E.cbox("stand_rail", (BL * 0.62, 0.06, 0.08), (bx(BL * 0.51), BY, 0.2), (0, 0, 0), "M_WoodDark", 0.015))

# --- anvil on a tree stump (front left), hammer on top --------------------------------------------------------------
AX, AY, AROT = -0.74, -0.74, 196.0
ST = 0.46


def root_wob(a):
    return 0.13 * max(0.0, math.cos(4 * a + 0.5)) ** 3


stump = S.loft("stump", [S.ring_pts(12, 0.28, 0.28, 0.0, (AX, AY), 2.0, 0.0, root_wob),
                         S.ring_pts(12, 0.245, 0.245, 0.08, (AX, AY), 2.0, 0.0, lambda a: root_wob(a) * 0.3),
                         S.ring_pts(12, 0.228, 0.228, 0.25, (AX, AY)),
                         S.ring_pts(12, 0.225, 0.225, ST - 0.02, (AX, AY)),
                         S.ring_pts(12, 0.212, 0.212, ST, (AX, AY))], "M_Bark", False, True, 50, fan=True)
bpy.context.view_layer.update()
rw.set_mat_where(stump, M("EndGrain"), lambda c, n: n.z > 0.7)
P.append(stump)
AN = [S.loft("anvil", [S.ring_pts(12, 0.18, 0.13, ST, (0, 0), 5.0), S.ring_pts(12, 0.18, 0.13, ST + 0.04, (0, 0), 5.0),
                       S.ring_pts(12, 0.12, 0.085, ST + 0.075, (0, 0), 4.0),
                       S.ring_pts(12, 0.09, 0.068, ST + 0.14, (0, 0), 4.0),
                       S.ring_pts(12, 0.14, 0.078, ST + 0.18, (0, 0), 4.0),
                       S.ring_pts(12, 0.2, 0.09, ST + 0.2, (-0.02, 0), 5.0)], "M_DarkMetal", True, True, 40)]
AT = ST + 0.3                                        # anvil face top
AN.append(E.rbox("anvil_face", (0.48, 0.19, 0.1), (-0.02, 0, AT - 0.05 - 0.012), (0, 0, 0), "M_DarkMetal", 0.02))
AN.append(E.cbox("anvil_top", (0.46, 0.17, 0.024), (-0.02, 0, AT - 0.006), (0, 0, 0), "M_Steel", 0.007))
AN.append(S.lathe("horn", [(0.0, -0.01), (0.075, -0.01), (0.07, 0.05), (0.047, 0.15), (0.022, 0.25), (0.0, 0.27)], 10,
                  (0.21, 0, AT - 0.055), "M_DarkMetal", 50, axis=(1, 0, -0.14)))
AN.append(rw.box("hardy", (0.035, 0.035, 0.004), (-0.19, 0.02, AT + 0.0), mat=M("Soot")))
hh0 = V((0.05, -0.05, AT + 0.02))
hh1 = V((-0.3, 0.1, AT + 0.02))
AN.append(E.rod("hammer_handle", tuple(hh0), tuple(hh1), 0.02, 8, "M_WoodDark"))
hd = (hh1 - hh0).normalized()
AN.append(pl.obox("hammer_head", (0.075, 0.18, 0.08), tuple(hh0 + V((0, 0, 0.02))), tuple(hd), (0, 0, 1), "M_Steel",
                  bevel=0.012, bevel_segments=1))
E.place(AN, (AX, AY, 0), (0, 0, AROT))
P += AN

# --- quench bucket with water and tongs (front right) ----------------------------------------------------------------
BUX, BUY = 0.98, -0.7
bucket = S.lathe("bucket", [(0.0, 0.0), (0.16, 0.0), (0.172, 0.03), (0.186, 0.045), (0.186, 0.09), (0.176, 0.1),
                            (0.196, 0.27), (0.21, 0.28), (0.21, 0.33), (0.2, 0.335), (0.203, 0.38), (0.186, 0.38),
                            (0.186, 0.33), (0.0, 0.33)], 10, (BUX, BUY, 0), "M_WoodPlanks", 40)
bpy.context.view_layer.update()
rw.set_mat_where(bucket, M("Iron"), lambda c, n: (0.035 < c.z < 0.1 or 0.27 < c.z < 0.336) and abs(n.z) < 0.8
                 and math.hypot(c.x - BUX, c.y - BUY) > 0.17)
rw.set_mat_where(bucket, M("Water"), lambda c, n: n.z > 0.9 and c.z < 0.335 and math.hypot(c.x - BUX, c.y - BUY) < 0.18)
P.append(bucket)
for sx in (-1, 1):
    P.append(E.ball("ear", 0.03, (BUX + sx * 0.205, BUY, 0.33), "Iron", 6, 4))
P.append(E.tube("bail", [(BUX - 0.21, BUY, 0.33), (BUX - 0.15, BUY + 0.05, 0.5), (BUX, BUY + 0.07, 0.56),
                         (BUX + 0.15, BUY + 0.05, 0.5), (BUX + 0.21, BUY, 0.33)], 0.012, "Iron", 1, True, 3))
piv = V((BUX + 0.02, BUY - 0.1, 0.42))
for s in (-1, 1):
    a = piv + V((-0.06 + 0.03 * s, 0.1, -0.26))          # jaw end, in the water
    b = piv + V((0.16 + 0.06 * s, -0.22, 0.36))          # handle end, leaning out toward the front right
    P.append(E.beam("tongs", tuple(a), tuple(b), 0.026, 0.018, "Iron", 0.006, up=(-1, 0, 0)))
P.append(E.ball("tongs_pivot", 0.026, tuple(piv), "Iron", 8, 4))

# --- coal heap (back right) -------------------------------------------------------------------------------------
for i in range(7):
    a = rnd.uniform(0, 2 * math.pi)
    d = rnd.uniform(0, 0.17)
    r = rnd.uniform(0.07, 0.11)
    P.append(rw.ico("coalheap", r, 1, (0.92 + math.cos(a) * d, 0.62 + math.sin(a) * d, r * 0.76 + 0.12 * (1 - d / 0.17)),
                    (rnd.uniform(0, 90), rnd.uniform(0, 90), 0), (1.0, 1.0, 0.75), M("Coal"), None, 0))

forge = E.join(P, "Forge", origin=(0, 0, 0))
rw.smooth(forge, 35)
rw.empty("LightPoint", (FX, Y_FRONT + 0.22, SILL + 0.26))

# --- collision -----------------------------------------------------------------------------------------------------
HT = HOOD_Z + 0.47
E.col_box("Furnace", (2 * (R + 0.1), 2 * (R + 0.1), HT), (FX, FY, HT / 2))
E.col_box("Chimney", (0.7, 0.7, 3.2 - HT), (FX - 0.01, FY + 0.03, (HT + 3.2) / 2))
E.col_box("Anvil", (0.62, 0.6, AT), (AX, AY, AT / 2), (0, 0, AROT))
E.col_box("Bellows", (BL + 0.2, BW + 0.04, ZT + TH + LIFT), (BX0 - BL / 2 - 0.05, BY, (ZT + TH + LIFT) / 2))
E.col_box("Bucket", (0.44, 0.44, 0.4), (BUX, BUY, 0.2))
S.ground_centre([forge])
S.finish(ASSET, (2.6, 2.0, 3.2), 6000, nodes=("Forge", "LightPoint"))
