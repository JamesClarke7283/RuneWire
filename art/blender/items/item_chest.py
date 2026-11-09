"""item_chest: wooden treasure chest, 1.0 (X) x 0.7 (Y) x 0.8 (Z) m. The lock side faces -Y.

Nodes (origin of the model = the ground centre, an intentional exception for containers):
  Chest   static body: a hollow planked box (M_WoodPlanks boards between M_WoodDark corner posts, a dark
          plinth and top rim), brass corner caps with nails, vertical brass straps front and back, a big
          brass shield lock plate with a keyhole, ring handles on the sides, two hinge knuckles at the back.
          Inside: a dark red velvet lining ("Velvet") on a raised floor, a heap of gold coins and a ruby.
  Lid     child of Chest, origin ON THE HINGE AXIS (back top edge, axis along X, at y = HINGE_Y,
          z = BODY_H). A domed (barrel-top) lid of four planks between dark D-shaped end caps, with brass
          bands over the arch, a front lip and a hasp that hangs over the lock. Its inside is velvet-lined.
          Open it by rotating about its local X by a NEGATIVE angle (about -100 deg): the front rises and
          swings back over the hinge.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_chest"
rw.reset()

BODY_H = 0.5                  # top of the body = lid seam
WX, WY = 0.46, 0.31           # outer half-extents of the plank walls
OX, OY = 0.475, 0.325         # outer half-extents of posts, plinth and rim
IX, IY = 0.38, 0.23           # inner hollow half-extents
HINGE_Y = 0.33
D = "M_WoodDark"
P = "M_WoodPlanks"
brass = il.mat("M_Brass")
nail = il.mat("Iron")

body = []
# frame: corner posts, plinth, top rim -------------------------------------------------------------------------
for sx in (-1, 1):
    for sy in (-1, 1):
        body.append(pl.obox("post", (0.095, 0.095, BODY_H), (sx * (OX - 0.0475), sy * (OY - 0.0475), BODY_H / 2),
                            rounded=0.014, segments=1, mat=il.mat(D)))
for sy in (-1, 1):
    body.append(pl.obox("plinth", (2 * OX, 0.06, 0.085), (0, sy * (OY - 0.03), 0.0425), rounded=0.012, segments=1,
                        mat=il.mat(D)))
    body.append(pl.obox("rim", (2 * OX, OY - IY, 0.055), (0, sy * (OY + IY) / 2, BODY_H - 0.0275), rounded=0.012,
                        segments=1, mat=il.mat(D)))
for sx in (-1, 1):
    body.append(pl.obox("plinth", (0.06, 2 * OY - 0.12, 0.085), (sx * (OX - 0.03), 0, 0.0425), rounded=0.012,
                        segments=1, mat=il.mat(D)))
    body.append(pl.obox("rim", (OX - IX, 2 * IY, 0.055), (sx * (OX + IX) / 2, 0, BODY_H - 0.0275), rounded=0.012,
                        segments=1, mat=il.mat(D)))
# plank walls: three boards per side between the posts --------------------------------------------------------
Z0, Z1, GAP = 0.085, BODY_H - 0.055, 0.014
bh = (Z1 - Z0 - 2 * GAP) / 3
for i in range(3):
    zc = Z0 + bh / 2 + i * (bh + GAP)
    for sy in (-1, 1):
        body.append(pl.obox("board", (2 * IX + 0.02, 0.05, bh), (0, sy * (WY - 0.025), zc), rounded=0.012, segments=1,
                            mat=il.mat(P)))
    for sx in (-1, 1):
        body.append(pl.obox("board", (0.05, 2 * IY + 0.02, bh), (sx * (WX - 0.025), 0, zc), rounded=0.012, segments=1,
                            mat=il.mat(P)))
# dark backing walls behind the boards (so the gaps read as dark seams) and the velvet hollow
for sy in (-1, 1):
    body.append(rw.box("backing", (2 * IX + 0.04, 0.02, Z1 - Z0), (0, sy * (WY - 0.06), (Z0 + Z1) / 2),
                       mat=il.mat("PouchShadow")))
for sx in (-1, 1):
    body.append(rw.box("backing", (0.02, 2 * IY + 0.04, Z1 - Z0), (sx * (WX - 0.06), 0, (Z0 + Z1) / 2),
                       mat=il.mat("PouchShadow")))
FLOOR = 0.31                 # raised velvet floor so the treasure shows over the front rim
body.append(il.liner("lining", -IX + 0.005, IX - 0.005, -IY + 0.005, IY - 0.005, FLOOR, BODY_H - 0.004, "Velvet"))

# brass: corner caps with nails, straps, lock plate, handles, hinge knuckles ------------------------------------
for sx in (-1, 1):
    for sy in (-1, 1):
        for z in (0.06, BODY_H - 0.06):
            c = V((sx * (OX - 0.055), sy * (OY - 0.055), z))
            body.append(pl.obox("cap", (0.12, 0.12, 0.12), c, rounded=0.02, segments=1, mat=brass))
            body.append(pl.rivet(c + V((0, sy * 0.06, 0)), (0, sy, 0), 0.011, 0.007, nail, 4))
            body.append(pl.rivet(c + V((sx * 0.06, 0, 0)), (sx, 0, 0), 0.011, 0.007, nail, 4))
for sy in (-1, 1):
    for sx in (-1, 1):
        x = sx * 0.25
        body.append(pl.obox("strap", (0.07, 0.016, Z1 - Z0 + 0.01), (x, sy * (WY + 0.006), (Z0 + Z1) / 2), rounded=0.006,
                            segments=1, mat=brass))
        for z in (Z0 + 0.06, Z1 - 0.06):
            body.append(pl.rivet(V((x, sy * (WY + 0.014), z)), (0, sy, 0), 0.01, 0.006, nail, 5))
# lock plate with keyhole
LC = V((0, -WY, 0.345))
body.append(il.wrap_prism("lockplate", il.shield_pts(0.2, 0.22), il.plane_map(LC, (1, 0, 0), (0, 0, 1), -0.002, 0.026),
                          brass, 30))
key_pts = [(0.022 * math.cos(math.radians(a)), 0.03 + 0.022 * math.sin(math.radians(a))) for a in range(-60, 241, 30)]
key_pts += [(-0.016, -0.04), (0.016, -0.04)]
body.append(il.wrap_prism("keyhole", key_pts, il.plane_map(LC, (1, 0, 0), (0, 0, 1), 0.023, 0.006), "PouchShadow"))
for (x, z) in ((-0.075, 0.08), (0.075, 0.08), (0, -0.085)):
    body.append(pl.rivet(LC + V((x, -0.024, z)), (0, -1, 0), 0.012, 0.007, brass, 6))
# side ring handles
for sx in (-1, 1):
    body.append(pl.obox("handle_mount", (0.026, 0.13, 0.06), (sx * (WX + 0.01), 0, 0.37), rounded=0.008, segments=1,
                        mat=brass))
    ring = rw.torus("handle", 0.058, 0.0135, 12, 5, (0, 0, 0), (0, 90, 0), il.mat("Iron"))
    ring.location = (sx * (WX + 0.018), 0, 0.31)
    body.append(ring)
# hinge knuckles at the back (on the hinge axis)
for sx in (-1, 1):
    body.append(rw.cylinder("hinge", 0.022, 0.1, 10, (sx * 0.25, HINGE_Y, BODY_H), (0, 90, 0), brass))

# treasure inside ------------------------------------------------------------------------------------------------
body += il.coin_pile((0.02, 0.02, FLOOR), 0.28, 0.17, 0.16, 9, 4, coin_r=0.05)
body.append(rw.ico("gem", 0.042, 1, (-0.13, -0.05, FLOOR + 0.1), (20, 10, 0), (1, 1, 1.3), il.mat("HeartRed"), None, 0))

chest = rw.join(body, "Chest", origin=(0, 0, 0))
rw.smooth(chest, 35)

# lid ------------------------------------------------------------------------------------------------------------
RY, RZ, LX = OY, 0.3, 0.44            # dome half-depth, height, plank half-length
lid = []
gap = 0.035
for k in range(4):
    t0 = math.pi * k / 4 + (gap / 2 if k else 0.0)
    t1 = math.pi * (k + 1) / 4 - (gap / 2 if k < 3 else 0.0)
    lid.append(il.arch_slab("plank", -LX, LX, RY, RZ, 0.0, BODY_H, t0, t1, 0.045, 3, P))
lid.append(il.arch_slab("lid_lining", -LX, LX, RY, RZ, 0.0, BODY_H, 0.0, math.pi, 0.012, 10, "Velvet", out=-0.04))
for sx in (-1, 1):
    lid.append(il.d_cap("endcap", min(sx * LX, sx * 0.49), max(sx * LX, sx * 0.49), RY, RZ, 0.0, BODY_H, 12, D))
    # brass bands: one over each end cap edge and one over the planks in line with the body straps
    x0, x1 = sorted((sx * 0.455, sx * 0.495))
    lid.append(il.arch_slab("band", x0, x1, RY, RZ, 0.0, BODY_H, 0.0, math.pi, 0.03, 12, "M_Brass", out=0.012))
    lid.append(il.arch_slab("band", sx * 0.25 - 0.035, sx * 0.25 + 0.035, RY, RZ, 0.0, BODY_H, 0.0, math.pi, 0.03, 12,
                            "M_Brass", out=0.012))
    for t in (math.pi * 0.2, math.pi * 0.5, math.pi * 0.8):
        y, z = il.arch_pt(t, RY + 0.012, RZ + 0.012, 0.0, BODY_H)
        n = V((0, -math.cos(t) / RY, math.sin(t) / RZ)).normalized()
        lid.append(pl.rivet(V((sx * 0.25, y, z)), n, 0.011, 0.007, nail, 5))
# front lip and the hasp over the lock
lid.append(pl.obox("lip", (2 * LX, 0.03, 0.035), (0, -RY - 0.006, BODY_H + 0.02), rounded=0.008, segments=1, mat=brass))
HC = V((0, -RY - 0.004, BODY_H - 0.005))
lid.append(il.wrap_prism("hasp", il.capsule_pts(0.075, 0.13), il.plane_map(HC, (1, 0, 0), (0, 0, 1), 0.0, 0.022), brass,
                         30))
lid.append(pl.rivet(HC + V((0, -0.022, 0.03)), (0, -1, 0), 0.012, 0.007, brass, 6))

lid_o = rw.join(lid, "Lid", origin=(0, HINGE_Y, BODY_H))
rw.smooth(lid_o, 35)
pl.parent_keep(lid_o, chest)

il.finish_container(ASSET, chest, lid_o, -100.0, (1.0, 0.7, 0.8))
