"""vm_boom_mortar: first-person hand mortar.

Nodes (origin = grip centre; the muzzle points -Y):
  BoomMortar  a short fat dark-iron barrel (diameter ~0.16): a chunky brass muzzle crown ringed with bolt
              heads around a dark bore, riveted brass bands, a yellow/black hazard-stripe band, rivet rows,
              a front blade sight and a rear notch sight; a rounded breech capped by a riveted brass breech
              plate carrying a big "boom-o-meter" pressure gauge (facing the player) and a locking lever; a
              lit fuse on top (brass fuse well, curling cord, glowing spark star) beside a caged rarity lamp;
              a brass elevation quadrant with tick marks and a pointer on the left (+X) side; two spare
              red-nosed shells strapped in a cradle, a breech hinge and a maker's plate with a bomb emblem on
              the right (-X) side; a spring recoil damper under the
              barrel; a brass bracket, trigger guard and trigger, and a wooden pistol grip with a brass pommel.
  Glove       the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle      empty at the centre of the muzzle mouth.
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

RAKE = 12.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
dh.flat_mats()
SPARK = rw.glow("FuseSpark", "ffd36b", 5.0)
RARITY = rw.glow("RarityGlow", "ffffff", 3.0)
rw.flat("FuseCord", "d9b06a", 0.8, 0.0)
SHELL_NOSE = "M_PaintedMetal__d8392b"
X_POS, X_NEG, Y_POS, Y_NEG, Z_POS, Z_NEG = (V((1, 0, 0)), V((-1, 0, 0)), V((0, 1, 0)), V((0, -1, 0)), V((0, 0, 1)),
                                            V((0, 0, -1)))
parts = []


def add(x):
    if isinstance(x, (list, tuple)):
        parts.extend(x)
    else:
        parts.append(x)


# --- grip ------------------------------------------------------------------------------------------------
add(glove.oriented_pillow("grip", (0.05, 0.066, 0.19), -fr * 0.004 - A * 0.005, o, fr, A, 0.6, 0.35, 16, 10,
                          "M_WoodDark"))
add(glove.oriented_pillow("pommel", (0.06, 0.076, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16, 8, "M_Brass"))

# --- barrel ------------------------------------------------------------------------------------------------
BZ = 0.155                      # barrel axis height
BR = 0.08                       # barrel radius (diameter 0.16)
Y_MOUTH = -0.33
Y_BREECH = 0.06
L = Y_BREECH - Y_MOUTH
BORE = 0.058
# dark-iron body: bore floor (h = 0.07 behind the mouth), out along the barrel to the rounded breech (h = L)
body = [(0.0, 0.07), (BORE - 0.001, 0.07), (BORE - 0.001, 0.03), (BR - 0.004, 0.03), (BR, 0.045), (BR, L - 0.07),
        (BR - 0.006, L - 0.04), (BR - 0.025, L - 0.015), (0.03, L), (0.0, L)]
add(pl.lathe_axis("barrel", body, Y_POS, (0, Y_MOUTH, BZ), 28, "M_DarkMetal", False, False, 40))


def barrel_r(y):
    """Outer radius of the iron barrel at world y."""
    h = y - Y_MOUTH
    for (r0, h0), (r1, h1) in zip(body[3:-1], body[4:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    return BR


def surf(y, ang_deg, lift=0.0):
    """Point on the barrel surface at world y and angle around the axis (0 = +X, 90 = +Z), outward normal."""
    a = math.radians(ang_deg)
    radial = V((math.cos(a), 0, math.sin(a)))
    dr = (barrel_r(y + 0.002) - barrel_r(y - 0.002)) / 0.004
    nrm = (radial - Y_POS * dr).normalized()
    return V((0, y, BZ)) + radial * (barrel_r(y) + lift), nrm


# chunky brass muzzle crown with bolt heads around it
crown = [(BORE, 0.042), (BORE, 0.004), (BORE + 0.004, 0.0), (BR + 0.011, 0.0), (BR + 0.015, 0.006),
         (BR + 0.015, 0.03), (BR + 0.007, 0.04), (BR - 0.002, 0.046)]
add(pl.lathe_axis("crown", crown, Y_POS, (0, Y_MOUTH, BZ), 28, "M_Brass", False, False, 40))
add(pl.rivet_ring((0, Y_MOUTH + 0.018, BZ), Y_POS, BR + 0.015, 8, 0.0075, 0.005, "M_Steel", 22.5, 8))
# riveted brass bands
for y in (Y_MOUTH + 0.068, -0.045):
    add(pl.band("band", BR + 0.01, 0.03, 0.016, Y_POS, (0, y, BZ), "M_Brass", 28, 0.0))
    add(pl.rivet_ring((0, y, BZ), Y_POS, BR + 0.01, 8, 0.0065, 0.0045, "M_Copper", 0, 6))
# hazard stripe band
HZ_Y = -0.16
add(dh.hazard_band("hazard", (0, HZ_Y, BZ), Y_POS, BR + 0.006, 0.062, 8, 30.0, 11.0, 0.012, 3, 3, 32))
# rivet rows on the iron between the bands
for y in (-0.212, -0.108):
    for k in range(8):
        if y > -0.15 and k in (0, 4):
            continue                            # leave room for the quadrant (+X) and the shell cradle (-X)
        p, nrm = surf(y, 45 * k)
        add(pl.rivet(p, nrm, 0.007, 0.0045, "M_Brass", 6))
# front blade sight on the front band, rear notch sight on the rear band
fs = V((0, Y_MOUTH + 0.068, BZ + BR + 0.01))
add(rw.rounded_box("fsight", (0.008, 0.02, 0.026), 0.0035, tuple(fs + V((0, 0, 0.01))), mat="M_Brass", segments=1))
add(rw.sphere("fsight_bead", 0.0065, 8, 4, tuple(fs + V((0, 0, 0.025))), mat="M_Brass"))
rsy = -0.045
for sx in (-1, 1):
    add(rw.rounded_box("rsight", (0.008, 0.014, 0.024), 0.003, (sx * 0.011, rsy, BZ + BR + 0.02), mat="M_Brass",
                       segments=1))
add(rw.rounded_box("rsight_base", (0.034, 0.016, 0.01), 0.003, (0, rsy, BZ + BR + 0.01), mat="M_Brass", segments=1))

# --- breech plate: riveted brass, a big pressure gauge facing the player, a locking lever ---------------------------
BP_Y = Y_BREECH - 0.016
add(pl.disc("breech_plate", 0.056, 0.02, Y_POS, (0, BP_Y, BZ), "M_Brass", 28, 0.4))
add(pl.rivet_face_ring((0, BP_Y + 0.01, BZ), Y_POS, 0.046, 10, 0.0055, 0.004, "M_Steel", 0, 6))
add(dh.gauge("boom_gauge", (0, BP_Y + 0.0095, BZ + 0.002), Y_POS, 0.03, up=(0, 0, 1), needle_deg=50.0,
             red=(55.0, 125.0), ticks=7, depth=0.012, segs=24))
la = math.radians(-35)
lever_n = V((math.cos(la), 0, math.sin(la)))
lever_p = V((0, BP_Y, BZ)) + lever_n * 0.056
add(pl.disc("lever_boss", 0.0105, 0.012, lever_n, lever_p, "M_Steel", 12, 0.4))
lv = [lever_p + lever_n * 0.004, lever_p + lever_n * 0.016 + V((0, 0.012, 0)),
      lever_p + lever_n * 0.026 + V((0, 0.024, -0.004))]
add(pl.sausage("lever", lv, [0.0065, 0.006, 0.0055], 8, 3, "M_Brass", (True, True), 2, True, 60))
add(rw.sphere("lever_knob", 0.0105, 12, 6, tuple(lv[-1] + V((0, 0.006, -0.002))), mat="M_Copper"))

# --- fuse on top of the breech + the caged rarity lamp beside it ------------------------------------------------------
fp, fn = surf(0.004, 90)
add(pl.lathe_axis("fuse_well", [(0.0, -0.01), (0.022, -0.01), (0.022, 0.012), (0.018, 0.018), (0.012, 0.019),
                                (0.012, 0.012), (0.0, 0.012)], fn, fp, 14, "M_Brass", False, False, 45))
add(pl.rivet_ring(fp + fn * 0.0, fn, 0.022, 4, 0.0042, 0.003, "M_Copper", 45, 6))
f0 = fp + fn * 0.012
fuse = [f0, f0 + V((0.006, 0.012, 0.026)), f0 + V((-0.006, 0.03, 0.042)), f0 + V((-0.02, 0.04, 0.046)),
        f0 + V((-0.026, 0.05, 0.058)), f0 + V((-0.018, 0.058, 0.068))]
add(pl.sausage("fuse", fuse, [0.0085, 0.0082, 0.008, 0.0078, 0.0075, 0.0072], 6, 3, "FuseCord", (True, True), 2,
               True, 60))
spark_c = fuse[-1] + V((0.003, 0.004, 0.009))
add(rw.ico("spark", 0.017, 1, tuple(spark_c), mat=SPARK, smooth_angle=0))
for k in range(6):
    a = math.radians(30 + 60 * k)
    d = V((math.cos(a), 0.25, math.sin(a))).normalized()
    add(pl.crystal("spark_ray", spark_c + d * 0.011, d, 0.028, 0.0075, 4, 0.6, 0.0, SPARK))
lp, ln = surf(0.006, 52)
add(dh.lamp("rarity", lp - ln * 0.002, ln, 0.0125, RARITY, up=(0, 1, 0), bezel="M_Brass", cage=0, dome=1.1))

# --- left (+X) side: brass elevation quadrant with ticks and a pointer --------------------------------------------
QC = V((BR + 0.006, -0.1, BZ - 0.012))           # quadrant pivot, on a boss on the barrel side
add(pl.disc("quad_boss", 0.014, 0.016, X_POS, QC - V((0.004, 0, 0)), "M_Steel", 14, 0.4))
qpts = [(0.0, 0.0)] + [(0.046 * math.cos(math.radians(a)), 0.046 * math.sin(math.radians(a)))
                       for a in range(-10, 101, 10)]
add(dh.prism("quadrant", qpts, QC, Y_NEG, Z_POS, X_POS, 0.005, "M_Brass", 0.0, 0.0015))
for k in range(6):
    a = math.radians(-5 + 20 * k)
    d = Y_NEG * math.cos(a) + Z_POS * math.sin(a)
    add(pl.obox("quad_tick", (0.0026, 0.0026, 0.009), QC + X_POS * 0.0055 + d * 0.039, X_POS, d, "DialInk"))
pa = math.radians(38)
pdir = Y_NEG * math.cos(pa) + Z_POS * math.sin(pa)
add(pl.capsule("quad_pointer", QC + X_POS * 0.008, QC + X_POS * 0.008 + pdir * 0.04, 0.004, 6, 1, "M_Copper"))
add(pl.rivet(QC + X_POS * 0.007, X_POS, 0.0075, 0.005, "M_Copper", 8))

# --- right (-X) side: two spare shells strapped in a cradle --------------------------------------------------------
SX = -(BR + 0.01)
SY0, SY1 = -0.128, -0.066
for sz in (-0.0185, 0.0185):
    c0 = V((SX, SY1, BZ + sz))
    shell = [(0.0, 0.0), (0.0165, 0.0), (0.0175, 0.003), (0.0175, 0.008), (0.016, 0.009), (0.016, 0.04),
             (0.0, 0.04)]
    add(pl.lathe_axis("shell_case", shell, Y_NEG, c0, 16, "M_Brass", False, False, 40))
    nose = [(0.0, 0.0), (0.0165, 0.0), (0.0165, 0.004), (0.014, 0.012), (0.009, 0.02), (0.0, 0.024)]
    add(pl.lathe_axis("shell_nose", nose, Y_NEG, c0 + Y_NEG * 0.039, 16, SHELL_NOSE, False, False, 50))
    add(pl.rivet(c0 + Y_POS * 0.0005, Y_POS, 0.005, 0.003, "M_Copper", 8))       # primer cap
add(rw.rounded_box("cradle", (0.016, SY1 - SY0 - 0.012, 0.064), 0.004, (-BR - 0.002, (SY0 + SY1) / 2, BZ),
                   mat="M_Steel", segments=1))
ST_Y = SY1 - 0.022
add(rw.rounded_box("shell_strap", (0.04, 0.009, 0.08), 0.004, (SX - 0.002, ST_Y, BZ), mat="M_Leather__5a3420",
                   segments=2))
add(rw.rounded_box("buckle", (0.006, 0.015, 0.017), 0.002, (SX - 0.0225, ST_Y, BZ + 0.004), mat="M_Brass",
                   segments=1))

# --- right (-X) side of the breech: hinge + maker's plate with a bomb emblem ------------------------------------
for dz in (-0.014, 0.014):
    add(pl.rod("hinge_knuckle", (-0.059, BP_Y, BZ + dz - 0.0085), (-0.059, BP_Y, BZ + dz + 0.0085), 0.0072, 10,
               "M_Brass"))
add(pl.rod("hinge_pin", (-0.059, BP_Y, BZ - 0.026), (-0.059, BP_Y, BZ + 0.026), 0.0032, 8, "M_Steel"))
add(rw.rounded_box("hinge_leaf", (0.008, 0.03, 0.044), 0.003, (-0.064, BP_Y - 0.016, BZ), mat="M_Brass", segments=1))
mp, mn = surf(0.004, 180)
add(dh.plate("maker", mp - mn * 0.0015, mn, 0.036, 0.03, 0.004, up=(0, 0, 1), mat="M_Brass", rivets="M_Copper",
             rr=0.0034))
mc = mp + mn * 0.0025
add(pl.disc("bomb", 0.0085, 0.004, mn, mc + V((0, 0.002, -0.002)), "M_DarkMetal", 14, 0.4))
mu, mv, _ = dh.basis(mn, (0, 0, 1))
add(pl.capsule("bomb_fuse", mc + mn * 0.002 + mv * 0.006 - mu * 0.003, mc + mn * 0.002 + mv * 0.011 - mu * 0.008,
               0.0022, 5, 1, "FuseCord"))
add(rw.ico("bomb_spark", 0.0042, 1, tuple(mc + mn * 0.003 + mv * 0.0125 - mu * 0.0095), mat=SPARK, smooth_angle=0))

# --- recoil damper under the barrel ----------------------------------------------------------------------------------
DZ = BZ - BR - 0.02
DY0, DY1 = -0.12, -0.25
add(pl.lathe_axis("damper", [(0.0, 0.0), (0.012, 0.0), (0.0135, 0.004), (0.0135, 0.07), (0.012, 0.075), (0.0, 0.075)],
                  Y_NEG, (0, DY0, DZ), 14, "M_Steel", False, False, 40))
add(pl.rod("damper_rod", (0, DY0 - 0.07, DZ), (0, DY1, DZ), 0.0062, 10, "M_Steel"))
add(dh.spring("damper_spring", (0, DY0 - 0.074, DZ), (0, DY1 + 0.006, DZ), 0.0105, 0.0028, 5.0, "M_Copper", 6))
for y in (DY0 - 0.012, DY1 + 0.002):
    add(rw.rounded_box("damper_clamp", (0.016, 0.012, 0.034), 0.004, (0, y, DZ + 0.013), mat="M_Brass", segments=1))

# --- bracket + trigger guard + trigger ----------------------------------------------------------------------------
add(rw.rounded_box("bracket", (0.05, 0.07, 0.05), 0.012, (0, 0.0, BZ - BR - 0.005), mat="M_Brass", segments=2))
for sx in (-1, 1):
    add(pl.rivet((sx * 0.025, 0.012, BZ - BR - 0.01), (sx, 0, 0), 0.0045, 0.003, "M_Steel", 6))
guard = [(0, -0.07, BZ - BR + 0.005), (0, -0.09, 0.02), (0, -0.072, -0.012), (0, -0.045, -0.02)]
add(pl.sausage("guard", guard, 0.0085, 8, 3, "M_Brass", (True, True), 2, True, 60))
add(pl.capsule("trigger", (0, -0.045, BZ - BR - 0.01), (0, -0.058, 0.035), 0.007, 8, 2, "M_Steel"))

mortar = rw.join(parts, "BoomMortar", origin=(0, 0, 0))
rw.smooth(mortar, 45)

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, Y_MOUTH, BZ))
pl.check("vm_boom_mortar", (0, 0, 0))
rw.finish("vm_boom_mortar", "weapons", icon=False)
import wpn_icon  # noqa: E402
wpn_icon.render("vm_boom_mortar")
