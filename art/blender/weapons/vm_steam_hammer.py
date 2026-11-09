"""vm_steam_hammer: first-person "Piston Maul", an oversized cartoon steam sledgehammer (melee).

Held one-handed like vm_thunder_wrench: the haft runs from the grip forward (-Y) and up at TILT degrees along AX.
The head is a steam cylinder lying across the top of the haft, perpendicular to it. In the head's own frame (haft
= up) the striking face points -Y; rotated with the haft that is the world direction SD = (0, -sin T, -cos T),
i.e. forward and down.

Nodes (origin = grip centre):
  PistonMaul  a spiral leather-wrapped grip between brass ferrules, a brass ball pommel with a hex nut and a
              lanyard ring; a long round steel haft with riveted steel langets, brass bands and a brass steam bottle
              strapped to its back (copper feed line and valve up into the head, the caged rarity lamp on its +X
              side); the head: a chunky brass steam cylinder with brass flanges, studs, a yellow/black hazard band
              at the striking end, a steel gland plate and brass packing nut the piston rod slides through, a domed
              steel back cap, two copper exhaust stacks with flared brass tops, a pressure gauge on the +X side
              (player view) and a steam-chest plate with a hand-wheel valve on the -X side (icon view), clamped to
              the haft by a riveted steel socket band.
  Piston      the steel striking-face block (chamfered, a brass band, bolt heads) plus a short steel piston rod
              that runs back into the cylinder (child of PistonMaul). Origin on the head axis at the centre of the
              block at rest. The game slides it 0.07 m along SD and back; even fully out, 0.05 m of rod stays in
              the gland, and nothing of the body sits in front of the face.
  Glove       the shared cartoon leather glove gripping the handle (glove.py).
  Tip         empty at the centre of the striking face at rest (child of PistonMaul).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tech_weapon_helpers as th  # noqa: E402

nw, dh, glove, pl, rw, V = th.nw, th.dh, th.glove, th.pl, th.rw, th.V
X = th.X
rw.reset()

TILT = 35.0
AX = V((0, -math.cos(math.radians(TILT)), math.sin(math.radians(TILT))))     # haft axis, toward the head
SD = V((0, -math.sin(math.radians(TILT)), -math.cos(math.radians(TILT))))    # striking direction (head's -Y)
RARITY = th.std_mats()
BRASS, COPPER, STEEL, DARK = "M_Brass", "M_Copper", "M_Steel", "M_DarkMetal"
GRIP_LEATHER = "M_Leather__5a321c"
parts = th.Parts()
add = parts.add


def P(a, s=0.0, x=0.0):
    """Point in the maul frame: a along the haft, s along the striking direction, x to the player's side."""
    return AX * a + SD * s + X * x


# --- grip, ferrules, pommel -------------------------------------------------------------------------------------
G0, G1 = -0.08, 0.12
add(nw.spiral_wrap("grip_wrap", P(G0), AX, G1 - G0, 0.026, 0.0034, 6.0, GRIP_LEATHER, segs=14, steps_per_turn=7,
                   x_hint=X))
add(pl.band("ferrule_top", 0.032, 0.022, 0.012, AX, P(G1 + 0.008), BRASS, 18, 0.4))
add(pl.band("ferrule_bottom", 0.031, 0.014, 0.01, AX, P(G0 - 0.004), BRASS, 18, 0.4))
nut = rw.cylinder("pommel_nut", 0.029, 0.016, 6, (0, 0, 0), mat=BRASS)
rw.add_bevel(nut, 0.003, 1, 30).harden_normals = False
pl.align(nut, AX, P(G0 - 0.017), x_hint=X)
add(nut)
add(pl.lathe_axis("pommel", [(0.0, 0.0), (0.024, 0.0), (0.031, 0.009), (0.033, 0.018), (0.028, 0.029), (0.016, 0.036),
                             (0.0, 0.038)], -AX, P(G0 - 0.024), 16, BRASS, False, False, 50))
