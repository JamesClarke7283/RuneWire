"""part_thruster: 0.45 x 0.9 x 0.45 m brass steam/jet thruster (long axis Y).

Rounded brass front cap at -Y with a steel nose button and a rivet ring, a brass body wound with a
copper coil between riveted steel collars, a little pressure gauge on top, a bolted mounting saddle
underneath, and a flared steel nozzle bell at +Y with a dark throat and an ember glow deep inside.
Empty "Exhaust" sits at the nozzle exit centre (0, +0.45, 0). Thrust pushes toward -Y (the front).
Origin at the bounding-box centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

L, D = 0.9, 0.45
Y0, Y1 = -L / 2, L / 2
RB = 0.165                     # body radius
AX = (0, 1, 0)                 # lathe axis: profile "height" runs along +Y
parts = []
rw.flat("DialFace", "f6ead0", 0.5, 0.0)
rw.flat("DialNeedle", "d8392b", 0.5, 0.0)
rw.flat("NailHead", "4a4f57", 0.4, 1.0)

# --- brass body: front dome + cylinder + neck --------------------------------------------------------
body_prof = [(0.0, Y0 + 0.012), (0.055, Y0 + 0.018), (0.1, Y0 + 0.04), (0.135, Y0 + 0.07), (0.158, Y0 + 0.11),
             (RB, Y0 + 0.155), (RB, 0.1), (0.15, 0.125), (0.125, 0.15), (0.0, 0.15)]
parts.append(pl.lathe_axis("body", body_prof, AX, (0, 0, 0), 32, "M_Brass", False, False, 40))
# steel nose button
parts.append(pl.lathe_axis("nose", [(0.0, Y0), (0.03, Y0 + 0.004), (0.045, Y0 + 0.016), (0.05, Y0 + 0.03)],
                           AX, (0, 0, 0), 16, "M_Steel", False, True, 60))
parts += pl.rivet_ring((0, Y0 + 0.1, 0), AX, 0.148, 8, 0.011, 0.006, "M_Steel", 22.5, 6)

# --- steel collars with rivets ---------------------------------------------------------------------------
for y in (Y0 + 0.17, 0.085):
    parts.append(pl.band("collar", RB + 0.022, 0.05, 0.03, AX, (0, y, 0), "M_Steel", 28))
    parts += pl.rivet_ring((0, y, 0), AX, RB + 0.022, 6, 0.012, 0.006, "M_Steel", 30, 6)

# --- copper coil wound around the body -----------------------------------------------------------------
c0, c1 = Y0 + 0.21, 0.045
parts.append(pl.helix("coil", RB + 0.018, 0.02, 4.5, c1 - c0, (0, c0, 0), AX, 12, 8, "M_Copper", 0))

# --- flared nozzle bell (steel outside, dark throat inside) + ember glow ----------------------------------
bell_out = [(0.12, 0.12), (0.135, 0.2), (0.16, 0.29), (0.19, 0.37), (0.214, 0.43), (0.225, Y1 - 0.004),
            (0.222, Y1), (0.205, Y1)]
bell_in = [(0.205, Y1), (0.19, Y1 - 0.04), (0.165, 0.34), (0.14, 0.29), (0.125, 0.27), (0.0, 0.265)]
bell = pl.lathe_axis("bell", bell_out + bell_in[1:], AX, (0, 0, 0), 32, "M_Steel", False, False, 40)
# the inner (throat) faces get dark metal
rw.set_mat_where(bell, "M_DarkMetal", lambda c, n: (c.x ** 2 + c.z ** 2) ** 0.5 < 0.2 and n.dot(V((c.x, 0, c.z))) < 0)
parts.append(bell)
parts.append(pl.band("lip", 0.225, 0.028, 0.02, AX, (0, Y1 - 0.016, 0), "M_Brass", 32))
glow = pl.disc("glow", 0.13, 0.02, AX, (0, 0.28, 0), "M_EmberGlow", 24, 0.5)
parts.append(glow)
# glowing burner cone in the throat
parts.append(pl.lathe_axis("glowcone", [(0.1, 0.285), (0.065, 0.33), (0.0, 0.36)], AX, (0, 0, 0), 16,
                           "M_EmberGlow", False, False, 40))

# --- pressure gauge on top --------------------------------------------------------------------------------
gy = Y0 + 0.235
parts.append(rw.cylinder("gauge_stem", 0.014, 0.05, 10, (0, gy, RB + 0.01), mat="M_Brass"))
parts.append(pl.disc("gauge", 0.045, 0.024, (0, 0, 1), (0, gy, D / 2 - 0.016), "M_Brass", 20, 0.4))
parts.append(pl.disc("gauge_face", 0.034, 0.006, (0, 0, 1), (0, gy, D / 2 - 0.0035), "DialFace", 20, 0.2))
parts.append(pl.obox("needle", (0.006, 0.026, 0.004), (0.006, gy - 0.008, D / 2 - 0.001), (1, 0, 0),
                     (0, 0, 1), "DialNeedle"))

# --- mounting saddle underneath ------------------------------------------------------------------------
parts.append(rw.rounded_box("saddle", (0.2, 0.3, 0.05), 0.012, (0, -0.07, -RB - 0.02), mat="M_Steel", segments=2))
for dx in (-0.065, 0.065):
    for dy in (-0.17, 0.03):
        parts.append(pl.bolt((dx, dy, -RB - 0.045), (0, 0, -1), 0.016, 0.01, "M_Steel", washer=False))

thruster = rw.join(parts, "Thruster")
rw.smooth(thruster, 40)
pl.recentre()
rw.set_origin(thruster, (0, 0, 0))
mn, mx = rw.bounds()
rw.empty("Exhaust", (0, mx.y, 0))
pl.check("part_thruster", (D, L, D))
rw.finish("part_thruster", "parts", icon=True)
