"""item_ley_lens: a round crystal ley lens in a thick brass ring with a short handle stub, about 0.18 x 0.11 x 0.27 m.

A fat biconvex glass lens (M_Glass) with a white glint, ringed by a soft glowing teal rim (emissive flat 39d5c4),
set in a thick rounded brass ring (M_Brass) fastened with six slotted screws, standing upright and facing the
viewer (tilted back a little), with a brass collar and a short turned dark-wood handle stub at the bottom.
One mesh object "LeyLens", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_ley_lens"
rw.reset()

BR = ml.mat("M_Brass")
A = V((-0.25, -1.0, 0.3)).normalized()                 # the lens faces this way
R = pl.frame_matrix(A)
C = V((0, 0, 0))
UP = (V((0, 0, 1)) - V((0, 0, 1)).dot(A) * A).normalized()
SIDE = UP.cross(A).normalized()
parts = []

# brass ring, glowing rim and the glass
parts.append(pl.band("ring", 0.092, 0.036, 0.024, A, C, BR, 32, 0.45))
parts.append(pl.band("rim", 0.0695, 0.018, 0.0125, A, C, ml.mat("LensGlow"), 32, 0.0))
lens = [(0.0, -0.013), (0.036, -0.011), (0.062, -0.004), (0.066, 0.0), (0.062, 0.004), (0.036, 0.011), (0.0, 0.013)]
parts.append(il.lathe("lens", lens, A, C, 32, "M_Glass", 60))
# cartoon glint on the glass (upper left)
gl = C + UP * 0.03 - SIDE * 0.022 + A * 0.0125
GU, GV = (SIDE + UP).normalized(), (UP - SIDE).normalized()          # the glint strokes run diagonally
parts.append(il.wrap_prism("glint", il.capsule_pts(0.011, 0.034), il.plane_map(gl, GU, GV, 0.0, 0.0015), "Shine"))
parts.append(il.wrap_prism("glint", il.capsule_pts(0.008, 0.012),
                           il.plane_map(gl + SIDE * 0.016 - UP * 0.016, GU, GV, 0.0, 0.0015), "Shine"))

# six slotted screws on the front face of the ring
FACE = A * 0.018
for k in range(6):
    a = math.radians(90 + 60 * k)
    d = SIDE * math.cos(a) + UP * math.sin(a)
    p = C + d * 0.08 + FACE
    parts.append(pl.rivet(p, A, 0.0085, 0.0055, BR, 8, "screw", 0.4))
    t = (d.cross(A) * math.cos(0.6 + k) + d * math.sin(0.6 + k)).normalized()
    parts.append(pl.obox("slot", (0.014, 0.0028, 0.004), p + A * 0.0045, t, A, ml.mat("Shadow")))

# collar, knuckle and a short turned wooden handle stub at the bottom
B = C - UP * 0.092
parts.append(rw.sphere("knuckle", 0.017, 12, 8, tuple(B - UP * 0.004), mat=BR))
parts.append(il.lathe("collar", [(0.0, 0.0), (0.016, 0.0), (0.019, 0.006), (0.019, 0.02), (0.016, 0.024), (0.0, 0.024)],
                      -UP, B - UP * 0.012, 16, BR, 40))
grip = [(0.0, 0.0), (0.016, 0.0), (0.018, 0.012), (0.017, 0.03), (0.019, 0.044), (0.016, 0.054), (0.009, 0.059),
        (0.0, 0.06)]
parts.append(il.lathe("grip", grip, -UP, B - UP * 0.034, 14, "M_WoodDark", 50))

lens_o = rw.join(parts, "LeyLens")
ml.preview_metals()
il.finish_item(ASSET, (0.18, 0.11, 0.27))
