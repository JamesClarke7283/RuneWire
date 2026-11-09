"""item_swift_elixir: "Swiftfoot Elixir", a slim glowing teal-green flask with brass wings, ~0.3 m tall.

A slim round-shouldered vial of glowing teal-green elixir (glass M_Glass above the fill line), a brass
collar round its waist carrying a pair of little three-feather brass wings swept back on its sides, a
yellow lightning bolt on the front, a brass neck band, a cork and white glints.
One mesh object "SwiftElixir", origin at the centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

rw, pl, V = il.rw, il.pl, il.V
ASSET = "item_swift_elixir"
rw.reset()

body = [(0.0, 0.0), (0.036, 0.0), (0.047, 0.012), (0.051, 0.045), (0.051, 0.148), (0.046, 0.178), (0.033, 0.198),
        (0.026, 0.214), (0.026, 0.232)]
lip = [(0.033, 0.236), (0.035, 0.245), (0.03, 0.25), (0.0, 0.25)]
b = il.Bottle(body, lip, fill=0.168, liquid="SwiftGreen", top="SwiftGreenTop", segs=24)
b.parts.append(il.wrap_prism("bolt", il.bolt_pts(0.062), b.map(-14, 0.062, 0.0012, 0.004), "StarYellow"))
b.shine(-62, 0.075, 0.012, 0.06)
b.shine(-58, 0.14, 0.01, 0.016)

parts = list(b.parts)
WZ = 0.118                                       # waist collar / wing root height
parts.append(pl.band("collar", 0.059, 0.026, 0.014, (0, 0, 1), (0, 0, WZ), il.mat("M_Brass"), 20, 0.0))
parts.append(pl.band("band", 0.034, 0.018, 0.012, (0, 0, 1), (0, 0, 0.206), il.mat("M_Brass"), 16, 0.0))
parts.append(il.cork(0.222, 0.3, 0.023, 0.033, 16))

# wings: three chunky rounded feathers fanning up and out, swept 12 deg back, flat in their plane
FEATHERS = (([(0.0, 0.016), (0.036, 0.064), (0.062, 0.114)], (0.018, 0.021, 0.01)),
            ([(0.0, 0.006), (0.05, 0.04), (0.092, 0.07)], (0.018, 0.021, 0.01)),
            ([(0.0, -0.006), (0.05, 0.008), (0.09, 0.02)], (0.017, 0.019, 0.009)))
for side in (-1, 1):
    sweep = math.radians(12)
    out = V((side * math.cos(sweep), math.sin(sweep), 0))
    up = V((0, 0, 1))
    nrm = out.cross(up).normalized()
    root = V((side * 0.057, 0.008, WZ + 0.004))
    for k, (pts2, radii) in enumerate(FEATHERS):
        pts = [root + out * a + up * c for (a, c) in pts2]
        parts.append(pl.sausage("feather", pts, list(radii), 6, 3, il.mat("M_Brass"), (True, True), 2, True, 60,
                                (0.34, 1.0), tuple(nrm)))
    parts.append(rw.sphere("wing_root", 0.022, 10, 6, tuple(root), scale=(1, 0.8, 1), mat="M_Brass"))

elixir = rw.join(parts, "SwiftElixir")
il.finish_item(ASSET, (0.3, 0.13, 0.3))
