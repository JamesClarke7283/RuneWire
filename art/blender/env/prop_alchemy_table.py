"""prop_alchemy_table: "Alchemist's Table", a crafting station for the town plaza, about 2.0 x 1.0 x 1.8 m.
Origin at the ground centre; the working side faces -Y.

A sturdy wooden table (plank top at 0.9 m on chunky turned legs, aprons, stretchers and a lower shelf with a
clay pot, a couple of jars and a stack of books). On the left stands a glass still: a little brass tripod
brazier with glowing coals (M_EmberGlow) heats a big round-bottomed flask of glowing green liquid (rw.glow
inside M_Glass) held in a brass ring stand. A copper alembic head on the flask's neck feeds a copper tube
that winds down through a coiled copper condenser on a brass stand and drips into a second round flask of
glowing purple liquid, sitting on a twine ring. On the right are a stone mortar and pestle with herbs, an
open spell book on a closed tome, two parchment scrolls, a quill in an ink pot and two little potion bottles.
At the back right, a small wooden drying rack hangs bundles of green herbs, sage, lavender and red berries
on twine.

Nodes: AlchemyTable (all static geometry) and the empty LightPoint (at the brazier).
Collision (-colonly boxes): Col_Table_0 (table body), Col_Still_0 (the glassware above the table) and
Col_Rack_0 (the drying rack).
"""
import math
import os
import random
import sys

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stationlib as S  # noqa: E402

E, rw, pl, V, M = S.E, S.rw, S.pl, S.V, S.M
ASSET = "prop_alchemy_table"
S.reset()
rnd = random.Random(3)
S.preview_glow("M_EmberGlow", "c8661c", "ff8a2a", 1.6)   # preview renders only
P = []
TOP = 0.9                   # table top surface
TX, TY0, TY1 = 0.98, -0.46, 0.44
TYC = (TY0 + TY1) / 2
TD = TY1 - TY0

# --- table -------------------------------------------------------------------------------------------------------
n_pl, gap = 3, 0.014
pw = (TD - gap * (n_pl - 1)) / n_pl
for i in range(n_pl):
    y = TY0 + pw / 2 + i * (pw + gap)
    P.append(E.cbox("topplank", (2 * TX, pw, 0.08), (0, y, TOP - 0.04), (0, 0, 0), "M_WoodPlanks", 0.018))
P.append(rw.box("topcore", (2 * TX - 0.06, TD - 0.06, 0.04), (0, TYC, TOP - 0.06), mat=M("Soot")))
LEG = [(0.055, 0.0), (0.07, 0.03), (0.06, 0.1), (0.05, 0.3), (0.075, 0.42), (0.05, 0.55), (0.062, TOP - 0.2),
       (0.072, TOP - 0.08), (0.0, TOP - 0.08)]
for sx in (-1, 1):
    for y in (TY0 + 0.1, TY1 - 0.1):
        P.append(S.lathe("leg", [(0.0, 0.0)] + LEG, 8, (sx * (TX - 0.11), y, 0), "M_WoodDark", 50))
    P.append(E.cbox("apron", (0.05, TD - 0.26, 0.13), (sx * (TX - 0.11), TYC, TOP - 0.15), (0, 0, 0), "M_WoodDark", 0.015))
    P.append(E.cbox("stretch", (0.06, TD - 0.24, 0.06), (sx * (TX - 0.11), TYC, 0.2), (0, 0, 0), "M_WoodDark", 0.015))
for y in (TY0 + 0.1, TY1 - 0.1):
    P.append(E.cbox("apron", (2 * TX - 0.3, 0.05, 0.13), (0, y, TOP - 0.15), (0, 0, 0), "M_WoodDark", 0.015))
P.append(E.cbox("shelf", (2 * TX - 0.28, TD - 0.26, 0.045), (0, TYC, 0.24), (0, 0, 0), "M_WoodPlanks", 0.012))
SH = 0.2625                 # lower shelf top
# lower shelf: clay pot with a cork, jars, a stack of books
P.append(S.lathe("pot", [(0.0, 0.0), (0.1, 0.0), (0.16, 0.06), (0.17, 0.14), (0.12, 0.24), (0.07, 0.27), (0.08, 0.3),
                         (0.065, 0.31), (0.0, 0.31)], 12, (-0.55, TYC, SH), "Clay", 50))
