"""bld_watchtower: the old watchtower west of the lake (5 x 5 x ~16 m).

A battered stone base with quoins, arrow slits, crenellations and an arched door; an open timber frame with
X-bracing and a ladder up its front to a railed lookout platform (alarm bell, telescope, lantern) under a bell-cast
pyramid roof. On the roof peak sits a brass beacon cage holding a big teal ley crystal centred exactly at 15 m above
the origin, where the game adds its teal OmniLight once the cargo quest is done.
Origin at the ground centre, front (door) facing -Y.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_watchtower"
B.reset()
P = []
L = B.Lights()

BEACON_Z = 15.0               # the game's OmniLight: Vector3(0, 15, 0) in the tower's local frame

# ---------------------------------------------------------------- stone base (battered square, chamfered corners)
ZS = 5.6                      # top of the stone base


def sq_ring(h, z, ch=0.22):
    """Square ring of half-size h with chamfered corners (8 points, CCW from +X)."""
    ring = [(h, -(h - ch)), (h, h - ch), (h - ch, h), (-(h - ch), h), (-h, h - ch), (-h, -(h - ch)), (-(h - ch), -h), (h - ch, -h)]
    return [(x, y, z) for (x, y) in ring]


def base_h(z):
    return 2.15 - 0.3 * max(0.0, min(1.0, (z - 0.4) / (ZS - 0.4)))


P.append(B.loft("plinth", [sq_ring(2.3, -0.25, 0.25), sq_ring(2.3, 0.45, 0.25), sq_ring(2.2, 0.6, 0.22)], "M_StoneRough", smooth=None))
P.append(B.loft("base", [sq_ring(base_h(z), z) for z in (0.5, 2.0, 4.0, ZS - 0.4)], "M_Stone", smooth=None))
P.append(B.loft("cornice", [sq_ring(base_h(ZS - 0.4) - 0.02, ZS - 0.45), sq_ring(2.02, ZS - 0.25), sq_ring(2.05, ZS), sq_ring(1.95, ZS + 0.02)],
                "M_StoneRough", smooth=None))
for o in P[-3:]:
    rw.add_bevel(o, 0.04, 1, 40, harden=False)
# quoins on the four corners
for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    for k in range(6):
        z = 0.95 + k * 0.82
        h = base_h(z)
        long_x = k % 2 == 0
        size = (0.62, 0.42, 0.34) if long_x else (0.42, 0.62, 0.34)
        c = (sx * (h - (0.2 if long_x else 0.12)), sy * (h - (0.12 if long_x else 0.2)), z)
        P.append(E.stone("quoin", size, c, (0, 0, 0), "M_StoneRough", 0.045, seed=k + sx * 3 + sy * 7, jitter=2.5))
# crenellations on the stone top
for (sx, sy, horiz) in ((0, -1, True), (0, 1, True), (-1, 0, False), (1, 0, False)):
    for a in (-0.85, 0.85):
        loc = (a, sy * 1.86, ZS + 0.32) if horiz else (sx * 1.86, a, ZS + 0.32)
        size = (0.62, 0.3, 0.6) if horiz else (0.3, 0.62, 0.6)
        P.append(E.stone("merlon", size, loc, (0, 0, 0), "M_StoneRough", 0.04, seed=int(a * 10) + sx + 3 * sy, jitter=2))
# arrow slits with a faint glow
for (face, a, z) in (("L", 0.6, 2.5), ("L", -0.7, 4.3), ("R", -0.4, 2.7), ("R", 0.7, 4.4), ("B", 0.5, 2.6), ("B", -0.6, 4.4), ("F", -1.05, 4.2)):
    h = base_h(z)
    if face == "F":
        pos, rot = (a, -h, z), (0, 0, 0)
    elif face == "B":
        pos, rot = (a, h, z), (0, 0, 180)
    elif face == "L":
        pos, rot = (-h, a, z), (0, 0, -90)
    else:
        pos, rot = (h, a, z), (0, 0, 90)
    slit = [rw.box("slit", (0.14, 0.06, 0.82), (0, -0.01, 0), mat=E.mat("WindowGlow")),
            E.rbox("slitframe", (0.42, 0.12, 0.14), (0, -0.04, 0.48), m="M_StoneRough", r=0.03),
            E.rbox("slitframe", (0.36, 0.12, 0.12), (0, -0.04, -0.47), m="M_StoneRough", r=0.03)]
    E.place(slit, pos, rot)
    P += slit
# door, steps, lantern
DH = base_h(1.2)
dr = E.door(1.15, 2.2, arch=True, m="M_WoodPlanks", frame="M_StoneRough", planks=4, frame_w=0.2)
E.place(dr, (0, -DH + 0.02, 0.5))
P += dr
P.append(E.rbox("step", (1.7, 0.36, 0.3), (0, -2.4, 0.1), m="M_StoneRough", r=0.05))
lp, lc = E.lantern((0.95, -DH - 0.33, 2.55), "wall", wall_normal=(0, -1, 0))
P += lp
L.add(lc)
# moss on the stones
for k, (x, y, z) in enumerate(((-2.0, -1.3, 0.6), (1.9, 1.6, 0.6), (-1.5, 2.1, 0.55), (2.1, -0.9, 3.0))):
    P += E.moss((x, y, z), 0.3, seed=k, n=3)

# ---------------------------------------------------------------- timber frame
ZD = 10.0                       # platform deck top
PB, PT = 1.6, 1.42              # post half-spacing at the bottom / top


def post_pt(sx, sy, z):
    t = (z - ZS) / (ZD - ZS)
    h = PB + (PT - PB) * t
    return V((sx * h, sy * h, z))


CORNERS = ((1, 1), (1, -1), (-1, -1), (-1, 1))
for (sx, sy) in CORNERS:
    P.append(E.beam("post", tuple(post_pt(sx, sy, ZS - 0.1)), tuple(post_pt(sx, sy, ZD - 0.12)), 0.32, 0.32, "M_WoodDark", 0.04))
    P.append(E.rbox("postfoot", (0.48, 0.48, 0.18), tuple(post_pt(sx, sy, ZS + 0.08)), m="IronDark", r=0.03))
GIRTS = (ZS + 0.3, 8.55, ZD - 0.32)
for i in range(4):
    (ax, ay), (bx, by) = CORNERS[i], CORNERS[(i + 1) % 4]
    for z in GIRTS:
        P.append(E.beam("girt", tuple(post_pt(ax, ay, z)), tuple(post_pt(bx, by, z)), 0.22, 0.2, "M_WoodDark", 0.035))
    for (z0, z1) in ((GIRTS[0], GIRTS[1]), (GIRTS[1], GIRTS[2])):
        P.append(E.beam("brace", tuple(post_pt(ax, ay, z0 + 0.1)), tuple(post_pt(bx, by, z1 - 0.1)), 0.16, 0.13, "M_WoodDark", 0.03))
        P.append(E.beam("brace", tuple(post_pt(bx, by, z0 + 0.1)), tuple(post_pt(ax, ay, z1 - 0.1)), 0.16, 0.13, "M_WoodDark", 0.03))
    # iron plates where the braces cross
    mid = (post_pt(ax, ay, 0) + post_pt(bx, by, 0)) / 2
    out = V((ax + bx, ay + by, 0)).normalized()
    for z in ((GIRTS[0] + GIRTS[1]) / 2, (GIRTS[1] + GIRTS[2]) / 2):
        P.append(E.disc("xplate", 0.13, 0.05, tuple(V((mid.x, mid.y, z)) + out * 0.1), tuple(out), 8, "IronDark"))
# the ladder: from the stone terrace up the front of the frame to a gap in the railing
P += B.ladder((0.62, -1.88, ZS + 0.02), (0.62, -1.5, ZD + 0.02), w=0.66, step=0.34, rail_w=0.11, rung_r=0.035, m="M_WoodPlanks",
              rung_m="M_WoodPlanks")
# and a second ladder leaning on the stone base, up to a crenel on the left
P += B.ladder((-2.42, 0.0, -0.05), (-1.98, 0.0, ZS + 0.55), w=0.62, step=0.34, rail_w=0.11, rung_r=0.035, m="M_WoodPlanks",
              rung_m="M_WoodPlanks", side=(0, 1, 0))

# ---------------------------------------------------------------- lookout platform
P.append(E.rbox("deck", (4.66, 4.66, 0.2), (0, 0, ZD - 0.1), m="M_WoodPlanks", r=0.04))
for (sx, sy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    if sx:
        P.append(E.rbox("rim", (0.2, 4.8, 0.3), (sx * 2.33, 0, ZD - 0.2), m="M_WoodDark", r=0.04))
    else:
        P.append(E.rbox("rim", (4.8, 0.2, 0.3), (0, sy * 2.33, ZD - 0.2), m="M_WoodDark", r=0.04))
for (sx, sy) in CORNERS:
    p0 = post_pt(sx, sy, ZD - 1.35)
    for (ex, ey) in ((sx * 2.3, sy * PT), (sx * PT, sy * 2.3)):
        P.append(E.beam("knee", tuple(p0), (ex * 0.97, ey, ZD - 0.28) if abs(ex) > abs(ey) else (ex, ey * 0.97, ZD - 0.28), 0.16, 0.16,
                        "M_WoodDark", 0.03))
# railing with a gap where the ladder arrives
RH = 1.0
RP = 2.2
rail_posts = []
for k in range(-2, 3):
    a = k * RP / 2
    rail_posts += [(a, -RP), (a, RP), (-RP, a), (RP, a)]
rail_posts = sorted(set(rail_posts))
for (x, y) in rail_posts:
    P.append(E.rbox("rpost", (0.13, 0.13, RH), (x, y, ZD + RH / 2), m="M_WoodDark", r=0.025))
for (p0, p1) in (((-RP, -RP), (RP, -RP)), ((RP, -RP), (RP, RP)), ((RP, RP), (-RP, RP)), ((-RP, RP), (-RP, -RP))):
    for (z, w) in ((ZD + RH, 0.14), (ZD + 0.5, 0.09)):
        P.append(E.beam("rail", (p0[0], p0[1], z), (p1[0], p1[1], z), w, w, "M_WoodDark", 0.02, extend=0.05))
# the hatch where the ladder comes up, with its lid propped open
P.append(rw.box("hatch", (0.72, 0.62, 0.03), (0.62, -1.55, ZD + 0.005), mat=E.mat("Interior")))
P.append(E.rbox("hatchlid", (0.74, 0.06, 0.64), (0.62, -1.2, ZD + 0.3), (-12, 0, 0), m="M_WoodPlanks", r=0.015))
for zz in (0.12, 0.48):
    P.append(rw.box("hatchstrap", (0.62, 0.02, 0.06), (0.62, -1.24 + zz * 0.2, ZD + zz), (-12, 0, 0), mat=E.mat("Iron")))
# roof posts, beams, bell, telescope, lantern
ZE = ZD + 2.2
for (sx, sy) in CORNERS:
    P.append(E.rbox("rpostbig", (0.22, 0.22, ZE - ZD + 0.1), (sx * RP, sy * RP, (ZD + ZE) / 2), m="M_WoodDark", r=0.035))
    P.append(E.beam("rbrace", (sx * RP, sy * RP, ZE - 0.6), (sx * RP * 0.55, sy * RP, ZE - 0.08), 0.12, 0.12, "M_WoodDark", 0.025))
    P.append(E.beam("rbrace", (sx * RP, sy * RP, ZE - 0.6), (sx * RP, sy * RP * 0.55, ZE - 0.08), 0.12, 0.12, "M_WoodDark", 0.025))
for sy in (-1, 1):
    P.append(E.rbox("plate", (2 * RP + 0.3, 0.22, 0.24), (0, sy * RP, ZE), m="M_WoodDark", r=0.035))
for sx in (-1, 1):
    P.append(E.rbox("plate", (0.22, 2 * RP + 0.3, 0.24), (sx * RP, 0, ZE), m="M_WoodDark", r=0.035))
P.append(E.rbox("crossbeam", (2 * RP, 0.2, 0.22), (0, 0, ZE - 0.05), m="M_WoodDark", r=0.035))
P.append(E.lathe("bell", [(0.0, 0.0), (0.3, 0.0), (0.32, 0.05), (0.27, 0.15), (0.22, 0.4), (0.16, 0.55), (0.06, 0.6), (0.0, 0.6)], 14,
                 loc=(0, 0, ZE - 0.95), m="M_Brass", smooth=50))
P.append(E.ring("bellyoke", 0.08, 0.03, (0, 0, ZE - 0.3), (1, 0, 0), "IronDark", 10, 5))
P.append(E.ball("clapper", 0.07, (0, 0, ZE - 1.0), "IronDark", 8, 6))
P.append(E.rod("bellrope", (0.05, 0, ZE - 0.95), (0.4, -0.3, ZD + 0.9), 0.02, 5, "Rope"))
# telescope on a tripod at the front-left corner, looking out
tc = V((-1.65, -1.55, ZD + 1.15))
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.4
    P.append(E.rod("tripod", tuple(tc), (tc.x + 0.4 * math.cos(a), tc.y + 0.4 * math.sin(a), ZD + 0.02), 0.025, 5, "M_WoodDark"))
tdir = V((-0.6, -0.75, 0.25)).normalized()
P.append(E.rod("scope", tuple(tc - tdir * 0.35), tuple(tc + tdir * 0.55), 0.07, 10, "M_Brass"))
P.append(E.rod("scopelens", tuple(tc + tdir * 0.5), tuple(tc + tdir * 0.62), 0.095, 10, "M_Brass"))
P.append(E.rod("scopeeye", tuple(tc - tdir * 0.45), tuple(tc - tdir * 0.33), 0.045, 8, "IronDark"))
P.append(E.disc("scopeglass", 0.08, 0.02, tuple(tc + tdir * 0.63), tuple(tdir), 10, "TealGlowSoft"))
lp2, lc2 = E.lantern((RP - 0.05, RP - 0.05, ZE - 0.12), "hang", scale=1.1)
P += lp2
L.add(lc2)

# ---------------------------------------------------------------- bell-cast pyramid roof
RHW = 2.42                      # eave half-width
RZ_TOP = 14.2
roof = E.cone_roof(RHW * math.sqrt(2), RZ_TOP - ZE, ZE + 0.05, t=0.2, flare=0.45, seg=4, m="M_RoofTiles", lip=0.18)
E.place([roof], (0, 0, 0), (0, 0, 45))
rw.smooth(roof, 25)
P.append(roof)


def roof_pt(sx, sy, t):
    """Point on a hip line (t = 0 at the eave corner, 1 at the apex), following the bell-cast profile."""
    rr = RHW * (1 - t) ** 1.45
    return V((sx * rr, sy * rr, ZE + 0.05 + (RZ_TOP - ZE) * t + 0.12))


for (sx, sy) in CORNERS:
    P.append(E.tube("hip", [tuple(roof_pt(sx, sy, t)) for t in (0.0, 0.08, 0.2, 0.38, 0.6, 0.82, 0.97)], 0.075, "M_WoodDark", 1,
                    smooth=True, ures=2))

# ---------------------------------------------------------------- clutter tucked into the chamfered corners
P += E.barrel(0.28, 0.78, (-2.2, -2.2, 0.0), 0)
P += E.crate((0.58, 0.58, 0.58), (2.15, 2.15, 0.0), 45)

E.tri_breakdown(P, 24)
main = E.join(P, "Watchtower")
W = E.wonk(main, 16.0, lean=(0.06, 0.04), twist=1.5, bulge=0.004)

# ---------------------------------------------------------------- beacon cage with the ley crystal
# (built after the wonk and joined in, so the crystal is centred exactly on (0, 0, BEACON_Z))
BP = []
BP.append(E.lathe("pedestal", [(0.66, RZ_TOP - 0.75), (0.5, RZ_TOP - 0.25), (0.53, RZ_TOP - 0.05), (0.42, RZ_TOP + 0.08),
                              (0.46, RZ_TOP + 0.16), (0.0, RZ_TOP + 0.16)], 12, m="M_Brass", smooth=40))
CB0, CB1 = RZ_TOP + 0.16, BEACON_Z + 0.82
for k in range(4):
    a = 2 * math.pi * k / 4 + math.pi / 4
    p = V((0.5 * math.cos(a), 0.5 * math.sin(a), 0))
    q = V((0.36 * math.cos(a), 0.36 * math.sin(a), 0))
    BP.append(E.tube("cagebar", [tuple(p + V((0, 0, CB0))), tuple(p * 1.3 + V((0, 0, BEACON_Z))), tuple(q + V((0, 0, CB1)))], 0.045,
                    "M_Brass", 1, smooth=True, ures=3))
for (z, r, t) in ((CB0 + 0.04, 0.5, 0.06), (BEACON_Z + 0.02, 0.65, 0.045), (CB1, 0.37, 0.05)):
    BP.append(E.ring("cagering", r, t, (0, 0, z), (0, 0, 1), "M_Brass", 18, 5))
BP.append(B.crystal("leycrystal", (0, 0, BEACON_Z), 0.33, 1.3, (0, 0), "M_Crystal", 6, 10))
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.5
    BP.append(B.crystal("leysmall", (0.24 * math.cos(a), 0.24 * math.sin(a), BEACON_Z - 0.3), 0.13, 0.55,
                       (-math.sin(a) * 24, math.cos(a) * 24), "M_Crystal", 5, 0))
BP.append(E.ring("leyglow", 0.36, 0.035, (0, 0, CB0 + 0.14), (0, 0, 1), "TealGlow", 16, 4))
BP.append(rw.cone("cagecap", 0.5, 0.05, 0.34, 12, (0, 0, CB1 + 0.17), (0, 0, 0), E.mat("M_Copper")))
BP.append(E.ball("capknob", 0.08, (0, 0, CB1 + 0.38), "M_Brass", 8, 6))
BP.append(E.rod("capspike", (0, 0, CB1 + 0.42), (0, 0, CB1 + 0.72), 0.03, 6, "M_Brass"))
BP.append(B.star_prism("capstar", 0.13, 0.055, 0.04, (0, 0, CB1 + 0.62), (0, -1, 0), "StarGold", 4))

main = E.join([main] + BP, "Watchtower")
rw.smooth(main, 35)

# ---------------------------------------------------------------- empties
L.emit(W)
rw.empty("Beacon", (0, 0, BEACON_Z))

# ---------------------------------------------------------------- collision
E.col_frustum("Base", 2.3, 1.95, ZS + 0.3, (0, 0, (ZS - 0.3) / 2), square=True)
for (sx, sy) in CORNERS:
    E.col_beam("Post", tuple(W(post_pt(sx, sy, ZS))), tuple(W(post_pt(sx, sy, ZD - 0.1))), 0.34, 0.34)
E.col_box("Deck", (4.8, 4.8, 0.3), tuple(W(V((0, 0, ZD - 0.15)))))
E.col_hull("Roof", [tuple(W(V((sx * RHW, sy * RHW, ZE - 0.05)))) for (sx, sy) in CORNERS] +
           [tuple(W(V((sx * RHW, sy * RHW, ZE + 0.25)))) for (sx, sy) in CORNERS] + [tuple(W(V((0, 0, RZ_TOP + 0.2))))])
E.col_cyl("Beacon", 0.66, CB1 - CB0 + 0.5, (0, 0, (CB0 + CB1) / 2 + 0.2), verts=10)
E.col_cyl("Barrel", 0.3, 0.8, (-2.2, -2.2, 0.4))

E.check(ASSET, (5, 5, 16), 25000)
rw.finish(ASSET, "env", previews=E.previews())
