"""Terrain material sets (tile every ~8 m in game): grass, dirt, rock, sand,
forest_floor, snow, plus the water normal map."""
import math
import array

from rwtex import *  # noqa: F401,F403
from rwtex import _clip  # noqa: F401


def shifted(base, name, hue=0.0, light=0.0, sat=0.0, mask=None, opacity=100.0):
    """Copy of `base` with a hue/lightness/saturation shift, optionally masked.
    Used for painted strokes that take their colour from what is under them."""
    L = dup(base, name, opacity=opacity)
    L.hue_saturation(Gimp.HueRange.ALL, float(hue), float(light), float(sat), 0.0)
    if mask is not None:
        set_mask(L, mask)
    return L


def scatter(S, rng, dens, n, lo, hi):
    """Rejection-sample n candidate points, keeping them where the density field is high."""
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        if rng.random() < smoothstep(lo, hi, dens[int(y) * S + int(x)]):
            out.append((x, y))
    return out


def tufts(pts, rng, n=(2, 3), length=(8, 15), width=(2.4, 3.6), spread=0.7, jit=3.0):
    polys = []
    for x, y in pts:
        for _ in range(rng.randint(*n)):
            polys.append(blade_pts(x + rng.uniform(-jit, jit), y + rng.uniform(-jit * 0.6, jit * 0.6),
                                   rng.uniform(*length), rng.uniform(*width),
                                   -math.pi / 2 + rng.uniform(-spread, spread), rng.uniform(-0.35, 0.35)))
    return polys


def ramp_color(luts, t):
    i = int(clamp(t) * 255)
    return (luts[0][i] / 255.0, luts[1][i] / 255.0, luts[2][i] / 255.0)


def spine(x, y, length, ang, bend, t):
    """Point at fraction t along a blade made by blade_pts(x, y, length, ..., ang, bend)."""
    px, py = t * length, bend * t * t * length
    ca, sa = math.cos(ang), math.sin(ang)
    return x + px * ca - py * sa, y + px * sa + py * ca


def clump_blades(cx, cy, rng, tone, luts, n=(7, 11), length=(20, 36), width=(5.0, 8.0),
                 spread=1.0, tips=2, tip_lift=0.22, hv=(0.35, 0.6)):
    """One painted tuft: blades fanned upward, back (dark) to front (light), lighter tips.
    Returns colour items and height items (grey = blade rank)."""
    items, hitems = [], []
    nb = rng.randint(*n)
    for k in range(nb):
        rank = k / max(1, nb - 1)
        t = clamp(0.1 + 0.5 * tone + 0.4 * rank + rng.uniform(-0.07, 0.07))
        col = quant(ramp_color(luts, t), 6)
        ang = -math.pi / 2 + rng.uniform(-spread, spread) * (1 - 0.35 * rank)
        ln = rng.uniform(*length) * (1 - 0.25 * rank)
        wd = rng.uniform(*width)
        bend = rng.uniform(-0.3, 0.3)
        bx = cx + rng.uniform(-11, 11)
        by = cy + rng.uniform(-5, 3) + rank * 5
        poly = blade_pts(bx, by, ln, wd, ang, bend)
        items.append((poly, col))
        g = round((hv[0] + hv[1] * rank) * 10) / 10
        hitems.append((poly, (g, g, g)))
        if k >= nb - tips:
            tx, ty = spine(bx, by, ln, ang, bend, 0.55)
            tip = blade_pts(tx, ty, ln * 0.45, wd * 0.5, ang + bend * 1.1, bend)
            items.append((tip, quant(ramp_color(luts, t + tip_lift), 6)))
            hitems.append((tip, (1.0, 1.0, 1.0)))
    return items, hitems


def paint_tufts(img, S, centres, rng, tone, luts, **kw):
    """Paint tufts at the given centres (top to bottom) into a new layer; returns the
    layer and a height field (float array) of the blades."""
    items, hitems = [], []
    for cx, cy in sorted(centres, key=lambda p: p[1]):
        i = (int(cy) % S) * S + int(cx) % S
        a, b = clump_blades(cx, cy, rng, tone[i], luts, **kw)
        items += a
        hitems += b
    L = layer(img, "tufts")
    fill_many(L, items)
    himg = new_image(S)
    hl = layer(himg, "h", fill="#000000", alpha=False)
    fill_many(hl, hitems)
    h = read_f(hl)
    himg.delete()
    return L, h