P.append(S.lathe("potcork", [(0.0, 0.29), (0.055, 0.29), (0.06, 0.34), (0.0, 0.35)], 8, (-0.55, TYC, SH), "EndGrain",
                 40))
for k, (x, h, m) in enumerate(((-0.2, 0.18, "BottleGreen"), (-0.08, 0.13, "BottleBlue"))):
    P.append(S.lathe("jar", [(0.0, 0.0), (0.05, 0.0), (0.055, 0.02), (0.055, h - 0.03), (0.035, h - 0.01), (0.035, h),
                             (0.0, h)], 8, (x, TYC + 0.05, SH), m, 40))
    P.append(S.lathe("jarcap", [(0.0, h - 0.005), (0.04, h - 0.005), (0.04, h + 0.025), (0.0, h + 0.025)], 8,
                     (x, TYC + 0.05, SH), "M_Brass", 40))
for k, (dz, rz, m) in enumerate(((0.0, 6, "BookTeal"), (0.07, -9, "BookRed"))):
    P.append(E.cbox("shelfbook", (0.32, 0.24, 0.065), (0.45, TYC, SH + 0.034 + dz), (0, 0, rz), m, 0.012))
    P.append(E.cbox("shelfpages", (0.3, 0.215, 0.05), (0.457, TYC, SH + 0.034 + dz), (0, 0, rz), "Parchment", 0.006))

# --- brazier (left), its coals and a flame ----------------------------------------------------------------------
BRX, BRY = -0.6, -0.04
P.append(S.lathe("brazier", [(0.0, 0.0), (0.06, 0.0), (0.12, 0.05), (0.14, 0.1), (0.15, 0.11), (0.135, 0.115),
                             (0.115, 0.08), (0.0, 0.08)], 12, (BRX, BRY, TOP + 0.06), "M_Brass", 40))
for k in range(3):
    a = math.radians(90 + 120 * k)
    d = V((math.cos(a), math.sin(a), 0.0))
    P.append(E.rod("brazier_leg", tuple(V((BRX, BRY, TOP)) + d * 0.13), tuple(V((BRX, BRY, TOP + 0.09)) + d * 0.09), 0.014,
                   6, "M_Brass"))
    P.append(E.ball("brazier_foot", 0.022, tuple(V((BRX, BRY, TOP + 0.012)) + d * 0.13), "M_Brass", 6, 4))
for k in range(6):
    a = 2 * math.pi * k / 6 + 0.3
    d = rnd.uniform(0.0, 0.07)
    r = rnd.uniform(0.032, 0.045)
    P.append(rw.ico("coal", r, 1, (BRX + math.cos(a) * d, BRY + math.sin(a) * d, TOP + 0.15 + (0.012 if d < 0.03 else 0)),
                    (rnd.uniform(0, 90), rnd.uniform(0, 90), 0), (1.0, 1.0, 0.75),
                    S.mat("M_EmberGlow" if k % 3 else "Coal"), None, 0))
P.append(S.flame("flame", (BRX - 0.01, BRY, TOP + 0.15), 0.11, 0.04, "FlameGold", 6))
P.append(S.flame("flame", (BRX + 0.04, BRY - 0.03, TOP + 0.15), 0.08, 0.03, "ForgeGlow", 6))

# --- the still: green flask in a ring stand, copper alembic head, coil, purple receiver ----------------------------


def flask(c, r, neck_r, neck_h, fill, liquid, segs=12, shoulder=62):
    """Round-bottomed glass flask (sphere centre c) with glowing liquid up to `fill` (height above c).
    Returns (parts, neck top point)."""
    c = V(c)
    prof = [(0.0, -r)]
    for i in range(1, 9):
        phi = math.radians(-90 + i * (90 + shoulder) / 8)
        prof.append((r * math.cos(phi), r * math.sin(phi)))
    zs = r * math.sin(math.radians(shoulder))
    prof += [(neck_r, zs + 0.03), (neck_r, zs + neck_h), (neck_r * 1.35, zs + neck_h + 0.012),
             (neck_r * 1.35, zs + neck_h + 0.03), (neck_r * 0.85, zs + neck_h + 0.032)]
    parts = [S.lathe("flask", prof, segs, tuple(c), "M_Glass", 60)]
    ri = r - 0.014
    pf = math.degrees(math.asin(max(-0.99, min(0.99, fill / ri))))
    lp = [(0.0, -ri)]
    for i in range(1, 6):
        phi = math.radians(-90 + i * (pf + 90) / 5)
        lp.append((ri * math.cos(phi), ri * math.sin(phi)))
    lp.append((0.0, fill))
    parts.append(S.lathe("liquid", lp, segs, tuple(c), liquid, 60))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        rr = r * 0.4
        parts.append(rw.ico("bubble", r * rnd.uniform(0.09, 0.13), 1,
                            tuple(c + V((math.cos(a) * rr, math.sin(a) * rr, fill + r * rnd.uniform(0.08, 0.3)))),
                            (0, 0, 0), (1, 1, 1), M(liquid), None, 0))
    return parts, c + V((0, 0, zs + neck_h + 0.032))


