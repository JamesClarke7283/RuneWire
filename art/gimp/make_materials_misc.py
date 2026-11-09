"""Misc material sets: rubber, leather, fabric (tintable), skin, crystal."""
import math
import array

from rwtex import *  # noqa: F401,F403


def make_rubber():
    T = TexSet("rubber", seed=301)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=3011)
    normalize(base)
    posterize(base, 5)
    blur(base, 14)
    gradient_map(base, [(0, "#25252b"), (0.4, "#2c2c33"), (0.75, "#33333b"), (1, "#3b3b44")])
    fine = field_noise(S, 16, 16, detail=2, seed=3012)
    grey_layer(img, to_u8(fine), "fine", mode=LM.OVERLAY, opacity=10)
    sc = layer(img, "scuffs", opacity=16)
    for _ in range(26):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(-0.6, 0.6)
        ln = rng.uniform(40, 140)
        stroke(sc, polyline_wavy(x, y, x + math.cos(a) * ln, y + math.sin(a) * ln, rng, 4, 6),
               "#6a6a78", rng.uniform(5, 14), "Acrylic 02")
    hn = field_noise(S, 8, 8, detail=3, seed=3013)
    h = array.array("f", [0.5 + 0.2 * hn[i] + 0.08 * fine[i] for i in range(S * S)])
    finish_lighting(img, T, h, 2.0, 0.7, 30, None, 0, hi_col="#5a5a6a", hi_op=25, hi_lo=140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.8 + 0.08 * hn[i]) for i in range(S * S)]))
    T.done()


def make_leather():
    T = TexSet("leather", seed=311)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=3111)
    normalize(base)
    posterize(base, 6)
    blur(base, 10)
    gradient_map(base, [(0, "#5c361f"), (0.35, "#6c4227"), (0.7, "#7c4e30"), (1, "#8e5c3a")])
    worn = field_noise(S, 4, 4, detail=3, seed=3112)
    wm = array.array("f", [smoothstep(0.6, 0.85, v) for v in worn])
    tint_layer(img, "#a87450", to_u8(field_blur(wm, S, S, 14)), 18, LM.SCREEN, "rubbed")
    # pebbled grain: creases from turbulent noise
    gimg, gl = scratch(S)
    noise(gl, 16, 16, detail=2, seed=3113, turbulent=True)
    normalize(gl)
    tb = read_f(gl)
    gimg.delete()
    crease = array.array("f", [1.0 - smoothstep(0.0, 0.16, v) for v in tb])
    crease = field_blur(crease, S, S, 0.8)
    tint_layer(img, "#3a2010", to_u8(crease), 22, LM.MULTIPLY, "creases")
    # stitched seams along U
    seams = [S * 0.25, S * 0.75]
    grooves, stitches, holes = [], [], []
    for sy in seams:
        grooves.append([(x, sy) for x in range(0, S + 1, 32)])
        y = sy + 14
        n = 44
        for k in range(n):
            cx = (k + 0.5) * S / n
            a = -0.28
            ca, sa = math.cos(a), math.sin(a)
            cap = rrect_pts(-7.0, -2.4, 14.0, 4.8, 2.4, 3)
            stitches.append([(cx + px * ca - py * sa, y + px * sa + py * ca) for px, py in cap])
            holes.append(ellipse_pts(cx - 8.2 * ca, y - 8.2 * sa, 2.4, 2.4, 0, 8))
            holes.append(ellipse_pts(cx + 8.2 * ca, y + 8.2 * sa, 2.4, 2.4, 0, 8))
    gr = layer(img, "groove", opacity=80)
    for g in grooves:
        stroke(gr, g, "#3a2214", 5.0)
    hl = layer(img, "groove_hi", opacity=45)
    for g in grooves:
        stroke(hl, [(x, y + 4) for x, y in g], "#b88a60", 2.0)
    hol = layer(img, "holes")
    fill_polys(hol, holes, "#2a160c")
    st = layer(img, "stitches")
    fill_polys(st, stitches, "#dcbc8c")
    sm = from_u8(mask_of(S, stitches))
    gm = strokes_field(S, grooves, 5.0, 1.0)
    hn = field_noise(S, 6, 6, detail=3, seed=3114)
    h = array.array("f", [0.55 + 0.12 * hn[i] - 0.12 * crease[i] - 0.3 * gm[i] + 0.25 * sm[i]
                          for i in range(S * S)])
    finish_lighting(img, T, h, 4.0, 0.9, 45, "#24120a", 40, 3, 3.0, "#f0c8a0", 30, 140)
    T.save_albedo(img)
    T.save_grey("roughness", array.array("f", [clamp(0.58 + 0.08 * hn[i] - 0.14 * wm[i] + 0.1 * crease[i])
                                               for i in range(S * S)]))
    T.done()


