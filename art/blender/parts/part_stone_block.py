"""part_stone_block: 1 x 1 x 1 m chiselled stone block.

A soft-edged M_Stone cube with planar chisel chips knocked off a few edges and corners, a hairline
crack on one side, and a carved rune circle on the front face (-Y): deep grooves with a faint
M_RuneGlow inlay sitting at the bottom of the grooves. Origin at the bounding-box centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
rw.reset()

S = 1.0
H = S / 2

# --- base: subdivided cube with gentle large-scale unevenness (front face kept flat for the carving) ----
import bmesh  # noqa: E402
from mathutils import noise  # noqa: E402

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=S)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
for v in bm.verts:
    n = noise.noise_vector(v.co * 1.7 + V((3.1, 7.3, 1.7)))
    d = n * 0.02
    if v.co.y < -H + 1e-4:
        d.y = 0.0               # the carved front face stays flat
    v.co += d
block = pl.obj_from_bm("Block", bm, "M_Stone", 0)
bev = rw.add_bevel(block, 0.045, 2, 40, harden=False)
rw.apply_modifiers(block)

# --- chisel chips: rotated boxes biting planar facets out of edges/corners ------------------------------
cutters = []
# (point on the block surface, outward normal of the cut plane, depth). Corner chips cut a triangle off a
# corner; edge chips are tilted along the edge so they taper out instead of running the full length.
CHIPS = (
    ((H, -H, H), (1, -1, 1.2), 0.15),          # top front right corner
    ((-H, H, H), (-1, 1, 0.9), 0.13),          # top back left corner
    ((H, H, -H), (1, 1.1, -0.8), 0.11),        # bottom back right corner
    ((-H, -H, -H), (-1, -0.8, -1), 0.1),       # bottom front left corner
    ((-H, -H, 0.15), (-1, -1, 0.3), 0.085),    # front-left vertical edge (tapers out along the edge)
    ((0.2, H, H), (0.3, 1, 1), 0.08),          # top back edge
    ((H, -0.1, -H), (1, -0.45, -1), 0.08),     # bottom right edge, front part
)
for (p, n, depth) in CHIPS:
    if depth <= 0:
        continue
    n = V(n).normalized()
    c = V(p) - n * depth           # plane passes `depth` inside the given point
    cut = pl.obox("chip", (2.0, 2.0, 1.0), c + n * 0.5, n.orthogonal(), n)
    cutters.append(cut)
pl.carve(block, cutters)

# --- hairline crack on the +X side (jagged groove) ---------------------------------------------------
crack = [(H, -0.36, 0.42), (H, -0.25, 0.28), (H, -0.29, 0.14), (H, -0.16, 0.02), (H, -0.2, -0.12),
         (H, -0.06, -0.22)]
crack_c = pl.sausage("crack", crack, [0.006, 0.011, 0.013, 0.012, 0.01, 0.005], 6, 1, None, (True, True), 2,
                     False, 0)
crack2 = [(H, -0.16, 0.02), (H, -0.03, 0.08), (H, 0.06, 0.03)]
crack_c2 = pl.sausage("crack", crack2, [0.011, 0.008, 0.004], 6, 1, None, (True, True), 2, False, 0)
pl.carve(block, [crack_c, crack_c2])

# --- rune circle on the front face: carve grooves, then lay a faint glow at the groove bottom -----------
FRONT = -H
RR = 0.3                 # ring radius
GW = 0.034               # groove width
GD = 0.03                # groove depth
cut_parts = [pl.lathe_axis("ring_cut", [(RR - GW / 2, -GD), (RR + GW / 2, -GD), (RR + GW / 2, GD),
                                        (RR - GW / 2, GD), (RR - GW / 2, -GD)], (0, -1, 0), (0, FRONT, 0), 48,
                           None, False, False, 0)]
cut_parts += pl.glyph_cutters("algiz", (0, FRONT, -0.01), (1, 0, 0), (0, 0, 1), 0.36, GW, GD * 2)
# small tick marks around the ring
for k in range(4):
    a = math.radians(45 + 90 * k)
    c = V((math.cos(a) * (RR + 0.075), FRONT, math.sin(a) * (RR + 0.075)))
    cut_parts.append(pl.obox("tick", (0.05, GW * 0.85, GD * 2), c, (math.cos(a), 0, math.sin(a)), (0, -1, 0)))
pl.carve(block, cut_parts)

inlay = []
inlay.append(pl.lathe_axis("ring_glow", [(RR - GW / 2 + 0.006, -0.004), (RR + GW / 2 - 0.006, -0.004),
                                         (RR + GW / 2 - 0.006, 0.004), (RR - GW / 2 + 0.006, 0.004),
                                         (RR - GW / 2 + 0.006, -0.004)], (0, -1, 0),
                           (0, FRONT + GD - 0.006, 0), 48, "M_RuneGlow", False, False, 0))
inlay += pl.glyph("algiz", (0, FRONT + GD - 0.006, -0.01), (1, 0, 0), (0, 0, 1), 0.36, GW - 0.012, 0.008,
                  "M_RuneGlow")
for k in range(4):
    a = math.radians(45 + 90 * k)
    c = V((math.cos(a) * (RR + 0.075), FRONT + GD - 0.006, math.sin(a) * (RR + 0.075)))
    inlay.append(pl.obox("tick_glow", (0.04, GW * 0.85 - 0.012, 0.008), c, (math.cos(a), 0, math.sin(a)),
                         (0, -1, 0), "M_RuneGlow"))

stone = rw.join([block] + inlay, "StoneBlock")
rw.smooth(stone, 30)
pl.recentre()
pl.fit_scale([stone], (S, S, S))
pl.recentre()
rw.set_origin(stone, (0, 0, 0))
pl.check("part_stone_block", (S, S, S))
rw.finish("part_stone_block", "parts", icon=True)