GC = V((BRX, BRY, 1.27))
gparts, gneck = flask(GC, 0.17, 0.04, 0.14, 0.03, "AlchemyGreen")
P += gparts
# ring stand around the flask's lower half
P.append(E.ring("ringstand", 0.112, 0.014, (BRX, BRY, 1.14), (0, 0, 1), "M_Brass", 14, 4))
for k in range(3):
    a = math.radians(30 + 120 * k)
    d = V((math.cos(a), math.sin(a), 0.0))
    P.append(E.rod("ringstand_leg", tuple(V((BRX, BRY, TOP)) + d * 0.19), tuple(V((BRX, BRY, 1.14)) + d * 0.115), 0.012, 6,
                   "M_Brass"))
# copper alembic head on the neck
HEAD = gneck - V((0, 0, 0.03))
P.append(S.lathe("alembic", [(0.0, 0.0), (0.06, 0.0), (0.085, 0.04), (0.08, 0.08), (0.05, 0.12), (0.018, 0.15),
                             (0.0, 0.16)], 12, tuple(HEAD), "M_Copper", 50))
P.append(E.ball("alembic_knob", 0.025, tuple(HEAD + V((0, 0, 0.165))), "M_Brass", 8, 6))
# coil condenser
CX, CY, CZ0, CH_, CR, TURNS = -0.18, 0.06, TOP + 0.13, 0.33, 0.1, 2.5
PH = 200.0
coil = pl.helix("coil", CR, 0.021, TURNS, CH_, (CX, CY, CZ0), (0, 0, 1), 8, 6, S.mat("M_Copper"), PH, (True, True), 1)
P.append(coil)
a0 = math.radians(PH)
a1 = math.radians(PH + 360 * TURNS)
c_bot = V((CX + CR * math.cos(a0), CY + CR * math.sin(a0), CZ0))
c_top = V((CX + CR * math.cos(a1), CY + CR * math.sin(a1), CZ0 + CH_))
beak = HEAD + V((0.07, 0.0, 0.07))
P.append(pl.sausage("tube_in", [beak, beak + V((0.12, 0.02, 0.0)), V((CX - 0.06, CY - 0.04, c_top.z + 0.08)), c_top],
                    0.021, 6, 3, S.mat("M_Copper"), (True, True), 1, True, 60))
P.append(E.rod("coil_post", (CX, CY, TOP), (CX, CY, CZ0 + CH_ + 0.05), 0.016, 6, "M_Brass"))
P.append(S.lathe("coil_foot", [(0.0, 0.0), (0.07, 0.0), (0.07, 0.02), (0.03, 0.04), (0.0, 0.045)], 10, (CX, CY, TOP),
                 "M_Brass", 40))
P.append(E.ball("coil_cap", 0.028, (CX, CY, CZ0 + CH_ + 0.06), "M_Brass", 8, 6))
PC = V((0.12, -0.06, TOP + 0.03 + 0.135))
pparts, pneck = flask(PC, 0.135, 0.034, 0.08, 0.025, "AlchemyPurple", 12, 58)
P += pparts
P.append(E.ring("flask_rest", 0.075, 0.022, (PC.x, PC.y, TOP + 0.018), (0, 0, 1), "Twine", 12, 4))
P.append(pl.sausage("tube_out", [c_bot, c_bot + V((0.08, -0.06, -0.02)), pneck + V((-0.03, 0.0, 0.08)),
                                 pneck + V((0.0, 0.0, -0.03))], 0.019, 6, 3, S.mat("M_Copper"), (True, True), 1, True, 60))

