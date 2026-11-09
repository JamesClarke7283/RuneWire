"""rwtex: RuneWire hand-painted texture toolkit for GIMP 3 (python-fu batch mode).

All image work happens inside GIMP: layers, blend modes, selections and fills,
paintbrush strokes and GEGL filters (through Gimp.DrawableFilter).  Python only
computes layouts (bricks, planks, Voronoi cells, stroke paths), lookup tables
and a few per-pixel combinations on GEGL buffers read from GIMP drawables.

Everything is seamless by construction:
  * shapes and strokes that cross an edge are drawn again on the opposite side,
  * neighbourhood filters (blur, distance transform, ...) run on a copy padded
    with wrapped pixels (Gegl.AbyssPolicy.LOOP) and the centre is copied back,
  * noise comes from tileable generators (gegl:noise-solid tileable=True).

Run from the project root with
  env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
      -b 'exec(open("art/gimp/make_materials.py").read())' --quit
"""
import gi
import os
import math
import random
import time
import array
import colorsys

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, Gio  # noqa: E402

ROOT = os.environ.get("RW_ROOT") or os.getcwd()
TEX_DIR = os.path.join(ROOT, "assets", "textures")
PREVIEW_DIR = os.path.join(ROOT, "art", "previews", "textures")

PREC = Gimp.Precision.FLOAT_NON_LINEAR  # work precision: float, perceptual (sRGB-encoded) values
LM = Gimp.LayerMode
REPLACE = Gimp.ChannelOps.REPLACE
ADD = Gimp.ChannelOps.ADD
SUBTRACT = Gimp.ChannelOps.SUBTRACT
NONE = Gegl.AbyssPolicy.NONE
LOOP = Gegl.AbyssPolicy.LOOP
FG = Gimp.FillType.FOREGROUND

# Light used for baked shading: from the upper left.  OpenGL tangent space
# (x right, y up), so "up" is +y here even though image rows grow downward.
LIGHT = (-0.55, 0.62, 0.56)


def log(*a):
    print("[rwtex]", *a, flush=True)


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0)) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# --------------------------------------------------------------------------
# colour helpers (sRGB-encoded floats 0..1)
# --------------------------------------------------------------------------

def rgb(c):
    if isinstance(c, (tuple, list)):
        return tuple(float(v) for v in c[:3])
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(clamp(v) * 255)) for v in rgb(c))


def gcol(c):
    return Gegl.Color.new(hexc(c))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(c, f):
    return tuple(clamp(v * f) for v in rgb(c))


def hsv_adj(c, dh=0.0, ds=0.0, dv=0.0):
    """Shift hue by dh (turns), scale saturation by (1+ds) and value by (1+dv)."""
    h, s, v = colorsys.rgb_to_hsv(*rgb(c))
    return colorsys.hsv_to_rgb((h + dh) % 1.0, clamp(s * (1 + ds)), clamp(v * (1 + dv)))


def jitter(c, rng, h=0.015, s=0.08, v=0.07):
    return hsv_adj(c, rng.uniform(-h, h), rng.uniform(-s, s), rng.uniform(-v, v))


def ramp_luts(stops):
    """stops: [(t, colour)] -> three 256-byte lookup tables (R, G, B)."""
    st = sorted((float(t), rgb(c)) for t, c in stops)
    out = [bytearray(256), bytearray(256), bytearray(256)]
    for i in range(256):
        t = i / 255.0
        if t <= st[0][0]:
            c = st[0][1]
        elif t >= st[-1][0]:
            c = st[-1][1]
        else:
            for k in range(len(st) - 1):
                t0, c0 = st[k]
                t1, c1 = st[k + 1]
                if t0 <= t <= t1:
                    u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                    u = u * u * (3 - 2 * u) * 0.35 + u * 0.65  # slightly eased blends
                    c = tuple(c0[j] + (c1[j] - c0[j]) * u for j in range(3))
                    break
        for j in range(3):
            out[j][i] = int(round(clamp(c[j]) * 255))
    return [bytes(o) for o in out]


def lut_bytes(fn):
    """256-entry byte LUT from a float function on 0..1."""
    return bytes(int(round(clamp(fn(i / 255.0)) * 255)) for i in range(256))


INVERT = bytes(255 - i for i in range(256))


# --------------------------------------------------------------------------
# images, layers, buffers
# --------------------------------------------------------------------------

def new_image(w, h=None):
    img = Gimp.Image.new_with_precision(int(w), int(h or w), Gimp.ImageBaseType.RGB, PREC)
    img.undo_disable()  # no undo bookkeeping: ~50x faster selections/paths in batch work
    return img


def perceptual(L):
    """Blend/composite in perceptual space, like a painting app."""
    try:
        L.set_blend_space(Gimp.LayerColorSpace.RGB_PERCEPTUAL)
        L.set_composite_space(Gimp.LayerColorSpace.RGB_PERCEPTUAL)
    except Exception:
        pass
    return L


def layer(img, name="layer", fill=None, mode=LM.NORMAL, opacity=100.0, alpha=True, pos=0):
    t = Gimp.ImageType.RGBA_IMAGE if alpha else Gimp.ImageType.RGB_IMAGE
    L = Gimp.Layer.new(img, name, img.get_width(), img.get_height(), t, float(opacity), mode)
    img.insert_layer(L, None, pos)
    perceptual(L)
    if fill is not None:
        fill_all(L, fill)
    return L


def copy_to(L, img, name=None, mode=LM.NORMAL, opacity=100.0, pos=0):
    N = Gimp.Layer.new_from_drawable(L, img)
    img.insert_layer(N, None, pos)
    N.set_mode(mode)
    N.set_opacity(float(opacity))
    if name:
        N.set_name(name)
    perceptual(N)
    return N


def dup(L, name=None, mode=None, opacity=None, above=True):
    img = L.get_image()
    N = L.copy()
    pos = img.get_item_position(L)
    img.insert_layer(N, None, pos if above else pos + 1)
    if name:
        N.set_name(name)
    if mode is not None:
        N.set_mode(mode)
    if opacity is not None:
        N.set_opacity(float(opacity))
    perceptual(N)
    return N


def merge_down(L):
    return L.get_image().merge_down(L, Gimp.MergeType.CLIP_TO_IMAGE)


