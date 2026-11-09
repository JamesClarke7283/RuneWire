"""Building / prop material sets (1 UV unit = 2 m on models): stone_bricks, cobble,
wood_planks, wood_dark, bark, leaves, stone_rough, plaster, roof_tiles, rune_stone."""
import math
import array

from rwtex import *  # noqa: F401,F403
from rwtex import _clip  # noqa: F401


def make_stone_bricks():
    T = TexSet("stone_bricks", seed=21)
    S, rng = T.S, T.rng
    rows, gap = 8, 12.0
    rh = S / rows
    palette = ["#aaa092", "#aaa092", "#aaa092", "#bcb1a0", "#bcb1a0", "#9c9ca3", "#9c9ca3",
               "#b09e84", "#918b87"]
    bricks = []
    for r in range(rows):
        y0 = r * rh
        x = rng.uniform(0, S)
        for ln in row_lengths(S, rng, 200, 330):
            x0, x1 = x + gap / 2, x + ln - gap / 2
            ya, yb = y0 + gap / 2 + rng.uniform(-1, 1), y0 + rh - gap / 2 + rng.uniform(-1, 1)
            poly = rrect_pts(x0, ya, x1 - x0, yb - ya, rng.uniform(13, 20), segs=5)
            poly = wobble(poly, rng, 1.4, seg=22)
            bricks.append((poly, jitter(rng.choice(palette), rng, 0.01, 0.10, 0.06), rng.uniform(0.8, 1.0)))
            x += ln

    chips, cracks = [], []
    for poly, c, hs in bricks:
        x0, y0, x1, y1 = bbox(poly)
        if rng.random() < 0.4:
            cx = x0 + 4 if rng.random() < 0.5 else x1 - 4
            cy = y0 + 4 if rng.random() < 0.5 else y1 - 4
            chips.append(blob_pts(cx, cy, rng.uniform(10, 18), rng, irregular=0.5))
        if rng.random() < 0.13:
            sx = rng.uniform(x0 + 30, x1 - 30)
            top = rng.random() < 0.5
            sy = y0 + 4 if top else y1 - 4
            ang = (math.pi / 2 if top else -math.pi / 2) + rng.uniform(-0.6, 0.6)
            cracks.append(crack_path(sx, sy, rng.uniform(45, 85), ang, rng, 9, 0.55))

    full = mask_of(S, [b[0] for b in bricks])
    mask = mask_of(S, [b[0] for b in bricks], chips)
    tone = tone_of(S, [(b[0], b[2]) for b in bricks])
    d = distance_field(mask, S, S, 30)
    bev = bevel(d, 20, "round")
    dfull = distance_field(full, S, S, 12)
    chipbev = bevel(dfull, 8, "round")
    hn = field_noise(S, 6, 6, detail=4, seed=211)
    crk = strokes_field(S, cracks, 3.5)
    h = array.array("f", [
        max(bev[i] * tone[i], chipbev[i] * 0.45 * tone[i]) * (0.9 + 0.12 * hn[i]) + 0.04 * hn[i]
        - 0.4 * crk[i] * (1 if full[i] > 127 else 0)
        for i in range(S * S)])

    img = new_image(S)
    layer(img, "mortar", fill="#4c4652", alpha=False)
    mn = layer(img, "mortar_noise", alpha=False, mode=LM.OVERLAY, opacity=35)
    noise(mn, 12, 12, detail=3, seed=212)
    br = layer(img, "bricks")
    for poly, c, hs in bricks:
        fill_poly(br, poly, c)
    ch = layer(img, "chips")
    fill_polys(ch, chips, "#827a7c")
    set_mask(ch, full)
    fv = layer(img, "facevar", alpha=False, mode=LM.SOFTLIGHT, opacity=45)
    noise(fv, 5, 5, detail=3, seed=213)
    normalize(fv)
    gradient_map(fv, [(0, "#4c5672"), (0.5, "#808080"), (1, "#f4d9a6")])
    overlay_grey(img, row_gradient(S, rh, 0.60, 0.42, 0), LM.OVERLAY, 60, "rowlight")

    nb = T.save_normal(h, 6.0)
    overlay_grey(img, light_from_normal(nb, 1.0), LM.OVERLAY, 60, "light")
    occ, rid = cavity(h, S, S, 5, 4.0)
    tint_layer(img, "#2a2640", occ, opacity=60, mode=LM.MULTIPLY, name="occ", invert=True)
    tint_layer(img, "#3a3456", shade_mask(nb), opacity=30, mode=LM.MULTIPLY, name="bevel_shade")
    tint_layer(img, "#fff4d8", hilite(nb), opacity=55, mode=LM.SCREEN, name="bevel_hi")
    cr = layer(img, "cracks")
    for p in cracks:
        stroke(cr, p, "#3b3442", 3.4)
    hi = layer(img, "crack_hi", opacity=55)
    for p in cracks:
        stroke(hi, [(x + 2.0, y + 2.0) for x, y in p], "#ece2cf", 1.6)

    T.save_albedo(img)
    T.done()


