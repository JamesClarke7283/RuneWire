"""part_lamp: 0.35 x 0.35 x 0.6 m brass lantern.

Stepped brass base with a rivet ring, four corner posts holding glass panes (M_Glass) with brass
cross-bars, a glowing ember core (M_EmberGlow) on a little brass burner cup, a domed brass roof with
a vented chimney cap and a ring handle on top. Empty "LightPoint" sits at the core centre.
Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, H = 0.35, 0.6
Z0 = -H / 2
parts = []

# --- base -------------------------------------------------------------------------------------------
base = [(0.0, Z0), (0.15, Z0), (0.158, Z0 + 0.008), (0.158, Z0 + 0.03), (0.15, Z0 + 0.038), (0.135, Z0 + 0.045),
        (0.128, Z0 + 0.07), (0.0, Z0 + 0.07)]
parts.append(pl.lathe_axis("base", base, (0, 0, 1), (0, 0, 0), 28, "M_Brass", False, False, 40))
parts += pl.rivet_ring((0, 0, Z0 + 0.02), (0, 0, 1), 0.158, 8, 0.009, 0.005, "M_Brass", 22.5, 6)

# --- cage: corner posts, glass panes, cross bars ---------------------------------------------------------
CZ0, CZ1 = Z0 + 0.07, Z0 + 0.38          # cage height range
P = 0.11                                 # post offset (square cage, posts at the corners)
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(rw.rounded_box("post", (0.04, 0.04, CZ1 - CZ0 + 0.02), 0.012, (sx * P, sy * P, (CZ0 + CZ1) / 2),
                                    mat="M_Brass", segments=2))
for (axis, s) in ((0, -1), (0, 1), (1, -1), (1, 1)):
    if axis == 0:
        size, loc = (0.012, 2 * P - 0.03, CZ1 - CZ0 - 0.01), (s * (P - 0.004), 0, (CZ0 + CZ1) / 2)
        bar = (0.02, 2 * P, 0.022)
    else:
        size, loc = (2 * P - 0.03, 0.012, CZ1 - CZ0 - 0.01), (0, s * (P - 0.004), (CZ0 + CZ1) / 2)
        bar = (2 * P, 0.02, 0.022)
    parts.append(rw.box("pane", size, loc, mat="M_Glass"))
    # a middle cross-bar on each pane
    bl = list(loc)
    bl[axis] = s * (P + 0.002)
    parts.append(rw.rounded_box("crossbar", bar, 0.008, tuple(bl), mat="M_Brass", segments=1))
# top and bottom rails
for z in (CZ0 + 0.01, CZ1 - 0.005):
    parts.append(rw.rounded_box("rail", (2 * P + 0.05, 2 * P + 0.05, 0.03), 0.012, (0, 0, z), mat="M_Brass", segments=2))

# --- burner cup + ember core ------------------------------------------------------------------------------
CORE_Z = (CZ0 + CZ1) / 2 - 0.005
cup = [(0.0, CZ0 + 0.02), (0.05, CZ0 + 0.02), (0.055, CZ0 + 0.04), (0.04, CZ0 + 0.065), (0.05, CORE_Z - 0.045),
       (0.0, CORE_Z - 0.045)]
parts.append(pl.lathe_axis("cup", cup, (0, 0, 1), (0, 0, 0), 16, "M_Brass", False, False, 40))
core = rw.sphere("core", 0.072, 16, 10, (0, 0, CORE_Z), scale=(1, 1, 1.15), mat="M_EmberGlow")
parts.append(core)
# little flame lick on top of the core
parts.append(pl.lathe_axis("flame", [(0.04, CORE_Z + 0.05), (0.028, CORE_Z + 0.085), (0.0, CORE_Z + 0.115)],
                           (0, 0, 1), (0, 0, 0), 12, "M_EmberGlow", False, False, 50))

# --- domed roof, chimney cap, ring handle --------------------------------------------------------------------
RZ = CZ1 + 0.01
roof = [(0.0, RZ), (0.17, RZ), (0.175, RZ + 0.012), (0.152, RZ + 0.03), (0.11, RZ + 0.07), (0.07, RZ + 0.1),
        (0.05, RZ + 0.11), (0.0, RZ + 0.11)]
parts.append(pl.lathe_axis("roof", roof, (0, 0, 1), (0, 0, 0), 28, "M_Brass", False, False, 40))
cap = [(0.0, RZ + 0.105), (0.055, RZ + 0.105), (0.06, RZ + 0.115), (0.06, RZ + 0.13), (0.045, RZ + 0.14),
       (0.0, RZ + 0.14)]
parts.append(pl.lathe_axis("chimney", cap, (0, 0, 1), (0, 0, 0), 16, "M_Brass", False, False, 40))
# ring handle (in the XZ plane so it reads from the front)
ring_r = 0.055
ring_c = V((0, 0, H / 2 - 0.016 - ring_r))
parts.append(rw.torus("handle", ring_r, 0.016, 20, 8, tuple(ring_c), (90, 0, 0), mat="M_Brass"))
parts.append(pl.band("handle_mount", 0.026, 0.03, 0.014, (0, 0, 1), (0, 0, RZ + 0.14), "M_Brass", 12))

lamp = rw.join(parts, "Lamp")
rw.smooth(lamp, 40)
shift = pl.recentre()
rw.set_origin(lamp, (0, 0, 0))
rw.empty("LightPoint", (0.0, 0.0, round(CORE_Z - shift.z, 4)))
pl.check("part_lamp", (W, W, H))
rw.finish("part_lamp", "parts", icon=True)
