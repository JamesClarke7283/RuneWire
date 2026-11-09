"""part_barrel: volatile mana barrel, diameter 0.7 x 1.0 m high.

Bulging dark-wood staves, riveted steel hoops, a glowing violet rune band (M_RuneGlow) with dark iron
runes, glowing mana drips leaking from under the top hoop, a yellow warning sign on the front and a
little violet crystal cluster in a brass collar on the lid. Origin at the bounding-box centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

Z0, Z1 = -0.5, 0.355            # stave body (the crystal cap reaches +0.5)
ZC = (Z0 + Z1) / 2
HB = (Z1 - Z0) / 2
R_MID, R_END = 0.322, 0.272
CRYSTAL = "M_Crystal__a066ff"
pl.tint_emission(CRYSTAL, "b07cff")
parts = []


def r_at(z):
    t = (z - ZC) / HB
    return R_END + (R_MID - R_END) * (1 - t * t)


# --- staves ---------------------------------------------------------------------------------------
parts.append(pl.stave_surface("staves", 14, Z0, Z1, r_at, 9, 0.013, 0.005, "M_WoodDark"))
# chime + recessed lids (top and bottom)
for (zr, s) in ((Z1, 1), (Z0, -1)):
    r = r_at(zr)
    zl = zr - s * 0.03
    prof = [(r - 0.006, zr - s * 0.035), (r + 0.004, zr - s * 0.004), (r - 0.012, zr + s * 0.002),
            (r - 0.04, zr), (r - 0.044, zl), (0.0, zl)]
    if s < 0:
        prof = [(p[0], p[1]) for p in prof]
    lid = rw.lathe("lid", prof, 32, mat="M_WoodDark", cap_bottom=False, cap_top=False, smooth_angle=40)
    parts.append(lid)
    # lid plank seams: two shallow dark strips
    for dx in (-0.09, 0.09):
        parts.append(rw.box("seam", (0.012, 2 * (r - 0.05), 0.006), (dx, 0, zl), mat="M_WoodDark"))

# --- steel hoops with rivets ----------------------------------------------------------------------
for dz in (-0.355, -0.2, 0.2, 0.33):
    z = ZC + dz
    r = r_at(z)
    parts.append(pl.band("hoop", r + 0.014, 0.05, 0.03, (0, 0, 1), (0, 0, z), "M_Steel", 24))
    for i in range(3):
        a = 2 * math.pi * (i + 0.25) / 3
        d = V((math.cos(a), math.sin(a), 0))
        parts.append(pl.rivet(V((0, 0, z)) + d * (r + 0.014), d, 0.013, 0.006, "M_Steel", 6))

# --- glowing rune band with dark iron runes --------------------------------------------------------
RB = 0.343
parts.append(pl.band("runeband", RB, 0.125, 0.04, (0, 0, 1), (0, 0, ZC), "M_RuneGlow", 32, 0.3))
for dz in (-0.075, 0.075):
    parts.append(pl.band("bandedge", RB + 0.005, 0.03, 0.045, (0, 0, 1), (0, 0, ZC + dz), "M_Steel", 28))
keys = ("algiz", "kenaz", "sowilo", "ingwaz", "tiwaz", "dagaz", "fehu", "othala")
for i, k in enumerate(keys):
    a = math.radians(-90 + 45 * i)
    c = V((RB * math.cos(a), RB * math.sin(a), ZC))
    u = V((-math.sin(a), math.cos(a), 0))
    parts += pl.glyph(k, c, u, (0, 0, 1), 0.085, 0.017, 0.012, "M_DarkMetal")

# --- glowing mana drips leaking from under the top hoop ---------------------------------------------
for (adeg, length) in ((-58, 0.1), (-125, 0.075), (40, 0.09)):
    a = math.radians(adeg)
    d = V((math.cos(a), math.sin(a), 0))
    pts, rad = [], []
    z_start = ZC + 0.31
    for k in range(5):
        t = k / 4
        z = z_start - length * t
        pts.append(d * (r_at(z) + 0.004 + (0.006 if k == 4 else 0.0)) + V((0, 0, z)))
        rad.append(0.017 - 0.005 * math.sin(t * math.pi) + (0.009 if k == 4 else 0.0))
    parts.append(pl.sausage("drip", pts, rad, 7, 2, "M_RuneGlow", (True, True), 2))

# --- warning sign on the front ---------------------------------------------------------------------
rw.flat("WarnYellow", "ffc531", 0.5, 0.0)
rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)
zs = ZC + 0.275
rs = r_at(zs) + 0.004
tri = []
for k in range(3):
    ang = math.radians(90 + 120 * k)
    cx, cy = 0.062 * math.cos(ang), 0.062 * math.sin(ang) - 0.012
    for j in range(5):
        aa = ang - math.radians(60) + math.radians(120) * j / 4
        tri.append((cx + 0.016 * math.cos(aa), cy + 0.016 * math.sin(aa)))
sign = rw.extrude_poly("sign", tri, 0.012, mat="WarnYellow", bevel=0.003)
pl.align(sign, (0, -1, 0), (0, -rs, zs), x_hint=(1, 0, 0))
parts.append(sign)
parts.append(pl.obox("bang", (0.012, 0.008, 0.045), (0, -rs - 0.007, zs + 0.008), mat="WarnBlack"))
parts.append(pl.obox("dot", (0.012, 0.008, 0.012), (0, -rs - 0.007, zs - 0.03), mat="WarnBlack"))

# --- crystal cap ----------------------------------------------------------------------------------
zl = Z1 - 0.03
parts.append(pl.lathe_axis("collar", [(0.115, zl - 0.01), (0.115, zl + 0.022), (0.1, zl + 0.04), (0.075, zl + 0.04),
                                      (0.075, zl + 0.02), (0.0, zl + 0.02)], (0, 0, 1), (0, 0, 0), 24, "M_Brass",
                           True, False, 40))
parts.append(pl.crystal("gem", (0, 0, zl + 0.0), (0.06, -0.05, 1), 0.5 - zl - 0.002, 0.062, 6, 0.3, 0.1, CRYSTAL))
parts.append(pl.crystal("gem", (0.045, 0.02, zl + 0.01), (0.7, 0.3, 1), 0.105, 0.04, 6, 0.32, 0.1, CRYSTAL, 20))
parts.append(pl.crystal("gem", (-0.045, 0.03, zl + 0.01), (-0.6, 0.45, 1), 0.09, 0.034, 6, 0.32, 0.1, CRYSTAL, 10))
parts.append(pl.crystal("gem", (0.0, -0.05, zl + 0.01), (0.1, -0.8, 1), 0.075, 0.03, 6, 0.32, 0.1, CRYSTAL, 30))

barrel = rw.join(parts, "Barrel")
rw.smooth(barrel, 30)
pl.recentre()
rw.set_origin(barrel, (0, 0, 0))
pl.check("part_barrel", (0.7, 0.7, 1.0))
rw.finish("part_barrel", "parts", icon=True)
