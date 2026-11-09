"""item_focus_gem: a big cut focus gem in a brass claw setting with a ring loop, about 0.14 x 0.13 x 0.2 m.

A chunky round brilliant-cut gem (M_Crystal tinted rosy magenta, with hand-painted facets in a lighter and a darker
tint of the same crystal: an octagonal table, star facets on the crown and a deep pointed pavilion) facing the
viewer and tilted up a little, cradled in a brass cup with six curled claws gripping its girdle, and a brass bail
with a ring loop on top. The tint keeps it apart from the many teal + brass items (ley lens, power cell, arcane
thread). One mesh object "FocusGem", origin at the centre.
"""
import math
import os
import sys

import bmesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_focus_gem"
rw.reset()

CRY, CRY_HI, CRY_LO = "M_Crystal__ff4fc8", "M_Crystal__ffa8ec", "M_Crystal__b8168c"
# preview/icon only: Godot tints its own crystal set (and its glow follows each tint)
il.preview_glow(CRY, "e83aae", "ff4fc8", 0.22)
il.preview_glow(CRY_HI, "ffa0e8", "ffb8f0", 0.22)
il.preview_glow(CRY_LO, "a0127a", "d0309e", 0.22)
BR = ml.mat("M_Brass")
A = V((0.0, -1.0, 0.4)).normalized()                 # the gem faces this way (front, tilted up)
R = pl.frame_matrix(A)                               # gem-local frame: local Z = A
C = V((0, 0, 0))
RG = 0.062                                           # girdle radius


def gpt(r, ang_deg, h):
    """Gem-local point: radius r at angle ang (degrees) round A, height h along A."""
    a = math.radians(ang_deg)
    return C + R @ V((r * math.cos(a), r * math.sin(a), h))


# --- the gem: table, star facets, crown, girdle, pavilion (flat facets) ---------------------------------------
bm = bmesh.new()
N = 8
table = [bm.verts.new(gpt(0.03, 45 * i, 0.044)) for i in range(N)]
star = [bm.verts.new(gpt(0.049, 45 * i + 22.5, 0.029)) for i in range(N)]
gird_t = [bm.verts.new(gpt(RG, 22.5 * i, 0.004)) for i in range(2 * N)]
gird_b = [bm.verts.new(gpt(RG, 22.5 * i, -0.004)) for i in range(2 * N)]
mid = [bm.verts.new(gpt(0.034, 45 * i + 22.5, -0.04)) for i in range(N)]
culet = bm.verts.new(gpt(0.0, 0, -0.072))
bm.faces.new(table)
for i in range(N):
    j = (i + 1) % N
    # star facet between two table corners and the star point
    bm.faces.new((table[i], star[i], table[j]))
    # kite facets from each table corner down to the girdle
    bm.faces.new((table[j], star[i], gird_t[2 * i + 1], gird_t[(2 * i + 2) % (2 * N)], star[j]))
    # upper-girdle facets
    bm.faces.new((star[i], gird_t[2 * i], gird_t[2 * i + 1]))
for k in range(2 * N):
    kk = (k + 1) % (2 * N)
    bm.faces.new((gird_t[k], gird_b[k], gird_b[kk], gird_t[kk]))
for i in range(N):
    j = (i + 1) % N
    bm.faces.new((gird_b[(2 * i + 1)], gird_b[2 * i], mid[i]))
    bm.faces.new((gird_b[(2 * i + 2) % (2 * N)], gird_b[2 * i + 1], mid[i]))
    bm.faces.new((gird_b[(2 * i + 2) % (2 * N)], mid[i], mid[j]))
    bm.faces.new((mid[j], mid[i], culet))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
gem = pl.obj_from_bm("gem", bm, rw._resolve_mat(CRY), 0)
rw.flat_shade(gem)
# hand-painted facets: light table and star facets, darker upper-girdle facets and girdle (faces in creation order)
hi = [0] + [1 + 3 * i for i in range(N)]
lo = [3 + 3 * i for i in range(N)] + list(range(1 + 3 * N, 1 + 3 * N + 2 * N))
rw.set_mat(gem, rw._resolve_mat(CRY_HI), hi)
rw.set_mat(gem, rw._resolve_mat(CRY_LO), lo)
parts = [gem]

# --- brass setting: a cup behind the pavilion, six claws over the girdle, a bail and a ring loop -----------------
cup = [(0.0, -0.064), (0.028, -0.066), (0.052, -0.044), (0.066, -0.016), (0.068, -0.006), (0.063, -0.004),
       (0.05, -0.02), (0.03, -0.045), (0.0, -0.05)]
parts.append(il.lathe("cup", cup, A, C, 20, BR, 40))
for k in range(6):
    ang = 30 + 60 * k
    claw = [gpt(0.068, ang, -0.018), gpt(0.071, ang, -0.002), gpt(0.066, ang, 0.012), gpt(0.055, ang, 0.024)]
    parts.append(pl.sausage("claw", claw, [0.0082, 0.0078, 0.0068, 0.0054], 8, 2, BR, (True, True), 2, True, 60))
up = (V((0, 0, 1)) - V((0, 0, 1)).dot(A) * A).normalized()   # 'up' on the gem plane
top = C + up * 0.072 - A * 0.02
parts.append(rw.sphere("bail", 0.016, 12, 8, tuple(top), mat=BR))
parts.append(rw.torus("loop", 0.024, 0.0075, 18, 8, tuple(top + V((0, 0, 0.032))), (90, 0, 90), BR))

gem_o = rw.join(parts, "FocusGem")
ml.preview_metals()
il.finish_item(ASSET, (0.14, 0.13, 0.2))
