"""vm_orb: first-person "Gloom Orb", a sceptre-like focus topped by a caged crystal orb.

Nodes (origin = grip centre; the sceptre runs forward (-Y) and 36 degrees up, held like vm_staff):
  OrbFocus  a short brass sceptre handle (twisted brass fluting between ringed ferrules, a brass pommel knob
            with a copper band and finial), a brass knop above the hand carrying the claw-set rarity gem
            (facing the player), a ringed dark-iron neck and a beaded brass cup from which four strap ribs
            curve round the orb, each sprouting a pair of flat filigree scrolls, and meet in a crown finial; a brass
            ring round the cage carries three small slate runestones (M_Stone) in brass cradles, each with
            a glowing teal rune facing outward.
  Orb       the big faceted crystal orb inside the cage (M_Crystal__a066ff - the only crystal on the model;
            the game swaps its tint per weapon). Child of OrbFocus, origin at its centre; the game slowly
            spins and pulses it, and it clears the cage at up to ~1.1x scale.
  Glove     the shared cartoon leather glove gripping the handle (glove.py), wrist toward +Y.
  Emitter   empty just in front (-Y) of the orb, in the gap between the two lower ribs.
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
RUNE = rw.glow("RuneTeal", "39d5c4", 3.0)
STONE = "M_Stone__59607a"            # dark slate
FACE = 60.0                     # radial angle (0 = +X, 90 = up) that looks at the player's eye

F = mh.AxisFrame(36.0)
AX = F.AX
parts = mh.Parts()

# --- stations along the axis ------------------------------------------------------------------------------------------
D_W0, D_W1 = -0.072, 0.064      # grip
D_KNOP = 0.106                  # knop with the rarity gem
D_NECK0, D_NECK1 = 0.126, 0.14
R_ORB = 0.052
D_C = 0.218                     # orb centre
C = F.P(D_C)
R_RIB = R_ORB + 0.0096          # rib centre-line radius (the orb clears the ribs up to ~1.1x scale)


def sph(theta, phi, r):
    """Point on a sphere round the orb centre: theta = polar angle from AX (degrees), phi = radial angle."""
    t = math.radians(theta)
    return C + AX * (math.cos(t) * r) + F.radial(phi) * (math.sin(t) * r)


# --- grip: twisted brass fluting between ringed ferrules ----------------------------------------------------------
parts.add(nw.spiral_wrap("grip_flutes", F.P(D_W0), AX, D_W1 - D_W0, 0.0236, 0.0036, 3.0, "M_Brass", segs=16,
                         steps_per_turn=8, x_hint=F.side))
parts.add(pl.rod("grip_core", F.P(D_W0 - 0.002), F.P(D_W1 + 0.002), 0.0232, 16, "M_DarkMetal"))
for d in (D_W0 - 0.004, D_W1 + 0.004):
    parts.add(pl.band("ferrule", 0.0288, 0.012, 0.009, AX, F.P(d), "M_Brass", 20, 0.4))
    parts.add(pl.band("ferrule_ring", 0.0262, 0.02, 0.004, AX, F.P(d), "M_Copper", 20, 0.4))
    parts.add(pl.rivet_ring(F.P(d), AX, 0.0288, 6, 0.0034, 0.0026, "M_Steel", FACE, 6))

# --- pommel knob ------------------------------------------------------------------------------------------------------
D_PB = D_W0 - 0.03
parts.add(pl.lathe_axis("pommel_neck", [(0.0245, 0.0), (0.026, 0.004), (0.02, 0.009), (0.015, 0.013), (0.0, 0.013)],
                        -AX, F.P(D_W0 - 0.009), 18, "M_Brass", True, False, 45))
parts.add(rw.sphere("pommel_knob", 0.0195, 16, 10, tuple(F.P(D_PB)), mat="M_Brass"))
band = rw.torus("pommel_band", 0.0196, 0.0034, 18, 5, (0, 0, 0), mat="M_Copper")
pl.align(band, AX, F.P(D_PB))
parts.add(band)
parts.add(pl.lathe_axis("pommel_finial", [(0.009, 0.0), (0.008, 0.003), (0.0055, 0.0075), (0.0026, 0.012),
                                          (0.0, 0.0155)], -AX, F.P(D_PB - 0.016), 12, "M_Brass", True, False, 45))

# --- knop above the hand with the rarity gem ----------------------------------------------------------------------------
parts.add(pl.lathe_axis("collar", [(0.0262, 0.0), (0.0282, 0.004), (0.0262, 0.009), (0.0205, 0.013), (0.0185, 0.017)],
                        AX, F.P(D_W1 + 0.008), 20, "M_Brass", True, False, 40))
parts.add(pl.lathe_axis("knop", [(0.017, -0.026), (0.0225, -0.019), (0.0265, -0.01), (0.0272, 0.0), (0.0255, 0.009),
                                 (0.02, 0.016), (0.0155, 0.02), (0.0148, 0.024)], AX, F.P(D_KNOP), 22, "M_Brass",
                        True, True, 40))
parts.add(pl.band("knop_band", 0.0278, 0.006, 0.004, AX, F.P(D_KNOP - 0.002), "M_Copper", 22, 0.4))
gn = F.radial(FACE)
parts.add(nw.gem(F.P(D_KNOP - 0.002, FACE, 0.0268), gn, 0.0072, RARITY, "M_Brass", 8, "rarity_gem"))

# --- dark-iron neck with brass rings ---------------------------------------------------------------------------------
parts.add(pl.rod("neck", F.P(D_NECK0 - 0.004), F.P(D_NECK1 + 0.006), 0.0142, 16, "M_DarkMetal"))
for d in (D_NECK0 + 0.004, D_NECK0 + 0.013):
    parts.add(pl.band("neck_ring", 0.0182, 0.0065, 0.005, AX, F.P(d), "M_Brass", 18, 0.4))

# --- cage cup ------------------------------------------------------------------------------------------------------------
CUP_TOP = D_C + R_RIB * math.cos(math.radians(146))      # where the ribs leave the cup
CUP_R = R_RIB * math.sin(math.radians(146))
parts.add(pl.lathe_axis("cup", [(0.0142, 0.0), (0.0175, 0.006), (0.0235, 0.013), (CUP_R - 0.001, CUP_TOP - D_NECK1 - 0.004),
                                (CUP_R + 0.002, CUP_TOP - D_NECK1), (CUP_R - 0.004, CUP_TOP - D_NECK1 + 0.0025),
                                (0.0, CUP_TOP - D_NECK1 + 0.0025)], AX, F.P(D_NECK1), 22, "M_Brass", True, True, 40))
for k in range(10):
    a = 18.0 + 36.0 * k
    parts.add(rw.sphere("cup_bead", 0.0038, 6, 4, tuple(F.P(CUP_TOP - 0.0035, a, CUP_R + 0.0028)), mat="M_Brass"))

# --- four strap ribs round the orb, meeting in a crown finial ---------------------------------------------------------
RIBS = (45.0, 135.0, 225.0, 315.0)
TH = [146, 128, 110, 92, 74, 56, 38, 22, 11]
for phi in RIBS:
    pts = [sph(t, phi, R_RIB + 0.0018 * math.sin(math.radians(t))) for t in TH]
    radii = [0.0052, 0.0056, 0.0058, 0.0058, 0.0056, 0.0052, 0.0048, 0.0044, 0.004]
    parts.add(pl.sausage("rib", pts, radii, 8, 3, "M_Brass", (True, True), 2, True, 60, (0.72, 1.45), F.radial(phi)))
    # filigree: a mirrored pair of flat brass scrolls springing from the rib above the equator, lying on the cage
    tt = 60.0
    pc = sph(tt, phi, R_RIB)
    nrm = (pc - C).normalized()
    tang = F.radial(phi + 90.0)
    tang = (tang - tang.dot(nrm) * nrm).normalized()
    v_dir = nrm.cross(tang).normalized()
    for s_ in (1, -1):
        cc = pc + tang * (s_ * 0.0112) - nrm * 0.0008
        parts.add(mh.flat_scroll("rib_scroll", cc, tang * s_, v_dir, 0.0092, 0.0019, 0.0034, "M_Brass", 0.95, 270.0,
                                 s_ > 0, 10, tail=(-0.0112, 0.0085)))
    parts.add(rw.sphere("rib_bead", 0.0044, 8, 5, tuple(sph(tt + 9, phi, R_RIB + 0.0035)), mat="M_Brass"))
D_TOP = D_C + R_RIB
parts.add(pl.lathe_axis("finial_cap", [(0.0, -0.006), (0.0115, -0.005), (0.0142, 0.0), (0.0128, 0.0045),
                                       (0.0085, 0.008), (0.0045, 0.0115), (0.0036, 0.014)], AX, F.P(D_TOP - 0.002), 18,
                        "M_Brass", True, True, 40))
parts.add(pl.lathe_axis("finial_spike", [(0.0055, 0.0), (0.0062, 0.003), (0.0042, 0.007), (0.0018, 0.012),
                                         (0.0, 0.016)], AX, F.P(D_TOP + 0.011), 10, "M_Brass", True, False, 40))
parts.add(rw.sphere("finial_bead", 0.0056, 10, 6, tuple(F.P(D_TOP + 0.0135)), mat="M_Copper"))
for phi in RIBS:
    parts.add(rw.sphere("crown_bead", 0.0034, 8, 5, tuple(F.P(D_TOP - 0.001, phi, 0.0128)), mat="M_Brass"))

# --- ring of runestones round the cage -------------------------------------------------------------------------------------
TH_RING = 100.0
RING_R = (R_RIB + 0.0062) * math.sin(math.radians(TH_RING))
D_RING = D_C + (R_RIB + 0.0062) * math.cos(math.radians(TH_RING))
ring = rw.torus("stone_ring", RING_R, 0.0044, 36, 5, (0, 0, 0), mat="M_Brass")
pl.align(ring, AX, F.P(D_RING))
parts.add(ring)
for phi in RIBS:  # clasps where the ring crosses the ribs
    p = F.P(D_RING, phi, RING_R)
    parts.add(pl.obox("ring_clasp", (0.0095, 0.012, 0.0062), p + F.radial(phi) * 0.0012, AX, F.radial(phi), "M_Copper",
                      rounded=0.002, segments=1))
STONES = ((90.0, "algiz"), (210.0, "ingwaz"), (330.0, "sowilo"))
for (phi, key) in STONES:
    out = F.radial(phi)
    tan = F.radial(phi + 90.0)
    sc = F.P(D_RING + 0.002, phi, RING_R + 0.0165)
    stone = glove.oriented_pillow("runestone", (0.03, 0.021, 0.041), sc, tan, out, AX, 0.6, 0.6, 12, 8, STONE)
    parts.add(stone)
    # brass cradle: a backing plate on the ring and two side prongs gripping the stone
    parts.add(pl.obox("cradle", (0.022, 0.016, 0.0055), F.P(D_RING, phi, RING_R + 0.0045), tan, out, "M_Brass",
                      rounded=0.002, segments=1))
    for s in (-1, 1):
        q0 = F.P(D_RING, phi, RING_R + 0.004) + tan * (s * 0.0105)
        q1 = sc + tan * (s * 0.0138) + out * 0.002
        parts.add(pl.sausage("prong", [q0, (q0 + q1) / 2 + tan * (s * 0.0015), q1], [0.0032, 0.003, 0.0026], 6, 2,
                             "M_Brass", (True, True), 2, True, 60))
    parts.add(mh.glyph2(key, sc + out * 0.0104, tan, AX, 0.0145, 0.023, 0.0043, 0.0034, RUNE, "stone_rune"))

focus = rw.join(parts, "OrbFocus", origin=(0, 0, 0))

# --- the orb: a faceted crystal ball (separate object so the game can spin and pulse it) ------------------------------
N_RINGS = 9
prof = [(R_ORB * math.sin(math.pi * i / N_RINGS), -R_ORB * math.cos(math.pi * i / N_RINGS)) for i in range(N_RINGS + 1)]
orb = mh.gem_lathe("Orb", prof, AX, C, 14, CRYSTAL, True, 0.0, F.side)     # origin at the orb centre
rw.smooth(orb, 24)
pl.parent_keep(orb, focus)

# --- glove: the same hammer grip as vm_staff ------------------------------------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Emitter", tuple(C + V((0, -1, 0)) * (R_ORB + 0.004)))
pl.check("vm_orb", (0, 0, 0))
mh.report_nodes(["OrbFocus", "Orb", "Glove", "Emitter"])
mh.crystal_audit()
rw.finish("vm_orb", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_orb")
mh.qa("vm_orb")
