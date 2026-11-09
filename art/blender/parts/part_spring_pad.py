"""part_spring_pad: diameter 1.2 m x 0.4 m high bounce pad.

Nodes (origin of the whole model = bounding-box centre; the ground is at z = -0.2):
  SpringPad  static: steel base disc with a hazard-striped rim, bolts and a raised spring seat; a big
             copper coil spring; a telescoping steel guide post in the middle.
  Top        separate object, origin at its centre: a steel pressure plate under a puffy tufted pad
             with alternating red/yellow segments, yellow piping and a brass centre button.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

R, H = 0.6, 0.4
Z0, Z1 = -H / 2, H / 2
RED = "M_Fabric__d8392b"
YELLOW = "M_Fabric__f2c12e"
rw.flat("WarnBlack", "1e1a22", 0.6, 0.0)
rw.flat("WarnYellow", "ffc531", 0.5, 0.0)

# --- base -------------------------------------------------------------------------------------------------
bp = []
BZ1 = Z0 + 0.05                               # base top
base = pl.lathe_axis("base", [(0.0, Z0), (R - 0.015, Z0), (R, Z0 + 0.015), (R, BZ1 - 0.02), (R - 0.02, BZ1),
                              (0.0, BZ1)], (0, 0, 1), (0, 0, 0), 36, "M_Steel", False, False, 40)
# hazard stripes on the rim: alternate yellow / black every 3 segments
seg = 2 * math.pi / 36


def hazard(c, n):
    if abs(n.z) > 0.5 or (c.x ** 2 + c.y ** 2) ** 0.5 < R - 0.025:
        return False
    k = int(((math.atan2(c.y, c.x) + 2 * math.pi) % (2 * math.pi)) / seg)
    return (k // 3) % 2 == 0


rw.set_mat_where(base, "WarnYellow", hazard)
rw.set_mat_where(base, "WarnBlack", lambda c, n: (abs(n.z) < 0.5 and (c.x ** 2 + c.y ** 2) ** 0.5 > R - 0.025
                                                 and not hazard(c, n)))
bp.append(base)
for i in range(8):
    a = math.radians(22.5 + 45 * i)
    bp.append(pl.bolt((math.cos(a) * 0.53, math.sin(a) * 0.53, BZ1), (0, 0, 1), 0.026, 0.014, "M_Steel",
                      washer=True, spin=10 * i, bevel=False))
# raised spring seat
SEAT_R = 0.39
SEAT_H = 0.016
bp.append(pl.lathe_axis("seat", [(SEAT_R - 0.06, BZ1 - 0.002), (SEAT_R + 0.06, BZ1 - 0.002), (SEAT_R + 0.06, BZ1 + 0.008),
                                 (SEAT_R + 0.045, BZ1 + SEAT_H), (SEAT_R - 0.045, BZ1 + SEAT_H), (SEAT_R - 0.06, BZ1 + 0.008),
                                 (SEAT_R - 0.06, BZ1 - 0.002)], (0, 0, 1), (0, 0, 0), 32, "M_DarkMetal", False,
                        False, 40))
# guide post (two telescoping tubes)
bp.append(pl.lathe_axis("post", [(0.0, BZ1), (0.1, BZ1), (0.1, BZ1 + 0.02), (0.075, BZ1 + 0.035), (0.075, 0.0),
                                 (0.055, 0.005), (0.055, 0.075), (0.0, 0.075)], (0, 0, 1), (0, 0, 0), 20, "M_Steel",
                        False, False, 40))

# --- copper coil spring --------------------------------------------------------------------------------------
TOP_PLATE_Z = 0.075                          # underside of the Top's steel plate
WIRE = 0.025
c0 = BZ1 + SEAT_H + WIRE
c1 = TOP_PLATE_Z - WIRE
bp.append(pl.helix("spring", SEAT_R, WIRE, 2.0, c1 - c0, (0, 0, c0), (0, 0, 1), 18, 8, "M_Copper", 90))
pad = rw.join(bp, "SpringPad", origin=(0, 0, 0))
rw.smooth(pad, 40)

# --- Top: pressure plate + puffy red/yellow pad ------------------------------------------------------------
tp = []
PL_T = 0.03
PR = 0.465                                    # pressure plate radius
tp.append(pl.lathe_axis("plate", [(0.0, TOP_PLATE_Z), (PR - 0.02, TOP_PLATE_Z), (PR, TOP_PLATE_Z + 0.012),
                                  (PR, TOP_PLATE_Z + PL_T), (0.0, TOP_PLATE_Z + PL_T)], (0, 0, 1), (0, 0, 0), 32,
                        "M_Steel", False, False, 40))
for i in range(10):
    a = math.radians(18 + 36 * i)
    d = V((math.cos(a), math.sin(a), 0))
    tp.append(pl.rivet(d * PR + V((0, 0, TOP_PLATE_Z + 0.02)), d, 0.013, 0.006, "M_Steel", 6))
CUSH_H = Z1 - (TOP_PLATE_Z + PL_T) + 0.004     # the brass button adds the last ~1.6 cm on top
cz = Z1 - 0.016 - CUSH_H / 2
cush = pl.superellipsoid("cushion", (0.94, 0.94, CUSH_H), (0, 0, cz), 1.0, 0.6, 32, 12, RED)
pl.tuft(cush, [(math.cos(math.radians(22.5 + 45 * i)) * 0.24, math.sin(math.radians(22.5 + 45 * i)) * 0.24, 0)
               for i in range(8)], 0.1, 0.022, axis=2, sign=1)
rw.set_mat_where(cush, YELLOW, lambda c, n: n.z > 0.25 and
                 int(((math.atan2(c.y, c.x) + 2 * math.pi) % (2 * math.pi)) / (math.pi / 4)) % 2 == 0)
tp.append(cush)
# yellow piping around the widest edge
tp.append(rw.torus("piping", 0.47, 0.022, 32, 6, (0, 0, cz), mat=YELLOW))
# brass centre button
mw = cush.matrix_world
top_c = max((mw @ v.co).z for v in cush.data.vertices if (mw @ v.co).xy.length < 0.05)
tp.append(pl.lathe_axis("button", [(0.0, top_c - 0.02), (0.07, top_c - 0.02), (0.075, top_c - 0.005),
                                   (0.05, top_c + 0.012), (0.0, top_c + 0.016)], (0, 0, 1), (0, 0, 0), 20, "M_Brass",
                        False, False, 50))
top = rw.join(tp, "Top", origin=None)
rw.smooth(top, 40)
rw.center_origin(top)

pl.check("part_spring_pad", (2 * R, 2 * R, H))
print("RWREPORT   Top origin %s" % (tuple(round(v, 3) for v in top.location),))
rw.finish("part_spring_pad", "parts", icon=True)
