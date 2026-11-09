"""scatterlib: helpers for RuneWire's scattered nature models (art/blender/nature/).

Used by rock_a, rock_b, rock_c, cliff_a, bush_round, bush_flower, flower_patch, mushroom_cluster, log_fallen
and stump. Builds on rwlib and naturelib, and borrows plant parts from env/gatherlib (imported on demand by
gather()). None of those modules is edited.

How the game uses these models (scripts/world/vegetation.gd) and what that means here:
* Every MeshInstance3D in the .glb becomes one MultiMesh per 80 m chunk, and every material surface is one draw
  call. So each asset is ONE mesh object (named like the asset) with 2-3 materials. one_mesh() joins the parts
  and finish() refuses to export anything else.
* Instances are scaled 0.7-1.6 and yawed at random; rocks and the cliff are also tilted up to +-11.5 degrees.
  Everything is sunk 0.15-0.35 m into the terrain (cliffs 1.5 m). So rocks, the cliff, the log and the stump
  carry a solid skirt that continues below z = 0, and a tilted or sloped instance never shows a floating edge.
  Plants are clipped at z = 0 instead (gatherlib.clip_below).
* Collision is a sphere the game builds itself (radius r x scale, centred 0.4 r above the origin), so no
  collision proxies are exported. Keep the solid bulk roughly inside that sphere's footprint.
* scripts/autoload/material_library.gd: a flat material whose name contains grass, leaf, leaves, foliage,
  flower or petal gets the wind-sway foliage shader, which drops emission. The sway moves each vertex by its
  height above the instance origin: up to 7 cm at 0.7 m for grass/flower/petal names, about 3 mm at 1.2 m for
  leaf/foliage names and M_Leaves. Parts that touch therefore share one sway class, and glowing parts never use
  those words.

Main builders
* boulder() / boulder_bm() / stone()   chunky faceted cartoon boulder: convex hull of a superellipsoid cap, a
                belly ring, a ground ring and a skirt ring; chiselled by a few planes into big flat facets; soft
                bevels with hardened normals (flat facets, rounded edges); the skirt floor is re-cut flat.
* split_bm()    cracks a boulder in two halves that lean apart from a hinge at the ground (rock_c).
* outline() / slab()   irregular notched polygons extruded into bevelled beds (cliff strata).
* moss_pad()    a moss blanket draped over a surface: a lobed pad that follows it (ray-cast from above) with a
                soft rounded edge tucked in; moss_cushion() fuses a few dropped lumps into one puffy cushion.
* bloom_bm() / leaf_bm()   cheap cartoon blossoms and leaves for the double-sided foliage shader.
* tube() / uv_rings()   swept tubes with cylindrical UVs, so bark ridges follow a lying log or a root.
* tinted_stone()   M_StoneRough__<tint> with a preview colour that matches the game (texture mean x tint).
* finish()      checks (one mesh, triangle budget, material count) + rw.finish + ground-line previews.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "..")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import rwlib as rw  # noqa: E402
import naturelib as nl  # noqa: E402

V = Vector
UP = Vector((0.0, 0.0, 1.0))
CAT = "nature"
QA_DIR = "/tmp/rwqa/nature"
SINK = 0.15          # vegetation.gd sinks every instance at least this far: the game's ground line in model space

# Flat accent colours shared by the scatter models (names are sway-safe unless noted).
MOSS = ("Moss", "6e9f3a")            # same name and colour as the moss on env/node_glowcap
END_GRAIN = ("EndGrain", "d9a96a")   # pale cut wood (same as the forge's EndGrain accent)


STONE_TEX_MEAN = "888384"   # mean sRGB of assets/textures/stone_rough/stone_rough_albedo.png (as in gatherlib)


def tinted_stone(tint_hex):
    """M_StoneRough__<tint>: Godot multiplies the stone texture by the tint. The Blender stand-in shows
    texture mean x tint so the previews match the game's value."""
    name = "M_StoneRough__%s" % tint_hex.lower()
    m = rw._resolve_mat(name)
    a = rw.srgb_to_linear(rw.hex_to_srgb(STONE_TEX_MEAN))
    t = rw.srgb_to_linear(rw.hex_to_srgb(tint_hex))
    lin = tuple(x * y for x, y in zip(a, t))
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = lin + (1.0,)
    m.diffuse_color = lin + (1.0,)
    return m


def gather():
    """env/gatherlib (mushroom, flower_head, ribbon, dome, clip_below...), imported on demand."""
    sys.dont_write_bytecode = True
    env = os.path.join(HERE, "..", "env")
    if env not in sys.path:
        sys.path.insert(0, env)
    import gatherlib as G  # noqa: E402
    return G


# --------------------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------------------


def update():
    bpy.context.view_layer.update()


def tris(o):
    return rw.tri_count([o])


def mats_of(o):
    return [s.material.name for s in o.material_slots if s.material]


def superellipse(phi, p):
    """Unit superellipse direction (p = 2 circle, larger p squarer)."""
    c, s = math.cos(phi), math.sin(phi)
    return (math.copysign(abs(c) ** (2.0 / p), c), math.copysign(abs(s) ** (2.0 / p), s))


