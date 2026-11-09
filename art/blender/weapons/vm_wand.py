"""vm_wand: first-person "Ley Wand", a slender, elegant ivory wand (the game reuses it for several wands -
fire, frost, ... - and tints the crystal per wand).

Nodes (origin = grip centre; the wand runs forward (-Y) and 32 degrees up, held like vm_staff):
  Wand     a pale ivory/white-birch shaft caged by two counter-wound filigree wires (brass and copper) with
           beads where they cross and mirrored brass scroll curls in the openings; a brass handle with a
           spiral teal leather wrap between riveted brass ferrules, a brass pommel bead with a copper band and
           a finial; a brass collar above the hand carrying the claw-set rarity gem (facing the player); a
           beaded brass crown cup with four leaf sepals curling down onto the shaft and a lotus of gold petal
           claws (four big with beaded tips, four small) hugging the big faceted crystal tip
           (M_Crystal__a066ff - the only crystal on the model; the game swaps its tint per wand).
  Glove    the shared cartoon leather glove wrapped round the handle (glove.py), wrist toward +Y.
  Emitter  empty at the crystal tip.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import magic_weapon_helpers as mh  # noqa: E402

glove, pl, rw, V, dh, nw = mh.glove, mh.pl, mh.rw, mh.V, mh.dh, mh.nw
rw.reset()

CRYSTAL = mh.crystal_mat()
RARITY = mh.rarity_mat()
IVORY = rw.flat("Ivory", "f2e7cf", 0.5, 0.0)
WRAP = "M_Leather__17707a"
FACE = 60.0                     # radial angle (0 = +X, 90 = up) that looks at the player's eye

F = mh.AxisFrame(32.0)
AX = F.AX
parts = mh.Parts()

# --- key stations along the wand axis (metres from the grip centre) ------------------------------------------------
D_BEAD = -0.1                   # pommel bead centre
D_W0, D_W1 = -0.072, 0.064      # leather wrap
D_COL0, D_COL1 = 0.072, 0.106   # gem collar
D_SH0, D_SH1 = 0.096, 0.218     # ivory shaft
D_CUP = 0.206                   # crown cup base
CUP_H = 0.022
D_CR = D_CUP + 0.011            # crystal foot (sunk in the cup)
CR_L = 0.118                    # crystal length


def shaft_r(d):
    t = max(0.0, min(1.0, (d - D_SH0) / (D_SH1 - D_SH0)))
    return 0.0186 - 0.005 * t + 0.0016 * math.sin(math.pi * t)


# --- ivory shaft ---------------------------------------------------------------------------------------------------
ds = [D_SH0 + (D_SH1 - D_SH0) * i / 10 for i in range(11)]
parts.add(pl.sausage("shaft", [F.P(d) for d in ds], [shaft_r(d) for d in ds], 16, 2, IVORY, (False, False), 2,
                     True, 50))

# --- filigree cage: a brass wire wound one way, a copper wire the other, beads where they cross ------------------
FD0, FD1, TURNS = D_COL1 + 0.002, D_CUP + 0.002, 1.5
WIRE = 0.0041
parts.add(mh.surface_helix("filigree_brass", F, FD0, FD1, shaft_r, TURNS, FACE, WIRE, "M_Brass", 0.28, 12, 7))
parts.add(mh.surface_helix("filigree_copper", F, FD0, FD1, shaft_r, -TURNS, FACE, WIRE, "M_Copper", 0.28, 12, 7))
k = 0
while True:
    t = k * 180.0 / (360.0 * TURNS)
    if t > 1.0001:
        break
    p, d = mh.helix_point(F, FD0, FD1, shaft_r, TURNS, FACE, t, WIRE * 0.9)
    if 0.0 < t < 0.999:
        parts.add(rw.sphere("cross_bead", 0.0062, 10, 6, tuple(p), mat="M_Brass"))
    k += 1
# where the wires cross on one side the cage is open on the other: a mirrored pair of brass scroll curls fills
# the openings that face the player, a copper bead the ones on the far side
SC_R = 0.0088
for k in range(1, 4):
    t = k * 180.0 / (360.0 * TURNS)
    if t > 0.98:
        continue
    _, d = mh.helix_point(F, FD0, FD1, shaft_r, TURNS, FACE, t)
    ang = FACE + 180.0 * (k + 1)
    if k % 2 == 1:
        for s in (-1, 1):
            pts2, tap = mh.spiral2d(SC_R, 0.85, 90.0, True, 8, 0.3, tail=(-SC_R * 0.95, SC_R * 1.25))
            path = [(y - 0.002, s * (SC_R * 0.92 + x * 0.92)) for (x, y) in pts2]
            parts.add(mh.cyl_ridge("scroll", F, path, shaft_r, d, ang, 0.0027, "M_Brass", 0.3, tap, 6, 2))
        parts.add(rw.sphere("scroll_bead", 0.0045, 8, 5, tuple(F.P(d + SC_R * 1.05, ang, shaft_r(d) + 0.002)),
                            mat="M_Brass"))
    else:
        parts.add(rw.sphere("back_bead", 0.0052, 8, 5, tuple(F.P(d, ang, shaft_r(d) + 0.0022)), mat="M_Copper"))

# --- handle: spiral leather wrap between riveted brass ferrules ----------------------------------------------------
parts.add(nw.spiral_wrap("grip_wrap", F.P(D_W0), AX, D_W1 - D_W0, 0.0242, 0.0034, 6.0, WRAP, segs=14,
                         steps_per_turn=6, x_hint=F.side))
for d in (D_W0 - 0.004, D_W1 + 0.004):
    parts.add(pl.band("ferrule", 0.0285, 0.013, 0.009, AX, F.P(d), "M_Brass", 20, 0.4))
    parts.add(pl.rivet_ring(F.P(d), AX, 0.0285, 6, 0.0034, 0.0026, "M_Copper", FACE, 6))

# --- pommel: brass neck, bead with a copper band, little finial -----------------------------------------------------
parts.add(pl.lathe_axis("pommel_neck", [(0.0248, 0.0), (0.0262, 0.004), (0.0225, 0.009), (0.0155, 0.012),
                                        (0.0135, 0.016), (0.0, 0.016)], -AX, F.P(D_W0 - 0.009), 20, "M_Brass",
                        True, False, 45))
parts.add(rw.sphere("pommel_bead", 0.0185, 16, 10, tuple(F.P(D_BEAD)), mat="M_Brass"))
band = rw.torus("pommel_band", 0.0186, 0.0034, 18, 5, (0, 0, 0), mat="M_Copper")
pl.align(band, AX, F.P(D_BEAD))
parts.add(band)
parts.add(pl.lathe_axis("pommel_finial", [(0.0085, 0.0), (0.0076, 0.003), (0.0052, 0.007), (0.0026, 0.011),
                                          (0.0, 0.014)], -AX, F.P(D_BEAD - 0.015), 12, "M_Brass", True, False,
                        45))

# --- gem collar above the hand, with the claw-set rarity gem facing the player --------------------------------------
parts.add(pl.lathe_axis("gem_collar", [(0.0262, 0.0), (0.028, 0.004), (0.0283, 0.011), (0.0262, 0.019),
                                       (0.0228, 0.026), (0.0205, 0.031), (0.0198, D_COL1 - D_COL0)], AX,
                        F.P(D_COL0), 20, "M_Brass", True, True, 40))
parts.add(pl.band("collar_lip", 0.0214, 0.006, 0.004, AX, F.P(D_COL1 - 0.002), "M_Copper", 18, 0.4))
D_GEM = D_COL0 + 0.012
gn = (F.radial(FACE) * 0.94 + AX * 0.34).normalized()
parts.add(nw.gem(F.P(D_GEM, FACE, 0.0268), gn, 0.0068, RARITY, "M_Brass", 8, "rarity_gem"))

# --- crown cup with a beaded rim and four leaf sepals curling down onto the shaft ----------------------------------
CUP_R = 0.0315
parts.add(pl.lathe_axis("crown_cup", [(0.0138, -0.004), (0.0165, 0.002), (0.0215, 0.007), (0.0272, 0.0125),
                                      (CUP_R, 0.0178), (CUP_R - 0.001, CUP_H), (CUP_R - 0.006, CUP_H + 0.0012),
                                      (0.0, CUP_H + 0.0012)], AX, F.P(D_CUP), 22, "M_Brass", True, True, 40))
parts.add(pl.band("cup_ring", 0.0185, 0.007, 0.0055, AX, F.P(D_CUP + 0.001), "M_Copper", 18, 0.4))
for k in range(10):
    a = 18.0 + 36.0 * k
    parts.add(rw.sphere("rim_bead", 0.0039, 8, 5, tuple(F.P(D_CUP + CUP_H - 0.0008, a, CUP_R - 0.0012)),
                        mat="M_Brass"))
for k in range(4):
    a = FACE + 90.0 * k
    out = F.radial(a)
    pts = [F.P(D_CUP + 0.008, a, 0.0215), F.P(D_CUP - 0.004, a, 0.0236), F.P(D_CUP - 0.018, a, 0.0212),
           F.P(D_CUP - 0.027, a, shaft_r(D_CUP - 0.027) + 0.0035)]
    parts.add(pl.sausage("sepal", pts, [0.0052, 0.0056, 0.0044, 0.003], 8, 3, "M_Brass", (True, True), 2, True, 60,
                         (0.7, 1.45), out))
    parts.add(rw.sphere("sepal_tip", 0.0037, 8, 5, tuple(pts[-1] + out * 0.001), mat="M_Brass"))

# --- the big faceted crystal ------------------------------------------------------------------------------------------
cprof = [(0.0, 0.0), (0.019, 0.008), (0.033, 0.022), (0.0365, 0.039), (0.0348, 0.061), (0.0255, 0.087),
         (0.0, CR_L)]
parts.add(mh.gem_lathe("crystal", cprof, AX, F.P(D_CR), 8, CRYSTAL, True, 22.5, F.side))
TIP = F.P(D_CR + CR_L)


def crystal_r(h):
    for (r0, h0), (r1, h1) in zip(cprof[:-1], cprof[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / max(h1 - h0, 1e-6)
    return 0.0


# --- a lotus of gold petal claws hugging the crystal: four big ones with beaded tips, four small ones between -----
H0 = D_CUP + CUP_H - 0.005 - D_CR             # petal roots, measured from the crystal foot
for k in range(8):
    big = k % 2 == 0
    a = 15.0 + 45.0 * k
    out = F.radial(a)
    hs = [H0, H0 + 0.012, H0 + 0.026, H0 + 0.039, H0 + 0.05] if big else [H0, H0 + 0.01, H0 + 0.02, H0 + 0.029]
    pts = [F.P(D_CR + h, a, max(crystal_r(h), CUP_R - 0.004) + (0.0036 if i else 0.0)) for i, h in enumerate(hs)]
    pts[-1] = pts[-1] - out * 0.0012
    radii = [0.0058, 0.0072, 0.0066, 0.0048, 0.0026] if big else [0.0052, 0.0058, 0.0044, 0.0024]
    parts.add(pl.sausage("petal" if big else "petal_small", pts, radii, 8, 3, "M_Brass", (True, True), 2, True,
                         60, (0.52, 1.65), out))
    if big:
        parts.add(rw.sphere("petal_bead", 0.0043, 8, 5, tuple(pts[-1] + out * 0.0022), mat="M_Brass"))

wand = rw.join(parts, "Wand", origin=(0, 0, 0))

# --- glove: the same hammer grip as vm_staff ------------------------------------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Emitter", tuple(TIP))
pl.check("vm_wand", (0, 0, 0))
mh.report_nodes(["Wand", "Glove", "Emitter"])
mh.crystal_audit()
rw.finish("vm_wand", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_wand")
mh.qa("vm_wand")
