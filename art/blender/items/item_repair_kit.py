"""item_repair_kit: "Tinker's Patch Kit", a stuffed leather tool pouch, about 0.3 x 0.17 x 0.33 m.

A chunky rounded leather pouch (M_Leather) with a stitched seam welt, a side strap with a brass buckle, a
lighter front pocket under a flap with a brass snap, a dark-navy cloth patch stitched on the pocket carrying a
glowing teal rune (rw.glow), a brass maker's plate on the back, and tools
poking out of its dark opening: a steel open-ended wrench, a brass oil can with a long spout and a red-
handled screwdriver. One mesh object "RepairKit", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_repair_kit"
rw.reset()

W, D, H = 0.27, 0.14, 0.2
parts = [pl.superellipsoid("pouch", (W, D, H), (0, 0, H / 2), 0.3, 0.45, 18, 10, il.mat("M_Leather"))]
# seam welt around the sides and bottom (where the front and back panels meet)
seam = []
for i in range(15):
    ph = math.radians(80 - 340 * i / 14)          # from top-right, down round the bottom, up to top-left
    c, s_ = math.cos(ph), math.sin(ph)
    x = W / 2 * math.copysign(abs(c) ** 0.45, c)
    z = H / 2 + H / 2 * math.copysign(abs(s_) ** 0.45, s_)
    seam.append(V((x * 1.005, 0.0, z)))
seam = [p for p in seam if p.z > 0.012 or abs(p.x) < 0.11]
parts.append(pl.sausage("seam", seam, 0.0085, 6, 2, il.mat("M_Leather__5b3520"), (True, True), 1, True, 60))
# dark opening on top for the tools
parts.append(il.wrap_prism("opening", il.ellipse_pts(0.2, 0.085, 18, 2.6), il.plane_map((0, 0.004, H - 0.004), (1, 0, 0),
                                                                                      (0, 1, 0), -0.004, 0.006),
                           "PouchShadow"))

# front pocket, flap with a brass snap
parts.append(pl.superellipsoid("pocket", (0.19, 0.05, 0.11), (0, -0.06, 0.075), 0.3, 0.4, 12, 7,
                               il.mat("M_Leather__b07644")))
parts.append(pl.superellipsoid("flap", (0.205, 0.034, 0.05), (0, -0.074, 0.128), 0.3, 0.5, 12, 6,
                               il.mat("M_Leather")))
parts.append(pl.rivet(V((0, -0.091, 0.118)), (0, -1, 0), 0.012, 0.008, il.mat("M_Brass"), 10))

# rune patch on the pocket
PC = V((0, -0.0855, 0.064))
parts.append(il.wrap_slab("patch", il.plane_map(PC, (1, 0, 0), (0, 0, 1), -0.002, 0.006), 0.1, 0.072, 4, 3,
                          "PatchCloth", 6.0, 0.0015, 5))
for k in range(10):                               # chunky stitch dashes round the patch
    a = 2 * math.pi * (k + 0.5) / 10
    p = PC + V((math.cos(a) * 0.043, -0.0045, math.sin(a) * 0.03))
    t = V((-math.sin(a) * 0.043, 0, math.cos(a) * 0.03)).normalized()
    parts.append(pl.obox("stitch", (0.011, 0.004, 0.004), p, t, (0, -1, 0), il.mat("Thread")))
parts += pl.glyph("tiwaz", PC + V((0, -0.0045, -0.002)), (1, 0, 0), (0, 0, 1), 0.05, 0.011, 0.006,
                  il.mat("TealGlow"), "rune")

# side strap with a brass buckle (-X side)
strap = []
for i in range(9):
    z = 0.012 + (H - 0.012) * i / 8
    t = abs(z - H / 2) / (H / 2)
    x = W / 2 * (1 - min(t, 0.999) ** (1 / 0.45)) ** (0.45 / 2) if t < 1 else 0.0
    strap.append(V((-(x + 0.004), 0.0, z)))
parts.append(pl.sausage("strap", strap, 0.017, 6, 1, il.mat("M_Leather__5b3520"), (False, False), 1, True, 40,
                        (0.28, 1.0), (1, 0, 0)))
bk = rw.torus("buckle", 0.021, 0.0055, 12, 4, (0, 0, 0), (0, 90, 0), il.mat("M_Brass"))
pl.xform(bk, il.Matrix.Diagonal((1.0, 1.0, 1.25, 1.0)))
bk.location = (-W / 2 - 0.009, 0.0, H * 0.55)
parts.append(bk)
parts.append(pl.rod("buckle_pin", V((-W / 2 - 0.011, 0, H * 0.55 - 0.024)), V((-W / 2 - 0.011, 0, H * 0.55 + 0.012)),
                    0.0045, 6, il.mat("M_Brass")))

# brass maker's plate with a gear emblem on the back
BC = V((0, D / 2 - 0.003, 0.105))
parts.append(il.wrap_slab("plate", il.plane_map(BC, (-1, 0, 0), (0, 0, 1), -0.002, 0.007), 0.13, 0.07, 3, 2,
                          "M_Brass", 6.0))
parts.append(il.gear("emblem", 0.024, 8, 0.007, 0.008, 0.009, tuple(BC + V((0, 0.005, 0))), (0, 1, 0), "M_Brass"))
for sx in (-1, 1):
    parts.append(pl.rivet(BC + V((sx * 0.052, 0.005, 0)), (0, 1, 0), 0.007, 0.005, il.mat("M_Brass"), 6))

# tools ----------------------------------------------------------------------------------------------------------
# wrench (steel), leaning left out of the opening, jaw up
d = V((-0.42, -0.06, 1)).normalized()
u = d.cross(V((0, -1, 0))).normalized()
hb = V((-0.035, 0.0, 0.1))
ht = hb + d * 0.17
parts.append(pl.beam_between("wrench", hb, ht, (0.026, 0.016), il.mat("M_Steel"), rounded=0.006, up=(0, -1, 0)))
head_c = ht + d * 0.02
parts.append(il.wrap_prism("wrench_head", il.wrench_head_pts(0.033, 0.024, 0.026), il.plane_map(head_c, -u, d, -0.009,
                                                                                               0.018), "M_Steel"))
# brass oil can, leaning right, spout reaching out
ax = V((0.3, 0.0, 1)).normalized()
base = V((0.05, -0.006, 0.135))
can = [(0.0, 0.0), (0.042, 0.0), (0.045, 0.006), (0.045, 0.072), (0.04, 0.083), (0.019, 0.1), (0.014, 0.112),
       (0.0, 0.112)]
parts.append(il.lathe("can", can, tuple(ax), tuple(base), 14, "M_Brass", 40))
parts.append(pl.band("can_band", 0.048, 0.012, 0.008, tuple(ax), tuple(base + ax * 0.06), il.mat("M_Copper"), 14, 0.0))
top = base + ax * 0.108
side = V((1, -0.35, 0.25)).normalized()
spout = [top - ax * 0.01, top + ax * 0.03 + side * 0.006, top + ax * 0.05 + side * 0.04, top + ax * 0.058 + side * 0.075]
parts.append(pl.sausage("spout", spout, [0.0105, 0.0095, 0.0085, 0.0078], 6, 2, il.mat("M_Brass"), (False, True), 1,
                        True, 60))
# screwdriver at the back, red handle up
sd = V((-0.08, 0.25, 1)).normalized()
sb = V((0.0, 0.03, 0.17))
parts.append(il.lathe("sd_handle", [(0.0, 0.0), (0.014, 0.0), (0.018, 0.012), (0.018, 0.07), (0.016, 0.082),
                                    (0.01, 0.088), (0.0, 0.088)], tuple(sd), tuple(sb), 10, "HandleRed", 40))
parts.append(pl.rod("sd_shaft", sb - sd * 0.06, sb, 0.0075, 8, il.mat("M_Steel")))

kit = rw.join(parts, "RepairKit")
il.finish_item(ASSET, (0.3, 0.17, 0.33))
