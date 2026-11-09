"""item_vault: "Ley Vault", a heavy rune-stone strongbox, 1.2 (X) x 0.8 (Y) x 0.95 (Z) m. The lock faces -Y.

Nodes (origin of the model = the ground centre, an intentional exception for containers):
  Vault   static body: a chamfered dark rune-stone block (M_StoneRough, slate tint) on a heavier plinth
          (M_Stone, darker tint), wrapped by riveted brass bands with brass corner guards, glowing teal rune
          circuit lines and glyphs carved into the stone (rw.glow 39d5c4), a big round brass rune lock on the
          front (a ring of glowing glyphs round a teal ley-crystal keystone) and brass hinge knuckles at the back.
          Inside: a violet velvet hollow ("VelvetViolet") with a heap of gold coins and a glowing ley crystal.
  Lid     child of Vault, origin ON THE HINGE AXIS (back top edge, axis along X, y = HINGE_Y, z = BODY_H).
          A stepped stone lid with brass corner caps, a glowing rune circle on top, a brass tongue that hangs
          over the lock, and a velvet-lined recess underneath. Open it by rotating about its local X by a
          NEGATIVE angle (about -100 deg): the front rises and swings back over the hinge.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_vault"
rw.reset()
il.preview_glow("M_Crystal", "3ad9c8", "40e8da", 0.6)   # preview/icon only: Godot uses its crystal set

STONE = "M_StoneRough__5d6678"
DARK = "M_Stone__454b58"
brass = il.mat("M_Brass")
glow = il.mat("VaultGlow")
BODY_H = 0.62
BX, BY = 0.55, 0.35            # body block half-extents
IX, IY = 0.44, 0.24            # hollow half-extents
HINGE_Y = 0.375
FLOOR = 0.44


def cham(name, size, loc, m, b=0.025):
    o = rw.box(name, size, loc, mat=il.mat(m))
    rw.add_bevel(o, b, 1, 40, harden=False)
    rw.apply_modifiers(o)
    return o


body = []
# stone: plinth, block (hollowed), cornice ---------------------------------------------------------------------
body.append(cham("plinth", (1.2, 0.8, 0.11), (0, 0, 0.055), DARK, 0.03))
block = cham("block", (2 * BX, 2 * BY, BODY_H - 0.16), (0, 0, 0.11 + (BODY_H - 0.16) / 2), STONE, 0.03)
cornice = cham("cornice", (2 * BX + 0.06, 2 * BY + 0.06, 0.07), (0, 0, BODY_H - 0.035), DARK, 0.02)
pl.carve(block, [rw.box("hollow", (2 * IX, 2 * IY, 0.5), (0, 0, FLOOR + 0.25))])
pl.carve(cornice, [rw.box("hollow", (2 * IX, 2 * IY, 0.5), (0, 0, FLOOR + 0.25))])
body += [block, cornice]
body.append(il.liner("lining", -IX + 0.004, IX - 0.004, -IY + 0.004, IY - 0.004, FLOOR, BODY_H - 0.003, "VelvetViolet"))

# brass bands (front/back/sides) with rivets and corner guards ---------------------------------------------------
for z in (0.17,):
    for sy in (-1, 1):
        body.append(pl.obox("band", (2 * BX + 0.02, 0.02, 0.06), (0, sy * (BY + 0.006), z), rounded=0.006, segments=1,
                            mat=brass))
    for sx in (-1, 1):
        body.append(pl.obox("band", (0.02, 2 * BY + 0.02, 0.06), (sx * (BX + 0.006), 0, z), rounded=0.006, segments=1,
                            mat=brass))
for sx in (-1, 1):
    for sy in (-1, 1):
        c = V((sx * (BX - 0.035), sy * (BY - 0.035), 0.11 + (BODY_H - 0.18) / 2))
        body.append(pl.obox("guard", (0.1, 0.1, BODY_H - 0.17), c + V((sx * 0.012, sy * 0.012, 0)), rounded=0.012,
                            segments=1, mat=brass))
        for z in (0.25, 0.48):
            body.append(pl.rivet(V((sx * (BX + 0.026), sy * (BY - 0.01), z)), (sx, 0, 0), 0.012, 0.008, brass, 5))
            body.append(pl.rivet(V((sx * (BX - 0.01), sy * (BY + 0.026), z)), (0, sy, 0), 0.012, 0.008, brass, 5))

# the round rune lock on the front --------------------------------------------------------------------------------
LZ = 0.39
LC = V((0, -BY, LZ))
body.append(il.lathe("lock", [(0.0, 0.0), (0.15, 0.0), (0.155, 0.012), (0.15, 0.03), (0.13, 0.036), (0.115, 0.03),
                              (0.06, 0.036), (0.0, 0.036)], (0, -1, 0), tuple(LC - V((0, 0.004, 0))), 28, "M_Brass", 35))
for i, k in enumerate(("algiz", "kenaz", "tiwaz", "sowilo", "ingwaz", "fehu")):
    a = math.radians(90 + 60 * i)
    p = LC + V((math.cos(a) * 0.087, -0.03, math.sin(a) * 0.087))
    body += pl.glyph(k, p, (1, 0, 0), (0, 0, 1), 0.04, 0.009, 0.008, glow, "lockrune")
body.append(il.lathe("keystone_ring", [(0.04, -0.01), (0.052, -0.01), (0.055, 0.0), (0.05, 0.012), (0.04, 0.012),
                                       (0.04, -0.01)], (0, -1, 0), tuple(LC + V((0, -0.036, 0))), 18, "M_Brass", 40))
body.append(pl.crystal("keystone", LC + V((0, -0.02, 0)), (0, -1, 0), 0.046, 0.044, 6, 0.6, 0.0, il.mat("M_Crystal"), 0))
for k in range(4):
    a = math.radians(45 + 90 * k)
    body.append(pl.rivet(LC + V((math.cos(a) * 0.135, -0.03, math.sin(a) * 0.135)), (0, -1, 0), 0.011, 0.007, brass, 5))

# glowing rune circuit lines on the front, glyphs on the sides and back -----------------------------------------
FY = -BY - 0.001
for sx in (-1, 1):
    path = [V((sx * 0.155, FY, LZ)), V((sx * 0.3, FY, LZ)), V((sx * 0.3, FY, 0.28)), V((sx * 0.42, FY, 0.28))]
    for a, b in zip(path[:-1], path[1:]):
        body.append(pl.beam_between("line", a, b, (0.028, 0.014), glow, up=(0, -1, 0)))
    body.append(pl.disc("node", 0.032, 0.014, (0, -1, 0), path[-1], glow, 12, 0.0))
    body.append(pl.disc("node", 0.026, 0.014, (0, -1, 0), V((sx * 0.3, FY, 0.5)), glow, 12, 0.0))
    body.append(pl.beam_between("line", V((sx * 0.3, FY, LZ)), V((sx * 0.3, FY, 0.5)), (0.028, 0.014), glow, up=(0, -1, 0)))
for sx, key in ((-1, "othala"), (1, "dagaz")):
    body += pl.glyph(key, V((sx * (BX + 0.001), 0, 0.4)), (0, -sx, 0), (0, 0, 1), 0.22, 0.032, 0.014, glow, "siderune")
body += pl.glyph("ingwaz", V((0, BY + 0.001, 0.4)), (-1, 0, 0), (0, 0, 1), 0.22, 0.032, 0.014, glow, "backrune")
# hinge knuckles at the back
for sx in (-1, 1):
    body.append(rw.cylinder("hinge", 0.026, 0.14, 10, (sx * 0.3, HINGE_Y, BODY_H), (0, 90, 0), brass))
    body.append(pl.obox("hinge_leaf", (0.12, 0.016, 0.1), (sx * 0.3, BY + 0.012, BODY_H - 0.07), rounded=0.006,
                        segments=1, mat=brass))

# treasure inside: gold heap and a glowing ley crystal
body += il.coin_pile((0.0, 0.02, FLOOR), 0.3, 0.17, 0.13, 9, 6, coin_r=0.05)
body.append(pl.crystal("loot_crystal", (0.17, -0.04, FLOOR + 0.05), (0.35, -0.25, 1), 0.2, 0.045, 6, 0.3, 0.1,
                       il.mat("M_Crystal"), 10))

vault = rw.join(body, "Vault", origin=(0, 0, 0))
rw.smooth(vault, 35)

# lid ---------------------------------------------------------------------------------------------------------
lid = []
L0, L1, L2, L3 = BODY_H, BODY_H + 0.12, BODY_H + 0.24, 0.95
slab = cham("lid_slab", (1.16, 0.76, L1 - L0), (0, 0, (L0 + L1) / 2), DARK, 0.025)
pl.carve(slab, [rw.box("recess", (2 * IX, 2 * IY, 0.12), (0, 0, L0))])
lid.append(slab)
lid.append(il.liner("lid_lining", -IX + 0.004, IX - 0.004, -IY + 0.004, IY - 0.004, L0 + 0.058, L0 + 0.002,
                    "VelvetViolet"))
lid.append(cham("lid_tier", (1.0, 0.6, L2 - L1 + 0.01), (0, 0, (L1 + L2) / 2), STONE, 0.03))
cap = il.lathe("lid_cap", [(0.0, L2 - 0.005), (0.42, L2 - 0.005), (0.36, L3), (0.0, L3)], (0, 0, 1), (0, 0, 0), 4, None,
               0, spin=45)
pl.xform(cap, il.Matrix.Diagonal((1.0, 0.5, 1.0, 1.0)))
rw.set_mat(cap, il.mat(DARK))
rw.flat_shade(cap)
lid.append(cap)
# rune circle on the top (half sunk) with a glyph
lid.append(rw.torus("runering", 0.105, 0.016, 24, 5, (0, 0, L3 + 0.003), (0, 0, 0), glow))
lid += pl.glyph("sowilo", V((0, 0, L3 + 0.003)), (1, 0, 0), (0, 1, 0), 0.14, 0.028, 0.014, glow, "toprune")
# brass corner caps on the slab, brass edge bands on the tier
for sx in (-1, 1):
    for sy in (-1, 1):
        lid.append(pl.obox("lidcap", (0.11, 0.11, L1 - L0 + 0.02), (sx * 0.535, sy * 0.335, (L0 + L1) / 2),
                           rounded=0.016, segments=1, mat=brass))
        lid.append(pl.rivet(V((sx * 0.535, sy * 0.39, (L0 + L1) / 2)), (0, sy, 0), 0.012, 0.008, brass, 5))
for sy in (-1, 1):
    lid.append(pl.obox("tierband", (1.02, 0.02, 0.04), (0, sy * 0.3, L1 + 0.03), rounded=0.006, segments=1, mat=brass))
# brass tongue hanging over the lock, with a glowing glyph
TC = V((0, -0.38 - 0.004, L0 - 0.01))
lid.append(il.wrap_prism("tongue", il.capsule_pts(0.1, 0.17), il.plane_map(TC, (1, 0, 0), (0, 0, 1), 0.0, 0.024), brass, 30))
lid += pl.glyph("tiwaz", TC + V((0, -0.024, 0.015)), (1, 0, 0), (0, 0, 1), 0.06, 0.012, 0.006, glow, "tonguerune")

lid_o = rw.join(lid, "Lid", origin=(0, HINGE_Y, BODY_H))
rw.smooth(lid_o, 35)
pl.parent_keep(lid_o, vault)

il.finish_container(ASSET, vault, lid_o, -100.0, (1.2, 0.8, 0.95))