def make_grass():
    T = TexSet("grass", seed=11)
    S, rng = T.S, T.rng
    img = new_image(S)

    # ground between the tufts: deep green with very soft large variation
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=2, seed=101)
    normalize(base)
    blur(base, 16)
    gradient_map(base, [(0, "#285a30"), (1, "#3b7c3b")])

    tone = field_noise(S, 3, 3, detail=2, seed=105)
    luts = ramp_luts([(0, "#2e6834"), (0.3, "#3f893d"), (0.6, "#58a345"), (0.85, "#7cbd4e"),
                      (1, "#a8d568")])
    centres = poisson(S, S, 30, rng)
    tl, hb = paint_tufts(img, S, centres, rng, tone, luts)

    # very large hue drift: blue-green <-> yellow-green
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=30)
    noise(hue, 2, 2, detail=2, seed=102)
    normalize(hue)
    gradient_map(hue, [(0, "#2f6680"), (0.5, "#808080"), (1, "#e8d24c")])

    hn = field_noise(S, 4, 4, detail=3, seed=103)
    h = array.array("f", [0.25 * hn[i] + 0.75 * hb[i] for i in range(S * S)])
    h = field_blur(h, S, S, 0.7)
    nb = T.save_normal(h, 3.5)
    overlay_grey(img, light_from_normal(nb, 0.8), LM.OVERLAY, 35, "light")
    T.save_albedo(img)
    T.done()


def make_dirt():
    T = TexSet("dirt", seed=31)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 4, 4, detail=3, seed=301)
    normalize(base)
    posterize(base, 6)
    blur(base, 6)
    hbase = read_f(base)
    gradient_map(base, [(0, "#4a3322"), (0.35, "#63432c"), (0.7, "#7b5638"), (1, "#936b48")])
    bl = layer(img, "blotch", alpha=False, mode=LM.SOFTLIGHT, opacity=50)
    noise(bl, 8, 8, detail=2, seed=302)
    normalize(bl)
    posterize(bl, 4)
    blur(bl, 3)
    gradient_map(bl, [(0, "#3a2a40"), (0.5, "#808080"), (1, "#f2c890")])
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=30)
    noise(hue, 2, 2, detail=2, seed=303)
    normalize(hue)
    gradient_map(hue, [(0, "#4a5a80"), (0.5, "#808080"), (1, "#f0a050")])

    # painted pebbles + a few tiny grit specks
    palette = ["#8b7d6b", "#a08f78", "#7a6a5c", "#b09a7c", "#8c6f58", "#6f6560", "#9a7b62"]
    peb = []
    for x, y in poisson(S, S, 38, rng):
        if rng.random() > 0.42:
            continue
        r = rng.uniform(5, 11) if rng.random() < 0.8 else rng.uniform(11, 16)
        poly = blob_pts(x, y, r, rng, 16, 0.3, rng.uniform(0, 3.14), rng.uniform(0.65, 1.0))
        peb.append((poly, quant(jitter(rng.choice(palette), rng, 0.02, 0.1, 0.08), 8)))
    grit = []
    for x, y in poisson(S, S, 16, rng):
        if rng.random() < 0.18:
            grit.append((blob_pts(x, y, rng.uniform(1.6, 3.0), rng, 8, 0.3), quant(
                jitter(rng.choice(["#5a3c26", "#a8865f", "#3f2a1c"]), rng), 8)))
    drop_shadow(img, [p for p, c in peb], 2.5, 3.5, "#3b2414", 60, 2.0)
    gl = layer(img, "grit")
    fill_many(gl, grit)
    pl = layer(img, "pebbles")
    fill_many(pl, peb)

    pm = mask_of(S, [p for p, c in peb])
    ph = dome(pm, S, 8)
    hb = field_blur(hbase, S, S, 3)
    h = array.array("f", [0.35 * hb[i] + 0.65 * ph[i] for i in range(S * S)])
    finish_lighting(img, T, h, 5.0, 1.0, 60, "#2a1a24", 45, 4, 3.0, "#ffe2b0", 45)
    T.save_albedo(img)
    T.done()


def split_poly(poly, rng, parts=2):
    """Split a convex polygon by random lines through (near) its centroid."""
    out = [poly]
    for _ in range(parts - 1):
        big = max(out, key=poly_area)
        out.remove(big)
        cx, cy = centroid(big)
        cx += rng.uniform(-12, 12)
        cy += rng.uniform(-12, 12)
        a = rng.uniform(0, math.pi)
        nx, ny = math.cos(a), math.sin(a)
        A = _clip(big, cx, cy, nx, ny, 0.0)
        B = _clip(big, cx, cy, -nx, -ny, 0.0)
        out += [p for p in (A, B) if len(p) >= 3]
    return out


