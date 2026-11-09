"""item_ley_cargo: the Ley Crystal Cargo (exactly 1.2 x 1.2 x 1.2 m), the heavy delivery crate of the cargo quest.

A reinforced crate: a chunky dark-wood frame (M_WoodDark edge beams) with brass corner caps and nail heads, three
horizontal slats per side with wide gaps, two riveted steel straps over every side, a slatted top with an open middle
and a solid plank floor. Inside, a big ley crystal (M_Crystal) with four smaller crystals and a glowing teal core
stands in a brass cradle, so it glows through every gap and its tip shows through the top. A brass label plate with a
teal ley rune sits on the front, and iron handles on the +-X sides.

A build Part (scripts/build/part.gd "cargo": a 1.2 m box collider): the origin is the BOUNDING-BOX CENTRE and the
model is one object ("Cargo"). No collision objects.
"""
import math
import os
import sys

from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "env"))
import proplib as PL  # noqa: E402

E, rw, V, M = PL.E, PL.rw, PL.V, PL.M
ASSET = "item_ley_cargo"
PL.reset()
PL.preview_glow("M_Crystal", "36c9b8", "5fe9ff", 1.1)   # previews / icon only (Godot uses its own M_Crystal)
P = []
H = 0.6                   # half size
F = 0.14                  # frame beam thickness
FO = H - 0.015            # frame outer face (the brass corner caps stand 5 mm prouder)
IN = FO - F               # inner half span (0.445)
SL = 0.045                # slat thickness
SO = H - 0.05             # slat outer face (the frame stands 5 cm proud of the slats)
FZ = -0.47                # floor top

# ---------------------------------------------------------------- frame: 12 edge beams
for sx in (-1, 1):
    for sy in (-1, 1):
        P.append(E.rbox("post", (F, F, 2 * FO - 0.02), (sx * (FO - F / 2), sy * (FO - F / 2), 0), m="M_WoodDark",
                        r=0.025))
        P.append(E.rbox("beamx", (2 * IN + 0.02, F, F), (0, sx * (FO - F / 2), sy * (FO - F / 2)), m="M_WoodDark",
                        r=0.025))
        P.append(E.rbox("beamy", (F, 2 * IN + 0.02, F), (sx * (FO - F / 2), 0, sy * (FO - F / 2)), m="M_WoodDark",
                        r=0.025))

# ---------------------------------------------------------------- slats: three per side with wide gaps
SH = 0.155                                          # slat height
ZS = (-IN + SH / 2 + 0.005, 0.0, IN - SH / 2 - 0.005)
for (n, t) in (((0, -1, 0), (1, 0, 0)), ((1, 0, 0), (0, 1, 0)), ((0, 1, 0), (-1, 0, 0)), ((-1, 0, 0), (0, -1, 0))):
    n, t = V(n), V(t)
    for k, z in enumerate(ZS):
        c = n * (SO - SL / 2) + V((0, 0, z))
        P.append(PL.obox("slat", (2 * IN + 0.02, SL, SH - 0.01), tuple(c), tuple(t), (0, 0, 1), "M_WoodPlanks", 0.012))
    # two riveted steel straps over the slats
    for s in (-1, 1):
        c = n * (SO + 0.008) + t * (s * 0.27)
        P.append(PL.obox("strap", (0.085, 0.018, 2 * IN + 0.02), tuple(c), tuple(t), (0, 0, 1), "M_Steel", 0.005))
        for z in (ZS[0], ZS[2]):
            P.append(PL.rivet(tuple(c + n * 0.009 + V((0, 0, z))), tuple(n), 0.02, 0.012, "M_Brass", 6))
# top: two slats at the sides and a cross batten, open in the middle for the crystal tip
for s in (-1, 1):
    P.append(PL.obox("topslat", (2 * IN + 0.02, 0.24, SL), (0, s * 0.33, SO - SL / 2), (1, 0, 0), (0, 0, 1),
                     "M_WoodPlanks", 0.012))
for s in (-1, 1):
    P.append(PL.obox("topbatten", (0.11, 2 * IN + 0.02, SL), (s * 0.3, 0, SO - SL / 2 + 0.012), (1, 0, 0), (0, 0, 1),
                     "M_WoodPlanks", 0.012))
# solid plank floor between the bottom beams
P.append(rw.box("floor", (2 * IN + 0.02, 2 * IN + 0.02, 0.1), (0, 0, FZ - 0.05), mat=PL.mat("M_WoodPlanks")))

