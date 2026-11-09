"""rwui.py: shared GIMP 3 helpers for the RuneWire UI, VFX and icon generators.

The generator scripts (make_fx.py, make_ui.py, make_ui_logo.py, make_icons.py,
make_ui_previews.py) import this module. Run any of them headless from the project root:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_ui.py").read())' --quit

All image work happens inside GIMP: selections, fills, gradients, paths, brush strokes,
text layers and GEGL drawable filters. There is no Pillow or numpy here.

Conventions
- Coordinates are pixels, origin top-left, y down.
- Colours are '#rrggbb' strings (sRGB) or '#rrggbbaa' where alpha matters (gradient stops).
- Light comes from the top-left; shadows are cool-tinted, never pure black.
"""
import math
import os
import random

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gegl, Gimp, Gio  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI_DIR = os.path.join(ROOT, "assets", "textures", "ui")
FX_DIR = os.path.join(ROOT, "assets", "textures", "fx")
PREVIEW_DIR = os.path.join(ROOT, "art", "previews", "ui")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

REPLACE = Gimp.ChannelOps.REPLACE
ADD = Gimp.ChannelOps.ADD
SUB = Gimp.ChannelOps.SUBTRACT
INTER = Gimp.ChannelOps.INTERSECT

NORMAL = Gimp.LayerMode.NORMAL
MULTIPLY = Gimp.LayerMode.MULTIPLY
SCREEN = Gimp.LayerMode.SCREEN
OVERLAY = Gimp.LayerMode.OVERLAY
SOFTLIGHT = Gimp.LayerMode.SOFTLIGHT
HARDLIGHT = Gimp.LayerMode.HARDLIGHT
ADDITION = Gimp.LayerMode.ADDITION
LIGHTEN = Gimp.LayerMode.LIGHTEN_ONLY
DARKEN = Gimp.LayerMode.DARKEN_ONLY
ERASE = Gimp.LayerMode.ERASE

LINEAR = Gimp.GradientType.LINEAR
BILINEAR = Gimp.GradientType.BILINEAR
RADIAL = Gimp.GradientType.RADIAL
SQUARE = Gimp.GradientType.SQUARE
CONICAL = Gimp.GradientType.CONICAL_ASYMMETRIC
CONICAL_SYM = Gimp.GradientType.CONICAL_SYMMETRIC
BURST = Gimp.GradientType.SHAPEBURST_SPHERICAL
BURST_ANG = Gimp.GradientType.SHAPEBURST_ANGULAR
BURST_DIMPLED = Gimp.GradientType.SHAPEBURST_DIMPLED

TAU = math.tau

# Shared palette (cartoon fantasy-tech).
PAL = {
    "ink": "#24182f",          # outlines: deep violet-navy, never pure black
    "ink_soft": "#3a2a45",
    "shadow": "#140d24",       # drop shadows (cool)
    "brass_hi": "#fff2b8",
    "brass_lt": "#ffd77a",
    "brass": "#e3a83c",
    "brass_md": "#c8862a",
    "brass_dk": "#8f5420",
    "brass_xdk": "#5e3418",
    "gold_hi": "#fff6c2",
    "gold": "#ffcf3f",
    "gold_md": "#f2a516",
    "gold_dk": "#c0700e",
    "copper": "#e07a45",
    "copper_dk": "#a24a28",
    "steel_hi": "#f2f7fb",
    "steel": "#b8c6d3",
    "steel_md": "#8597aa",
    "steel_dk": "#56657a",
    "parch_hi": "#fff6dc",
    "parch": "#f4e2b6",
    "parch_md": "#e8cc94",
    "parch_dk": "#c99c5e",
    "parch_burn": "#a5713c",
    "slate_hi": "#4b5d80",
    "slate": "#2c3a55",
    "slate_md": "#222d44",
    "slate_dk": "#161e30",
    "teal_hi": "#c9fff6",
    "teal": "#3ff2d6",
    "teal_md": "#1fc2b4",
    "teal_dk": "#127a7a",
    "teal_xdk": "#0d4a55",
    "violet_hi": "#f0dcff",
    "violet": "#b07cff",
    "violet_md": "#8a4dff",
    "violet_dk": "#5326b8",
    "violet_xdk": "#2e1470",
    "orange": "#ff8a2a",
    "fire_y": "#ffe25a",
    "fire_o": "#ff9a1f",
    "fire_r": "#ef4a24",
    "fire_dk": "#9e1f1f",
    "red_hi": "#ffb0b8",
    "red": "#ff4762",
    "red_md": "#e0233f",
    "red_dk": "#9a1236",
    "green_hi": "#d9ffc8",
    "green": "#6ee86f",
    "green_md": "#2fbf5a",
    "green_dk": "#167a45",
    "blue_hi": "#d6f1ff",
    "blue": "#45b4ff",
    "blue_md": "#1f7cf0",
    "blue_dk": "#1747a8",
    "cyan_hi": "#e6ffff",
    "cyan": "#5ff4ff",
    "cyan_md": "#19c3f2",
    "cyan_dk": "#0b6fae",
    "wood_hi": "#f2bb76",
    "wood": "#d08a48",
    "wood_md": "#b06a34",
    "wood_dk": "#7a4224",
    "wood_xdk": "#4e2818",
    "white": "#ffffff",
}