ring = rw.torus("lanyard_ring", 0.012, 0.0042, 14, 5, (0, 0, 0), mat=STEEL)
pl.align(ring, X, P(G0 - 0.075))
add(ring)
add(pl.rod("lanyard_post", P(G0 - 0.066), P(G0 - 0.058), 0.0055, 8, STEEL))

# --- haft: round steel shaft, riveted langets, brass bands, steam bottle ---------------------------------------
A_HEAD = 0.55                     # head centre along the haft
HR = 0.058                        # head cylinder radius
HAFT_R = 0.0185
add(pl.rod("haft", P(G1 + 0.004), P(A_HEAD - HR + 0.01), HAFT_R, 14, STEEL))
for a in (0.215, 0.33):
    add(pl.band("haft_band", HAFT_R + 0.0055, 0.014, 0.008, AX, P(a), BRASS, 14, 0.4))
LA0, LA1 = 0.36, A_HEAD - HR
for sx in (-1, 1):
    add(pl.obox("langet", (LA1 - LA0 + 0.012, 0.022, 0.006), P((LA0 + LA1) / 2, 0.0, sx * (HAFT_R + 0.001)), AX,
                X * sx, STEEL, rounded=0.0025, segments=1))
    for a in (LA0 + 0.014, (LA0 + LA1) / 2, LA1 - 0.012):
        add(nw.stud(P(a, 0.0, sx * (HAFT_R + 0.004)), X * sx, 0.0046, 0.0034, BRASS, 6))
# brass steam bottle strapped to the back (-SD side) of the haft, with the rarity lamp on its +X side
SB0, SB1 = 0.175, 0.33
SBO = -(HAFT_R + 0.021)            # bottle axis offset along SD
SBR = 0.021
add(pl.lathe_axis("steam_bottle", [(0.0, 0.0), (0.012, 0.003), (0.019, 0.012), (SBR, 0.024), (SBR, SB1 - SB0 - 0.024),
                                   (0.019, SB1 - SB0 - 0.012), (0.012, SB1 - SB0 - 0.003), (0.0, SB1 - SB0)], AX,
                  P(SB0, SBO), 16, BRASS, False, False, 40))
for a in (SB0 + 0.04, SB1 - 0.04):
    add(pl.obox("bottle_clamp", (0.012, 0.022, (abs(SBO) + SBR) + 0.004), P(a, SBO / 2 - 0.004), AX, -SD, STEEL,
                rounded=0.003, segments=1))
    add(pl.band("bottle_strap", SBR + 0.003, 0.01, 0.005, AX, P(a, SBO), STEEL, 14, 0.0))
add(th.ring_studs(P(SB0 + 0.07, SBO), AX, SBR, 4, 0.0038, 0.0028, COPPER, 45.0, 405.0, up=X))
lamp_n = (X * 0.85 - SD * 0.5).normalized()
add(dh.lamp("rarity", P(SB0 + 0.105, SBO) + lamp_n * (SBR - 0.002), lamp_n, 0.0092, RARITY, up=AX, bezel=BRASS, cage=2,
            cage_mat=STEEL, segs=12))
# copper feed line from the bottle's top valve up into the head's socket
add(pl.rod("bottle_neck", P(SB1 - 0.004, SBO), P(SB1 + 0.012, SBO), 0.0068, 10, BRASS))
add(dh.valve("bottle_valve", P(SB1 + 0.008, SBO, 0.006), X, 0.0105, 0.0034, 3, COPPER, BRASS, 0.008, STEEL, up=AX))
feed = [P(SB1 + 0.012, SBO), P(SB1 + 0.05, SBO - 0.003), P(A_HEAD - HR - 0.05, -(HAFT_R + 0.014)),
        P(A_HEAD - HR + 0.008, -0.03)]
