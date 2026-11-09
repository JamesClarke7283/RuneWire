"""vm_tome: first-person "Wispcaller Grimoire", a chunky open spellbook held up toward the camera.

The glove holds the book from below at its lower edge: palm under the spine and the brass tail cap, fingers
curled under the left cover, thumb across the gutter pinning the pages. The pages face up and toward the
camera (+Y/+Z): the spine runs from the lower edge forward and 40 degrees up (SPINE_DIR).

Nodes (origin = grip centre):
  Tome     thick plum leather covers on a rounded spine with raised bands and brass end caps, brass corner
           caps with rivets, two cream text blocks with ridged fore-edges and curved parchment pages: a
           glowing teal magic circle (rings, hexagram, ticks, eye rune) and a row of runes on the left page,
           three rows of runes and inked lines on the right page (rw.glow 39d5c4), inked page borders; a crimson ribbon
           bookmark lying across the right page and hanging over the lower edge with a swallowtail end; a
           short brass chain hanging from the left cover's fore-edge ending in a clasp that carries the
           rarity gem (facing the player). The front cover (left, underneath) carries a faceted crystal gem
           in a brass medallion with filigree scrolls (M_Crystal__a066ff - the only crystal on the model;
           the game swaps its tint per tome); the back cover a brass sun boss and studs.
  Pages    three loose leaves fanning up from the gutter (child of Tome; origin on the spine/gutter line;
           the game flutters it - rotate it about SPINE_DIR).
  Glove    the shared cartoon leather glove (glove.py).
  Emitter  empty just above the open pages, over the gutter in the middle of the book.
"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import magic_weapon_helpers as mh  # noqa: E402

glove, pl, rw, V, dh, nw = mh.glove, mh.pl, mh.rw, mh.V, mh.dh, mh.nw
rw.reset()

CRYSTAL = mh.crystal_mat()
RARITY = mh.rarity_mat()
RUNE = rw.glow("PageRune", "39d5c4", 3.0)
PAGE = rw.flat("Parchment", "f7e6ba", 0.8, 0.0)
PAGE_EDGE = rw.flat("PageEdge", "e0c993", 0.85, 0.0)
INK = rw.flat("Ink", "4a3426", 0.7, 0.0)
RIBBON = rw.flat("Ribbon", "b8202e", 0.6, 0.0)
COVER = "M_Leather__4a2d6b"
SPINE_LEATHER = "M_Leather__36204f"

# --- book frame --------------------------------------------------------------------------------------------------------
TILT = 40.0
_t = math.radians(TILT)
S = V((0, -math.cos(_t), math.sin(_t)))       # spine direction: lower edge -> top edge (SPINE_DIR)
N = V((0, math.sin(_t), math.cos(_t)))        # page normal: up and toward the camera
X = V((1, 0, 0))                               # +X = the left page (the player's left)
PHI = 8.0                                      # each half rises PHI degrees from the spine (shallow V)
_cp, _sp = math.cos(math.radians(PHI)), math.sin(math.radians(PHI))
N0 = 0.011                                     # the spine axis sits this far above the grip axis (along N)
O = N * N0


def Lv(sd):
    """Across the half `sd` (+1 left, -1 right), from the spine toward its fore-edge."""
    return X * (sd * _cp) + N * _sp


def Uv(sd):
    """Up out of the half's pages."""
    return X * (-sd * _sp) + N * _cp


def BP(sd, l, h, u):
    return O + Lv(sd) * l + S * h + Uv(sd) * u


# book dimensions (metres): text block, covers
H0, H1 = -0.045, 0.235                         # text block, lower edge -> top edge
CH0, CH1 = -0.052, 0.242                       # covers
LT0, LT1 = 0.006, 0.18                         # text block from the gutter to the fore-edge
LC0, LC1 = 0.026, 0.192                        # covers
UC0, UC1 = -0.038, -0.02                       # cover board (outer face, inner face)


