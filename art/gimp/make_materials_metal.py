"""Metal material sets (1 UV unit = 2 m on models): brass, copper, steel, painted_metal,
dark_metal, rust, metal_corrugated.  All of them also get a greyscale roughness map."""
import math
import array

from rwtex import *  # noqa: F401,F403


def brushed_field(S, seed, xs=1, ys=16, streak=90):
    """Horizontal brushed-metal streaks (0..1), wrap-safe."""
    img, L = scratch(S)
    noise(L, xs, ys, detail=4, seed=seed)
    normalize(L)
    motion_blur(L, streak, 0)
    normalize(L)
    a = read_f(L)
    img.delete()
    return a


def blotch_mask(S, seed, lo, hi, xs=4, ys=4, detail=4, soft=0.0):
    a = field_noise(S, xs, ys, detail=detail, seed=seed)
    m = array.array("f", [smoothstep(lo, hi, v) for v in a])
    if soft:
        m = field_blur(m, S, S, soft)
    return m


def scratches(rng, S, n, lmin=20, lmax=90):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, math.pi) if rng.random() < 0.4 else rng.uniform(-0.35, 0.35)
        ln = rng.uniform(lmin, lmax)
        out.append(polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 1.5, 5))
    return out


def paint_scratches(img, lines, light, dark, size=1.3, op=70):
    dl = layer(img, "scratch_dark", opacity=op * 0.8)
    for p in lines:
        stroke(dl, [(x + 1.1, y + 1.1) for x, y in p], dark, size, "2. Hardness 075")
    ll = layer(img, "scratch_light", opacity=op)
    for p in lines:
        stroke(ll, p, light, size, "2. Hardness 075")


def metal_base(img, S, seed, stops, brushed, brushed_op=22, post=5, soft=22, xs=2, ys=3):
    base = layer(img, "base", alpha=False)
    noise(base, xs, ys, detail=3, seed=seed)
    normalize(base)
    posterize(base, post)
    blur(base, soft)
    gradient_map(base, stops)
    grey_layer(img, to_u8(brushed), "brushed", mode=LM.OVERLAY, opacity=brushed_op)
    return base


def reflections(img, rng, S, color, n=6, op=30):
    """A few long, soft horizontal highlight streaks (painted reflections)."""
    L = layer(img, "reflect", opacity=op)
    for _ in range(n):
        y = rng.uniform(0, S)
        stroke(L, periodic_line(S, y, rng, 6.0, (1, 2), 16.0), color, rng.uniform(8, 22), "2. Hardness 025")
    blur(L, 5)
    return L


def make_brass():
    T = TexSet("brass", seed=201)
    S, rng = T.S, T.rng
    img = new_image(S)
    br = brushed_field(S, 2011)
    metal_base(img, S, 2012, [(0, "#a87e36"), (0.4, "#c09440"), (0.75, "#d4a94e"), (1, "#e8c66c")], br)
    reflections(img, rng, S, "#fff2c0")
    grime = blotch_mask(S, 2013, 0.66, 0.84, 5, 5, 4, 3.0)
    tint_layer(img, "#6a5428", to_u8(grime), 40, LM.MULTIPLY, "grime")
    specks = []
    for x, y in poisson(S, S, 12, rng):
        if rng.random() < 0.3 * grime[int(y) * S + int(x)]:
            specks.append(blob_pts(x, y, rng.uniform(1.5, 3.5), rng, 8, 0.4))
    sl = layer(img, "grime_specks", opacity=45)
    fill_polys(sl, specks, "#3e3014")
    lines = scratches(rng, S, 26)
    paint_scratches(img, lines, "#ffeeb8", "#6a5020")
    sc = strokes_field(S, lines, 1.6, 0.6)
    h = array.array("f", [0.5 + 0.12 * br[i] + 0.06 * grime[i] - 0.15 * sc[i] for i in range(S * S)])
    finish_lighting(img, T, h, 3.0, 0.8, 35, None, 0, hi_col="#fff4c8", hi_op=25, hi_lo=140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.3 + 0.08 * br[i] + 0.38 * grime[i] - 0.06 * sc[i])
                                               for i in range(S * S)]))
    T.done()


