"""Contact sheet of material previews (QA), made in GIMP.

    RW_SETS=grass,dirt,rock RW_KIND=tiled RW_OUT=sheet_terrain \
    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_materials_sheet.py").read())' --quit

RW_KIND: tiled | lit | seam (which preview to use); RW_CELL: cell size in px (default 512);
RW_COLS: columns (default 3).  Writes art/previews/textures/<RW_OUT>.png.
"""
import os
import sys

_GIMP_DIR = os.path.join(os.environ.get("RW_ROOT") or os.getcwd(), "art", "gimp")
if _GIMP_DIR not in sys.path:
    sys.path.insert(0, _GIMP_DIR)
import rwtex as T  # noqa: E402
from rwtex import Gimp, Gio  # noqa: E402


def sheet():
    names = [s.strip() for s in os.environ.get("RW_SETS", "").split(",") if s.strip()]
    kind = os.environ.get("RW_KIND", "tiled")
    cell = int(os.environ.get("RW_CELL", "512"))
    out = os.environ.get("RW_OUT", "sheet")
    cols = min(int(os.environ.get("RW_COLS", "3")), len(names))
    rows = (len(names) + cols - 1) // cols
    img = T.new_image(cols * cell, rows * cell)
    T.layer(img, "bg", fill="#202020", alpha=False)
    for i, n in enumerate(names):
        p = os.path.join(T.PREVIEW_DIR, "%s_%s.png" % (n, kind))
        if not os.path.exists(p):
            T.log("missing", p)
            continue
        src = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(p))
        src.scale(cell, cell)
        L = T.copy_to(src.get_layers()[0], img)
        L.set_offsets((i % cols) * cell, (i // cols) * cell)
        src.delete()
    T.export(img, os.path.join(T.PREVIEW_DIR, out + ".png"))
    img.delete()
    T.log("sheet", out, names)


sheet()