def clip_convex(poly, clipper):
    """Clip polygon by a convex clipper polygon (either winding)."""
    cx, cy = centroid(clipper)
    out = poly
    n = len(clipper)
    for i in range(n):
        (ax, ay), (bx, by) = clipper[i], clipper[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        nx, ny = ey, -ex
        d = math.hypot(nx, ny) or 1.0
        nx, ny = nx / d, ny / d
        if (cx - ax) * nx + (cy - ay) * ny > 0:  # make n point outward
            nx, ny = -nx, -ny
        out = _clip(out, ax, ay, nx, ny, 0.0)
        if len(out) < 3:
            return []
    return out


def make_rock():
    T = TexSet("rock", seed=41)
    S, rng = T.S, T.rng
    # chunky blocks separated by cracks; each block is a dome cut into flat facets
    big_pts = poisson(S, S, 190, rng)
    blocks = voronoi(big_pts, S, S, gap=6.0, sx=0.85, sy=1.0)
    blocks = [wobble(b, rng, 2.0, 20) for b in blocks]
    bm = mask_of(S, blocks)
    dome_h = bevel(distance_field(bm, S, S, 100), 85, "round")
    smalls = voronoi(poisson(S, S, 56, rng), S, S)
    ids = id_field(S, smalls)

    def D(x, y):
        return dome_h[(int(y) % S) * S + int(x) % S]

    planes = []
    for f in smalls:
        cx, cy = centroid(f)
        e = 8
        gx = (D(cx + e, cy) - D(cx - e, cy)) / (2 * e) + rng.uniform(-0.003, 0.003)
        gy = (D(cx, cy + e) - D(cx, cy - e)) / (2 * e) + rng.uniform(-0.003, 0.003)
        planes.append((cx, cy, D(cx, cy), gx, gy))
    fh = facet_planes(S, ids, planes)
    fh = field_blur(fh, S, S, 1.0)
    edge = bevel(distance_field(bm, S, S, 10), 6, "round")
    cracks = []
    for _ in range(14):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        cracks.append(crack_path(x, y, rng.uniform(40, 100), rng.uniform(0, 6.28), rng, 9, 0.45))
    ck = strokes_field(S, cracks, 3.0, 0.8)
    hn = field_noise(S, 8, 8, detail=3, seed=402)
    h = array.array("f", [edge[i] * (0.2 + 0.8 * max(0.0, fh[i])) + 0.012 * hn[i] - 0.06 * ck[i]
                          for i in range(S * S)])

    img = new_image(S)
    layer(img, "gap", fill="#34374f", alpha=False)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=403)
    normalize(base)
    posterize(base, 5)
    blur(base, 8)
    gradient_map(base, [(0, "#6a7590"), (0.4, "#7c87a0"), (0.75, "#8f98ae"), (1, "#a0a8bb")])
    set_mask(base, bm)
    bl = layer(img, "blocks", mode=LM.OVERLAY, opacity=45)
    fill_many(bl, [(b, quant(jitter("#808080", rng, 0.0, 0.0, 0.10), 6)) for b in blocks])
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=35)
    noise(hue, 2, 2, detail=2, seed=404)
    normalize(hue)
    gradient_map(hue, [(0, "#4a4a90"), (0.5, "#808080"), (1, "#e6c494")])
    nb = finish_lighting(img, T, h, 28.0, 0.9, 80, "#262844", 55, 4, 3.0, "#f2f2ff", 40, 146, 3.0)
    tint_layer(img, "#34365c", shade_mask(nb, 104, 2.5), 35, LM.MULTIPLY, "shade")
    cr = layer(img, "cracks")
    for p in cracks:
        stroke(cr, p, "#2e2f48", 3.0)
    lip = layer(img, "crack_lip", opacity=45)
    for p in cracks:
        stroke(lip, [(x + 2.0, y + 2.0) for x, y in p], "#d4daee", 1.5)
    T.save_albedo(img)
    T.done()


