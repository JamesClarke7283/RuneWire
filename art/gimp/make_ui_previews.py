"""make_ui_previews.py: review sheets for the UI / VFX / icon textures (art/previews/ui/).

Composes the exported PNGs inside GIMP: raw sheets on checker backgrounds, 9-slice stretch
tests (same patch maths as Godot's StyleBoxTexture / NinePatchRect), and HUD / menu mock-ups.
Run from the project root after the generators:

    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_ui_previews.py").read())' --quit
"""
import importlib
import math
import os
import sys

sys.dont_write_bytecode = True  # keep art/gimp free of rwui .pyc files
sys.path.insert(0, os.path.join(os.getcwd(), "art", "gimp"))
import rwui as R  # noqa: E402

importlib.reload(R)
from gi.repository import Gimp, Gio  # noqa: E402
from rwui import Pic  # noqa: E402

UI = R.UI_DIR
FX = R.FX_DIR
NINE = {
    "ui_panel.png": (48, 48, 48, 48),
    "ui_panel_dark.png": (48, 48, 48, 48),
    "ui_button.png": (24, 26, 24, 28),
    "ui_button_hover.png": (24, 26, 24, 28),
    "ui_button_pressed.png": (24, 26, 24, 28),
    "ui_bar_frame.png": (20, 12, 20, 12),
    "ui_bar_fill.png": (20, 12, 20, 12),
}


def ui(n):
    return os.path.join(UI, n)


def background(p, lay, c1, c2, sq=16):
    p.sel_none()
    try:
        p.fx(lay, "gegl:checkerboard", x=sq, y=sq, color1=R.col(c1), color2=R.col(c2))
    except Exception:
        p.fill(lay, c1)


def load(p, path):
    lay = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, p.img, Gio.File.new_for_path(path))
    p.img.insert_layer(lay, None, 0)
    return lay


def place(p, path, x, y, w=None, h=None, scale_up=False, center=True):
    lay = load(p, path)
    lw, lh = lay.get_width(), lay.get_height()
    if w is None:
        w, h = lw, lh
    s = min(w / lw, h / lh)
    if s > 1 and not scale_up:
        s = 1.0
    nw, nh = max(1, int(round(lw * s))), max(1, int(round(lh * s)))
    if (nw, nh) != (lw, lh):
        lay.scale(nw, nh, False)
    if center:
        lay.set_offsets(int(x + (w - nw) / 2), int(y + (h - nh) / 2))
    else:
        lay.set_offsets(int(x), int(y))
    return lay


def tint_layer(p, lay, c):
    """Multiply a layer's colour by c, keeping its alpha (as a modulate/tint does in game)."""
    t = p.layer("tint", mode=R.MULTIPLY, above=lay, fill=c)
    t.set_composite_mode(Gimp.LayerCompositeMode.CLIP_TO_BACKDROP)
    return p.img.merge_down(t, Gimp.MergeType.EXPAND_AS_NECESSARY)


def nine(p, path, x, y, w, h, margins=None, tint=None):
    """Draw a texture 9-sliced into the rect (x, y, w, h); returns the merged layer."""
    margins = margins or NINE[os.path.basename(path)]
    L, T, Rm, B = margins
    base = load(p, path)
    tw, th = base.get_width(), base.get_height()
    xs, ys = [0, L, tw - Rm, tw], [0, T, th - B, th]
    xd, yd = [0, L, w - Rm, w], [0, T, h - B, h]
    made = []
    for i in range(3):
        for j in range(3):
            sw, sh = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
            dw, dh = xd[i + 1] - xd[i], yd[j + 1] - yd[j]
            if sw <= 0 or sh <= 0 or dw <= 0 or dh <= 0:
                continue
            l = base.copy()
            p.img.insert_layer(l, None, 0)
            l.resize(sw, sh, -xs[i], -ys[j])
            if (dw, dh) != (sw, sh):
                l.scale(dw, dh, False)
            l.set_offsets(int(x + xd[i]), int(y + yd[j]))
            made.append(l)
    p.img.remove_layer(base)
    m = p.merge_layers(made, name="nine")
    m.resize_to_image_size()
    if tint:
        m = tint_layer(p, m, tint)
    return m


def label(p, s, x, y, size=15, c="#d8dde8", font="Nunito Bold"):
    return p.text(s, font, size, c, x, y)