def T(l):
    """Text block thickness above the cover's inner face: dips into the gutter, slopes to the fore-edge."""
    if l >= 0.035:
        return 0.056 - (l - 0.035) * 0.1241
    k = max(0.0, (l - LT0) / (0.035 - LT0))
    return 0.044 + 0.012 * math.sin(math.pi / 2 * k)


def UT(l):
    return UC1 + T(l)


def page_frame(sd, l, h):
    """(point on the page surface, tangent across, tangent along the spine, normal) at (l, h)."""
    p = BP(sd, l, h, UT(l))
    dl = 0.002
    tl = (BP(sd, l + dl, h, UT(l + dl)) - BP(sd, l - dl, h, UT(l - dl))).normalized()
    n = tl.cross(S).normalized()
    if n.dot(Uv(sd)) < 0:
        n = -n
    return p, tl, S.copy(), n


parts = mh.Parts()

# --- text blocks: a lofted section (bottom on the cover, ridged fore-edge, curved page top) -------------------------
TOP_L = [0.18, 0.16, 0.14, 0.12, 0.1, 0.08, 0.06, 0.045, 0.035, 0.027, 0.02, 0.014, 0.009, LT0]
FORE = [(LT1, UC1), (LT1 + 0.0016, UC1 + 0.007), (LT1 - 0.0004, UC1 + 0.012), (LT1 + 0.0016, UC1 + 0.018),
        (LT1 - 0.0004, UC1 + 0.024), (LT1 + 0.0012, UC1 + 0.03)]
for sd in (1, -1):
    sec = [(LT0, UC1 - 0.007, 1)] + [(l, u, 1) for (l, u) in FORE] + [(l, UT(l), 0) for l in TOP_L]
    bm = bmesh.new()
    rings = [[bm.verts.new(BP(sd, l, h, u)) for (l, u, _) in sec] for h in (H0, H1)]
    n = len(sec)
    for j in range(n):
        jj = (j + 1) % n
        f = bm.faces.new((rings[0][j], rings[0][jj], rings[1][jj], rings[1][j]))
        f.material_index = 0 if (sec[j][2] == 0 and sec[jj][2] == 0) else 1
    for r in rings:
        f = bm.faces.new(r)
        f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tb = pl.obj_from_bm("text_block", bm, None, 0)
    tb.data.materials.append(rw._resolve_mat(PAGE))
    tb.data.materials.append(rw._resolve_mat(PAGE_EDGE))
    rw.smooth(tb, 30)
    parts.add(tb)
# the fold where the two text blocks meet the spine (a shallow crease)
parts.add(pl.obox("gutter_fold", (0.016, H1 - H0, 0.034), O + S * ((H0 + H1) / 2) + N * 0.002, X, N, PAGE_EDGE))

# --- covers ----------------------------------------------------------------------------------------------------------------
for sd in (1, -1):
    c = BP(sd, (LC0 + LC1) / 2, (CH0 + CH1) / 2, (UC0 + UC1) / 2)
    parts.add(pl.obox("cover", (LC1 - LC0, CH1 - CH0, UC1 - UC0), c, Lv(sd), Uv(sd), COVER, rounded=0.0045,
                      segments=2))

# --- spine: a rounded leather back joining the covers' inner edges, raised bands, brass end caps -----------------
# spine arc (x, n relative to O): passes through the covers' inner bottom corners and dips SP_DIP below them
_cx = LC0 * _cp - UC0 * _sp
_cn = LC0 * _sp + UC0 * _cp
SP_DIP = 0.017
_nb = _cn - SP_DIP
_k = ((_cx ** 2 + _cn ** 2) - _nb ** 2) / (2 * (_cn - _nb))     # centre height from |c - corner| = c - nb
SPC = (0.0, _k)
SPR = _k - _nb


