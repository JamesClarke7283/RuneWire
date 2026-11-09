"""part_rotor: motor hub 0.5 x 0.5 x 0.35 m with a 3-blade rotor, blade span diameter 2.4 m.

Nodes:
  Hub     static motor housing at the origin: bolted steel base plate, finned brass motor drum with
          copper windings and a little glowing status window, steel bearing collar.
    Blades  child of Hub; origin on the spin axis (0, 0, BLADE_Z); spins about Z. A brass spinner,
            three pitched wooden blades with brass tip caps and bolted brass root clamps.
The hub is centred on the origin (z -0.175..0.175); the blades turn inside that height range, so the
whole model is 0.35 m tall. Blade tips reach radius 1.2 m.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

HZ = 0.35
Z0, Z1 = -HZ / 2, HZ / 2
TIP_R = 1.2
BLADE_Z = 0.1
PITCH = 14.0
hub_parts, blade_parts = [], []

# --- Hub ---------------------------------------------------------------------------------------------
hub_parts.append(rw.rounded_box("baseplate", (0.5, 0.5, 0.05), 0.016, (0, 0, Z0 + 0.025), mat="M_Steel",
                                segments=2))
for sx in (-1, 1):
    for sy in (-1, 1):
        hub_parts.append(pl.bolt((sx * 0.19, sy * 0.19, Z0 + 0.05), (0, 0, 1), 0.024, 0.014, "M_Steel",
                                 spin=10 * sx * sy))
drum_prof = [(0.17, Z0 + 0.045), (0.2, Z0 + 0.06), (0.2, 0.01), (0.185, 0.03), (0.12, 0.035), (0.0, 0.035)]
hub_parts.append(pl.lathe_axis("drum", drum_prof, (0, 0, 1), (0, 0, 0), 28, "M_Brass", False, False, 40))
for z in (Z0 + 0.085, -0.03):
    hub_parts.append(pl.band("fin", 0.222, 0.026, 0.03, (0, 0, 1), (0, 0, z), "M_Steel", 28))
hub_parts.append(pl.band("winding", 0.208, 0.05, 0.016, (0, 0, 1), (0, 0, Z0 + 0.135), "M_Copper", 28, 0.5))
hub_parts += pl.rivet_ring((0, 0, -0.03), (0, 0, 1), 0.222, 6, 0.012, 0.006, "M_Steel", 0, 6)
# glowing status window on the front of the drum
win = pl.disc("window", 0.03, 0.02, (0, -1, 0), (0, -0.2, Z0 + 0.135), "M_TechGlow", 12, 0.4)
hub_parts.append(win)
hub_parts.append(pl.band("window_rim", 0.04, 0.018, 0.012, (0, -1, 0), (0, -0.205, Z0 + 0.135), "M_Brass", 12))
# bearing collar + shaft
hub_parts.append(pl.lathe_axis("collar", [(0.13, 0.03), (0.13, 0.05), (0.11, 0.065), (0.05, 0.065), (0.05, 0.08),
                                          (0.0, 0.08)], (0, 0, 1), (0, 0, 0), 24, "M_Steel", False, False, 40))
hub = rw.join(hub_parts, "Hub", origin=(0, 0, 0))
rw.smooth(hub, 40)

# --- Blades ------------------------------------------------------------------------------------------
# spinner: brass hub disc + dome cap
blade_parts.append(pl.lathe_axis("spinner", [(0.14, BLADE_Z - 0.03), (0.15, BLADE_Z - 0.012), (0.15, BLADE_Z + 0.02),
                                             (0.13, BLADE_Z + 0.035), (0.1, BLADE_Z + 0.05), (0.06, Z1 - 0.012),
                                             (0.025, Z1 - 0.002), (0.0, Z1)], (0, 0, 1), (0, 0, 0), 24, "M_Brass",
                                 True, False, 45))
blade_parts += pl.rivet_ring((0, 0, BLADE_Z + 0.0), (0, 0, 1), 0.15, 6, 0.012, 0.006, "M_Steel", 0, 6)


def blade(angle_deg):
    """One pitched blade along +Y, then rotated to angle_deg about Z."""
    out = []
    tip_r = 0.115                         # chord half-width at the tip
    end_y = TIP_R - tip_r                 # hemispherical tip cap reaches TIP_R
    pts = [(0, 0.12, 0), (0, 0.3, 0), (0, 0.62, 0), (0, 0.9, 0), (0, end_y, 0)]
    rad = [0.06, 0.115, 0.135, 0.13, tip_r]
    wood = pl.sausage("blade", pts, rad, 12, 2, "M_WoodPlanks", (False, True), 3, True, 50,
                      scale_xy=(0.2, 1.0), up_hint=(0, 0, 1))
    # brass tip cap: same section, slightly fatter, over the outer end
    tip_pts = [(0, 0.98, 0), (0, end_y, 0)]
    tip = pl.sausage("tip", tip_pts, [0.128, tip_r + 0.006], 12, 1, "M_Brass", (False, True), 3, False, 50,
                     scale_xy=(0.24, 1.0), up_hint=(0, 0, 1))
    pl.xform(tip, pl.Matrix.Translation((0, (TIP_R - (end_y + tip_r + 0.006)), 0)))
    # root clamp
    clamp = rw.rounded_box("clamp", (0.17, 0.13, 0.075), 0.02, (0, 0.17, 0), mat="M_Brass", segments=2)
    bolts = [pl.bolt((dx, 0.17, 0.037), (0, 0, 1), 0.017, 0.01, "M_Steel", washer=False) for dx in (-0.04, 0.04)]
    for o in [wood, tip, clamp] + bolts:
        rw.apply_modifiers(o)
        M = pl.Matrix.Translation((0, 0, BLADE_Z)) @ pl.Matrix.Rotation(math.radians(angle_deg), 4, 'Z') @ \
            pl.Matrix.Rotation(math.radians(PITCH), 4, 'Y')
        if o in (clamp,) or o in bolts:
            M = pl.Matrix.Translation((0, 0, BLADE_Z)) @ pl.Matrix.Rotation(math.radians(angle_deg), 4, 'Z')
        mw = o.matrix_world.copy()
        o.matrix_world = pl.Matrix.Identity(4)
        o.data.transform(M @ mw)
        o.data.update()
        out.append(o)
    return out


for k in range(3):
    blade_parts += blade(180 + 120 * k)      # R_z(180) maps +Y to -Y: first blade points to the front

blades = rw.join(blade_parts, "Blades", origin=(0, 0, BLADE_Z))
rw.smooth(blades, 40)
rw.set_parent(blades, hub)

pl.check("part_rotor", (0, 0, HZ))
mn, mx = rw.bounds([blades])
print("RWREPORT   blade tip radius max %.3f" % max(abs(mn.x), abs(mx.x), abs(mn.y), abs(mx.y)))
rw.finish("part_rotor", "parts", icon=True)
