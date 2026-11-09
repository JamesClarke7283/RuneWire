"""bld_factory_shed: the Gearworks open-sided factory shed (20 x 14 x 9 m).

Signal-orange steel I-beam columns and four steel trusses carry a corrugated roof (grey M_PaintedMetal__8a8f95
sheets patched with M_Rust) with a ridge ventilator. The walls at +X and +Y are closed (brick dado, corrugated
cladding, factory windows, a big sliding door); the front (-Y) and the left side (-X) stand open, with hazard stripes
along the floor edges and column feet. Inside: a yellow overhead crane with a hook block, six hanging lamps
(LightPoint_n empties) and pipework. A big brass gear emblem with a glowing core sits on the clad front gable.
Collision is only on the columns, the closed walls (plus the barrels tucked in the back corner) and the roof, so the
player can walk in. Origin at the ground centre, front facing -Y.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_factory_shed"
B.reset()
P = []
L = B.Lights()
rnd = random.Random(20)

SHEET, RUST = "M_PaintedMetal__8a8f95", "M_Rust"
ORANGE = "M_PaintedMetal"            # library default tint: signal orange
CX = 9.4                             # column lines at x = +-CX
CYS = (-6.4, -2.13, 2.13, 6.4)       # truss / column rows along Y
ZE = 5.2                             # column tops (the truss bottom chord sits on them)
RX, RY = 10.1, 7.05                  # roof half extents (eaves / gable overhang)
ZR = 8.75                            # ridge (top of the sheets)
ZEV = 5.6                            # eave (top of the sheets at x = +-RX)
WX, WY = 9.62, 6.62                  # outer faces of the closed walls (+X, +Y)


def roof_z(x):
    return ZR - (ZR - ZEV) * abs(x) / RX


# ---------------------------------------------------------------- floor slab with hazard edges
P.append(E.rbox("floor", (2 * CX + 0.6, 2 * 6.4 + 0.6, 0.3), (0, 0, -0.1), m="M_Stone", r=0.05))
for k in range(16):
    x0 = -CX + 2 * CX * k / 16
    P.append(rw.box("hazfloor", (2 * CX / 16 - 0.02, 0.3, 0.03), (x0 + CX / 16, -6.48, 0.06),
                    mat=B.mat("HazardYellow" if k % 2 == 0 else "HazardBlack")))
for k in range(11):
    y0 = -6.4 + 12.8 * k / 11
    P.append(rw.box("hazfloor", (0.3, 12.8 / 11 - 0.02, 0.03), (-CX - 0.08, y0 + 6.4 / 11, 0.06),
                    mat=B.mat("HazardYellow" if k % 2 == 0 else "HazardBlack")))

# ---------------------------------------------------------------- columns (I-beams) with base plates and hazard feet
for sx in (-1, 1):
    for y in CYS:
        x = sx * CX
        P.append(B.ibeam("column", (x, y, 0.05), (x, y, ZE + 0.02), 0.44, 0.34, 0.06, 0.06, ORANGE, up=(1, 0, 0)))
        P.append(E.rbox("baseplate", (0.7, 0.62, 0.1), (x, y, 0.08), m="M_DarkMetal", r=0.02))
        for (bx, by) in ((-0.25, -0.22), (0.25, -0.22), (-0.25, 0.22), (0.25, 0.22)):
            P.append(rw.cylinder("bolt", 0.035, 0.08, 6, (x + bx, y + by, 0.16), (0, 0, 0), E.mat("M_Steel")))
        P.append(E.rbox("capplate", (0.55, 0.45, 0.06), (x, y, ZE), m="M_DarkMetal", r=0.015))
        open_col = sx < 0 or y < -6.0
        if open_col:
            for k in range(4):
                P.append(rw.box("hazcol", (0.47, 0.37, 0.24), (x, y, 0.3 + 0.25 * k), mat=B.mat("HazardYellow" if k % 2 == 0 else "HazardBlack")))

# ---------------------------------------------------------------- trusses, purlins
TOPC = 0.44                          # top chord centre sits this far below the sheets (clear of the corrugation valleys)
WEBX = (2.35, 4.7, 7.05)


def chord_z(x):
    return roof_z(x) - TOPC - 0.04


for y in CYS:
    front = y < -6.0
    P.append(B.ibeam("botchord", (-CX - 0.15, y, ZE + 0.1), (CX + 0.15, y, ZE + 0.1), 0.26, 0.2, 0.045, 0.045, "M_Steel", up=(0, 0, 1)))
    for sx in (-1, 1):
        P.append(B.ibeam("topchord", (sx * (CX + 0.5), y, chord_z(CX + 0.5) - 0.06), (0, y, chord_z(0.0)), 0.26, 0.2, 0.045, 0.045,
                         "M_Steel", up=(0, 0, 1)))
        for i, wx in enumerate(WEBX):
            x = sx * wx
            P.append(B.bar("web", (x, y, ZE + 0.18), (x, y, chord_z(wx) - 0.08), 0.11, 0.11, "M_Steel"))
            x2 = sx * (WEBX[i + 1] if i + 1 < len(WEBX) else CX)
            P.append(B.bar("web", (x, y, ZE + 0.18), (x2, y, chord_z(abs(x2)) - 0.06), 0.09, 0.09, "M_Steel"))
            P.append(E.rbox("gusset", (0.34, 0.06, 0.3), (x, y, ZE + 0.14), m="M_DarkMetal", r=0.012))
        P.append(B.bar("web", (0.0, y, ZE + 0.18), (sx * WEBX[0], y, chord_z(WEBX[0]) - 0.06), 0.09, 0.09, "M_Steel"))
    P.append(B.bar("kingpost", (0.0, y, ZE + 0.18), (0.0, y, chord_z(0.0) - 0.06), 0.13, 0.13, "M_Steel"))
    P.append(E.rbox("ridgegusset", (0.5, 0.07, 0.4), (0, y, chord_z(0.0) - 0.12), m="M_DarkMetal", r=0.015))
    if front:
        P += B.hazard_bar((-CX + 0.3, y - 0.14, ZE + 0.1), (CX - 0.3, y - 0.14, ZE + 0.1), 0.06, 0.28, 14, up=(0, 0, 1))
for sx in (-1, 1):
    for px in (1.6, 4.1, 6.6, 9.0):
        x = sx * px
        z = roof_z(px) - 0.27
        P.append(B.bar("purlin", (x, -RY + 0.15, z), (x, RY - 0.15, z), 0.12, 0.16, "M_DarkMetal"))
# eave beams along the long sides
for sx in (-1, 1):
    P.append(B.ibeam("eavebeam", (sx * CX, -6.6, ZE + 0.1), (sx * CX, 6.6, ZE + 0.1), 0.3, 0.2, 0.05, 0.05, ORANGE, up=(0, 0, 1)))

# ---------------------------------------------------------------- corrugated roof: sheet panels, some rusty, plus a ridge cap
NP = 6
for sx in (-1, 1):
    slope = V((sx * RX, 0, ZEV - ZR))
    nrm = V((sx * (ZR - ZEV), 0, RX)).normalized()
    for k in range(NP):
        ya = -RY + 2 * RY * k / NP - (0.04 if k else 0)
        yb = -RY + 2 * RY * (k + 1) / NP + 0.04 * (k < NP - 1)
        rusty = (sx, k) in ((1, 1), (-1, 4), (1, 4))
        lift = rnd.uniform(-0.015, 0.025) + 0.03 * (k % 2)
        prof = B.corrugate((0, ya, ZR - 0.06 + lift), (0, yb, ZR - 0.06 + lift), tuple(nrm), 0.065, 0.75, 6)
        P.append(B.sweep("sheet", prof, tuple(slope * 1.0), 0.05, RUST if rusty else SHEET, smooth=60))
cap = [(-0.55, ZR - 0.12), (-0.2, ZR + 0.06), (0.2, ZR + 0.06), (0.55, ZR - 0.12)]
P.append(B.sweep("ridgecap", [(x, -RY - 0.05, z + 0.02) for (x, z) in cap], (0, 2 * RY + 0.1, 0), -0.05, SHEET, smooth=40))
# ridge ventilator: louvred box with its own little roof
MV0, MV1 = -3.6, 3.6
P.append(E.rbox("ventbase", (1.6, MV1 - MV0, 0.18), (0, 0, ZR + 0.12), m="M_DarkMetal", r=0.03))
for sx in (-1, 1):
    for k in range(3):
        P.append(rw.box("louvre", (0.06, MV1 - MV0 - 0.2, 0.09), (sx * 0.74, 0, ZR + 0.3 + 0.13 * k), (0, sx * 30, 0), mat=E.mat("IronDark")))
for y in (MV0 + 0.05, 0.0, MV1 - 0.05):
    for sx in (-1, 1):
        P.append(rw.box("ventpost", (0.1, 0.1, 0.55), (sx * 0.76, y, ZR + 0.45), mat=E.mat("M_DarkMetal")))
vroof = [(-1.1, ZR + 0.6), (0.0, ZR + 0.86), (1.1, ZR + 0.6)]
P.append(B.sweep("ventroof", [(x, MV0 - 0.15, z) for (x, z) in vroof], (0, MV1 - MV0 + 0.3, 0), -0.06, SHEET, smooth=40))

# ---------------------------------------------------------------- closed walls (+X long side, +Y back gable)
# brick dados
P.append(E.rbox("dadoR", (0.36, 2 * 6.62, 1.3), (WX - 0.18, 0, 0.5), m="M_Stone", r=0.05))
P.append(E.rbox("dadoB", (2 * WX, 0.36, 1.3), (0, WY - 0.18, 0.5), m="M_Stone", r=0.05))
P.append(E.rbox("dadocapR", (0.46, 2 * 6.66, 0.12), (WX - 0.18, 0, 1.18), m="M_StoneRough", r=0.03))
P.append(E.rbox("dadocapB", (2 * WX + 0.04, 0.46, 0.12), (0, WY - 0.18, 1.18), m="M_StoneRough", r=0.03))
# corrugated cladding panels (vertical ribs)
CL0 = 1.22
for k in range(5):
    ya, yb = -6.62 + 13.24 * k / 5, -6.62 + 13.24 * (k + 1) / 5 + 0.05
    prof = B.corrugate((WX, ya, CL0), (WX, yb, CL0), (1, 0, 0), 0.06, 0.7, 6)
    P.append(B.sweep("cladR", prof, (0, 0, roof_z(WX) - 0.14 - CL0), 0.05, RUST if k == 3 else SHEET, smooth=60))
for k in range(7):
    xa, xb = -WX + 2 * WX * k / 7, -WX + 2 * WX * (k + 1) / 7 + 0.05
    prof = B.corrugate((xb, WY, CL0), (xa, WY, CL0), (0, 1, 0), 0.06, 0.7, 6)
    P.append(B.sweep("cladB", prof, (0, 0, ZE + 0.15 - CL0), 0.05, RUST if k == 1 else SHEET, smooth=60))
# back gable triangle (clad, with vertical ribs) and the clad front gable carrying the gear emblem
for (y, d, hx, z0) in ((WY - 0.04, 0.08, WX - 0.02, ZE + 0.13), (CYS[0] - 0.22, 0.08, CX + 0.1, ZE + 0.26)):
    pent = [(-hx, z0), (hx, z0), (hx, roof_z(hx) - 0.2), (0.0, roof_z(0.0) - 0.2), (-hx, roof_z(hx) - 0.2)]
    P.append(E.upright_prism("gable", pent, d, y, 0, 0, SHEET))
    side = -1 if y < 0 else 1
    for k in range(-8, 9):
        x = k * 1.24
        zt = roof_z(x) - 0.24
        if abs(x) > hx - 0.1 or zt - z0 < 0.2:
            continue
        P.append(rw.box("gablerib", (0.08, 0.06, zt - z0), (x, y + side * (d / 2 + 0.03), (zt + z0) / 2), mat=B.mat(SHEET)))
# corner trims (orange angle sections) on the closed corner
for (x, y) in ((WX - 0.02, WY - 0.02), (WX - 0.02, -6.6), (-WX + 0.02, WY - 0.02)):
    P.append(E.rbox("cornertrim", (0.2, 0.2, ZE + 0.1), (x, y, (ZE + 0.1) / 2), m=ORANGE, r=0.03))

# factory windows: steel grids with glowing panes
def factory_window(c, normal, w=2.6, h=1.5, nx=4, nz=3):
    n = V(normal).normalized()
    u = V((0, 0, 1)).cross(n).normalized()
    c = V(c)
    out = [E.beam("wframe", tuple(c - u * w / 2 + V((0, 0, h / 2)) + n * 0.06), tuple(c + u * w / 2 + V((0, 0, h / 2)) + n * 0.06),
                  0.12, 0.1, "M_DarkMetal", 0.02, up=tuple(n), extend=0.06),
           E.beam("wframe", tuple(c - u * w / 2 - V((0, 0, h / 2)) + n * 0.06), tuple(c + u * w / 2 - V((0, 0, h / 2)) + n * 0.06),
                  0.12, 0.14, "M_DarkMetal", 0.02, up=tuple(n), extend=0.1)]
    pane = rw.box("wpane", (1, 1, 1), tuple(c + n * 0.01), mat=E.mat("WindowGlow"))
    pane.scale = (abs(u.x) * w + abs(n.x) * 0.04, abs(u.y) * w + abs(n.y) * 0.04, h)
    rw.apply_transform(pane)
    out.append(pane)
    for i in range(nx + 1):
        a = -w / 2 + w * i / nx
        out.append(B.bar("wmull", tuple(c + u * a - V((0, 0, h / 2)) + n * 0.06), tuple(c + u * a + V((0, 0, h / 2)) + n * 0.06), 0.07, 0.07,
                         "M_DarkMetal"))
    for j in range(1, nz):
        zz = -h / 2 + h * j / nz
        out.append(B.bar("wmull", tuple(c - u * w / 2 + V((0, 0, zz)) + n * 0.06), tuple(c + u * w / 2 + V((0, 0, zz)) + n * 0.06), 0.06,
                         0.06, "M_DarkMetal"))
    return out


for y in (-4.27, 0.0, 4.27):
    P += factory_window((WX + 0.02, y, 3.75), (1, 0, 0))
for x in (-6.4, -2.6):
    P += factory_window((x, WY + 0.02, 3.75), (0, 1, 0), 2.6, 1.5)
# big sliding door on the back wall (outside), on a rail
DX0, DX1 = 1.2, 6.8
P.append(E.rod("doorrail", (DX0 - 0.6, WY + 0.25, 4.62), (DX1 + 2.0, WY + 0.25, 4.62), 0.06, 8, "M_Steel"))
P.append(E.rbox("doorframe", (DX1 - DX0, 0.14, 4.4), ((DX0 + DX1) / 2, WY + 0.22, 2.25), m=ORANGE, r=0.04))
dp = B.corrugate((DX1 - 0.12, WY + 0.32, 0.18), (DX0 + 0.12, WY + 0.32, 0.18), (0, 1, 0), 0.05, 0.6, 6)
P.append(B.sweep("doorsheet", dp, (0, 0, 4.06), 0.05, SHEET, smooth=60))
for z in (0.9, 2.25, 3.6):
    P.append(E.rbox("doorbar", (DX1 - DX0 - 0.1, 0.08, 0.16), ((DX0 + DX1) / 2, WY + 0.38, z), m=ORANGE, r=0.02))
P.append(E.beam("doorbrace", (DX0 + 0.2, WY + 0.4, 0.4), (DX1 - 0.2, WY + 0.4, 4.1), 0.14, 0.06, ORANGE, 0.02, up=(0, 1, 0)))
for x in (DX0 + 0.5, DX1 - 0.5):
    P.append(rw.cylinder("doorroller", 0.13, 0.1, 10, (x, WY + 0.25, 4.62 + 0.12), (90, 0, 0), E.mat("M_Brass")))
P.append(E.rod("doorhandle", (DX0 + 0.35, WY + 0.46, 1.6), (DX0 + 0.35, WY + 0.46, 2.4), 0.035, 6, "M_Steel"))

# ---------------------------------------------------------------- the big gear emblem on the front gable
GC = V((0.0, CYS[0] - 0.42, 6.95))
P += B.gear_wheel("emblem", 1.25, 14, tuple(GC), (0, -1, 0), 0.22, m="M_Brass", spokes=6, hub=0.34, hub_m="M_Copper")
P.append(E.disc("emblemback", 1.02, 0.08, tuple(GC + V((0, 0.12, 0))), (0, -1, 0), 24, "M_DarkMetal"))
P.append(E.ball("emblemcore", 0.2, tuple(GC + V((0, -0.22, 0))), "M_TechGlow", 10, 8))
P += E.rivet_ring(tuple(GC + V((0, -0.12, 0))), 0.86, 12, 0.04, "M_Steel", axis="Y")
for sx in (-1, 1):
    P.append(B.bar("emblemarm", (sx * 0.95, CYS[0] - 0.22, 5.85), (sx * 0.5, CYS[0] - 0.36, 6.35), 0.1, 0.1, "M_DarkMetal"))

# ---------------------------------------------------------------- overhead crane
RWX = CX - 0.5
for sx in (-1, 1):
    P.append(B.ibeam("runway", (sx * RWX, -6.5, 4.3), (sx * RWX, 6.5, 4.3), 0.36, 0.26, 0.05, 0.05, "M_DarkMetal", up=(0, 0, 1)))
    for y in CYS:
        P.append(B.bar("corbel", (sx * (CX - 0.2), y, 4.05), (sx * (RWX - 0.05), y, 4.05), 0.22, 0.22, ORANGE))
CRY = 0.9
P.append(E.rbox("bridge", (2 * RWX, 0.55, 0.62), (0, CRY, 4.75), m="HazardYellow", r=0.04))
for sx in (-1, 1):
    P += B.hazard_bar((sx * (RWX - 1.2), CRY - 0.29, 4.75), (sx * (RWX - 0.1), CRY - 0.29, 4.75), 0.04, 0.5, 4, up=(0, 0, 1))
    P.append(E.rbox("endtruck", (0.5, 1.6, 0.42), (sx * RWX, CRY, 4.65), m="HazardYellow", r=0.04))
    for dy in (-0.55, 0.55):
        P.append(rw.cylinder("crwheel", 0.14, 0.12, 10, (sx * RWX, CRY + dy, 4.53), (0, 90, 0), E.mat("IronDark")))
TX = -2.6
P.append(E.rbox("trolley", (1.1, 1.0, 0.46), (TX, CRY, 5.27), m="PaintOrange", r=0.05))
P.append(rw.cylinder("drum", 0.22, 0.8, 12, (TX, CRY, 4.9), (0, 90, 0), E.mat("M_DarkMetal")))
for dx in (-0.12, 0.12):
    P.append(E.rod("cable", (TX + dx, CRY, 4.7), (TX + dx, CRY, 3.0), 0.02, 5, "M_Steel"))
P.append(E.rbox("hookblock", (0.5, 0.32, 0.5), (TX, CRY, 2.8), m="HazardYellow", r=0.06))
P.append(rw.cylinder("sheave", 0.18, 0.36, 10, (TX, CRY, 2.92), (90, 0, 0), E.mat("M_DarkMetal")))
P.append(E.tube("hook", [(TX, CRY, 2.52), (TX, CRY, 2.3), (TX + 0.08, CRY, 2.12), (TX + 0.26, CRY, 2.16), (TX + 0.3, CRY, 2.32)], 0.055,
                "M_Steel", 1, smooth=True, ures=3))

# ---------------------------------------------------------------- hanging lamps
for y in (CYS[1], CYS[2]):
    for x in (-5.6, 0.0, 5.6):
        lp, bulb = B.pendant_lamp((x, y, ZE + 0.02), 1.15, 0.36, "M_PaintedMetal__2e7d5a")
        P += lp
        L.add(bulb)

# ---------------------------------------------------------------- pipework and an electrics panel on the closed walls (inside)
IX = CX - 0.4
P += E.pipe("wallpipe", [(IX, -6.2, 2.25), (IX, 3.0, 2.25), (IX, 3.0, 3.75), (WX - 0.12, 3.0, 3.75)], 0.11, "M_Copper", 0.35)
P += E.pipe("wallpipe2", [(IX + 0.05, -6.2, 1.75), (IX + 0.05, 5.9, 1.75), (2.0, 5.9, 1.75)], 0.08, "M_Steel", 0.3)
P += E.valve_wheel((IX - 0.2, -2.0, 2.25), (-1, 0, 0), 0.22, "PaintRed")
P += E.valve_wheel((IX - 0.2, 1.2, 2.25), (-1, 0, 0), 0.22, "PaintRed")
P.append(E.rod("gaugeriser", (IX, -0.4, 2.25), (IX, -0.4, 2.62), 0.045, 8, "M_Copper"))   # the gauge sits on a riser off the pipe
P += E.gauge((IX - 0.04, -0.4, 2.8), (-1, 0, 0), 0.18, 40)
P.append(E.rbox("epanel", (0.22, 1.1, 1.3), (WX - 0.2, -4.3, 3.1), m="M_DarkMetal", r=0.04))
for k in range(3):
    P.append(E.disc("elight", 0.07, 0.04, (WX - 0.32, -4.65 + 0.35 * k, 3.5), (-1, 0, 0), 8, "M_TechGlow" if k != 1 else "TealGlow"))
P.append(E.rbox("lever", (0.08, 0.08, 0.5), (WX - 0.36, -4.0, 2.85), (25, 0, 0), m="PaintRed", r=0.02))
# barrels and crates tucked into the back-right corner
for (x, y, r) in ((8.55, 5.6, 0.0), (7.85, 5.75, 30.0), (8.6, 4.9, 60.0)):
    P += E.barrel(0.32, 0.88, (x, y, 0.05), r, m="M_PaintedMetal__3f6fb8", hoop="IronDark")
P += E.crate((0.9, 0.9, 0.9), (6.9, 5.7, 0.05), 8)
P += E.crate((0.7, 0.7, 0.7), (6.95, 5.68, 0.95), -12)

E.tri_breakdown(P, 28)
main = E.join(P, "FactoryShed")
W = E.wonk(main, 9.0, lean=(0.08, 0.04), twist=0.8, bulge=0.0)
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit(W)

# ---------------------------------------------------------------- collision: columns, closed walls, roof
for sx in (-1, 1):
    for y in CYS:
        E.col_box("Column", (0.5, 0.42, ZE + 0.2), (sx * CX, y, (ZE + 0.2) / 2))
E.col_box("WallRight", (0.75, 2 * 6.62, ZE + 0.25), (WX - 0.3, 0, (ZE + 0.25) / 2))
E.col_box("WallBack", (2 * WX, 0.75, ZE + 0.25), (0, WY - 0.3, (ZE + 0.25) / 2))
E.col_hull("GableBack", [(x, y, z) for (x, z) in ((-RX + 0.3, ZE), (RX - 0.3, ZE), (0.0, ZR - 0.1)) for y in (WY - 0.6, WY + 0.05)])
E.col_box("Corner", (2.3, 1.6, 1.8), (7.9, 5.4, 0.9))
for sx in (-1, 1):
    run, rise = RX, ZR - ZEV
    Lr = math.hypot(run, rise)
    ang = math.degrees(math.atan2(rise, run))
    E.col_box("Roof", (Lr + 0.1, 2 * RY, 0.35), (sx * RX / 2, 0, (ZR + ZEV) / 2 - 0.15), (0, sx * ang, 0))

E.check(ASSET, (20, 14, 9), 30000)
rw.finish(ASSET, "env", previews=E.previews())