def arc_outline(r_out, r_in, a0, a1, steps=10):
    outer = [(SPC[0] + r_out * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
              SPC[1] + r_out * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]
    inner = [(SPC[0] + r_in * math.cos(math.radians(a1 + (a0 - a1) * i / steps)),
              SPC[1] + r_in * math.sin(math.radians(a1 + (a0 - a1) * i / steps))) for i in range(steps + 1)]
    return outer + inner


def spine_piece(name, r_out, r_in, a0, a1, h0, h1, mat, bevel=0.0):
    return nw.slab(name, arc_outline(r_out, r_in, a0, a1), h1 - h0, O + S * ((h0 + h1) / 2), X, N, mat,
                   bevel=bevel, segments=1, angle=40, smooth_angle=50)


parts.add(spine_piece("spine", SPR, SPR - 0.011, -18.0, -162.0, CH0 + 0.004, CH1 - 0.004, SPINE_LEATHER))
for h in (0.118, 0.19):
    parts.add(spine_piece("spine_band", SPR + 0.0032, SPR - 0.004, -24.0, -156.0, h - 0.0045, h + 0.0045,
                          SPINE_LEATHER, 0.0012))
for (h0, h1) in ((CH0 - 0.004, CH0 + 0.012), (CH1 - 0.012, CH1 + 0.004)):
    parts.add(spine_piece("spine_cap", SPR + 0.0035, SPR - 0.013, -14.0, -166.0, h0, h1, "M_Brass", 0.0015))
for h in (CH0 + 0.004, CH1 - 0.004):
    p = O + S * h + N * SPC[1] - N * (SPR + 0.0035)
    parts.add(nw.stud(p, -N, 0.0045, 0.0032, "M_Copper", 6))

# --- brass corner caps on the fore-edge corners of both covers ---------------------------------------------------------
for sd in (1, -1):
    for head in (False, True):
        hc = CH1 if head else CH0
        hs = -1.0 if head else 1.0
        tri = [(0.0025, -0.0025 * hs), (-0.042, -0.0025 * hs), (0.0025, 0.042 * hs)]
        if sd * hs < 0:
            tri = tri[::-1]
        outline = nw.rounded_poly(tri, [0.005, 0.004, 0.004], 3)
        cc = BP(sd, LC1, hc, (UC0 + UC1) / 2)
        parts.add(nw.slab("corner_cap", outline, (UC1 - UC0) + 0.006, cc, Lv(sd), S, "M_Brass", bevel=0.0018,
                          segments=1, angle=35))
        for uu, nn in ((UC1 + 0.003, Uv(sd)), (UC0 - 0.003, -Uv(sd))):
            parts.add(nw.stud(BP(sd, LC1 - 0.011, hc + hs * 0.011, uu), nn, 0.0042, 0.003, "M_Copper", 6))

# --- front cover (left, underneath): the crystal in a brass medallion with filigree; back cover: sun boss ---------
MC = BP(1, 0.106, 0.095, UC0)
mn = -Uv(1)
parts.add(pl.lathe_axis("medallion", [(0.0, 0.0), (0.03, 0.0), (0.031, 0.002), (0.028, 0.0045), (0.0235, 0.005),
                                      (0.0215, 0.0035), (0.0, 0.0035)], mn, MC, 24, "M_Brass", False, False, 40))
parts.add(mh.gem_lathe("cover_gem", [(0.0, -0.001), (0.0195, 0.0025), (0.0205, 0.0065), (0.0175, 0.0115),
                                     (0.011, 0.0155), (0.0, 0.0175)], mn, MC + mn * 0.002, 10, CRYSTAL, True, 0.0, S))
for k in range(4):
    a = math.radians(45 + 90 * k)
    d = Lv(1) * math.cos(a) + S * math.sin(a)
    parts.add(pl.capsule("gem_claw", MC + d * 0.0215 + mn * 0.0045, MC + d * 0.0178 + mn * 0.0115, 0.0028, 6, 1,
                         "M_Brass"))
    sc = MC + d * 0.046 + mn * 0.0004
    parts.add(mh.flat_scroll("cover_scroll", sc, d, d.cross(mn), 0.0115, 0.0024, 0.003, "M_Brass", 0.9, 180.0, True,
                             10, tail=(-0.0175, 0.0)))
    parts.add(nw.stud(BP(1, 0.106 + 0.062 * math.cos(a), 0.095 + 0.105 * math.sin(a), UC0), mn, 0.0052, 0.0036,
                      "M_Brass", 8))
BC = BP(-1, 0.106, 0.095, UC0)
bn = -Uv(-1)
parts.add(pl.disc("sun_boss", 0.021, 0.006, bn, BC + bn * 0.002, "M_Brass", 20, 0.4))
parts.add(mh.sun_glyph("sun", BC + bn * 0.005, Lv(-1), S, 0.024, "M_Brass", 0.004, 10, None, None, True, 16))
for k in range(4):
    a = math.radians(45 + 90 * k)
    parts.add(nw.stud(BP(-1, 0.106 + 0.062 * math.cos(a), 0.095 + 0.105 * math.sin(a), UC0), bn, 0.0052, 0.0036,
                      "M_Brass", 8))

# --- left page: a glowing magic circle and a row of runes ------------------------------------------------------------
RD = 0.0013                                     # rune stroke depth (half sunk into the paper)
p, tl, ts, pn = page_frame(1, 0.106, 0.098)
for (r, w) in ((0.047, 0.0033), (0.0372, 0.0026)):
    ring = rw.torus("circle_ring", r, w, 40, 4, (0, 0, 0), mat=RUNE)
    pl.align(ring, pn, p, x_hint=tl)
    pl.xform(ring, pl.Matrix.Scale(0.3, 4, pn))
    parts.add(ring)
for tri in (0, 1):
    pts = [p + tl * (0.0375 * math.cos(math.radians(90 + 120 * k + 60 * tri))) +
           ts * (0.0375 * math.sin(math.radians(90 + 120 * k + 60 * tri))) for k in range(3)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        parts.add(pl.obox("hexagram", ((b - a).length + 0.0034, 0.0034, RD), (a + b) / 2, b - a, pn, RUNE))
for k in range(12):
    a = math.radians(15 + 30 * k)
    d = tl * math.cos(a) + ts * math.sin(a)
    parts.add(pl.obox("circle_tick", (0.0058, 0.0032, RD), p + d * 0.0421, d, pn, RUNE))
parts.add(mh.glyph2("eye", p, -tl, ts, 0.024, 0.028, 0.0036, RD, RUNE, "page_rune"))
for (l, key) in ((0.072, "kenaz"), (0.106, "tiwaz"), (0.14, "fehu")):
    q, a_, b_, n_ = page_frame(1, l, 0.192)
    parts.add(mh.glyph2(key, q, -a_, b_, 0.017, 0.024, 0.0046, RD, RUNE, "page_rune"))
for (h, l0, l1) in ((0.032, 0.06, 0.158), (0.012, 0.06, 0.13)):
    q0 = page_frame(1, l0, h)[0]
    q1 = page_frame(1, l1, h)[0]
    parts.add(pl.obox("ink_line", ((q1 - q0).length, 0.0028, RD), (q0 + q1) / 2, q1 - q0,
                      page_frame(1, (l0 + l1) / 2, h)[3], INK))

# --- right page: rows of runes and inked lines ------------------------------------------------------------------------
KEYS = ["algiz", "sowilo", "othala", "dagaz", "hagal", "kenaz", "ingwaz", "fehu", "tiwaz"]
i = 0
# runes in the lower half (left clear of the leaves, which hide the upper half from the player), clear of the ribbon
for h in (0.098, 0.062, 0.026):
    for l in (0.082, 0.114, 0.146):
        q, a_, b_, n_ = page_frame(-1, l, h)
        # u = the reader's right (-X), which on the right page is the +l tangent
        parts.add(mh.glyph2(KEYS[i % len(KEYS)], q, a_, b_, 0.017, 0.024, 0.0046, RD, RUNE, "page_rune"))
        i += 1
for (h, l0, l1) in ((0.205, 0.04, 0.16), (0.183, 0.04, 0.145), (0.161, 0.05, 0.16), (0.139, 0.06, 0.13)):
    q0 = page_frame(-1, l0, h)[0]
    q1 = page_frame(-1, l1, h)[0]
    parts.add(pl.obox("ink_line", ((q1 - q0).length, 0.0028, RD), (q0 + q1) / 2, q1 - q0,
                      page_frame(-1, (l0 + l1) / 2, h)[3], INK))

# --- inked page borders (top, bottom and the outer side of each page) -----------------------------------------------
for sd in (1, -1):
    for (l0, h0, l1, h1) in ((0.03, 0.222, 0.168, 0.222), (0.03, -0.032, 0.168, -0.032), (0.168, -0.032, 0.168, 0.222)):
        q0 = page_frame(sd, l0, h0)[0]
        q1 = page_frame(sd, l1, h1)[0]
        parts.add(pl.obox("ink_border", ((q1 - q0).length + 0.003, 0.003, RD), (q0 + q1) / 2, q1 - q0,
                          page_frame(sd, (l0 + l1) / 2, (h0 + h1) / 2)[3], INK))


# --- ribbon bookmark: across the right page, over the lower edge, hanging with a swallowtail ----------------------
def ribbon_strip(name, pts, normals, width, thick, mat, fork=0.012):
    P = [V(p) for p in pts]
    m = len(P)
    bm = bmesh.new()
    rings = []
    for i in range(m):
        tng = (P[min(i + 1, m - 1)] - P[max(i - 1, 0)]).normalized()
        w = tng.cross(V(normals[i])).normalized()
        nn = w.cross(tng).normalized()
        rings.append([bm.verts.new(P[i] + w * (sx * width / 2) + nn * (sy * thick / 2))
                      for (sx, sy) in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    for i in range(m - 2):
        a, b = rings[i], rings[i + 1]
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    bm.faces.new(list(reversed(rings[0])))
    # last segment ends in a swallowtail: a V-notch cut back `fork` into the strip
    a, b = rings[-2], rings[-1]
    tng = (P[-1] - P[-2]).normalized()
    c0 = bm.verts.new((b[0].co + b[1].co) / 2 - tng * fork)
    c1 = bm.verts.new((b[2].co + b[3].co) / 2 - tng * fork)
    bm.faces.new((a[0], a[1], b[1], c0, b[0]))
    bm.faces.new((a[1], a[2], b[2], b[1]))
    bm.faces.new((a[2], a[3], b[3], c1, b[2]))
    bm.faces.new((a[3], a[0], b[0], b[3]))
    bm.faces.new((b[0], c0, c1, b[3]))
    bm.faces.new((b[1], b[2], c1, c0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, mat, 40)


RB = []
RN = []
for (l, h) in ((0.004, 0.17), (0.016, 0.13), (0.03, 0.085), (0.045, 0.035), (0.058, -0.012), (0.064, -0.038)):
    q, a_, b_, n_ = page_frame(-1, l, h)
    RB.append(q + n_ * 0.0018)
    RN.append(n_)
edge = BP(-1, 0.066, H0 - 0.003, UT(0.066) - 0.004)
RB += [edge, BP(-1, 0.067, H0 - 0.0045, UC1 - 0.004), BP(-1, 0.068, CH0 - 0.004, UC0 - 0.006)]
RN += [-S, -S, -S]
low = RB[-1]
for k, dz in enumerate((0.022, 0.044, 0.064)):
    RB.append(low + V((0, 0, -dz)) + S * (-0.004 - 0.003 * k) + X * (-0.002 * k))
    RN.append(-S)
parts.add(ribbon_strip("ribbon", RB, RN, 0.016, 0.0026, RIBBON, 0.012))

# --- chain with a clasp hanging from the left cover's fore-edge -------------------------------------------------------
ANC = BP(1, LC1 + 0.001, 0.016, (UC0 + UC1) / 2)
staple = rw.torus("staple", 0.0062, 0.0024, 12, 5, (0, 0, 0), mat="M_Brass")
pl.align(staple, S, ANC + Lv(1) * 0.004)
parts.add(staple)
top = ANC + Lv(1) * 0.0095
for i in range(4):
    lc = top + V((0, 0, -(0.009 + 0.0148 * i)))
    link = rw.torus("chain_link", 0.0074, 0.0024, 12, 5, (0, 0, 0), mat="M_Brass")
    pl.xform(link, pl.Matrix.Diagonal((1.0, 1.4, 1.0, 1.0)))
    if i % 2 == 0:
        pl.align(link, (0, 1, 0), lc, x_hint=(1, 0, 0))
    else:
        pl.align(link, (1, 0, 0), lc, x_hint=(0, 1, 0))
    parts.add(link)
CL = top + V((0, 0, -(0.009 + 0.0148 * 3 + 0.03)))
cn = V((0.3, 1.0, 0.25)).normalized()
cu = V((0, 0, 1))
cx = cu.cross(cn).normalized()
ring = rw.torus("clasp_ring", 0.0058, 0.0024, 12, 5, (0, 0, 0), mat="M_Brass")
pl.align(ring, cx, CL + cu * 0.0215)
parts.add(ring)
parts.add(nw.slab("clasp", nw.rounded_poly([(-0.012, 0.016), (0.012, 0.016), (0.009, -0.014), (0.0, -0.022),
                                            (-0.009, -0.014)], [0.004, 0.004, 0.006, 0.004, 0.006], 3), 0.007, CL,
                  cx, cu, "M_Brass", bevel=0.0018, segments=1, angle=35))
parts.add(nw.gem(CL + cn * 0.0035 + cu * 0.002, cn, 0.0062, RARITY, "M_Copper", 8, "rarity_gem"))
hook = [CL - cu * 0.019, CL - cu * 0.028 + cn * 0.003, CL - cu * 0.03 + cn * 0.011, CL - cu * 0.024 + cn * 0.015]
parts.add(pl.sausage("clasp_hook", hook, [0.0034, 0.0032, 0.003, 0.0028], 6, 3, "M_Brass", (True, True), 2, True, 60))

tome = rw.join(parts, "Tome", origin=(0, 0, 0))

# --- Pages: three loose leaves fanning up from the gutter -----------------------------------------------------------------
HINGE_N = N0 + UT(LT0) * _cp + 0.0008           # gutter line height above the grip axis (along N)
LEAF_H = (0.075, 0.228)


def leaf(name, beta0, kappa, width, h0, h1, twist, thick=0.0028, ns=8, nh=3):
    """A curved page: its cross-section starts at the hinge at angle beta0 (0 = lying right, 90 = upright,
    180 = lying left), bending by kappa degrees toward its free edge, twisting by `twist` along the spine."""
    bm = bmesh.new()
    grid_top, grid_bot = [], []
    for j in range(nh + 1):
        hh = h0 + (h1 - h0) * j / nh
        tw = twist * (j / nh - 0.5)
        p = N * HINGE_N + S * hh
        row_t, row_b = [], []
        for i in range(ns + 1):
            if i > 0:
                b = math.radians(beta0 + (kappa + tw) * ((i - 0.5) / ns))
                p = p + (-X * math.cos(b) + N * math.sin(b)) * (width / ns)
            b = math.radians(beta0 + (kappa + tw) * (i / ns))
            nrm = X * math.sin(b) + N * math.cos(b)
            row_t.append(bm.verts.new(p + nrm * (thick / 2)))
            row_b.append(bm.verts.new(p - nrm * (thick / 2)))
        grid_top.append(row_t)
        grid_bot.append(row_b)
    for j in range(nh):
        for i in range(ns):
            bm.faces.new((grid_top[j][i], grid_top[j][i + 1], grid_top[j + 1][i + 1], grid_top[j + 1][i]))
            bm.faces.new((grid_bot[j][i], grid_bot[j + 1][i], grid_bot[j + 1][i + 1], grid_bot[j][i + 1]))
    for j in range(nh):
        for i in (0, ns):
            bm.faces.new((grid_top[j][i], grid_top[j + 1][i], grid_bot[j + 1][i], grid_bot[j][i]))
    for i in range(ns):
        for j in (0, nh):
            bm.faces.new((grid_top[j][i], grid_bot[j][i], grid_bot[j][i + 1], grid_top[j][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, PAGE, 50)


lparts = mh.Parts()
for (b0, kap, wd, hh0, hh1, tw) in ((40.0, -24.0, 0.15, 0.08, 0.226, 10.0), (74.0, -34.0, 0.152, 0.077, 0.228, -14.0),
                                    (112.0, -30.0, 0.146, 0.082, 0.222, 12.0)):
    lf = leaf("leaf", b0, kap, wd, hh0, hh1, tw)
    lparts.add(lf)
# a few inked lines and a glowing rune on the leaves (on the face toward the camera)
for (b0, kap, wd, hh0, hh1, tw) in ((40.0, -24.0, 0.15, 0.08, 0.226, 10.0), (74.0, -34.0, 0.152, 0.077, 0.228, -14.0),
                                    (112.0, -30.0, 0.146, 0.082, 0.222, 12.0)):
    for (fs, hh, ln) in ((0.45, 0.19, 0.07), (0.45, 0.165, 0.08), (0.45, 0.14, 0.06)):
        # walk to fraction fs of the width along the leaf's centre line at height hh
        p = N * HINGE_N + S * hh
        ns = 8
        pts = [p]
        for i in range(1, ns + 1):
            b = math.radians(b0 + kap * ((i - 0.5) / ns))
            p = p + (-X * math.cos(b) + N * math.sin(b)) * (wd / ns)
            pts.append(p)
        k = fs * ns
        i0 = int(k)
        q = pts[i0].lerp(pts[min(i0 + 1, ns)], k - i0)
        b = math.radians(b0 + kap * fs)
        nrm = X * math.sin(b) + N * math.cos(b)
        across = (-X * math.cos(b) + N * math.sin(b))
        # the camera looks at the face whose normal points toward +Y/+Z: pick that side
        side = 1.0 if nrm.dot(V((0.2, 0.7, 0.7))) > 0 else -1.0
        lparts.add(pl.obox("leaf_ink", (ln, 0.0026, 0.0014), q + nrm * side * 0.0015, across, nrm * side, INK))
pages = rw.join(list(lparts), "Pages", origin=tuple(N * HINGE_N + S * ((LEAF_H[0] + LEAF_H[1]) / 2)))
pl.parent_keep(pages, tome)

# --- glove: palm up under the spine, fingers under the left cover, thumb across the gutter ---------------------------
g = glove.fist(A=S, out=-N, F=(-0.3, 1.0, -1.0), wrist_len=0.05, finger_wrap=0.45, thumb_lift=-0.03)

rw.empty("Emitter", tuple(N * (HINGE_N + 0.07) + S * 0.11))
pl.check("vm_tome", (0, 0, 0))
mh.report_nodes(["Tome", "Pages", "Glove", "Emitter"])
mh.crystal_audit()
print("RWREPORT   SPINE_DIR blender (%.4f, %.4f, %.4f) = gltf/godot (%.4f, %.4f, %.4f)" % (S.x, S.y, S.z, S.x, S.z, -S.y))
rw.finish("vm_tome", "weapons", icon=False)

import wpn_icon  # noqa: E402
# the default side-on icon view sees the open book edge-on; look down onto the pages instead
wpn_icon.render("vm_tome", view=(-0.2, 0.6, 0.8))
mh.qa("vm_tome")