def bvh_of(o):
    """BVH of an object's evaluated mesh in world space."""
    update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = o.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def inside(bvh, p, eps=0.0):
    """True if p is inside the closed surface held by bvh (nearest-face normal test)."""
    loc, nrm, _, _ = bvh.find_nearest(p)
    if loc is None:
        return False
    return (p - loc).dot(nrm) < -eps


def drop(bvh, x, y, z0=100.0):
    """Ray straight down onto the surface: (point, normal) or (None, None)."""
    loc, nrm, _, _ = bvh.ray_cast(V((x, y, z0)), V((0, 0, -1)))
    if loc is None:
        return None, None
    if nrm.z < 0:
        nrm = -nrm
    return loc, nrm


def cull_inside(o, bvh, eps=0.004):
    """Delete the faces of o whose vertices are all inside the surface in bvh (hidden under a rock)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    mw = o.matrix_world
    kill = [f for f in bm.faces if all(inside(bvh, mw @ v.co, eps) for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return len(kill)


def soft_bevel(o, width=0.05, segments=2, angle=30.0, profile=0.55, apply=True):
    """Cartoon stone edges: flat facets (hardened normals) with softly rounded bevels between them.
    Faces are smooth-shaded so the bevel strips interpolate while the big facets keep their own normal."""
    nl.shade_smooth_all(o)
    m = o.modifiers.new("SoftBevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = True
    m.use_clamp_overlap = True
    m.profile = profile
    m.miter_outer = 'MITER_ARC'
    if apply:
        rw.apply_modifiers(o)
    return o


def flat_cap_below(o, z):
    """Cut everything below height z (world) and close the cut with one flat n-gon (the skirt floor):
    removes the bevel rounding that a buried bottom edge would otherwise carry."""
    rw.apply_modifiers(o)
    update()
    co = o.matrix_world.inverted() @ V((0, 0, z))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=co,
                                 plane_no=(0, 0, 1), clear_inner=True)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid]
    if edges:
        try:
            r = bmesh.ops.edgeloop_fill(bm, edges=edges)
            new = r.get("faces", [])
        except Exception:
            r = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            new = r.get("faces", [])
        for f in new:
            f.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


# --------------------------------------------------------------------------------------
# Boulders
# --------------------------------------------------------------------------------------


def _support(bm, c, n):
    return max((v.co - c).dot(n) for v in bm.verts)


def chisel(bm, cuts, centre, seed=0):
    """Slice planes off a convex bmesh. cuts = [(azimuth_deg, elevation_deg, depth), ...]: each plane faces
    that direction (from `centre`) and removes `depth` x the mesh's support distance along it, leaving one big
    flat facet."""
    c = V(centre)
    for (az, el, depth) in cuts:
        a, e = math.radians(az), math.radians(el)
        n = V((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
        s = _support(bm, c, n)
        co = c + n * s * (1.0 - depth)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=co,
                                     plane_no=n, clear_outer=True)
        edges = [x for x in res["geom_cut"] if isinstance(x, bmesh.types.BMEdge) and x.is_valid]
        if edges:
            try:
                bmesh.ops.edgeloop_fill(bm, edges=edges)
            except Exception:
                bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    return bm


def boulder_bm(size, seed=0, skirt=0.5, n_top=18, jitter=0.25, rmin=0.86, shoulder=2.3, plan=2.2, belly=0.32,
               n_ring=9, foot=0.94, taper=0.86, cuts=(), lean=(0.0, 0.0), dissolve=5.0, top_squash=1.0,
               centre=(0.0, 0.0), spin=0.0, shear=(0.0, 0.0)):
    """Chunky convex boulder in a bmesh.

    size      (w, d, h): footprint and height above z = 0 (the skirt is extra, below z = 0)
    belly     height of the widest ring as a fraction of h
    shoulder  superellipsoid exponent of the cap profile (2 = ellipsoid, higher = squarer shoulders)
    plan      superellipse exponent of the footprint
    foot      radius at z = 0 relative to the belly; taper: radius at z = -skirt
    cuts      chisel planes [(azimuth, elevation, depth), ...] (see chisel)
    lean      (dx, dy) shift of the top relative to the belly (cartoon lean)
    shear     (kx, ky): heights above z = 0 scale by 1 + kx x/rx + ky y/ry (a wedge rising toward +x / +y)
    """
    rng = random.Random(seed)
    w, d, h = size
    rx, ry = w / 2.0, d / 2.0
    zb = h * belly
    hz = h - zb
    bm = bmesh.new()
    ga = math.pi * (3 - math.sqrt(5))
    ph0 = rng.uniform(0, 2 * math.pi)

    def put(x, y, z):
        t = max(0.0, (z - zb) / hz) if hz > 0 else 0.0
        if z > 0 and shear != (0.0, 0.0):
            z *= max(0.2, 1.0 + shear[0] * x / rx + shear[1] * y / ry)
        bm.verts.new((x + lean[0] * t, y + lean[1] * t, z))

    for i in range(n_top):
        cz = 1.0 - (i + 0.5) / n_top                 # cos(theta), top -> equator (uniform area)
        th = math.acos(max(-1.0, min(1.0, cz)))
        ph = ph0 + ga * i + rng.uniform(-jitter, jitter)
        s, c = math.sin(th), math.cos(th)
        rr = abs(s) ** (2.0 / shoulder)
        vz = abs(c) ** (2.0 / shoulder) * top_squash
        px, py = superellipse(ph, plan)
        k = rng.uniform(rmin, 1.0)
        kz = rng.uniform(rmin, 1.0)
        put(rx * rr * px * k, ry * rr * py * k, zb + hz * min(1.0, vz * kz))
    for ring_z, fac, jit in ((zb, 1.0, 0.04), (0.0, foot, 0.03), (-skirt, taper, 0.02)):
        for i in range(n_ring):
            ph = ph0 + 2 * math.pi * (i + rng.uniform(-0.3, 0.3)) / n_ring
            px, py = superellipse(ph, plan)
            k = fac * rng.uniform(1.0 - jit * 2, 1.0)
            z = ring_z + (rng.uniform(-jit, jit) * h if ring_z > 0 else 0.0)
            if ring_z > 0:
                put(rx * px * k, ry * py * k, z)
            else:
                bm.verts.new((rx * px * k, ry * py * k, z))
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    unused = list({v for v in res.get("geom_interior", []) + res.get("geom_unused", [])
                   if isinstance(v, bmesh.types.BMVert) and v.is_valid})
    if unused:
        bmesh.ops.delete(bm, geom=unused, context='VERTS')
    if cuts:
        chisel(bm, cuts, (0.0, 0.0, zb), seed)
    if dissolve:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve), verts=bm.verts[:], edges=bm.edges[:])
    if spin:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(spin), 3, 'Z'))
    if centre != (0.0, 0.0):
        bmesh.ops.translate(bm, verts=bm.verts[:], vec=V((centre[0], centre[1], 0.0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def boulder(name, size, mat="M_StoneRough", bevel=0.05, segments=2, bevel_angle=30.0, skirt=0.5, **kw):
    """boulder_bm -> object with soft bevels applied; the skirt floor is re-cut flat (no buried bevel)."""
    bm = boulder_bm(size, skirt=skirt, **kw)
    o = nl.obj_from_bm(name, bm, mat)
    if bevel:
        soft_bevel(o, bevel, segments, bevel_angle)
        flat_cap_below(o, -skirt + bevel * 1.2)
    return o


def split_bm(bm, normal=(1.0, 0.0, 0.0), offset=0.0, gap_deg=6.0, drop=(0.0, 0.0), shift=0.0):
    """Split a convex bmesh by a vertical plane into two halves that lean apart from a hinge line at z = 0
    (a cracked boulder with a V-shaped cleft). drop = (dz first, dz second) sinks a half; shift slides both
    halves apart along the normal. Returns (bm_a, bm_b); the input bm is freed."""
    n = V(normal).normalized()
    co = n * offset
    hinge = n.cross(UP).normalized()
    out = []
    for side, sign in ((0, 1.0), (1, -1.0)):
        b = bm.copy()
        res = bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], dist=1e-5, plane_co=co,
                                     plane_no=n, clear_outer=(side == 0), clear_inner=(side == 1))
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid]
        if edges:
            try:
                bmesh.ops.edgeloop_fill(b, edges=edges)
            except Exception:
                bmesh.ops.holes_fill(b, edges=edges, sides=0)
        # the first half (behind the plane, -n side) tips toward -n, the second toward +n
        ang = math.radians(gap_deg) * (1.0 if side == 0 else -1.0)
        R = Matrix.Rotation(ang, 3, hinge)
        bmesh.ops.rotate(b, verts=b.verts[:], cent=co, matrix=R)
        bmesh.ops.translate(b, verts=b.verts[:], vec=n * (-shift if side == 0 else shift) + V((0, 0, drop[side])))
        bmesh.ops.recalc_face_normals(b, faces=b.faces[:])
        out.append(b)
    bm.free()
    return out[0], out[1]


def stone(name, bm, mat="M_StoneRough", bevel=0.05, segments=2, bevel_angle=30.0, floor=None):
    """Object from a stone bmesh with soft bevels; floor = z of the flat skirt floor to re-cut (or None)."""
    o = nl.obj_from_bm(name, bm, mat)
    if bevel:
        soft_bevel(o, bevel, segments, bevel_angle)
        if floor is not None:
            flat_cap_below(o, floor + bevel * 1.2)
    return o


# --------------------------------------------------------------------------------------
# Strata (cliffs)
# --------------------------------------------------------------------------------------


def outline(n, rx, ry, seed=0, centre=(0.0, 0.0), p=2.4, jitter=0.07, notches=(), phase=0.0, ang_jitter=0.25):
    """Chunky irregular polygon (counter-clockwise) on a superellipse: n corners with radial jitter, plus
    V-notches [(angle_deg, depth_m, half_width_deg), ...] cut into the edge (vertical joints in a cliff wall)."""
    rng = random.Random(seed)
    cx, cy = centre
    items = []
    for i in range(n):
        a = phase + 2 * math.pi * (i + rng.uniform(-ang_jitter, ang_jitter)) / n
        items.append((a % (2 * math.pi), 1.0 + rng.uniform(-jitter, jitter), 0.0))
    for (ad, depth, hw) in notches:
        a = math.radians(ad) % (2 * math.pi)
        items = [it for it in items if min(abs(it[0] - a), 2 * math.pi - abs(it[0] - a)) > math.radians(hw) * 1.2]
        for da, dd in ((-hw, 0.0), (0.0, depth), (hw, 0.0)):
            items.append(((a + math.radians(da)) % (2 * math.pi), 1.0, dd))
    items.sort(key=lambda t: t[0])
    pts = []
    for a, r, dd in items:
        ux, uy = superellipse(a, p)
        x, y = rx * ux * r, ry * uy * r
        if dd:
            L = math.hypot(x, y) or 1.0
            x, y = x - x / L * dd, y - y / L * dd
        pts.append((cx + x, cy + y))
    return pts


def slab_bm(bm, pts, z0, z1, inset=0.15, dip=(0.0, 0.0), flare=0.0, top_jitter=0.0, seed=0, floor=True):
    """One stratum: polygon pts extruded from z0 to z1 into `bm`. The top ring is pulled `inset` toward the
    centroid (walls lean in), the bottom ring pushed out by `flare`; dip = (dz/dx, dz/dy) tilts both faces
    (parallel strata), top_jitter adds a little unevenness to the top rim. floor=False leaves the bottom open
    (a bed resting on the one below, whose underside can never be seen)."""
    rng = random.Random(seed)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    bot, top = [], []
    for (x, y) in pts:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        bx, by = x + dx / L * flare, y + dy / L * flare
        tx, ty = x - dx / L * inset, y - dy / L * inset
        bot.append(bm.verts.new((bx, by, z0 + dip[0] * bx + dip[1] * by)))
        top.append(bm.verts.new((tx, ty, z1 + dip[0] * tx + dip[1] * ty + rng.uniform(-top_jitter, top_jitter))))
    n = len(pts)
    if floor:
        bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    return bm


def slab(name, pts, z0, z1, mat="M_StoneRough", bevel=0.14, segments=2, bevel_angle=32.0, **kw):
    bm = bmesh.new()
    slab_bm(bm, pts, z0, z1, **kw)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = nl.obj_from_bm(name, bm, mat)
    if bevel:
        soft_bevel(o, bevel, segments, bevel_angle)
    return o


# --------------------------------------------------------------------------------------
# Moss
# --------------------------------------------------------------------------------------


def moss_pad(name, target, centre, radius, thick=0.07, lobes=((3, 0.16), (5, 0.08)), seg=14,
             rings=(0.0, 0.42, 0.72, 0.9, 1.0), mat=None, seed=0, squash=(1.0, 1.0), rot=0.0, tuck=0.035,
             bvh=None, smooth_iters=2, puff=0.0, dome=(4.0, 0.5)):
    """Moss blanket draped over the top of `target`: a lobed pad around `centre` (x, y) whose surface follows
    the stone below (ray-cast from above) plus a soft cushion profile thick * (1 - rf^a)^b (dome = (a, b);
    (4, 0.5) is flat-topped, (2, 0.6) domed), its rim tucked `tuck` into the stone so no gap shows. puff adds
    soft noise bumps. Returns the pad object (or None if it missed the target)."""
    rng = random.Random(seed)
    bvh = bvh or bvh_of(target)
    cx, cy = centre
    phases = [rng.uniform(0, 2 * math.pi) for _ in lobes]
    bm = bmesh.new()
    grid = []
    for ri, rf in enumerate(rings):
        ring = []
        n = 1 if rf == 0.0 else seg
        for k in range(n):
            a = 2 * math.pi * k / seg + math.radians(rot)
            lobe = 1.0 + sum(amp * math.sin(f * a + p) for (f, amp), p in zip(lobes, phases))
            r = radius * rf * lobe
            x = cx + r * math.cos(a) * squash[0]
            y = cy + r * math.sin(a) * squash[1]
            p, nrm = drop(bvh, x, y)
            k = 0
            while p is None and k < 12:          # off the edge: pull the point back toward the centre
                k += 1
                x, y = cx + (x - cx) * 0.9, cy + (y - cy) * 0.9
                p, nrm = drop(bvh, x, y)
            if p is None:
                bm.free()
                return None
            if rf >= 1.0:
                z = p.z - tuck
            else:
                prof = max(0.0, 1.0 - rf ** dome[0]) ** dome[1]
                bump = puff * noise.noise(V((x * 3.1, y * 3.1, seed * 1.7)))
                z = p.z + thick * prof * (1.0 + bump)
            ring.append(bm.verts.new((x, y, z)))
        grid.append(ring)
    for ri in range(len(grid) - 1):
        a, b = grid[ri], grid[ri + 1]
        if len(a) == 1:
            for k in range(seg):
                bm.faces.new((a[0], b[k], b[(k + 1) % seg]))
        else:
            for k in range(seg):
                j = (k + 1) % seg
                bm.faces.new((a[k], b[k], b[j], a[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = nl.obj_from_bm(name, bm, mat)
    if smooth_iters:
        # relax the inner rings only (keep the tucked rim where it is)
        bm2 = bmesh.new()
        bm2.from_mesh(o.data)
        rim = set(v for v in bm2.verts if v.is_boundary)
        bmesh.ops.smooth_vert(bm2, verts=[v for v in bm2.verts if v not in rim], factor=0.5,
                              use_axis_x=False, use_axis_y=False, use_axis_z=True)
        for _ in range(smooth_iters - 1):
            bmesh.ops.smooth_vert(bm2, verts=[v for v in bm2.verts if v not in rim], factor=0.5,
                                  use_axis_x=False, use_axis_y=False, use_axis_z=True)
        bm2.to_mesh(o.data)
        bm2.free()
    # make sure every face points up/outward
    bm3 = bmesh.new()
    bm3.from_mesh(o.data)
    bm3.normal_update()
    up = sum((f.normal.z for f in bm3.faces), 0.0)
    if up < 0:
        bmesh.ops.reverse_faces(bm3, faces=bm3.faces[:])
    bm3.to_mesh(o.data)
    bm3.free()
    nl.shade_smooth_all(o)
    return o


def moss_cushion(name, target, spots, mat=None, voxel=0.035, budget=110, seed=0, sink=0.45, bvh=None, noise_amt=0.1,
                 smooth_iters=3):
    """Puffy moss cushion on top of `target`: flattened lumps dropped onto the surface (spots = [(x, y, rx, ry, h),
    ...], each sunk `sink` x h below the hit point), fused into one soft surface, the part hidden inside the
    stone culled, then decimated to `budget` triangles."""
    bvh = bvh or bvh_of(target)
    parts = []
    for i, (x, y, rx, ry, h) in enumerate(spots):
        p, nrm = drop(bvh, x, y)
        if p is None:
            continue
        c = V((x, y, p.z - sink * h))
        parts.append(rw.blob("%s_lump%d" % (name, i), (2 * rx, 2 * ry, 2 * h), tuple(c), (0, 0, (i * 53) % 360), mat,
                             subdiv=3, noise=noise_amt, noise_size=0.35, seed=seed + i * 5, smooth_angle=0))
    if not parts:
        return None
    o = rw.join(parts, name, origin=(0, 0, 0))
    nl.purge_helpers()
    nl.remesh(o, voxel, smooth_iters, 0.5)
    nl.drop_small_islands(o, 30)
    cull_inside(o, bvh, 0.03)
    nl.decimate(o, budget)
    nl.shade_smooth_all(o)
    return o


# --------------------------------------------------------------------------------------
# Flowers
# --------------------------------------------------------------------------------------


def frame(normal, spin=0.0):
    """3x3 rotation taking +Z to `normal`, then spun `spin` radians about it."""
    n = V(normal).normalized()
    q = UP.rotation_difference(n).to_matrix()
    return q @ Matrix.Rotation(spin, 3, 'Z')


def bloom_bm(bm_petal, bm_eye, centre, normal, R=0.07, rc=0.024, n_petals=5, cup=0.25, spin=0.0, petal_w=0.62,
             eye_h=0.5, tip_round=0.55, back=True, cheap=False):
    """A cheap cartoon blossom written into two bmeshes (petals / eye disc): n_petals rounded petals around a
    domed centre, cupped `cup` x R toward the facing direction. Built facing +Z at the origin, then turned to
    face `normal` and moved to `centre`. back=True adds a flat back for each petal (closed, for one-sided
    shaders); False leaves single-sided petals (for the double-sided foliage shader). cheap=True: pentagon petals
    and an n_petals-sided eye (about 4 x n_petals triangles per blossom)."""
    M3 = frame(normal, spin)
    c = V(centre)

    def P(x, y, z):
        return c + M3 @ V((x, y, z))

    seg = 2 * math.pi / n_petals
    hw = seg * petal_w / 2
    # eye: a low dome (fan) of 2 * n_petals rim verts
    rim = []
    ne = n_petals if cheap else 2 * n_petals
    for k in range(ne):
        a = k * 2 * math.pi / ne + (seg / 2 if cheap else 0.0)
        rim.append(bm_eye.verts.new(P(rc * math.cos(a), rc * math.sin(a), rc * 0.15)))
    top = bm_eye.verts.new(P(0, 0, rc * eye_h + rc * 0.15))
    for k in range(ne):
        bm_eye.faces.new((rim[k], rim[(k + 1) % ne], top))
    # petals: base pair under the eye rim, a widened middle pair, and a rounded tip
    for k in range(n_petals):
        a = k * seg
        z_mid, z_tip = cup * R * 0.45, cup * R
        b0 = P(rc * 0.7 * math.cos(a - hw * 0.55), rc * 0.7 * math.sin(a - hw * 0.55), 0.0)
        b1 = P(rc * 0.7 * math.cos(a + hw * 0.55), rc * 0.7 * math.sin(a + hw * 0.55), 0.0)
        rm = rc + (R - rc) * 0.62
        m0 = P(rm * math.cos(a - hw), rm * math.sin(a - hw), z_mid)
        m1 = P(rm * math.cos(a + hw), rm * math.sin(a + hw), z_mid)
        tip = P(R * math.cos(a), R * math.sin(a), z_tip)
        rt = R * (1 - (1 - tip_round) * 0.25)
        t0 = P(rt * math.cos(a - hw * tip_round), rt * math.sin(a - hw * tip_round), z_tip * 0.92)
        t1 = P(rt * math.cos(a + hw * tip_round), rt * math.sin(a + hw * tip_round), z_tip * 0.92)
        ring = (b0, m0, tip, m1, b1) if cheap else (b0, m0, t0, tip, t1, m1, b1)
        vs = [bm_petal.verts.new(p) for p in ring]
        bm_petal.faces.new(vs)
        if back:
            off = M3 @ V((0, 0, -0.006))
            vb = [bm_petal.verts.new(v.co + off) for v in vs]
            bm_petal.faces.new(list(reversed(vb)))
            for i in range(len(vs)):
                j = (i + 1) % len(vs)
                bm_petal.faces.new((vs[j], vs[i], vb[i], vb[j]))
    return bm_petal, bm_eye


def leaf_bm(bm, base, heading, length, width, rise=0.3, droop=0.25, fold=0.25, tilt=0.0):
    """Cheap cartoon leaf in a bmesh (about 10 triangles, single-sided: for the double-sided foliage shader):
    a pointed oval along an arch that leaves `base` toward azimuth `heading` (radians), climbs `rise` x length
    and droops `droop` x length at the tip; the blade is folded up along its midrib by `fold` x width.
    tilt (radians) rolls the blade about its midrib."""
    b = V(base)
    out = V((math.cos(heading), math.sin(heading), 0.0))
    side = V((-out.y, out.x, 0.0))
    ts = (0.0, 0.3, 0.62, 1.0)
    ws = (0.3, 1.0, 0.85, 0.0)
    rows = []
    for t, w in zip(ts, ws):
        z = length * (rise * math.sin(math.pi * min(t, 0.75) / 1.5) * 1.6 - droop * t * t)
        c = b + out * (length * t) + V((0, 0, z))
        hw = width * 0.5 * w
        s_ = side * math.cos(tilt) + UP * math.sin(tilt)
        up = UP * math.cos(tilt) - side * math.sin(tilt)
        if w <= 0.0:
            rows.append([bm.verts.new(c)])
        else:
            rows.append([bm.verts.new(c + s_ * hw + up * (fold * hw)), bm.verts.new(c),
                         bm.verts.new(c - s_ * hw + up * (fold * hw))])
    for i in range(len(rows) - 1):
        a, d = rows[i], rows[i + 1]
        if len(d) == 1:
            bm.faces.new((a[0], a[1], d[0]))
            bm.faces.new((a[1], a[2], d[0]))
        else:
            bm.faces.new((a[0], a[1], d[1], d[0]))
            bm.faces.new((a[1], a[2], d[2], d[1]))
    return bm


def surface_points(target, centre, dirs, bvh=None):
    """Ray-cast from far outside toward `centre` along each direction; returns [(point, normal), ...]."""
    bvh = bvh or bvh_of(target)
    c = V(centre)
    out = []
    for d in dirs:
        d = V(d).normalized()
        o = c + d * 50.0
        loc, nrm, _, _ = bvh.ray_cast(o, -d)
        if loc is None:
            continue
        if nrm.dot(d) < 0:
            nrm = -nrm
        out.append((loc, nrm))
    return out


def fib_dirs(n, zmin=-1.0, seed=0, jitter=0.0):
    """n roughly even directions on the unit sphere with z >= zmin (Fibonacci spiral)."""
    rng = random.Random(seed)
    ga = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        z = 1 - (1 - zmin) * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        th = ga * i + rng.uniform(-jitter, jitter)
        out.append(V((math.cos(th) * r, math.sin(th) * r, z)))
    return out


# --------------------------------------------------------------------------------------
# UVs for swept tubes (logs, roots, branches)
# --------------------------------------------------------------------------------------


def uv_rings(bm, rings, tile=2.0, wraps=None):
    """Cylindrical UVs on the quads between consecutive rings (as returned by naturelib.sweep_bm): V runs along
    the tube (so the bark texture's ridges follow a lying log), U around it. wraps = texture repeats around the
    tube (default: the mean circumference / tile, rounded to a whole number so there is no seam)."""
    uv = bm.loops.layers.uv.verify()
    n = len(rings[0])
    cen = [sum((v.co for v in r), V()) / len(r) for r in rings]
    arc = [0.0]
    for i in range(1, len(rings)):
        arc.append(arc[-1] + (cen[i] - cen[i - 1]).length)
    if wraps is None:
        rad = sum((v.co - cen[i]).length for i, r in enumerate(rings) for v in r) / (n * len(rings))
        wraps = max(1, round(2 * math.pi * rad / tile))
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(n):
            j = (k + 1) % n
            f = bm.faces.get((a[k], a[j], b[j], b[k]))
            if f is None:
                continue
            uk, uj = wraps * k / n, wraps * (k + 1) / n
            coords = {a[k]: (uk, arc[i] / tile), a[j]: (uj, arc[i] / tile), b[j]: (uj, arc[i + 1] / tile),
                      b[k]: (uk, arc[i + 1] / tile)}
            for loop in f.loops:
                loop[uv].uv = coords[loop.vert]
    return bm


def tube(name, pts, radii, sides=8, per_seg=2, mat="M_Bark", cap_start=True, cap_end=True, shaper=None, phase=0.0,
         up_hint=None, tile=2.0, smooth=True):
    """naturelib-style swept tube (sweep_bm) with cylindrical UVs (see uv_rings). Returns the object."""
    bm = bmesh.new()
    rings, _ = nl.sweep_bm(bm, pts, radii, sides, per_seg, cap_start, cap_end, 0.0, shaper, phase, 0.0, up_hint)
    uv_rings(bm, rings, tile)
    o = nl.obj_from_bm(name, bm, mat)
    if smooth:
        nl.shade_smooth_all(o)
    return o


# --------------------------------------------------------------------------------------
# Joining, checks, finishing
# --------------------------------------------------------------------------------------


def one_mesh(parts, name):
    """Join everything into ONE mesh object named `name`, origin at the base centre (0, 0, 0)."""
    parts = [p for p in parts if p is not None]
    o = rw.join(parts, name, origin=(0, 0, 0)) if len(parts) > 1 else parts[0]
    o.name = name
    o.data.name = name
    nl.purge_helpers()
    return o


def above_ground_size(o):
    update()
    mw = o.matrix_world
    pts = [mw @ v.co for v in o.data.vertices]
    up = [p for p in pts if p.z >= -1e-4]
    mn = V((min(p.x for p in up), min(p.y for p in up), 0.0))
    mx = V((max(p.x for p in up), max(p.y for p in up), max(p.z for p in up)))
    zmin = min(p.z for p in pts)
    return mn, mx, zmin


def footprint_radius(o, zmax=None):
    """Largest horizontal distance of the mesh from the origin axis (above ground, below zmax)."""
    mw = o.matrix_world
    r = 0.0
    for v in o.data.vertices:
        p = mw @ v.co
        if p.z < 0 or (zmax is not None and p.z > zmax):
            continue
        r = max(r, math.hypot(p.x, p.y))
    return r


def preview_glow(mat_name, base_hex, emit_hex, strength):
    """Previews only (call after the export): AgX washes bright flat glows toward white while the game keeps their
    hue, so give the Blender stand-in a darker base and a moderate emission (same idea as stationlib.preview_glow).
    The exported .glb keeps the real values, which Godot converts into its glow material."""
    m = bpy.data.materials.get(mat_name)
    if m is None:
        return None
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(base_hex)
    b.inputs["Emission Color"].default_value = rw._lin(emit_hex)
    b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = rw._lin(base_hex)[:3] + (1.0,)
    return m


def finish(asset, o, budget, max_mats=3, col_r=None, note="", preview_glows=None, ground_z=0.0, uv=True):
    """Checks (one mesh object, triangle budget, material count) + RWREPORT lines, then rw.finish.
    preview_glows {material: (base_hex, emission_hex, strength)} is applied after the .blend/.glb are written,
    for the preview renders only. uv=False keeps the script's own UVs (e.g. uv_rings on a lying log) instead of
    rwlib's world box projection."""
    update()
    meshes = [m for m in rw.all_mesh_objects()]
    assert len(meshes) == 1 and meshes[0] == o, "expected exactly one mesh object, got %s" % [m.name for m in meshes]
    n = tris(o)
    mats = mats_of(o)
    used = sorted({o.data.materials[p.material_index].name for p in o.data.polygons})
    mn, mx, zmin = above_ground_size(o)
    size = mx - mn
    print("RWREPORT %s CHECK one mesh '%s'; tris %d / %d %s; materials %d %s (used %s)" % (
        asset, o.name, n, budget, "OK" if n <= budget else "OVER BUDGET", len(mats), mats, used))
    print("RWREPORT %s CHECK above-ground size %.2f x %.2f x %.2f m (x %.2f..%.2f, y %.2f..%.2f); lowest z %.2f" % (
        asset, size.x, size.y, size.z, mn.x, mx.x, mn.y, mx.y, zmin))
    if col_r:
        print("RWREPORT %s CHECK footprint radius (z 0..%.2f) %.2f vs collision sphere %.2f" % (
            asset, col_r * 1.4, footprint_radius(o, col_r * 1.4), col_r))
    if note:
        print("RWREPORT %s NOTE %s" % (asset, note))
    if n > budget:
        raise SystemExit("%s: %d triangles is over the %d budget" % (asset, n, budget))
    if len(mats) > max_mats:
        raise SystemExit("%s: %d materials (max %d)" % (asset, len(mats), max_mats))
    rw.finish(asset, CAT, previews=(), uv=uv)
    for name, (base_hex, emit_hex, strength) in (preview_glows or {}).items():
        preview_glow(name, base_hex, emit_hex, strength)
    previews(asset, o, ground_z=ground_z)


GROUND_HEX = "9c8f72"     # preview ground disc (earthy, so greens and greys both read against it)


def previews(asset, o, views=("front34", "back34"), size=640, ground=True, ground_z=0.0):
    """The standard previews (art/previews/nature/<asset>_<view>.png, same rig, lights and outline as rw.finish),
    but framed on the part above the ground line and standing on a ground disc at ground_z (0, or SINK for the
    small plants, which the game sinks 0.15 m), so the buried skirt doesn't distort the picture. Runs after the
    .blend and .glb are written; the disc and the temporary ground-cut copy are removed again."""
    mn, mx, _ = above_ground_size(o)
    mn.z = ground_z
    g = None
    shown = o
    if ground:
        r = max(mx.x - mn.x, mx.y - mn.y) * 0.85 + 0.5
        g = qa_ground(r, ground_z, GROUND_HEX)
        # Freestyle can't split an outline where it passes into the disc, so buried skirt edges would be drawn
        # through the ground: render a temporary copy cut at the ground line instead (the terrain hides that
        # part in the game too)
        shown = o.copy()
        shown.data = o.data.copy()
        bpy.context.scene.collection.objects.link(shown)
        bm = bmesh.new()
        bm.from_mesh(shown.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                               plane_co=(0, 0, ground_z - 0.01), plane_no=(0, 0, 1), clear_inner=True)
        bm.to_mesh(shown.data)
        bm.free()
        o.hide_render = True
    for v in views:
        rw._setup_render(size, False, True)
        temp = rw._temp_rig(mn, mx, v)
        path = os.path.join(rw.ART, "previews", CAT, "%s_%s.png" % (asset, v))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        for t in temp:
            d = t.data
            bpy.data.objects.remove(t, do_unlink=True)
            if isinstance(d, bpy.types.Camera):
                bpy.data.cameras.remove(d)
            elif isinstance(d, bpy.types.Light):
                bpy.data.lights.remove(d)
        print("RWREPORT   rendered", path)
    if g is not None:
        bpy.data.objects.remove(g, do_unlink=True)
    if shown is not o:
        me = shown.data
        bpy.data.objects.remove(shown, do_unlink=True)
        bpy.data.meshes.remove(me)
        o.hide_render = False


# --------------------------------------------------------------------------------------
# QA (renders to /tmp only; never part of the exported asset)
# --------------------------------------------------------------------------------------


def qa_on():
    return bool(os.environ.get("RW_QA"))


def qa_render(asset, tag, direction, target=None, radius=None, size=640, fov=35.0, objs=None, outline_px=None,
              path=None):
    """Render the current scene from `direction` (looking at target, framing a sphere of radius) to
    /tmp/rwqa/nature/<asset>_<tag>.png (or `path`) with the preview lights and outline."""
    os.makedirs(QA_DIR, exist_ok=True)
    mn, mx = rw.bounds(objs)
    target = V(target) if target is not None else (mn + mx) / 2
    radius = radius if radius is not None else (mx - mn).length / 2
    rw._setup_render(size, False, True)
    if outline_px:
        bpy.context.scene.render.line_thickness = outline_px
        bpy.context.view_layer.freestyle_settings.linesets[0].linestyle.thickness = outline_px
    cd = bpy.data.cameras.new("QA_Cam")
    cd.lens_unit = 'FOV'
    cd.angle = math.radians(fov)
    cd.clip_end = 5000
    cam = bpy.data.objects.new("QA_Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = target + V(direction).normalized() * (radius / math.sin(math.radians(fov) / 2) * 1.08)
    cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    temp = [cam]
    for nm, energy, colr, rot in (("QA_Key", 3.2, (1, 1, 1), (50, -10, -35)),
                                  ("QA_Fill", 0.8, (0.75, 0.82, 1.0), (70, 0, 150))):
        lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        lo.data.energy = energy
        lo.data.color = colr
        lo.rotation_euler = tuple(math.radians(a) for a in rot)
        bpy.context.scene.collection.objects.link(lo)
        temp.append(lo)
    path = path or os.path.join(QA_DIR, "%s_%s.png" % (asset, tag))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for ob in temp:
        dd = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if isinstance(dd, bpy.types.Camera):
            bpy.data.cameras.remove(dd)
        else:
            bpy.data.lights.remove(dd)
    print("RWREPORT   QA rendered", path)
    return path


def qa_ground(radius, z=0.0, colour="7fb34f", loc=(0.0, 0.0)):
    """A thin disc whose top is at height z (QA and previews only; removed before anything is saved)."""
    return rw.cylinder("QA_Ground", radius, 0.02, 64, (loc[0], loc[1], z - 0.01),
                       mat=rw.flat("QA_Ground_%s" % colour, colour))


def qa_extra(asset, views=(("side", (-1, 0, 0.12)), ("top", (0.001, -0.25, 1))), ground=True, sink=0.0):
    """After rw.finish (the .blend/.glb are already written): optional QA renders to /tmp with a ground disc at
    the sink line. Set RW_QA=1."""
    if not qa_on():
        return
    vis = [o for o in rw.all_mesh_objects() if not o.hide_render]
    mn, mx = rw.bounds(vis)
    g = None
    if ground:
        g = qa_ground(max(mx.x - mn.x, mx.y - mn.y) * 1.1 + 0.6, sink, GROUND_HEX)
    for tag, d in views:
        qa_render(asset, tag, d, objs=vis)
    if g is not None:
        bpy.data.objects.remove(g, do_unlink=True)