def make_copper():
    T = TexSet("copper", seed=211)
    S, rng = T.S, T.rng
    img = new_image(S)
    br = brushed_field(S, 2111)
    metal_base(img, S, 2112, [(0, "#a4553a"), (0.4, "#c46a42"), (0.75, "#d8824e"), (1, "#eca070")], br)
    reflections(img, rng, S, "#ffd0a8")
    # patina: big blotches plus clusters of small spots
    pm = blotch_mask(S, 2113, 0.6, 0.7, 4, 4, 4)
    spots = []
    dens = field_noise(S, 5, 5, detail=2, seed=2114)
    for x, y in poisson(S, S, 16, rng):
        if rng.random() < smoothstep(0.6, 0.85, dens[int(y) * S + int(x)]) * 0.35:
            spots.append(blob_pts(x, y, rng.uniform(3, 7), rng, 12, 0.45))
    sm = from_u8(mask_of(S, spots))
    pat = array.array("f", [max(pm[i], sm[i]) for i in range(S * S)])
    pat = field_blur(pat, S, S, 1.0)
    pmb = field_blur(pm, S, S, 1.0)
    halo = field_blur(pmb, S, S, 6.0)
    ring = array.array("f", [clamp((halo[i] - pmb[i]) * 2.5) for i in range(S * S)])
    tint_layer(img, "#6a3020", to_u8(ring), 35, LM.MULTIPLY, "oxide")
    pl = layer(img, "patina", alpha=False)
    noise(pl, 8, 8, detail=3, seed=2115)
    normalize(pl)
    posterize(pl, 4)
    blur(pl, 1.5)
    gradient_map(pl, [(0, "#3f9682"), (0.4, "#52ad94"), (0.75, "#6cc2a8"), (1, "#94dcc4")])
    set_mask(pl, to_u8(pat))
    pn = field_noise(S, 10, 10, detail=3, seed=2116)
    h = array.array("f", [0.45 + 0.1 * br[i] + pat[i] * (0.25 + 0.15 * pn[i]) for i in range(S * S)])
    finish_lighting(img, T, h, 4.0, 0.9, 45, "#2a1a20", 35, 3, 3.0, "#ffe0c0", 30, 140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.32 + 0.08 * br[i] + 0.55 * pat[i] + 0.15 * ring[i])
                                               for i in range(S * S)]))
    T.done()


def make_steel():
    T = TexSet("steel", seed=221)
    S, rng = T.S, T.rng
    img = new_image(S)
    br = brushed_field(S, 2211, streak=120)
    metal_base(img, S, 2212, [(0, "#8b929c"), (0.4, "#a2a9b2"), (0.75, "#b7bdc5"), (1, "#cdd2d9")], br, 32)
    reflections(img, rng, S, "#f4f8ff", 8, 25)
    smudge = blotch_mask(S, 2213, 0.6, 0.85, 3, 3, 3, 8.0)
    tint_layer(img, "#6a7080", to_u8(smudge), 18, LM.MULTIPLY, "smudge")
    lines = scratches(rng, S, 70, 15, 80)
    paint_scratches(img, lines, "#f6f9fc", "#5c626c", 1.5, 85)
    sc = strokes_field(S, lines, 1.6, 0.6)
    h = array.array("f", [0.5 + 0.14 * br[i] - 0.18 * sc[i] for i in range(S * S)])
    finish_lighting(img, T, h, 3.0, 0.8, 35, None, 0, hi_col="#ffffff", hi_op=25, hi_lo=140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.26 + 0.1 * br[i] + 0.25 * smudge[i] - 0.08 * sc[i])
                                               for i in range(S * S)]))
    T.done()