add(pl.sausage("feed_line", feed, 0.0058, 8, 3, COPPER, (True, True), 2, True, 60))

# --- head: brass steam cylinder across the top of the haft ---------------------------------------------------------
HC = P(A_HEAD)
HS0, HS1 = -0.1, 0.1               # cylinder back / front along SD
add(pl.rod("cylinder", HC + SD * HS0, HC + SD * HS1, HR, 28, BRASS))
for s in (HS0 + 0.006, HS1 - 0.006):
    add(pl.band("head_flange", HR + 0.008, 0.016, 0.012, SD, HC + SD * s, BRASS, 28, 0.4))
add(th.ring_studs(HC + SD * (HS0 + 0.026), SD, HR, 10, 0.0048, 0.0035, STEEL, 18.0, 378.0, up=AX))
add(th.hazard_ring("head_hazard", HR + 0.0015, 0.026, SD, HC + SD * (HS1 - 0.03), stripes=10, slant=30, half_w=8.0,
                   segs=28))
# socket band clamping the head onto the haft
add(pl.band("socket_band", HR + 0.0055, 0.034, 0.008, SD, HC + SD * 0.012, STEEL, 28, 0.3))
add(pl.rod("socket", P(A_HEAD - HR - 0.032), P(A_HEAD - HR + 0.012), HAFT_R + 0.0075, 14, STEEL))
add(pl.band("socket_ring", HAFT_R + 0.0115, 0.01, 0.006, AX, P(A_HEAD - HR - 0.03), BRASS, 14, 0.0))
for sx in (-1, 1):
    for da in (-0.026, 0.026):
        add(nw.stud(HC + SD * (0.012 + da * 0.45) + X * (sx * (HR + 0.0055)), X * sx, 0.0048, 0.0036, BRASS, 6))
# domed back cap with a centre bolt
cap = [(HR - 0.002, -0.003), (HR - 0.002, 0.0), (0.052, 0.012), (0.04, 0.022), (0.022, 0.028), (0.0, 0.03)]
add(pl.lathe_axis("back_cap", cap, -SD, HC + SD * HS0, 24, STEEL, False, False, 40))
add(pl.bolt(HC + SD * (HS0 - 0.029), -SD, 0.011, 0.008, BRASS, "cap_bolt", washer=False))
# two copper exhaust stacks rising from the top of the cylinder, near the back
for k, s in enumerate((-0.062, -0.024)):
    base = HC + SD * s + AX * (HR - 0.006)
    top = base + AX * 0.042 - SD * 0.008
    add(pl.sausage("stack", [base, base + AX * 0.022, top], 0.0098, 10, 2, COPPER, (False, False), 1, True, 50))
    add(pl.lathe_axis("stack_bell", [(0.0085, 0.0), (0.012, 0.004), (0.0152, 0.013), (0.016, 0.018), (0.0136, 0.019),
                                     (0.0095, 0.011)], (top - base).normalized(), top, 12, BRASS, False, False, 45))
    add(pl.band("stack_band", 0.0118, 0.008, 0.004, AX, base + AX * 0.012, BRASS, 12, 0.0))
# pressure gauge on the +X side (player view), on a boss
GB = HC + SD * (-0.04)
add(rw.cylinder("gauge_boss", 0.024, 0.016, 16, tuple(GB + X * (HR - 0.004)), (0, 90, 0), mat=BRASS))
gn = (X - SD * 0.25).normalized()
add(nw.gauge(GB + X * (HR + 0.004), gn, AX, 0.025, BRASS,
             zones=(("DialTeal", -120, -20), ("DialYellow", -20, 55), ("DialRed", 55, 120)), needle_deg=70.0, ticks=7,
             depth=0.012, segs=16, glass=True, name="pressure_gauge"))