def btn_text(p, s, x, y, w, h, size=26, pressed=False):
    """Label centred on the button face (face = 9 px below the top to 15 px above the bottom)."""
    tl = p.text(s, "Fredoka Bold", size, "#ffffff", 0, 0)
    lay = p.text_to_layer(tl, "#fff8e6", "btn_text")
    p.sel_layer(lay)
    x1, y1, x2, y2 = p.sel_bounds()
    p.sel_none()
    top = y + 9 + (4 if pressed else 0)
    bot = y + h - 15 + (4 if pressed else 0)
    lay.transform_translate(x + (w - (x2 - x1)) / 2 - x1, (top + bot) / 2 - (y2 - y1) / 2 - y1)
    lay.resize_to_image_size()
    p.outline(lay, 3, "#123c40")


def sheet(name, items, cols, cell_w, cell_h, c1, c2, label_c="#d8dde8", pad=16, scale_up=False):
    rows = (len(items) + cols - 1) // cols
    W = cols * (cell_w + pad) + pad
    H = rows * (cell_h + pad + 22) + pad
    p = Pic(W, H)
    bg = p.layer("bg", fill=c1)
    background(p, bg, c1, c2)
    for i, it in enumerate(items):
        path, lab = it[0], it[1]
        cx = pad + (i % cols) * (cell_w + pad)
        cy = pad + (i // cols) * (cell_h + pad + 22)
        if os.path.exists(path):
            place(p, path, cx, cy, cell_w, cell_h, scale_up=scale_up)
        label(p, lab, cx, cy + cell_h + 3, c=label_c)
    p.save(os.path.join(R.PREVIEW_DIR, name))
    p.close()


# --------------------------------------------------------------------------------------
def fx_sheets():
    names = ["vfx_glow", "vfx_spark", "vfx_smoke", "vfx_flame", "vfx_star", "vfx_scorch", "vfx_ring", "vfx_lightning"]
    items = [(os.path.join(FX, n + ".png"), n) for n in names]
    sheet("review_fx_dark.png", items, 4, 256, 256, "#1b2030", "#232a3c")
    sheet("review_fx_light.png", items, 4, 256, 256, "#8f9bb0", "#9aa6ba")
    sheet("review_rune_circle.png", [(os.path.join(FX, "vfx_rune_circle.png"), "vfx_rune_circle (1024)")], 1, 1024,
          1024, "#141826", "#1a1f30")


def fx_tinted():
    """VFX sprites multiplied by game-like tints over a dark scene colour."""
    W, H = 1100, 600
    p = Pic(W, H)
    p.layer("bg", fill="#1c2233")
    tints = [("vfx_glow", "#b07cff"), ("vfx_spark", "#ffe25a"), ("vfx_smoke", "#c9c3d6"), ("vfx_flame", "#ff8a2a"),
             ("vfx_star", "#ffd34a"), ("vfx_scorch", "#ffffff"), ("vfx_ring", "#3ff2d6"), ("vfx_lightning", "#5ff4ff")]
    for i, (n, t) in enumerate(tints):
        x = 20 + (i % 4) * 270
        y = 20 + (i // 4) * 290
        lay = place(p, os.path.join(FX, n + ".png"), x, y, 250, 250)
        lay.resize_to_image_size()
        tint_layer(p, lay, t)
        label(p, "%s x %s" % (n, t), x, y + 254)
    p.save(os.path.join(R.PREVIEW_DIR, "review_fx_tinted.png"))
    p.close()


def ui_raw():
    names = ["ui_panel", "ui_panel_dark", "ui_slot", "ui_slot_selected", "ui_button", "ui_button_hover",
             "ui_button_pressed", "ui_coin", "ui_bar_frame", "ui_bar_fill", "ui_quest_marker", "ui_quest_turnin",
             "ui_crosshair"]
    sheet("review_ui_raw.png", [(ui(n + ".png"), n) for n in names], 4, 256, 256, "#5d6b85", "#66748e")


def icon_sheets():
    names = ["icon_spell_arcane_bolt", "icon_spell_fireball", "icon_spell_chain_lightning", "icon_spell_mending_ward",
             "icon_upgrade_vitality", "icon_upgrade_arcana", "icon_upgrade_engineering", "icon_upgrade_capacity",
             "icon_upgrade_mana_regen"]
    sheet("review_icons.png", [(ui(n + ".png"), n.replace("icon_", "")) for n in names], 3, 256, 256, "#5d6b85",
          "#66748e")
    # small sizes, as they appear in the hotbar / shop, on light and dark
    W, H = 9 * 84 + 20, 2 * 96 + 40
    p = Pic(W, H)
    bg = p.layer("bg", fill="#2a3247")
    p.sel_rect(0, H // 2, W, H // 2)
    p.fill(bg, "#e9d9b4")
    p.sel_none()
    for i, n in enumerate(names):
        place(p, ui(n + ".png"), 10 + i * 84, 14, 72, 72, scale_up=False)
        place(p, ui(n + ".png"), 10 + i * 84, H // 2 + 14, 72, 72, scale_up=False)
    p.save(os.path.join(R.PREVIEW_DIR, "review_icons_small.png"))
    p.close()


def logo_sheet():
    W, H = 1440, 900
    p = Pic(W, H)
    bg = p.layer("bg")
    p.grad(bg, [(0, "#2a3a6e"), (0.55, "#6a7fc0"), (1, "#f2c79a")], 0, 0, 0, H // 2)
    p.sel_rect(0, H // 2, W, H // 2)
    p.fill(bg, "#151a28")
    p.sel_none()
    place(p, ui("ui_title_logo.png"), 20, 20, 1400, 420)
    place(p, ui("ui_title_logo.png"), 20, H // 2 + 20, 1400, 420)
    p.save(os.path.join(R.PREVIEW_DIR, "review_logo.png"))
    p.close()


def nineslice_sheet():
    W, H = 1300, 980
    p = Pic(W, H)
    bg = p.layer("bg", fill="#46536e")
    background(p, bg, "#46536e", "#4d5b78")
    nine(p, ui("ui_panel.png"), 20, 20, 560, 330)
    label(p, "ui_panel 560x330 (margins 48)", 24, 354)
    nine(p, ui("ui_panel.png"), 600, 20, 180, 420)
    label(p, "180x420", 604, 444)
    nine(p, ui("ui_panel_dark.png"), 800, 20, 480, 250)
    label(p, "ui_panel_dark 480x250 (48)", 804, 274)
    nine(p, ui("ui_panel_dark.png"), 800, 310, 220, 130)
    label(p, "220x130", 804, 444)
    y = 480
    for i, (n, txt) in enumerate((("ui_button.png", "Play"), ("ui_button_hover.png", "Options"),
                                   ("ui_button_pressed.png", "Quit"))):
        nine(p, ui(n), 20 + i * 300, y, 280, 72)
        btn_text(p, txt, 20 + i * 300, y, 280, 72, pressed="pressed" in n)
        label(p, n + " 280x72", 24 + i * 300, y + 76)
    nine(p, ui("ui_button.png"), 920, y, 360, 56)
    btn_text(p, "Accept Quest", 920, y, 360, 56, size=22)
    label(p, "ui_button 360x56", 924, y + 60)
    y = 620
    for k, (val, tint, nm) in enumerate(((0.85, "#ff4762", "health"), (0.55, "#45b4ff", "mana"),
                                         (0.3, "#ffcf3f", "xp"))):
        yy = y + k * 76
        for (x0, bw, bh) in ((20, 460, 44), (520, 320, 32), (880, 260, 24)):
            nine(p, ui("ui_bar_frame.png"), x0, yy, bw, bh)
            fw = int(40 + (bw - 40) * val)
            nine(p, ui("ui_bar_fill.png"), x0, yy, fw, bh, tint=tint)
            label(p, "%s %d%%  %dx%d" % (nm, val * 100, bw, bh), x0 + 4, yy + bh + 3, size=13)
    p.save(os.path.join(R.PREVIEW_DIR, "review_nineslice.png"))
    p.close()


def hud_mock():
    """Dark HUD over a sky/grass backdrop: hotbar slots with icons, bars, coins, quest marker."""
    W, H = 1280, 720
    p = Pic(W, H)
    bg = p.layer("bg")
    p.grad(bg, [(0, "#5aa7e6"), (0.6, "#a9d8f2"), (1, "#e8f1d0")], 0, 0, 0, 420)
    p.sel_rect(0, 420, W, 300)
    p.grad(bg, [(0, "#6dbb4f"), (1, "#3f7f3a")], 0, 420, 0, 720)
    p.sel_none()
    # crosshair + quest marker in the world
    place(p, ui("ui_crosshair.png"), W / 2 - 32, H / 2 - 32)
    place(p, ui("ui_quest_marker.png"), 860, 250, 84, 84, center=False)
    place(p, ui("ui_quest_turnin.png"), 300, 280, 64, 64, center=False)
    # top-left status panel
    nine(p, ui("ui_panel_dark.png"), 16, 16, 380, 132)
    for k, (val, tint) in enumerate(((0.8, "#ff4762"), (0.6, "#45b4ff"), (0.35, "#ffcf3f"))):
        yy = 34 + k * 34
        nine(p, ui("ui_bar_frame.png"), 40, yy, 330, 32)
        nine(p, ui("ui_bar_fill.png"), 40, yy, int(48 + (330 - 48) * val), 32, tint=tint)
    # coin counter
    nine(p, ui("ui_panel_dark.png"), W - 226, 16, 210, 72)
    place(p, ui("ui_coin.png"), W - 214, 20, 64, 64)
    tl = p.text("1,250", "Fredoka Bold", 34, "#ffe27a", W - 146, 28)
    p.outline(p.text_to_layer(tl, "#ffe27a"), 3, "#1b1426")
    # hotbar
    icons = ["icon_spell_arcane_bolt", "icon_spell_fireball", "icon_spell_chain_lightning", "icon_spell_mending_ward",
             "icon_upgrade_engineering", "icon_upgrade_capacity"]
    n = len(icons)
    sz = 84
    x0 = W / 2 - n * sz / 2
    nine(p, ui("ui_panel_dark.png"), int(x0 - 18), H - sz - 40, n * sz + 36, sz + 26)
    for i, ic in enumerate(icons):
        x = x0 + i * sz
        place(p, ui("ui_slot_selected.png" if i == 1 else "ui_slot.png"), x, H - sz - 27, sz, sz)
        place(p, ui(ic + ".png"), x + 14, H - sz - 27 + 12, sz - 28, sz - 28)
    p.save(os.path.join(R.PREVIEW_DIR, "review_hud_mock.png"))
    p.close()


def menu_mock():
    W, H = 1280, 720
    p = Pic(W, H)
    bg = p.layer("bg")
    p.grad(bg, [(0, "#1e1640"), (0.5, "#3a3a7a"), (1, "#e09a6a")], 0, 0, 0, H)
    place(p, ui("ui_title_logo.png"), W / 2 - 490, 20, 980, 294)
    nine(p, ui("ui_panel.png"), W / 2 - 200, 320, 400, 370)
    for i, (n, txt) in enumerate((("ui_button.png", "New Game"), ("ui_button_hover.png", "Continue"),
                                   ("ui_button.png", "Options"), ("ui_button_pressed.png", "Quit"))):
        y = 350 + i * 80
        nine(p, ui(n), W / 2 - 150, y, 300, 64)
        btn_text(p, txt, W / 2 - 150, y, 300, 64, size=28, pressed="pressed" in n)
    p.save(os.path.join(R.PREVIEW_DIR, "review_menu_mock.png"))
    p.close()


def shop_mock():
    """Parchment shop panel with upgrade icons, coin prices and buttons."""
    W, H = 900, 560
    p = Pic(W, H)
    bg = p.layer("bg", fill="#2c3550")
    nine(p, ui("ui_panel.png"), 20, 20, W - 40, H - 40)
    tl = p.text("Artificer's Upgrades", "Lilita One Regular", 40, "#5a2f14", 60, 44)
    ups = ["icon_upgrade_vitality", "icon_upgrade_arcana", "icon_upgrade_engineering", "icon_upgrade_capacity",
           "icon_upgrade_mana_regen"]
    for i, u in enumerate(ups):
        x = 60 + i * 160
        place(p, ui("ui_slot.png"), x, 120, 128, 128)
        place(p, ui(u + ".png"), x + 18, 136, 92, 92)
        place(p, ui("ui_coin.png"), x + 6, 262, 40, 40)
        t = p.text(str(100 * (i + 1)), "Fredoka Bold", 26, "#5a2f14", x + 50, 266)
        nine(p, ui("ui_button.png" if i != 2 else "ui_button_hover.png"), x - 4, 320, 136, 56)
        btn_text(p, "Buy", x - 4, 320, 136, 56, size=22)
    p.save(os.path.join(R.PREVIEW_DIR, "review_shop_mock.png"))
    p.close()


ALL = [fx_sheets, fx_tinted, ui_raw, icon_sheets, logo_sheet, nineslice_sheet, hud_mock, menu_mock, shop_mock]
_only = [s for s in os.environ.get("RW_ONLY", "").split(",") if s]
R.run_all(ALL, only=_only or None, logpath="/tmp/rwui_prev_log.txt")