# --- right side: mortar and pestle, books, scrolls, ink pot, potions ---------------------------------------------
MX, MY = 0.42, -0.22
P.append(S.lathe("mortar", [(0.0, 0.0), (0.09, 0.0), (0.12, 0.04), (0.13, 0.1), (0.115, 0.115), (0.095, 0.11),
                            (0.07, 0.06), (0.0, 0.05)], 12, (MX, MY, TOP), "M_StoneRough", 40))
P.append(rw.ico("mortar_herbs", 0.07, 1, (MX, MY, TOP + 0.075), (0, 0, 0), (1.0, 1.0, 0.45), M("Herb"), None, 30))
P.append(pl.sausage("pestle", [V((MX - 0.03, MY + 0.01, TOP + 0.07)), V((MX + 0.08, MY + 0.06, TOP + 0.24))],
                    [0.032, 0.022], 8, 1, S.mat("M_Stone"), (True, True), 2, False, 60))
# closed tome with brass corners and an open spell book on it
BKX, BKY, BKR = 0.74, 0.0, -8.0
book = [E.cbox("tome", (0.36, 0.27, 0.07), (0, 0, 0.035), (0, 0, 0), "BookPurple", 0.014),
        E.cbox("tome_pages", (0.34, 0.245, 0.055), (0.012, 0, 0.035), (0, 0, 0), "Parchment", 0.006)]
for sx in (-1, 1):
    for sy in (-1, 1):
        book.append(rw.box("tome_corner", (0.045, 0.045, 0.074), (sx * 0.16, sy * 0.115, 0.035), mat=S.mat("M_Brass")))
for s in (-1, 1):
    leaf = E.param_slab("openbook", lambda u, v, t, s=s: (s * (0.012 + u * 0.16), (v - 0.5) * 0.24,
                                                          0.075 + t * 0.018 + 0.035 * math.sin(math.pi * min(1, u * 1.15))
                                                          * (1 - u * 0.4)), 4, 1, "Parchment")
    book.append(leaf)
    book.append(E.cbox("opencover", (0.18, 0.26, 0.016), (s * 0.095, 0, 0.078), (0, s * -4, 0), "BookRed", 0.006))
book.append(rw.box("inkline", (0.1, 0.008, 0.004), (-0.09, 0.03, 0.122), mat=M("Ink")))
book.append(rw.box("inkline", (0.08, 0.008, 0.004), (-0.1, -0.02, 0.122), mat=M("Ink")))
book.append(rw.box("inkline", (0.09, 0.008, 0.004), (0.09, 0.0, 0.122), mat=M("Ink")))
E.place(book, (BKX, BKY, TOP), (0, 0, BKR))
P += book
# scrolls
for (x, y, rz, L, r) in ((0.62, -0.32, 78, 0.3, 0.032), (0.84, -0.3, 64, 0.26, 0.028)):
    sc = [rw.cylinder("scroll", r, L, 10, (0, 0, 0), (0, 90, 0), M("Parchment"))]
    for sx in (-1, 1):
        sc.append(rw.cylinder("scroll_end", r * 0.55, 0.03, 8, (sx * (L / 2 + 0.012), 0, 0), (0, 90, 0), S.mat("M_WoodDark")))
    sc.append(rw.torus("ribbon", r * 1.02, 0.008, 10, 3, (0.03, 0, 0), (0, 90, 0), M("PaintRed")))
    E.place(sc, (x, y, TOP + r), (0, 0, rz))
    P += sc
# ink pot and quill
P.append(S.lathe("inkpot", [(0.0, 0.0), (0.045, 0.0), (0.05, 0.04), (0.03, 0.06), (0.025, 0.075), (0.0, 0.075)], 10,
                 (0.4, 0.18, TOP), "GlassDark", 40))
P.append(pl.sausage("quill", [V((0.41, 0.18, TOP + 0.06)), V((0.37, 0.2, TOP + 0.2)), V((0.3, 0.24, TOP + 0.31))],
                    [0.008, 0.024, 0.008], 6, 2, M("PaperBlue"), (True, True), 1, True, 50))
# potion bottles (red tonic, blue draught)
for (x, y, h, m) in ((0.92, 0.25, 0.2, "PaintRed"), (0.58, 0.28, 0.16, "BottleBlue")):
    P.append(S.lathe("potion", [(0.0, 0.0), (0.05, 0.0), (0.06, 0.03), (0.055, h * 0.55), (0.022, h * 0.75),
                                (0.02, h * 0.9), (0.0, h * 0.9)], 10, (x, y, TOP), m, 50))
    P.append(S.lathe("potion_cork", [(0.0, h * 0.86), (0.02, h * 0.86), (0.024, h), (0.0, h)], 8, (x, y, TOP), "EndGrain",
                     40))