# --------------------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------------------
def _parse(c):
    c = PAL.get(c, c)
    s = c.lstrip("#")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    a = int(s[6:8], 16) if len(s) >= 8 else 255
    return r, g, b, a


def hexa(c, a=None):
    """'#rrggbb' / palette key -> '#rrggbb' or '#rrggbbaa' (if alpha a given)."""
    r, g, b, aa = _parse(c)
    if a is None:
        a = aa / 255.0
    if a >= 0.999:
        return "#%02x%02x%02x" % (r, g, b)
    return "#%02x%02x%02x%02x" % (r, g, b, int(round(max(0.0, min(1.0, a)) * 255)))


def col(c, a=None):
    return Gegl.Color.new(hexa(c, a))


def mix(c1, c2, t):
    """Blend two colours in sRGB (fine for painterly palette mixing)."""
    a = _parse(c1)
    b = _parse(c2)
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# --------------------------------------------------------------------------------------
# Geometry helpers (pure python point lists)
# --------------------------------------------------------------------------------------
def flat(pts):
    out = []
    for x, y in pts:
        out.append(float(x))
        out.append(float(y))
    return out


def rot_pts(pts, ang, cx=0.0, cy=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def move_pts(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def scale_pts(pts, sx, sy=None, cx=0.0, cy=0.0):
    sy = sx if sy is None else sy
    return [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in pts]


def xform(pts, sx=1.0, sy=None, ang=0.0, dx=0.0, dy=0.0):
    """Scale about origin, rotate about origin, then translate."""
    sy = sx if sy is None else sy
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        x, y = x * sx, y * sy
        out.append((x * ca - y * sa + dx, x * sa + y * ca + dy))
    return out


def circle_pts(cx, cy, r, n=96, a0=0.0, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + TAU * i / n), cy + ry * math.sin(a0 + TAU * i / n)) for i in range(n)]


def arc_pts(cx, cy, r, a0, a1, n=48):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1)))
            for i in range(n)]


def catmull(pts, closed=True, samples=10, tension=0.5):
    """Catmull-Rom spline through pts -> dense polyline."""
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[min(i + 1, n - 1)]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def spline(pts, sharp=(), closed=True, samples=12, tension=1.0):
    """Cardinal (Hermite) spline through pts; indices in `sharp` get zero tangents (pointy tips)."""
    n = len(pts)
    sharp = set(sharp)

    def tangent(i):
        if i in sharp:
            return (0.0, 0.0)
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        return (0.5 * tension * (b[0] - a[0]), 0.5 * tension * (b[1] - a[1]))

    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        p1, p2 = pts[i], pts[(i + 1) % n]
        m1, m2 = tangent(i), tangent((i + 1) % n)
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            h00, h10, h01, h11 = 2 * t3 - 3 * t2 + 1, t3 - 2 * t2 + t, -2 * t3 + 3 * t2, t3 - t2
            out.append((h00 * p1[0] + h10 * m1[0] + h01 * p2[0] + h11 * m2[0],
                        h00 * p1[1] + h10 * m1[1] + h01 * p2[1] + h11 * m2[1]))
    if not closed:
        out.append(pts[-1])
    return out


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def bez(p0, p1, p2, p3, n=24, include_end=False):
    """Cubic Bezier p0..p3 -> n points (end excluded unless include_end)."""
    out = []
    m = n + (1 if include_end else 0)
    for i in range(m):
        t = i / n
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def gear_pts(cx, cy, r_root, r_tip, teeth, rot=0.0, tip=0.38, root=0.30, per_tooth=40):
    """Cartoon gear outline with soft trapezoid teeth."""
    pts = []
    flank = (1.0 - tip - root) / 2.0
    n = teeth * per_tooth
    for i in range(n):
        a = rot + TAU * i / n
        ph = (i % per_tooth) / per_tooth
        if ph < root / 2:
            r = r_root
        elif ph < root / 2 + flank:
            r = r_root + (r_tip - r_root) * smoothstep((ph - root / 2) / flank)
        elif ph < root / 2 + flank + tip:
            r = r_tip
        elif ph < 1 - root / 2:
            r = r_tip - (r_tip - r_root) * smoothstep((ph - root / 2 - flank - tip) / flank)
        else:
            r = r_root
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def star_pts(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sparkle_pts(cx, cy, rx, ry=None, pinch=2.6, n=4, rot=0.0, samples=256):
    """Four-point (or n-point) sparkle: superellipse-like astroid with concave sides."""
    ry = rx if ry is None else ry
    pts = []
    for i in range(samples):
        t = TAU * i / samples
        # |cos|^p, |sin|^p gives concave diamond (astroid when p=3)
        c, s = math.cos(t), math.sin(t)
        x = math.copysign(abs(c) ** pinch, c)
        y = math.copysign(abs(s) ** pinch, s)
        pts.append((x * rx, y * ry))
    if n != 4:
        raise ValueError("only n=4 supported")
    return [(cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)) for x, y in pts]


