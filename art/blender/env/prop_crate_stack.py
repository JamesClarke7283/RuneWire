"""prop_crate_stack: stack of wooden crates and grain sacks (2 x 2 x 2 m). Origin at the ground centre."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_crate_stack"
rw.reset()
P = []
# (size, bottom-centre, rotz)
crates = [((0.92, 0.92, 0.9), (-0.5, -0.47, 0.0), 4),
          ((0.84, 0.84, 0.84), (0.53, -0.52, 0.0), -9),
          ((0.9, 0.9, 0.9), (-0.49, 0.52, 0.0), -3),
          ((0.76, 0.76, 0.72), (-0.42, 0.02, 0.9), 13),
          ((0.42, 0.42, 0.38), (-0.36, 0.0, 1.62), -20)]
for i, (sz, loc, rz) in enumerate(crates):
    P += E.crate(sz, loc, rz, m="M_WoodPlanks", trim="M_WoodDark")
    E.col_box("Crate", sz, (loc[0], loc[1], loc[2] + sz[2] / 2), (0, 0, rz))
# sacks
sacks = [((0.52, 0.5, 0.0), 0.62, 0.28, 30, 0), ((0.78, 0.2, 0.0), 0.55, 0.25, -20, -8),
         ((0.5, -0.5, 0.84), 0.5, 0.24, 60, 6), ((0.25, 0.78, 0.0), 0.5, 0.24, 10, 10)]
for (loc, h, r, rz, tilt) in sacks:
    P += E.sack(loc, h, r, rz, tilt, m="M_Fabric__c9a66b")
    E.col_box("Sack", (2 * r * 0.9, 2 * r * 0.9, h * 0.85), (loc[0], loc[1], loc[2] + h * 0.42), (0, 0, rz))
# a coil of rope and a lantern on top for charm
P.append(E.ring("rope", 0.13, 0.035, (0.53, -0.4, 0.88), (0, 0, 1), "Rope", 14, 6))
P.append(E.ring("rope", 0.1, 0.03, (0.53, -0.4, 0.93), (0, 0, 1), "Rope", 14, 6))
E.join(P, "CrateStack")
E.check(ASSET, (2.0, 2.0, 2.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