# ---------------------------------------------------------------------------
# cobble
# ---------------------------------------------------------------------------

def make_cobble():
    T = TexSet("cobble", seed=91)
    S, rng = T.S, T.rng
    pal = ["#8a8f9c", "#9c958a", "#9a8574", "#b0aa9e", "#7d7b86", "#a08478", "#94989f"]
    stones = []
    for c in voronoi(poisson(S, S, 100, rng), S, S, gap=16.0):
        c = wobble(round_corners(c, 24, 5), rng, 3.0, 16)
        stones.append((c, quant(jitter(rng.choice(pal), rng, 0.015, 0.12, 0.08), 6), rng.uniform(0.75, 1.0)))
    mask = mask_of(S, [st[0] for st in stones])
    tone = tone_of(S, [(st[0], st[2]) for st in stones])
    hb = bevel(distance_field(mask, S, S, 44), 38, "round")
    hn = field_noise(S, 8, 8, detail=4, seed=911)
    h = array.array("f", [hb[i] * tone[i] * (0.9 + 0.1 * hn[i]) + 0.05 * hn[i] for i in range(S * S)])

    img = new_image(S)
    layer(img, "mortar", fill="#3d3a42", alpha=False)
    mn = layer(img, "mortar_noise", alpha=False, mode=LM.OVERLAY, opacity=40)
    noise(mn, 14, 14, detail=3, seed=912)
    grit = []
    for x, y in poisson(S, S, 9, rng):
        if rng.random() < 0.3:
            grit.append((blob_pts(x, y, rng.uniform(1.5, 3.2), rng, 8, 0.3),
                         quant(rng.choice(["#5d5862", "#2c2830", "#6e6670"]), 8)))
    gl = layer(img, "grit")
    fill_many(gl, grit)
    sl = layer(img, "stones")
    fill_many(sl, [(st[0], st[1]) for st in stones])
    fv = layer(img, "facevar", alpha=False, mode=LM.SOFTLIGHT, opacity=45)
    noise(fv, 6, 6, detail=3, seed=913)
    normalize(fv)
    gradient_map(fv, [(0, "#4c5672"), (0.5, "#808080"), (1, "#f4dcae")])
    set_mask(fv, mask)
    finish_lighting(img, T, h, 7.0, 1.0, 70, "#1e1a28", 60, 5, 3.5, "#fff2da", 50, 138, 4.0,
                    "#2c2a4c", 35)
    T.save_albedo(img)
    T.done()


# ---------------------------------------------------------------------------
# wood
# ---------------------------------------------------------------------------

def wood_grain(L, rng, S, y0, y1, base_col, n, knots, dark=0.6, light=1.18, size=(2.0, 3.2),
               amp=5.0, dark_op=75, light_op=40):
    """Paint grain lines flowing along x between y0 and y1 (periodic across the tile)."""
    lines = []
    for k in range(n):
        yy = y0 + (y1 - y0) * (k + 0.5) / n + rng.uniform(-0.3, 0.3) * (y1 - y0) / n
        lines.append(periodic_line(S, yy, rng, amp, (1, 2, 3, 4, 6), 12.0, knots))
    for i, pts in enumerate(lines):
        if rng.random() < 0.75:
            stroke(L, pts, mul(base_col, dark * rng.uniform(0.9, 1.08)), rng.uniform(*size),
                   "2. Hardness 075", dark_op * rng.uniform(0.6, 1.0))
        else:
            stroke(L, pts, mul(base_col, light), rng.uniform(1.2, 2.0), "2. Hardness 050", light_op)
    return lines


def knot_items(kx, ky, kr, rng, col):
    """Painted knot: dark outer ring, warm band, dark core."""
    a = rng.uniform(-0.15, 0.15)
    return [
        (ellipse_pts(kx, ky, kr * 1.5, kr * 0.75, a, 30), mul(col, 0.55)),
        (ellipse_pts(kx, ky, kr * 1.15, kr * 0.55, a, 28), mul(col, 0.85)),
        (ellipse_pts(kx, ky, kr * 0.75, kr * 0.38, a, 24), mul(col, 0.5)),
        (ellipse_pts(kx - kr * 0.15, ky - kr * 0.08, kr * 0.35, kr * 0.16, a, 16), mul(col, 0.35)),
    ]


