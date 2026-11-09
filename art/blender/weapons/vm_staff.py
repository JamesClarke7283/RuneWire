"""vm_staff: first-person spell focus, a short gnarled wand.

Nodes (origin = grip centre; the crystal points -Y):
  Staff    a knobbly dark-wood wand (M_WoodDark) held like a sword, angled forward and up: a brass pommel
           and ferrule, a spiral violet-leather grip wrap, glowing gold rune inlays on the bare wood above the
           hand, a brass ferrule with a claw-set rarity gem, then the wood splits into three twisting strands
           that braid up to a brass setting and curl into root claws gripping the violet crystal head
           (M_Crystal__a066ff) with its three side shards; two glowing gold rune halos float around the braid
           and a little twig with a leaf sprouts from the shaft.
           Only the head crystal and the side shards use M_Crystal__a066ff (the game swaps its tint per spell).
  Glove    the shared cartoon leather glove wrapped around the wand (glove.py), wrist toward +Y.
  Emitter  empty at the crystal tip.
"""
import math
import os
import sys

from mathutils import noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402
import detail_helpers as dh  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

CRYSTAL = "M_Crystal__a066ff"
pl.tint_emission(CRYSTAL, "a066ff", 1.6)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
RUNE = rw.glow("RuneGold", "ffc65a", 3.0)
LEAF = rw.flat("LeafGreen", "6cbf45", 0.7, 0.0)
WRAP = "M_Leather__4b2d5c"
parts = []


def add(x):
    if isinstance(x, (list, tuple)):
        parts.extend(x)
    else:
        parts.append(x)


# The wand axis runs from the pommel (behind/below the hand) through the grip to the head (in front/up).
TILT = 32.0                                       # degrees up from -Y
AX = V((0, -math.cos(math.radians(TILT)), math.sin(math.radians(TILT))))
L_BACK, L_FRONT = 0.085, 0.35                     # wand extent behind / in front of the grip centre
side = V((1, 0, 0))
upv = AX.cross(side).normalized()                 # perpendicular to the wand, pointing up and back
FACE = 60.0                                       # angle (0 = +X, 90 = up) that faces the player's eye


def radial(ang_deg):
    a = math.radians(ang_deg)
    return side * math.cos(a) + upv * math.sin(a)


def wob(d, amp=0.006):
    """Small organic wobble perpendicular to the wand."""
    w = noise.noise_vector(V((d * 21.0, 1.7, 0.3)))
    return side * (w.x * amp) + upv * (w.y * amp)


# --- lower shaft: knobbly wood from the pommel to where the braid starts --------------------------------------
D_RUNE0, D_FER, D_BRAID, D_HEAD = 0.078, 0.144, 0.15, 0.272
def shaft_r(d):
    return 0.0265 - 0.004 * max(0.0, (d - 0.07) / 0.09) + 0.002 * math.sin(d * 70.0)


pts, rad = [], []
N = 12
for i in range(N + 1):
    t = i / N
    d = -L_BACK + (D_BRAID + 0.012 + L_BACK) * t
    pts.append(AX * d)
    rad.append(shaft_r(d))
add(pl.sausage("shaft", pts, rad, 12, 3, "M_WoodDark", (True, True), 2, True, 50))
for (d, ang, s) in ((0.101, 300, 0.9), (0.127, 15, 0.75)):
    add(rw.sphere("knot", 0.0105 * s, 8, 5, tuple(AX * d + radial(ang) * (shaft_r(d) - 0.004)), mat="M_WoodDark"))

# --- pommel + lower ferrule ----------------------------------------------------------------------------------------
add(pl.lathe_axis("pommel", [(0.0, -0.03), (0.012, -0.029), (0.022, -0.024), (0.034, -0.012), (0.035, 0.004),
                             (0.027, 0.014), (0.0, 0.016)], AX, AX * (-L_BACK - 0.012), 18, "M_Brass", False, False,
                  50))
add(pl.lathe_axis("pommel_tip", [(0.0, 0.0), (0.012, 0.0), (0.009, 0.008), (0.004, 0.014), (0.0, 0.016)], -AX,
                  AX * (-L_BACK - 0.012 - 0.029), 12, "M_Brass", False, False, 50))
add(pl.band("ferrule_low", 0.035, 0.02, 0.014, AX, AX * -0.078, "M_Brass", 18, 0.0))
add(pl.rivet_ring(AX * -0.078, AX, 0.035, 4, 0.0045, 0.0035, "M_Copper", FACE, 6))

# --- spiral leather grip wrap (mostly inside the glove) + the brass collar above the hand ---------------------------
add(dh.wrap("wrap", AX * -0.066, AX * 0.064, 0.0262, 7, WRAP, 0.0042, 10.0, (1, 0, 0), 14))
add(pl.band("ferrule_mid", 0.0335, 0.016, 0.012, AX, AX * 0.072, "M_Brass", 18, 0.0))

# --- glowing gold rune inlays on the bare wood above the hand (facing the player), and on the far side ------------
for (d, key, ang) in ((0.094, "algiz", FACE), (0.122, "kenaz", FACE), (0.108, "sowilo", FACE + 180)):
    n = radial(ang)
    t = AX.cross(n).normalized()
    add(pl.glyph(key, AX * d + n * (shaft_r(d) + 0.0006), t, AX, 0.017, 0.0042, 0.0042, RUNE, "rune"))

# --- ferrule with the claw-set rarity gem ---------------------------------------------------------------------------
add(pl.band("ferrule_gem", 0.0315, 0.02, 0.012, AX, AX * D_FER, "M_Brass", 18, 0.25))
gn = radial(FACE)
gb = AX * D_FER + gn * 0.03
add(pl.lathe_axis("gem_cup", [(0.0, -0.004), (0.0115, -0.004), (0.0115, 0.002), (0.0095, 0.0055), (0.0078, 0.0058)],
                  gn, gb, 12, "M_Brass", False, False, 45))