def make_painted_metal():
    """Tintable: light neutral paint (value ~0.85) with chips showing dark metal."""
    T = TexSet("painted_metal", seed=231)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "paint", alpha=False)
    noise(base, 3, 3, detail=3, seed=2311)
    normalize(base)
    posterize(base, 5)
    blur(base, 12)
    gradient_map(base, [(0, "#d0d0d0"), (0.5, "#d9d9d9"), (1, "#e2e2e2")])
    strokes = layer(img, "brush", opacity=18)
    for _ in range(60):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(-0.25, 0.25)
        ln = rng.uniform(120, 300)
        stroke(strokes, polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 5, 6),
               rng.choice(["#f0f0f0", "#c4c4c4"]), rng.uniform(30, 60), "Acrylic 01")
    # chips cluster where a noise field is high
    dens = field_noise(S, 4, 4, detail=3, seed=2312)
    chips = []
    for x, y in poisson(S, S, 22, rng):
        p = smoothstep(0.52, 0.8, dens[int(y) * S + int(x)])
        if rng.random() < p * 0.55:
            r = rng.uniform(4, 10) if rng.random() < 0.7 else rng.uniform(10, 20)
            chips.append(wobble(blob_pts(x, y, r, rng, 16, 0.6, rng.uniform(0, 3), rng.uniform(0.4, 0.9)),
                                rng, r * 0.18, 4))
    rim = [scale_poly(c, 1.0 + 7.0 / max(6.0, poly_area(c) ** 0.5)) for c in chips]
    rl = layer(img, "chip_rim")
    fill_polys(rl, rim, "#f4f4f4")
    cl = layer(img, "chips")
    fill_many(cl, [(c, quant(jitter("#4a4e58", rng, 0.01, 0.1, 0.12), 6)) for c in chips])
    scr = scratches(rng, S, 18, 25, 70)
    scl = layer(img, "scrapes", opacity=70)
    for pth in scr:
        stroke(scl, pth, "#5a5e68", 1.6, "2. Hardness 075")
    cm = from_u8(mask_of(S, chips))
    hn = field_noise(S, 8, 8, detail=3, seed=2313)
    sf = field_blur(from_u8(read(strokes, "Y' u8")), S, S, 2)
    h = array.array("f", [0.75 - 0.45 * cm[i] + 0.03 * hn[i] + 0.04 * sf[i] for i in range(S * S)])
    h = field_blur(h, S, S, 0.8)
    finish_lighting(img, T, h, 5.0, 0.9, 40, "#3a3a46", 35, 3, 3.0, "#ffffff", 30, 140)
    alb = T.save_albedo(img)
    mean = sum(alb[0::3]) / (S * S) / 255.0
    log("  painted_metal mean albedo value %.3f" % mean)
    T.save_grey("roughness", array.array("f", [clamp(0.5 + 0.05 * hn[i] - 0.15 * cm[i]) for i in range(S * S)]))
    T.done()


def make_dark_metal():
    T = TexSet("dark_metal", seed=241)
    S, rng = T.S, T.rng
    img = new_image(S)
    br = brushed_field(S, 2411)
    metal_base(img, S, 2412, [(0, "#343943"), (0.4, "#3e4450"), (0.75, "#49505c"), (1, "#555c69")], br, 28)
    reflections(img, rng, S, "#8a94a8", 6, 25)
    worn = blotch_mask(S, 2413, 0.66, 0.86, 5, 5, 4, 3.0)
    tint_layer(img, "#7a8496", to_u8(worn), 28, LM.NORMAL, "worn")
    lines = scratches(rng, S, 40, 15, 70)
    paint_scratches(img, lines, "#9aa4b4", "#22262e", 1.3, 70)
    sc = strokes_field(S, lines, 1.6, 0.6)
    h = array.array("f", [0.5 + 0.1 * br[i] - 0.06 * worn[i] - 0.16 * sc[i] for i in range(S * S)])
    finish_lighting(img, T, h, 3.0, 0.8, 35, None, 0, hi_col="#b8c4dc", hi_op=25, hi_lo=140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.42 + 0.06 * br[i] - 0.14 * worn[i] - 0.06 * sc[i])
                                               for i in range(S * S)]))
    T.done()


def make_rust():
    T = TexSet("rust", seed=251)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 4, 4, detail=4, seed=2511)
    normalize(base)
    posterize(base, 6)
    blur(base, 3)
    hb = read_f(base)
    gradient_map(base, [(0, "#4a2214"), (0.25, "#6a3418"), (0.5, "#8a4a20"), (0.75, "#a85e28"), (1, "#c27a36")])
    dk = layer(img, "dark", alpha=False, mode=LM.MULTIPLY, opacity=45)
    noise(dk, 3, 3, detail=3, seed=2512)
    normalize(dk)
    gradient_map(dk, [(0, "#5a3040"), (0.5, "#c8a090"), (1, "#ffffff")])
    flakes = []
    for x, y in poisson(S, S, 20, rng):
        if rng.random() < 0.2:
            flakes.append((wobble(blob_pts(x, y, rng.uniform(3, 9), rng, 10, 0.5), rng, 1.0, 4),
                           quant(rng.choice(["#cf8a42", "#b86e32", "#d89a52", "#9a5226"]), 8)))
    fl = layer(img, "flakes", opacity=75)
    fill_many(fl, flakes)
    pits = []
    for x, y in poisson(S, S, 17, rng):
        if rng.random() < 0.22:
            pits.append(ellipse_pts(x, y, rng.uniform(2, 5), rng.uniform(1.8, 4.2), rng.uniform(0, 3), 10))
    pl = layer(img, "pit_rim", opacity=70)
    fill_polys(pl, [[(x + 1.2, y + 1.2) for x, y in p] for p in pits], "#e0a060")
    pd = layer(img, "pits")
    fill_polys(pd, pits, "#2c140c")
    pm = from_u8(mask_of(S, pits))
    fm = from_u8(mask_of(S, [f[0] for f in flakes]))
    hn = field_noise(S, 10, 10, detail=4, seed=2513)
    h = array.array("f", [0.45 + 0.25 * hb[i] + 0.12 * hn[i] + 0.1 * fm[i] - 0.35 * pm[i] for i in range(S * S)])
    h = field_blur(h, S, S, 0.8)
    finish_lighting(img, T, h, 5.0, 0.9, 50, "#2a1010", 45, 3, 3.0, "#ffc890", 25, 142)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.84 + 0.1 * hn[i] - 0.05 * fm[i]) for i in range(S * S)]))
    T.done()