def make_wood_planks():
    T = TexSet("wood_planks", seed=101)
    S, rng = T.S, T.rng
    rows, gap = 4, 8.0
    ph = S / rows
    pal = ["#b07a44", "#a46f3d", "#bb8650", "#9e6a3a"]
    boards, knots_all, nails = [], [], []
    for r in range(rows):
        y0, y1 = r * ph + gap / 2, (r + 1) * ph - gap / 2
        jx = (0.0 if r % 2 == 0 else 0.5) * S + rng.uniform(-70, 70)
        poly = wobble(rrect_pts(jx + gap / 2, y0, S - gap, y1 - y0, 12, 4), rng, 1.2, 48)
        col = jitter(pal[r % len(pal)], rng, 0.01, 0.06, 0.05)
        kn = []
        for _ in range(rng.choice([1, 1, 2])):
            kx = (jx + rng.uniform(140, S - 140)) % S
            kn.append((kx, rng.uniform(y0 + 50, y1 - 50), rng.uniform(13, 19)))
        boards.append((poly, col, y0, y1, jx, kn))
        knots_all += kn
        for side in (-1, 1):
            for fy in (0.27, 0.73):
                nails.append(((jx + side * 26) % S, y0 + (y1 - y0) * fy))
    full = mask_of(S, [b[0] for b in boards])
    bev = bevel(distance_field(full, S, S, 16), 12, "round")

    img = new_image(S)
    layer(img, "gaps", fill="#2c1b13", alpha=False)
    bl = layer(img, "boards")
    for poly, col, y0, y1, jx, kn in boards:
        fill_poly(bl, poly, col)
    streak = layer(img, "streak", alpha=False, mode=LM.SOFTLIGHT, opacity=55)
    noise(streak, 1, 10, detail=3, seed=1011)
    normalize(streak)
    gradient_map(streak, [(0, "#3a2a50"), (0.5, "#808080"), (1, "#ffe0a0")])
    set_mask(streak, full)
    gl = layer(img, "grain")
    glines = []
    for poly, col, y0, y1, jx, kn in boards:
        glines += wood_grain(gl, rng, S, y0 + 6, y1 - 6, col, 13, kn)
    set_mask(gl, full)
    kl = layer(img, "knots")
    items = []
    for poly, col, y0, y1, jx, kn in boards:
        for kx, ky, kr in kn:
            items += knot_items(kx, ky, kr, rng, col)
    fill_ordered(kl, items)
    gfield = strokes_field(S, glines, 2.4, 0.8)
    kfield = from_u8(mask_of(S, [ellipse_pts(kx, ky, kr * 1.2, kr * 0.6, 0, 24) for kx, ky, kr in knots_all]))
    nail_polys = [ellipse_pts(x, y, 6.5, 6.5, 0, 16) for x, y in nails]
    nfield = dome(mask_of(S, nail_polys), S, 5)
    h = array.array("f", [bev[i] * (0.92 - 0.06 * gfield[i] - 0.08 * kfield[i]) + 0.35 * nfield[i]
                          for i in range(S * S)])
    nl = layer(img, "nails")
    fill_polys(nl, nail_polys, "#3e3a40")
    fill_polys(nl, [ellipse_pts(x - 1.5, y - 1.8, 2.6, 2.2, 0, 10) for x, y in nails], "#a9a7b4")
    finish_lighting(img, T, h, 6.0, 1.0, 65, "#24140e", 55, 4, 3.5, "#ffe2b4", 55, 138, 4.0,
                    "#3a2440", 30)
    T.save_albedo(img)
    T.done()


def make_wood_dark():
    T = TexSet("wood_dark", seed=111)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 1, 8, detail=4, seed=1111)
    normalize(base)
    posterize(base, 6)
    blur(base, 2, 6)
    gradient_map(base, [(0, "#3a2416"), (0.35, "#4b2e1d"), (0.7, "#5b3925"), (1, "#6b452c")])
    knots = [(rng.uniform(0, S), rng.uniform(0, S), rng.uniform(16, 22)) for _ in range(3)]
    gl = layer(img, "grain")
    lines = wood_grain(gl, rng, S, 0, S, "#5a3824", 44, knots, dark=0.5, light=1.45,
                       size=(1.8, 3.4), amp=7.0, dark_op=95, light_op=60)
    kl = layer(img, "knots")
    items = []
    for kx, ky, kr in knots:
        items += knot_items(kx, ky, kr, rng, "#5a3824")
    fill_ordered(kl, items)
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=30)
    noise(hue, 2, 3, detail=2, seed=1112)
    normalize(hue)
    gradient_map(hue, [(0, "#3a3060"), (0.5, "#808080"), (1, "#f0b070")])
    g = strokes_field(S, lines, 2.4, 0.8)
    hn = field_noise(S, 1, 10, detail=3, seed=1113)
    kf = from_u8(mask_of(S, [ellipse_pts(kx, ky, kr * 1.2, kr * 0.6, 0, 24) for kx, ky, kr in knots]))
    h = array.array("f", [0.6 + 0.25 * hn[i] - 0.2 * g[i] - 0.15 * kf[i] for i in range(S * S)])
    finish_lighting(img, T, h, 4.0, 0.9, 50, "#1a0e0a", 35, 3, 3.0, "#d89a68", 30, 140, 4.0)
    T.save_albedo(img)
    T.done()


