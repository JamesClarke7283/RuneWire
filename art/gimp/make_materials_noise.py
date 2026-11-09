"""Utility noise textures for shaders (assets/textures/fx/): 512x512 greyscale, tiling.
noise_perlin (fBm), noise_cells (Worley F1), noise_clouds (soft sky clouds),
noise_streaks (vertical streaks for scrolling fire/energy)."""
import os
import array
import random

from rwtex import *  # noqa: F401,F403

S = 512
FX_DIR = os.path.join(TEX_DIR, "fx")


def _save(name, a):
    data = to_u8(a)
    path = os.path.join(FX_DIR, name + ".png")
    export_bytes(data, S, S, path, "Y' u8", grey=True)
    tiled_preview(data, S, S, os.path.join(PREVIEW_DIR, name + "_tiled.png"), "Y' u8", 1024, grey=True)
    log("  %s: seam %.2f" % (name, seam_score(data, S, S, 1)))


def make_noise():
    t0 = time.time()
    os.makedirs(FX_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    Gimp.context_push()
    rng = random.Random(901)
    log("== fx noise")

    # perlin-style fBm
    a = field_noise(S, 4, 4, detail=5, seed=9011)
    _save("noise_perlin", a)

    # cells: distance to the nearest feature point (Worley F1), wrap-aware
    pts = poisson(S, S, 44, rng)
    img = new_image(S)
    L = layer(img, "m", fill="#ffffff", alpha=False)
    fill_polys(L, [ellipse_pts(x, y, 1.6, 1.6, 0, 8) for x, y in pts], "#000000")
    mask = read(L, "Y' u8")
    img.delete()
    d = distance_field(mask, S, S, 80)
    mx = max(d) or 1.0
    c = field_blur(array.array("f", [min(1.0, v / mx) for v in d]), S, S, 1.2)
    mn, mx = min(c), max(c)
    c = array.array("f", [(v - mn) / (mx - mn) for v in c])
    _save("noise_cells", c)

    # clouds: soft puffs with clear gaps
    b = field_noise(S, 3, 3, detail=4, seed=9012)
    b2 = field_noise(S, 6, 6, detail=3, seed=9014)
    b = array.array("f", [smoothstep(0.22, 0.95, 0.8 * b[i] + 0.2 * b2[i]) ** 1.15 for i in range(S * S)])
    b = field_blur(b, S, S, 3.0)
    mn, mxv = min(b), max(b)
    _save("noise_clouds", array.array("f", [(v - mn) / (mxv - mn) for v in b]))

    # streaks: tall vertical streaks
    img, L = scratch(S)
    noise(L, 16, 2, detail=4, seed=9013)
    normalize(L)
    motion_blur(L, 70, 90)
    normalize(L)
    st = read_f(L)
    img.delete()
    st = array.array("f", [v ** 1.6 for v in st])
    mn, mxv = min(st), max(st)
    _save("noise_streaks", array.array("f", [(v - mn) / (mxv - mn) for v in st]))
    Gimp.context_pop()
    for im in Gimp.get_images():
        im.delete()
    log("  fx noise done in %.1fs" % (time.time() - t0))


SETS = {"noise": make_noise}