def heart_pts(cx, cy, size, samples=200):
    """Chubby cartoon heart, roughly size px wide, centred on (cx, cy)."""
    pts = []
    for i in range(samples):
        t = TAU * i / samples
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x, -y))
    # normalise to width 1
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs)
    my = (max(ys) + min(ys)) / 2
    return [(cx + x / w * size, cy + (y - my) / w * size) for x, y in pts]


# --------------------------------------------------------------------------------------
# Context
# --------------------------------------------------------------------------------------
def reset_context():
    Gimp.context_set_defaults()
    Gimp.context_set_antialias(True)
    Gimp.context_set_feather(False)
    Gimp.context_set_opacity(100.0)
    Gimp.context_set_paint_mode(NORMAL)
    try:
        Gimp.context_enable_dynamics(False)
    except Exception:
        pass
    Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
    Gimp.context_set_gradient_repeat_mode(Gimp.RepeatMode.NONE)
    Gimp.context_set_gradient_reverse(False)
    Gimp.context_set_stroke_method(Gimp.StrokeMethod.LINE)
    Gimp.context_set_line_cap_style(Gimp.CapStyle.ROUND)
    Gimp.context_set_line_join_style(Gimp.JoinStyle.ROUND)
    Gimp.context_set_line_width_unit(Gimp.Unit.pixel())


_grad_counter = [0]