def make_bark():
    T = TexSet("bark", seed=121)
    S, rng = T.S, T.rng
    # long vertical furrows (periodic wavy lines) joined now and then by diagonal cracks,
    # which leaves long ridge plates between them, like oak bark
    n = 16
    xs = sorted((k + rng.uniform(-0.25, 0.25)) * S / n for k in range(n))
    furrows = [periodic_line(S, x, rng, 10.0, (1, 2, 3, 5), 12.0, vertical=True) for x in xs]

    def fx(k, y):
        pts = furrows[k % n]
        i = int((y % S) / S * (len(pts) - 1))
        return pts[i][0] + (S if k >= n else 0)

    links = []
    for k in range(n):
        for _ in range(rng.randint(2, 4)):
            y = rng.uniform(0, S)
            dy = rng.uniform(40, 110) * rng.choice([-1, 1])
            links.append([(fx(k, y), y), (fx(k + 1, y + dy), y + dy)])
    cimg = new_image(S)
    cl = layer(cimg, "c", fill="#000000", alpha=False)
    for pts in furrows:
        stroke(cl, pts, "#ffffff", rng.uniform(19, 26), "2. Hardness 075")
    for pts in links:
        stroke(cl, pts, "#ffffff", rng.uniform(11, 15), "2. Hardness 075")
    crev = read(cl, "Y' u8")
    cimg.delete()
    plates = crev.translate(INVERT)
    pd = distance_field(plates, S, S, 30)
    hb = bevel(pd, 22, "round")
    fib = []
    for k in range(40):
        fib.append(periodic_line(S, (k + rng.uniform(0, 1)) * S / 40, rng, 6.0, (1, 2, 3), 14.0, vertical=True))
    ff = strokes_field(S, fib, 2.0, 0.8)
    hn = field_noise(S, 8, 2, detail=4, seed=1211)
    h = array.array("f", [hb[i] * (0.88 + 0.12 * hn[i]) - 0.07 * ff[i] * hb[i] for i in range(S * S)])

    img = new_image(S)
    layer(img, "crevice", fill="#2a1c1a", alpha=False)
    pl = layer(img, "plates", alpha=False)
    noise(pl, 6, 1, detail=3, seed=1213)
    normalize(pl)
    posterize(pl, 5)
    blur(pl, 3, 10)
    gradient_map(pl, [(0, "#5d4a3b"), (0.35, "#6c5644"), (0.7, "#7a6450"), (1, "#8a735d")])
    set_mask(pl, plates)
    st = layer(img, "streaks", alpha=False, mode=LM.SOFTLIGHT, opacity=45)
    noise(st, 14, 1, detail=3, seed=1212)
    normalize(st)
    gradient_map(st, [(0, "#2e2238"), (0.5, "#808080"), (1, "#f0d0a0")])
    set_mask(st, plates)
    fl = layer(img, "fibres", opacity=40)
    for pts in fib:
        stroke(fl, pts, "#3a2a22", 1.8)
    set_mask(fl, plates)
    finish_lighting(img, T, h, 7.0, 1.0, 70, "#1a1014", 60, 5, 3.5, "#f0dcc0", 45, 138, 4.0,
                    "#2e2440", 35)
    T.save_albedo(img)
    T.done()


# ---------------------------------------------------------------------------
# foliage
# ---------------------------------------------------------------------------

