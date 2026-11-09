"""vm_scepter: first-person "Sunlance Scepter", an ornate golden sun-standard that fires a beam.

Nodes (origin = grip centre; the shaft rises forward (-Y) and 42 degrees up, held like vm_staff; the sun head
is turned to face straight forward, -Y):
  Scepter  a slim ringed golden shaft (gold rings and knops on ivory enamel), a royal-blue leather grip
           between gold ferrules, a gold sun-ball pommel with a spike; the rarity gem on the knop above the
           hand (facing the player); a gold cup and crescent cradle at the shaft top holding the sun disc
           (raised rim, engraved rays and a bezel on the front, a domed boss, rivets and glowing gold runes
           on the back that faces the player) with nine radiating spikes and flame rays round its upper
           rim, and a big faceted crystal pointing forward from the centre (M_Crystal__a066ff - the only
           crystal on the model; the game swaps its tint per weapon).
  Halo     a thin glowing ring of eight small sun runes floating round the head, just outside the spike tips
           in the disc's plane (child of Scepter, origin at the head centre, ring axis along Blender Y; the
           game spins it about Y while the beam fires - nothing on the body crosses its path).
  Glove    the shared cartoon leather glove gripping the shaft (glove.py), wrist toward +Y.
  Emitter  empty at the crystal's front tip.
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
GOLD = rw.flat("Gold", "ffc93c", 0.3, 1.0)
ENAMEL = rw.flat("Enamel", "f4ead6", 0.45, 0.0)
SUN_RUNE = rw.glow("SunRune", "ffd86a", 3.0)
HALO_RING = rw.glow("HaloGlow", "ffb93a", 2.2)
WRAP = "M_Leather__1d3f9e"
FACE = 60.0                     # radial angle (0 = +X, 90 = up) that looks at the player's eye
X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))

F = mh.AxisFrame(42.0)
AX = F.AX
parts = mh.Parts()

# --- stations along the shaft --------------------------------------------------------------------------------------
D_W0, D_W1 = -0.072, 0.064      # grip
D_SH1 = 0.335                   # shaft top (cup)
R_SH = 0.0135                   # slim shaft radius
R_D = 0.056                     # sun disc radius
DISC_T = 0.022                  # sun disc thickness (along Y)
HC = F.P(D_SH1) + Z * (R_D + 0.014)          # head centre: the disc sits in a crescent on top of the shaft

# --- grip, ferrules, pommel ----------------------------------------------------------------------------------------
parts.add(nw.spiral_wrap("grip_wrap", F.P(D_W0), AX, D_W1 - D_W0, 0.0242, 0.0034, 6.0, WRAP, segs=14,
                         steps_per_turn=6, x_hint=F.side))
for d in (D_W0 - 0.004, D_W1 + 0.004):
    parts.add(pl.band("ferrule", 0.0285, 0.013, 0.009, AX, F.P(d), GOLD, 20, 0.4))
    parts.add(pl.rivet_ring(F.P(d), AX, 0.0285, 6, 0.0034, 0.0026, "M_Copper", FACE, 6))
D_PB = D_W0 - 0.032
parts.add(pl.lathe_axis("pommel_neck", [(0.0245, 0.0), (0.026, 0.004), (0.02, 0.009), (0.0145, 0.014), (0.0, 0.014)],
                        -AX, F.P(D_W0 - 0.009), 18, GOLD, True, False, 45))
parts.add(rw.sphere("pommel_ball", 0.0195, 14, 8, tuple(F.P(D_PB)), mat=GOLD))
pband = rw.torus("pommel_band", 0.0197, 0.0034, 18, 5, (0, 0, 0), mat="M_Copper")
pl.align(pband, AX, F.P(D_PB))
parts.add(pband)
for k in range(6):
    a = 30.0 + 60.0 * k
    parts.add(pl.crystal("pommel_ray", F.P(D_PB, a, 0.016), F.radial(a), 0.014, 0.0055, 4, 0.6, 0.0, GOLD, 45))
parts.add(pl.lathe_axis("pommel_spike", [(0.0085, 0.0), (0.0075, 0.004), (0.0045, 0.01), (0.0018, 0.018), (0.0, 0.024)],
                        -AX, F.P(D_PB - 0.016), 12, GOLD, True, False, 45))

# --- slim ringed shaft: ivory enamel with gold rings and two knops -------------------------------------------------
parts.add(pl.rod("shaft", F.P(D_W1 + 0.006), F.P(D_SH1 - 0.004), R_SH, 16, ENAMEL))
D_KNOP = 0.1
parts.add(pl.lathe_axis("knop", [(0.0215, -0.03), (0.0255, -0.026), (0.0255, -0.02), (0.019, -0.014), (0.0215, -0.008),
                                 (0.0265, 0.0), (0.0258, 0.008), (0.021, 0.015), (0.0165, 0.019), (0.0152, 0.024)],
                        AX, F.P(D_KNOP), 20, GOLD, True, True, 40))
parts.add(nw.gem(F.P(D_KNOP + 0.001, FACE, 0.0258), F.radial(FACE), 0.0072, RARITY, "M_Copper", 8, "rarity_gem"))
D_KNOP2 = 0.262
parts.add(pl.lathe_axis("knop2", [(0.0155, -0.02), (0.0205, -0.014), (0.0232, -0.005), (0.0225, 0.004), (0.018, 0.011),
                                  (0.0155, 0.016)], AX, F.P(D_KNOP2), 20, GOLD, True, True, 40))
for k in range(4):
    a = 45.0 + 90.0 * k
    parts.add(pl.crystal("knop_spur", F.P(D_KNOP2 - 0.004, a, 0.02), (F.radial(a) * 0.8 + AX * 0.6).normalized(),
                         0.018, 0.0055, 4, 0.6, 0.0, GOLD, 45))
for d in (0.134, 0.158, 0.182, 0.206, 0.23, 0.29, 0.31):
    parts.add(pl.band("shaft_ring", R_SH + 0.0042, 0.0062, 0.0055, AX, F.P(d), GOLD, 14, 0.3))

# --- cup and crescent cradle ------------------------------------------------------------------------------------------
parts.add(pl.lathe_axis("cup", [(R_SH + 0.001, -0.018), (0.0185, -0.012), (0.0225, -0.004), (0.024, 0.002),
                                (0.019, 0.006), (0.0, 0.006)], AX, F.P(D_SH1), 20, GOLD, True, True, 40))
A0, A1 = 192.0, 348.0           # the crescent hugs the disc's lower rim between these angles (0 = +X, 90 = up)


def disc_dir(a):
    return X * math.cos(math.radians(a)) + Z * math.sin(math.radians(a))


outer, inner = [], []
for i in range(13):
    a = A0 + (A1 - A0) * i / 12
    k = math.sin(math.pi * i / 12)
    outer.append(((R_D + 0.002 + 0.0155 * k) * math.cos(math.radians(a)), (R_D + 0.002 + 0.0155 * k) *
                  math.sin(math.radians(a))))
    inner.append(((R_D - 0.006) * math.cos(math.radians(a)), (R_D - 0.006) * math.sin(math.radians(a))))
cres = outer + inner[::-1]
parts.add(nw.slab("crescent", cres, DISC_T + 0.008, HC, X, Z, GOLD, bevel=0.003, segments=2, angle=35))
for a in (A0 + 4, A1 - 4):     # little balls on the horn tips
    parts.add(rw.sphere("horn_ball", 0.0058, 10, 6, tuple(HC + disc_dir(a) * (R_D + 0.003)), mat=GOLD))
for s in (-1, 1):              # rivets on both faces of the crescent
    for a in (230.0, 270.0, 310.0):
        parts.add(nw.stud(HC + disc_dir(a) * (R_D + 0.0085) + Y * (s * (DISC_T / 2 + 0.004)), Y * s, 0.0042, 0.003,
                          "M_Copper", 6))

# --- sun disc -----------------------------------------------------------------------------------------------------------
parts.add(pl.disc("sun_disc", R_D, DISC_T, Y, HC, GOLD, 32, 0.35))
# front (-Y): raised rim ring, engraved rays, crystal bezel
for s, base in ((-1, HC - Y * (DISC_T / 2)), (1, HC + Y * (DISC_T / 2))):
    rim = rw.torus("disc_rim", R_D - 0.006, 0.0042, 28, 5, (0, 0, 0), mat=GOLD)
    pl.align(rim, Y, base)
    parts.add(rim)
fb = HC - Y * (DISC_T / 2)
parts.add(pl.lathe_axis("bezel", [(0.0, 0.0), (0.0315, 0.0), (0.032, 0.004), (0.029, 0.008), (0.024, 0.0085),
                                  (0.0, 0.0085)], -Y, fb, 20, GOLD, False, False, 40))
for k in range(12):
    a = 15.0 + 30.0 * k
    d = disc_dir(a)
    parts.add(pl.obox("front_ray", (0.011 if k % 2 else 0.015, 0.004, 0.003), fb + d * (0.039 + (0.0 if k % 2 else 0.002))
                      - Y * 0.001, d, -Y, ENAMEL, rounded=0.0012, segments=1))
# back (+Y, toward the player): domed boss, rivet ring, glowing gold runes
bb = HC + Y * (DISC_T / 2)
parts.add(pl.lathe_axis("back_boss", [(0.0, 0.0), (0.026, 0.0), (0.0255, 0.004), (0.02, 0.009), (0.011, 0.0125),
                                      (0.0, 0.0135)], Y, bb, 20, GOLD, False, False, 45))
parts.add(pl.band("boss_ring", 0.0272, 0.006, 0.0035, Y, bb + Y * 0.002, "M_Copper", 18, 0.4))
for k in range(8):
    a = 22.5 + 45.0 * k
    parts.add(nw.stud(bb + disc_dir(a) * 0.0425, Y, 0.0036, 0.0026, "M_Copper", 6))
for k, key in enumerate(("sowilo", "tiwaz", "dagaz", "ingwaz")):
    a = 0.0 + 90.0 * k
    d = disc_dir(a)
    t = Y.cross(d).normalized()
    parts.add(mh.glyph2(key, bb + d * 0.0335, -t, d, 0.0085, 0.0115, 0.0028, 0.002, SUN_RUNE, "back_rune"))

# --- radiating spikes and flame rays round the upper rim --------------------------------------------------------------
for i in range(9):
    a = -30.0 + 30.0 * i
    d = disc_dir(a)
    if i % 2 == 0:              # long straight spike: a four-sided gold point
        parts.add(pl.crystal("spike", HC + d * (R_D - 0.008), d, 0.052, 0.0105, 4, 0.7, 0.0, GOLD, 45))
    else:                       # short wavy flame ray
        tng = Y.cross(d).normalized()
        pts = [HC + d * (R_D - 0.004), HC + d * (R_D + 0.012) + tng * 0.006, HC + d * (R_D + 0.024) - tng * 0.005,
               HC + d * (R_D + 0.036) + tng * 0.002]
        parts.add(pl.sausage("flame_ray", pts, [0.0085, 0.0074, 0.0055, 0.003], 7, 3, GOLD, (True, True), 2, True, 60,
                             (0.62, 1.0), Y))
# little gold beads between the rays on the rim
for i in range(8):
    a = -15.0 + 30.0 * i
    parts.add(rw.sphere("rim_bead", 0.0045, 6, 4, tuple(HC + disc_dir(a) * (R_D + 0.001)), mat=GOLD))

# --- the faceted crystal pointing forward -------------------------------------------------------------------------------
CR_L = 0.1
cprof = [(0.0, 0.0), (0.0205, 0.004), (0.0278, 0.015), (0.0285, 0.031), (0.0228, 0.055), (0.0, CR_L)]
parts.add(mh.gem_lathe("crystal", cprof, -Y, fb - Y * 0.002, 8, CRYSTAL, True, 22.5, X))
for k in range(4):
    a = 45.0 + 90.0 * k
    d = disc_dir(a)
    parts.add(pl.sausage("crystal_claw", [fb - Y * 0.004 + d * 0.0292, fb - Y * 0.013 + d * 0.0318,
                                          fb - Y * 0.022 + d * 0.0278], [0.0038, 0.0036, 0.0028], 6, 3, GOLD,
                         (True, True), 2, True, 60))
TIP = fb - Y * (0.002 + CR_L)

scepter = rw.join(parts, "Scepter", origin=(0, 0, 0))

# --- Halo: a thin glowing ring of small sun runes round the head (spins about Y) ---------------------------------
hparts = mh.Parts()
R_H = 0.108                     # outside the spike tips; the shaft and crescent stay inside the ring
HB = HC.copy()
hring = rw.torus("halo_ring", R_H, 0.0047, 44, 6, (0, 0, 0), mat=HALO_RING)
pl.align(hring, Y, HB)
hparts.add(hring)
for k in range(8):
    a = 22.5 + 45.0 * k
    c = HB + disc_dir(a) * R_H
    hparts.add(mh.star_rune("halo_rune", c, X, Z, 0.0165, 0.0078, 8, 0.0052, SUN_RUNE, HALO_RING))
halo = rw.join(list(hparts), "Halo", origin=tuple(HC))
pl.parent_keep(halo, scepter)

# --- glove: the same hammer grip as vm_staff ------------------------------------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Emitter", tuple(TIP))
pl.check("vm_scepter", (0, 0, 0))
mh.report_nodes(["Scepter", "Halo", "Glove", "Emitter"])
mh.crystal_audit()
rw.finish("vm_scepter", "weapons", icon=False)

import wpn_icon  # noqa: E402
# the default icon view sees the forward-facing sun disc edge-on; turn a little toward the front so it reads
wpn_icon.render("vm_scepter", view=(-0.8, -0.7, 0.42))
mh.qa("vm_scepter")
