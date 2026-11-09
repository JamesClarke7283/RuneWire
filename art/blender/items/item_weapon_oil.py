"""item_weapon_oil: "Gunsmith's Oil", a classic brass oiler with a long thin spout, about 0.27 x 0.18 x 0.28 m.

A classic pump oil can in brass (M_Brass): a squat round base with a rolled foot ring and a signal-orange painted
label band carrying a brass gear emblem on a steel boss, a tall conical top rising to a long thin brass spout that
reaches up and out to the left, a fat drop of amber gun oil hanging from the spout tip, and a brass loop handle on
the right side with a steel thumb-pump lever. One mesh object "WeaponOil", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pouchlib as pk  # noqa: E402

il, rw, pl, V = pk.il, pk.rw, pk.pl, pk.V
ASSET = "item_weapon_oil"
rw.reset()

BRASS = pk.mat("M_Brass")
STEEL = pk.mat("M_Steel")
PAINT = pk.mat("SignalOrange")
OIL = pk.mat("OilAmber")

# squat base and conical top up to the spout socket
can = [(0.0, 0.0), (0.074, 0.0), (0.08, 0.004), (0.082, 0.012), (0.078, 0.018), (0.076, 0.022), (0.076, 0.082),
       (0.08, 0.086), (0.08, 0.092), (0.072, 0.096), (0.05, 0.122), (0.03, 0.146), (0.018, 0.162), (0.016, 0.17),
       (0.0, 0.17)]
parts = [il.lathe("can", can, segs=24, m=BRASS, smooth=40)]
# painted label band with a gear emblem facing the 3/4 view
parts.append(pl.band("label", 0.0795, 0.05, 0.006, (0, 0, 1), (0, 0, 0.05), PAINT, 24, 0.0))
FA = -26
d = V((math.sin(math.radians(FA)), -math.cos(math.radians(FA)), 0))
ec = d * 0.0795 + V((0, 0, 0.05))
parts.append(pl.disc("boss", 0.025, 0.006, tuple(d), tuple(ec + d * 0.001), STEEL, 14, 0.4))
parts.append(il.gear("emblem", 0.027, 8, 0.008, 0.008, 0.0085, tuple(ec + d * 0.005), tuple(d), "M_Brass", spin=11))

# long thin spout from the apex, up and out to the left
sd = V((-0.7, -0.1, 0.72)).normalized()
s0 = V((0.0, 0.0, 0.164))
spout = [s0, s0 + sd * 0.06, s0 + sd * 0.125, s0 + sd * 0.165 + V((-0.006, 0.0, -0.012))]
parts.append(pl.sausage("spout", spout, [0.013, 0.009, 0.0072, 0.0066], 8, 3, BRASS, (False, True), 2, True, 50))
parts.append(pl.band("spout_ring", 0.0185, 0.014, 0.008, tuple(sd), tuple(s0 + sd * 0.008), BRASS, 12, 0.3))
tip = spout[-1]
drop_c = tip + V((-0.002, 0, -0.03))
parts.append(il.lathe("drop", [(0.0, -0.018), (0.009, -0.016), (0.014, -0.008), (0.014, 0.0), (0.01, 0.01),
                               (0.005, 0.02), (0.002, 0.026), (0.0, 0.03)], loc=tuple(drop_c), segs=12, m=OIL,
                      smooth=60))
parts.append(rw.sphere("drop_hi", 0.0042, 8, 4, tuple(drop_c + V((0.004, -0.011, -0.002))), mat=pk.mat("Shine")))

# loop handle on the right (+X) with a steel thumb-pump lever above it
hb = [V((0.074, 0.0, 0.074)), V((0.108, 0.0, 0.086)), V((0.122, 0.0, 0.056)), V((0.106, 0.0, 0.026)),
      V((0.074, 0.0, 0.03))]
parts.append(pl.sausage("handle", hb, 0.0115, 8, 3, BRASS, (True, True), 2, True, 50, (1.0, 0.72), (0, 1, 0)))
parts.append(pl.obox("pump_lever", (0.05, 0.018, 0.008), V((0.062, 0.0, 0.112)), (1, 0, -0.55), (0.55, 0, 1), STEEL,
                     rounded=0.003, segments=1))
parts.append(pl.rod("pump_pin", V((0.044, -0.012, 0.12)), V((0.044, 0.012, 0.12)), 0.0045, 6, STEEL))

oil = rw.join(parts, "WeaponOil")
pk.fit(oil, 0.28)  # largest dimension, as in the brief
il.finish_item(ASSET, (0.28,))
