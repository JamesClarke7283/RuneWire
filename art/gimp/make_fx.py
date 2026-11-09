"""make_fx.py: RuneWire VFX sprites (white/greyscale on transparent, tinted in game).

Writes assets/textures/fx/vfx_*.png (the noise_* files belong to another generator).
Run from the project root:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_fx.py").read())' --quit

Optional: set RW_ONLY="fx_ring,fx_star" in the environment to rebuild a subset.
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

OUT = R.FX_DIR
W = "#ffffff"


def radial_profile(fn, n=48):
    """Sample an alpha profile fn(r in 0..1) into white gradient stops."""
    return [(i / n, W, max(0.0, min(1.0, fn(i / n)))) for i in range(n + 1)]


# --------------------------------------------------------------------------------------
def fx_glow():
    """Soft radial glow: bright core + wide halo, alpha reaches 0 before the edge."""
    S = 256
    p = Pic(S, S)
    lay = p.layer("glow")

    def f(r):
        tail = 0.55 * math.exp(-(1 / 0.17) ** 2) + 0.45 * math.exp(-(1 / 0.45) ** 2)
        v = 0.55 * math.exp(-(r / 0.17) ** 2) + 0.45 * math.exp(-(r / 0.45) ** 2)
        return (v - tail) / (1 - tail)

    p.grad(lay, radial_profile(f, 64), 128, 128, 128 + 126, 128, kind=R.RADIAL, segments=128)
    p.save(os.path.join(OUT, "vfx_glow.png"), keep_transparent_rgb=True)
    p.close()


# --------------------------------------------------------------------------------------
def fx_spark():
    """Four-point sparkle with a smaller diagonal twinkle and a soft halo."""
    S = 256
    c = S / 2
    p = Pic(S, S)
    halo = p.layer("halo")
    p.grad(halo, radial_profile(lambda r: 0.55 * math.exp(-(r / 0.38) ** 2) * (1 - r)), c, c, c + 92, c,
           kind=R.RADIAL)
    diag = p.layer("diag")
    p.sel_poly(R.sparkle_pts(c, c, 64, 64, pinch=3.4, rot=math.pi / 4))
    p.fill(diag, W, opacity=70)
    main = p.layer("main")
    p.sel_poly(R.sparkle_pts(c, c, 120, 120, pinch=3.1))
    p.fill(main, W)
    p.sel_none()
    g = p.glow(main, W, grow=2, blur=7, opacity=55)
    p.save(os.path.join(OUT, "vfx_spark.png"), keep_transparent_rgb=True)
    p.close()


# --------------------------------------------------------------------------------------
def fx_smoke():
    """Cartoon smoke puff: clean lobed silhouette, white top-left, soft toon shadow band."""
    S = 256
    p = Pic(S, S)
    lobes = [(128, 150, 72), (80, 126, 48), (122, 92, 50), (172, 104, 46), (198, 156, 42), (62, 172, 40),
             (110, 196, 44), (164, 194, 44)]
    p.sel_none()
    for x, y, r in lobes:
        p.sel_ellipse(x, y, r, op=R.ADD)
    p.round_sel(concave=6)
    ch = p.save_sel()
    base = p.layer("base")
    p.load_sel(ch)
    p.fill(base, "#f4f4f4")
    # soft large-scale core shading
    p.crescent(ch, 36, 40, feather=26)
    p.fill(base, "#b9b9b9", opacity=70)
    # defined toon shadow band, lower-right
    p.crescent(ch, 15, 18, feather=4)
    p.fill(base, "#a6a6a6", opacity=85)
    # lobe creases: a short soft arc just outside the top-left edge of each front lobe
    for x, y, r in lobes:
        if y < 150:
            continue
        p.sel_ellipse(x, y, r)
        p.grow(6)
        p.sel_ellipse(x, y, r, op=R.SUB)
        p.sel_ellipse(x - r * 0.5, y - r * 0.6, r * 0.9, op=R.INTER)
        p.feather(4)
        p.load_sel(ch, R.INTER)
        p.fill(base, "#c9c9c9", opacity=55)
    # highlights on the upper lobes
    for x, y, r in lobes:
        if y > 160:
            continue
        p.sel_ellipse(x - r * 0.26, y - r * 0.32, r * 0.44, r * 0.3)
        p.feather(r * 0.18)
        p.load_sel(ch, R.INTER)
        p.fill(base, W, opacity=95)
    # bright rim, top-left
    p.crescent(ch, -6, -7, feather=3)
    p.fill(base, W)
    p.sel_none()
    p.blur(base, 1.0)
    p.save(os.path.join(OUT, "vfx_smoke.png"))
    p.close()


# --------------------------------------------------------------------------------------
def flame_outline(cx, base_y, h, w, lean=0.0):
    """Cartoon flame silhouette (main tip + two side tongues) as a dense polygon."""
    # unit frame: x in [-0.5, 0.5], y from 0 (bottom) to -1 (top); tips are sharp
    ctrl = [(0.0, 0.0), (0.27, -0.03), (0.44, -0.14), (0.5, -0.3), (0.45, -0.45), (0.36, -0.56),
            (0.46, -0.74), (0.24, -0.62), (0.2, -0.76), (0.12, -0.88), (0.06, -1.0), (-0.04, -0.85),
            (-0.13, -0.74), (-0.33, -0.83), (-0.27, -0.6), (-0.4, -0.5), (-0.49, -0.33), (-0.47, -0.16),
            (-0.36, -0.05), (-0.19, -0.005)]
    tips = (6, 10, 13)
    pts = R.spline(ctrl, sharp=tips, closed=True, samples=16)
    return [(cx + (x + lean * y) * w, base_y + y * h) for x, y in pts]


def fx_flame():
    """Flame: light-grey teardrop body with three tongues, white core, faint glow."""
    S = 256
    p = Pic(S, S)
    outer = flame_outline(128, 240, 226, 168)
    inner = flame_outline(127, 232, 136, 92)
    body = p.layer("body")
    p.sel_poly(outer)
    ch = p.save_sel()
    p.grad(body, [(0, "#a8a8a8"), (0.5, "#cdcdcd"), (1, "#ececec")], 128, 18, 128, 238)
    # toon shading band down the right side
    p.crescent(ch, 16, 6, feather=6)
    p.fill(body, "#8f8f8f", opacity=50)
    # bright left rim
    p.crescent(ch, -6, -2, feather=2)
    p.fill(body, "#f4f4f4", opacity=80)
    core = p.layer("core")
    p.sel_poly(inner)
    p.feather(2)
    p.fill(core, W)
    p.sel_ellipse(127, 200, 34, 28)
    p.feather(12)
    p.fill(core, W)
    p.sel_none()
    p.glow(body, W, grow=1, blur=6, opacity=28)
    p.save(os.path.join(OUT, "vfx_flame.png"))
    p.close()


# --------------------------------------------------------------------------------------
def fx_ring():
    """Shockwave ring: crisp bright band, soft inner falloff, short outer glow."""
    S = 512
    c = S / 2
    p = Pic(S, S)
    lay = p.layer("ring")

    def f(r):
        rc, half = 0.86, 0.035
        d = r - rc
        if abs(d) <= half:
            return 1.0
        if d < 0:
            x = (-d - half) / 0.22
            return max(0.0, 0.85 * math.exp(-(x / 0.4) ** 2) * (1 - x) if x < 1 else 0.0)
        x = (d - half) / 0.06
        return max(0.0, 0.8 * (1 - x) ** 2) if x < 1 else 0.0

    p.grad(lay, radial_profile(f, 200), c, c, c + 250, c, kind=R.RADIAL, segments=200)
    p.save(os.path.join(OUT, "vfx_ring.png"), keep_transparent_rgb=True)
    p.close()


# --------------------------------------------------------------------------------------
def polygon_vertices(cx, cy, r, n, rot):
    return [(cx + r * math.cos(rot + TAU * i / n), cy + r * math.sin(rot + TAU * i / n)) for i in range(n)]


TAU = math.tau


def fx_rune_circle():
    """1024 px magic circle: concentric rings, glyph bands, octagram, hexagram, sigil."""
    S = 1024
    c = S / 2
    rng = random.Random(7)
    p = Pic(S, S)
    lines = p.layer("lines")

    def ring(r, w, op=100.0):
        pts = R.circle_pts(c, c, r, n=360)
        pts.append(pts[0])
        p.stroke(lines, [pts], w, W, opacity=op)

    # outer frame rings
    ring(490, 11)
    ring(462, 5)
    ring(392, 8)
    ring(378, 3)
    # outer glyph band (between 462 and 392): 30 glyphs facing outward
    gb = R.GlyphBatch()
    n_out = 30
    order = list(range(len(R.GLYPHS)))
    for i in range(n_out):
        a = -math.pi / 2 + TAU * (i + 0.5) / n_out
        g = R.GLYPHS[order[(i * 7) % len(order)]]
        gb.add(g, c + 427 * math.cos(a), c + 427 * math.sin(a), 40, ang=a + math.pi / 2, flip=(i % 5 == 3))
    gb.draw(p, lines, 6.5, W)
    # separators: small diamonds between glyphs on the band
    p.sel_none()
    for i in range(n_out):
        a = -math.pi / 2 + TAU * i / n_out
        x, y = c + 427 * math.cos(a), c + 427 * math.sin(a)
        d = [(x + 9 * math.cos(a), y + 9 * math.sin(a)), (x + 4.5 * math.cos(a + math.pi / 2), y + 4.5 * math.sin(a + math.pi / 2)),
             (x - 9 * math.cos(a), y - 9 * math.sin(a)), (x - 4.5 * math.cos(a + math.pi / 2), y - 4.5 * math.sin(a + math.pi / 2))]
        p.sel_poly(d, op=R.ADD)
    p.fill(lines, W)
    p.sel_none()
    # tick ring
    ticks = []
    for i in range(120):
        a = TAU * i / 120
        r0, r1 = (352, 372) if i % 10 == 0 else (362, 372)
        ticks.append([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))])
    p.stroke(lines, ticks, 3.5, W)
    ring(346, 4)
    # octagram (two squares) inscribed in r=346
    sq1 = polygon_vertices(c, c, 346, 4, -math.pi / 2)
    sq2 = polygon_vertices(c, c, 346, 4, -math.pi / 4)
    p.stroke(lines, [sq1 + [sq1[0]], sq2 + [sq2[0]]], 6, W, join=R.Gimp.JoinStyle.MITER)
    # node circles at octagram vertices
    nodes = polygon_vertices(c, c, 346, 8, -math.pi / 2)
    p.sel_none()
    for x, y in nodes:
        p.sel_ellipse(x, y, 30, op=R.ADD)
    p.sel_none()
    # punch the lines out under node discs so the node circles read cleanly
    for x, y in nodes:
        p.sel_ellipse(x, y, 30, op=R.ADD)
    lines.edit_clear()
    p.sel_none()
    node_rings = []
    for x, y in nodes:
        pts = R.circle_pts(x, y, 26, n=60)
        node_rings.append(pts + [pts[0]])
    p.stroke(lines, node_rings, 6, W)
    nb = R.GlyphBatch()
    for i, (x, y) in enumerate(nodes):
        a = -math.pi / 2 + TAU * i / 8
        nb.add(R.GLYPHS[(i * 5 + 2) % len(R.GLYPHS)], x, y, 26, ang=a + math.pi / 2)
    nb.draw(p, lines, 4.5, W)
    # inner circle + inner glyph band
    ring(250, 7)
    ring(196, 4)
    ib = R.GlyphBatch()
    n_in = 16
    for i in range(n_in):
        a = -math.pi / 2 + TAU * (i + 0.5) / n_in
        ib.add(R.GLYPHS[(i * 11 + 4) % len(R.GLYPHS)], c + 223 * math.cos(a), c + 223 * math.sin(a), 30,
               ang=a + math.pi / 2)
    ib.draw(p, lines, 5, W)
    # hexagram in r=196
    t1 = polygon_vertices(c, c, 196, 3, -math.pi / 2)
    t2 = polygon_vertices(c, c, 196, 3, math.pi / 2)
    p.stroke(lines, [t1 + [t1[0]], t2 + [t2[0]]], 5, W, join=R.Gimp.JoinStyle.MITER)
    # small arcs between hexagram tips (crescents)
    arcs = []
    for i in range(6):
        a = -math.pi / 2 + TAU * i / 6 + TAU / 12
        arcs.append(R.arc_pts(c + 150 * math.cos(a), c + 150 * math.sin(a), 22, a + 2.2, a + 4.1, n=20))
    p.stroke(lines, arcs, 4, W)
    # central sigil
    p.sel_ellipse(c, c, 92)
    lines.edit_clear()
    p.sel_none()
    ring(92, 6)
    ring(74, 3)
    rays = []
    for i in range(12):
        a = TAU * i / 12
        r0, r1 = (92, 112) if i % 3 == 0 else (92, 102)
        rays.append([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))])
    p.stroke(lines, rays, 4, W)
    cb = R.GlyphBatch()
    sig = [("l", [(0, -0.62), (0, 0.62)]), ("l", [(-0.44, -0.18), (0, -0.62), (0.44, -0.18)]),
           ("a", 0, 0.12, 0.34, 0.0, math.pi), ("d", 0, -0.08, 0.1), ("l", [(-0.3, 0.62), (0.3, 0.62)])]
    cb.add(sig, c, c, 100)
    cb.draw(p, lines, 7, W)
    # dots around inner ring
    p.sel_none()
    for i in range(24):
        a = TAU * (i + 0.5) / 24
        p.sel_ellipse(c + 272 * math.cos(a), c + 272 * math.sin(a), 4.5 if i % 2 else 7, op=R.ADD)
    p.fill(lines, W)
    p.sel_none()
    # glow: faint luminous fill + blurred halo of the linework
    fillg = p.layer("fill", below=lines)
    p.sel_ellipse(c, c, 490)
    p.grad(fillg, [(0, W, 0.12), (0.7, W, 0.05), (0.93, W, 0.16), (1.0, W, 0.0)], c, c, c + 490, c, kind=R.RADIAL)
    p.sel_none()
    p.glow(lines, W, grow=2, blur=9, opacity=55, name="halo")
    p.merge_all("circle")
    p.img.scale(992, 992)
    p.img.resize(S, S, 16, 16)
    for lay in p.img.get_layers():
        lay.resize_to_image_size()
    p.save(os.path.join(OUT, "vfx_rune_circle.png"), keep_transparent_rgb=True)
    p.close()


# --------------------------------------------------------------------------------------
def zigzag(x0, x1, y, rng, seg=(36, 64), amp=(10, 30), sub_amp=6):
    """Chunky cartoon zigzag from (x0, y) to (x1, y): big alternating kinks + small jitter."""
    xs = [x0]
    while xs[-1] < x1 - seg[0]:
        xs.append(xs[-1] + rng.uniform(*seg))
    xs[-1] = x1
    pts = []
    sign = 1
    for i, x in enumerate(xs):
        if i in (0, len(xs) - 1):
            pts.append((x, y))
        else:
            pts.append((x, y + sign * rng.uniform(*amp)))
            sign = -sign
    out = [pts[0]]
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        mx, my = (ax + bx) / 2 + rng.uniform(-6, 6), (ay + by) / 2 + rng.uniform(-sub_amp, sub_amp)
        out += [(mx, my), (bx, by)]
    return out


def fx_lightning():
    """Horizontal bolt strip 512x128, tiles along U (drawn 3x wide, centre cropped)."""
    W_, H = 512, 128
    p = Pic(W_ * 3, H)
    rng = random.Random(23)
    main = zigzag(0, W_, H / 2, rng)
    # short spurs from a few kinks, pointing outward and forward
    branches = []
    kinks = [i for i in range(2, len(main) - 2, 2) if abs(main[i][1] - H / 2) > 18]
    for i in rng.sample(kinks, min(3, len(kinks))):
        x, y = main[i]
        dirn = -1 if y < H / 2 else 1
        mid = (x + 12, y + dirn * 7)
        end = (x + 26, y + dirn * 12)
        branches.append([(x, y), mid, (end[0], max(24, min(H - 24, end[1])))])
    allmain = [[(x + k * W_, y) for x, y in main] for k in range(3)]
    allbr = [[(x + k * W_, y) for x, y in b] for k in range(3) for b in branches]
    wide = p.layer("wide")
    p.stroke(wide, allmain, 30, W)
    p.stroke(wide, allbr, 16, W)
    p.blur(wide, 12)
    wide.set_opacity(50)
    mid = p.layer("mid")
    p.stroke(mid, allmain, 16, W, join=R.Gimp.JoinStyle.MITER)
    p.stroke(mid, allbr, 9, W)
    p.blur(mid, 3.5)
    mid.set_opacity(80)
    core = p.layer("core")
    p.stroke(core, allmain, 8, W, join=R.Gimp.JoinStyle.MITER)
    p.stroke(core, allbr, 4.5, W, join=R.Gimp.JoinStyle.MITER)
    p.img.crop(W_, H, W_, 0)
    p.w = W_
    merged = p.merge_all("bolt")
    mask = merged.create_mask(R.Gimp.AddMaskType.WHITE)
    merged.add_mask(mask)
    p.sel_none()
    p.grad(mask, [(0, "#000000"), (0.16, "#ffffff"), (0.84, "#ffffff"), (1, "#000000")], 0, 0, 0, H)
    merged.remove_mask(R.Gimp.MaskApplyMode.APPLY)
    p.save(os.path.join(OUT, "vfx_lightning.png"), keep_transparent_rgb=True)
    p.close()


# --------------------------------------------------------------------------------------
def fx_star():
    """Chunky rounded five-point star with bevelled facets in greys (tints nicely)."""
    S = 256
    cx, cy = 128, 136
    p = Pic(S, S)
    r_out, r_in = 114, 52
    pts = R.star_pts(cx, cy, r_out, r_in, 5)
    star = p.layer("star")
    p.sel_poly(pts)
    p.round_sel(convex=12, concave=5)
    ch = p.save_sel()
    p.fill(star, W)
    # facets: the clockwise half of every arm is shaded
    p.sel_none()
    for i in range(5):
        tip = pts[2 * i]
        inner_r = pts[(2 * i + 1) % 10]
        p.sel_poly([(cx, cy), (tip[0], tip[1]), (inner_r[0], inner_r[1])], op=R.ADD)
    p.feather(1.0)
    p.load_sel(ch, R.INTER)
    p.fill(star, "#d2d2d2")
    # lower-right shadow rim and top-left highlight rim
    p.crescent(ch, 8, 9, feather=3)
    p.load_sel(ch, R.INTER)
    p.fill(star, "#a7a7a7", opacity=80)
    p.crescent(ch, -5, -6, feather=1.5)
    p.fill(star, W)
    p.sel_none()
    p.glow(star, W, grow=2, blur=8, opacity=30)
    p.save(os.path.join(OUT, "vfx_star.png"))
    p.close()


# --------------------------------------------------------------------------------------
def fx_scorch():
    """Scorch decal: charcoal burn with ragged radial edge, soot halo and splatter."""
    S = 512
    c = S / 2
    rng = random.Random(5)
    p = Pic(S, S)
    # irregular blob silhouette
    blob = []
    n = 180
    phases = [rng.uniform(0, TAU) for _ in range(6)]
    for i in range(n):
        a = TAU * i / n
        r = 150 + 18 * math.sin(3 * a + phases[0]) + 12 * math.sin(5 * a + phases[1]) + 8 * math.sin(9 * a + phases[2])
        r += 6 * math.sin(17 * a + phases[3])
        blob.append((c + r * math.cos(a), c + r * math.sin(a)))
    soot = p.layer("soot")
    p.sel_ellipse(c, c, 236)
    p.grad(soot, [(0, "#1c1c1c", 0.7), (0.6, "#1c1c1c", 0.45), (1, "#1c1c1c", 0.0)], c, c, c + 236, c, kind=R.RADIAL)
    p.sel_none()
    burn = p.layer("burn")
    p.sel_poly(blob)
    # radial spikes
    for k in range(26):
        a = TAU * k / 26 + rng.uniform(-0.08, 0.08)
        L = rng.uniform(175, 238)
        wdt = rng.uniform(0.05, 0.11)
        base_r = 120
        tri = [(c + base_r * math.cos(a - wdt), c + base_r * math.sin(a - wdt)),
               (c + L * math.cos(a), c + L * math.sin(a)),
               (c + base_r * math.cos(a + wdt), c + base_r * math.sin(a + wdt))]
        p.sel_poly(tri, op=R.ADD)
    # splatter dots
    for k in range(34):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(150, 228)
        p.sel_ellipse(c + rr * math.cos(a), c + rr * math.sin(a), rng.uniform(3, 11), op=R.ADD)
    p.round_sel(concave=4)
    ch = p.save_sel()
    p.grad(burn, [(0, "#2a2a2a"), (0.35, "#141414"), (0.75, "#101010"), (1, "#1a1a1a")], c, c, c + 230, c,
           kind=R.RADIAL)
    p.sel_none()
    p.blur(burn, 1.6)
    # mottled alpha: noise layer used as an eraser-ish lighten of the charred core
    ash = p.layer("ash", above=burn)
    p.load_sel(ch)
    p.shrink(30)
    p.feather(40)
    p.fill(ash, "#4a4a4a", opacity=60)
    p.sel_none()
    nz = p.noise_layer("mottle", scale=6, detail=4, seed=9, opacity=35, mode=R.OVERLAY, above=ash)
    p.clip_to(nz, ch)
    p.save(os.path.join(OUT, "vfx_scorch.png"))
    p.close()


ALL = [fx_glow, fx_spark, fx_smoke, fx_flame, fx_ring, fx_rune_circle, fx_lightning, fx_star, fx_scorch]
_only = [s for s in os.environ.get("RW_ONLY", "").split(",") if s]
R.run_all(ALL, only=_only or None, logpath="/tmp/rwui_fx_log.txt")