# --------------------------------------------------------------------------------------
# Picture: an image plus drawing helpers
# --------------------------------------------------------------------------------------
class Pic:
    def __init__(self, w, h):
        reset_context()
        self.w, self.h = int(w), int(h)
        self.img = Gimp.Image.new(self.w, self.h, Gimp.ImageBaseType.RGB)

    # ---- layers ------------------------------------------------------------------------
    def layer(self, name="layer", opacity=100.0, mode=NORMAL, below=None, above=None, fill=None):
        """New full-canvas RGBA layer. `fill` paints the whole layer (ignores the selection)."""
        lay = Gimp.Layer.new(self.img, name, self.w, self.h, Gimp.ImageType.RGBA_IMAGE, float(opacity), mode)
        pos = 0
        if below is not None:
            pos = self.img.get_item_position(below) + 1
        elif above is not None:
            pos = self.img.get_item_position(above)
        self.img.insert_layer(lay, None, pos)
        if fill is None:
            lay.fill(Gimp.FillType.TRANSPARENT)
        else:
            Gimp.context_set_foreground(col(fill))
            lay.fill(Gimp.FillType.FOREGROUND)
        return lay

    def dup(self, lay, name=None, below=False):
        d = lay.copy()
        pos = self.img.get_item_position(lay) + (1 if below else 0)
        self.img.insert_layer(d, None, pos)
        if name:
            d.set_name(name)
        return d

    def merge_down(self, lay):
        return self.img.merge_down(lay, Gimp.MergeType.CLIP_TO_IMAGE)

    def merge_layers(self, layers, name=None):
        """Merge a list of layers (any order) into one, keeping others untouched."""
        hidden = []
        for l in self.img.get_layers():
            if l not in layers and l.get_visible():
                l.set_visible(False)
                hidden.append(l)
        for l in layers:
            l.set_visible(True)
        m = self.img.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
        for l in hidden:
            l.set_visible(True)
        if name:
            m.set_name(name)
        return m

    def merge_all(self, name="merged"):
        m = self.img.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
        m.set_name(name)
        return m

    def remove(self, lay):
        self.img.remove_layer(lay)

    # ---- selections --------------------------------------------------------------------
    def sel_none(self):
        Gimp.Selection.none(self.img)

    def sel_all(self):
        Gimp.Selection.all(self.img)

    def sel_ellipse(self, cx, cy, rx, ry=None, op=REPLACE):
        ry = rx if ry is None else ry
        self.img.select_ellipse(op, cx - rx, cy - ry, 2 * rx, 2 * ry)

    def sel_rect(self, x, y, w, h, op=REPLACE):
        self.img.select_rectangle(op, x, y, w, h)

    def sel_rrect(self, x, y, w, h, r, op=REPLACE):
        self.img.select_round_rectangle(op, x, y, w, h, r, r)

    def sel_poly(self, pts, op=REPLACE):
        self.img.select_polygon(op, flat(pts))

    def sel_layer(self, lay, op=REPLACE):
        self.img.select_item(op, lay)

    def sel_item(self, item, op=REPLACE):
        self.img.select_item(op, item)

    def grow(self, n):
        if n > 0:
            Gimp.Selection.grow(self.img, int(n))

    def shrink(self, n):
        if n > 0:
            Gimp.Selection.shrink(self.img, int(n))

    def feather(self, r):
        if r > 0:
            Gimp.Selection.feather(self.img, float(r))

    def border(self, r):
        Gimp.Selection.border(self.img, int(r))

    def translate_sel(self, dx, dy):
        Gimp.Selection.translate(self.img, int(round(dx)), int(round(dy)))

    def invert(self):
        pdb = Gimp.get_pdb()
        proc = pdb.lookup_procedure("gimp-selection-invert")
        cfg = proc.create_config()
        cfg.set_property("image", self.img)
        proc.run(cfg)

    def save_sel(self):
        return Gimp.Selection.save(self.img)

    def load_sel(self, ch, op=REPLACE):
        self.img.select_item(op, ch)

    def sel_bounds(self):
        r = Gimp.Selection.bounds(self.img)
        return r[2], r[3], r[4], r[5]

    def is_empty(self):
        return Gimp.Selection.is_empty(self.img)

    def round_sel(self, convex=0, concave=0):
        """Round convex corners (shrink, grow) and/or concave corners (grow, shrink)."""
        if convex:
            self.shrink(convex)
            self.grow(convex)
        if concave:
            self.grow(concave)
            self.shrink(concave)

    # ---- channels / masks built from shapes -----------------------------------------------
    def shape(self, fn):
        """Run a selection-building function and return the result as a saved channel."""
        fn()
        return self.save_sel()

    def crescent(self, ch, dx, dy, feather=0.0, keep_inside=True):
        """Selection = shape minus shape shifted by (-dx, -dy): the rim on the (dx, dy) side."""
        self.load_sel(ch)
        self.translate_sel(-dx, -dy)
        t = self.save_sel()
        self.load_sel(ch)
        self.load_sel(t, SUB)
        if feather:
            self.feather(feather)
            if keep_inside:
                self.load_sel(ch, INTER)
        self.img.remove_channel(t)

    # ---- painting ----------------------------------------------------------------------
    def fill(self, lay, c, opacity=100.0, mode=NORMAL):
        Gimp.context_set_foreground(col(c))
        Gimp.context_set_opacity(float(opacity))
        Gimp.context_set_paint_mode(mode)
        lay.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.context_set_opacity(100.0)
        Gimp.context_set_paint_mode(NORMAL)

    def clear(self, lay):
        lay.edit_clear()

    def grad(self, lay, stops, x1, y1, x2, y2, kind=LINEAR, opacity=100.0, mode=NORMAL,
             repeat=Gimp.RepeatMode.NONE, offset=0.0, segments=64):
        """Gradient fill of the current selection. stops: [(pos, colour[, alpha]), ...].

        The GIMP gradient is built from `segments` uniform segments whose end colours sample
        the piecewise-linear stop function (sRGB + alpha), so stops can sit anywhere."""
        _grad_counter[0] += 1
        g = Gimp.Gradient.new("rwui_tmp_%d_%d" % (os.getpid(), _grad_counter[0]))
        norm = []
        for s in stops:
            r, gg, b, a = _parse(s[1])
            if len(s) > 2:
                a = int(round(255 * s[2]))
            norm.append((float(s[0]), (r, gg, b, a)))
        norm.sort(key=lambda t: t[0])

        def sample(p):
            if p <= norm[0][0]:
                return norm[0][1]
            for i in range(len(norm) - 1):
                p0, c0 = norm[i]
                p1, c1 = norm[i + 1]
                if p <= p1:
                    t = 0.0 if p1 <= p0 else (p - p0) / (p1 - p0)
                    return tuple(c0[k] + (c1[k] - c0[k]) * t for k in range(4))
            return norm[-1][1]

        def gc(c):
            return Gegl.Color.new("#%02x%02x%02x%02x" % tuple(int(round(max(0, min(255, v)))) for v in c))

        g.segment_range_split_uniform(0, 0, segments)
        for i in range(segments):
            g.segment_set_left_color(i, gc(sample(i / segments)))
            g.segment_set_right_color(i, gc(sample((i + 1) / segments)))
        Gimp.context_set_gradient(g)
        Gimp.context_set_gradient_repeat_mode(repeat)
        Gimp.context_set_gradient_blend_color_space(Gimp.GradientBlendColorSpace.RGB_PERCEPTUAL)
        Gimp.context_set_opacity(float(opacity))
        Gimp.context_set_paint_mode(mode)
        lay.edit_gradient_fill(kind, float(offset), False, 1, 0.0, True, float(x1), float(y1), float(x2), float(y2))
        Gimp.context_set_opacity(100.0)
        Gimp.context_set_paint_mode(NORMAL)
        Gimp.context_set_gradient_repeat_mode(Gimp.RepeatMode.NONE)
        g.delete()

    def paint(self, lay, pts, size, c, brush="2. Hardness 075", opacity=100.0, mode=NORMAL, spacing=4.0):
        """Paintbrush stroke(s) through pts (list of (x, y)). A single point paints a dab."""
        Gimp.context_set_brush(Gimp.Brush.get_by_name(brush))
        Gimp.context_set_brush_size(float(size))
        Gimp.context_set_brush_spacing(float(spacing))
        Gimp.context_set_brush_aspect_ratio(0.0)
        Gimp.context_set_brush_angle(0.0)
        Gimp.context_set_foreground(col(c))
        Gimp.context_set_opacity(float(opacity))
        Gimp.context_set_paint_mode(mode)
        if len(pts) == 1:
            pts = [pts[0], (pts[0][0] + 0.01, pts[0][1])]
        Gimp.paintbrush_default(lay, flat(pts))
        Gimp.context_set_opacity(100.0)
        Gimp.context_set_paint_mode(NORMAL)

    def dab(self, lay, x, y, size, c, brush="2. Hardness 050", opacity=100.0, mode=NORMAL):
        self.paint(lay, [(x, y)], size, c, brush=brush, opacity=opacity, mode=mode)

    # ---- paths -------------------------------------------------------------------------
    def path(self, polylines, closed=False, name="path"):
        """polylines: list of point lists. Returns a Gimp.Path (inserted in image)."""
        p = Gimp.Path.new(self.img, name)
        self.img.insert_path(p, None, 0)
        for pts in polylines:
            if len(pts) < 2:
                continue
            sid = p.bezier_stroke_new_moveto(float(pts[0][0]), float(pts[0][1]))
            for x, y in pts[1:]:
                p.bezier_stroke_lineto(sid, float(x), float(y))
            if closed:
                p.stroke_close(sid)
        return p

    def stroke(self, lay, polylines, width, c, closed=False, opacity=100.0, mode=NORMAL,
               cap=Gimp.CapStyle.ROUND, join=Gimp.JoinStyle.ROUND):
        """Crisp antialiased vector stroke of polylines (list of point lists)."""
        p = self.path(polylines, closed)
        Gimp.context_set_stroke_method(Gimp.StrokeMethod.LINE)
        Gimp.context_set_line_width(float(width))
        Gimp.context_set_line_width_unit(Gimp.Unit.pixel())
        Gimp.context_set_line_cap_style(cap)
        Gimp.context_set_line_join_style(join)
        Gimp.context_set_foreground(col(c))
        Gimp.context_set_opacity(float(opacity))
        Gimp.context_set_paint_mode(mode)
        Gimp.context_set_antialias(True)
        lay.edit_stroke_item(p)
        Gimp.context_set_opacity(100.0)
        Gimp.context_set_paint_mode(NORMAL)
        self.img.remove_path(p)

    def stroke_selection(self, lay, width, c, opacity=100.0):
        Gimp.context_set_stroke_method(Gimp.StrokeMethod.LINE)
        Gimp.context_set_line_width(float(width))
        Gimp.context_set_foreground(col(c))
        Gimp.context_set_opacity(float(opacity))
        lay.edit_stroke_selection()
        Gimp.context_set_opacity(100.0)

    # ---- text --------------------------------------------------------------------------
    def text(self, s, font="Lilita One Regular", size=64, c="#ffffff", x=0, y=0, spacing=0.0):
        f = Gimp.Font.get_by_name(font)
        if f is None:
            raise RuntimeError("font not found: %s" % font)
        tl = Gimp.TextLayer.new(self.img, s, f, float(size), Gimp.Unit.pixel())
        self.img.insert_layer(tl, None, 0)
        tl.set_antialias(True)
        tl.set_hint_style(Gimp.TextHintStyle.NONE)
        tl.set_color(col(c))
        tl.set_letter_spacing(float(spacing))
        tl.set_offsets(int(x), int(y))
        return tl

    def text_to_layer(self, tl, c="#ffffff", name="text"):
        """Replace a text layer by a full-canvas layer filled with `c` through its alpha."""
        lay = self.layer(name, above=tl)
        self.sel_layer(tl)
        self.fill(lay, c)
        self.sel_none()
        self.img.remove_layer(tl)
        return lay

    # ---- filters -----------------------------------------------------------------------
    def fx(self, lay, op, **props):
        f = Gimp.DrawableFilter.new(lay, op, "")
        cfg = f.get_config()
        for k, v in props.items():
            cfg.set_property(k.replace("_", "-"), v)
        f.update()
        lay.merge_filter(f)

    def blur(self, lay, sx, sy=None):
        sy = sx if sy is None else sy
        if sx <= 0 and sy <= 0:
            return
        self.sel_none()
        self.fx(lay, "gegl:gaussian-blur", std_dev_x=float(sx), std_dev_y=float(sy))

    def motion_blur(self, lay, length, angle):
        self.sel_none()
        self.fx(lay, "gegl:motion-blur-linear", length=float(length), angle=float(angle))

    # ---- compound effects --------------------------------------------------------------------
    def outline(self, lay, width, c="ink", opacity=100.0, feather=0.0, name="outline"):
        """New layer below `lay` holding its silhouette grown by width px."""
        self.sel_layer(lay)
        self.grow(width)
        if feather:
            self.feather(feather)
        ol = self.layer(name, below=lay)
        self.fill(ol, c, opacity)
        self.sel_none()
        return ol

    def glow(self, lay, c, grow=4, blur=10, opacity=100.0, mode=NORMAL, name="glow", below=True):
        self.sel_layer(lay)
        self.grow(grow)
        g = self.layer(name, below=lay if below else None, above=None if below else lay, mode=mode)
        self.fill(g, c)
        self.sel_none()
        self.blur(g, blur)
        g.set_opacity(float(opacity))
        return g

    def drop_shadow(self, lay, dx=0, dy=6, blur=6, c="shadow", opacity=55.0, grow=0, name="shadow"):
        self.sel_layer(lay)
        if grow:
            self.grow(grow)
        sh = self.layer(name, below=lay)
        self.fill(sh, c)
        self.sel_none()
        self.blur(sh, blur)
        sh.set_offsets(int(dx), int(dy))
        sh.resize_to_image_size()
        sh.set_opacity(float(opacity))
        return sh

    def clip_to(self, lay, mask_item):
        """Clear everything in `lay` outside mask_item's alpha (a layer or channel)."""
        self.sel_item(mask_item)
        self.invert()
        lay.edit_clear()
        self.sel_none()

    def noise_layer(self, name="noise", scale=4.0, detail=3, seed=1, turbulent=False, opacity=30.0,
                    mode=OVERLAY, below=None, above=None, tileable=False):
        """Greyscale solid-noise layer (soft painterly variation)."""
        n = self.layer(name, mode=mode, opacity=opacity, below=below, above=above, fill="#808080")
        self.fx(n, "gegl:noise-solid", x_size=float(scale), y_size=float(scale), detail=int(detail),
                seed=int(seed), turbulent=turbulent, tileable=tileable, width=self.w, height=self.h)
        return n

    def lock_alpha(self, lay, on=True):
        lay.set_lock_alpha(on)

    # ---- output ------------------------------------------------------------------------
    def save(self, path, keep_transparent_rgb=False):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.sel_none()
        merged = self.img.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
        proc = Gimp.get_pdb().lookup_procedure("file-png-export")
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", self.img)
        cfg.set_property("file", Gio.File.new_for_path(path))
        for k, v in (("interlaced", False), ("compression", 9), ("bkgd", False), ("offs", False),
                     ("phys", False), ("time", False), ("save-transparent", keep_transparent_rgb),
                     ("include-exif", False), ("include-iptc", False), ("include-xmp", False),
                     ("include-color-profile", False), ("include-thumbnail", False),
                     ("include-comment", False)):
            try:
                cfg.set_property(k, v)
            except Exception:
                pass
        res = proc.run(cfg)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            raise RuntimeError("PNG export failed for %s: %s" % (path, status))
        return merged

    def close(self):
        self.img.delete()


