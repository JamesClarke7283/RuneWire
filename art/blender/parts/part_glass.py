"""part_glass: 2.0 x 0.08 x 2.0 m upright glass panel (thin axis Y).

A clear M_Glass pane held by inner brass beads inside a chunky brass frame (0.08 thick including the
rivet heads), riveted rails, corner caps with big dome rivets, and cartoon shine streaks on both
faces of the glass. Origin at the bounding-box centre.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
rw.reset()

S, T = 2.0, 0.08
FW = 0.11                 # frame face width
FD = 0.068                # frame depth (Y); rivet heads bring it to 0.08
CAP = 0.19
parts = []
rw.flat("NailHead", "4a4f57", 0.4, 1.0)
shine = rw.material("GlassShine", "f4fbff", 0.1, 0.0, None, 0.0, 0.6)

# --- frame rails + corner caps ----------------------------------------------------------------------
for s in (-1, 1):
    parts.append(rw.rounded_box("rail", (S - 0.1, FD, FW), 0.022, (0, 0, s * (S / 2 - FW / 2)), mat="M_Brass",
                                segments=2))
    parts.append(rw.rounded_box("rail", (FW, FD, S - 0.1), 0.022, (s * (S / 2 - FW / 2), 0, 0), mat="M_Brass",
                                segments=2))
for sx in (-1, 1):
    for sz in (-1, 1):
        c = (sx * (S / 2 - CAP / 2), 0, sz * (S / 2 - CAP / 2))
        parts.append(rw.rounded_box("cap", (CAP, FD + 0.006, CAP), 0.03, c, mat="M_Brass", segments=2))
        for sy in (-1, 1):
            parts.append(pl.rivet((c[0], sy * (FD / 2 + 0.003), c[2]), (0, sy, 0), 0.032, T / 2 - FD / 2 - 0.003,
                                  "NailHead", 12))

# --- rivets along the rails (both faces) -------------------------------------------------------------
RH = T / 2 - FD / 2
E = S / 2 - FW / 2
for sy in (-1, 1):
    for i in range(4):
        t = -0.51 + 0.34 * i
        for (x, z) in ((t, -E), (t, E), (-E, t), (E, t)):
            parts.append(pl.rivet((x, sy * FD / 2, z), (0, sy, 0), 0.025, RH, "NailHead", 10))

# --- glass pane + inner beads ------------------------------------------------------------------------
inner = S - 2 * FW
glass = rw.box("pane", (inner + 0.04, 0.022, inner + 0.04), mat="M_Glass")
parts.append(glass)
for sy in (-1, 1):
    y = sy * 0.02
    for s in (-1, 1):
        parts.append(rw.rounded_box("bead", (inner + 0.02, 0.018, 0.03), 0.008, (0, y, s * (inner / 2 - 0.004)),
                                    mat="M_Brass", segments=1))
        parts.append(rw.rounded_box("bead", (0.03, 0.018, inner + 0.02), 0.008, (s * (inner / 2 - 0.004), y, 0),
                                    mat="M_Brass", segments=1))

# --- cartoon shine streaks, painted flush into both pane faces ---------------------------------------
# The pane is sliced with bisect planes so the streaks are coplanar faces with the GlassShine material
# (no raised geometry, so no outline around them).
import bmesh  # noqa: E402

STREAKS = []
for sy in (-1, 1):
    # same world position on both faces: the pane is see-through, so they overlap from either side
    d = pl.V((0.7071, 0, 0.7071))
    perp = pl.V((-0.7071, 0, 0.7071))
    for (off, w, L) in ((-0.1, 0.11, 1.0), (0.13, 0.05, 0.75), (0.32, 0.035, 0.45)):
        c = perp * (0.255 + off)
        STREAKS.append((sy, c, d, perp, L / 2, w / 2))

bm = bmesh.new()
bm.from_mesh(glass.data)
for (sy, c, d, perp, hl, hw) in STREAKS:
    if sy > 0:
        continue        # identical planes for the back face: cut each plane only once
    for (co, no) in ((c + perp * hw, perp), (c - perp * hw, perp), (c + d * hl, d), (c - d * hl, d)):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(glass.data)
bm.free()
rw.set_mat(glass, shine, [])        # add the slot
glass.data.update()
shine_idx = [i for i, m in enumerate(glass.data.materials) if m and m.name == "GlassShine"][0]
for f in glass.data.polygons:
    if abs(f.normal.y) < 0.99:
        continue
    fc = pl.V(f.center)
    for (sy, c, d, perp, hl, hw) in STREAKS:
        if f.normal.y * sy > 0:
            rel = fc - pl.V((c.x, fc.y, c.z))
            if abs(rel.dot(d)) < hl - 1e-4 and abs(rel.dot(perp)) < hw - 1e-4:
                f.material_index = shine_idx

panel = rw.join(parts, "Glass")
rw.smooth(panel, 35)
pl.recentre()
rw.set_origin(panel, (0, 0, 0))
pl.check("part_glass", (S, T, S))
rw.finish("part_glass", "parts", icon=True)