def make_leaves():
    T = TexSet("leaves", seed=131)
    S, rng = T.S, T.rng
    ramp = ramp_luts([(0, "#1d4628"), (0.2, "#2a6332"), (0.4, "#3b8239"), (0.6, "#539d43"),
                      (0.8, "#78ba50"), (1, "#a6d66a")])

    def col(t):
        i = int(clamp(t) * 255)
        return quant((ramp[0][i] / 255, ramp[1][i] / 255, ramp[2][i] / 255), 6)

    img = new_image(S)
    layer(img, "deep", fill="#1b4026", alpha=False)
    hsum = array.array("f", [0.0]) * (S * S)
    for depth in range(3):
        centres = poisson(S, S, 92 - depth * 8, rng)
        backs, items = [], []
        for cx, cy in centres:
            R = rng.uniform(40, 56)
            backs.append((blob_pts(cx, cy + 4, R * 0.95, rng, 18, 0.25), col(0.08 + 0.12 * depth)))
            nl = rng.randint(13, 19)
            for k in range(nl):
                a = rng.uniform(0, 2 * math.pi)
                rr = R * math.sqrt(rng.uniform(0.05, 1.0)) * 0.85
                lx, ly = cx + math.cos(a) * rr, cy + math.sin(a) * rr
                up = (cy - ly) / R  # +1 at the top of the clump
                t = 0.18 + 0.2 * depth + 0.28 * up + rng.uniform(-0.08, 0.08)
                ang = a + rng.uniform(-0.5, 0.5)
                ln = rng.uniform(26, 38)
                items.append((leaf_pts(lx + math.cos(ang) * ln * 0.3, ly + math.sin(ang) * ln * 0.3,
                                       ln, ln * rng.uniform(0.42, 0.55), ang, 8, rng.uniform(-0.2, 0.2)),
                              col(t)))
            for k in range(rng.randint(2, 4)):
                lx = cx + rng.uniform(-R * 0.4, R * 0.4)
                ly = cy - R * rng.uniform(0.35, 0.7)
                ang = -math.pi / 2 + rng.uniform(-0.9, 0.9)
                ln = rng.uniform(20, 28)
                items.append((leaf_pts(lx, ly, ln, ln * 0.45, ang, 8), col(0.62 + 0.15 * depth)))
        drop_shadow(img, [b[0] for b in backs], 4, 7, "#0e2a1a", 45, 5.0, "clump_shadow%d" % depth)
        L = layer(img, "clumps%d" % depth)
        fill_many(L, backs)
        fill_many(L, items)
        m = from_u8(mask_of(S, [b[0] for b in backs]))
        for i in range(S * S):
            if m[i] > 0.0:
                hsum[i] = max(hsum[i], (0.3 + 0.3 * depth) * m[i])
    lum = from_u8(read(merge(img), "Y' u8"))
    h = array.array("f", [0.6 * hsum[i] + 0.4 * lum[i] for i in range(S * S)])
    h = field_blur(h, S, S, 1.2)
    finish_lighting(img, T, h, 5.0, 0.9, 45, "#0c2418", 40, 5, 3.0, "#e6ffb0", 30, 140, 4.0)
    T.save_albedo(img)
    T.done()


# ---------------------------------------------------------------------------
# stone
# ---------------------------------------------------------------------------