def log(msg, path="/tmp/rwui_log.txt"):
    with open(path, "a") as fh:
        fh.write(str(msg) + "\n")


def run_all(funcs, only=None, logpath="/tmp/rwui_log.txt"):
    """Run generator functions; record failures without aborting the batch."""
    import traceback
    open(logpath, "w").close()
    for fn in funcs:
        if only and fn.__name__ not in only:
            continue
        try:
            fn()
            log("OK   %s" % fn.__name__, logpath)
        except Exception:
            log("FAIL %s\n%s" % (fn.__name__, traceback.format_exc()), logpath)


# --------------------------------------------------------------------------------------
# Rune glyphs (original designs). Unit box: x in [-0.5, 0.5], y in [-0.7, 0.7], y down.
#   ("l", [pts...])            polyline
#   ("c", cx, cy, r)            stroked circle
#   ("a", cx, cy, r, a0, a1)    stroked arc (radians, screen angles)
#   ("d", cx, cy, r)            filled dot
# --------------------------------------------------------------------------------------
def _spiral(cx, cy, r0, r1, turns, n=60, a0=0.0):
    return [(cx + (r0 + (r1 - r0) * i / (n - 1)) * math.cos(a0 + TAU * turns * i / (n - 1)),
             cy + (r0 + (r1 - r0) * i / (n - 1)) * math.sin(a0 + TAU * turns * i / (n - 1))) for i in range(n)]


