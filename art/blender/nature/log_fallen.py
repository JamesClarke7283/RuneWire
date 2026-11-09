"""log_fallen: a fallen mossy log, about 4.2 x 1.1 x 0.85 m above the game's ground line (z = 0.15).

A chunky, gently bent and lumpy log (M_Bark) lies along X. The root end (-X) flares out and shows a sawn face of
pale end grain (EndGrain) with two stepped growth rings, ringed by four fat roots: two short broken stubs with
end-grain tips and two that arch down into the ground. The other end (+X) is hollow: a rim of end grain around a
dark bark-lined hole. Two broken branch stubs (end-grain tips) stick up, and a long moss blanket (Moss) drapes
over the top, with a second patch near the root end. The bark gets cylindrical UVs so its ridges run along the
log (rwlib's box projection would wrap them around it).

The game sinks every instance 0.15 m, so the log rests on that ground line with its belly 5 cm in, and a hidden
bark skirt under its whole length reaches down to z = -0.75: a log lying across a slope never shows daylight
under it. ONE mesh object, three materials, origin at the base centre. Collision: none in the model (the game
adds a 0.5 m sphere at its middle).
"""
import math
import os
import sys

import bmesh
from mathutils import noise

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scatterlib as sl  # noqa: E402

rw, nl = sl.rw, sl.nl
V = sl.V
ASSET = "log_fallen"
rw.reset()
GL = sl.SINK
bark = rw._resolve_mat("M_Bark")
grain = rw.flat(*sl.END_GRAIN, 0.9)
moss_m = rw.flat(*sl.MOSS, 0.95)

SIDES = 12
ZC = GL + 0.32                                     # axis height: the belly sits ~5 cm under the ground line
PATH = [(-1.9, 0.0, ZC + 0.03), (-0.95, 0.08, ZC), (0.05, 0.03, ZC - 0.01), (1.05, -0.07, ZC + 0.01),
        (1.98, -0.03, ZC + 0.03)]
RADII = [0.39, 0.375, 0.365, 0.35, 0.34]


def log_shape(u, p, d, r):
    """Lumpy bark and a widening root end (u = 0)."""
    rr = r * (1.0 + 0.05 * noise.noise(p * 1.3 + d * 0.7 + V((3.1, 1.7, 0.4))))
    if u < 0.16:
        t = 1.0 - u / 0.16
        rr *= 1.0 + 0.2 * t * t
    return rr


# --- the log body with its two worked ends -------------------------------------------------------------------------
bm = bmesh.new()
rings, _ = nl.sweep_bm(bm, PATH, RADII, sides=SIDES, per_seg=3, cap_start=True, cap_end=True, shaper=log_shape,
                       phase=math.radians(-90), up_hint=(0, 0, 1))
sl.uv_rings(bm, rings, 2.0)
caps = [f for f in bm.faces if len(f.verts) == SIDES]
root_cap = min(caps, key=lambda f: f.calc_center_median().x)
tip_cap = max(caps, key=lambda f: f.calc_center_median().x)
GRAIN_I, BARK_I = 1, 0                              # material slots: 0 bark, 1 end grain
end_faces = [root_cap, tip_cap]
# root end: two stepped growth rings (a riser drops 2 cm, then a flat band)
for (t, dep) in ((0.0, -0.022), (0.075, 0.0), (0.0, -0.02), (0.07, 0.0)):
    res = bmesh.ops.inset_region(bm, faces=[root_cap], thickness=t, depth=dep, use_even_offset=True)
    end_faces += res["faces"]
# hollow end: a rim of end grain, then a deep bark-lined hole
res = bmesh.ops.inset_region(bm, faces=[tip_cap], thickness=0.075, depth=0.0, use_even_offset=True)
end_faces += res["faces"]
res = bmesh.ops.inset_region(bm, faces=[tip_cap], thickness=0.0, depth=-0.42, use_even_offset=True)
hole_faces = res["faces"] + [tip_cap]
for f in bm.faces:
    f.material_index = BARK_I
for f in end_faces:
    f.material_index = GRAIN_I
for f in hole_faces:
    f.material_index = BARK_I
body = nl.obj_from_bm("body", bm, None)
body.data.materials.append(bark)
body.data.materials.append(grain)
nl.shade_smooth_all(body)
for p in body.data.polygons:
    if p.material_index == GRAIN_I:
        p.use_smooth = False
parts = [body]
bvh = sl.bvh_of(body)