def make_stone_rough():
    T = TexSet("stone_rough", seed=141)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=1411)
    normalize(base)
    posterize(base, 6)
    blur(base, 5)
    gradient_map(base, [(0, "#6c6872"), (0.35, "#7f7b80"), (0.7, "#938e8b"), (1, "#a8a39b")])
    # painted planes: crisp facets of different values, like big flat brush strokes
    cells = [wobble(c, rng, 2.5, 20) for c in voronoi(poisson(S, S, 105, rng), S, S)]
    cl = layer(img, "planes", mode=LM.SOFTLIGHT, opacity=70)
    fill_many(cl, [(c, quant(jitter("#808080", rng, 0, 0, 0.26), 4)) for c in cells])
    blur(cl, 1.2)
    # chisel-like broad strokes in lighter / darker stone tones
    ch = layer(img, "strokes", opacity=22)
    for _ in range(140):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(30, 90)
        stroke(ch, polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 3, 4),
               rng.choice(["#c4beb4", "#5a5668", "#b0aaa0", "#4e4c5c"]), rng.uniform(10, 26), "Acrylic 02")
    hue = layer(img, "hue", alpha=False, mode=LM.SOFTLIGHT, opacity=35)
    noise(hue, 2, 2, detail=2, seed=1412)
    normalize(hue)
    gradient_map(hue, [(0, "#4a5490"), (0.5, "#808080"), (1, "#e8c08a")])
    cracks = []
    for _ in range(8):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        main = crack_path(x, y, rng.uniform(100, 180), rng.uniform(0, 6.28), rng, 10, 0.45)
        cracks.append(main)
        for _b in range(rng.randint(1, 2)):
            bx, by = main[rng.randrange(2, len(main) - 1)]
            cracks.append(crack_path(bx, by, rng.uniform(25, 60), rng.uniform(0, 6.28), rng, 7, 0.55))
    pits = []
    for x, y in poisson(S, S, 60, rng):
        if rng.random() < 0.18:
            pits.append(ellipse_pts(x, y, rng.uniform(2, 4), rng.uniform(1.6, 3.2), rng.uniform(0, 3), 10))
    # moss: tiny irregular specks gathered in a few soft patches
    mossmask = field_noise(S, 3, 3, detail=2, seed=1413)
    moss = []
    for x, y in poisson(S, S, 7, rng):
        v = mossmask[int(y) * S + int(x)]
        if rng.random() < smoothstep(0.66, 0.82, v) * 0.5:
            moss.append((wobble(blob_pts(x, y, rng.uniform(1.6, 3.6), rng, 8, 0.5), rng, 0.6, 3),
                         quant(rng.choice(["#4f7230", "#5e8236", "#6f9440", "#46682c"]), 8)))
    ck = strokes_field(S, cracks, 3.6, 1.0)
    pt = from_u8(mask_of(S, pits))
    mf = from_u8(mask_of(S, [m[0] for m in moss]))
    hn = field_noise(S, 6, 6, detail=4, seed=1414)
    hc = field_blur(from_u8(read(cl, "Y' u8")), S, S, 1.5)
    hs = field_blur(from_u8(read(ch, "Y' u8")), S, S, 2.0)
    h = array.array("f", [0.3 * hn[i] + 0.5 * hc[i] + 0.12 * hs[i] - 0.3 * ck[i] - 0.15 * pt[i] + 0.1 * mf[i]
                          for i in range(S * S)])
    pl = layer(img, "pits", opacity=80)
    fill_polys(pl, pits, "#4a4656")
    finish_lighting(img, T, h, 9.0, 1.0, 70, "#24223a", 55, 4, 3.5, "#f6f0e6", 45, 140, 4.0,
                    "#33355a", 35)
    cr = layer(img, "cracks")
    for pth in cracks:
        stroke(cr, pth, "#34324a", 3.4)
    lip = layer(img, "crack_lip", opacity=50)
    for pth in cracks:
        stroke(lip, [(x + 2.2, y + 2.2) for x, y in pth], "#dcd6cc", 1.5)
    drop_shadow(img, [m[0] for m in moss], 1.2, 1.6, "#20283a", 40, 1.0, "moss_shadow")
    ml = layer(img, "moss")
    fill_many(ml, moss)
    T.save_albedo(img)
    T.done()


def make_plaster():
    T = TexSet("plaster", seed=151)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=1511)
    normalize(base)
    posterize(base, 5)
    blur(base, 16)
    gradient_map(base, [(0, "#dccaa8"), (0.35, "#e5d4b4"), (0.7, "#eee2c8"), (1, "#f5ecd8")])
    pl = layer(img, "patches", opacity=30)
    patches = []
    for _ in range(9):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        patches.append((blob_pts(x, y, rng.uniform(55, 120), rng, 22, 0.35, rng.uniform(0, 3), 1.3),
                        quant(rng.choice(["#dcc49c", "#e3cfaa", "#f6eedc", "#d8c2a2"]), 6)))
    fill_many(pl, patches)
    blur(pl, 12)
    tr = layer(img, "trowel", opacity=22)
    strokes = []
    for _ in range(46):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(90, 220)
        pts = polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 8, 6)
        strokes.append(pts)
        stroke(tr, pts, rng.choice(["#fffaf0", "#c8b088", "#fff4e0"]), rng.uniform(26, 48), "Acrylic 03")
    cracks = []
    for _ in range(5):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        cracks.append(crack_path(x, y, rng.uniform(40, 90), rng.uniform(0, 6.28), rng, 8, 0.6))
    hn = field_noise(S, 8, 8, detail=4, seed=1512)
    ck = strokes_field(S, cracks, 2.0, 0.6)
    tf = field_blur(from_u8(read(tr, "Y' u8")), S, S, 3)
    h = array.array("f", [0.6 * hn[i] + 0.3 * tf[i] - 0.25 * ck[i] for i in range(S * S)])
    finish_lighting(img, T, h, 2.5, 0.8, 40, "#8a7060", 30, 3, 3.0, None)
    cl = layer(img, "cracks", opacity=75)
    for pth in cracks:
        stroke(cl, pth, "#a8906e", 1.8)
    T.save_albedo(img)
    T.done()