def _wave(x0, x1, y, amp, periods, n=40):
    return [(x0 + (x1 - x0) * i / (n - 1), y + amp * math.sin(TAU * periods * i / (n - 1))) for i in range(n)]


GLYPHS = [
    [("l", [(-0.15, -0.7), (-0.15, 0.7)]), ("l", [(-0.15, -0.22), (0.36, -0.66)]), ("l", [(-0.15, 0.18), (0.36, -0.26)])],
    [("l", [(0, -0.7), (0, 0.7)]), ("l", [(-0.38, -0.3), (0, -0.7), (0.38, -0.3)]), ("l", [(-0.3, 0.36), (0.3, 0.36)])],
    [("l", [(0, 0.7), (0, 0.16)]), ("l", [(0, 0.16), (-0.36, -0.27), (0, -0.7), (0.36, -0.27), (0, 0.16)])],
    [("l", [(-0.36, -0.7), (0.36, -0.7), (-0.36, 0.7), (0.36, 0.7), (-0.36, -0.7)])],
    [("l", [(0, -0.42), (0, 0.7)]), ("l", [(-0.36, -0.7), (-0.36, -0.2), (0.36, -0.2), (0.36, -0.7)]), ("d", 0, -0.62, 0.1)],
    [("l", [(-0.32, -0.7), (0.32, -0.24), (-0.32, 0.22), (0.32, 0.7)])],
    [("c", 0, -0.32, 0.3), ("l", [(0, -0.02), (0, 0.7)]), ("d", 0, -0.32, 0.1)],
    [("l", [(-0.36, -0.7), (0, -0.14), (0.36, -0.7)]), ("l", [(0, -0.14), (0, 0.7)]), ("l", [(-0.3, 0.4), (0.3, 0.4)])],
    [("l", [(-0.36, -0.7), (0.36, -0.08)]), ("l", [(0.36, -0.7), (-0.36, -0.08)]), ("l", [(0, -0.39), (0, 0.7)])],
    [("a", 0.1, 0, 0.5, 1.05, 5.23), ("d", 0.12, 0, 0.11)],
    [("l", [(0, -0.7), (0.32, -0.35), (0, 0), (-0.32, -0.35), (0, -0.7)]), ("l", [(0, 0), (0.32, 0.35), (0, 0.7), (-0.32, 0.35), (0, 0)])],
    [("l", [(0, -0.7), (0, 0.7)]), ("l", [(-0.36, -0.7), (0, -0.3), (0.36, -0.7)]), ("l", [(-0.36, 0.7), (0, 0.3), (0.36, 0.7)])],
    [("l", [(0.32, -0.7), (-0.3, 0), (0.32, 0.7)]), ("l", [(-0.3, 0), (0.38, 0)])],
    [("l", [(0, -0.64), (0.42, 0.56), (-0.42, 0.56), (0, -0.64)]), ("d", 0, 0.18, 0.11)],
    [("l", [(0, -0.7), (0, 0.7)]), ("l", _wave(-0.42, 0.42, -0.2, 0.13, 1.5)), ("l", _wave(-0.42, 0.42, 0.25, 0.13, 1.5))],
    [("l", [(-0.3, -0.7), (-0.3, 0.7)]), ("l", [(-0.3, -0.68), (0.34, -0.36)]), ("l", [(-0.3, -0.14), (0.34, 0.18)]),
     ("l", [(-0.3, 0.4), (0.34, 0.7)])],
    [("l", _spiral(0, -0.2, 0.04, 0.38, 1.35, a0=0.6)), ("l", [(0, 0.18), (0, 0.7)])],
    [("a", 0, 0.42, 0.62, 3.83, 5.6), ("a", 0, -0.42, 0.62, 0.68, 2.46), ("d", 0, 0, 0.12)],
    [("l", [(-0.34, -0.46), (0.34, -0.46), (0.34, 0.5), (-0.34, 0.5), (-0.34, -0.46)]), ("l", [(-0.34, 0.5), (0.34, -0.46)]),
     ("l", [(0, -0.7), (0, -0.46)])],
    [("l", [(0, -0.7), (0, 0.7)]), ("a", 0, -0.5, 0.38, 0.0, math.pi)],
    [("l", [(-0.38, -0.2), (0, -0.62), (0.38, -0.2)]), ("l", [(-0.38, 0.32), (0, -0.1), (0.38, 0.32)]), ("l", [(0, -0.1), (0, 0.7)])],
    [("l", [(0, -0.62), (0, 0.62)]), ("l", [(-0.42, 0), (0.42, 0)]), ("c", 0, 0, 0.2)],
    [("c", 0, -0.46, 0.22), ("l", [(0, -0.24), (0, 0.7)]), ("l", [(0, 0.34), (0.28, 0.34)]), ("l", [(0, 0.6), (0.28, 0.6)])],
    [("l", [(-0.26, -0.7), (-0.26, 0.7)]), ("l", [(0.26, -0.7), (0.26, 0.7)]), ("l", [(-0.26, -0.34), (0.26, 0.34)])],
]


