"""part_hover_stone: 0.8 x 0.8 x 0.6 m levitation rune stone.

A chunky carved octagonal stone (M_Stone) shaped like a little floating island: a flat top for
mounting, faceted sides that lean in toward a tapered underside, and a glowing violet levitation
crystal under the tip. Deep rune grooves are carved into the eight upper side faces with a glowing
M_RuneGlow inlay at the bottom of each groove. A riveted brass band wraps the top edge and a second
band hugs the taper; three little pebbles float around the underside. Origin at the bounding-box centre.
"""
import math
import os
import sys

import bmesh
from mathutils import noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

W, H = 0.8, 0.6
C8 = math.cos(math.radians(22.5))
SPIN = 22.5                       # put the octagon's flats on the +-X / +-Y axes


def oct_r(apothem):
    return apothem / C8


def lathe8(name, prof_apothem, mat, cap_b=False, cap_t=False):
    prof = [(oct_r(a), z) for (a, z) in prof_apothem]
    return pl.lathe_axis(name, prof, (0, 0, 1), (0, 0, 0), 8, mat, cap_b, cap_t, 30, SPIN)


TOP = 0.3
A_TOP = 0.379                     # apothem at the top edge (band + rivets add 0.021 -> 0.4 half-width)
# side faces: from (A_TOP, 0.245) leaning in to (A_MID, 0.03), then the taper
A_MID = 0.315
body_prof = [(0.0, TOP), (A_TOP - 0.032, TOP), (A_TOP, TOP - 0.045), (A_TOP, 0.245), (A_MID, 0.03),
             (0.24, -0.08), (0.14, -0.17), (0.07, -0.215), (0.0, -0.225)]
stone = lathe8("stone", body_prof, "M_Stone")
bm = bmesh.new()
bm.from_mesh(stone.data)
bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.06],
                          cuts=2, use_grid_fill=False)
for v in bm.verts:
    if v.co.z > TOP - 0.05:
        continue                  # keep the mounting top and its chamfer clean
    n = noise.noise_vector(v.co * 3.1 + V((2.3, 5.1, 7.7)))
    v.co += V((n.x * 0.02, n.y * 0.02, n.z * 0.01))
bm.to_mesh(stone.data)
bm.free()

# --- deep rune grooves on the eight upper side faces --------------------------------------------------------
KEYS = ("algiz", "sowilo", "ingwaz", "tiwaz", "dagaz", "fehu", "othala", "kenaz")
RS = 0.15                         # rune size
GW = 0.03                         # groove width
GD = 0.028                        # groove depth
z_lo, z_hi = 0.03, 0.245
faces = []
for i in range(8):
    ang = math.radians(-90 + 45 * i)              # i = 0 is the front face (-Y)
    n_h = V((math.cos(ang), math.sin(ang), 0))
    u = V((-math.sin(ang), math.cos(ang), 0))     # along the face, horizontal
    p_lo = n_h * A_MID + V((0, 0, z_lo))
    p_hi = n_h * A_TOP + V((0, 0, z_hi))
    v = (p_hi - p_lo).normalized()                # up along the leaning face
    nrm = u.cross(v).normalized()
    if nrm.dot(n_h) < 0:
        u = -u
        nrm = -nrm
    c = (p_lo + p_hi) / 2
    faces.append((c, u, v, nrm, KEYS[i]))
cutters = []
for (c, u, v, nrm, key) in faces:
    cutters += pl.glyph_cutters(key, c, u, v, RS, GW, GD * 2)
pl.carve(stone, cutters)
parts = [stone]
for (c, u, v, nrm, key) in faces:
    parts += pl.glyph(key, c - nrm * (GD - 0.006), u, v, RS, GW - 0.008, 0.01, "M_RuneGlow")

# --- brass bands with rivets ---------------------------------------------------------------------------
bz0, bz1 = 0.245, TOP - 0.045
parts.append(lathe8("band_top", [(A_TOP - 0.006, bz0 - 0.004), (A_TOP + 0.012, bz0 - 0.004),
                                 (A_TOP + 0.016, bz0 + 0.002), (A_TOP + 0.016, bz1 + 0.006),
                                 (A_TOP + 0.012, bz1 + 0.012), (A_TOP - 0.03, bz1 + 0.012),
                                 (A_TOP - 0.006, bz0 - 0.004)], "M_Brass"))
for i in range(8):
    ang = math.radians(-90 + 45 * i)
    n = V((math.cos(ang), math.sin(ang), 0))
    u = V((-math.sin(ang), math.cos(ang), 0))
    for k in (-1, 1):
        parts.append(pl.rivet(n * (A_TOP + 0.016) + u * (k * 0.1) + V((0, 0, (bz0 + bz1) / 2 + 0.004)), n, 0.011,
                              0.005, "M_Brass", 6))


def apothem_at(z):
    prof = body_prof[3:]
    for (a0, z0), (a1, z1) in zip(prof[:-1], prof[1:]):
        if z1 <= z <= z0:
            t = (z0 - z) / (z0 - z1)
            return a0 + (a1 - a0) * t
    return 0.0


t0, t1 = -0.07, -0.025
a0, a1 = apothem_at(t0), apothem_at(t1)
parts.append(lathe8("band_low", [(a0 - 0.012, t0), (a0 + 0.012, t0), (a0 + 0.017, t0 + 0.006),
                                 (a1 + 0.017, t1 - 0.006), (a1 + 0.012, t1), (a1 - 0.012, t1),
                                 (a0 - 0.012, t0)], "M_Brass"))

# --- glowing levitation crystal under the tip -----------------------------------------------------------
BOT = -H / 2
parts.append(pl.crystal("tip", (0, 0, BOT), (0, 0, 1), 0.12, 0.065, 6, 0.55, 0.1, "M_RuneGlow"))
parts.append(lathe8("tip_collar", [(0.0, -0.215), (0.09, -0.215), (0.1, -0.205), (0.1, -0.185), (0.08, -0.17)],
                    "M_Brass"))

# --- three little floating pebbles around the underside --------------------------------------------------
for i, (ang, z, s) in enumerate(((-65, -0.15, 0.075), (55, -0.19, 0.065), (175, -0.13, 0.07))):
    a = math.radians(ang)
    p = V((math.cos(a) * 0.3, math.sin(a) * 0.3, z))
    parts.append(rw.ico("pebble", s, 1, tuple(p), (17 * i, 31 * i, 11 * i), (1.0, 0.85, 0.7), mat="M_Stone",
                        smooth_angle=0))
    parts += pl.glyph("tiwaz" if i % 2 else "kenaz", p + V((math.cos(a), math.sin(a), 0)) * (s * 0.45),
                      V((-math.sin(a), math.cos(a), 0)), (0, 0, 1), s * 0.7, 0.012, 0.012, "M_RuneGlow")

hover = rw.join(parts, "HoverStone")
rw.smooth(hover, 30)
pl.recentre()
rw.set_origin(hover, (0, 0, 0))
pl.check("part_hover_stone", (W, W, H))
rw.finish("part_hover_stone", "parts", icon=True)
