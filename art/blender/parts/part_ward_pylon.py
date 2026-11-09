"""part_ward_pylon: 0.6 x 0.6 x 1.7 m ward pylon.

Nodes (origin of the whole model = bounding-box centre; the ground is at z = -0.85):
  Pylon     static: a wide octagonal stone plinth with a riveted brass band, a tapered octagonal stone
            column with carved glowing rune glyphs, a brass cradle cup with a glowing rune ring and an
            emitter dome, and three curved brass claws (glowing gem tips) rising around the crystal.
  Crystal   separate object, origin at its centre (0, 0, CRYSTAL_Z) = 1.45 m above the ground: a
            double-pointed teal crystal (M_Crystal) floating between the claws, with two little shards
            orbiting it (part of the same object, so they turn with it).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, H = 0.6, 1.7
Z0 = -H / 2
CRYSTAL_Z = Z0 + 1.45
C8 = math.cos(math.radians(22.5))


def lathe8(name, prof_apothem, mat):
    return pl.lathe_axis(name, [(a / C8, z) for (a, z) in prof_apothem], (0, 0, 1), (0, 0, 0), 8, mat, False,
                         False, 30, 22.5)


parts = []
# --- stone plinth + tapered column (one carved lathe) ---------------------------------------------------
P1 = Z0 + 0.24               # plinth top
C0, C1 = P1 + 0.05, Z0 + 0.95  # column faces
A0, A1 = 0.19, 0.165         # column apothem bottom/top
stone = lathe8("stone", [(0.0, Z0), (0.284, Z0), (0.3, Z0 + 0.016), (0.3, Z0 + 0.06), (0.275, Z0 + 0.085),
                         (0.262, P1 - 0.03), (0.245, P1), (0.215, P1 + 0.012), (A0, C0), (A1, C1),
                         (A1 + 0.02, C1 + 0.01), (A1 + 0.02, C1 + 0.05), (0.0, C1 + 0.05)], "M_Stone")
KEYS = ("algiz", "ingwaz", "tiwaz", "sowilo", "dagaz", "othala", "kenaz", "fehu")
glyph_faces = []
tilt = math.atan2(A0 - A1, C1 - C0)
for i in range(8):
    ang = math.radians(-90 + 45 * i)
    n_h = V((math.cos(ang), math.sin(ang), 0))
    u = V((-math.sin(ang), math.cos(ang), 0))
    v = (V((0, 0, 1)) * math.cos(tilt) - n_h * math.sin(tilt)).normalized()
    zc = (C0 + C1) / 2 + 0.03
    a_at = A0 + (A1 - A0) * (zc - C0) / (C1 - C0)
    nrm = u.cross(v).normalized()
    if nrm.dot(n_h) < 0:
        u = -u
        nrm = -nrm
    glyph_faces.append((n_h * a_at + V((0, 0, zc)), u, v, nrm, KEYS[i]))
cut = []
for (c, u, v, n, k) in glyph_faces:
    cut += pl.glyph_cutters(k, c, u, v, 0.15, 0.026, 0.05)
pl.carve(stone, cut)
parts.append(stone)
for (c, u, v, n, k) in glyph_faces:
    parts += pl.glyph(k, c - n * 0.019, u, v, 0.15, 0.018, 0.01, "M_RuneGlow")
# brass band with rivets around the plinth, and a band at the column foot
parts.append(lathe8("band", [(0.28, Z0 + 0.105), (0.282, Z0 + 0.105), (0.282, Z0 + 0.15), (0.26, Z0 + 0.15),
                             (0.28, Z0 + 0.105)], "M_Brass"))
for i in range(8):
    ang = math.radians(-90 + 45 * i)
    n = V((math.cos(ang), math.sin(ang), 0))
    parts.append(pl.rivet(n * 0.279 + V((0, 0, Z0 + 0.1275)), n, 0.013, 0.006, "M_Brass", 6))
parts.append(lathe8("footband", [(0.2, C0 - 0.005), (0.212, C0 - 0.005), (0.212, C0 + 0.04), (0.19, C0 + 0.04),
                                 (0.2, C0 - 0.005)], "M_Brass"))

# --- brass cradle cup with a glowing rune ring and an emitter dome ------------------------------------------
K0 = C1 + 0.04
cup = [(0.0, K0), (0.16, K0), (0.2, K0 + 0.03), (0.2, K0 + 0.06), (0.185, K0 + 0.07), (0.185, K0 + 0.11),
       (0.21, K0 + 0.13), (0.21, K0 + 0.16), (0.16, K0 + 0.18), (0.0, K0 + 0.18)]
parts.append(pl.lathe_axis("cup", cup, (0, 0, 1), (0, 0, 0), 24, "M_Brass", False, False, 40))
parts.append(pl.band("runering", 0.19, 0.035, 0.02, (0, 0, 1), (0, 0, K0 + 0.09), "M_RuneGlow", 24, 0.0))
TOPZ = K0 + 0.18
parts.append(rw.sphere("emitter", 0.08, 16, 8, (0, 0, TOPZ), scale=(1, 1, 0.55), mat="M_Crystal"))
parts.append(pl.band("emitter_ring", 0.095, 0.025, 0.02, (0, 0, 1), (0, 0, TOPZ + 0.005), "M_Brass", 20, 0.0))

# --- three curved brass claws ------------------------------------------------------------------------------
for i in range(3):
    a = math.radians(90 + 120 * i)                 # one claw at the back (+Y), two toward the front
    d = V((math.cos(a), math.sin(a), 0))
    pts = [d * 0.15 + V((0, 0, TOPZ - 0.05)), d * 0.225 + V((0, 0, TOPZ + 0.06)),
           d * 0.25 + V((0, 0, CRYSTAL_Z - 0.06)), d * 0.225 + V((0, 0, CRYSTAL_Z + 0.12)),
           d * 0.13 + V((0, 0, H / 2 - 0.05))]
    parts.append(pl.sausage("claw", pts, [0.05, 0.046, 0.042, 0.038, 0.034], 10, 4, "M_Brass", (True, True), 2,
                            True, 50))
    parts.append(pl.band("collar", 0.06, 0.05, 0.02, (pts[1] - pts[0]).normalized(), pts[0] + (pts[1] - pts[0]) * 0.5,
                         "M_Steel", 12, 0.0))
    tip = pts[-1]
    parts.append(rw.sphere("knuckle", 0.05, 12, 6, tuple(tip), mat="M_Brass"))
    parts.append(pl.crystal("tipgem", tip - d * 0.02, (-d.x, -d.y, -0.9), 0.09, 0.028, 6, 0.4, 0.15,
                            "M_RuneGlow"))
pylon = rw.join(parts, "Pylon", origin=(0, 0, 0))
rw.smooth(pylon, 40)

# --- the floating crystal -------------------------------------------------------------------------------------
CL = 0.4
cparts = [pl.crystal("main", (0, 0, CRYSTAL_Z - CL / 2), (0, 0, 1), CL, 0.105, 6, 0.3, 0.1, "M_Crystal",
                     spin=0, double=True)]
for (a, z) in ((30, 0.05), (210, -0.06)):
    d = V((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
    cparts.append(pl.crystal("shard", d * 0.155 + V((0, 0, CRYSTAL_Z + z - 0.045)), (0, 0, 1), 0.09, 0.028, 6, 0.32,
                             0.1, "M_Crystal", spin=a, double=True))
crystal = rw.join(cparts, "Crystal", origin=(0, 0, CRYSTAL_Z))
rw.smooth(crystal, 20)

pl.check("part_ward_pylon", (W, W, H))
print("RWREPORT   crystal centre height above ground %.3f" % (CRYSTAL_Z - Z0))
rw.finish("part_ward_pylon", "parts", icon=True)