# --- herb drying rack (back right) --------------------------------------------------------------------------------
RX0, RX1, RY, RT = 0.22, 0.92, 0.36, 1.8
for x in (RX0, RX1):
    P.append(E.rbox("rackpost", (0.06, 0.06, RT - TOP - 0.06), (x, RY, (TOP + RT - 0.06) / 2), (0, 0, 0), "M_WoodDark",
                    0.012))
    P.append(E.cbox("rackfoot", (0.1, 0.16, 0.035), (x, RY - 0.02, TOP + 0.017), (0, 0, 0), "M_WoodDark", 0.01))
    P.append(E.ball("rackfinial", 0.042, (x, RY, RT - 0.04), "M_Brass", 8, 6))
P.append(E.rbox("rackbar", (RX1 - RX0 + 0.12, 0.05, 0.05), ((RX0 + RX1) / 2, RY, RT - 0.12), (0, 0, 0), "M_WoodDark", 0.012))
P.append(E.beam("rackbrace", (RX0 + 0.03, RY, RT - 0.36), (RX0 + 0.2, RY, RT - 0.145), 0.035, 0.035, "M_WoodDark", 0.0))
P.append(E.beam("rackbrace", (RX1 - 0.03, RY, RT - 0.36), (RX1 - 0.2, RY, RT - 0.145), 0.035, 0.035, "M_WoodDark", 0.0))
HB = RT - 0.12 - 0.025           # bottom of the bar
for k, (x, L, m, berry) in enumerate(((0.34, 0.2, "Herb", False), (0.5, 0.26, "HerbLavender", False),
                                      (0.66, 0.2, "HerbSage", True), (0.81, 0.24, "Herb", False))):
    top = V((x, RY - 0.005, HB))
    tie = top - V((0, 0, 0.06))
    P.append(rw.box("herbstring", (0.012, 0.012, 0.06), tuple(top - V((0, 0, 0.03))), mat=M("Twine")))
    P.append(rw.cylinder("herbtie", 0.03, 0.03, 8, tuple(tie), (0, 0, 0), M("Twine")))
    P.append(S.lathe("herbstems", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.06), (0.0, 0.06)], 6, tuple(tie), "HerbSage",
                     40))
    bundle = S.lathe("herbs", [(0.0, -L), (0.05, -L * 0.92), (0.085, -L * 0.62), (0.075, -L * 0.3), (0.04, -0.03),
                               (0.0, 0.0)], 8, tuple(tie - V((0, 0, 0.012))), m, 30)
    E.deform(bundle, lambda p, x=x: V((p.x + 0.015 * math.sin(p.z * 40 + x * 9), p.y + 0.012 * math.cos(p.z * 33), p.z)))
    P.append(bundle)
    for j in range(3):
        a = 2 * math.pi * j / 3 + k
        P.append(rw.ico("herbleaf", 0.035, 1, tuple(tie + V((math.cos(a) * 0.06, math.sin(a) * 0.05, -L * 0.55))),
                        (0, 0, rnd.uniform(0, 90)), (1.2, 0.8, 1.6), M(m), None, 30))
    if berry:
        for j in range(4):
            a = 2 * math.pi * j / 4
            P.append(rw.ico("berry", 0.022, 1, tuple(tie + V((math.cos(a) * 0.06, math.sin(a) * 0.06 - 0.02, -L * 0.8))),
                            (0, 0, 0), (1, 1, 1), M("HerbBerry"), None, 0))

table = E.join(P, "AlchemyTable", origin=(0, 0, 0))
rw.smooth(table, 35)
rw.empty("LightPoint", (BRX, BRY, TOP + 0.17))

# --- collision -----------------------------------------------------------------------------------------------------
E.col_box("Table", (2 * TX, TD, TOP), (0, TYC, TOP / 2))
E.col_box("Still", (0.92, 0.5, 0.82), (-0.42, 0.0, TOP + 0.41))
E.col_box("Rack", (RX1 - RX0 + 0.16, 0.12, RT - TOP), ((RX0 + RX1) / 2, RY, (TOP + RT) / 2))
S.preview_glass()
S.ground_centre([table])
S.finish(ASSET, (2.0, 1.0, 1.8), 6000, nodes=("AlchemyTable", "LightPoint"))