def make_fabric():
    """Tintable: light neutral plain weave (value ~0.85)."""
    T = TexSet("fabric", seed=321)
    S, rng = T.S, T.rng
    pitch = 16.0
    slub_x = field_noise(S, 1, 16, detail=2, seed=3211)  # weft threads vary along rows
    slub_y = field_noise(S, 16, 1, detail=2, seed=3212)  # warp threads vary along columns
    h = array.array("f", [0.0]) * (S * S)
    tone = array.array("f", [0.0]) * (S * S)
    sw = [math.sin(math.pi * clamp((i / pitch - 0.08) / 0.84)) ** 0.7 for i in range(int(pitch))]
    for y in range(S):
        cy = int(y // pitch)
        fy = sw[int(y % pitch)]
        row = y * S
        for x in range(S):
            cx = int(x // pitch)
            fx = sw[int(x % pitch)]
            i = row + x
            if (cx + cy) & 1:  # weft (horizontal thread) on top
                v = 0.55 + 0.45 * fy * (0.75 + 0.25 * fx)
                t = slub_x[i]
            else:  # warp on top
                v = 0.55 + 0.45 * fx * (0.75 + 0.25 * fy)
                t = slub_y[i]
            if fx < 0.25 and fy < 0.25:
                v *= 0.6
            h[i] = v
            tone[i] = t
    img = new_image(S)
    base = layer(img, "base", fill="#c2c2c2", alpha=False)
    big = layer(img, "big", alpha=False, mode=LM.SOFTLIGHT, opacity=18)
    noise(big, 3, 3, detail=2, seed=3213)
    normalize(big)
    grey_layer(img, to_u8(tone, -0.2, 1.2), "slub", mode=LM.SOFTLIGHT, opacity=30)
    grey_layer(img, to_u8(h), "weave", mode=LM.OVERLAY, opacity=75)
    hs = field_blur(h, S, S, 0.6)
    finish_lighting(img, T, hs, 3.0, 0.8, 30, None, 0)
    alb = T.save_albedo(img)
    log("  fabric mean albedo value %.3f" % (sum(alb[0::3]) / (S * S) / 255.0))
    T.done()


def make_skin():
    T = TexSet("skin", seed=331)
    S, rng = T.S, T.rng
    img = new_image(S)
    base = layer(img, "base", alpha=False)
    noise(base, 3, 3, detail=3, seed=3311)
    normalize(base)
    blur(base, 24)
    gradient_map(base, [(0, "#e3ad8c"), (0.5, "#ebb998"), (1, "#f2c6a6")])
    flush = layer(img, "flush", alpha=False, mode=LM.SOFTLIGHT, opacity=25)
    noise(flush, 2, 2, detail=2, seed=3312)
    normalize(flush)
    gradient_map(flush, [(0, "#c8a0a8"), (0.5, "#808080"), (1, "#ff9a7a")])
    fine = field_noise(S, 12, 12, detail=2, seed=3313)
    grey_layer(img, to_u8(fine), "fine", mode=LM.SOFTLIGHT, opacity=8)
    hn = field_noise(S, 8, 8, detail=3, seed=3314)
    h = array.array("f", [0.5 + 0.25 * hn[i] + 0.05 * fine[i] for i in range(S * S)])
    h = field_blur(h, S, S, 2.0)
    T.save_normal(h, 1.5)
    T.save_albedo(img)
    T.done()


def make_crystal():
    """Light, nearly neutral (slightly cool) facets so the game's tints still work."""
    T = TexSet("crystal", seed=341)
    S, rng = T.S, T.rng
    pts = poisson(S, S, 120, rng)
    cells = voronoi(pts, S, S)
    img = new_image(S)
    base = layer(img, "base", fill="#c8dbe6", alpha=False)
    fl = layer(img, "facets")
    planes = []
    for poly, (px, py) in zip(cells, pts):
        a = rng.uniform(0, 2 * math.pi)
        R = 110
        c0 = mix("#8fa8c4", "#b6cad8", rng.random())
        c1 = mix("#e6f2f8", "#ffffff", rng.random())
        gradient_poly(fl, poly, (px - math.cos(a) * R, py - math.sin(a) * R),
                      (px + math.cos(a) * R, py + math.sin(a) * R), c0, c1)
        tilt = rng.uniform(0.0015, 0.004)
        planes.append((px, py, 0.5, math.cos(a) * tilt, math.sin(a) * tilt))
    ids = id_field(S, cells)
    fh = facet_planes(S, ids, planes)
    edges = []
    for poly in cells:
        if rng.random() < 0.8:
            edges.append(poly + [poly[0]])
    el = layer(img, "edges", opacity=55)
    for e in edges:
        stroke(el, e, "#ffffff", 2.4, "2. Hardness 075")
    ed = layer(img, "edge_dark", opacity=35)
    for e in edges:
        stroke(ed, [(x + 2.0, y + 2.0) for x, y in e], "#6a86a8", 2.0, "2. Hardness 050")
    cloud = layer(img, "cloud", alpha=False, mode=LM.SOFTLIGHT, opacity=40)
    noise(cloud, 3, 2, detail=4, seed=3411)
    normalize(cloud)
    gradient_map(cloud, [(0, "#5a6aa0"), (0.5, "#808080"), (1, "#ffffff")])
    sparks = []
    for x, y in poisson(S, S, 60, rng):
        if rng.random() < 0.25:
            r = rng.uniform(5, 10)
            sparks.append([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22),
                           (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)])
    sp = layer(img, "sparkles", opacity=85)
    fill_polys(sp, sparks, "#ffffff")
    ef = strokes_field(S, edges, 2.4, 0.8)
    h = array.array("f", [fh[i] + 0.04 * ef[i] for i in range(S * S)])
    T.save_normal(h, 40.0)
    T.save_albedo(img)
    hn = field_noise(S, 6, 6, detail=3, seed=3412)
    T.save_grey("roughness", array.array("f", [clamp(0.08 + 0.06 * hn[i]) for i in range(S * S)]))
    T.done()


SETS = {
    "rubber": make_rubber,
    "leather": make_leather,
    "fabric": make_fabric,
    "skin": make_skin,
    "crystal": make_crystal,
}