def make_sand():
    T = TexSet("sand", seed=51)
    S, rng = T.S, T.rng
    warp = field_noise(S, 3, 3, detail=2, seed=501)
    warp2 = field_noise(S, 6, 2, detail=2, seed=502)
    period = S / 16.0

    def prof(u):
        u -= math.floor(u)
        return smoothstep(0.0, 0.72, u) if u < 0.72 else 1.0 - smoothstep(0.72, 1.0, u)

    lut = [prof(i / 1024.0) for i in range(1024)]
    h = array.array("f", [0.0]) * (S * S)
    for y in range(S):
        row = y * S
        for x in range(S):
            i = row + x
            u = (y + 70.0 * (warp[i] - 0.5) + 18.0 * (warp2[i] - 0.5)) / period
            h[i] = lut[int((u - math.floor(u)) * 1024) & 1023]
    h = field_blur(h, S, S, 1.5)
    hn = field_noise(S, 3, 3, detail=3, seed=503)
    h = array.array("f", [0.55 * h[i] + 0.45 * hn[i] for i in range(S * S)])

    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=504)
    normalize(base)
    posterize(base, 6)
    blur(base, 10)
    gradient_map(base, [(0, "#c49a62"), (0.4, "#d4ad74"), (0.75, "#e2c08a"), (1, "#ecd09e")])
    rip = grey_layer(img, to_u8(h), "ripples", mode=LM.SOFTLIGHT, opacity=55)
    gradient_map(rip, [(0, "#7a5a70"), (0.5, "#808080"), (1, "#fff0c8")])
    grains = []
    for x, y in poisson(S, S, 14, rng):
        if rng.random() < 0.12:
            grains.append((blob_pts(x, y, rng.uniform(1.4, 2.6), rng, 8, 0.3),
                           quant(rng.choice(["#a07850", "#f8e8c0", "#b88c60", "#8a6a58"]), 8)))
    gl = layer(img, "grains", opacity=80)
    fill_many(gl, grains)
    finish_lighting(img, T, h, 3.5, 0.9, 50, None, 0, hi_col="#fff6dc", hi_op=30, hi_lo=140)
    T.save_albedo(img)
    T.done()


def make_forest_floor():
    T = TexSet("forest_floor", seed=61)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 4, 4, detail=3, seed=601)
    normalize(base)
    posterize(base, 5)
    blur(base, 6)
    gradient_map(base, [(0, "#2a2618"), (0.5, "#3b3520"), (1, "#4d4428")])
    moss = layer(img, "moss", alpha=False, mode=LM.NORMAL, opacity=70)
    noise(moss, 3, 3, detail=3, seed=602)
    normalize(moss)
    mm = read(moss, "Y' u8").translate(lut_bytes(lambda v: smoothstep(0.55, 0.75, v)))
    gradient_map(moss, [(0, "#2e4622"), (1, "#47632b")])
    set_mask(moss, mm)

    leaf_cols = [["#3d3020", "#4a3a22", "#3a4022"],
                 ["#6b4a2a", "#5e5a2c", "#7a5530", "#4f5a2a"],
                 ["#8a5a2e", "#9b6b35", "#a08a3a", "#6f7a34", "#b07a3c"]]
    hsum = array.array("f", [0.0]) * (S * S)
    for depth, (count, lmin, lmax) in enumerate([(520, 24, 40), (380, 26, 44), (170, 28, 46)]):
        items, polys, veins = [], [], []
        for _ in range(count):
            x, y = rng.uniform(0, S), rng.uniform(0, S)
            ln = rng.uniform(lmin, lmax)
            wd = ln * rng.uniform(0.4, 0.55)
            a = rng.uniform(0, 2 * math.pi)
            poly = leaf_pts(x, y, ln, wd, a, 8, rng.uniform(-0.15, 0.15))
            items.append((poly, quant(jitter(rng.choice(leaf_cols[depth]), rng, 0.02, 0.1, 0.1), 8)))
            polys.append(poly)
            if depth == 2:
                veins.append(leaf_pts(x, y, ln * 0.85, 2.2, a, 6))
        drop_shadow(img, polys, 2.0, 3.0, "#1a160e", 55, 2.0, "leaf_shadow%d" % depth)
        L = layer(img, "leaves%d" % depth)
        fill_many(L, items)
        if veins:
            vl = layer(img, "veins", opacity=55)
            fill_polys(vl, veins, "#4a3018")
        m = from_u8(mask_of(S, polys))
        for i in range(S * S):
            if m[i] > 0.0:
                hsum[i] = max(hsum[i], (0.35 + 0.3 * depth) * m[i])
    twigs = []
    for _ in range(16):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(60, 140)
        twigs.append(polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 4, 8))
    drop = layer(img, "twig_shadow", mode=LM.MULTIPLY, opacity=50)
    for p in twigs:
        stroke(drop, [(x + 2, y + 3) for x, y in p], "#1a140c", 6)
    blur(drop, 1.5)
    tw = layer(img, "twigs")
    for p in twigs:
        stroke(tw, p, "#5a3a22", 5)
    twh = layer(img, "twig_hi", opacity=60)
    for p in twigs:
        stroke(twh, [(x - 1, y - 1.2) for x, y in p], "#9a7048", 1.8)
    tk = strokes_field(S, twigs, 5.0, 1.0)
    hn = field_noise(S, 5, 5, detail=3, seed=603)
    h = array.array("f", [0.25 * hn[i] + 0.75 * max(hsum[i], 0.9 * tk[i]) for i in range(S * S)])
    h = field_blur(h, S, S, 1.0)
    finish_lighting(img, T, h, 4.0, 0.9, 50, "#120e10", 40, 4, 3.0, "#e8d8a0", 25)
    T.save_albedo(img)
    T.done()