def make_roof_tiles():
    T = TexSet("roof_tiles", seed=161)
    S, rng = T.S, T.rng
    rows, cols = 8, 6
    rh, cw = S / rows, S / cols
    pal = ["#c4603a", "#b9583a", "#cf6e44", "#ad5136", "#c86a3c", "#b8643f"]

    def tile(cx, y0, w):
        # exposed area y0..y0+rh with a round (scalloped) lower edge; hidden part reaches up
        top = y0 - rh * 0.6
        r = w / 2 - 3
        pts = [(cx - w / 2 + 3, top), (cx + w / 2 - 3, top), (cx + w / 2 - 3, y0 + rh - r)]
        for k in range(1, 16):
            a = math.pi * k / 16
            pts.append((cx + r * math.cos(a), y0 + rh - r + r * 1.0 * math.sin(a) + 4))
        pts.append((cx - w / 2 + 3, y0 + rh - r))
        return pts

    order = list(range(rows - 1, -1, -1))  # bottom rows first: upper rows lie on top
    tiles = []
    for r in order:
        off = (cw / 2) if r % 2 else 0.0
        for c in range(cols):
            tiles.append((r, tile(c * cw + off + cw / 2, r * rh, cw),
                          jitter(rng.choice(pal), rng, 0.012, 0.08, 0.07), 0))
    # rows form a cycle (row 7's scallops lie on row 0 of the next tile): after drawing
    # rows 7..0, draw row 7 once more shifted up by one tile so its scallops cover row 0.
    tiles = ([(r, poly, col, S) for r, poly, col, dy in tiles if r == 0] + tiles +
             [(r, poly, col, -S) for r, poly, col, dy in tiles if r == rows - 1])

    img = new_image(S)
    layer(img, "under", fill="#4a2018", alpha=False)
    tl = layer(img, "tiles")
    himg = new_image(S)
    hl = layer(himg, "h", fill="#000000", alpha=False)

    def grad_fill(L, poly, y_a, y_b, c0, c1):
        im = L.get_image()
        x0, y0, x1, y1 = bbox(poly)
        Gimp.context_set_foreground(gcol(c0))
        Gimp.context_set_background(gcol(c1))
        Gimp.context_set_gradient_fg_bg_rgb()
        for dx in (-S, 0, S):  # wrap in x only
            if x1 + dx < 0 or x0 + dx > S:
                continue
            im.select_polygon(REPLACE, [float(c) for x, y in poly for c in (x + dx, y)])
            L.edit_gradient_fill(Gimp.GradientType.LINEAR, 0.0, False, 1, 0.0, False, 0, y_a, 0, y_b)
        sel_none(im)

    for r, poly, col, dy in tiles:
        poly = [(x, y + dy) for x, y in poly]
        x0, y0, x1, y1 = bbox(poly)
        ya = r * rh + dy + rh * 0.05
        grad_fill(tl, poly, ya, y1, mul(col, 0.6), col)
        grad_fill(hl, poly, ya, y1, (0.12,) * 3, (0.95,) * 3)
    h = field_blur(read_f(hl), S, S, 1.6)
    himg.delete()
    hn = field_noise(S, 8, 8, detail=3, seed=1611)
    h = array.array("f", [h[i] * (0.94 + 0.06 * hn[i]) for i in range(S * S)])
    fv = layer(img, "facevar", alpha=False, mode=LM.SOFTLIGHT, opacity=40)
    noise(fv, 6, 6, detail=3, seed=1612)
    normalize(fv)
    gradient_map(fv, [(0, "#5a3a60"), (0.5, "#808080"), (1, "#ffd890")])
    finish_lighting(img, T, h, 7.0, 1.0, 60, "#3a1418", 60, 5, 3.5, "#ffd8b0", 50, 138, 4.0,
                    "#4a2038", 30)
    T.save_albedo(img)
    T.done()


# ---------------------------------------------------------------------------
# rune stone (+ emission)
# ---------------------------------------------------------------------------

def rune_glyph(cx, cy, size, rng):
    """A random angular rune made of strokes between nodes of a 3x4 grid."""
    gx = [cx - size * 0.32, cx, cx + size * 0.32]
    gy = [cy - size * 0.5, cy - size * 0.17, cy + size * 0.17, cy + size * 0.5]
    strokes = []
    stem = rng.choice([0, 1, 1, 2])
    strokes.append([(gx[stem], gy[0]), (gx[stem], gy[3])])
    nodes = [(i, j) for i in range(3) for j in range(4)]
    for _ in range(rng.randint(2, 3)):
        j0 = rng.randrange(4)
        a = (stem, j0)
        b = rng.choice([n for n in nodes if n[0] != stem and abs(n[1] - j0) <= 2])
        strokes.append([(gx[a[0]], gy[a[1]]), (gx[b[0]], gy[b[1]])])
    if rng.random() < 0.5:
        j = rng.randrange(1, 3)
        side = 2 if stem < 2 else 0
        strokes.append([(gx[stem], gy[j]), (gx[side], gy[j] - size * 0.15), (gx[side], gy[j] + size * 0.2)])
    dots = []
    if rng.random() < 0.6:
        side = 0 if stem > 0 else 2
        dots.append((gx[side], gy[rng.randrange(4)]))
    return strokes, dots