# ---------------------------------------------------------------- brass corner caps with nail heads
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            c = V((sx * (H - 0.115), sy * (H - 0.115), sz * (H - 0.115)))
            P.append(E.cbox("cap", (0.21, 0.21, 0.21), tuple(c), (0, 0, 0), "M_Brass", 0.03))
            # flat nail heads standing 1 cm proud of each cap face (they define the 1.2 m envelope)
            for d in ((sx, 0, 0), (0, sy, 0), (0, 0, sz)):
                size = tuple(0.02 if d[i] else 0.04 for i in range(3))
                rot = tuple(45 * abs(d[i]) for i in range(3))
                P.append(rw.box("nail", size, tuple(c + V(d) * 0.105), rot, PL.mat("Iron")))

# ---------------------------------------------------------------- the crystal inside, in a brass cradle
P.append(PL.lathe_ax("cradle", [(0.0, 0.0), (0.36, 0.0), (0.36, 0.05), (0.3, 0.09), (0.22, 0.1), (0.0, 0.1)],
                     (0, 0, 1), (0, 0, FZ), 12, "M_Brass", 40, False, False))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = V((math.cos(a), math.sin(a), 0))
    P.append(PL.sausage("prong", [d * 0.33 + V((0, 0, FZ + 0.08)), d * 0.38 + V((0, 0, -0.2)),
                                  d * 0.33 + V((0, 0, -0.03))], 0.028, 6, 2, "M_Brass", (True, True), 2))
P.append(E.bipyramid("crystal", 0.31, 0.55, 0.16, 6, (0, 0, -0.11), "M_Crystal", twist=0, mid=0.26))
P.append(rw.ico("core", 0.21, 1, (0, 0, -0.09), (0, 0, 0), (1, 1, 1.7), M("TealGlow"), None, 0))
for k, (ang, tilt, L, r) in enumerate(((20, 28, 0.42, 0.09), (110, 34, 0.36, 0.08), (200, 26, 0.44, 0.095),
                                       (290, 32, 0.34, 0.075))):
    a = math.radians(ang)
    d = V((math.cos(a) * math.sin(math.radians(tilt)), math.sin(a) * math.sin(math.radians(tilt)),
           math.cos(math.radians(tilt))))
    base = V((math.cos(a) * 0.16, math.sin(a) * 0.16, FZ + 0.1))
    sh = E.bipyramid("shard", r, L * 0.7, 0.06, 6, (0, 0, 0), "TealGlow" if k % 2 else "M_Crystal", twist=ang, mid=L * 0.3)
    PL.align(sh, tuple(d))
    sh.location = tuple(base + d * 0.12)
    P.append(sh)

# ---------------------------------------------------------------- label plate and handles
P.append(PL.obox("label", (0.34, 0.13, 0.025), (0, -SO - 0.0125, 0.0), (1, 0, 0), (0, -1, 0), "M_Brass", 0.008))
P += PL.glyph("algiz", (0, -SO - 0.026, 0.0), (1, 0, 0), (0, 0, 1), 0.1, 0.022, 0.01, "TealGlow")
for (u, z) in ((-0.14, 0.0), (0.14, 0.0)):
    P.append(PL.rivet((u, -SO - 0.025, z), (0, -1, 0), 0.014, 0.008, "M_Copper", 6))
for sx in (-1, 1):
    x = sx * SO
    for s in (-1, 1):
        P.append(rw.box("handlemount", (0.03, 0.06, 0.08), (x + sx * 0.015, s * 0.12, 0.0), mat=PL.mat("Iron")))
    P.append(PL.sausage("handle", [(x + sx * 0.02, -0.12, 0.0), (x + sx * 0.03, -0.08, -0.02),
                                   (x + sx * 0.032, 0.0, -0.025), (x + sx * 0.03, 0.08, -0.02),
                                   (x + sx * 0.02, 0.12, 0.0)], 0.016, 6, 2, "Iron", (True, True), 2))

E.tri_breakdown(P, 18)
cargo = E.join(P, "Cargo", origin=(0, 0, 0))
rw.smooth(cargo, 35)

# the bounding-box centre must be the origin: re-centre if the details made it lopsided
mn, mx = rw.bounds([cargo])
c = (mn + mx) / 2
if c.length > 1e-4:
    cargo.data.transform(Matrix.Translation(-c))
    cargo.data.update()
print("RWCHECK %s bbox centre before re-centring (%.4f, %.4f, %.4f)" % (ASSET, c.x, c.y, c.z))
PL.finish(ASSET, (1.2, 1.2, 1.2), 4000, category="items", icon=True, tol=0.03, height_tol=0.03,
          origin_note="(origin = bbox centre)")