# --- four fat roots around the flared end: the upper two are short broken stubs (end-grain tips), the lower two
# arch out and dive into the ground just past the end ----------------------------------------------------------------
for k, (theta, rad, down, broken) in enumerate(((38, 0.14, 0.0, True), (150, 0.13, 0.0, True),
                                                (232, 0.16, 0.3, False), (308, 0.15, 0.28, False))):
    a = math.radians(theta)
    out = V((0.0, math.cos(a), math.sin(a)))
    c = lambda x: V((x, 0.0, ZC))                  # noqa: E731
    if broken:
        pts = [c(-1.45) + out * 0.12, c(-1.85) + out * 0.42, c(-2.05) + out * 0.56]
        radii = [rad, rad * 0.95, rad * 0.85]
    else:
        pts = [c(-1.5) + out * 0.12, c(-1.88) + out * 0.42, c(-2.08) + out * 0.52 - V((0, 0, 0.03)),
               c(-2.2) + out * 0.56 - V((0, 0, down))]
        radii = [rad, rad * 0.95, rad * 0.75, rad * 0.5]
    root = sl.tube("root%d" % k, pts, radii, sides=7, per_seg=1, mat=bark, cap_start=True, cap_end=True)
    if broken:
        root.data.materials.append(grain)
        tipd = (V(pts[-1]) - V(pts[-2])).normalized()
        end_f = max(root.data.polygons, key=lambda pp: pp.center.dot(tipd))
        end_f.material_index = 1
        end_f.use_smooth = False
    parts.append(root)

# --- two broken branch stubs with end-grain tips -------------------------------------------------------------------
for k, (x, theta, L, rad) in enumerate(((-0.55, 72, 0.4, 0.11), (0.95, 128, 0.28, 0.085))):
    a = math.radians(theta)
    out = V((0.0, math.cos(a), math.sin(a)))
    base = V((x, 0.0, ZC)) + out * 0.12
    tip = V((x + 0.08, 0.0, ZC)) + out * (0.36 + L)
    stub = sl.tube("branch%d" % k, [base, base.lerp(tip, 0.55) + V((0.03, 0, 0)), tip], [rad * 1.15, rad, rad * 0.9],
                   sides=8, per_seg=1, mat=bark, cap_start=False, cap_end=True)
    stub.data.materials.append(grain)
    end = max(stub.data.polygons, key=lambda pp: (pp.center - V((0, 0, 0))).dot(out))
    end.material_index = 1
    end.use_smooth = False
    parts.append(stub)

# --- the hidden skirt: a bark wedge under the whole log down to z = -0.75 -----------------------------------
rings_sk = []
for x, y in ((-1.86, 0.02), (-0.85, 0.06), (0.05, 0.03), (0.95, -0.04), (1.9, -0.03)):
    rings_sk.append([(x, y - 0.22, GL + 0.03), (x, y + 0.22, GL + 0.03), (x, y + 0.34, -0.75), (x, y - 0.34, -0.75)])
bmk = bmesh.new()
vr = [[bmk.verts.new(pnt) for pnt in r] for r in rings_sk]
for i in range(len(vr) - 1):
    for j in range(4):
        jj = (j + 1) % 4
        bmk.faces.new((vr[i][j], vr[i][jj], vr[i + 1][jj], vr[i + 1][j]))
bmk.faces.new(list(reversed(vr[0])))
bmk.faces.new(vr[-1])
bmesh.ops.recalc_face_normals(bmk, faces=bmk.faces[:])
parts.append(nl.obj_from_bm("skirt", bmk, bark))

# --- moss over the top -------------------------------------------------------------------------------------------
pads = [sl.moss_pad("moss", body, (0.3, 0.02), 0.66, thick=0.11, mat=moss_m, seed=5, squash=(1.9, 0.42), rot=0,
                    lobes=((3, 0.16), (5, 0.1), (7, 0.05)), rings=(0.0, 0.4, 0.72, 0.9, 1.0), seg=16, puff=0.3,
                    tuck=0.03, dome=(2.2, 0.6), bvh=bvh),
        sl.moss_pad("moss2", body, (-1.3, 0.06), 0.34, thick=0.09, mat=moss_m, seed=9, squash=(1.3, 0.62), rot=20,
                    lobes=((3, 0.18), (5, 0.08)), rings=(0.0, 0.45, 0.8, 1.0), seg=12, puff=0.3, tuck=0.03,
                    dome=(2.2, 0.6), bvh=bvh)]
parts += [p for p in pads if p is not None]
print("RWREPORT   parts: " + ", ".join("%s %d" % (o.name, sl.tris(o)) for o in parts))
obj = sl.one_mesh(parts, ASSET)
sl.finish(ASSET, obj, 1000, max_mats=3, col_r=0.5, ground_z=GL, uv=False,
          note="collision sphere r 0.5 covers only the middle of a 4 m log")
if sl.qa_on():
    sl.qa_render(ASSET, "ends", (1.0, -0.35, 0.3), objs=[obj])
    sl.qa_render(ASSET, "root", (-1.0, -0.4, 0.3), objs=[obj])
sl.qa_extra(ASSET, sink=GL)
