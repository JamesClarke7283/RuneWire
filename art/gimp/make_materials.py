"""Build every RuneWire material texture set in GIMP 3 (headless).

    cd /home/james/Projects/RuneWire
    env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
        -b 'exec(open("art/gimp/make_materials.py").read())' --quit

Optional: RW_SETS=grass,stone_bricks (comma list) builds only those sets;
RW_SETS=noise builds the fx utility noise textures.  Default: everything.
Outputs go to assets/textures/<set>/ and previews to art/previews/textures/.
"""
import os
import sys
import time
import traceback
import importlib

_GIMP_DIR = os.path.join(os.environ.get("RW_ROOT") or os.getcwd(), "art", "gimp")
if _GIMP_DIR not in sys.path:
    sys.path.insert(0, _GIMP_DIR)

import rwtex  # noqa: E402
import make_materials_terrain  # noqa: E402
import make_materials_build  # noqa: E402
import make_materials_metal  # noqa: E402
import make_materials_misc  # noqa: E402
import make_materials_noise  # noqa: E402

for _m in (rwtex, make_materials_terrain, make_materials_build, make_materials_metal,
           make_materials_misc, make_materials_noise):
    importlib.reload(_m)

SETS = {}
for _m in (make_materials_terrain, make_materials_build, make_materials_metal, make_materials_misc,
           make_materials_noise):
    SETS.update(_m.SETS)


def main():
    want = [s.strip() for s in os.environ.get("RW_SETS", "all").split(",") if s.strip()]
    names = list(SETS) if want == ["all"] else want
    t0 = time.time()
    failed = []
    for name in names:
        if name not in SETS:
            rwtex.log("unknown set", name)
            failed.append(name)
            continue
        try:
            SETS[name]()
        except Exception:
            traceback.print_exc()
            failed.append(name)
    rwtex.log("built %d set(s) in %.1fs; failed: %s" % (len(names) - len(failed), time.time() - t0,
                                                      ", ".join(failed) or "none"))


main()
