"""make_ui_logo.py: the RUNEWIRE title logo (assets/textures/ui/ui_title_logo.png, 1400x420).

Lilita One letters set on a gentle arch, each with a bevelled gold/brass face, a dark rim and
its own outline; a thick shared outline with a 3D extrusion; a brass gear and a glowing rune
ring behind the word; violet (magic, left) to teal (tech, right) glow; sparkles.

Run from the project root:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_ui_logo.py").read())' --quit
"""
import importlib
import math
import os
import sys

sys.dont_write_bytecode = True  # keep art/gimp free of rwui .pyc files
sys.path.insert(0, os.path.join(os.getcwd(), "art", "gimp"))
import rwui as R  # noqa: E402

importlib.reload(R)
from gi.repository import Gimp  # noqa: E402
from rwui import Pic  # noqa: E402

W, H = 1400, 420
INK = "#24152e"
FACE_STOPS = [(0.0, "#fff8cf"), (0.3, "#ffe07a"), (0.49, "#ffc93f"), (0.51, "#f5a524"), (0.8, "#e0861a"),
              (1.0, "#b8600f")]


def build_letters(p, text, size, spacing, cx, base_y, arch, tilt_scale, jitter, kern=None):
    """Return list of (layer, ink bounds) for each letter placed on an arch."""
    raw = []
    for ch in text:
        tl = p.text(ch, "Lilita One Regular", size, "#ffffff", 0, 0)
        lay = p.text_to_layer(tl, "#ffffff", "L_" + ch)
        p.sel_layer(lay)
        x1, y1, x2, y2 = p.sel_bounds()
        p.sel_none()
        raw.append((lay, x1, y1, x2, y2))
    kern = kern or {}
    gaps = [spacing + kern.get(text[i:i + 2], 0) for i in range(len(raw) - 1)]
    total = sum(r[3] - r[1] for r in raw) + sum(gaps)
    x = cx - total / 2.0
    half = total / 2.0
    out = []
    for i, (lay, x1, y1, x2, y2) in enumerate(raw):
        w = x2 - x1
        mid = x + w / 2.0
        u = (mid - cx) / half
        by = base_y + arch * u * u
        dx = x - x1
        dy = by - y2
        lay.transform_translate(dx, dy)
        lay.resize_to_image_size()
        ang = math.atan(2 * arch * u / half) * tilt_scale + jitter[i % len(jitter)]
        if abs(ang) > 1e-4:
            Gimp.context_set_transform_resize(Gimp.TransformResize.ADJUST)
            Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
            lay = lay.transform_rotate(ang, False, mid, by - (y2 - y1) / 2.0)
            lay.resize_to_image_size()
        p.sel_layer(lay)
        b = p.sel_bounds()
        p.sel_none()
        out.append((lay, b))
        x += w + (gaps[i] if i < len(gaps) else 0)
    return out


def letter_unit(p, lay, b, idx):
    """Paint one letter: gold face, bevel, gloss, dark rim and its own outline. Returns merged layer."""
    x1, y1, x2, y2 = b
    p.sel_layer(lay)
    ch = p.save_sel()
    # face gradient
    p.load_sel(ch)
    p.grad(lay, FACE_STOPS, 0, y1, 0, y2)
    # bevel: bright top-left rim, deep bottom-right rim
    p.crescent(ch, -5, -5, feather=1.5)
    p.fill(lay, "#fffbe8", 90)
    p.crescent(ch, 5, 6, feather=2)
    p.fill(lay, "#a5530f", 60)
    # gloss streak on the upper part
    p.load_sel(ch)
    p.shrink(9)
    g = p.save_sel()
    p.sel_ellipse((x1 + x2) / 2 - (x2 - x1) * 0.12, y1 + (y2 - y1) * 0.2, (x2 - x1) * 0.42, (y2 - y1) * 0.13)
    p.load_sel(g, R.INTER)
    p.feather(3)
    p.load_sel(g, R.INTER)
    p.fill(lay, "#ffffff", 55)
    p.sel_none()
    # dark rim + own outline
    rim = p.layer("rim_%d" % idx, below=lay)
    p.load_sel(ch)
    p.grow(4)
    p.fill(rim, "#6b3010")
    ol = p.layer("ol_%d" % idx, below=rim)
    p.load_sel(ch)
    p.grow(10)
    p.fill(ol, INK)
    p.sel_none()
    return p.merge_layers([lay, rim, ol], name="unit_%d" % idx)


def gear_motif(p, cx, cy):
    """Big brass gear (mostly hidden behind the letters) with a teal rune ring around it."""
    gl = p.layer("gear")
    p.sel_poly(R.gear_pts(cx, cy, 112, 138, 13, rot=0.08, per_tooth=36))
    p.sel_ellipse(cx, cy, 46, op=R.SUB)
    gch = p.save_sel()
    gol = p.layer("gear_ol", below=gl)
    p.load_sel(gch)
    p.grow(8)
    p.fill(gol, INK)
    p.load_sel(gch)
    p.grad(gl, [(0, "#f2c66a"), (0.5, "#cf8f35"), (1, "#8f531f")], cx - 136, cy - 136, cx + 136, cy + 136)
    R.bevel(p, gl, gch, d=4, hi="#fff0bf", lo="#5e3016", hi_op=85, lo_op=70)
    # spokes cut-outs (darker recesses) to read as a gear wheel
    p.sel_none()
    for k in range(5):
        a = -math.pi / 2 + math.tau * k / 5 + 0.3
        p.sel_ellipse(cx + 80 * math.cos(a), cy + 80 * math.sin(a), 20, op=R.ADD)
    p.load_sel(gch, R.INTER)
    p.fill(gl, "#4a2412", 85)
    p.sel_none()
    # hub ring
    p.sel_ellipse(cx, cy, 46)
    p.sel_ellipse(cx, cy, 35, op=R.SUB)
    p.fill(gl, "#7a4219")
    p.sel_none()
    return gl, gol


