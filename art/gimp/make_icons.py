"""make_icons.py: RuneWire spell and upgrade icons (assets/textures/ui/icon_*.png, 256x256).

Shared framing: the subject sits in a ~210 px box centred slightly above the middle, every part
has its own 3-4 px ink line, the whole silhouette gets a 6 px ink outline, spells get a soft
colour glow, and every icon gets the same soft drop shadow (0, +7 px).

Run from the project root:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_icons.py").read())' --quit

Optional: RW_ONLY="icon_spell_fireball,icon_upgrade_vitality" rebuilds a subset.
"""
import importlib
import math
import os
import random
import sys

sys.dont_write_bytecode = True  # keep art/gimp free of rwui .pyc files
sys.path.insert(0, os.path.join(os.getcwd(), "art", "gimp"))
import rwui as R  # noqa: E402

importlib.reload(R)
from rwui import Pic  # noqa: E402

S = 256
INK = "#24182f"
OUT = R.UI_DIR


class Icon:
    """Collects part layers, then outlines, glows and shadows them consistently."""

    def __init__(self):
        self.p = Pic(S, S)
        self.parts = []

    def part(self, name, ch, paint, ol=4):
        """Create a part painted by paint(layer, ch) with its own ink line below.

        Any helper layers the painter creates are merged into the part afterwards."""
        p = self.p
        before = set(l.get_id() for l in p.img.get_layers())
        lay = p.layer(name)
        paint(lay, ch)
        p.sel_none()
        new = [l for l in p.img.get_layers() if l.get_id() not in before]
        lay = p.merge_layers(new, name=name) if len(new) > 1 else new[0]
        if ol:
            line = p.layer(name + "_ol", below=lay)
            p.load_sel(ch)
            p.grow(ol)
            p.fill(line, INK)
            p.sel_none()
            self.parts += [line, lay]
        else:
            self.parts.append(lay)
        return lay

    def deco(self, name):
        lay = self.p.layer(name)
        self.parts.append(lay)
        return lay

    def finish(self, fname, glow=None, glow_op=70, outline=6, shadow=True):
        p = self.p
        subj = p.merge_layers(self.parts, name="subject")
        ol = p.outline(subj, outline, INK, name="outline")
        bottom = ol
        if glow:
            g = p.glow(ol, glow, grow=4, blur=11, opacity=glow_op, name="glow")
            bottom = g
        if shadow:
            p.drop_shadow(ol, 0, 7, 6, c="#140d24", opacity=55)
        p.save(os.path.join(OUT, fname))
        p.close()


def shape(p, fn):
    p.sel_none()
    fn()
    return p.save_sel()


def toon(p, lay, ch, stops, x0, y0, x1, y1, shade=None, shade_off=(9, 10), shade_op=80, hi="#ffffff",
         hi_off=(-4, -5), hi_op=70, kind=None, feather_shade=3):
    """Gradient fill + cool shadow band (bottom-right) + bright rim (top-left)."""
    p.load_sel(ch)
    if kind is None:
        p.grad(lay, stops, x0, y0, x1, y1)
    else:
        p.grad(lay, stops, x0, y0, x1, y1, kind=kind)
    if shade:
        p.crescent(ch, shade_off[0], shade_off[1], feather=feather_shade)
        p.fill(lay, shade, shade_op)
    if hi:
        p.crescent(ch, hi_off[0], hi_off[1], feather=1.5)
        p.fill(lay, hi, hi_op)
    p.sel_none()


def gloss(p, lay, ch, x, y, rx, ry, op=85, feather=2.0, ang=0.0):
    pts = R.xform(R.circle_pts(0, 0, 1, n=48), rx, ry, ang, x, y)
    p.sel_poly(pts)
    p.load_sel(ch, R.INTER)
    p.feather(feather)
    p.load_sel(ch, R.INTER)
    p.fill(lay, "#ffffff", op)
    p.sel_none()


