"""item_pouch_alchemist: "Alchemist's Bandolier", a curved leather strap of potion vials, about 0.30 x 0.24 x 0.15 m.

A short length of bandolier: a sturdy brown leather strap (M_Leather) curving in a C (convex toward the
front), with a brass buckle at one end and a pointed, punched tip at the other. Four little corked glass vials
of red, blue, green and violet potion stand in darker leather loops (M_Leather__a07858) along its front, each
loop studded with a brass rivet; the curve is turned 32 deg toward the 3/4 view. One mesh object "PouchAlchemist", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_pouch_alchemist"
rw.reset()

STRAP = "M_Leather"
LOOP = "M_Leather__a07858"
BRASS = pk.mat("M_Brass")
pk.glow("VialViolet", "8a3dff", 0.5)
pk.glow("VialVioletTop", "c9a0ff", 0.8)

R, CY = 0.15, 0.09                           # strap arc radius and centre (convex toward -Y)
SH, ST = 0.056, 0.01                         # strap height (Z) and thickness
A0, A1 = 212, 328                            # arc span in degrees (270 = straight at the front)


def arc_pt(a, r=R):
    t = math.radians(a)
    return V((r * math.cos(t), CY + r * math.sin(t), 0.0))


def out_dir(a):
    t = math.radians(a)
    return V((math.cos(t), math.sin(t), 0.0))


path = [arc_pt(A0 + (A1 - A0) * i / 12) for i in range(13)]
parts = [pk.strap("strap", path, SH, ST, lambda q: (q - V((0, CY, q.z))).normalized(), STRAP, 2, taper=None)]
# pointed tip at the left end with punched holes, buckle at the right end
tip_a = A0 - 9
tip = [arc_pt(A0), arc_pt(A0 - 4), arc_pt(tip_a)]
parts.append(pk.strap("strap_tip", tip, SH, ST, lambda q: (q - V((0, CY, q.z))).normalized(), STRAP, 2,
                      taper=(1.0, 0.25)))
for k in range(2):
    a = A0 + 2 - 6 * k
    p = arc_pt(a, R - ST / 2 - 0.0005)
    parts.append(pl.disc("hole", 0.0055, 0.003, tuple(-out_dir(a)), tuple(p), pk.mat("PouchShadow"), 8, 0.2))
    p = arc_pt(a, R + ST / 2 + 0.0005)
    parts.append(pl.disc("hole", 0.0055, 0.003, tuple(out_dir(a)), tuple(p), pk.mat("PouchShadow"), 8, 0.2))
end = arc_pt(A1)
parts += pk.buckle("buckle", arc_pt(A1 - 2, R + ST / 2 + 0.002), out_dir(A1 - 2),
                   (V((0, 0, 1)).cross(out_dir(A1))), SH + 0.012, 0.03, 0.0052, BRASS, bar=True, prong=True)

# four vials in leather loops
VIALS = (("TonicRed", "TonicRedTop", None, 0.115), ("ManaBlue", "ManaBlueTop", "ManaWax", 0.125),
         ("SwiftGreen", "SwiftGreenTop", None, 0.12), ("VialViolet", "VialVioletTop", "VelvetViolet", 0.115))
VR = 0.023
for i, (liq, top, wax, h) in enumerate(VIALS):
    a = A0 + 14 + (A1 - A0 - 28) * i / 3
    d = out_dir(a)
    base = arc_pt(a, R + ST / 2 + VR + 0.004) + V((0, 0, -0.034))
    parts.append(pk.vial("vial", base, (0, 0, 1), h, VR, liq, top, 0.78, "Cork", 10, spin=a + 90, wax=wax,
                         cork_segs=8))
    c = base + V((0, 0, 0.036))
    parts.append(pl.band("loop", VR + 0.0065, 0.024, 0.006, (0, 0, 1), tuple(c), pk.mat(LOOP), 12, 0.0))
    parts.append(pl.rivet(c + d * (VR + 0.0065), d, 0.006, 0.0045, BRASS, 6))

pouch = rw.join(parts, "PouchAlchemist", origin=(0, 0, 0))
pk.transform(pouch, pk.rot((0, 0, 1), -32))          # turn the curve's front toward the 3/4 view so no vial hides
pk.fit(pouch, 0.30)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.30,))
