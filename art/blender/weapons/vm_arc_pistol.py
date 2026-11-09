"""vm_arc_pistol: first-person retro-futuristic arc pistol.

Nodes (origin = grip centre; the muzzle points -Y):
  ArcPistol  a sculpted brass body: a riveted copper rear dome with a knurled charge knob and a claw-set
             rarity gem, a glass tube on top holding a glowing cyan core between copper electrodes (brass
             caps with rivets and a rear terminal post, cage bars, saddle clips), a filigree side panel with a pressure gauge and a row of
             glowing charge pips (left/+X, toward the player), an exposed gear train and a maker's plate
             (right/-X), a bolted collar, a copper-coiled steel barrel ending in a finned ray-gun emitter
             dish with a spark ball and a prong ring, a capacitor cell slung under the barrel, wiring,
             a brass trigger guard and a dark-wood grip with a brass pommel and lanyard ring.
  Glove      the shared cartoon leather glove gripping the handle (glove.py), wrist toward +Y.
  Muzzle     empty at the emitter tip.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402
import detail_helpers as dh  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

RAKE = 15.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
CYAN = rw.glow("ArcCore", "5ff3ff", 4.0)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
dh.flat_mats()
parts = []


def add(x):
    if isinstance(x, (list, tuple)):
        parts.extend(x)
    else:
        parts.append(x)


X_POS, X_NEG, Y_POS, Y_NEG, Z_POS = V((1, 0, 0)), V((-1, 0, 0)), V((0, 1, 0)), V((0, -1, 0)), V((0, 0, 1))

# --- grip --------------------------------------------------------------------------------------------------
add(glove.oriented_pillow("grip", (0.046, 0.062, 0.2), fr * (-0.004), o, fr, A, 0.6, 0.35, 16, 10, "M_WoodDark"))
add(glove.oriented_pillow("pommel", (0.056, 0.072, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16, 8,
                          "M_Brass"))
add(dh.sling_ring("lanyard", A * -0.113 - fr * 0.004, -A, 0.011, 0.0035, "M_Steel", up=(0, -1, 0)))

# --- body: a sculpted side profile with a raised rear hump ------------------------------------------------------
BZ = 0.128                      # barrel / body axis height
HW = 0.033                      # body half width
body_prof = [(-0.166, 0.096), (-0.12, 0.09), (-0.04, 0.088), (0.03, 0.088), (0.058, 0.094), (0.068, 0.11),
             (0.07, 0.135), (0.066, 0.158), (0.052, 0.172), (0.02, 0.178), (-0.03, 0.173), (-0.09, 0.167),
             (-0.14, 0.165), (-0.162, 0.159), (-0.168, 0.14), (-0.168, 0.11)]
add(dh.slab("body", body_prof, -HW, HW, "M_Brass", 0.012, 3))
# steel belt along the lower edge of both sides
for sx in (-1, 1):
    add(pl.obox("belt", (0.006, 0.19, 0.012), (sx * (HW + 0.001), -0.05, 0.1), X_POS, Z_POS, "M_Steel",
                rounded=0.0025, segments=1))
    add(dh.rivet_line((sx * (HW + 0.004), -0.125, 0.1), (sx * (HW + 0.004), 0.025, 0.1), 4, (sx, 0, 0), 0.0045,
                      0.003, "M_Brass", 6))

# --- front collar where the barrel leaves the body ---------------------------------------------------------------
add(pl.disc("collar", 0.037, 0.014, Y_NEG, (0, -0.168, BZ), "M_Steel", 24, 0.35))
add(pl.rivet_face_ring((0, -0.175, BZ), Y_NEG, 0.028, 6, 0.0055, 0.0045, "M_Brass", 30, 6))

# --- rear dome with the charge knob and the rarity gem ------------------------------------------------------------
RD_Y = 0.05
dome_prof = [(0.036, -0.012), (0.041, 0.0), (0.041, 0.012), (0.037, 0.03), (0.029, 0.042), (0.016, 0.05),
             (0.0, 0.052)]
add(pl.lathe_axis("rear_dome", dome_prof, Y_POS, (0, RD_Y, BZ), 24, "M_Copper", False, False, 40))
add(pl.band("rear_flange", 0.045, 0.012, 0.01, Y_POS, (0, RD_Y + 0.004, BZ), "M_Brass", 24, 0.0))


def dome_r(h):
    for (r0, h0), (r1, h1) in zip(dome_prof[:-1], dome_prof[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    return 0.0


def dome_pt(h, ang_deg):
    """Point on the rear dome at depth h and angle (0 = +X, 90 = +Z) with its outward normal."""
    a = math.radians(ang_deg)
    radial = V((math.cos(a), 0, math.sin(a)))
    r = dome_r(h)
    dr = (dome_r(h + 0.002) - dome_r(h - 0.002)) / 0.004
    nrm = (radial - Y_POS * dr).normalized()
    return V((0, RD_Y + h, BZ)) + radial * r, nrm


for k in range(8):
    if k == 2:
        continue                                    # the gem sits on top
    p, nrm = dome_pt(0.034, 45 * k)
    add(pl.rivet(p, nrm, 0.0055, 0.004, "M_Brass", 6))
add(dh.knob("charge_knob", (0, RD_Y + 0.05, BZ), Y_POS, 0.015, 0.011, 10, "M_Brass", "M_Copper"))
# pointer line on the knob cap
add(pl.obox("knob_pointer", (0.0045, 0.012, 0.004), (0, RD_Y + 0.0665, BZ + 0.0075), X_POS, Y_POS, "DialInk",
            rounded=0.0012, segments=1))
# rarity gem: claw-set on the upper-rear of the dome, facing up and back toward the player
gp, gn = dome_pt(0.03, 90)
gem_base = gp + gn * 0.002
add(pl.lathe_axis("gem_cup", [(0.0125, -0.004), (0.0125, 0.002), (0.0105, 0.006), (0.0085, 0.0062)], gn, gem_base,
                  12, "M_Brass", False, False, 45))
add(pl.lathe_axis("gem", [(0.0, -0.002), (0.0088, 0.004), (0.0088, 0.0075), (0.0055, 0.0125), (0.0, 0.0135)], gn,
                  gem_base, 8, RARITY, False, False, 15))
gu, gv, _ = dh.basis(gn, (1, 0, 0))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = gu * math.cos(a) + gv * math.sin(a)
    add(pl.capsule("gem_claw", gem_base + d * 0.0115 + gn * 0.004, gem_base + d * 0.008 + gn * 0.011, 0.0022, 5, 1,
                   "M_Brass"))

# --- left (+X) side: filigree panel, pressure gauge, charge pips -------------------------------------------------
PX = HW
add(dh.plate("lpanel", (PX - 0.002, -0.055, 0.131), X_POS, 0.17, 0.046, 0.005, mat="M_Copper", rivets="M_Brass",
             rr=0.0042))
add(dh.gauge("gauge", (PX + 0.003, -0.02, 0.131), X_POS, 0.02, needle_deg=-40.0, depth=0.011))
add(dh.pips("charge", (PX + 0.003, -0.098, 0.138), X_POS, 4, 3, CYAN, size=0.0075, gap=0.0035))
# filigree scrolls framing the gauge and under the pips
add(dh.scroll("filigree", (PX + 0.003, -0.098, 0.119), X_POS, 0.05, width=0.0055, height=0.0026, mat="M_Brass"))
add(dh.scroll("filigree", (PX + 0.003, 0.0145, 0.131), X_POS, 0.033, width=0.0055, height=0.0026, mat="M_Brass",
              angle=90.0))

# --- right (-X) side: exposed gear train on a dark plate + maker's plate ----------------------------------------
NX = -HW
add(dh.plate("gearplate", (NX + 0.002, -0.05, 0.131), X_NEG, 0.1, 0.046, 0.004, mat="M_DarkMetal",
             rivets="M_Brass", rr=0.004))
gA_c = V((NX - 0.006, -0.03, 0.134))
rA, nA, dA = 0.019, 11, 0.0045
rB, nB, dB = 0.0135, 8, 0.0045
rC, nC, dC = 0.0105, 6, 0.0045
thB = -18.0
spinA, spinBf = dh.mesh_spin(rA, nA, thB)
gu_, gv_, gn_ = dh.basis(X_NEG, Z_POS)
gB_c = gA_c + (gu_ * math.cos(math.radians(thB)) + gv_ * math.sin(math.radians(thB))) * (rA + rB - dA * 0.9)
spinB = spinBf(nB)
thC = 28.0
spinB2, spinCf = dh.mesh_spin(rB, nB, thC)
gC_c = gB_c + (gu_ * math.cos(math.radians(thC)) + gv_ * math.sin(math.radians(thC))) * (rB + rC - dB * 0.9)
add(dh.gear("gearA", gA_c, X_NEG, rA, nA, dA, 0.006, "M_Brass", holes=4, spin=spinA))
add(dh.gear("gearB", gB_c, X_NEG, rB, nB, dB, 0.006, "M_Copper", spin=spinB))
add(dh.gear("gearC", gC_c, X_NEG, rC, nC, dC, 0.006, "M_Brass", spin=spinCf(nC) - (spinB - spinB2) * nB / nC))
# maker's plate with a lightning-bolt emblem behind the gears
add(dh.plate("maker", (NX - 0.001, 0.022, 0.135), X_NEG, 0.034, 0.03, 0.004, mat="M_Brass", rivets="M_Copper",
             rr=0.0035))
add(dh.bolt_emblem("maker_bolt", (NX - 0.005, 0.022, 0.135), X_NEG, 0.022, mat="M_Copper"))

# --- barrel: steel tube, copper coil, brass bands ---------------------------------------------------------------
BY0, BY1 = -0.17, -0.275
add(pl.rod("barrel", (0, BY0, BZ), (0, BY1, BZ), 0.02, 16, "M_Steel"))
add(pl.helix("coil", 0.029, 0.0085, 4.5, 0.078, (0, BY0 - 0.012, BZ), Y_NEG, 12, 6, "M_Copper", res=1))
for y in (BY0 - 0.007, BY1 + 0.008):
    add(pl.band("barrel_band", 0.037, 0.014, 0.016, Y_POS, (0, y, BZ), "M_Brass", 20, 0.0))

# --- emitter dish with fins, spark ball and the prong ring ------------------------------------------------------
flare = [(0.024, 0.0), (0.026, 0.012), (0.034, 0.03), (0.05, 0.05), (0.054, 0.056), (0.05, 0.06),
         (0.036, 0.046), (0.02, 0.038), (0.0, 0.036)]
FL_Y = BY1 + 0.004
add(pl.lathe_axis("emitter", flare, Y_NEG, (0, FL_Y, BZ), 24, "M_Brass", False, False, 45))
add(rw.sphere("tip_glow", 0.017, 12, 6, (0, FL_Y - 0.038, BZ), mat=CYAN))
# three copper electrodes in the dish pointing at the spark ball
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = V((math.cos(a), 0, math.sin(a)))
    add(pl.capsule("electrode", V((0, FL_Y - 0.04, BZ)) + d * 0.036, V((0, FL_Y - 0.046, BZ)) + d * 0.024, 0.0045, 6,
                   1, "M_Copper"))
# swept ray-gun fins on the back of the dish
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = V((math.cos(a), 0, math.sin(a)))
    fn = Y_NEG.cross(d).normalized()
    fin = [(-0.004, 0.018), (0.044, 0.036), (0.046, 0.048), (0.018, 0.058), (-0.016, 0.062), (-0.02, 0.05)]
    add(dh.prism("fin", fin, V((0, FL_Y + 0.004, BZ)), Y_NEG, d, fn, 0.006, "M_Brass", -0.003, 0.0018))
TIP_Y = FL_Y - 0.06
ring_y = TIP_Y - 0.01
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = V((math.cos(a), 0, math.sin(a)))
    add(pl.capsule("prong", V((0, FL_Y - 0.054, BZ)) + d * 0.043, V((0, ring_y, BZ)) + d * 0.03, 0.006, 6, 2,
                   "M_Brass"))
add(rw.torus("ring", 0.03, 0.007, 20, 6, (0, ring_y, BZ), (90, 0, 0), mat="M_Brass"))

# --- capacitor cell slung under the barrel ----------------------------------------------------------------------
CZ = BZ - 0.052
add(dh.cell("cell", (0, BY0 - 0.004, CZ), (0, BY1 + 0.006, CZ), 0.012, CYAN, bands=0))
for y in (BY0 - 0.007, BY1 + 0.008):
    add(pl.obox("cell_strap", (0.012, 0.01, 0.028), (0, y, CZ + 0.016), X_POS, Z_POS, "M_Brass", rounded=0.003,
                segments=1))

# --- glass tube with the glowing cyan core on top -----------------------------------------------------------------
TZ = 0.2
ty0, ty1 = -0.135, 0.02
add(pl.rod("tube", (0, ty0, TZ), (0, ty1, TZ), 0.025, 16, "M_Glass"))
add(pl.capsule("core", (0, ty0 + 0.034, TZ), (0, ty1 - 0.034, TZ), 0.0105, 10, 2, CYAN))
for y, d in ((ty0, -1), (ty1, 1)):
    add(pl.lathe_axis("tube_cap", [(0.03, -0.012), (0.03, 0.01), (0.024, 0.018), (0.012, 0.022), (0.0, 0.023)],
                      (0, d, 0), (0, y, TZ), 16, "M_Brass", True, False, 45))
    # copper electrode cone inside the glass, pointing at the core
    add(pl.lathe_axis("tube_electrode", [(0.01, 0.0), (0.007, 0.006), (0.003, 0.011), (0.0, 0.012)], (0, -d, 0),
                      (0, y - d * 0.008, TZ), 10, "M_Copper", True, False, 40))
    add(pl.rivet_ring((0, y - d * 0.001, TZ), Y_POS, 0.03, 4, 0.0045, 0.0035, "M_Copper", 45, 6))
    add(rw.rounded_box("tube_clip", (0.028, 0.02, 0.032), 0.008, (0, y, TZ - 0.03), mat="M_Brass", segments=1))
# copper terminal post with a knurled brass nut on the rear cap (faces the player)
add(pl.rod("terminal", (0, ty1 + 0.019, TZ), (0, ty1 + 0.03, TZ), 0.0055, 10, "M_Copper"))
add(dh.knob("terminal_nut", (0, ty1 + 0.027, TZ), Y_POS, 0.0098, 0.0065, 8, "M_Brass", "M_Copper"))
# protective cage bars over the glass
for s in (-1, 1):
    a = math.radians(90 + s * 52)
    d = V((math.cos(a), 0, math.sin(a)))
    add(pl.rod("cage_bar", V((0, ty0 + 0.006, TZ)) + d * 0.029, V((0, ty1 - 0.006, TZ)) + d * 0.029, 0.0042, 8,
               "M_Brass"))

# --- wiring: tube front cap down around the left of the collar to the capacitor cell ----------------------------
wpath = [V((0.016, ty0 - 0.014, TZ - 0.014)), V((0.032, -0.163, 0.172)), V((0.043, -0.171, 0.14)),
         V((0.038, -0.175, 0.104)), V((0.014, -0.176, 0.08))]
add(dh.wires("wire", wpath, 2, 0.0046, 0.0008, ("M_Copper", "M_Steel"), up=(1, 0, 0)))

# --- trigger guard + trigger ---------------------------------------------------------------------------------------
guard = [(0, -0.13, BZ - 0.035), (0, -0.135, 0.04), (0, -0.118, 0.008), (0, -0.088, 0.0), (0, -0.064, 0.012)]
add(pl.sausage("guard", guard, 0.0085, 8, 3, "M_Brass", (True, True), 2, True, 60))
add(pl.capsule("guard_spur", (0, -0.128, 0.022), (0, -0.142, 0.012), 0.0065, 6, 2, "M_Brass"))
add(pl.capsule("trigger", (0, -0.088, BZ - 0.04), (0, -0.098, 0.05), 0.007, 8, 2, "M_Steel"))

pistol = rw.join(parts, "ArcPistol", origin=(0, 0, 0))
rw.smooth(pistol, 45)

# --- glove ----------------------------------------------------------------------------------------------------------
g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, TIP_Y - 0.008, BZ))
pl.check("vm_arc_pistol", (0, 0, 0))
rw.finish("vm_arc_pistol", "weapons", icon=False)
import wpn_icon  # noqa: E402
wpn_icon.render("vm_arc_pistol")
