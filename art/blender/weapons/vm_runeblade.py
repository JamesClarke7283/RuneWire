"""vm_runeblade: first-person "Runeblade", a magic melee sword.

Nodes (origin = grip centre; the blade runs forward (-Y) and 35 degrees up, held like vm_thunder_wrench):
  Runeblade  a broad, slightly leaf-shaped steel blade with a lens cross-section, bright painted edge bevels
             and a dark fuller channel down its centre on both faces in which a line of glowing runes is
             inlaid (M_Crystal__a066ff - the only crystal on the model; the game swaps its tint per weapon);
             a winged-gear brass crossguard (a chamfered gear with a copper boss and the rarity gem set in its
             player-side face, flanked by scalloped brass wings with copper panels and raised feather lines), a
             brass collar, an oxblood spiral leather grip between brass ferrules and a brass gear pommel with
             copper domes. The blade is rolled 30 degrees about its axis so its flat (and the runes) face the
             player in first person and still read on the inventory icon (-X side).
  Glove      the shared cartoon leather glove gripping the handle (glove.py).
  Tip        empty at the blade tip.
"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import magic_weapon_helpers as mh  # noqa: E402

glove, pl, rw, V, dh, nw = mh.glove, mh.pl, mh.rw, mh.V, mh.dh, mh.nw
rw.reset()

TILT, ROLL = 35.0, 30.0
X = V((1, 0, 0))
AX = V((0, -math.cos(math.radians(TILT)), math.sin(math.radians(TILT))))    # grip/blade axis, toward the tip
UPW = V((0, math.sin(math.radians(TILT)), math.cos(math.radians(TILT))))    # perpendicular to AX, up and back
NF = (X * math.cos(math.radians(ROLL)) + UPW * math.sin(math.radians(ROLL))).normalized()  # blade flat normal
WD = AX.cross(NF).normalized()                                              # across the blade (edge to edge)

CRYSTAL = mh.crystal_mat()
RARITY = mh.rarity_mat()
EDGE = rw.flat("BladeEdge", "eef4f8", 0.3, 0.0)
GRIP_LEATHER = "M_Leather__7a1c22"
parts = mh.Parts()


def P(a, w=0.0, n=0.0):
    """Point in the blade frame: a along the axis, w across the blade, n out of the player-side flat."""
    return AX * a + WD * w + NF * n


# --- blade ----------------------------------------------------------------------------------------------------------
B0, B1 = 0.128, 0.626             # blade root (inside the guard) and tip
BL = B1 - B0
UM, W0, WM = 0.58, 0.036, 0.056   # widest point (fraction of the length) and half widths
U_CH = 0.7                        # the rune channel runs to here, then closes by U_CH + 0.1
CH_W = 0.0098                     # channel half width


def half_w(u):
    if u <= UM:
        return W0 + (WM - W0) * math.sin(math.pi / 2 * u / UM) ** 1.3
    return WM * math.cos(math.pi / 2 * (u - UM) / (1.0 - UM))


def half_t(u):
    return 0.0098 - 0.0028 * u - 0.0042 * max(0.0, (u - UM) / (1.0 - UM))


def chan(u):
    """(channel half width, channel depth)."""
    if u <= U_CH:
        return CH_W, 0.0034
    k = min(1.0, (u - U_CH) / 0.1)
    return CH_W * (1 - k) + 0.0012 * k, 0.0034 * (1 - k)


def section(u):
    w, t = half_w(u), half_t(u)
    e = min(0.0105, 0.3 * w)
    te = 0.0024 * (1 - 0.45 * u)
    cw, dep = chan(u)
    c = min(cw + 0.0038, 0.62 * (w - e))
    cw = min(cw, c - 0.0008)
    fl = max(cw - 0.0026, 0.0004)
    top = [(w, 0.0, 0), (w - e, te, 1), (c, t, 2), (cw, t, 3), (fl, t - dep, 4), (-fl, t - dep, 5), (-cw, t, 6),
           (-c, t, 7), (-w + e, te, 8)]
    bot = [(-w, 0.0, 9), (-w + e, -te, 10), (-c, -t, 11), (-cw, -t, 12), (-fl, -t + dep, 13), (fl, -t + dep, 14),
           (cw, -t, 15), (c, -t, 16), (w - e, -te, 17)]
    return top + bot


# face material per band (band j joins section point j and j+1)
BAND_MAT = {0: 0, 8: 0, 9: 0, 17: 0, 1: 1, 2: 1, 6: 1, 7: 1, 10: 1, 11: 1, 15: 1, 16: 1, 3: 2, 4: 2, 5: 2, 12: 2,
            13: 2, 14: 2}
US = [0.0, 0.03, 0.07, 0.12, 0.18, 0.25, 0.32, 0.39, 0.46, 0.53, 0.6, 0.65, U_CH, 0.74, 0.78, 0.8, 0.84, 0.88,
      0.92, 0.955, 0.98]
bm = bmesh.new()
rings = []
for u in US:
    d = B0 + BL * u
    rings.append([bm.verts.new(P(d, x, y)) for (x, y, _) in section(u)])
n = len(rings[0])
for i in range(len(rings) - 1):
    a, b = rings[i], rings[i + 1]
    for j in range(n):
        jj = (j + 1) % n
        f = bm.faces.new((a[j], a[jj], b[jj], b[j]))
        f.material_index = BAND_MAT[j]
tip_v = bm.verts.new(P(B1))
for j in range(n):
    f = bm.faces.new((rings[-1][j], rings[-1][(j + 1) % n], tip_v))
    f.material_index = BAND_MAT[j]
bm.faces.new(list(reversed(rings[0])))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
blade = pl.obj_from_bm("blade", bm, None, 0)
for m in (EDGE, "M_Steel", "M_DarkMetal"):
    blade.data.materials.append(rw._resolve_mat(m))
rw.smooth(blade, 28)
parts.add(blade)

# --- runes inlaid in the channel on both faces, joined by a glowing line -------------------------------------------
RUNES = [(0.105, "tiwaz"), (0.225, "algiz"), (0.345, "ingwaz"), (0.465, "sowilo"), (0.585, "dagaz")]
GU, GV, GW = 0.0215, 0.032, 0.0062        # glyph width (across), height (along), stroke width
for side in (1, -1):
    u_dir = WD * side
    nf = NF * side

    def floor(u):
        cw, dep = chan(u)
        return half_t(u) - dep

    for (u, key) in RUNES:
        d = B0 + BL * u
        parts.add(mh.glyph2(key, P(d) + nf * floor(u), u_dir, AX, GU, GV, GW, 0.0038, CRYSTAL, "rune"))
    # line segments between the runes, plus the lead-in and the long run-out toward the tip
    stops = [0.04] + [u for (u, _) in RUNES] + [U_CH + 0.065]
    for (ua, ub) in zip(stops[:-1], stops[1:]):
        a = ua + (GV * 0.5) / BL if ua > 0.05 else ua
        b = ub - (GV * 0.5) / BL if ub < U_CH else ub
        if b <= a:
            continue
        um = (a + b) / 2
        da, db = B0 + BL * a, B0 + BL * b
        parts.add(pl.obox("rune_line", (db - da + GW, 0.0052, 0.0034), P((da + db) / 2) + nf * floor(um), AX, nf,
                          CRYSTAL))
    # a small diamond where the line starts, just above the guard
    parts.add(mh.glyph2("ingwaz", P(B0 + BL * 0.04) + nf * floor(0.04), u_dir, AX, 0.016, 0.016, 0.005, 0.0034,
                        CRYSTAL, "rune"))

# --- crossguard: a winged gear ------------------------------------------------------------------------------------
GC = P(0.124)
GR = 0.036
parts.add(nw.gear("guard_gear", GR, 12, 0.03, NF, GC, "M_Brass", depth=0.0068, chamfer=0.0022, x_hint=WD))
parts.add(pl.disc("guard_boss", 0.0235, 0.035, NF, GC, "M_Copper", 20, 0.35))
parts.add(pl.band("guard_ring", 0.0255, 0.036, 0.004, NF, GC, "M_Brass", 20, 0.4))
parts.add(nw.gem(GC + NF * 0.0172, NF, 0.0088, RARITY, "M_Brass", 8, "rarity_gem"))
parts.add(nw.stud(GC - NF * 0.017, -NF, 0.0125, 0.007, "M_Brass", 10))
for side in (1, -1):
    for k in range(4):
        a = math.radians(45 + 90 * k)
        parts.add(nw.stud(GC + (WD * math.cos(a) + AX * math.sin(a)) * 0.0185 + NF * side * 0.0172, NF * side,
                          0.0034, 0.0024, "M_Steel", 6))
# a scalloped brass wing on each side: a curved leading edge sweeping up toward the blade, four feather tips
WING = [(0.018, -0.017), (0.018, 0.02), (0.05, 0.036), (0.086, 0.058), (0.116, 0.084), (0.134, 0.104),
        (0.126, 0.07), (0.11, 0.052), (0.122, 0.044), (0.1, 0.022), (0.092, 0.017), (0.1, 0.004), (0.074, -0.008),
        (0.066, -0.012), (0.07, -0.03), (0.04, -0.026)]
WING_R = [0.002, 0.006, 0.02, 0.02, 0.012, 0.004, 0.012, 0.003, 0.006, 0.009, 0.003, 0.006, 0.008, 0.003, 0.006,
          0.008]
FEATHER_LINES = [[(0.04, 0.012), (0.075, 0.034), (0.106, 0.063)], [(0.04, 0.004), (0.07, 0.014), (0.098, 0.028)],
                 [(0.038, -0.006), (0.058, -0.008), (0.075, -0.01)]]
for s_ in (1, -1):
    wing = [(x * s_, y) for (x, y) in WING]
    radii = WING_R
    if s_ < 0:
        wing, radii = wing[::-1], radii[::-1]
    parts.add(nw.slab("wing", nw.rounded_poly(wing, radii, 3), 0.015, GC, WD, AX, "M_Brass", bevel=0.0035, segments=2,
                      angle=35))
    # copper inner panel standing proud of both faces, leaving a brass rim
    panel = nw.rounded_poly(mh.inset_poly(wing, 0.0062), [r * 0.6 for r in radii], 2)
    parts.add(nw.slab("wing_panel", panel, 0.0185, GC, WD, AX, "M_Copper", bevel=0.0018, segments=1, angle=35))
    for sd in (1, -1):
        for line in FEATHER_LINES:
            pts = [GC + WD * (s_ * x) + AX * y + NF * (sd * 0.0091) for (x, y) in line]
            parts.add(dh.ridge("feather_line", pts, NF * sd, 0.005, 0.0024, "M_Brass", 3, [1.0, 0.85, 0.55]))
        parts.add(nw.stud(GC + WD * (s_ * 0.03) + AX * 0.006 + NF * (sd * 0.0091), NF * sd, 0.0044, 0.0032,
                          "M_Brass", 6))

# --- collar, grip, ferrules, pommel --------------------------------------------------------------------------------
G0, G1 = -0.074, 0.068
parts.add(nw.spiral_wrap("grip_wrap", P(G0), AX, G1 - G0, 0.0244, 0.0034, 6.0, GRIP_LEATHER, segs=14,
                         steps_per_turn=6, x_hint=WD))
parts.add(pl.band("ferrule_top", 0.0285, 0.012, 0.009, AX, P(G1 + 0.004), "M_Brass", 20, 0.4))
parts.add(pl.lathe_axis("collar", [(0.0275, 0.0), (0.029, 0.004), (0.0262, 0.01), (0.0215, 0.014), (0.0205, 0.02),
                                   (0.0, 0.02)], AX, P(G1 + 0.008), 20, "M_Brass", True, True, 40))
parts.add(pl.band("ferrule_bottom", 0.0285, 0.012, 0.009, AX, P(G0 - 0.004), "M_Brass", 20, 0.4))
for d in (G1 + 0.004, G0 - 0.004):
    parts.add(pl.rivet_ring(P(d), AX, 0.0285, 6, 0.0034, 0.0026, "M_Copper", 30, 6))
PC = P(G0 - 0.036)
parts.add(pl.lathe_axis("pommel_neck", [(0.022, 0.0), (0.0235, 0.004), (0.016, 0.01), (0.0, 0.01)], -AX,
                        P(G0 - 0.009), 16, "M_Brass", True, False, 45))
parts.add(nw.gear("pommel_gear", 0.03, 10, 0.026, NF, PC, "M_Brass", depth=0.0062, chamfer=0.002, x_hint=WD))
for sd in (1, -1):
    parts.add(pl.lathe_axis("pommel_dome", [(0.0175, 0.0), (0.0172, 0.003), (0.0135, 0.0075), (0.007, 0.0105),
                                            (0.0, 0.0115)], NF * sd, PC + NF * (sd * 0.012), 16, "M_Copper", False,
                            False, 45))
parts.add(pl.lathe_axis("pommel_cap", [(0.0, 0.0), (0.0105, 0.0), (0.0098, 0.0045), (0.006, 0.0085), (0.0, 0.0095)],
                        -AX, P(G0 - 0.036 - 0.0285), 12, "M_Brass", False, False, 45))

sword = rw.join(parts, "Runeblade", origin=(0, 0, 0))

# --- glove: a hammer grip round the handle, like vm_thunder_wrench --------------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Tip", tuple(P(B1)))
pl.check("vm_runeblade", (0, 0, 0))
mh.report_nodes(["Runeblade", "Glove", "Tip"])
mh.crystal_audit()
rw.finish("vm_runeblade", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_runeblade")
mh.qa("vm_runeblade", placement=(0.26, -0.29, -0.40))