class GlyphBatch:
    """Collects transformed glyph strokes and dots, then draws them in two GIMP calls."""

    def __init__(self):
        self.lines = []
        self.dots = []

    def add(self, glyph, cx, cy, size, ang=0.0, flip=False):
        ca, sa = math.cos(ang), math.sin(ang)

        def T(x, y):
            if flip:
                x = -x
            x, y = x * size, y * size
            return (cx + x * ca - y * sa, cy + x * sa + y * ca)

        for el in glyph:
            kind = el[0]
            if kind == "l":
                self.lines.append([T(x, y) for x, y in el[1]])
            elif kind == "c":
                pts = circle_pts(el[1], el[2], el[3], n=40)
                pts.append(pts[0])
                self.lines.append([T(x, y) for x, y in pts])
            elif kind == "a":
                self.lines.append([T(x, y) for x, y in arc_pts(el[1], el[2], el[3], el[4], el[5], n=36)])
            elif kind == "d":
                x, y = T(el[1], el[2])
                self.dots.append((x, y, el[3] * size))

    def add_line(self, pts):
        self.lines.append(list(pts))

    def draw(self, pic, lay, width, c, dot_scale=1.0, opacity=100.0):
        if self.lines:
            pic.stroke(lay, self.lines, width, c, opacity=opacity)
        if self.dots:
            pic.sel_none()
            for x, y, r in self.dots:
                rr = max(r * dot_scale, width * 0.75)
                pic.sel_ellipse(x, y, rr, op=ADD)
            pic.fill(lay, c, opacity)
            pic.sel_none()


