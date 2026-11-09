"""make_ui.py: RuneWire UI textures (assets/textures/ui/).

Panels, buttons, hotbar slots, bar frame/fill, coin, crosshair and quest markers.
The logo is made by make_ui_logo.py and the icons by make_icons.py.

Run from the project root:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_ui.py").read())' --quit

Optional: RW_ONLY="ui_panel,ui_slot" rebuilds a subset.

9-slice layout rule: every texel that varies along an edge (corner plates, rivets, gems,
sparkles) sits inside the corner patches; the edge strips only vary across the edge.
The margins the game should use are listed in NINE_SLICE below.
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

OUT = R.UI_DIR
INK = "#2b1a24"          # warm-plum outline for brass / parchment pieces
INK_HUD = "#141826"      # outline for the crosshair

# left, top, right, bottom (px) for StyleBoxTexture / NinePatchRect / TextureProgressBar
NINE_SLICE = {
    "ui_panel.png": (48, 48, 48, 48),
    "ui_panel_dark.png": (48, 48, 48, 48),
    "ui_button.png": (24, 26, 24, 28),
    "ui_button_hover.png": (24, 26, 24, 28),
    "ui_button_pressed.png": (24, 26, 24, 28),
    "ui_bar_frame.png": (20, 12, 20, 12),
    "ui_bar_fill.png": (20, 12, 20, 12),
}


def rr(p, x, y, w, h, r):
    p.sel_rrect(x, y, w, h, r)
    return p.save_sel()


def mirror4(S, fn):
    """Call fn(mx, my) for the four corners; mx/my map top-left coords to that corner."""
    for fx in (False, True):
        for fy in (False, True):
            fn((lambda x, fx=fx: S - x if fx else x), (lambda y, fy=fy: S - y if fy else y))


# --------------------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------------------
def panel_frame(p, S, band_out, band_in, radius_out, radius_in, ink=INK):
    """Outline + bevelled brass band. Returns (outline layer, band layer, inner channel)."""
    outer = rr(p, band_out - 3, band_out - 3, S - 2 * (band_out - 3), S - 2 * (band_out - 3), radius_out + 3)
    frame = rr(p, band_out, band_out, S - 2 * band_out, S - 2 * band_out, radius_out)
    inner = rr(p, band_in, band_in, S - 2 * band_in, S - 2 * band_in, radius_in)
    groove = rr(p, band_in - 2, band_in - 2, S - 2 * (band_in - 2), S - 2 * (band_in - 2), radius_in + 2)
    lo = p.layer("outline")
    p.load_sel(outer)
    p.fill(lo, ink)
    band = p.layer("band")
    p.load_sel(frame)
    p.load_sel(groove, R.SUB)
    band_ch = p.save_sel()
    p.fill(band, "#e6aa44")
    # raised ridge along the middle of the band (uniform along every edge)
    p.load_sel(groove)
    p.grow(3)
    rg = p.save_sel()
    p.load_sel(frame)
    p.shrink(3)
    p.load_sel(rg, R.SUB)
    p.feather(1.5)
    p.load_sel(band_ch, R.INTER)
    p.fill(band, "#f8d77e", 85)
    R.bevel(p, band, band_ch, d=2, hi="#fff4c8", lo="#7a4219", hi_op=90, lo_op=70)
    return lo, band, inner


def parchment_fill(p, lay, inner, S, margin=48, seed=3):
    rng = random.Random(seed)
    p.load_sel(inner)
    p.grad(lay, [(0, "#fbecc6"), (0.5, "#f4e0b2"), (1, "#ecd29e")], 0, 18, 0, S - 18)
    # big soft painted blotches, centre patch only (keeps the 9-slice edge strips uniform)
    for i in range(14):
        p.load_sel(inner)
        p.sel_rect(margin + 2, margin + 2, S - 2 * margin - 4, S - 2 * margin - 4, op=R.INTER)
        x = rng.uniform(margin + 10, S - margin - 10)
        y = rng.uniform(margin + 10, S - margin - 10)
        c = rng.choice(["#ecd39f", "#fff3d4", "#e9cc93", "#fbe9c0"])
        p.dab(lay, x, y, rng.uniform(60, 110), c, brush="2. Hardness 025", opacity=rng.uniform(18, 32))
    # warm burnt edge (uniform along each edge)
    p.load_sel(inner)
    p.shrink(9)
    p.feather(22)
    p.invert()
    p.load_sel(inner, R.INTER)
    p.fill(lay, "#c9995a", 55)
    p.load_sel(inner)
    p.shrink(3)
    p.feather(5)
    p.invert()
    p.load_sel(inner, R.INTER)
    p.fill(lay, "#a8733f", 45)
    # shadow cast by the raised frame onto the parchment (top + left inner edges)
    p.crescent(inner, -5, -5, feather=3)
    p.fill(lay, "#7e5129", 35)
    p.sel_none()


def corner_bracket(p, S, layer_ink, layer_metal, mx, my, gem_stops, glow_lay=None):
    """Brass L-bracket with a round boss + gem on one corner (top-left coords mirrored)."""
    def X(v):
        return mx(v)

    def Y(v):
        return my(v)

    def rect(x0, y0, x1, y1, op):
        xa, xb = sorted((X(x0), X(x1)))
        ya, yb = sorted((Y(y0), Y(y1)))
        p.sel_rect(xa, ya, xb - xa, yb - ya, op=op)

    p.sel_none()
    p.sel_ellipse(X(25), Y(25), 18, op=R.ADD)
    rect(6, 6, 45, 20, R.ADD)
    rect(6, 6, 20, 45, R.ADD)
    p.round_sel(convex=4, concave=5)
    ch = p.save_sel()
    p.load_sel(ch)
    p.grow(3)
    p.fill(layer_ink, INK)
    p.load_sel(ch)
    ys = sorted((Y(6), Y(45)))
    p.grad(layer_metal, R.BRASS_STOPS, 0, ys[0], 0, ys[1])
    R.bevel(p, layer_metal, ch, d=2, hi="#fff6d2", lo="#7a4219", hi_op=90, lo_op=70)
    # engraved line following the bracket
    p.load_sel(ch)
    p.shrink(4)
    p.border(1)
    p.load_sel(ch, R.INTER)
    p.fill(layer_metal, "#a8641f", 55)
    p.sel_none()
    R.gem(p, layer_metal, X(25), Y(25), 8.5, gem_stops, rim=INK, glow=None)
    R.rivet(p, layer_metal, X(39), Y(13), 3.2, ink=INK)
    R.rivet(p, layer_metal, X(13), Y(39), 3.2, ink=INK)


def ui_panel():
    S = 256
    p = Pic(S, S)
    lo, band, inner = panel_frame(p, S, band_out=6, band_in=19, radius_out=22, radius_in=10)
    parch = p.layer("parchment")
    parchment_fill(p, parch, inner, S)
    ink = p.layer("corner_ink")
    metal = p.layer("corner_metal")
    teal = [(0, "#d5fff8"), (0.4, "#45f0d6"), (1, "#0f7272")]
    mirror4(S, lambda mx, my: corner_bracket(p, S, ink, metal, mx, my, teal))
    p.save(os.path.join(OUT, "ui_panel.png"))
    p.close()


def tech_corner(p, S, layer_ink, layer_metal, glow_lay, mx, my):
    """Chamfered brass corner plate with two rivets and a teal status light."""
    pts = [(5, 5), (40, 5), (40, 15), (25, 15), (15, 25), (15, 40), (5, 40)]
    pts = [(mx(x), my(y)) for x, y in pts]
    p.sel_poly(pts)
    p.round_sel(convex=2, concave=2)
    ch = p.save_sel()
    p.load_sel(ch)
    p.grow(3)
    p.fill(layer_ink, INK)
    ys = sorted((my(5), my(40)))
    p.load_sel(ch)
    p.grad(layer_metal, R.BRASS_STOPS, 0, ys[0], 0, ys[1])
    R.bevel(p, layer_metal, ch, d=2, hi="#fff6d2", lo="#7a4219", hi_op=90, lo_op=70)
    R.rivet(p, layer_metal, mx(33), my(10), 2.8, ink=INK)
    R.rivet(p, layer_metal, mx(10), my(33), 2.8, ink=INK)
    R.gem(p, layer_metal, mx(12), my(12), 4.2, [(0, "#eafffb"), (0.45, "#4ff5dc"), (1, "#127a7a")], rim=INK)
    p.sel_ellipse(mx(12), my(12), 10)
    p.feather(8)
    p.fill(glow_lay, "#3ff2d6", 60)
    p.sel_none()


def ui_panel_dark():
    S = 256
    p = Pic(S, S)
    lo, band, inner = panel_frame(p, S, band_out=6, band_in=15, radius_out=20, radius_in=10)
    slate = p.layer("slate")
    p.load_sel(inner)
    p.grad(slate, [(0, "#33415f"), (0.5, "#273450"), (1, "#1b2439")], 0, 15, 0, S - 15)
    # inner shadow from the frame
    p.load_sel(inner)
    p.shrink(4)
    p.feather(14)
    p.invert()
    p.load_sel(inner, R.INTER)
    p.fill(slate, "#0d1220", 55)
    p.crescent(inner, -4, -4, feather=2)
    p.fill(slate, "#0a0e18", 45)
    # faint bottom-edge bounce light
    p.crescent(inner, 3, 3, feather=2)
    p.fill(slate, "#4a5d84", 45)
    # teal inlay line (uniform along every edge)
    p.load_sel(inner)
    p.shrink(9)
    a = p.save_sel()
    p.load_sel(inner)
    p.shrink(11)
    b = p.save_sel()
    p.load_sel(a)
    p.load_sel(b, R.SUB)
    p.fill(slate, "#3ff2d6", 30)
    p.sel_none()
    glow = p.layer("glow", mode=R.SCREEN)
    ink = p.layer("corner_ink")
    metal = p.layer("corner_metal")
    mirror4(S, lambda mx, my: tech_corner(p, S, ink, metal, glow, mx, my))
    p.save(os.path.join(OUT, "ui_panel_dark.png"))
    p.close()


# --------------------------------------------------------------------------------------
# Buttons 192x64
# --------------------------------------------------------------------------------------
BTN_FACES = {
    "normal": [(0, "#5be6d3"), (0.45, "#27b9ad"), (1, "#127c7b")],
    "hover": [(0, "#9dfff0"), (0.45, "#3fdcc9"), (1, "#169a95")],
    "pressed": [(0, "#1f9f98"), (0.5, "#167f7d"), (1, "#0f5d61")],
}


def make_button(state, fname):
    W, H = 192, 64
    p = Pic(W, H)
    dy = 4 if state == "pressed" else 0
    outline = rr(p, 1, 1 + dy, W - 2, H - 2 - dy, 20)
    lip = rr(p, 4, 10, W - 8, 50, 17)
    rim = rr(p, 4, 4 + dy, W - 8, 50, 17)
    face = rr(p, 9, 9 + dy, W - 18, 40, 12)
    lo = p.layer("outline")
    p.load_sel(outline)
    p.fill(lo, INK)
    body = p.layer("body")
    p.load_sel(lip)
    p.fill(body, "#7c4519")
    p.crescent(lip, 0, 2, feather=1)
    p.fill(body, "#4e2a12", 60)
    rim_stops = R.BRASS_STOPS if state != "hover" else [(0, "#fffbe0"), (0.3, "#ffe08a"), (0.62, "#eeab45"), (1, "#b56c22")]
    R.brass(p, body, rim, 4 + dy, 54 + dy, d=2, stops=rim_stops)
    # dark groove around the face
    p.load_sel(face)
    p.grow(2)
    p.fill(body, "#5a3014", 90)
    fl = p.layer("face")
    p.load_sel(face)
    p.grad(fl, BTN_FACES[state], 0, 9 + dy, 0, 49 + dy)
    if state == "pressed":
        # inner shadow along the top: the face is pushed in
        p.crescent(face, 0, -5, feather=3)
        p.fill(fl, "#08353a", 60)
    else:
        p.crescent(face, 0, 3, feather=1.5)
        p.fill(fl, "#0b4b50", 55)
        p.crescent(face, 0, -2, feather=1)
        p.fill(fl, "#e6fffb", 70)
        # gloss band: rounded rect, uniform across the stretchable middle
        p.sel_rrect(16, 12 + dy, W - 32, 13, 6.5)
        p.load_sel(face, R.INTER)
        p.fill(fl, "#ffffff", 30 if state == "normal" else 38)
    if state == "hover":
        p.load_sel(face)
        p.shrink(1)
        p.border(3)
        p.feather(2)
        p.load_sel(face, R.INTER)
        p.fill(fl, "#e6fffb", 40)
    # corner sparkle (inside the left corner patch)
    if state != "pressed":
        R.spark4(p, fl, 17, 17 + dy, 4.0 if state == "normal" else 5.0, "#ffffff", 90)
    p.sel_none()
    p.save(os.path.join(OUT, fname))
    p.close()


def ui_buttons():
    make_button("normal", "ui_button.png")
    make_button("hover", "ui_button_hover.png")
    make_button("pressed", "ui_button_pressed.png")


# --------------------------------------------------------------------------------------
# Hotbar slots 128x128
# --------------------------------------------------------------------------------------
def make_slot(selected, fname):
    S = 128
    p = Pic(S, S)
    outline = rr(p, 8, 8, 112, 112, 27)
    ring = rr(p, 11, 11, 106, 106, 24)
    rec = rr(p, 22, 22, 84, 84, 14)
    groove = rr(p, 20, 20, 88, 88, 16)
    if selected:
        gl = p.layer("glow")
        p.load_sel(outline)
        p.grow(3)
        p.fill(gl, "#3ff2d6")
        p.sel_none()
        p.blur(gl, 5)
        g2 = p.layer("glow2", below=gl)
        p.load_sel(outline)
        p.grow(2)
        p.fill(g2, "#3ff2d6")
        p.sel_none()
        p.blur(g2, 2.2)
    lo = p.layer("outline")
    p.load_sel(outline)
    p.fill(lo, INK)
    if selected:
        p.load_sel(outline)
        p.border(1)
        p.load_sel(outline, R.INTER)
        p.fill(lo, "#1d6d6a", 70)
    metal = p.layer("ring")
    p.load_sel(ring)
    p.load_sel(groove, R.SUB)
    band = p.save_sel()
    stops = R.BRASS_STOPS if not selected else [(0, "#fffbe0"), (0.3, "#ffe28e"), (0.62, "#efb04a"), (1, "#b56c22")]
    p.load_sel(band)
    p.grad(metal, stops, 0, 11, 0, 117)
    R.bevel(p, metal, band, d=2, hi="#fff6d2", lo="#7a4219", hi_op=90, lo_op=70)
    p.load_sel(groove)
    p.fill(metal, "#4a2a14")
    well = p.layer("well")
    p.load_sel(rec)
    p.grad(well, [(0, "#34425f"), (0.6, "#222c43"), (1, "#151c2c")], 64, 56, 64 + 58, 56, kind=R.RADIAL)
    p.crescent(rec, -6, -6, feather=4)
    p.fill(well, "#080b14", 65)
    p.crescent(rec, 3, 3, feather=2)
    p.fill(well, "#4e6288", 50)
    if selected:
        p.load_sel(rec)
        p.shrink(1)
        p.border(5)
        p.feather(4)
        p.load_sel(rec, R.INTER)
        p.fill(well, "#3ff2d6", 55)
        p.load_sel(rec)
        p.shrink(10)
        p.feather(18)
        p.fill(well, "#1d8c8a", 25)
        p.sel_none()
    for x, y in ((21.5, 21.5), (106.5, 21.5), (21.5, 106.5), (106.5, 106.5)):
        R.rivet(p, metal, x, y, 3.3, ink=INK)
    if selected:
        for x, y in ((64, 15.5), (64, 112.5)):
            R.gem(p, metal, x, y, 4.6, [(0, "#eafffb"), (0.45, "#4ff5dc"), (1, "#127a7a")], rim=INK)
        fx = p.layer("sparkles")
        R.spark4(p, fx, 104, 26, 7, "#ffffff", 95)
        R.spark4(p, fx, 23, 101, 5, "#c9fff6", 85)
    p.sel_none()
    p.save(os.path.join(OUT, fname))
    p.close()


def ui_slots():
    make_slot(False, "ui_slot.png")
    make_slot(True, "ui_slot_selected.png")


# --------------------------------------------------------------------------------------
# Bar frame + fill (same canvas; the fill sits exactly in the frame's track)
# --------------------------------------------------------------------------------------
BAR_W, BAR_H = 256, 40
# The frame border (outline + brass + groove) is 10 px; the track and fill live entirely in the
# stretchable middle rows, so 12 px top/bottom margins let the bar draw at any height >= 24 px.


def ui_bar_frame():
    W, H = BAR_W, BAR_H
    p = Pic(W, H)
    outline = rr(p, 1, 1, W - 2, H - 2, 19)
    rim = rr(p, 4, 4, W - 8, H - 8, 16)
    groove = rr(p, 9, 9, W - 18, H - 18, 11)
    track = rr(p, 10, 10, W - 20, H - 20, 10)
    lo = p.layer("outline")
    p.load_sel(outline)
    p.fill(lo, INK)
    metal = p.layer("rim")
    p.load_sel(rim)
    p.load_sel(groove, R.SUB)
    band = p.save_sel()
    p.load_sel(band)
    p.grad(metal, R.BRASS_STOPS, 0, 4, 0, H - 4)
    R.bevel(p, metal, band, d=2, hi="#fff6d2", lo="#7a4219", hi_op=90, lo_op=70)
    p.load_sel(groove)
    p.fill(metal, "#4a2a14")
    tr = p.layer("track")
    p.load_sel(track)
    p.grad(tr, [(0, "#0b101c"), (0.5, "#151d2e"), (1, "#24304a")], 0, 10, 0, H - 10)
    p.crescent(track, 0, -3, feather=1.5)
    p.fill(tr, "#05070d", 55)
    p.sel_none()
    p.save(os.path.join(OUT, "ui_bar_frame.png"))
    p.close()


def ui_bar_fill():
    W, H = BAR_W, BAR_H
    p = Pic(W, H)
    fill = rr(p, 11, 11, W - 22, H - 22, 9)
    lay = p.layer("fill")
    p.load_sel(fill)
    p.grad(lay, [(0, "#ffffff"), (0.42, "#f4f4f4"), (0.58, "#d6d6d6"), (1, "#a9a9a9")], 0, 11, 0, H - 11)
    p.crescent(fill, 0, 2, feather=1)
    p.fill(lay, "#8a8a8a", 70)
    p.sel_rrect(17, 13, W - 34, 4, 2)
    p.load_sel(fill, R.INTER)
    p.fill(lay, "#ffffff", 95)
    p.sel_none()
    p.save(os.path.join(OUT, "ui_bar_fill.png"))
    p.close()


# --------------------------------------------------------------------------------------
# Coin 128x128
# --------------------------------------------------------------------------------------
def ui_coin():
    S = 128
    cx, cy, r = 62, 58, 48
    th = 8
    p = Pic(S, S)
    face = p.shape(lambda: p.sel_ellipse(cx, cy, r))
    side = p.shape(lambda: p.sel_ellipse(cx, cy + th, r))
    p.load_sel(face)
    p.load_sel(side, R.ADD)
    silh = p.save_sel()
    lo = p.layer("outline")
    p.load_sel(silh)
    p.grow(4)
    p.fill(lo, INK)
    body = p.layer("body")
    p.load_sel(side)
    p.grad(body, [(0, "#f0a01e"), (0.5, "#c06a10"), (1, "#7e3c0c")], cx - r, 0, cx + r, 0)
    # coin edge ridges (reeded edge), only on the visible side band
    p.load_sel(side)
    p.load_sel(face, R.SUB)
    edge = p.save_sel()
    ridges = []
    for i in range(1, 22):
        a = math.pi * i / 22
        x = cx - r * math.cos(a)
        ridges.append([(x, cy + r * math.sin(a) - 2), (x, cy + r * math.sin(a) + th + 2)])
    rl = p.layer("ridges")
    p.stroke(rl, ridges, 1.6, "#7a3a0c", opacity=70)
    p.clip_to(rl, edge)
    p.load_sel(face)
    p.grad(body, [(0, "#fff7c4"), (0.35, "#ffd650"), (0.7, "#f1a51f"), (1, "#c26b10")], cx - r * 0.7, cy - r * 0.8,
           cx + r * 0.7, cy + r * 0.8)
    # raised outer rim
    inner = p.shape(lambda: p.sel_ellipse(cx, cy, r - 8))
    p.load_sel(face)
    p.load_sel(inner, R.SUB)
    rimc = p.save_sel()
    R.bevel(p, body, rimc, d=2, hi="#fff8d8", lo="#a35a0c", hi_op=90, lo_op=70)
    p.load_sel(inner)
    p.grad(body, [(0, "#ffe27a"), (0.5, "#f8bd34"), (1, "#d98a17")], cx - r * 0.5, cy - r * 0.6, cx + r * 0.5,
           cy + r * 0.6)
    p.crescent(inner, -3, -3, feather=1.5)
    p.fill(body, "#b8650e", 70)
    p.crescent(inner, 2, 2, feather=1)
    p.fill(body, "#fff4c4", 80)
    p.sel_none()
    # emblem: embossed gear with a rune in its hub
    em = p.layer("emblem")
    p.sel_poly(R.gear_pts(cx, cy, 24, 31, 10, rot=0.1, per_tooth=28))
    p.sel_ellipse(cx, cy, 13, op=R.SUB)
    gear = p.save_sel()
    p.load_sel(gear)
    p.grow(2)
    p.fill(em, "#a85a0c", 90)
    p.load_sel(gear)
    p.grad(em, [(0, "#fff0a0"), (0.5, "#ffcf45"), (1, "#e3961b")], cx - 30, cy - 30, cx + 30, cy + 30)
    R.bevel(p, em, gear, d=2, hi="#fffbe6", lo="#b0600d", hi_op=95, lo_op=75)
    gb = R.GlyphBatch()
    gb.add(R.GLYPHS[1], cx, cy, 15)
    gb.draw(p, em, 3.0, "#9a4f0b")
    # shine
    sh = p.layer("shine")
    p.sel_poly(R.xform([(-1, -0.18), (1, -0.18), (1, 0.18), (-1, 0.18)], 40, 40, math.radians(-45), cx - 18, cy - 18))
    p.load_sel(face, R.INTER)
    p.feather(3)
    p.load_sel(face, R.INTER)
    p.fill(sh, "#ffffff", 35)
    p.sel_none()
    R.spark4(p, sh, cx + 36, cy - 34, 11, "#ffffff", 100)
    R.spark4(p, sh, cx - 30, cy + 30, 5, "#fff6c2", 85)
    p.drop_shadow(lo, 0, 4, 3, c="shadow", opacity=45)
    p.save(os.path.join(OUT, "ui_coin.png"))
    p.close()


# --------------------------------------------------------------------------------------
# Crosshair 64x64
# --------------------------------------------------------------------------------------
def ui_crosshair():
    S = 64
    c = S / 2
    p = Pic(S, S)
    ticks = []
    for a in (0, 90, 180, 270):
        ar = math.radians(a)
        ticks.append([(c + 9 * math.cos(ar), c + 9 * math.sin(ar)), (c + 20 * math.cos(ar), c + 20 * math.sin(ar))])
    dark = p.layer("dark")
    p.stroke(dark, ticks, 8.5, INK_HUD, opacity=100)
    p.sel_ellipse(c, c, 4.6)
    p.fill(dark, INK_HUD)
    p.sel_none()
    dark.set_opacity(80)
    white = p.layer("white")
    p.stroke(white, ticks, 4.5, "#ffffff")
    p.sel_ellipse(c, c, 2.6)
    p.fill(white, "#ffffff")
    p.sel_none()
    p.save(os.path.join(OUT, "ui_crosshair.png"))
    p.close()


# --------------------------------------------------------------------------------------
# Quest markers 128x128
# --------------------------------------------------------------------------------------
def shield_pts(cx=64, top=10, w=88, h=104):
    x0, x1 = cx - w / 2, cx + w / 2
    ctrl = [(x0, top + 4), (cx, top - 2), (x1, top + 4), (x1 + 1, top + 40), (x1 - 8, top + 70), (cx, top + h),
            (x0 + 8, top + 70), (x0 - 1, top + 40)]
    return R.spline(ctrl, sharp=(0, 2, 5), closed=True, samples=20)


def make_quest(symbol, field, glow_c, fname):
    S = 128
    p = Pic(S, S)
    shp = p.shape(lambda: p.sel_poly(shield_pts()))
    p.load_sel(shp)
    p.round_sel(convex=3)
    shp = p.save_sel()
    p.load_sel(shp)
    p.shrink(7)
    fld = p.save_sel()
    lo = p.layer("outline")
    p.load_sel(shp)
    p.grow(4)
    p.fill(lo, INK)
    rim = p.layer("rim")
    p.load_sel(shp)
    p.load_sel(fld, R.SUB)
    band = p.save_sel()
    p.load_sel(band)
    p.grad(rim, R.BRASS_STOPS, 0, 10, 0, 120)
    R.bevel(p, rim, band, d=2, hi="#fff6d2", lo="#7a4219", hi_op=90, lo_op=70)
    p.load_sel(fld)
    p.grow(1)
    p.fill(rim, "#4a2a14")
    fl = p.layer("field")
    p.load_sel(fld)
    p.grad(fl, field, 64, 40, 64 + 70, 40, kind=R.RADIAL)
    p.crescent(fld, -5, -6, feather=3)
    p.fill(fl, "#0a0716", 50)
    p.crescent(fld, 3, 3, feather=2)
    p.fill(fl, "#ffffff", 18)
    for x, y in ((25, 19), (103, 19)):
        R.rivet(p, rim, x, y, 3.2, ink=INK)
    # symbol in Lilita One
    tl = p.text(symbol, "Lilita One Regular", 86, "#ffffff", 0, 0)
    sym = p.text_to_layer(tl, "#ffffff", "symbol")
    p.sel_layer(sym)
    x1, y1, x2, y2 = p.sel_bounds()
    p.sel_none()
    sym.transform_translate(64 - (x1 + x2) / 2, 60 - (y1 + y2) / 2)
    sym.resize_to_image_size()
    p.sel_layer(sym)
    sch = p.save_sel()
    x1, y1, x2, y2 = p.sel_bounds()
    p.grad(sym, R.GOLD_STOPS, 0, y1, 0, y2)
    R.bevel(p, sym, sch, d=3, hi="#fffbe6", lo="#9a4f0b", hi_op=95, lo_op=70)
    so = p.outline(sym, 4, INK)
    p.load_sel(sch)
    p.grow(4)
    p.translate_sel(0, 4)
    p.load_sel(sch, R.SUB)
    sd = p.layer("symbol_depth", below=so)
    p.fill(sd, INK)
    p.sel_none()
    fx = p.layer("sparkle")
    R.spark4(p, fx, 96, 36, 8, "#ffffff", 95)
    # soft golden aura + drop shadow for readability at distance
    aura = p.layer("aura", below=lo)
    p.load_sel(shp)
    p.grow(6)
    p.fill(aura, glow_c)
    p.sel_none()
    p.blur(aura, 4)
    aura.set_opacity(55)
    p.save(os.path.join(OUT, fname))
    p.close()


def ui_quest_markers():
    make_quest("!", [(0, "#7a5ad8"), (0.6, "#4a32a6"), (1, "#2a1a6a")], "#ffd34a", "ui_quest_marker.png")
    make_quest("?", [(0, "#2fc7b8"), (0.6, "#167f80"), (1, "#0b4352")], "#ffd34a", "ui_quest_turnin.png")


ALL = [ui_panel, ui_panel_dark, ui_buttons, ui_slots, ui_bar_frame, ui_bar_fill, ui_coin, ui_crosshair,
       ui_quest_markers]
_only = [s for s in os.environ.get("RW_ONLY", "").split(",") if s]
R.run_all(ALL, only=_only or None, logpath="/tmp/rwui_ui_log.txt")