def merge(img):
    return img.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)


def rect(x, y, w, h):
    return Gegl.Rectangle.new(int(x), int(y), int(w), int(h))


def read(d, fmt="R'G'B' u8", r=None, abyss=NONE):
    if r is None:
        r = (0, 0, d.get_width(), d.get_height())
    return bytes(d.get_buffer().get(rect(*r), 1.0, fmt, abyss))


def write(d, data, fmt="R'G'B' u8", r=None):
    if r is None:
        r = (0, 0, d.get_width(), d.get_height())
    buf = d.get_buffer()
    buf.set(rect(*r), fmt, data)
    buf.flush()
    d.update(*[int(v) for v in r])


def read_f(d, fmt="Y' float"):
    return array.array("f", read(d, fmt))


def write_f(d, arr, fmt="Y' float"):
    write(d, array.array("f", arr).tobytes(), fmt)


def grey_layer(img, data, name="grey", mode=LM.NORMAL, opacity=100.0, pos=0, fmt="Y' u8"):
    L = layer(img, name, mode=mode, opacity=opacity, alpha=False, pos=pos)
    write(L, data if not isinstance(data, array.array) else data.tobytes(), fmt)
    return L


def scratch(W, H=None, data=None, fmt="Y' float"):
    """A throwaway single-layer image (returns image, layer)."""
    img = new_image(W, H or W)
    L = layer(img, "scratch", alpha=False)
    if data is not None:
        write(L, data.tobytes() if isinstance(data, array.array) else data, fmt)
    return img, L


# --------------------------------------------------------------------------
# context / fills / selections
# --------------------------------------------------------------------------

def paint_ctx(color=None, opacity=100.0, mode=LM.NORMAL):
    if color is not None:
        Gimp.context_set_foreground(gcol(color))
    Gimp.context_set_opacity(float(opacity))
    Gimp.context_set_paint_mode(mode)


def fill_all(L, color, opacity=100.0, mode=LM.NORMAL):
    Gimp.Selection.none(L.get_image())
    paint_ctx(color, opacity, mode)
    L.edit_fill(FG)
    paint_ctx(None)


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def wrap_offsets(x0, y0, x1, y1, W, H, wrap=True):
    if not wrap:
        return [(0, 0)]
    xs, ys = [0], [0]
    if x0 < 0:
        xs.append(W)
    if x1 > W:
        xs.append(-W)
    if y0 < 0:
        ys.append(H)
    if y1 > H:
        ys.append(-H)
    return [(dx, dy) for dx in xs for dy in ys]


def _next_op(op, i):
    return op if (i == 0 or op != REPLACE) else ADD


def sel_poly(img, pts, op=REPLACE, wrap=True):
    W, H = img.get_width(), img.get_height()
    x0, y0, x1, y1 = bbox(pts)
    for i, (dx, dy) in enumerate(wrap_offsets(x0, y0, x1, y1, W, H, wrap)):
        img.select_polygon(_next_op(op, i), [float(c) for x, y in pts for c in (x + dx, y + dy)])


def sel_ellipse(img, cx, cy, rx, ry, op=REPLACE, wrap=True):
    W, H = img.get_width(), img.get_height()
    for i, (dx, dy) in enumerate(wrap_offsets(cx - rx, cy - ry, cx + rx, cy + ry, W, H, wrap)):
        img.select_ellipse(_next_op(op, i), cx - rx + dx, cy - ry + dy, 2 * rx, 2 * ry)


def sel_rect(img, x, y, w, h, op=REPLACE, wrap=True):
    W, H = img.get_width(), img.get_height()
    for i, (dx, dy) in enumerate(wrap_offsets(x, y, x + w, y + h, W, H, wrap)):
        img.select_rectangle(_next_op(op, i), x + dx, y + dy, w, h)


def sel_none(img):
    Gimp.Selection.none(img)


def fill_sel(L, color, opacity=100.0, mode=LM.NORMAL):
    paint_ctx(color, opacity, mode)
    L.edit_fill(FG)
    paint_ctx(None)


def fill_poly(L, pts, color, opacity=100.0, mode=LM.NORMAL, wrap=True):
    img = L.get_image()
    sel_poly(img, pts, REPLACE, wrap)
    fill_sel(L, color, opacity, mode)
    sel_none(img)


def _copies(pts, W, H, wrap=True):
    x0, y0, x1, y1 = bbox(pts)
    out = []
    for dx, dy in wrap_offsets(x0, y0, x1, y1, W, H, wrap):
        if x1 + dx < 0 or x0 + dx > W or y1 + dy < 0 or y0 + dy > H:
            continue
        out.append([(x + dx, y + dy) for x, y in pts])
    return out