# steam chest on the -X side (icon view): a riveted plate with a hand-wheel valve and a maker's badge
CHC = HC + SD * (-0.037)
add(pl.obox("steam_chest", (0.058, 0.05, 0.014), CHC - X * (HR - 0.004), SD, -X, COPPER, rounded=0.005, segments=2))
for ds in (-0.022, 0.022):
    for da in (-0.018, 0.018):
        add(nw.stud(CHC - X * (HR + 0.0035) + SD * ds + AX * da, -X, 0.0042, 0.003, BRASS, 6))
add(dh.valve("chest_valve", CHC - X * (HR + 0.003) + SD * 0.008, -X, 0.0135, 0.0038, 3, BRASS, COPPER, 0.012, STEEL,
             up=AX))
# front: steel gland plate + brass packing nut the piston rod slides through
add(pl.disc("gland_plate", 0.05, 0.008, SD, HC + SD * (HS1 + 0.004), STEEL, 24, 0.35))
for k in range(6):
    a = math.radians(30 + 60 * k)
    d = AX * math.cos(a) + X * math.sin(a)
    add(pl.bolt(HC + SD * (HS1 + 0.008) + d * 0.04, SD, 0.0048, 0.0036, STEEL, "gland_bolt", washer=False))
nutp = rw.cylinder("packing_nut", 0.026, 0.012, 6, (0, 0, 0), mat=BRASS)
rw.add_bevel(nutp, 0.0025, 1, 30).harden_normals = False
pl.align(nutp, SD, HC + SD * (HS1 + 0.014), x_hint=X)
add(nutp)

maul = rw.join(parts, "PistonMaul", origin=(0, 0, 0))
rw.smooth(maul, 45)

# --- the Piston: striking-face block + rod, slides along SD --------------------------------------------------------
S_BLOCK = HS1 + 0.024              # back face of the block at rest (just clear of the packing nut)
BL = 0.058                         # block length along SD
pp = th.Parts()
pp.add(pl.rod("piston_rod", HC + SD * (HS1 - 0.11), HC + SD * (S_BLOCK + 0.004), 0.0158, 14, STEEL))
face = [(0.0, 0.0), (0.05, 0.0), (0.063, 0.007), (0.068, 0.017), (0.068, 0.041), (0.064, 0.05), (0.052, 0.056),
        (0.03, 0.0575), (0.0, BL)]
pp.add(pl.lathe_axis("face_block", face, SD, HC + SD * S_BLOCK, 28, STEEL, False, False, 40))
pp.add(pl.band("face_band", 0.0705, 0.012, 0.006, SD, HC + SD * (S_BLOCK + 0.029), BRASS, 28, 0.3))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = AX * math.cos(a) + X * math.sin(a)
    pp.add(pl.bolt(HC + SD * S_BLOCK + d * 0.036, -SD, 0.0062, 0.0048, STEEL, "block_bolt", washer=False))
PISTON_C = HC + SD * (S_BLOCK + BL / 2)
piston = rw.join(pp, "Piston", origin=tuple(PISTON_C))
rw.smooth(piston, 45)
pl.parent_keep(piston, maul)

# --- glove + empties ---------------------------------------------------------------------------------------------
g = glove.fist(A=AX, out=(-1, 0, 0.35), F=(0.1, 1, -0.3), wrist_len=0.05)
TIP = HC + SD * (S_BLOCK + BL)
pl.empty_at("Tip", tuple(TIP), maul)
print("RWREPORT   CHECK striking direction SD = (%.4f, %.4f, %.4f); Piston origin %s; Tip %s; rod in gland at +0.07: "
      "%.3f m" % (SD.x, SD.y, SD.z, tuple(round(v, 4) for v in PISTON_C), tuple(round(v, 4) for v in TIP),
                  (HS1 + 0.02) - (HS1 - 0.11 + 0.07)))
pl.check("vm_steam_hammer", (0, 0, 0))
rw.finish("vm_steam_hammer", "weapons", icon=False)

import wpn_icon  # noqa: E402
wpn_icon.render("vm_steam_hammer")