def rune_ring(p, cx, cy, r):
    lay = p.layer("rune_ring")
    pts = R.circle_pts(cx, cy, r, n=240)
    p.stroke(lay, [pts + [pts[0]]], 5, "#bffcf2")
    pts2 = R.circle_pts(cx, cy, r + 24, n=240)
    p.stroke(lay, [pts2 + [pts2[0]]], 3, "#bffcf2")
    gb = R.GlyphBatch()
    n = 26
    for i in range(n):
        a = -math.pi / 2 + math.tau * (i + 0.5) / n
        gb.add(R.GLYPHS[(i * 7 + 3) % len(R.GLYPHS)], cx + (r + 12) * math.cos(a), cy + (r + 12) * math.sin(a), 14,
               ang=a + math.pi / 2)
    gb.draw(p, lay, 2.6, "#e6fffb")
    glow = p.glow(lay, "#3ff2d6", grow=3, blur=9, opacity=90, name="rune_glow")
    return lay, glow


def make_logo():
    p = Pic(W, H)
    cx, base_y = W / 2, 292
    letters = build_letters(p, "RUNEWIRE", 240, -10, cx, base_y, arch=-26, tilt_scale=0.55,
                            jitter=[0.0, 0.02, -0.015, 0.012, -0.02, 0.015, -0.01, 0.018],
                            kern={"WI": 12, "IR": 12})
    units = [letter_unit(p, lay, b, i) for i, (lay, b) in enumerate(letters)]
    # union silhouette of the letters
    p.sel_none()
    for u in units:
        p.sel_layer(u, R.ADD)
    union = p.save_sel()
    ux1, uy1, ux2, uy2 = p.sel_bounds()
    # thick shared outline
    outer = p.layer("outer_outline")
    p.load_sel(union)
    p.grow(6)
    base_ch = p.save_sel()
    p.fill(outer, INK)
    # 3D extrusion: union of the outline silhouette shifted down 1..16 px
    p.load_sel(base_ch)
    for k in range(16):
        p.translate_sel(0, 1)
        p.load_sel(base_ch, R.ADD)
    full = p.save_sel()
    ext = p.layer("extrude")
    p.load_sel(full)
    p.grad(ext, [(0, "#9a4a1c"), (1, "#4a1c18")], 0, uy1 + 40, 0, uy2 + 26)
    # thin highlight where the outline meets the extrusion
    p.load_sel(full)
    p.load_sel(base_ch, R.SUB)
    ext_vis = p.save_sel()
    p.crescent(ext_vis, 0, -2, feather=1)
    p.fill(ext, "#c86a2a", 60)
    ext_ol = p.layer("extrude_ol")
    p.load_sel(full)
    p.grow(4)
    p.fill(ext_ol, INK)
    p.sel_none()
    # soft drop shadow
    sh = p.layer("shadow")
    p.load_sel(full)
    p.grow(4)
    p.fill(sh, "#140d24")
    p.sel_none()
    p.blur(sh, 10)
    sh.set_offsets(0, 12)
    sh.resize_to_image_size()
    sh.set_opacity(55)
    # gear + rune ring behind the word
    gear, gear_ol = gear_motif(p, cx + 4, base_y - 92)
    ring, ring_glow = rune_ring(p, cx + 4, base_y - 92, 152)
    # back glow: violet (magic) to teal (tech)
    back = p.layer("back_glow")
    p.load_sel(full)
    p.grow(24)
    p.grad(back, [(0, "#9b5cff"), (0.42, "#a07cff"), (0.58, "#4fd6e8"), (1, "#3ff2d6")], ux1, 0, ux2, 0)
    p.sel_none()
    p.blur(back, 24)
    # sparkles
    sp = p.layer("sparkles")
    for (x, y, r, c) in ((ux1 + 46, uy1 + 30, 26, "#ffffff"), (ux2 - 120, uy1 + 18, 18, "#ffffff"),
                         (cx - 168, uy1 - 22, 13, "#e9dbff"), (ux2 + 6, uy2 - 64, 15, "#c9fff6"),
                         (ux1 - 10, uy2 - 40, 12, "#e9dbff"), (cx + 230, uy2 + 40, 10, "#c9fff6")):
        R.spark4(p, sp, x, y, r, c, 100)
    spg = p.glow(sp, "#ffffff", grow=1, blur=5, opacity=70, name="sparkle_glow")
    order = [sp, spg] + list(reversed(units)) + [outer, ext, ext_ol, sh, gear, gear_ol, ring, ring_glow, back]
    for k, lay in enumerate(order):
        p.img.reorder_item(lay, None, k)
    p.save(os.path.join(R.UI_DIR, "ui_title_logo.png"))
    p.close()


R.run_all([make_logo], logpath="/tmp/rwui_logo_log.txt")
