"""vm_boom_mortar: first-person hand mortar.

Nodes (origin = grip centre; the muzzle points -Y):
  BoomMortar  a short fat dark-iron barrel (diameter ~0.16) with brass bands, a yellow/black hazard
              stripe band, a flared muzzle lip and a dark bore; a rounded breech with a riveted brass
              cap, a lit fuse (copper holder, cord and a glowing ember spark) on top, a little brass
              aiming sight, a wooden pistol grip under the breech and a front handle bracket.
  Glove       the shared cartoon leather glove gripping the pistol grip (glove.py).
  Muzzle      empty at the centre of the muzzle mouth.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glove  # noqa: E402

pl = glove.pl
rw = glove.rw
V = glove.V
rw.reset()

RAKE = 12.0
A = V((0, -math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE))))
_, o, fr = glove.frame(A, (-1, 0, 0))
rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)
rw.flat("WarnYellow", "ffc531", 0.5, 0.0)
SPARK = rw.glow("FuseSpark", "ffd36b", 5.0)
parts = []

# --- grip ------------------------------------------------------------------------------------------------
parts.append(glove.oriented_pillow("grip", (0.05, 0.066, 0.19), -fr * 0.004 - A * 0.005, o, fr, A, 0.6, 0.35, 16,
                                   10, "M_WoodDark"))
parts.append(glove.oriented_pillow("pommel", (0.06, 0.076, 0.03), A * -0.1 - fr * 0.004, o, fr, A, 0.6, 0.6, 16, 8,
                                   "M_Brass"))

# --- barrel ------------------------------------------------------------------------------------------------
BZ = 0.155                      # barrel axis height
BR = 0.08                       # barrel radius (diameter 0.16)
Y_MOUTH = -0.33
Y_BREECH = 0.06
# profile from the bore floor (h = 0.07 inside), out through the mouth (h = 0), then back along the outside
# to the rounded breech (h = L); h runs along +Y from the mouth
L = Y_BREECH - Y_MOUTH
outer = [(0.062, 0.0), (BR + 0.012, 0.0), (BR + 0.016, 0.008), (BR + 0.016, 0.026), (BR + 0.004, 0.034),
         (BR, 0.045), (BR, L - 0.07), (BR - 0.006, L - 0.04), (BR - 0.025, L - 0.015), (0.03, L), (0.0, L)]
barrel = pl.lathe_axis("barrel", [(0.0, 0.07), (0.062, 0.07), (0.062, 0.0)] + outer, (0, 1, 0), (0, Y_MOUTH, BZ), 24,
                       "M_DarkMetal", False, False, 40)
parts.append(barrel)
# brass bands
for (y, w) in ((Y_MOUTH + 0.075, 0.03), (-0.04, 0.03)):
    parts.append(pl.band("band", BR + 0.01, w, 0.016, (0, 1, 0), (0, y, BZ), "M_Brass", 24, 0.0))
# hazard stripe band: a yellow band with 8 wide black slanted stripes, as curved quads hugging its surface
HZ_Y, HZ_W = -0.16, 0.062
HR = BR + 0.006
parts.append(pl.band("hazard", HR, HZ_W, 0.012, (0, 1, 0), (0, HZ_Y, BZ), "WarnYellow", 32, 0.0))
import bmesh  # noqa: E402
bm = bmesh.new()
N_STRIPES, SLANT, HALF_W, STEPS, COLS = 8, 30.0, 11.0, 4, 4   # degrees: twist across the band, half width
for k in range(N_STRIPES):
    a0 = 360.0 * k / N_STRIPES
    grids = []
    for rr in (HR + 0.0016, HR - 0.004):                       # outer surface, inner surface
        grid = []
        for j in range(STEPS + 1):
            t = j / STEPS
            y = HZ_Y - HZ_W / 2 + 0.003 + (HZ_W - 0.006) * t
            row = []
            for c in range(COLS + 1):
                a = math.radians(a0 + SLANT * t + HALF_W * (2 * c / COLS - 1))
                row.append(bm.verts.new((math.cos(a) * rr, y, BZ + math.sin(a) * rr)))
            grid.append(row)
        grids.append(grid)
    out, inn = grids
    for j in range(STEPS):
        for c in range(COLS):
            bm.faces.new((out[j][c], out[j][c + 1], out[j + 1][c + 1], out[j + 1][c]))
            bm.faces.new((inn[j][c], inn[j + 1][c], inn[j + 1][c + 1], inn[j][c + 1]))
    # walls around the border
    for j in range(STEPS):
        for c in (0, COLS):
            bm.faces.new((out[j][c], out[j + 1][c], inn[j + 1][c], inn[j][c]))
    for c in range(COLS):
        for j in (0, STEPS):
            bm.faces.new((out[j][c], inn[j][c], inn[j][c + 1], out[j][c + 1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
parts.append(pl.obj_from_bm("stripes", bm, "WarnBlack", 0))
# rivets around the barrel between the bands
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    d = V((math.cos(a), 0, math.sin(a)))
    parts.append(pl.rivet(V((0, -0.095, BZ)) + d * BR, d, 0.008, 0.005, "M_Brass", 6))
# breech cap
cap_c = V((0, Y_BREECH - 0.012, BZ))
parts.append(pl.disc("breech_cap", 0.05, 0.02, (0, 1, 0), cap_c, "M_Brass", 20, 0.45))
for k in range(6):
    a = math.radians(30 + 60 * k)
    parts.append(pl.rivet(cap_c + V((math.cos(a) * 0.036, 0.01, math.sin(a) * 0.036)), (0, 1, 0), 0.007, 0.004,
                          "M_Steel", 6))

# --- fuse on top of the breech ---------------------------------------------------------------------------------
fz = BZ + BR - 0.01
parts.append(pl.lathe_axis("fuse_holder", [(0.0, 0.0), (0.02, 0.0), (0.02, 0.018), (0.014, 0.026), (0.0, 0.026)],
                           (0, 0, 1), (0, 0.0, fz), 12, "M_Copper", False, False, 45))
fuse = [V((0, 0.0, fz + 0.02)), V((0.004, 0.012, fz + 0.05)), V((-0.006, 0.03, fz + 0.065)),
        V((-0.012, 0.05, fz + 0.075))]
parts.append(pl.sausage("fuse", fuse, [0.009, 0.0085, 0.008, 0.0075], 6, 3, "M_Fabric__c8a26a", (True, True), 2,
                        True, 60))
spark_c = fuse[-1] + V((-0.004, 0.006, 0.008))
parts.append(rw.ico("spark", 0.019, 1, tuple(spark_c), mat=SPARK, smooth_angle=0))
# cartoon spark star: 6 chunky glowing points
for k in range(6):
    a = math.radians(30 + 60 * k)
    d = V((math.cos(a), 0.25, math.sin(a))).normalized()
    parts.append(pl.crystal("spark_ray", spark_c + d * 0.012, d, 0.03, 0.008, 4, 0.6, 0.0, SPARK))

# --- aiming sight + front handle bracket ------------------------------------------------------------------------
parts.append(rw.rounded_box("sight", (0.012, 0.03, 0.03), 0.004, (0, Y_MOUTH + 0.075, BZ + BR + 0.022),
                            mat="M_Brass", segments=1))
parts.append(rw.sphere("sight_bead", 0.008, 8, 4, (0, Y_MOUTH + 0.075, BZ + BR + 0.04), mat="M_Brass"))
# bracket joining barrel to the grip
parts.append(rw.rounded_box("bracket", (0.05, 0.07, 0.05), 0.012, (0, 0.0, BZ - BR - 0.005), mat="M_Brass",
                            segments=2))
guard = [(0, -0.07, BZ - BR + 0.005), (0, -0.09, 0.02), (0, -0.072, -0.012), (0, -0.045, -0.02)]
parts.append(pl.sausage("guard", guard, 0.008, 8, 3, "M_Brass", (True, True), 2, True, 60))
parts.append(pl.capsule("trigger", (0, -0.045, BZ - BR - 0.01), (0, -0.058, 0.035), 0.007, 8, 2, "M_Steel"))

mortar = rw.join(parts, "BoomMortar", origin=(0, 0, 0))
rw.smooth(mortar, 45)

g = glove.fist(A=A, out=(-1, 0, 0), F=(0, 1, -0.4))

rw.empty("Muzzle", (0, Y_MOUTH, BZ))
pl.check("vm_boom_mortar", (0, 0, 0))
rw.finish("vm_boom_mortar", "weapons", icon=True)
