"""prop_barrels: group of wooden barrels, one lying on its side, a small keg on top (2 x 2 x 1.2 m).
Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_barrels"
rw.reset()
P = []
# upright barrels: (r, h, x, y, rotz)
ups = [(0.4, 1.2, -0.56, 0.55, 10), (0.37, 0.98, 0.58, 0.58, -25), (0.36, 0.92, -0.6, -0.5, 40)]
for i, (r, h, x, y, rz) in enumerate(ups):
    P += E.barrel(r, h, (x, y, 0.0), rz, seg=14, m="M_WoodDark" if i != 1 else "M_WoodPlanks", hoop="Iron")
    E.col_cyl("Barrel", r, h, (x, y, h / 2), verts=12)
# painted gear brand on the tall barrel
P.append(E.gear("brand", 0.13, 8, 0.035, 0.02, 0.0, (-0.56, 0.55 - 0.405, 0.62), (0, -1, 0), "Gold", 0.004))
# brass tap on the middle barrel
P.append(E.rod("tap", (0.58 - 0.0, 0.58 - 0.36, 0.25), (0.58, 0.58 - 0.47, 0.25), 0.03, 8, "M_Brass"))
P.append(E.rod("tapdown", (0.58, 0.58 - 0.47, 0.25), (0.58, 0.58 - 0.47, 0.17), 0.022, 8, "M_Brass"))
P.append(E.rbox("taphandle", (0.1, 0.025, 0.03), (0.58, 0.58 - 0.45, 0.3), m="M_Brass", r=0.008))
# barrel lying on its side, chocked with a wedge
lay = E.barrel(0.32, 0.86, (0, 0, 0), 0, seg=14, m="M_WoodPlanks", hoop="Iron", lying=True)
E.place(lay, (0.55, -0.55, 0.0), (0, 0, 65))
P += lay
E.col_beam("Lying", (0.55 - 0.43 * 0.4226, -0.55 - 0.43 * 0.9063, 0.32), (0.55 + 0.43 * 0.4226, -0.55 + 0.43 * 0.9063, 0.32), 0.62, 0.62)
# small keg on top of the front-left barrel
keg = E.barrel(0.14, 0.24, (0, 0, 0), 0, seg=12, m="M_WoodDark", hoop="M_Brass", lying=True)
E.place(keg, (-0.6, -0.5, 0.92), (0, 0, 20))
P += keg
P.append(E.ring("rope", 0.09, 0.025, (0.58, 0.58, 1.0), (0, 0, 1), "Rope", 12, 5))
E.join(P, "Barrels")
E.check(ASSET, (2.0, 2.0, 1.2), 4000)
rw.finish(ASSET, "env", previews=E.previews())