# --------------------------------------------------------------------------------------
# Spells
# --------------------------------------------------------------------------------------
def comet_tail(cx, cy, r, length, ang, tips=((-1.0, -0.55), (-1.12, 0.05), (-0.9, 0.6))):
    """Tapered flame/comet tail behind a ball at (cx, cy) heading in direction ang."""
    L = length
    ctrl = [(r * 0.3, -r * 0.98), (-r * 0.6, -r * 1.02)]
    sharp = []
    for k, (tx, ty) in enumerate(tips):
        ctrl.append((tx * L, ty * r))
        sharp.append(len(ctrl) - 1)
        if k < len(tips) - 1:
            nx = (tx + tips[k + 1][0]) / 2 * L * 0.62
            ny = (ty + tips[k + 1][1]) / 2 * r
            ctrl.append((nx, ny))
    ctrl += [(-r * 0.6, r * 1.02), (r * 0.3, r * 0.98)]
    pts = R.spline(ctrl, sharp=sharp, closed=True, samples=14)
    return R.xform(pts, 1, 1, ang, cx, cy)


def icon_spell_arcane_bolt():
    ic = Icon()
    p = ic.p
    cx, cy, r = 150, 100, 52
    ang = math.radians(-38)
    tail = comet_tail(cx, cy, r * 0.92, 132, ang, tips=((-1.0, -0.5), (-1.15, 0.1), (-0.82, 0.62)))
    tail_ch = shape(p, lambda: p.sel_poly(tail))
    # tail: violet streaks fading toward the tips
    tx, ty = cx + 150 * math.cos(ang + math.pi), cy + 150 * math.sin(ang + math.pi)

    def paint_tail(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#4a1fa8"), (0.55, "#8a4dff"), (1, "#c9a0ff")], tx, ty, cx, cy)
        p.crescent(ch, 0, -5, feather=2)
        p.fill(lay, "#e7d2ff", 70)
        # inner streak
        inner = R.xform(R.spline([(0, -r * 0.45), (-110, -r * 0.1), (-60, r * 0.35), (0, r * 0.45)], sharp=(1,),
                                 closed=True, samples=12), 1, 1, ang, cx, cy)
        p.sel_poly(inner)
        p.feather(4)
        p.load_sel(ch, R.INTER)
        p.fill(lay, "#f0e2ff", 55)

    ic.part("tail", tail_ch, paint_tail, ol=4)
    orb_ch = shape(p, lambda: p.sel_ellipse(cx, cy, r))

    def paint_orb(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#fff4ff"), (0.25, "#e2bcff"), (0.6, "#a066ff"), (1, "#4c1db0")], cx - r * 0.45,
               cy - r * 0.5, cx - r * 0.45 + r * 1.7, cy - r * 0.5, kind=R.RADIAL)
        p.crescent(ch, 9, 10, feather=4)
        p.fill(lay, "#3a1288", 55)
        # swirl
        sw = R._spiral(cx + 4, cy + 4, 6, r * 0.62, 1.15, n=60, a0=2.4)
        p.load_sel(ch)
        p.stroke(lay, [sw], 6, "#f6eaff", opacity=85)
        p.sel_none()
        gloss(p, lay, ch, cx - r * 0.38, cy - r * 0.42, r * 0.3, r * 0.2, op=95, ang=-0.6)
        p.sel_ellipse(cx + r * 0.5, cy + r * 0.32, r * 0.08)
        p.fill(lay, "#ffffff", 80)
        p.sel_none()

    orb = ic.part("orb", orb_ch, paint_orb, ol=4)
    sp = ic.deco("sparks")
    for (x, y, rr_) in ((62, 196, 15), (40, 150, 9), (104, 214, 8), (196, 50, 9)):
        R.spark4(p, sp, x, y, rr_, "#ffffff", 100)
    for (x, y, rr_) in ((80, 168, 4.5), (58, 226, 3.5), (122, 186, 3)):
        p.sel_ellipse(x, y, rr_)
        p.fill(sp, "#f0dcff")
    p.sel_none()
    ic.finish("icon_spell_arcane_bolt.png", glow="#a368ff", glow_op=80)


def icon_spell_fireball():
    ic = Icon()
    p = ic.p
    cx, cy, r = 156, 98, 52
    ang = math.radians(-38)
    layers = [
        ("outer", 1.0, (-1.0, -0.6), [(0, "#ffb347"), (0.5, "#f4561f"), (1, "#b81f1f")]),
        ("mid", 0.78, (-0.82, -0.4), [(0, "#ffe680"), (0.6, "#ff9a1f"), (1, "#f0641c")]),
        ("inner", 0.55, (-0.66, -0.2), [(0, "#fffbe0"), (0.6, "#ffe25a"), (1, "#ffb52a")]),
    ]
    for k, (name, s, _, stops) in enumerate(layers):
        rr_ = r * s
        ccx = cx - (1 - s) * r * 0.55 * math.cos(ang) + (1 - s) * 6
        ccy = cy - (1 - s) * r * 0.55 * math.sin(ang) + (1 - s) * 10
        tail = comet_tail(ccx, ccy, rr_, 124 * s, ang, tips=((-1.0, -0.62), (-1.18, 0.05), (-0.86, 0.66)))

        def build(ccx=ccx, ccy=ccy, rr_=rr_, tail=tail):
            p.sel_ellipse(ccx, ccy, rr_)
            p.sel_poly(tail, op=R.ADD)

        ch = shape(p, build)

        def paint(lay, ch, stops=stops, ccx=ccx, ccy=ccy, rr_=rr_, k=k):
            p.load_sel(ch)
            p.grad(lay, stops, ccx - rr_ * 0.3, ccy - rr_ * 0.3, ccx - rr_ * 0.3 + rr_ * 2.6, ccy - rr_ * 0.3,
                   kind=R.RADIAL)
            if k == 0:
                p.crescent(ch, 8, 9, feather=3)
                p.fill(lay, "#8e1414", 55)
            p.crescent(ch, -3, -4, feather=1.5)
            p.fill(lay, "#fff3c0", 70 if k else 55)

        ic.part(name, ch, paint, ol=(4 if k == 0 else 0))
    # hot core highlight
    core = ic.deco("core")
    p.sel_ellipse(cx - 8, cy - 8, 22, 18)
    p.feather(8)
    p.fill(core, "#ffffff", 90)
    p.sel_none()
    gl = ic.deco("gloss")
    p.sel_poly(R.xform(R.circle_pts(0, 0, 1, n=40), 14, 8, -0.7, cx - 26, cy - 34))
    p.feather(1.5)
    p.fill(gl, "#ffffff", 85)
    p.sel_none()
    em = ic.deco("embers")
    rng = random.Random(4)
    for (x, y, rr_) in ((58, 168, 7), (44, 204, 5), (96, 218, 6), (76, 136, 4), (204, 160, 4.5), (124, 36, 4)):
        p.sel_ellipse(x, y, rr_ + 2.5)
        p.fill(em, INK)
        p.sel_ellipse(x, y, rr_)
        p.fill(em, "#ffb02e")
        p.sel_ellipse(x - rr_ * 0.3, y - rr_ * 0.3, rr_ * 0.45)
        p.fill(em, "#fff3b0")
    p.sel_none()
    ic.finish("icon_spell_fireball.png", glow="#ff8a2a", glow_op=75)


def icon_spell_chain_lightning():
    ic = Icon()
    p = ic.p
    def fit(pts):
        return [(128 + (x - 136) * 0.9, 132 + (y - 125) * 0.9) for x, y in pts]

    bolt = fit([(132, 14), (184, 14), (150, 96), (190, 96), (104, 236), (122, 132), (82, 132)])
    bch = shape(p, lambda: (p.sel_poly(bolt), p.round_sel(convex=3)))
    # forks (strokes) ending in chain nodes
    forks = [
        fit([(110, 120), (78, 146), (88, 166), (48, 196)]),
        fit([(168, 104), (196, 124), (184, 146), (218, 172)]),
    ]
    nodes = [fit([(42, 202)])[0] + (15,), fit([(224, 178)])[0] + (15,)]
    fl = p.layer("forks_tmp")
    p.stroke(fl, forks, 15, "#ffffff", join=R.Gimp.JoinStyle.MITER)
    p.sel_layer(fl)
    fch = p.save_sel()
    p.remove(fl)

    def paint_fork(lay, ch):
        p.load_sel(ch)
        p.fill(lay, "#2fd9f5")
        p.sel_none()
        p.stroke(lay, forks, 5, "#effeff", join=R.Gimp.JoinStyle.MITER)

    ic.part("forks", fch, paint_fork, ol=4)
    ndch = shape(p, lambda: [p.sel_ellipse(x, y, rr_, op=R.ADD) for x, y, rr_ in nodes])

    def paint_nodes(lay, ch):
        for x, y, rr_ in nodes:
            p.sel_ellipse(x, y, rr_)
            p.grad(lay, [(0, "#ffffff"), (0.35, "#b8fbff"), (0.75, "#2fd9f5"), (1, "#0b74b8")], x - 4, y - 4,
                   x - 4 + rr_ * 1.4, y - 4, kind=R.RADIAL)
            p.sel_ellipse(x - rr_ * 0.35, y - rr_ * 0.38, rr_ * 0.3, rr_ * 0.22)
            p.fill(lay, "#ffffff", 95)
        p.sel_none()

    ic.part("nodes", ndch, paint_nodes, ol=4)

    def paint_bolt(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#e9ffff"), (0.35, "#7cf2ff"), (0.75, "#19c3f2"), (1, "#0b6fae")], 120, 24, 150, 228)
        p.crescent(ch, 8, 6, feather=2)
        p.fill(lay, "#0a5a96", 70)
        p.crescent(ch, -4, -3, feather=1.2)
        p.fill(lay, "#ffffff", 90)
        # inner white core streak
        core = fit([(150, 30), (166, 30), (138, 104), (164, 104), (116, 196), (126, 124), (104, 124)])
        p.sel_poly(core)
        p.feather(2.5)
        p.load_sel(ch, R.INTER)
        p.fill(lay, "#ffffff", 75)
        p.sel_none()

    ic.part("bolt", bch, paint_bolt, ol=4)
    sp = ic.deco("sparks")
    for (x, y, rr_) in ((206, 46, 12), (56, 76, 9), (226, 214, 7), (28, 158, 6)):
        R.spark4(p, sp, x, y, rr_, "#ffffff", 100)
    ic.finish("icon_spell_chain_lightning.png", glow="#2fd9f5", glow_op=80)


def icon_spell_mending_ward():
    ic = Icon()
    p = ic.p
    cx, cy = 128, 122
    R_out, R_in = 100, 82
    ring_ch = shape(p, lambda: (p.sel_ellipse(cx, cy, R_out), p.sel_ellipse(cx, cy, R_in, op=R.SUB)))
    disc_ch = shape(p, lambda: p.sel_ellipse(cx, cy, R_in))

    def paint_disc(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#eaffd6"), (0.35, "#7ff07a"), (0.75, "#2fbf5a"), (1, "#14743f")], cx, cy - 10, cx + R_in,
               cy - 10, kind=R.RADIAL)
        p.crescent(ch, -7, -8, feather=4)
        p.fill(lay, "#0c4a2c", 55)
        # glyph band (gold runes on the green field)
        band = R.GlyphBatch()
        n = 12
        for i in range(n):
            a = -math.pi / 2 + math.tau * (i + 0.5) / n
            band.add(R.GLYPHS[(i * 5 + 1) % len(R.GLYPHS)], cx + 66 * math.cos(a), cy + 66 * math.sin(a), 16,
                     ang=a + math.pi / 2)
        p.load_sel(ch)
        band.draw(p, lay, 3.2, "#fff2a8")
        # inner ring line
        pts = R.circle_pts(cx, cy, 52, n=120)
        p.stroke(lay, [pts + [pts[0]]], 3.5, "#fff2a8", opacity=90)

    ic.part("disc", disc_ch, paint_disc, ol=0)

    def paint_ring(lay, ch):
        R.brass(p, lay, ch, cy - R_out, cy + R_out, d=3, stops=R.GOLD_STOPS, hi="#fffbe6", lo="#8a4a0c",
                hi_op=95, lo_op=70)
        # engraved centre line
        p.sel_ellipse(cx, cy, (R_out + R_in) / 2 + 1)
        p.sel_ellipse(cx, cy, (R_out + R_in) / 2 - 1, op=R.SUB)
        p.fill(lay, "#b8700f", 60)
        p.sel_none()

    ic.part("ring", ring_ch, paint_ring, ol=4)
    # four ward nodes on the ring
    nodes_ch = shape(p, lambda: [p.sel_ellipse(cx + 91 * math.cos(a), cy + 91 * math.sin(a), 13, op=R.ADD)
                                 for a in (-math.pi / 2, 0, math.pi / 2, math.pi)])

    def paint_nodes(lay, ch):
        for a in (-math.pi / 2, 0, math.pi / 2, math.pi):
            x, y = cx + 91 * math.cos(a), cy + 91 * math.sin(a)
            R.gem(p, lay, x, y, 11, [(0, "#f2ffe0"), (0.45, "#6ee86f"), (1, "#167a45")], rim=INK)

    ic.part("nodes", nodes_ch, paint_nodes, ol=0)
    # central healing cross
    def cross():
        p.sel_rrect(cx - 15, cy - 42, 30, 84, 9)
        p.sel_rrect(cx - 42, cy - 15, 84, 30, 9, op=R.ADD)

    cr_ch = shape(p, cross)

    def paint_cross(lay, ch):
        toon(p, lay, ch, [(0, "#ffffff"), (0.5, "#e6ffd6"), (1, "#9fe58a")], cx - 40, cy - 40, cx + 40, cy + 40,
             shade="#4fb35a", shade_off=(5, 6), shade_op=75, hi="#ffffff", hi_op=90)

    ic.part("cross", cr_ch, paint_cross, ol=4)
    sp = ic.deco("sparks")
    for (x, y, rr_, c) in ((208, 36, 13, "#ffffff"), (40, 52, 9, "#fff6c2"), (222, 196, 8, "#e6ffd6"),
                           (30, 200, 7, "#ffffff")):
        R.spark4(p, sp, x, y, rr_, c, 100)
    ic.finish("icon_spell_mending_ward.png", glow="#6ee86f", glow_op=75)


# --------------------------------------------------------------------------------------
# Upgrades
# --------------------------------------------------------------------------------------
def icon_upgrade_vitality():
    ic = Icon()
    p = ic.p
    cx, cy = 128, 124
    heart = R.heart_pts(cx, cy, 214)
    hch = shape(p, lambda: (p.sel_poly(heart), p.round_sel(concave=4)))

    def paint(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#ff9aa8"), (0.3, "#ff4d63"), (0.7, "#e0233f"), (1, "#a4153a")], cx - 70, cy - 80,
               cx + 60, cy + 90)
        p.crescent(ch, 14, 16, feather=5)
        p.fill(lay, "#8a1036", 60)
        p.crescent(ch, -5, -6, feather=1.5)
        p.fill(lay, "#ffd1d8", 85)
        gloss(p, lay, ch, cx - 52, cy - 46, 26, 16, op=95, ang=-0.6)
        gloss(p, lay, ch, cx - 20, cy - 60, 7, 5, op=90)
        gloss(p, lay, ch, cx + 54, cy - 50, 12, 7, op=55, ang=0.5)

    ic.part("heart", hch, paint, ol=0)
    sp = ic.deco("sparks")
    R.spark4(p, sp, 214, 46, 13, "#ffffff", 100)
    R.spark4(p, sp, 40, 196, 7, "#ffe0e5", 95)
    ic.finish("icon_upgrade_vitality.png")


def icon_upgrade_arcana():
    ic = Icon()
    p = ic.p
    cx, cy = 128, 122
    pts = []
    for i in range(16):
        a = -math.pi / 2 + math.pi * i / 8
        r = (108 if i % 4 == 0 else 74) if i % 2 == 0 else 46
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    sch = shape(p, lambda: (p.sel_poly(pts), p.round_sel(convex=5, concave=2)))

    def paint(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#f3e6ff"), (0.3, "#b98cff"), (0.7, "#7c3cf0"), (1, "#3e1499")], cx - 90, cy - 100,
               cx + 90, cy + 100)
        # facets: clockwise half of each point darker
        p.sel_none()
        for i in range(0, 16, 2):
            tip = pts[i]
            nxt = pts[(i + 1) % 16]
            p.sel_poly([(cx, cy), tip, nxt], op=R.ADD)
        p.feather(1.0)
        p.load_sel(ch, R.INTER)
        p.fill(lay, "#4a1aa8", 45)
        p.crescent(ch, 6, 7, feather=2)
        p.fill(lay, "#2c0c78", 55)
        p.crescent(ch, -3, -4, feather=1.2)
        p.fill(lay, "#ffffff", 80)
        p.sel_none()

    ic.part("star", sch, paint, ol=0)
    med_ch = shape(p, lambda: p.sel_ellipse(cx, cy, 38))

    def paint_med(lay, ch):
        R.brass(p, lay, ch, cy - 38, cy + 38, d=2, stops=R.GOLD_STOPS, hi="#fffbe6", lo="#8a4a0c")
        p.sel_ellipse(cx, cy, 28)
        inner = p.save_sel()
        p.grad(lay, [(0, "#4ff5dc"), (0.6, "#14857f"), (1, "#0b3f4a")], cx, cy, cx + 28, cy, kind=R.RADIAL)
        p.crescent(inner, -3, -3, feather=1.5)
        p.fill(lay, "#062a30", 60)
        p.sel_none()
        gb = R.GlyphBatch()
        gb.add(R.GLYPHS[4], cx, cy, 32)
        gl = p.layer("rune")
        gb.draw(p, gl, 4.0, "#e9fffb")
        p.glow(gl, "#3ff2d6", grow=1, blur=3, opacity=90)

    ic.part("medallion", med_ch, paint_med, ol=4)
    sp = ic.deco("sparks")
    R.spark4(p, sp, 210, 40, 12, "#ffffff", 100)
    R.spark4(p, sp, 46, 200, 8, "#efe2ff", 95)
    ic.finish("icon_upgrade_arcana.png", glow="#a368ff", glow_op=55)


def icon_upgrade_engineering():
    ic = Icon()
    p = ic.p
    gx, gy = 112, 116
    gear_ch = shape(p, lambda: (p.sel_poly(R.gear_pts(gx, gy, 64, 82, 10, rot=0.15, per_tooth=36)),
                                p.sel_ellipse(gx, gy, 24, op=R.SUB)))

    def paint_gear(lay, ch):
        R.brass(p, lay, ch, gy - 82, gy + 82, d=3, stops=R.BRASS_STOPS, hi="#fff6d2", lo="#7a4219", hi_op=90,
                lo_op=70)
        p.crescent(ch, 9, 10, feather=4)
        p.fill(lay, "#7a4219", 35)
        p.sel_ellipse(gx, gy, 44)
        p.sel_ellipse(gx, gy, 38, op=R.SUB)
        p.load_sel(ch, R.INTER)
        p.fill(lay, "#a8641f", 70)
        p.sel_none()
        for k in range(6):
            a = math.tau * k / 6 + 0.3
            R.rivet(p, lay, gx + 52 * math.cos(a), gy + 52 * math.sin(a), 3.4, ink="#5e3418")

    ic.part("gear", gear_ch, paint_gear, ol=4)
    # wrench, built along +x then rotated
    ang = math.radians(-45)
    wx, wy = 134, 134

    def wrench_sel():
        p.sel_poly(R.xform([(-92, -15), (52, -15), (52, 15), (-92, 15)], 1, 1, ang, wx, wy))
        p.sel_poly(R.xform(R.circle_pts(0, 0, 36, n=64), 1, 1, ang, wx + 74 * math.cos(ang), wy + 74 * math.sin(ang)),
                   op=R.ADD)
        p.sel_poly(R.xform(R.circle_pts(0, 0, 25, n=64), 1, 1, ang, wx - 96 * math.cos(ang), wy - 96 * math.sin(ang)),
                   op=R.ADD)
        # open jaw
        p.sel_poly(R.xform([(74, -13), (130, -16), (130, 16), (74, 13)], 1, 1, ang, wx, wy), op=R.SUB)
        p.sel_poly(R.xform(R.circle_pts(74, 0, 14, n=40), 1, 1, ang, wx, wy), op=R.SUB)
        # ring hole at the tail
        p.sel_poly(R.xform(R.circle_pts(-96, 0, 10, n=40), 1, 1, ang, wx, wy), op=R.SUB)
        p.round_sel(convex=3, concave=3)

    wch = shape(p, wrench_sel)

    def paint_wrench(lay, ch):
        toon(p, lay, ch, [(0, "#ffffff"), (0.35, "#d7e2ec"), (0.7, "#9fb0c2"), (1, "#5d6d82")], 60, 60, 200, 200,
             shade="#46546a", shade_off=(6, 7), shade_op=70, hi="#ffffff", hi_op=95)
        # engraved groove along the handle
        groove = R.xform([(-70, 0), (40, 0)], 1, 1, ang, wx, wy)
        p.stroke(lay, [groove], 5, "#6b7c92", opacity=85)
        p.stroke(lay, [R.move_pts(groove, -1.5, -1.5)], 2, "#ffffff", opacity=60)

    ic.part("wrench", wch, paint_wrench, ol=4)
    sp = ic.deco("sparks")
    R.spark4(p, sp, 214, 42, 12, "#ffffff", 100)
    ic.finish("icon_upgrade_engineering.png")


def crate(p, ic, name, x, y, s):
    """Front-facing cartoon crate (s px square) at top-left (x, y)."""
    ch = shape(p, lambda: p.sel_rrect(x, y, s, s, 7))

    def paint(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#f0b36c"), (0.5, "#d08a48"), (1, "#a8642f")], x, y, x + s, y + s)
        # recessed plank panel
        b = max(10, s * 0.15)
        p.sel_rect(x + b, y + b, s - 2 * b, s - 2 * b)
        inner = p.save_sel()
        p.grad(lay, [(0, "#c47b3c"), (1, "#8f5226")], x, y + b, x, y + s - b)
        # plank seams
        seams = []
        for k in (1, 2):
            yy = y + b + (s - 2 * b) * k / 3
            seams.append([(x + b, yy), (x + s - b, yy)])
        p.load_sel(inner)
        p.stroke(lay, seams, 2.5, "#5e3018", opacity=85)
        p.crescent(inner, -4, -4, feather=1.5)
        p.fill(lay, "#5e3018", 55)
        # diagonal brace
        brace = [(x + b, y + s - b - 10), (x + b, y + s - b), (x + b + 10, y + s - b), (x + s - b, y + b + 10),
                 (x + s - b, y + b), (x + s - b - 10, y + b)]
        p.sel_poly(brace)
        p.load_sel(inner, R.INTER)
        br = p.save_sel()
        p.grow(2)
        p.load_sel(inner, R.INTER)
        p.fill(lay, "#4e2818")
        p.load_sel(br)
        p.grad(lay, [(0, "#f3be7a"), (1, "#c27a3c")], x, y, x + s, y + s)
        p.crescent(br, 0, 3, feather=1)
        p.fill(lay, "#7a4224", 50)
        # frame bevel
        p.load_sel(ch)
        p.load_sel(inner, R.SUB)
        fr = p.save_sel()
        p.load_sel(inner)
        p.grow(2)
        p.load_sel(inner, R.SUB)
        p.fill(lay, "#4e2818", 90)
        R.bevel(p, lay, fr, d=3, hi="#ffd9a0", lo="#6e3a1c", hi_op=85, lo_op=65)
        # brass corner brackets + rivets
        c = s * 0.2
        for (ax, ay, sx, sy) in ((x, y, 1, 1), (x + s, y, -1, 1), (x, y + s, 1, -1), (x + s, y + s, -1, -1)):
            tri = [(ax, ay), (ax + sx * c, ay), (ax, ay + sy * c)]
            p.sel_poly(tri)
            p.load_sel(ch, R.INTER)
            cb = p.save_sel()
            p.load_sel(cb)
            p.grow(2)
            p.load_sel(ch, R.INTER)
            p.fill(lay, INK)
            p.load_sel(cb)
            p.grad(lay, R.BRASS_STOPS, ax, ay, ax + sx * c, ay + sy * c)
            p.sel_none()
            R.rivet(p, lay, ax + sx * c * 0.32, ay + sy * c * 0.32, 2.6, ink="#5e3418")

    return ic.part(name, ch, paint, ol=4)


def icon_upgrade_capacity():
    ic = Icon()
    p = ic.p
    s = 96
    crate(p, ic, "crate_bl", 22, 132, s)
    crate(p, ic, "crate_br", 138, 132, s)
    crate(p, ic, "crate_top", 76, 32, s + 8)
    sp = ic.deco("sparks")
    R.spark4(p, sp, 214, 46, 12, "#ffffff", 100)
    ic.finish("icon_upgrade_capacity.png")


def icon_upgrade_mana_regen():
    ic = Icon()
    p = ic.p
    cx, cy, r = 124, 152, 74
    ctrl = [(cx, 22), (cx + 46, 82), (cx + r, cy - 6), (cx + r * 0.72, cy + r * 0.72), (cx, cy + r),
            (cx - r * 0.72, cy + r * 0.72), (cx - r, cy - 6), (cx - 46, 82)]
    drop = R.spline(ctrl, sharp=(0,), closed=True, samples=20)
    dch = shape(p, lambda: p.sel_poly(drop))

    def paint(lay, ch):
        p.load_sel(ch)
        p.grad(lay, [(0, "#d6f1ff"), (0.25, "#6cc6ff"), (0.6, "#2a86f2"), (1, "#1747a8")], cx - 50, 50, cx + 50,
               cy + r)
        p.crescent(ch, 14, 14, feather=5)
        p.fill(lay, "#13308a", 60)
        p.crescent(ch, -5, -4, feather=1.5)
        p.fill(lay, "#e6f8ff", 85)
        # curved reflection along the left side
        refl = R.spline([(cx - 50, cy - 18), (cx - 38, cy - 52), (cx - 22, cy - 72), (cx - 30, cy - 40),
                         (cx - 40, cy - 8)], sharp=(0, 2), closed=True, samples=12)
        p.sel_poly(refl)
        p.feather(1.5)
        p.load_sel(ch, R.INTER)
        p.fill(lay, "#ffffff", 90)
        gloss(p, lay, ch, cx - 44, cy + 6, 7, 9, op=90)
        # inner bubbles
        for (bx, by, br) in ((cx + 26, cy + 26, 9), (cx + 4, cy + 48, 5), (cx + 40, cy - 6, 4)):
            p.sel_ellipse(bx, by, br)
            p.sel_ellipse(bx + 1.5, by + 1.5, br * 0.75, op=R.SUB)
            p.fill(lay, "#bfe8ff", 80)
        p.sel_none()

    ic.part("drop", dch, paint, ol=0)
    sp = ic.deco("sparks")
    R.spark4(p, sp, 196, 64, 22, "#ffffff", 100)
    R.spark4(p, sp, 222, 112, 9, "#d6f1ff", 100)
    R.spark4(p, sp, 40, 70, 7, "#ffffff", 95)
    ic.finish("icon_upgrade_mana_regen.png", glow="#45b4ff", glow_op=45)


ALL = [icon_spell_arcane_bolt, icon_spell_fireball, icon_spell_chain_lightning, icon_spell_mending_ward,
       icon_upgrade_vitality, icon_upgrade_arcana, icon_upgrade_engineering, icon_upgrade_capacity,
       icon_upgrade_mana_regen]
_only = [s for s in os.environ.get("RW_ONLY", "").split(",") if s]
R.run_all(ALL, only=_only or None, logpath="/tmp/rwui_icons_log.txt")
