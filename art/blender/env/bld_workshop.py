"""bld_workshop: Odda's Workshop, the master artificer's hangar on the town plaza (12 x 10 x ~10 m).

A teal metal barrel-vault hangar with brass ribs on stone corner piers. Big sliding plank doors stand open on a
rail, showing a dark interior (flywheel, bench, hanging lamp). Above them: a sign board with a gear emblem and a
train of three giant gears, the biggest of which is a glowing round window. A lean-to store on the left, a brass
chimney stack, a copper boiler and copper pipes on the right. Origin at the ground centre, front facing -Y.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_workshop"
B.reset()
P = []          # visual parts
L = B.Lights()  # LightPoint locations (mapped through the wonk at the end)

# ---------------------------------------------------------------- dimensions
HX = 4.5                 # half width of the hall walls
FY, BY = -4.1, 4.1       # front / back wall faces
Z0 = 0.5                 # floor (plinth top)
ZE = 5.4                 # wall top = vault springing
RISE = 3.2               # vault rise above ZE
OW, OH = 4.4, 4.55       # hangar opening width / top
REC = 0.8                # depth of the opening recess
ROOF = "M_PaintedMetal__2f9c95"

# ---------------------------------------------------------------- masses
P.append(E.rbox("plinth", (2 * HX + 0.5, BY - FY + 0.5, 0.75), (0, (FY + BY) / 2, 0.125), m="M_Stone", r=0.08))
P.append(E.rbox("core", (2 * HX, BY - FY - REC, ZE - Z0 + 0.1), (0, (FY + REC + BY) / 2, (Z0 + ZE) / 2), m="M_Plaster", r=0.04))
for sx in (-1, 1):
    x0, x1 = sx * OW / 2, sx * HX
    P.append(E.rbox("frontwall", (HX - OW / 2, REC + 0.04, ZE - Z0 + 0.1), ((x0 + x1) / 2, FY + REC / 2, (Z0 + ZE) / 2), m="M_Plaster", r=0.04))
P.append(E.rbox("headwall", (OW + 0.1, REC + 0.04, ZE - OH + 0.05), (0, FY + REC / 2, (OH + ZE) / 2), m="M_Plaster", r=0.04))

# vault roof (outer profile swept along Y), gables follow its underside
prof = B.vault_profile(HX + 0.08, ZE, RISE, n=16, kick=0.5, drop=0.22)
VY0, VY1 = FY - 0.5, BY + 0.45
P.append(B.sweep("vault", [(x, VY0, z) for (x, z) in prof], (0, VY1 - VY0, 0), 0.24, ROOF, smooth=50))
gab = [(HX, ZE - 0.25), (-HX, ZE - 0.25)] + [(HX * math.sin(-math.pi / 2 + math.pi * i / 16),
                                            ZE + (RISE - 0.12) * math.cos(-math.pi / 2 + math.pi * i / 16)) for i in range(17)]
for (y0, y1) in ((FY, FY + 0.3), (BY - 0.3, BY)):
    P.append(E.upright_prism("gable", gab, y1 - y0, (y0 + y1) / 2, 0, 0, "M_Plaster"))


def outward(i, off):
    """Point i of the vault profile pushed `off` along its outward normal."""
    a = V((prof[max(0, i - 1)][0], 0, prof[max(0, i - 1)][1]))
    b = V((prof[min(len(prof) - 1, i + 1)][0], 0, prof[min(len(prof) - 1, i + 1)][1]))
    t = (b - a).normalized()
    n = V((-t.z, 0, t.x))
    return V((prof[i][0], 0, prof[i][1])) + n * off


# brass ribs over the vault, a fat one along each end
for y, r in ((VY0 + 0.1, 0.14), (-1.6, 0.085), (0.8, 0.085), (VY1 - 0.1, 0.12)):
    pts = [tuple(outward(i, r * 0.6) + V((0, y, 0))) for i in range(len(prof))]
    P.append(E.tube("rib", pts, r, "M_Brass", 1, smooth=False))
# rusty patch plates riveted onto the roof
for (i0, y0, y1) in ((4, -0.5, 0.4), (11, 1.5, 2.6), (8, -3.4, -2.6)):
    pts = [tuple(outward(i, 0.03) + V((0, y0, 0))) for i in (i0, i0 + 1, i0 + 2)]
    P.append(B.sweep("patch", pts, (0, y1 - y0, 0), 0.03, "M_Rust"))
    for i in (i0, i0 + 2):
        for yy in (y0 + 0.1, y1 - 0.1):
            P.append(E.rivet("riv", tuple(outward(i, 0.06) + V((0, yy, 0))), 0.035, "M_Steel", lo=True))

# ridge lantern (glazed roof monitor) with a little vault cap
LZ = ZE + RISE - 0.15
P.append(E.rbox("monitor", (1.4, 3.4, 0.75), (0, 0.2, LZ + 0.3), m="M_WoodDark", r=0.04))
for sx in (-1, 1):
    for k in range(3):
        y = -0.85 + k * 1.05
        P.append(rw.box("mpane", (0.05, 0.75, 0.42), (sx * 0.71, y, LZ + 0.37), mat=E.mat("WindowGlow")))
        P.append(rw.box("mmul", (0.07, 0.06, 0.42), (sx * 0.72, y, LZ + 0.37), mat=E.mat("M_WoodDark")))
cap = B.vault_profile(0.8, LZ + 0.66, 0.32, n=8, kick=0.12, drop=0.08)
P.append(B.sweep("mcap", [(x, -1.6, z) for (x, z) in cap], (0, 3.6, 0), 0.08, ROOF, smooth=50))
P.append(E.tube("mrib", [(x, -1.62, z + 0.05) for (x, z) in cap], 0.06, "M_Brass", 1, smooth=False))

# ---------------------------------------------------------------- stone piers
for sx in (-1, 1):
    for (y, fy) in ((FY + 0.12, -1), (BY - 0.1, 1)):
        P.append(E.rbox("pier", (0.78, 0.78, ZE + 0.15), (sx * HX, y, (ZE - 0.25) / 2 + 0.05), m="M_Stone", r=0.07))
        P.append(E.rbox("piercap", (0.95, 0.95, 0.22), (sx * HX, y, ZE + 0.02), m="M_StoneRough", r=0.06))
        P.append(E.rbox("pierfoot", (0.92, 0.92, 0.5), (sx * HX, y, 0.2), m="M_StoneRough", r=0.06))
        for k, z in enumerate((1.05, 2.1, 3.15, 4.2)):
            sz = (0.9, 0.84, 0.32) if k % 2 == 0 else (0.84, 0.9, 0.32)
            P.append(E.stone("quoin", sz, (sx * HX, y, z), m="M_StoneRough", b=0.05, seed=k + int(sx * 3 + y), jitter=2.0))

# ---------------------------------------------------------------- hangar opening, interior
P.append(rw.box("interior", (OW + 0.1, 0.04, OH - Z0 + 0.1), (0, FY + REC - 0.03, (Z0 + OH) / 2), mat=E.mat("Interior")))
P.append(E.rbox("floor", (OW, REC + 0.1, 0.08), (0, FY + REC / 2, Z0 + 0.02), m="M_WoodPlanks", r=0.02))
P.append(E.rbox("ceil", (OW + 0.05, REC, 0.06), (0, FY + REC / 2, OH + 0.01), m="M_WoodDark", r=0.02))
for sx in (-1, 1):
    P.append(E.rbox("jamb", (0.3, 0.32, OH - Z0 + 0.1), (sx * (OW / 2 + 0.08), FY - 0.02, (Z0 + OH) / 2), m="M_WoodDark", r=0.05))
# inside: a big dark flywheel, a bench with a glowing vice, a hanging lamp, a chain hoist
P += B.gear_wheel("flywheel", 1.35, 14, (1.25, FY + REC - 0.2, 2.0), (0, -1, 0), 0.16, m="Iron", hub_m="M_Brass", spokes=6)
P.append(E.rbox("bench", (1.6, 0.5, 0.12), (-1.15, FY + REC - 0.35, 1.35), m="M_WoodPlanks", r=0.03))
for bx in (-1.8, -0.5):
    P.append(rw.box("benchleg", (0.1, 0.4, 0.85), (bx, FY + REC - 0.35, 0.92), mat=E.mat("M_WoodDark")))
P.append(E.rbox("vice", (0.3, 0.3, 0.22), (-0.7, FY + REC - 0.35, 1.52), m="M_Steel", r=0.04))
P.append(rw.box("toolboard", (1.4, 0.05, 0.9), (-1.2, FY + REC - 0.06, 2.35), mat=E.mat("M_WoodDark")))
for k, tx in enumerate((-1.7, -1.4, -1.05, -0.75)):
    P.append(rw.box("tool", (0.07, 0.04, 0.45 + 0.1 * (k % 2)), (tx, FY + REC - 0.1, 2.3), mat=E.mat("M_Steel" if k % 2 else "M_Brass")))
lamp, lamp_c = E.lantern((0.0, FY + 0.45, OH - 0.02), "hang", scale=1.3)
P += lamp
L.add(lamp_c)
P.append(E.rod("hoistchain", (-0.4, FY + 0.3, OH - 0.02), (-0.4, FY + 0.3, 3.3), 0.025, 5, "IronDark"))
P.append(E.ring("hook", 0.11, 0.03, (-0.4, FY + 0.3, 3.18), (1, 0, 0), "M_Steel", 10, 5))

# steel girder over the opening (signal orange, riveted)
GZ0, GZ1 = OH, OH + 0.42
P.append(E.rbox("girder", (OW + 1.4, 0.3, GZ1 - GZ0), (0, FY - 0.05, (GZ0 + GZ1) / 2), m="M_PaintedMetal", r=0.03))
for sz in (GZ0 + 0.06, GZ1 - 0.06):
    P.append(E.rbox("flange", (OW + 1.5, 0.38, 0.08), (0, FY - 0.06, sz), m="M_PaintedMetal", r=0.02))
for i in range(12):
    x = -OW / 2 - 0.55 + (OW + 1.1) * i / 11
    P.append(E.rivet("riv", (x, FY - 0.22, (GZ0 + GZ1) / 2), 0.04, "M_Brass", lo=True))

# ---------------------------------------------------------------- sliding doors on a rail
RAIL_Z = GZ1 + 0.12
P.append(E.rod("rail", (-HX + 0.3, FY - 0.36, RAIL_Z), (HX - 0.3, FY - 0.36, RAIL_Z), 0.05, 8, "M_Steel"))
for x in (-HX + 0.45, -OW / 2 - 0.1, OW / 2 + 0.1, HX - 0.45):
    P.append(E.rbox("railbracket", (0.12, 0.4, 0.12), (x, FY - 0.2, RAIL_Z), m="IronDark", r=0.02))


def leaf(x0, x1, z0, z1, y):
    """Sliding barn-door leaf between x0..x1 / z0..z1, its back face on the plane y."""
    out = []
    w, h = x1 - x0, z1 - z0
    n = 5
    for i in range(n):
        px = x0 + w * (i + 0.5) / n
        out.append(E.rbox("plank", (w / n - 0.03, 0.1, h - 0.05), (px, y - 0.05, (z0 + z1) / 2), m="M_WoodPlanks", r=0.02))
    for zz in (z0 + 0.22, (z0 + z1) / 2, z1 - 0.22):
        out.append(E.rbox("batten", (w + 0.04, 0.08, 0.22), ((x0 + x1) / 2, y - 0.14, zz), m="PaintTeal", r=0.025))
    for (za, zb) in ((z0 + 0.3, (z0 + z1) / 2 - 0.1), ((z0 + z1) / 2 + 0.1, z1 - 0.3)):
        out.append(E.beam("brace", (x0 + 0.15, y - 0.14, za), (x1 - 0.15, y - 0.14, zb), 0.16, 0.07, "PaintTeal", 0.02, up=(0, -1, 0)))
    for xx in (x0 + 0.15, x1 - 0.15):
        for zz in (z0 + 0.22, z1 - 0.22):
            out.append(E.rivet("nail", (xx, y - 0.2, zz), 0.035, "Iron", lo=True))
    for xx in (x0 + 0.35, x1 - 0.35):
        out.append(rw.box("hanger", (0.1, 0.04, RAIL_Z - z1 + 0.15), (xx, y - 0.12, (z1 + RAIL_Z) / 2), mat=E.mat("IronDark")))
        out.append(rw.cylinder("roller", 0.11, 0.08, 10, (xx, FY - 0.36, RAIL_Z + 0.09), (90, 0, 0), E.mat("M_Brass")))
    hx = x1 - 0.25 if x0 < 0 else x0 + 0.25
    out.append(E.rod("handle", (hx, y - 0.24, (z0 + z1) / 2 - 0.45), (hx, y - 0.24, (z0 + z1) / 2 + 0.25), 0.03, 6, "M_Brass"))
    return out


DY = FY - 0.28
P += leaf(-HX + 0.38, -OW / 2 + 0.2, Z0 + 0.04, OH - 0.05, DY)
P += leaf(OW / 2 - 0.2, HX - 0.38, Z0 + 0.04, OH - 0.05, DY)

# threshold: stone ramp up to the floor
P.append(E.rbox("ramp", (OW + 0.4, 0.7, 0.32), (0, FY - 0.42, 0.12), (8, 0, 0), m="M_StoneRough", r=0.05))

# ---------------------------------------------------------------- sign board with a gear emblem
SZ = 5.82
P.append(E.rbox("sign", (3.4, 0.16, 1.0), (0, FY - 0.1, SZ), m="M_WoodDark", r=0.06))
P.append(E.rbox("signpanel", (3.08, 0.06, 0.76), (0, FY - 0.2, SZ), m="PaintCream", r=0.025))
for sx in (-1, 1):
    for sz in (SZ + 0.38, SZ - 0.38):
        P.append(E.rivet("sriv", (sx * 1.56, FY - 0.21, sz), 0.055, "M_Brass"))
    # bold teal flourish bars either side of the emblem
    P.append(E.rbox("flour", (0.86, 0.06, 0.13), (sx * 1.0, FY - 0.24, SZ + 0.13), m="PaintTeal", r=0.03))
    P.append(E.rbox("flour", (0.62, 0.06, 0.13), (sx * 0.88, FY - 0.24, SZ - 0.13), m="PaintTeal", r=0.03))
# crossed wrench and hammer behind the emblem gear
P.append(E.beam("wrench", (-0.5, FY - 0.27, SZ - 0.27), (0.48, FY - 0.27, SZ + 0.26), 0.1, 0.05, "M_Steel", 0.02, up=(0, -1, 0)))
P.append(E.ring("wrenchhead", 0.11, 0.045, (0.55, FY - 0.27, SZ + 0.3), (0, -1, 0), "M_Steel", 10, 5))
P.append(E.beam("hammer", (0.5, FY - 0.27, SZ - 0.27), (-0.42, FY - 0.27, SZ + 0.22), 0.09, 0.05, "M_WoodPlanks", 0.02, up=(0, -1, 0)))
P.append(E.beam("hammerhead", (-0.6, FY - 0.27, SZ + 0.04), (-0.32, FY - 0.27, SZ + 0.43), 0.17, 0.08, "IronDark", 0.025, up=(0, -1, 0)))
P += B.gear_wheel("emblem", 0.37, 10, (0, FY - 0.32, SZ), (0, -1, 0), 0.07, m="M_Brass", spokes=0, hub=0.13, hub_m="PaintRed")

# ---------------------------------------------------------------- the gear train on the gable
# a round window on the gable, and a giant brass gear on an axle in front of it that breaks the roofline
GY = FY - 0.68
GC = V((0, GY, 7.55))
GR = 1.5
P.append(E.disc("gearpane", 0.86, 0.04, (0, FY - 0.02, 7.5), (0, -1, 0), 20, "WindowGlow"))
P.append(E.ring("paneframe", 0.88, 0.07, (0, FY - 0.05, 7.5), (0, -1, 0), "M_Brass", 20, 6))
P += B.gear_wheel("gearbig", GR, 16, tuple(GC), (0, -1, 0), 0.2, m="M_Brass", spokes=6, hub=0.3, hub_m="M_Copper")
P.append(E.rod("axle", (0, FY, GC.z), (0, GY - 0.12, GC.z), 0.13, 10, "M_Steel"))
P.append(E.ball("gearcore", 0.13, (0, GY - 0.2, GC.z), "TealGlow", 8, 6))
L.add((0, GY - 0.45, GC.z - 0.4))
for (r, teeth, ang, m, spin, spokes) in ((0.85, 11, 180.0, "M_Copper", 9.0, 4), (0.62, 9, -16.0, "M_Brass", 6.0, 3)):
    d = GR + r - 0.2
    c = GC + V((d * math.cos(math.radians(ang)), 0.02, d * math.sin(math.radians(ang))))
    P += B.gear_wheel("gear", r, teeth, tuple(c), (0, -1, 0), 0.16, m=m, spokes=spokes, spin=spin, hub_m="M_Brass")
    P.append(E.rod("axle", (c.x, FY, c.z), (c.x, c.y - 0.1, c.z), 0.08, 8, "M_Steel"))
# timber on the gable around the gears
gf = E.Face((0, FY, 0), (1, 0, 0), (0, -1, 0))
P.append(gf.beam(-HX + 0.35, ZE - 0.02, HX - 0.35, ZE - 0.02, 0.24, 0.16, 0.08, extend=0.0))
for sx in (-1, 1):
    zt = ZE + (RISE - 0.2) * math.sqrt(max(0.0, 1 - (3.15 / HX) ** 2))
    P.append(gf.beam(sx * 3.15, ZE + 0.1, sx * 3.15, zt - 0.05, 0.18, 0.12, 0.06))
    P.append(gf.beam(sx * 3.15, ZE + 0.6, sx * 3.85, ZE + 0.1, 0.14, 0.1, 0.05))

# lanterns on the front piers
for sx in (-1, 1):
    lp, lc = E.lantern((sx * HX, FY - 0.55, 3.35), "wall", wall_normal=(0, -1, 0), scale=1.25)
    P += lp
    L.add(lc)

# ---------------------------------------------------------------- side and back walls: timber frames, windows
right = E.Face((HX, 0, 0), (0, 1, 0), (1, 0, 0))
left = E.Face((-HX, 0, 0), (0, -1, 0), (-1, 0, 0))
back = E.Face((0, BY, 0), (-1, 0, 0), (0, 1, 0))


def frame(f, a0, a1, posts, braces, rails=(2.9,)):
    out = [f.beam(a0, Z0 + 0.1, a1, Z0 + 0.1, 0.2, 0.14, 0.06), f.beam(a0, ZE - 0.12, a1, ZE - 0.12, 0.22, 0.14, 0.06)]
    for z in rails:
        out.append(f.beam(a0, z, a1, z, 0.16, 0.12, 0.05))
    for a in posts:
        out.append(f.beam(a, Z0 + 0.1, a, ZE - 0.1, 0.18, 0.14, 0.06))
    for (a, b, za, zb) in braces:
        out.append(f.beam(a, za, b, zb, 0.15, 0.1, 0.045))
    return out


ry0, ry1 = FY + 0.5, BY - 0.45
P += frame(right, ry0, ry1, (-1.25, 1.95), ((ry0, -1.25, 3.0, ZE - 0.2), (1.95, ry1, ZE - 0.2, 3.0)), rails=(2.95,))
P += frame(left, -(BY - 0.45), -(FY + 0.5), (-1.3, 1.4), ((-1.3, -(FY + 0.5), ZE - 0.2, 4.4),))
P += frame(back, -HX + 0.45, HX - 0.45, (-1.3, 0.55), ((-HX + 0.45, -1.3, 3.0, ZE - 0.2), (0.55, HX - 0.45, ZE - 0.2, 3.0)))
for (f, a, z, kw) in ((right, -2.55, 1.95, dict()), (right, 0.35, 1.95, dict(shutters="PaintTeal")),
                      (left, 2.6, 1.95, dict(flowerbox=True)),
                      (back, -2.6, 1.95, dict()), (right, -2.55, 4.15, dict()), (right, 0.35, 4.15, dict())):
    w = E.window(1.0 if z < 3 else 0.8, 1.15 if z < 3 else 0.62, kind="rect", seed=int(a * 10 + z), **kw)
    f.put(w, a, z, 0.0)
    P += w
L.add(right.p(-2.55, 1.95, 0.5))
# back gable: tie beam, posts and braces like the front
bg = E.Face((0, BY, 0), (-1, 0, 0), (0, 1, 0))
P.append(bg.beam(-HX + 0.35, ZE - 0.02, HX - 0.35, ZE - 0.02, 0.24, 0.16, 0.08))
for sx in (-1, 1):
    zt = ZE + (RISE - 0.2) * math.sqrt(max(0.0, 1 - (2.4 / HX) ** 2))
    P.append(bg.beam(sx * 2.4, ZE + 0.1, sx * 2.4, zt - 0.05, 0.18, 0.12, 0.06))
    P.append(bg.beam(sx * 2.4, ZE + 0.15, sx * 1.0, ZE + 1.3, 0.14, 0.1, 0.05))
    P.append(bg.beam(sx * 2.4, ZE + 1.1, sx * 3.7, ZE + 0.12, 0.14, 0.1, 0.05))
# back gable round window + door
bw = E.window(1.1, 1.1, kind="round", frame="M_Brass")
back.put(bw, 0.0, ZE + 1.5, 0.08)
P += bw
dr = E.door(1.1, 2.2, arch=True, m="M_WoodPlanks", frame="M_WoodDark", planks=4)
back.put(dr, 1.6, Z0, 0.0)
P += dr
P.append(E.rbox("backstep", (1.5, 0.5, 0.3), (-1.6, BY + 0.25, 0.15), m="M_StoneRough", r=0.05))

# ---------------------------------------------------------------- lean-to store on the left
AX1 = -5.75
AY0, AY1 = -1.25, 2.85
AZ_IN, AZ_OUT = 4.05, 3.0
P.append(E.rbox("annexplinth", (HX - AX1 + 0.3 - 2 * HX, AY1 - AY0 + 0.3, 0.7), ((-HX + AX1) / 2 - 0.15, (AY0 + AY1) / 2, 0.1),
                m="M_Stone", r=0.06))
R0, R1 = V((-HX + 0.1, 0, AZ_IN + 0.05)), V((AX1 - 0.35, 0, AZ_OUT - 0.05))


def zroof(x):
    return R0.z + (x - R0.x) * (R1.z - R0.z) / (R1.x - R0.x)


P.append(E.upright_prism("annex", [(AX1, 0.4), (-HX + 0.02, 0.4), (-HX + 0.02, zroof(-HX) - 0.12), (AX1, zroof(AX1) - 0.12)],
                         AY1 - AY0, (AY0 + AY1) / 2, 0, 0, "M_WoodPlanks", bevel=0.03))
for y in (AY0, AY1):
    P.append(E.rbox("annexpost", (0.2, 0.2, zroof(AX1) - 0.55), (AX1, y, 0.4 + (zroof(AX1) - 0.55) / 2), m="M_WoodDark", r=0.03))
for y in (AY0 + 0.02, AY1 - 0.02):
    P.append(E.beam("annexrafter", (-HX, y, zroof(-HX) - 0.16), (AX1 - 0.3, y, zroof(AX1 - 0.3) - 0.16), 0.14, 0.14, "M_WoodDark", 0.025))
# corrugated mono-pitch roof
cp = B.corrugate((R0.x, AY0 - 0.3, R0.z), (R0.x, AY1 + 0.3, R0.z), (0, 0, 1), 0.05, 0.6, 6)
P.append(B.sweep("annexroof", cp, (R1.x - R0.x, 0, R1.z - R0.z), 0.06, ROOF, smooth=60))
ad = E.door(0.85, 1.85, arch=False, m="M_WoodPlanks", frame="M_WoodDark", planks=3, knob=True)
E.place(ad, (-5.12, AY0, 0.45))
P += ad
aw = E.window(0.6, 0.6, kind="round", frame="M_Brass")
E.Face((AX1, 0, 0), (0, -1, 0), (-1, 0, 0)).put(aw, -0.8, 2.0, 0.0)   # on the store's outer wall
P += aw
# crates behind the store
P += E.crate((0.8, 0.8, 0.8), (-5.3, AY1 + 0.75, 0.0), 8)
P += E.crate((0.6, 0.6, 0.6), (-5.32, AY1 + 0.73, 0.8), -14)


# ---------------------------------------------------------------- brass chimney stack (right, outside the wall)
CX, CY = HX + 0.98, 2.15
P.append(E.rbox("chimbase", (1.05, 1.05, 1.6), (CX, CY, 0.55), m="M_Stone", r=0.07))
P.append(E.rbox("chimbasecap", (1.15, 1.15, 0.16), (CX, CY, 1.35), m="M_StoneRough", r=0.05))
P.append(E.lathe("chimney", [(0.52, 1.4), (0.51, 1.62), (0.44, 1.9), (0.43, 6.0), (0.41, 8.9), (0.5, 9.3), (0.58, 9.72),
                             (0.55, 9.85), (0.4, 9.85), (0.4, 9.6)], 16, loc=(CX, CY, 0), m="M_Brass", smooth=40,
                  cap_bottom=False, cap_top=False))
P.append(E.disc("soot", 0.41, 0.02, (CX, CY, 9.62), (0, 0, 1), 14, "Soot"))
for z in (3.0, 5.0, 7.0):
    P.append(E.ring("chimband", 0.44, 0.055, (CX, CY, z), (0, 0, 1), "M_Copper", 16, 5))
P.append(E.lathe("crownband", [(0.43, 8.72), (0.5, 8.76), (0.5, 9.02), (0.43, 9.06)], 16, loc=(CX, CY, 0), m="M_Copper",
                 smooth=40, cap_bottom=False, cap_top=False))
P += E.rivet_ring((CX, CY, 8.89), 0.5, 10, 0.035, "M_Brass", lo=True)
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.3
    p = V((CX + 0.36 * math.cos(a), CY + 0.36 * math.sin(a), 9.82))
    P.append(E.rod("hatleg", tuple(p), tuple(p + V((0, 0, 0.32))), 0.025, 5, "IronDark"))
P.append(rw.cone("hat", 0.66, 0.05, 0.38, 12, (CX, CY, 10.3), (0, 0, 0), E.mat("IronDark")))
for z in (3.0, 7.0):
    P.append(E.beam("chimstrap", (HX, CY, z), (CX - 0.42, CY, z), 0.1, 0.06, "IronDark", 0.015))
# flue pipe from the wall into the chimney
P += E.pipe("flue", [(HX + 0.05, CY - 0.9, 3.9), (HX + 0.55, CY - 0.9, 3.9), (CX, CY - 0.9, 3.9), (CX, CY - 0.3, 3.9)], 0.13, "M_Copper", 0.3)

# ---------------------------------------------------------------- copper boiler and pipes (right side)
BXC, BYC = HX + 0.62, -0.95
P.append(E.lathe("boiler", [(0.0, 0.42), (0.5, 0.42), (0.56, 0.55), (0.56, 2.25), (0.46, 2.55), (0.24, 2.7), (0.0, 2.72)], 16,
                 loc=(BXC, BYC, 0), m="M_Copper", smooth=40))
for z in (0.8, 1.6, 2.2):
    P.append(E.ring("boilband", 0.57, 0.045, (BXC, BYC, z), (0, 0, 1), "M_Brass", 16, 5))
P += E.rivet_ring((BXC, BYC, 1.2), 0.565, 10, 0.03, "M_Brass", lo=True)
P.append(E.rbox("boilerplinth", (1.25, 1.25, 0.6), (BXC, BYC, 0.12), m="M_StoneRough", r=0.05))
P += E.gauge((BXC + 0.4, BYC - 0.4, 1.75), tuple(V((0.7, -0.7, 0)).normalized()), 0.17, 30)
P += E.valve_wheel((BXC + 0.58, BYC + 0.05, 1.25), (1, 0, 0), 0.2, "PaintRed")
P.append(E.rod("safety", (BXC, BYC, 2.65), (BXC, BYC, 3.05), 0.06, 8, "M_Brass"))
P.append(rw.cone("whistle", 0.1, 0.04, 0.16, 8, (BXC, BYC, 3.13), (0, 0, 0), E.mat("M_Brass")))
P += E.pipe("bpipe", [(BXC - 0.3, BYC + 0.2, 2.5), (BXC - 0.3, BYC + 0.2, 3.6), (HX + 0.05, BYC + 0.2, 3.6)], 0.1, "M_Copper", 0.25)
P += E.pipe("bpipe2", [(BXC, BYC + 0.56, 0.9), (BXC, CY - 1.4, 0.9), (CX, CY - 1.4, 0.9), (CX, CY - 0.52, 0.9)], 0.09, "M_Copper", 0.3)
P += E.pipe("bpipe3", [(HX + 0.05, -3.3, 4.6), (HX + 0.3, -3.3, 4.6), (HX + 0.3, -3.3, 0.6)], 0.075, "M_Copper", 0.2)

# back: a hay-loft hoist beam with a pulley, a pent roof over the door, a coal bin and a pipe run
P.append(E.rbox("hoist", (0.24, 1.25, 0.26), (0, BY + 0.42, 7.95), m="M_WoodDark", r=0.04))
P.append(E.beam("hoistbrace", (0, BY + 0.02, 7.2), (0, BY + 0.7, 7.85), 0.14, 0.14, "M_WoodDark", 0.025, up=(1, 0, 0)))
P.append(E.ring("pulley", 0.17, 0.05, (0, BY + 0.9, 7.68), (1, 0, 0), "M_Brass", 12, 5))
P.append(E.rod("rope", (0.0, BY + 0.9 - 0.17, 7.68), (0.0, BY + 0.9 - 0.17, 5.9), 0.025, 5, "Rope"))
P.append(E.ring("hook", 0.11, 0.03, (0.0, BY + 0.73, 5.8), (1, 0, 0), "M_Steel", 10, 5))
pp = B.corrugate((-2.55, BY + 0.05, 3.55), (-0.65, BY + 0.05, 3.55), (0, 0, 1), 0.04, 0.55, 6)
P.append(B.sweep("pent", pp, (0, 1.0, -0.38), 0.05, ROOF, smooth=60))
for x in (-2.4, -0.8):
    P.append(E.beam("pentbracket", (x, BY + 0.02, 2.95), (x, BY + 0.8, 3.38), 0.1, 0.1, "M_WoodDark", 0.02, up=(1, 0, 0)))
P.append(E.rbox("coalbin", (1.1, 0.75, 0.75), (-3.3, BY + 0.42, 0.37), m="M_WoodPlanks", r=0.04))
for k in range(5):
    P.append(E.pebble("coal", 0.17, (-3.6 + 0.15 * k, BY + 0.35 + 0.06 * (k % 2), 0.76), "Charcoal", seed=k, squash=0.8))
P += E.pipe("backpipe", [(CX - 0.1, CY + 0.42, 1.15), (CX - 0.1, BY + 0.28, 1.15), (2.2, BY + 0.28, 1.15), (2.2, BY + 0.28, 3.7),
                         (2.2, BY + 0.02, 3.7)], 0.09, "M_Copper", 0.3)
P += E.valve_wheel((2.2, BY + 0.5, 2.3), (0, 1, 0), 0.18, "PaintRed")

E.tri_breakdown(P, 24)
main = E.join(P, "Workshop")
W = E.wonk(main, 10.5, lean=(0.08, 0.05), twist=1.4, bulge=0.008)
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit(W)
rw.empty("Smoke", tuple(W((CX, CY, 10.1))))

# ---------------------------------------------------------------- collision
E.col_box("Hall", (2 * HX + 0.8, BY - FY + 0.85, ZE + 0.25), (0, (FY + BY) / 2 - 0.05, (ZE - 0.25) / 2))
B.col_prism_xz("Vault", [(x, z) for (x, z) in prof] + [(-(HX + 0.5), ZE - 0.3), (HX + 0.5, ZE - 0.3)], VY0, VY1)
E.col_box("Annex", (-HX - AX1 + 0.45, AY1 - AY0 + 0.4, AZ_IN), (((-HX) + AX1) / 2 - 0.15, (AY0 + AY1) / 2, AZ_IN / 2 - 0.1))
E.col_box("Crates", (1.0, 1.0, 1.4), (-5.3, AY1 + 0.75, 0.7))
E.col_box("ChimBase", (1.15, 1.15, 1.6), (CX, CY, 0.55))
E.col_cyl("Chimney", 0.45, 8.6, (CX + 0.04, CY, 5.8))
E.col_cyl("Boiler", 0.6, 2.9, (BXC, BYC, 1.3))

E.check(ASSET, (12, 10, 10), 25000)
rw.finish(ASSET, "env", previews=E.previews())
