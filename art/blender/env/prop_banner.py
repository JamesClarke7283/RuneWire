"""prop_banner: pole with a hanging blue banner (M_Fabric__2a6fdb) and a gear + rune emblem (1 x 0.2 x 5 m).
The banner faces -Y. Origin at the ground centre."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envlib as E  # noqa: E402

rw = E.rw
ASSET = "prop_banner"
rw.reset()
P = []
PY = 0.025   # pole y (behind the banner)
P.append(E.lathe("pole", [(0.068, 0.0), (0.068, 0.22), (0.052, 0.25), (0.048, 4.62), (0.0, 4.62)], 10, loc=(0, PY, 0), m="M_WoodDark"))
P.append(E.ring("collar", 0.066, 0.017, (0, PY, 0.24), (0, 0, 1), "M_Brass", 12, 5))
P.append(E.ring("collar", 0.058, 0.016, (0, PY, 1.3), (0, 0, 1), "M_Brass", 12, 5))
P.append(E.lathe("finial", [(0.06, 4.6), (0.07, 4.66), (0.05, 4.7), (0.035, 4.72), (0.065, 4.78), (0.0, 5.0)], 8, loc=(0, PY, 0), m="M_Brass", smooth=0))
P.append(E.rod("crossbar", (-0.46, PY, 4.47), (0.46, PY, 4.47), 0.03, 8, "M_Brass"))
for sx in (-1, 1):
    P.append(E.ball("barend", 0.045, (sx * 0.46, PY, 4.47), "M_Brass", 8, 6))
for i in range(5):
    x = -0.36 + 0.18 * i
    P.append(E.ring("loop", 0.045, 0.012, (x, PY - 0.01, 4.47), (1, 0, 0), "M_Brass", 8, 4))
ban = E.cloth("banner", 0.82, 2.6, (0, -0.035, 4.44), wave=0.03, waves=1.2, tail=0.42, m="M_Fabric__2a6fdb", t=0.025, nu=8, nv=10)
P.append(ban)
# gold trim along the swallowtail
trim = []
for k in range(9):
    u = k / 8
    depth = 2.6 - 0.42 * (1 - abs(2 * u - 1))
    trim.append(((u - 0.5) * 0.82, -0.035 + 0.03 * math.sin((u * 1.2 + 0.6) * 2 * math.pi), 4.44 - depth + 0.03))
P.append(E.tube("trim", trim, 0.018, "Gold", 1, smooth=False))
# emblem: gear + rune, front only
gz = 3.45
y_face = -0.035 + 0.03 * math.sin((0.5 * 1.2 + (4.44 - gz) / 2.6 * 0.6) * 2 * math.pi) * (0.3 + 0.7 * (4.44 - gz) / 2.6)
P.append(E.gear("gear", 0.31, 10, 0.07, 0.02, 0.0, (0, y_face - 0.022, gz), (0, -1, 0), "M_Brass", 0.005))
P.append(E.disc("gearface", 0.2, 0.02, (0, y_face - 0.03, gz), (0, -1, 0), 16, "M_Fabric__1f4fa8"))
P += E.glyph(3, 0.27, (0, y_face - 0.042, gz), (0, -1, 0), "TealGlow", stroke=0.2, depth=0.014)
E.join(P, "Banner")
E.col_cyl("Pole", 0.08, 5.0, (0, PY, 2.5), verts=8)
E.check(ASSET, (1.0, 0.2, 5.0), 4000)
rw.finish(ASSET, "env", previews=E.previews())