def make_snow():
    T = TexSet("snow", seed=71)
    S, rng = T.S, T.rng
    img = new_image(S)
    # wind drifts: warped asymmetric ridges (long gentle windward side, short lee side)
    w1 = field_noise(S, 2, 2, detail=2, seed=701)
    w2 = field_noise(S, 4, 3, detail=2, seed=705)
    period = S / 5.0

    def prof(u):
        return smoothstep(0.0, 0.8, u) if u < 0.8 else 1.0 - smoothstep(0.8, 1.0, u)

    lut = [prof(i / 1024.0) for i in range(1024)]
    h = array.array("f", [0.0]) * (S * S)
    for y in range(S):
        row = y * S
        for x in range(S):
            i = row + x
            u = (y + 150.0 * (w1[i] - 0.5) + 40.0 * (w2[i] - 0.5)) / period
            h[i] = lut[int((u - math.floor(u)) * 1024) & 1023]
    big = field_noise(S, 2, 2, detail=3, seed=702)
    hn = field_noise(S, 8, 8, detail=2, seed=703)
    h = array.array("f", [0.6 * h[i] + 0.37 * big[i] + 0.03 * hn[i] for i in range(S * S)])
    h = field_blur(h, S, S, 2.0)
    base = grey_layer(img, to_u8(big), "base")
    gradient_map(base, [(0, "#dbe5f5"), (0.5, "#e9f0fa"), (1, "#f8fbff")])
    nb = finish_lighting(img, T, h, 40.0, 1.0, 75, None, 0, hi_col="#ffffff", hi_op=55, hi_lo=140, hi_gain=4)
    tint_layer(img, "#7a8cd2", shade_mask(nb, 124, 2.5), 50, LM.MULTIPLY, "cool_shade")
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=25)
    noise(hue, 3, 3, detail=2, seed=704)
    normalize(hue)
    gradient_map(hue, [(0, "#7a70c0"), (0.5, "#808080"), (1, "#e0f4ff")])
    sp = []
    for x, y in poisson(S, S, 40, rng):
        if rng.random() < 0.12:
            sp.append(ellipse_pts(x, y, rng.uniform(1.2, 2.2), rng.uniform(1.2, 2.2), 0, 8))
    spl = layer(img, "sparkle", opacity=70)
    fill_polys(spl, sp, "#ffffff")
    T.save_albedo(img)
    # the strong normal above only drives the baked albedo shading; ship a gentler one
    T.save_normal(field_blur(h, S, S, 4.0), 16.0)
    T.done()


def make_water():
    T = TexSet("water", seed=81)
    S = T.S
    a = field_noise(S, 2, 4, detail=3, seed=801)
    b = field_noise(S, 5, 8, detail=2, seed=802)
    c = field_noise(S, 11, 14, detail=1, seed=803)
    # rounded crests: inverted turbulent noise has soft ridges where the noise crosses zero
    img, L = scratch(S)
    noise(L, 3, 5, detail=2, seed=804, turbulent=True)
    normalize(L)
    t = read_f(L)
    img.delete()
    h = array.array("f", [0.4 * a[i] + 0.22 * b[i] + 0.1 * c[i] + 0.28 * (1.0 - t[i]) ** 2
                          for i in range(S * S)])
    h = field_blur(h, S, S, 2.0)
    T.save_normal(h, 14.0)
    T.done()


SETS = {
    "grass": make_grass,
    "dirt": make_dirt,
    "rock": make_rock,
    "sand": make_sand,
    "forest_floor": make_forest_floor,
    "snow": make_snow,
    "water": make_water,
}