def _passes(polys, W, H, wrap=True, cell=48):
    """Split polygons (with their wrap copies) into groups whose bounding boxes do not
    overlap, because GIMP fills a path with the even-odd rule (overlaps would be holes)."""
    passes = []  # each: (grid dict, list of copies)
    for pts in polys:
        if len(pts) < 3:
            continue
        cps = _copies(pts, W, H, wrap)
        boxes = [bbox(c) for c in cps]
        cells = set()
        for bx0, by0, bx1, by1 in boxes:
            for gx in range(int(bx0 // cell), int(bx1 // cell) + 1):
                for gy in range(int(by0 // cell), int(by1 // cell) + 1):
                    cells.add((gx, gy))
        placed = False
        for grid, members in passes:
            clash = False
            for c in cells:
                for ob in grid.get(c, ()):
                    for b in boxes:
                        if b[0] <= ob[2] and ob[0] <= b[2] and b[1] <= ob[3] and ob[1] <= b[3]:
                            clash = True
                            break
                    if clash:
                        break
                if clash:
                    break
            if not clash:
                for c in cells:
                    grid.setdefault(c, []).extend(boxes)
                members.extend(cps)
                placed = True
                break
        if not placed:
            grid = {}
            for c in cells:
                grid.setdefault(c, []).extend(boxes)
            passes.append((grid, list(cps)))
    return [m for g, m in passes]


def sel_polys(img, polys, op=REPLACE, wrap=True):
    """Select the union of many polygons through GIMP paths (fast)."""
    W, H = img.get_width(), img.get_height()
    groups = _passes(polys, W, H, wrap)
    if not groups and op == REPLACE:
        sel_none(img)
    for i, group in enumerate(groups):
        path = Gimp.Path.new(img, "polys")
        img.insert_path(path, None, 0)
        for pts in group:
            cps = []
            for x, y in pts:
                cps += [float(x), float(y)] * 3
            path.stroke_new_from_points(Gimp.PathStrokeType.BEZIER, cps, True)
        img.select_item(_next_op(op, i), path)
        img.remove_path(path)
    return len(groups)


def fill_polys(L, polys, color, opacity=100.0, mode=LM.NORMAL, wrap=True):
    """Fill the union of many polygons with one colour."""
    img = L.get_image()
    if sel_polys(img, polys, REPLACE, wrap):
        fill_sel(L, color, opacity, mode)
    sel_none(img)


def luma(c):
    r, g, b = rgb(c)
    return 0.3 * r + 0.59 * g + 0.11 * b


def fill_many(L, items, opacity=100.0, mode=LM.NORMAL, wrap=True, order="luma"):
    """Fill [(polygon, colour), ...]: polygons are grouped by colour (hex) and each group
    is filled in one go.  order="luma" paints dark groups first (light strokes end up on
    top, like layered paint); order="first" keeps first-appearance order."""
    groups = {}
    first = []
    for poly, col in items:
        hx = hexc(col)
        if hx not in groups:
            groups[hx] = []
            first.append(hx)
        groups[hx].append(poly)
    keys = sorted(first, key=luma) if order == "luma" else first
    for hx in keys:
        fill_polys(L, groups[hx], hx, opacity, mode, wrap)


def fill_ordered(L, items, opacity=100.0, mode=LM.NORMAL, wrap=True):
    """Fill polygons one by one in the given order (slow; for small counts)."""
    img = L.get_image()
    paint_ctx(None, opacity, mode)
    last = None
    for poly, col in items:
        if len(poly) < 3:
            continue
        sel_poly(img, poly, REPLACE, wrap)
        hx = hexc(col)
        if hx != last:
            Gimp.context_set_foreground(Gegl.Color.new(hx))
            last = hx
        L.edit_fill(FG)
    sel_none(img)
    paint_ctx(None)


def quant(c, step=12):
    """Snap a colour to a coarse grid so fill_many can batch similar colours."""
    return tuple(round(v * 255 / step) * step / 255.0 for v in rgb(c))


def fill_ellipse(L, cx, cy, rx, ry, color, opacity=100.0, mode=LM.NORMAL, wrap=True):
    img = L.get_image()
    sel_ellipse(img, cx, cy, rx, ry, REPLACE, wrap)
    fill_sel(L, color, opacity, mode)
    sel_none(img)


def gradient_poly(L, pts, p0, p1, c0, c1, wrap=True):
    """Linear gradient c0 at p0 -> c1 at p1, clipped to a polygon.  Every wrap copy gets
    its own (shifted) gradient so planar facets stay continuous across the seams."""
    img = L.get_image()
    W, H = img.get_width(), img.get_height()
    x0, y0, x1, y1 = bbox(pts)
    Gimp.context_set_foreground(gcol(c0))
    Gimp.context_set_background(gcol(c1))
    Gimp.context_set_gradient_fg_bg_rgb()
    Gimp.context_set_gradient_repeat_mode(Gimp.RepeatMode.NONE)
    Gimp.context_set_opacity(100.0)
    Gimp.context_set_paint_mode(LM.NORMAL)
    for dx, dy in wrap_offsets(x0, y0, x1, y1, W, H, wrap):
        img.select_polygon(REPLACE, [float(c) for x, y in pts for c in (x + dx, y + dy)])
        L.edit_gradient_fill(Gimp.GradientType.LINEAR, 0.0, False, 1, 0.0, False,
                             p0[0] + dx, p0[1] + dy, p1[0] + dx, p1[1] + dy)
    sel_none(img)


def stroke(L, pts, color, size, brush="2. Hardness 075", opacity=100.0, mode=LM.NORMAL, wrap=True):
    """Paintbrush stroke along a polyline (GIMP paint core), wrapped at the edges."""
    W, H = L.get_width(), L.get_height()
    paint_ctx(color, opacity, mode)
    Gimp.context_set_brush(Gimp.Brush.get_by_name(brush))
    Gimp.context_set_brush_size(float(size))
    if len(pts) == 1:
        pts = [pts[0], (pts[0][0] + 0.01, pts[0][1])]
    x0, y0, x1, y1 = bbox(pts)
    m = size
    for dx, dy in wrap_offsets(x0 - m, y0 - m, x1 + m, y1 + m, W, H, wrap):
        Gimp.paintbrush_default(L, [float(c) for x, y in pts for c in (x + dx, y + dy)])
    paint_ctx(None)


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def ellipse_pts(cx, cy, rx, ry, ang=0.0, n=28):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def blob_pts(cx, cy, r, rng, n=18, irregular=0.25, ang=0.0, aspect=1.0):
    """A soft irregular round blob (pebble/clump) as a polygon."""
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    amp = [irregular * rng.uniform(0.3, 1.0) for _ in range(3)]
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = r * (1 + amp[0] * 0.5 * math.sin(2 * t + ph[0]) + amp[1] * 0.35 * math.sin(3 * t + ph[1])
                  + amp[2] * 0.2 * math.sin(5 * t + ph[2]))
        x, y = rr * math.cos(t) * aspect, rr * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def leaf_pts(cx, cy, length, width, ang, n=8, bend=0.0):
    """Pointed leaf / blade lens shape centred on (cx, cy), long axis at angle ang."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (t - 0.5) * length
        y = -math.sin(math.pi * t) * width * 0.5 + bend * (t - 0.5) ** 2 * length
        pts.append((x, y))
    for i in range(n - 1, 0, -1):
        t = i / n
        x = (t - 0.5) * length
        y = math.sin(math.pi * t) * width * 0.5 + bend * (t - 0.5) ** 2 * length
        pts.append((x, y))
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def blade_pts(x, y, length, width, ang, bend=0.0, n=6):
    """Tapered grass blade from base (x, y) pointing along ang (radians, 0 = +x)."""
    ca, sa = math.cos(ang), math.sin(ang)
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = width * 0.5 * (1 - t) ** 0.8
        px = t * length
        py = bend * t * t * length
        left.append((px, py - w))
        right.append((px, py + w))
    pts = left + right[::-1][1:]
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]


def round_corners(pts, r, segs=4):
    """Replace every corner by a quadratic arc of (at most) radius-ish r."""
    n = len(pts)
    out = []
    for i in range(n):
        px, py = pts[i - 1]
        vx, vy = pts[i]
        nx, ny = pts[(i + 1) % n]
        d1 = math.hypot(px - vx, py - vy)
        d2 = math.hypot(nx - vx, ny - vy)
        if d1 < 1e-6 or d2 < 1e-6:
            continue
        t1 = min(r / d1, 0.5)
        t2 = min(r / d2, 0.5)
        ax, ay = vx + (px - vx) * t1, vy + (py - vy) * t1
        bx, by = vx + (nx - vx) * t2, vy + (ny - vy) * t2
        for k in range(segs + 1):
            u = k / segs
            x = (1 - u) ** 2 * ax + 2 * (1 - u) * u * vx + u * u * bx
            y = (1 - u) ** 2 * ay + 2 * (1 - u) * u * vy + u * u * by
            out.append((x, y))
    return out


def subdivide(pts, seg=12.0, closed=True):
    out = []
    n = len(pts)
    for i in range(n if closed else n - 1):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        d = math.hypot(bx - ax, by - ay)
        k = max(1, int(d / seg))
        for j in range(k):
            t = j / k
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    if not closed:
        out.append(pts[-1])
    return out


def wobble(pts, rng, amp, seg=14.0, closed=True, waves=4):
    """Subdivide an outline and displace it along its normals by a smooth periodic
    function (sum of a few random sinusoids) for a hand-drawn, kink-free edge."""
    p = subdivide(pts, seg, closed)
    n = len(p)
    comps = [(rng.randint(2, 9), rng.uniform(0, 2 * math.pi), rng.uniform(0.4, 1.0)) for _ in range(waves)]
    norm = sum(c[2] for c in comps) * 0.6
    out = []
    for i in range(n):
        t = i / n
        o = sum(a * math.sin(2 * math.pi * f * t + ph) for f, ph, a in comps) / norm
        ax, ay = p[i - 1]
        bx, by = p[(i + 1) % n]
        tx, ty = bx - ax, by - ay
        d = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / d, tx / d
        out.append((p[i][0] + nx * o * amp, p[i][1] + ny * o * amp))
    return out


def rrect_pts(x, y, w, h, r, segs=4):
    return round_corners([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], r, segs)


def polyline_wavy(x0, y0, x1, y1, rng, amp, n=12, freq=1.0):
    """Gently wavy line from (x0,y0) to (x1,y1)."""
    ph = rng.uniform(0, 6.283)
    ph2 = rng.uniform(0, 6.283)
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    out = []
    for i in range(n + 1):
        t = i / n
        o = amp * (math.sin(t * math.pi * 2 * freq + ph) * 0.7 + math.sin(t * math.pi * 4.3 * freq + ph2) * 0.3)
        out.append((x0 + dx * t + nx * o, y0 + dy * t + ny * o))
    return out


def periodic_line(S, y0, rng, amp=6.0, harmonics=(1, 2, 3, 5), step=16.0, knots=(), vertical=False):
    """A full-width wavy line whose offset is periodic in x (period S), so it continues
    seamlessly across the tile edge.  knots: [(kx, ky, radius)] the line flows around.
    vertical=True swaps axes (line runs top to bottom)."""
    comps = [(k, rng.uniform(0, 2 * math.pi), amp * rng.uniform(0.3, 1.0) / k ** 0.6) for k in harmonics]
    pts = []
    n = int(S / step)
    for i in range(n + 1):
        x = i * S / n
        y = y0 + sum(a * math.sin(2 * math.pi * k * x / S + ph) for k, ph, a in comps)
        for kx, ky, kr in knots:
            for ox in (-S, 0, S):
                dx = x - (kx + ox)
                dy = y - ky
                if abs(dx) < kr * 3 and abs(dy) < kr * 2.2:
                    push = kr * 1.15 * math.exp(-(dx / (kr * 1.3)) ** 2) * max(0.0, 1 - abs(dy) / (kr * 2.2))
                    y += push if dy >= 0 else -push
        pts.append((y, x) if vertical else (x, y))
    return pts


def crack_path(x, y, length, ang, rng, seg=10.0, jag=0.5):
    pts = [(x, y)]
    a = ang
    steps = max(2, int(length / seg))
    for _ in range(steps):
        a += rng.uniform(-jag, jag)
        x += math.cos(a) * seg
        y += math.sin(a) * seg
        pts.append((x, y))
    return pts


def poisson(W, H, r, rng, attempts=30, limit=100000):
    """Poisson-disc points on a torus W x H (min distance r)."""
    cell = r / math.sqrt(2)
    gw, gh = int(math.ceil(W / cell)), int(math.ceil(H / cell))
    grid = {}
    pts = []
    active = []

    def ok(x, y):
        gx, gy = int(x / cell), int(y / cell)
        for ix in range(gx - 2, gx + 3):
            for iy in range(gy - 2, gy + 3):
                q = grid.get((ix % gw, iy % gh))
                if q is None:
                    continue
                ddx = abs(q[0] - x)
                ddy = abs(q[1] - y)
                ddx = min(ddx, W - ddx)
                ddy = min(ddy, H - ddy)
                if ddx * ddx + ddy * ddy < r * r:
                    return False
        return True

    def add(x, y):
        pts.append((x, y))
        active.append((x, y))
        grid[(int(x / cell) % gw, int(y / cell) % gh)] = (x, y)

    add(rng.uniform(0, W), rng.uniform(0, H))
    while active and len(pts) < limit:
        i = rng.randrange(len(active))
        ax, ay = active[i]
        placed = False
        for _ in range(attempts):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(r, 2 * r)
            x = (ax + math.cos(a) * d) % W
            y = (ay + math.sin(a) * d) % H
            if ok(x, y):
                add(x, y)
                placed = True
                break
        if not placed:
            active.pop(i)
    return pts


def _clip(poly, px, py, nx, ny, c):
    out = []
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        da = (ax - px) * nx + (ay - py) * ny - c
        db = (bx - px) * nx + (by - py) * ny - c
        if da <= 0:
            out.append((ax, ay))
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return out


def voronoi(pts, W, H, gap=0.0, sx=1.0, sy=1.0, k=26):
    """Periodic Voronoi cells (convex polygons, inset by gap/2 on every side).
    sx, sy stretch the metric (e.g. sy<1 gives cells elongated vertically)."""
    ext = []
    for i, (x, y) in enumerate(pts):
        for dx in (-W, 0, W):
            for dy in (-H, 0, H):
                ext.append((x + dx, y + dy, i))
    cells = []
    for i, (px, py) in enumerate(pts):
        cand = sorted(ext, key=lambda q: ((q[0] - px) * sx) ** 2 + ((q[1] - py) * sy) ** 2)[1:k]
        R = max(W, H)
        poly = [(px - R, py - R), (px + R, py - R), (px + R, py + R), (px - R, py + R)]
        for qx, qy, j in cand:
            # work in stretched space: bisector of p and q under metric (sx, sy)
            dx, dy = (qx - px) * sx * sx, (qy - py) * sy * sy
            d = math.hypot(dx, dy)
            if d < 1e-9:
                continue
            nx, ny = dx / d, dy / d
            # midpoint
            mx, my = (qx - px) / 2, (qy - py) / 2
            c = mx * nx + my * ny - gap / 2
            poly = _clip(poly, px, py, nx, ny, c)
            if not poly:
                break
        cells.append(poly)
    return cells


def poly_area(p):
    a = 0.0
    for i in range(len(p)):
        x0, y0 = p[i - 1]
        x1, y1 = p[i]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def centroid(p):
    xs = sum(q[0] for q in p) / len(p)
    ys = sum(q[1] for q in p) / len(p)
    return xs, ys


def scale_poly(p, f, cx=None, cy=None):
    if cx is None:
        cx, cy = centroid(p)
    return [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in p]


# --------------------------------------------------------------------------
# GEGL filters
# --------------------------------------------------------------------------

def gegl(d, op, aux=None, **props):
    f = Gimp.DrawableFilter.new(d, op, "")
    cfg = f.get_config()
    for k, v in props.items():
        cfg.set_property(k.replace("_", "-"), v)
    if aux is not None:
        f.set_aux_input("aux", aux)
    f.update()
    d.merge_filter(f)


def wrap_filter(L, fn, margin, fmt=None):
    """Run fn(layer) on a copy of L padded with wrapped pixels; copy the centre back."""
    W, H = L.get_width(), L.get_height()
    alpha = L.has_alpha()
    fmt = fmt or ("R'G'B'A float" if alpha else "R'G'B' float")
    m = int(max(2, margin))
    tmp = new_image(W + 2 * m, H + 2 * m)
    t = layer(tmp, "pad", alpha=alpha)
    write(t, read(L, fmt, (-m, -m, W + 2 * m, H + 2 * m), LOOP), fmt)
    fn(t)
    write(L, read(t, fmt, (m, m, W, H)), fmt)
    tmp.delete()


def blur(L, sx, sy=None):
    sy = sx if sy is None else sy
    if sx <= 0 and sy <= 0:
        return
    m = int(3 * max(sx, sy)) + 3
    wrap_filter(L, lambda t: gegl(t, "gegl:gaussian-blur", std_dev_x=float(max(sx, 0.01)),
                                  std_dev_y=float(max(sy, 0.01))), m)


def motion_blur(L, length, angle):
    m = int(length) + 4
    wrap_filter(L, lambda t: gegl(t, "gegl:motion-blur-linear", length=float(length), angle=float(angle)), m)


def median(L, radius, percentile=50.0):
    wrap_filter(L, lambda t: gegl(t, "gegl:median-blur", radius=int(radius), percentile=float(percentile)),
                int(radius) + 3)


def oilify(L, radius=4, exponent=8):
    wrap_filter(L, lambda t: gegl(t, "gegl:oilify", mask_radius=int(radius), exponent=int(exponent),
                                  use_inten=True), int(radius) + 3)


def snn(L, radius=4):
    wrap_filter(L, lambda t: gegl(t, "gegl:snn-mean", radius=int(radius), pairs=2), int(radius) + 3)


def noise(L, xs, ys=None, detail=3, seed=0, turbulent=False):
    """Tileable solid noise (gegl:noise-solid) filling the layer."""
    gegl(L, "gegl:noise-solid", x_size=float(xs), y_size=float(ys if ys is not None else xs),
         detail=int(detail), seed=int(seed), tileable=True, turbulent=bool(turbulent),
         width=L.get_width(), height=L.get_height())


def levels(L, lo=0.0, hi=1.0, gamma=1.0, olo=0.0, ohi=1.0):
    L.levels(Gimp.HistogramChannel.VALUE, float(lo), float(hi), True, float(gamma), float(olo), float(ohi), True)


def curves(L, pts):
    L.curves_spline(Gimp.HistogramChannel.VALUE, [float(c) for p in pts for c in p])


def posterize(L, n):
    L.posterize(int(n))


def normalize(L, lo=0.0, hi=1.0):
    """Stretch the grey values of L to lo..hi (exact, float)."""
    a = read_f(L)
    mn, mx = min(a), max(a)
    s = (hi - lo) / (mx - mn) if mx > mn else 0.0
    write_f(L, array.array("f", [lo + (v - mn) * s for v in a]))


def gradient_map(L, stops, src=None):
    """Colourise: luminance of src (default L itself) through a colour ramp into L."""
    g = read(src or L, "Y' u8")
    lr, lg, lb = ramp_luts(stops)
    n = len(g)
    if L.has_alpha():
        a = read(L, "R'G'B'A u8")[3::4]
        out = bytearray(n * 4)
        out[0::4], out[1::4], out[2::4], out[3::4] = g.translate(lr), g.translate(lg), g.translate(lb), a
        write(L, bytes(out), "R'G'B'A u8")
    else:
        out = bytearray(n * 3)
        out[0::3], out[1::3], out[2::3] = g.translate(lr), g.translate(lg), g.translate(lb)
        write(L, bytes(out), "R'G'B' u8")


def set_mask(L, data, invert=False):
    """Give layer L a mask from grey bytes (Y' u8) or a grey layer."""
    if not isinstance(data, (bytes, bytearray)):
        data = read(data, "Y' u8")
    if invert:
        data = bytes(data).translate(INVERT)
    m = L.get_mask()
    if m is None:
        m = L.create_mask(Gimp.AddMaskType.WHITE)
        L.add_mask(m)
    write(m, bytes(data), "Y' u8")
    return m


def sel_from_bytes(img, data, op=REPLACE):
    """Selection from a grey mask (bytes Y' u8)."""
    ch = Gimp.Channel.new(img, "selmask", img.get_width(), img.get_height(), 100.0, gcol("#000000"))
    img.insert_channel(ch, None, 0)
    write(ch, bytes(data), "Y' u8")
    img.select_item(op, ch)
    img.remove_channel(ch)


# --------------------------------------------------------------------------
# float-array image algebra (grey fields, e.g. heights)
# --------------------------------------------------------------------------

def field_noise(W, xs, ys=None, detail=3, seed=0, turbulent=False, lo=0.0, hi=1.0, H=None):
    img, L = scratch(W, H)
    noise(L, xs, ys, detail, seed, turbulent)
    normalize(L, lo, hi)
    a = read_f(L)
    img.delete()
    return a


def field_blur(a, W, H, sx, sy=None):
    img, L = scratch(W, H, a)
    blur(L, sx, sy)
    out = read_f(L)
    img.delete()
    return out


def field_from_layer(L):
    return read_f(L)


def to_u8(a, lo=0.0, hi=1.0):
    s = 255.0 / (hi - lo)
    return bytes([0 if v <= lo else 255 if v >= hi else int((v - lo) * s + 0.5) for v in a])


def from_u8(b):
    return array.array("f", [v / 255.0 for v in b])


def distance_field(mask, W, H, maxd, thresh=0.5):
    """Euclidean distance (px) from every 'on' pixel of mask (Y' u8 bytes) to the nearest
    'off' pixel, computed by gegl:distance-transform on a wrap-padded copy."""
    m = int(maxd) + 6
    src_img, src = scratch(W, H, mask, "Y' u8")
    tmp, t = scratch(W + 2 * m, H + 2 * m)
    write(t, read(src, "Y' u8", (-m, -m, W + 2 * m, H + 2 * m), LOOP), "Y' u8")
    gegl(t, "gegl:distance-transform", metric="euclidean", normalize=False,
         threshold_lo=float(thresh), threshold_hi=1.0, edge_handling="below")
    d = array.array("f", read(t, "Y float", (m, m, W, H)))
    src_img.delete()
    tmp.delete()
    return d


def warp_field(a, W, H, dx, dy, amount):
    """Displace field a by fields dx, dy (0..1, 0.5 = none) times amount px, wrapping
    (gegl:displace with a looping abyss)."""
    img = new_image(W, H)
    src = layer(img, "src", alpha=False)
    write_f(src, a)
    ax = layer(img, "dx", alpha=False, pos=1)
    write_f(ax, dx)
    ay = layer(img, "dy", alpha=False, pos=2)
    write_f(ay, dy)
    f = Gimp.DrawableFilter.new(src, "gegl:displace", "")
    cfg = f.get_config()
    cfg.set_property("displace-mode", "cartesian")
    cfg.set_property("abyss-policy", "loop")
    cfg.set_property("amount-x", float(amount))
    cfg.set_property("amount-y", float(amount))
    f.set_aux_input("aux", ax)
    f.set_aux_input("aux2", ay)
    f.update()
    src.merge_filter(f)
    out = read_f(src)
    img.delete()
    return out


def id_field(S, polys):
    """Render polygons with unique colours (no antialiasing) and return, per pixel, the
    index of the polygon covering it (-1 = none).  Later polygons win."""
    img = new_image(S)
    L = layer(img, "ids", fill="#000000", alpha=False)
    Gimp.context_set_antialias(False)
    for k, p in enumerate(polys):
        v = k + 1
        fill_poly(L, p, (((v >> 16) & 255) / 255.0, ((v >> 8) & 255) / 255.0, (v & 255) / 255.0))
    Gimp.context_set_antialias(True)
    d = read(L, "R'G'B' u8")
    img.delete()
    R, G, B = d[0::3], d[1::3], d[2::3]
    return [((r << 16) | (g << 8) | b) - 1 for r, g, b in zip(R, G, B)]


def facet_planes(S, ids, planes):
    """Piecewise-planar height: planes[k] = (cx, cy, h0, gx, gy) evaluated at every pixel
    of polygon k (offsets wrap, so planes stay continuous across the seams)."""
    out = array.array("f", [0.0]) * (S * S)
    half = S / 2.0
    for y in range(S):
        row = y * S
        for x in range(S):
            k = ids[row + x]
            if k < 0:
                continue
            cx, cy, h0, gx, gy = planes[k]
            dx = (x - cx + half) % S - half
            dy = (y - cy + half) % S - half
            out[row + x] = h0 + gx * dx + gy * dy
    return out


def bevel(dist, radius, profile="round"):
    """Map a distance field to a 0..1 bevel height."""
    n = 2048
    if profile == "round":
        lut = [math.sqrt(max(0.0, 1 - (1 - i / (n - 1)) ** 2)) for i in range(n)]
    elif profile == "soft":
        lut = [smoothstep(0, 1, i / (n - 1)) for i in range(n)]
    elif profile == "linear":
        lut = [i / (n - 1) for i in range(n)]
    else:  # "pillow": rounded but keeps rising slowly
        lut = [math.sqrt(max(0.0, 1 - (1 - i / (n - 1)) ** 2)) for i in range(n)]
    s = (n - 1) / float(radius)
    top = n - 1
    return array.array("f", [lut[top if v * s >= top else int(v * s)] if v > 0 else 0.0 for v in dist])


def normal_map(h, W, H, strength):
    """Height field (array 0..1) -> OpenGL normal map. Returns (image, layer, rgb bytes)."""
    img, L = scratch(W, H, h)
    gegl(L, "gegl:normal-map", scale=float(strength), tileable=True, flip_y=True, flip_x=False)
    nb = read(L, "R'G'B' u8")
    return img, L, nb


def light_from_normal(nb, k=1.0, light=LIGHT, bands=0):
    """Grey overlay (128 = neutral) of the tilt lighting encoded in a normal map."""
    R = nb[0::3]
    G = nb[1::3]
    lx, ly = light[0], light[1]
    lr = [int(round(k * lx * (i - 128))) for i in range(256)]
    lg = [int(round(k * ly * (i - 128))) + 128 + 1024 for i in range(256)]
    clip = bytes([max(0, min(255, v - 1024)) for v in range(4096)])
    out = bytes([clip[lr[r] + lg[g]] for r, g in zip(R, G)])
    if bands:
        step = 256 // bands
        out = out.translate(bytes([min(255, (i // step) * step + step // 2) for i in range(256)]))
    return out


def cavity(h, W, H, radius, k=4.0):
    """Returns (occlusion, ridge) grey bytes from height: occlusion 255 = open, dark in
    crevices; ridge 0 = none, bright on convex edges."""
    hb = field_blur(h, W, H, radius)
    occ = bytearray(len(h))
    rid = bytearray(len(h))
    for i in range(len(h)):
        d = (h[i] - hb[i]) * k
        if d < 0:
            occ[i] = 255 - min(255, int(-d * 255))
            rid[i] = 0
        else:
            occ[i] = 255
            rid[i] = min(255, int(d * 255))
    return bytes(occ), bytes(rid)


# --------------------------------------------------------------------------
# compositing helpers on an albedo work image
# --------------------------------------------------------------------------

def overlay_grey(img, data, mode=LM.OVERLAY, opacity=100.0, name="shade"):
    """Add a grey layer (bytes) with a blend mode on top of img."""
    return grey_layer(img, data, name, mode=mode, opacity=opacity)


def tint_layer(img, color, mask, opacity=100.0, mode=LM.NORMAL, name="tint", invert=False):
    """A flat colour layer shown through a grey mask."""
    L = layer(img, name, fill=color, mode=mode, opacity=opacity)
    set_mask(L, mask, invert)
    return L


def ramp_layer(img, data, stops, mode=LM.NORMAL, opacity=100.0, name="ramp"):
    """Grey bytes coloured through a ramp, as a new layer."""
    L = grey_layer(img, data, name, mode=mode, opacity=opacity)
    gradient_map(L, stops)
    return L


# --------------------------------------------------------------------------
# layout / mask helpers shared by the material generators
# --------------------------------------------------------------------------

def row_lengths(S, rng, lo, hi):
    """Random lengths in [lo, hi] that sum exactly to S."""
    ls, tot = [], 0.0
    while tot < S:
        v = rng.uniform(lo, hi)
        ls.append(v)
        tot += v
    if len(ls) > 1 and tot - S > lo * 0.5:
        tot -= ls.pop()
    f = S / tot
    return [v * f for v in ls]


def mask_of(S, polys, cut=None):
    img = new_image(S)
    L = layer(img, "m", fill="#000000", alpha=False)
    fill_polys(L, polys, "#ffffff")
    if cut:
        fill_polys(L, cut, "#000000")
    data = read(L, "Y' u8")
    img.delete()
    return data


def tone_of(S, items, bg=0.0):
    """Float field: each polygon filled with its own grey value."""
    img = new_image(S)
    L = layer(img, "t", fill=(bg, bg, bg), alpha=False)
    for poly, v in items:
        fill_poly(L, poly, (v, v, v))
    a = read_f(L)
    img.delete()
    return a


def strokes_field(S, paths, size, blur_r=0.8):
    img = new_image(S)
    L = layer(img, "s", fill="#000000", alpha=False)
    for p in paths:
        stroke(L, p, "#ffffff", size)
    a = read_f(L)
    img.delete()
    if blur_r:
        a = field_blur(a, S, S, blur_r)
    return a


def hilite(nb, lo=136, gain=5.0):
    """Crisp mask of the light-facing bevels (painted edge highlight)."""
    lt = light_from_normal(nb, 1.0)
    return lt.translate(bytes([int(min(255, max(0, (i - lo) * gain))) for i in range(256)]))


def shade_mask(nb, hi=118, gain=4.0):
    """Mask of the bevels facing away from the light."""
    lt = light_from_normal(nb, 1.0)
    return lt.translate(bytes([int(min(255, max(0, (hi - i) * gain))) for i in range(256)]))


def row_gradient(S, period, top=0.62, bottom=0.40, offset=0.0):
    """Grey field repeating every `period` rows: light at the top of each row."""
    rows = []
    for y in range(S):
        t = ((y - offset) % period) / period
        v = top + (bottom - top) * t
        rows.append(bytes([int(v * 255)]) * S)
    return b"".join(rows)


def dome(mask, S, radius):
    """Rounded dome height (0..1) for every shape in a mask."""
    return bevel(distance_field(mask, S, S, radius + 3), radius, "round")


def drop_shadow(img, polys, dx, dy, color, opacity=55, soft=2.0, name="shadow"):
    L = layer(img, name, mode=LM.MULTIPLY, opacity=opacity)
    fill_polys(L, [[(x + dx, y + dy) for x, y in p] for p in polys], color)
    if soft:
        blur(L, soft)
    return L


def finish_lighting(img, T, h, strength, light=0.9, light_op=55, occ_col=None, occ_op=50,
                    occ_r=5, occ_k=3.0, hi_col=None, hi_op=40, hi_lo=138, hi_gain=4.0,
                    shade_col=None, shade_op=30, shade_hi=118, shade_gain=3.0):
    """Normal map from h, then baked light, crevice occlusion, cool shading on the
    bevels facing away from the light and painted highlights on the lit ones."""
    nb = T.save_normal(h, strength)
    overlay_grey(img, light_from_normal(nb, light), LM.OVERLAY, light_op, "light")
    if shade_col:
        tint_layer(img, shade_col, shade_mask(nb, shade_hi, shade_gain), opacity=shade_op,
                   mode=LM.MULTIPLY, name="shade")
    if occ_col:
        occ, rid = cavity(h, T.S, T.S, occ_r, occ_k)
        tint_layer(img, occ_col, occ, opacity=occ_op, mode=LM.MULTIPLY, name="occ", invert=True)
    if hi_col:
        tint_layer(img, hi_col, hilite(nb, hi_lo, hi_gain), opacity=hi_op, mode=LM.SCREEN, name="hi")
    return nb


# --------------------------------------------------------------------------
# export / previews / QA
# --------------------------------------------------------------------------

def export(src, path, grey=False):
    """Export a layer or image as 8-bit PNG (flattened)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(src, Gimp.Image):
        img = src.duplicate()
    else:
        img = new_image(src.get_width(), src.get_height())
        copy_to(src, img)
    img.flatten()
    if grey:
        img.convert_grayscale()
    if img.get_precision() != Gimp.Precision.U8_NON_LINEAR:
        img.convert_precision(Gimp.Precision.U8_NON_LINEAR)
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, img, Gio.File.new_for_path(path), None)
    img.delete()


def export_bytes(data, W, H, path, fmt="R'G'B' u8", grey=False):
    img, L = scratch(W, H, data, fmt)
    export(img, path, grey)
    img.delete()


def seam_score(data, W, H, ch=3):
    """Mean abs difference across the wrap seams relative to the mean difference of
    interior neighbour pairs at unaligned positions (~1 = seamless; >2 suspicious)."""
    def px(x, y):
        i = (y * W + x) * ch
        return sum(data[i:i + min(ch, 3)])

    fr = (0.137, 0.291, 0.377, 0.473, 0.619, 0.733, 0.859, 0.947)
    seam = interior = 0
    for y in range(0, H, 2):
        seam += abs(px(W - 1, y) - px(0, y))
        for f in fr:
            x = int(W * f)
            interior += abs(px(x - 1, y) - px(x, y)) / len(fr)
    for x in range(0, W, 2):
        seam += abs(px(x, H - 1) - px(x, 0))
        for f in fr:
            y = int(H * f)
            interior += abs(px(x, y - 1) - px(x, y)) / len(fr)
    return seam / max(1e-6, interior)


def seam_crop(src_layer_or_bytes, W, H, path, fmt="R'G'B' u8", half=128, zoom=2):
    """Zoomed window centred on the tile corner (where all four seams meet)."""
    img, L = scratch(W, H, src_layer_or_bytes, fmt)
    data = read(L, fmt, (-half, -half, 2 * half, 2 * half), LOOP)
    img.delete()
    img2, L2 = scratch(2 * half, 2 * half, data, fmt)
    Gimp.context_set_interpolation(Gimp.InterpolationType.NONE)
    img2.scale(2 * half * zoom, 2 * half * zoom)
    Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
    export(img2, path)
    img2.delete()


def tiled_preview(data, W, H, path, fmt="R'G'B' u8", size=1024, grey=False):
    img = new_image(2 * W, 2 * H)
    L = layer(img, "tile", alpha=False)
    for oy in (0, H):
        for ox in (0, W):
            write(L, data, fmt, (ox, oy, W, H))
    Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
    img.scale(size, size)
    export(img, path, grey)
    img.delete()


def lit_bytes(albedo, nb, light=LIGHT, ambient=0.42):
    """Albedo shaded by the normal map (Lambert, light from upper left) for QA previews."""
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln
    out = bytearray(len(albedo))
    for i in range(0, len(nb), 3):
        nx = nb[i] / 127.5 - 1
        ny = nb[i + 1] / 127.5 - 1
        nz = nb[i + 2] / 127.5 - 1
        d = nx * lx + ny * ly + nz * lz
        s = ambient + (1 - ambient) * (d if d > 0 else 0) / lz * 0.85
        out[i] = min(255, int(albedo[i] * s))
        out[i + 1] = min(255, int(albedo[i + 1] * s))
        out[i + 2] = min(255, int(albedo[i + 2] * s))
    return bytes(out)


class TexSet:
    """Book-keeping for one material set: output paths, exports, previews, QA."""

    def __init__(self, name, size=1024, seed=1):
        self.name = name
        self.S = size
        self.rng = random.Random(seed)
        self.dir = os.path.join(TEX_DIR, name)
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(PREVIEW_DIR, exist_ok=True)
        self.t0 = time.time()
        self.albedo = None
        self.nb = None
        self.files = []
        Gimp.context_push()
        Gimp.context_set_antialias(True)
        Gimp.context_set_feather(False)
        Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
        log("==", name)

    def path(self, kind):
        return os.path.join(self.dir, "%s_%s.png" % (self.name, kind))

    def save_albedo(self, src):
        """src: work image (flattened on export) or layer."""
        p = self.path("albedo")
        export(src, p)
        img = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(p))
        self.albedo = read(img.get_layers()[0], "R'G'B' u8")
        img.delete()
        self.files.append(p)
        log("  albedo seam %.2f" % seam_score(self.albedo, self.S, self.S))
        return self.albedo

    def save_normal(self, h, strength, name="normal"):
        img, L, nb = normal_map(h, self.S, self.S, strength)
        p = self.path(name)
        export(img, p)
        img.delete()
        self.nb = nb
        self.files.append(p)
        log("  normal seam %.2f" % seam_score(nb, self.S, self.S))
        return nb

    def save_grey(self, kind, data):
        """data: Y' u8 bytes or float array 0..1."""
        if isinstance(data, array.array):
            data = to_u8(data)
        p = self.path(kind)
        export_bytes(data, self.S, self.S, p, "Y' u8", grey=True)
        self.files.append(p)
        return p

    def previews(self):
        S = self.S
        if self.albedo is not None:
            tiled_preview(self.albedo, S, S, os.path.join(PREVIEW_DIR, self.name + "_tiled.png"))
            seam_crop(self.albedo, S, S, os.path.join(PREVIEW_DIR, self.name + "_seam.png"))
            if self.nb is not None:
                tiled_preview(lit_bytes(self.albedo, self.nb), S, S,
                              os.path.join(PREVIEW_DIR, self.name + "_lit.png"))
        elif self.nb is not None:
            tiled_preview(self.nb, S, S, os.path.join(PREVIEW_DIR, self.name + "_tiled.png"))

    def done(self):
        self.previews()
        Gimp.context_pop()
        for im in Gimp.get_images():
            im.delete()
        log("  %s done in %.1fs" % (self.name, time.time() - self.t0))