add(pl.lathe_axis("gem", [(0.0, -0.002), (0.008, 0.0035), (0.008, 0.007), (0.005, 0.0115), (0.0, 0.0125)], gn, gb, 8,
                  RARITY, False, False, 15))
gu = AX
gv = gn.cross(gu).normalized()
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = gu * math.cos(a) + gv * math.sin(a)
    add(pl.capsule("gem_claw", gb + d * 0.0105 + gn * 0.003, gb + d * 0.0072 + gn * 0.0095, 0.002, 5, 1, "M_Brass"))

# --- three twisting wooden strands braided up to the head, curling into root claws around the crystal --------------
TURNS = 0.8
BR_RHO, STRAND_R = 0.0132, 0.0116
CR_R = 0.045                                       # crystal radius
CL = 0.15                                          # crystal length
claw_angles = []
for k in range(3):
    th0 = 90.0 + 120.0 * k
    spts, srad = [], []
    n = 9
    for i in range(n):
        t = i / n
        d = D_BRAID - 0.012 + (D_HEAD - D_BRAID + 0.012) * t
        th = th0 + 360.0 * TURNS * t
        spts.append(AX * d + radial(th) * BR_RHO + wob(d + k, 0.002))
        srad.append(STRAND_R * (1.0 - 0.06 * t))
    th_end = th0 + 360.0 * TURNS
    claw_angles.append(th_end)
    # root claw: flare gradually out of the setting, hug the crystal and curl the tip in onto it
    for (dd, rho, rr) in ((0.0, 0.016, 0.0112), (0.012, 0.026, 0.0108), (0.026, 0.04, 0.0102), (0.044, 0.0515, 0.0095),
                          (0.064, 0.0515, 0.0088), (0.08, 0.045, 0.0078), (0.09, 0.037, 0.0066)):
        spts.append(AX * (D_HEAD + dd) + radial(th_end + 10.0 * dd / 0.09) * rho)
        srad.append(rr)
    add(pl.sausage("strand", spts, srad, 8, 3, "M_WoodDark", (True, True), 2, True, 55))
# brass binding band low on the braid
add(pl.band("braid_band", 0.0285, 0.014, 0.0085, AX, AX * 0.172, "M_Brass", 18, 0.3))
# two floating rune halos around the braid (slightly tilted)
for (d, r, tilt) in ((0.203, 0.041, 9.0), (0.236, 0.035, -7.0)):
    halo = rw.torus("halo", r, 0.0064, 28, 6, (0, 0, 0), mat=RUNE)
    pl.align(halo, (pl.Matrix.Rotation(math.radians(tilt), 3, side) @ AX).normalized(), AX * d)
    add(halo)
# knots on the strands
for k, dd in ((0, 0.188), (1, 0.252)):
    t = (dd - (D_BRAID - 0.012)) / (D_HEAD - D_BRAID + 0.012)
    th = 90.0 + 120.0 * k + 360.0 * TURNS * t
    add(rw.sphere("knot", 0.0082, 8, 5, tuple(AX * dd + radial(th) * (BR_RHO + 0.0095)), mat="M_WoodDark"))

# --- brass setting, crystal head and side shards --------------------------------------------------------------------
HEAD = AX * D_HEAD
add(pl.lathe_axis("setting", [(0.022, -0.016), (0.03, -0.006), (0.038, 0.006), (0.036, 0.014), (0.026, 0.018),
                              (0.0, 0.019)], AX, HEAD, 18, "M_Brass", True, False, 45))
add(pl.rivet_ring(HEAD + AX * 0.004, AX, 0.0375, 6, 0.004, 0.003, "M_Copper", 30, 6))
C0 = HEAD + AX * 0.008
add(pl.crystal("head", C0, AX, CL, CR_R, 6, 0.34, 0.1, CRYSTAL, 0))
for k, ang in enumerate(claw_angles):
    a = ang + 60.0
    d = radial(a)
    ln = (0.058, 0.048, 0.052)[k]
    add(pl.crystal("shard", C0 + d * 0.024 + AX * 0.006, (AX * 0.7 + d * 0.71).normalized(), ln, 0.014, 5, 0.42,
                   0.12, CRYSTAL, 15))
TIP = C0 + AX * CL

# --- a twig with a leaf on the far (-X) side --------------------------------------------------------------------------
tw_n = radial(188)
tw0 = AX * 0.09 + tw_n * 0.019
tw1 = tw0 + (tw_n * 0.75 + AX * 0.66).normalized() * 0.042
add(pl.sausage("twig", [tw0, (tw0 + tw1) / 2 + tw_n * 0.004, tw1], [0.0072, 0.0058, 0.0045], 6, 3, "M_WoodDark",
               (True, True), 2, True, 60))
leaf = rw.sphere("leaf", 1.0, 10, 6, (0, 0, 0), scale=(0.0115, 0.0032, 0.021), mat=LEAF)
leaf.data.transform(pl.Matrix.Translation((0, 0, 0.019)))
pl.align(leaf, (tw1 - tw0).normalized() * 0.6 + AX * 0.55 + tw_n * 0.3, tw1, x_hint=side)
add(leaf)

staff = rw.join(parts, "Staff", origin=(0, 0, 0))
rw.smooth(staff, 50)

# --- glove: a hammer grip around the wand axis, fingers wrapping from below ----------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)

rw.empty("Emitter", tuple(TIP))
pl.check("vm_staff", (0, 0, 0))
rw.finish("vm_staff", "weapons", icon=False)
import wpn_icon  # noqa: E402
wpn_icon.render("vm_staff")
