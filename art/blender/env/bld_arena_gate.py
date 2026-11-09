"""bld_arena_gate: the gate segment of the Arena of Echoes ring wall (one of 24 segments, faces the town).

The same 15-degree arc as bld_arena_wall (ring centre at Blender (0, -30, 0), inner face radius 30 m, outer 32.5 m).
Its two ends (-7.5 .. -6.4 and 6.4 .. 7.5 degrees) are built from the same bldlib.ARENA_LAYERS and half pilasters as
the wall, so it matches its neighbours exactly. Between them stands a taller gatehouse with a walkable archway
(5 m wide, 6 m to the crown; collision only beside and above it): a raised portcullis whose spikes show in the top of
the arch, oak gate leaves folded back against the passage walls, voussoir arches with glowing rune keystones, a
crenellated top with an emblem crest, banners and lanterns, and two brass ley pylons marking the entrance outside.
Origin at the ground centre of the inner face, inner face towards -Y.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bldlib as B  # noqa: E402

E, rw, V = B.E, B.rw, B.V
ASSET = "bld_arena_gate"
B.reset()
P = []
L = B.Lights()
C = B.ARENA_C
H = B.AHALF
GH = H - B.APIL                 # the gatehouse spans -GH .. GH degrees
GR0, GR1 = 29.55, 32.95         # gatehouse inner / outer face radius
HW = 2.5                        # half width of the passage (planes x = +-HW)
ASP, ARI = 4.0, 2.0             # arch spring and rise: crown at 6.0
ZT = 7.1                        # gatehouse wall top (cornice above)
BANNER = "M_Fabric__b3342a"


def z_arch(x):
    return ASP + ARI * math.sqrt(max(0.0, 1 - (x / HW) ** 2))


def th_x(x, r):
    return math.degrees(math.asin(x / r))


def bendp(p, R):
    """A point given in a flat face frame (x along the face, y off the face) -> its place on the ring face R."""
    return E.ring_point(C, R + p[1], math.degrees(p[0] / R), p[2])


def block(name, th_a, th_b, z_a, z_b, r0, r1, nu, m):
    """Ring block between angle functions th_a(r) .. th_b(r) and height functions z_a(x) .. z_b(x)
    (x is the chord coordinate of each strip)."""
    def P_(u, v, s):
        r = r0 if s == 0 else r1
        th = th_a(r) + (th_b(r) - th_a(r)) * u
        x = r * math.sin(math.radians(th))
        z = z_a(x) + (z_b(x) - z_a(x)) * v
        return E.ring_point(C, r, th, z)
    return E.param_slab(name, P_, nu, 1, m)


# ---------------------------------------------------------------- the two ends: identical to bld_arena_wall
for (a, b) in ((-H, -GH), (GH, H)):
    P += B.arena_band(a, b)
P += B.arena_half_pilasters(-H, -GH)
P += B.arena_half_pilasters(GH, H)

# ---------------------------------------------------------------- gatehouse masonry around the passage
const = lambda v: (lambda _r: v)  # noqa: E731
P.append(block("gjambL", const(-GH), lambda r: -th_x(HW, r), const(-0.2), const(ZT), GR0, GR1, 2, "M_Stone"))
P.append(block("gjambR", lambda r: th_x(HW, r), const(GH), const(-0.2), const(ZT), GR0, GR1, 2, "M_Stone"))
P.append(block("gtop", lambda r: -th_x(HW, r), lambda r: th_x(HW, r), z_arch, lambda x: ZT, GR0, GR1, 16, "M_Stone"))
for sgn in (-1, 1):
    lo = (lambda r: -GH - 0.12) if sgn < 0 else (lambda r: th_x(HW, r))
    hi = (lambda r: -th_x(HW, r)) if sgn < 0 else (lambda r: GH + 0.12)
    P.append(block("gplinth", lo, hi, const(-0.2), const(0.78), GR0 - 0.16, GR1 + 0.16, 2, "M_StoneRough"))
P.append(E.arc_block("gcornice", C, GR0 - 0.14, GR1 + 0.14, -GH - 0.15, GH + 0.15, ZT, ZT + 0.26, 6, "M_StoneRough"))
P.append(E.arc_block("grune", C, GR0 - 0.165, GR0 - 0.1, -GH - 0.1, GH + 0.1, ZT + 0.07, ZT + 0.19, 6, "M_RuneGlow"))
ZW = ZT + 0.26
for (r0, r1) in ((GR0 - 0.05, GR0 + 0.45), (GR1 - 0.45, GR1 + 0.05)):
    P.append(E.arc_block("gparapet", C, r0, r1, -GH, GH, ZW, ZW + 0.42, 6, "M_Stone"))
    for th in (-5.3, -3.3, 3.3, 5.3):
        P.append(E.arc_block("gmerlon", C, r0, r1, th - 0.75, th + 0.75, ZW + 0.4, ZW + 0.86, 1, "M_Stone"))
        P.append(E.arc_block("gmerloncap", C, r0 - 0.04, r1 + 0.04, th - 0.82, th + 0.82, ZW + 0.84, ZW + 0.94, 1, "M_StoneRough"))
P.append(E.arc_block("gwalk", C, GR0 + 0.45, GR1 - 0.45, -GH, GH, ZW - 0.05, ZW + 0.05, 6, "M_StoneRough"))
# the crest over the arch, with an emblem on each face
P.append(E.arc_block("crest", C, GR0 - 0.05, GR1 + 0.05, -1.7, 1.7, ZW, ZW + 0.92, 2, "M_Stone"))
P.append(E.arc_block("crestcap", C, GR0 - 0.12, GR1 + 0.12, -1.85, 1.85, ZW + 0.9, ZW + 1.04, 2, "M_StoneRough"))
# passage floor
P.append(block("gfloor", lambda r: -th_x(HW, r), lambda r: th_x(HW, r), const(-0.2), const(0.03), GR0, GR1, 4, "M_Cobble"))

# ---------------------------------------------------------------- arch voussoirs, jambs and emblems on both faces


def face_details(outer):
    """Voussoirs, jamb quoins, keystone rune and crest emblem built flat (+y = away from the wall), bent later."""
    out = []
    sgn = 1 if outer else -1
    VD = 0.52
    ra, rb = HW + VD / 2, ARI + VD / 2
    nv = 11
    for i in range(nv):
        phi = math.pi * (i + 0.5) / nv
        xm, zm = ra * math.cos(phi), ASP + rb * math.sin(phi)
        beta = math.degrees(math.atan2(rb * math.cos(phi), -ra * math.sin(phi)))
        key = i == nv // 2
        size = (0.85, 0.36, VD + 0.3) if key else (0.7, 0.26, VD)
        out.append(E.stone("gvous", size, (xm, sgn * (size[1] / 2 - 0.08), zm + (0.1 if key else 0)), (0, -beta, 0),
                           "M_StoneRough" if key or i % 2 else "M_Stone", 0.05, seed=i + 20 * outer, jitter=0 if key else 1.5))
    for sx in (-1, 1):
        for k in range(3):
            z = 0.8 + (ASP - 0.8) * (k + 0.5) / 3
            wide = k % 2 == 0
            out.append(E.stone("gjamb", (VD + (0.18 if wide else 0.0), 0.24, (ASP - 0.8) / 3 - 0.05), (sx * ra + sx * 0.04, sgn * 0.06, z),
                               (0, 0, 0), "M_Stone" if wide else "M_StoneRough", 0.05, seed=k + 7 * sx, jitter=1.0))
        out.append(E.rbox("gimpost", (VD + 0.36, 0.32, 0.24), (sx * ra, sgn * 0.1, ASP + 0.02), m="M_StoneRough", r=0.04))
    out += E.glyph(2 if outer else 5, 0.48, (0, sgn * 0.36, ASP + rb + 0.12), (0, sgn, 0), "M_RuneGlow", 0.17, 0.05)
    # crest emblem: a bronze shield with crossed swords and a glowing boss
    ez = ZW + 0.46
    out.append(E.disc("eshield", 0.5, 0.1, (0, sgn * 0.08, ez), (0, sgn, 0), 18, "M_Copper"))
    out.append(E.ring("erim", 0.5, 0.05, (0, sgn * 0.12, ez), (0, sgn, 0), "M_Brass", 16, 4))
    for k in (-1, 1):
        out.append(E.beam("sword", (k * 0.48, sgn * 0.17, ez - 0.48), (-k * 0.4, sgn * 0.17, ez + 0.4), 0.09, 0.04, "M_Steel", 0.015,
                          up=(0, sgn, 0)))
        out.append(E.beam("guard", (k * 0.36 - 0.12, sgn * 0.18, ez - 0.24 - 0.12 * k), (k * 0.36 + 0.12, sgn * 0.18, ez - 0.36 + 0.12 * k),
                          0.06, 0.05, "M_Brass", 0.012, up=(0, sgn, 0)))
    out.append(E.ball("eboss", 0.13, (0, sgn * 0.2, ez), "TealGlow", 6, 4))
    return out


INNER = face_details(False)
B.ring_bend(INNER, GR0)
P += INNER
OUTER = face_details(True)
# banners from the outer parapet and lanterns flanking the arch (outer face)
for sx in (-1, 1):
    ban = E.cloth("gbanner", 0.95, 2.75, (0, 0, 0), wave=0.04, waves=1.3, tail=0.4, m=BANNER, t=0.03, nu=6, nv=7, sway=0.05)
    gold = [E.ring("bring", 0.24, 0.035, (0, -0.03, -0.95), (0, -1, 0), "StarGold", 12, 4),
            B.star_prism("bstar", 0.17, 0.07, 0.14, (0, -0.02, -0.95), (0, -1, 0), "StarGold", 5)]
    E.place([ban] + gold, (sx * 3.15, 0.32, ZT + 0.02), (0, 0, 180))
    OUTER += [ban] + gold
    OUTER.append(E.rod("banrod", (sx * 3.15 - 0.58, 0.32, ZT + 0.04), (sx * 3.15 + 0.58, 0.32, ZT + 0.04), 0.035, 6, "M_Brass"))
    for k in (-1, 1):
        OUTER.append(B.bar("banbracket", (sx * 3.15 + k * 0.42, 0.0, ZT + 0.04), (sx * 3.15 + k * 0.42, 0.34, ZT + 0.04), 0.05, 0.05,
                           "IronDark"))
    lp, lc = E.lantern((sx * 3.38, 0.36, 3.15), "wall", wall_normal=(0, 1, 0), scale=1.15)
    OUTER += lp
    L.add(bendp(lc, GR1))
B.ring_bend(OUTER, GR1)
P += OUTER

# ---------------------------------------------------------------- the raised portcullis and the folded-back gate leaves
PY = (GR0 + GR1) / 2 - 30.0     # mid-depth plane of the passage (y in the segment frame)
for k in range(10):
    x = -2.25 + 0.5 * k
    P.append(E.rod("pbar", (x, PY, 5.12), (x, PY, ZT - 0.2), 0.055, 6, "IronDark"))
    P.append(rw.cone("pspike", 0.07, 0.0, 0.26, 6, (x, PY, 5.0), (180, 0, 0), E.mat("IronDark")))
for z in (5.38, 5.9):
    P.append(E.rbox("prail", (2 * HW - 0.08, 0.1, 0.1), (0, PY, z), m="IronDark", r=0.02))
for sx in (-1, 1):
    x = sx * (HW - 0.07)
    nb = 6
    y0, y1 = 0.22, 2.32
    for j in range(nb):
        yy = y0 + (y1 - y0) * (j + 0.5) / nb
        P.append(rw.box("leafboard", (0.1, (y1 - y0) / nb - 0.03, 3.75), (x, yy, 0.05 + 3.75 / 2), mat=E.mat("M_WoodPlanks")))
    for z in (0.7, 2.0, 3.3):
        P.append(rw.box("leafstrap", (0.04, y1 - y0 + 0.04, 0.14), (x - sx * 0.06, (y0 + y1) / 2, z), mat=E.mat("IronDark")))
        for j in range(2):
            P.append(E.rivet("stud", (x - sx * 0.09, y0 + 0.3 + (y1 - y0 - 0.6) * j, z), 0.04, "M_Brass", lo=True))
# a lantern hanging in the passage
P.append(E.rod("plampchain", (0, 0.65, z_arch(0.0)), (0, 0.65, z_arch(0.0) - 0.3), 0.02, 5, "IronDark"))
plamp, plc = E.lantern((0, 0.65, z_arch(0.0) - 0.25), "hang", scale=1.15)
P += plamp
L.add(plc)

# ---------------------------------------------------------------- ley pylons marking the entrance outside
PYL = []
for sgn in (-1, 1):
    base = V(E.ring_point(C, 33.75, sgn * 6.5, 0.0))
    P.append(E.cbox("pylbase", (1.15, 1.15, 0.62), tuple(base + V((0, 0, 0.21))), (0, 0, -sgn * 6.5), "M_StoneRough", 0.06))
    py, pyc = B.ley_pylon(sgn * 6.5, 33.75, 0.52, 1.18)
    P += py
    PYL.append((base, pyc))

E.tri_breakdown(P, 24)
main = E.join(P, "ArenaGate")
rw.smooth(main, 40)

# ---------------------------------------------------------------- empties
L.emit()

# ---------------------------------------------------------------- collision: the ends, the gatehouse beside and above the opening
B.arena_hulls("Wall", -H, -GH, 29.85, 32.62, -0.2, 6.95, n=1)
B.arena_hulls("Wall", GH, H, 29.85, 32.62, -0.2, 6.95, n=1)
CW = HW - 0.14                  # the folded gate leaves narrow the clear width a little
for sgn in (-1, 1):
    pts = []
    for r in (GR0 - 0.15, GR1 + 0.15):
        for th in (sgn * GH, sgn * th_x(CW, r)):
            for z in (-0.2, ZW + 0.4):
                pts.append(E.ring_point(C, r, th, z))
    E.col_hull("Jamb", pts)
    # haunches between the arch and the jambs
    for (xa, xb) in ((1.7, HW), (0.8, 1.7)):
        pts = []
        for r in (GR0, GR1):
            for x in (xa, xb):
                for z in (z_arch(x) + 0.02, z_arch(0.0) + 0.02):
                    pts.append(E.ring_point(C, r, sgn * th_x(x, r), z))
        E.col_hull("Haunch", pts)
pts = []
for r in (GR0 - 0.15, GR1 + 0.15):
    for x in (-HW, HW):
        for z in (z_arch(0.0), ZW + 1.0):
            pts.append(E.ring_point(C, r, th_x(x, r), z))
E.col_hull("Lintel", pts)
for base, pyc in PYL:
    E.col_cyl("Pylon", 0.62, 2.9, (base.x, base.y, 1.45), verts=10)

E.check(ASSET, (8.6, 4.9, 8.8), 8000)
rw.finish(ASSET, "env", previews=E.previews())