def make_rune_stone():
    T = TexSet("rune_stone", seed=171)
    S, rng = T.S, T.rng
    rows = 2
    rh = S / rows
    gap = 14.0
    blocks, glyphs = [], []
    for r in range(rows):
        off = 0.0 if r == 0 else S / 4
        for c in range(2):
            x0 = off + c * S / 2 + gap / 2
            y0 = r * rh + gap / 2
            w, hgt = S / 2 - gap, rh - gap
            poly = wobble(rrect_pts(x0, y0, w, hgt, 26, 6), rng, 2.0, 30)
            blocks.append((poly, quant(jitter(rng.choice(["#5d6380", "#646a86", "#585d7a", "#6a6c88"]),
                                              rng, 0.01, 0.08, 0.06), 6)))
            st, dots = rune_glyph(x0 + w / 2, y0 + hgt / 2, hgt * 0.56, rng)
            frame = rrect_pts(x0 + 40, y0 + 40, w - 80, hgt - 80, 30, 6)
            glyphs.append((st, dots, frame + [frame[0]]))
    full = mask_of(S, [b[0] for b in blocks])
    bev = bevel(distance_field(full, S, S, 30), 24, "round")
    # glyph grooves: paint strokes into a groove mask (wide) and a glow core mask (narrow)
    gimg = new_image(S)
    groove = layer(gimg, "groove", fill="#000000", alpha=False)
    core = layer(gimg, "core", fill="#000000", alpha=False)
    framel = layer(gimg, "frame", fill="#000000", alpha=False)
    for st, dots, frame in glyphs:
        for pts in st:
            stroke(groove, pts, "#ffffff", 38, "2. Hardness 100")
            stroke(core, pts, "#ffffff", 17, "2. Hardness 075")
        for d in dots:
            stroke(groove, [d], "#ffffff", 42, "2. Hardness 100")
            stroke(core, [d], "#ffffff", 20, "2. Hardness 075")
        stroke(framel, frame, "#ffffff", 9, "2. Hardness 100")
    gm = read(groove, "Y' u8")
    cm = read(core, "Y' u8")
    fm = read(framel, "Y' u8")
    gimg.delete()
    gdist = bevel(distance_field(gm, S, S, 16), 12, "round")
    fdist = bevel(distance_field(fm, S, S, 6), 4, "linear")
    hn = field_noise(S, 6, 6, detail=4, seed=1711)
    h = array.array("f", [bev[i] * (0.9 + 0.08 * hn[i]) - 0.55 * gdist[i] * bev[i] - 0.18 * fdist[i]
                          for i in range(S * S)])

    img = new_image(S)
    layer(img, "gap", fill="#26243a", alpha=False)
    bl = layer(img, "blocks")
    fill_many(bl, blocks)
    fv = layer(img, "facevar", alpha=False, mode=LM.SOFTLIGHT, opacity=50)
    noise(fv, 5, 5, detail=3, seed=1712)
    normalize(fv)
    gradient_map(fv, [(0, "#3c3470"), (0.5, "#808080"), (1, "#d8d0f0")])
    set_mask(fv, full)
    gl = tint_layer(img, "#2a2048", gm, 100, LM.NORMAL, "groove")
    fr = tint_layer(img, "#3a3858", fm, 70, LM.NORMAL, "frame")
    nb = finish_lighting(img, T, h, 7.0, 1.0, 65, "#1a1630", 60, 5, 3.5, "#e8e4ff", 45, 138, 4.0,
                         "#2a2650", 30)
    glow = tint_layer(img, "#9a6cff", cm, 100, LM.NORMAL, "glow")
    soft = field_blur(from_u8(cm), S, S, 5)
    tint_layer(img, "#7a4ce0", to_u8(soft), 55, LM.SCREEN, "glow_soft")
    hot = bytes(cm).translate(lut_bytes(lambda v: smoothstep(0.6, 1.0, v)))
    tint_layer(img, "#e6d8ff", field_blur_u8(hot, S, 1.5), 70, LM.NORMAL, "glow_hot")
    T.save_albedo(img)
    em = field_blur(from_u8(cm), S, S, 1.5)
    T.save_grey("emission", em)
    T.done()


def field_blur_u8(data, S, r):
    return to_u8(field_blur(from_u8(data), S, S, r))


SETS = {
    "stone_bricks": make_stone_bricks,
    "cobble": make_cobble,
    "wood_planks": make_wood_planks,
    "wood_dark": make_wood_dark,
    "bark": make_bark,
    "leaves": make_leaves,
    "stone_rough": make_stone_rough,
    "plaster": make_plaster,
    "roof_tiles": make_roof_tiles,
    "rune_stone": make_rune_stone,
}