def make_metal_corrugated():
    T = TexSet("metal_corrugated", seed=261)
    S, rng = T.S, T.rng
    pitch = S / 16.0
    seam_y = 104.0
    # corrugation: vertical ridges (cosine profile); a panel overlap seam with rivets
    row = array.array("f", [0.5 + 0.5 * math.cos(2 * math.pi * x / pitch) for x in range(S)])
    h = array.array("f", row.tolist() * S)
    for y in range(S):
        d = (y - seam_y) % S
        if d < 14:  # the upper panel's edge laps over the lower panel
            lift = 0.25 * (1 - d / 14.0)
            for x in range(S):
                h[y * S + x] += lift
    rivets = [((k + 0.5) * pitch * 2, seam_y - 6) for k in range(8)]
    rv = dome(mask_of(S, [ellipse_pts(x, y, 7, 7, 0, 16) for x, y in rivets]), S, 6)
    h = array.array("f", [h[i] * 0.85 + 0.45 * rv[i] for i in range(S * S)])

    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 2, detail=3, seed=2611)
    normalize(base)
    posterize(base, 5)
    blur(base, 10)
    gradient_map(base, [(0, "#858c96"), (0.5, "#9aa1aa"), (1, "#b2b8c0")])
    # rust streaks run down from the seam and rivets, plus faint long streaks everywhere
    streaks = []
    for x, y in rivets:
        streaks.append(blade_pts(x + rng.uniform(-2, 2), y + 4, rng.uniform(160, 420), rng.uniform(14, 24),
                                 math.pi / 2 + rng.uniform(-0.03, 0.03), rng.uniform(-0.02, 0.02)))
    for _ in range(10):
        x = rng.uniform(0, S)
        streaks.append(blade_pts(x, seam_y + 12, rng.uniform(100, 300), rng.uniform(10, 18),
                                 math.pi / 2 + rng.uniform(-0.03, 0.03), 0.0))
    sm = field_blur(from_u8(mask_of(S, streaks)), S, S, 4.0, 6.0)
    long = field_noise(S, 16, 1, detail=3, seed=2612)
    lm = array.array("f", [smoothstep(0.6, 0.85, v) * 0.55 for v in long])
    valley = row.tolist() * S
    rust = array.array("f", [clamp((sm[i] * 1.1 + lm[i] * 1.2) * (1.15 - 0.6 * valley[i])) for i in range(S * S)])
    rl = layer(img, "rust", alpha=False)
    noise(rl, 6, 2, detail=3, seed=2613)
    normalize(rl)
    gradient_map(rl, [(0, "#6a3418"), (0.5, "#8e4a22"), (1, "#b06a30")])
    set_mask(rl, to_u8(rust))
    rl.set_opacity(80.0)
    sl = layer(img, "seam_line")
    stroke(sl, [(0, seam_y + 13), (S, seam_y + 13)], "#3a3e48", 3.0)
    rvl = layer(img, "rivets")
    fill_polys(rvl, [ellipse_pts(x, y, 7, 7, 0, 16) for x, y in rivets], "#8a909a")
    finish_lighting(img, T, h, 10.0, 1.1, 85, "#2a2c3a", 45, 6, 2.5, "#f4f8ff", 45, 138, 4.0, "#363a56", 35)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.42 + 0.45 * rust[i]) for i in range(S * S)]))
    T.done()


SETS = {
    "brass": make_brass,
    "copper": make_copper,
    "steel": make_steel,
    "painted_metal": make_painted_metal,
    "dark_metal": make_dark_metal,
    "rust": make_rust,
    "metal_corrugated": make_metal_corrugated,
}