# --------------------------------------------------------------------------------------
# Material painters (operate on a saved shape channel)
# --------------------------------------------------------------------------------------
BRASS_STOPS = [(0.0, "#fff1b4"), (0.3, "#f7cd68"), (0.62, "#dc9634"), (1.0, "#a9621f")]
GOLD_STOPS = [(0.0, "#fff7c9"), (0.42, "#ffd856"), (0.56, "#f6ae22"), (1.0, "#c46a0e")]


def bevel(p, lay, ch, d=2, hi="#fff3c4", lo="#7e451b", hi_op=85.0, lo_op=60.0, feather=0.8):
    """Toon bevel: light rim on the top-left edges, dark rim on the bottom-right edges."""
    if hi:
        p.crescent(ch, -d, -d, feather=feather)
        p.fill(lay, hi, hi_op)
    if lo:
        p.crescent(ch, d, d, feather=feather)
        p.fill(lay, lo, lo_op)
    p.sel_none()


def brass(p, lay, ch, y0, y1, d=2, stops=None, hi="#fff6d2", lo="#7a4219", hi_op=85.0, lo_op=60.0, x0=None, x1=None):
    """Fill a shape with a brass gradient and bevel it."""
    p.load_sel(ch)
    if x0 is None:
        p.grad(lay, stops or BRASS_STOPS, 0, y0, 0, y1)
    else:
        p.grad(lay, stops or BRASS_STOPS, x0, y0, x1, y1)
    bevel(p, lay, ch, d, hi, lo, hi_op, lo_op)


def rivet(p, lay, x, y, r, ink="ink", stops=None):
    p.sel_ellipse(x, y, r + 1.4)
    p.fill(lay, ink)
    p.sel_ellipse(x, y, r)
    p.grad(lay, stops or [(0, "#fff6cf"), (0.45, "#eab04a"), (1, "#8a4b1a")], x - r * 0.7, y - r * 0.7,
           x + r * 0.8, y + r * 0.8)
    p.sel_ellipse(x - r * 0.32, y - r * 0.36, r * 0.36)
    p.fill(lay, "#ffffff", 85)
    p.sel_none()


def gem(p, lay, x, y, r, stops, rim="ink", hi="#ffffff", glow=None, glow_lay=None):
    p.sel_ellipse(x, y, r + 1.6)
    p.fill(lay, rim)
    p.sel_ellipse(x, y, r)
    p.grad(lay, stops, x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.9)
    p.sel_ellipse(x + r * 0.1, y + r * 0.15, r * 0.78)
    p.sel_ellipse(x - r * 0.1, y - r * 0.15, r * 0.8, op=SUB)
    p.feather(r * 0.15)
    p.fill(lay, "#ffffff", 30)
    p.sel_ellipse(x - r * 0.35, y - r * 0.38, r * 0.34, r * 0.26)
    p.fill(lay, hi, 95)
    p.sel_none()
    if glow and glow_lay is not None:
        p.sel_ellipse(x, y, r * 1.9)
        p.feather(r * 1.4)
        p.fill(glow_lay, glow, 70)
        p.sel_none()


def spark4(p, lay, x, y, r, c="#ffffff", opacity=100.0, pinch=3.0, rot=0.0):
    p.sel_poly(sparkle_pts(x, y, r, r, pinch=pinch, rot=rot))
    p.fill(lay, c, opacity)
    p.sel_none()
