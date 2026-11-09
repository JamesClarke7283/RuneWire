"""gatherlib: helpers for the gathering nodes and the Tailor's Loom (art/blender/env/).

Used by node_ore_copper, node_ore_iron, node_glowcap, node_sunpetal, node_reeds and prop_loom.

    import os, sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gatherlib as G
    S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M

Builds on stationlib (accent materials, hull_rock, surface_hit / hit_toward, loft, lathe, ground_centre,
node_report), envlib, partlib and rwlib. None of those is edited.

Helpers: xform / turn / on_ground / radial (placement); ribbon (leaves, blades, petals), dome (bumps, moss, spots),
nugget / octa / nodules / vein / arc_dirs (ore on a rock surface), mushroom, flower_head, rosette_leaf, stub;
tinted (a textured library material tinted so its in-game colour hits a target); join_harvest; clip_below,
ground_centre_on; finish_env / finish_node (check, report, .blend, .glb, previews).

QA switches (environment variables): RW_PREVIEWS=front34 renders fewer previews; RW_QA=1 also renders each node
with Harvest shrunk to 0.05 to /tmp/rwqa/<asset>_harvested_front34.png; RW_QA_CLOSE="tag:dx,dy,dz:tx,ty,tz:radius|..."
adds close-ups (/tmp/rwqa/<asset>_<tag>.png). None of them changes the saved .blend or the exported .glb.

The gathering-node contract (ASSET_SPEC "World props for treasure, gathering and crafting", and
scripts/world/harvest_node.gd):
* The base (rock, stump, clump or mud) is one static mesh, origin at the ground centre.
* Everything the player gathers is ONE mesh object named exactly "Harvest", a child of the base (rw.set_parent).
  The game tweens its scale to 0.05 when gathered and back to 1.0 when it regrows. Each gathered bit therefore
  moves on a straight line toward the Harvest origin, so the bits are placed where that line runs through the
  base (they sink into the rock, stump or clump rather than fly through the air). The base must look natural
  on its own.
* One collision cylinder (E.col_cyl, a "-convcolonly" node).
* The game spins every node to a random yaw, so it has to read from all sides.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import stationlib as S  # noqa: E402

E, rw, pl, V, M = S.E, S.rw, S.pl, S.V, S.M
UP = Vector((0.0, 0.0, 1.0))


# --------------------------------------------------------------------------------------
# Transforms
# --------------------------------------------------------------------------------------

def xform(objs, Mx):
    """Apply a 4x4 world matrix to objects and bake rotation/scale into the meshes (nodes keep a location)."""
    bpy.context.view_layer.update()
    out = []
    for o in (objs if isinstance(objs, (list, tuple)) else [objs]):
        if o is None:
            continue
        o.matrix_world = Mx @ o.matrix_world
        if o.type == 'MESH':
            rw.apply_transform(o)
        out.append(o)
    bpy.context.view_layer.update()
    return out


def turn(objs, az_deg, loc=(0.0, 0.0, 0.0)):
    """Rotate objects built around the origin by az_deg about Z, then move them to loc."""
    return xform(objs, Matrix.Translation(V(loc)) @ Matrix.Rotation(math.radians(az_deg), 4, 'Z'))


def on_ground(o, z=0.0):
    """Move o so that its lowest point sits at height z."""
    bpy.context.view_layer.update()
    mn, _ = rw.bounds([o])
    o.location.z += z - mn.z
    bpy.context.view_layer.update()
    return o


def radial(az_deg, r, z=0.0, c=(0.0, 0.0)):
    a = math.radians(az_deg)
    return V((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r, z))


# --------------------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------------------

def ribbon(name, pts, widths, side, m=None, keel=0.18, thick=0.012, res=1, smooth_angle=60, tri=False):
    """Leaf, blade or petal: a thin strip along a Catmull-Rom path through pts, with a raised midrib.

    widths: one width per path point; a width of 0 at the end makes a pointed tip.
    side: the across-the-blade direction, a vector or a function t (0..1) -> vector (made perpendicular to the path).
    The midrib bulges toward N = tangent x side by keel * width; thick is the thickness at the midrib.
    tri=True uses a triangular cross-section (flat back), which is cheaper (petals)."""
    P, W = pl._resample(pts, widths, max(1, res), res > 1)
    n = len(P)
    bm = bmesh.new()
    rings = []
    for i in range(n):
        t = i / (n - 1)
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        T = (b - a).normalized()
        s = V(side(t) if callable(side) else side)
        s = s - T * s.dot(T)
        if s.length < 1e-6:
            s = T.orthogonal()
        s.normalize()
        N = T.cross(s).normalized()
        w = max(W[i], 0.0)
        if w < 1e-4:
            rings.append([bm.verts.new(P[i])])
            continue
        h = w / 2
        if tri:
            ring = [bm.verts.new(P[i] + s * h), bm.verts.new(P[i] + N * (keel * w + thick)), bm.verts.new(P[i] - s * h)]
        else:
            ring = [bm.verts.new(P[i] + s * h), bm.verts.new(P[i] + N * (keel * w + thick / 2)),
                    bm.verts.new(P[i] - s * h), bm.verts.new(P[i] - N * (thick / 2))]
        rings.append(ring)
    k = 3 if tri else 4
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        if len(A) == k and len(B) == k:
            for j in range(k):
                jj = (j + 1) % k
                bm.faces.new((A[j], A[jj], B[jj], B[j]))
        elif len(A) == k and len(B) == 1:
            for j in range(k):
                bm.faces.new((A[j], A[(j + 1) % k], B[0]))
        elif len(A) == 1 and len(B) == k:
            for j in range(k):
                bm.faces.new((A[0], B[(j + 1) % k], B[j]))
    if len(rings[0]) == k:
        bm.faces.new(rings[0])
    if len(rings[-1]) == k:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.obj_from_bm(name, bm, S.mat(m), smooth_angle)


def dome(name, r, h, p, n=(0, 0, 1), m=None, segs=8, rings=3, sink=0.3, squash=(1.0, 1.0), spin=0.0, smooth=70,
         wall=True):
    """Half-ellipsoid bump (nodule, spot, moss cushion) standing on point p with outward normal n.
    Its base sits sink * h below p, so it looks set into the surface (a flat disc and a short wall, or with
    wall=False a shallow cone)."""
    if wall:
        prof = [(0.0, -sink * h), (r, -sink * h)]
        ks = range(rings + 1)
    else:   # cheaper: a shallow cone underneath, the equator a little below the surface point
        prof = [(0.0, -sink * h), (r, -0.15 * h)]
        ks = range(1, rings + 1)
    for k in ks:
        phi = (math.pi / 2) * k / (rings + 1)
        prof.append((r * math.cos(phi), h * math.sin(phi)))
    prof.append((0.0, h))
    o = S.lathe(name, prof, segs, (0, 0, 0), m, smooth, spin=spin)
    if squash != (1.0, 1.0):
        pl.xform(o, Matrix.Diagonal((squash[0], squash[1], 1.0, 1.0)))
    pl.align(o, n, tuple(p))
    return o


def nugget(name, size, p, n, seed=0, m="M_Copper", sink=0.42, n_points=10, spin=0.0, bevel=0.012, jitter=0.32,
           rmin=0.72, lean=None):
    """Faceted ore chunk (flat-shaded convex hull) standing on surface point p with outward normal n, sunk by
    sink * its height. `lean` (a vector) tips it away from the normal."""
    o = S.hull_rock(name, size, (0, 0, 0), seed=seed, n_points=n_points, jitter=jitter, rmin=rmin, bevel=bevel, m=m,
                    rot_z=spin, dissolve_deg=4.0)
    d = V(n).normalized()
    if lean is not None:
        d = (d + V(lean)).normalized()
    pl.align(o, d, None)
    o.location = V(p) + d * (size[2] * (0.5 - sink))
    return o


def vein(name, target, centre, dirs, r=0.035, lift=0.15, m="M_Copper", segs=6, res=1, taper=(1.0, 1.0),
         flat=(0.5, 1.4), smooth_path=True):
    """Raised vein following target's surface: each direction (from `centre`) is ray-cast back onto the surface;
    the band centre sits lift * r above it (lift 0 = half sunk). taper scales the radius from start to end.
    flat = (across the surface normal, along the surface) squashes the section into a flat inlaid band."""
    pts, nrms = [], []
    for d in dirs:
        p, nrm = S.hit_toward(target, centre, d)
        if p is not None:
            pts.append(p + nrm * (r * flat[0] * lift))
            nrms.append(nrm)
    if len(pts) < 2:
        return None
    radii = [r * (taper[0] + (taper[1] - taper[0]) * i / (len(pts) - 1)) for i in range(len(pts))]
    return pl.sausage(name, pts, radii, segs, res, S.mat(m), (True, True), 2, smooth_path, 60, scale_xy=flat,
                      up_hint=tuple(nrms[0]))


def arc_dirs(az0, el0, az1, el1, n, wiggle=0.0, waves=2.0, phase=0.0, zig=0.0):
    """n directions along a path from (az0, el0) to (az1, el1) (degrees), with a smooth wiggle in elevation and/or
    a zig-zag of +-zig degrees (of arc) in azimuth, both fading out at the ends."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        fade = math.sin(math.pi * t)
        el = el0 + (el1 - el0) * t + wiggle * math.sin(math.pi * 2 * waves * t + phase) * fade
        az = az0 + (az1 - az0) * t + zig * (1 if i % 2 else -1) * fade / max(0.2, math.cos(math.radians(el)))
        out.append(S.sph(az, el))
    return out


def cone_dirs(d, spread_deg, count, seed=0):
    """`count` directions scattered within spread_deg of direction d (the first one is d itself)."""
    rnd = random.Random(seed)
    d = V(d).normalized()
    a = d.orthogonal().normalized()
    b = d.cross(a).normalized()
    out = [d]
    for k in range(1, count):
        th = 2 * math.pi * (k + rnd.uniform(-0.25, 0.25)) / max(1, count - 1)
        s = math.tan(math.radians(spread_deg * rnd.uniform(0.55, 1.0)))
        out.append((d + (a * math.cos(th) + b * math.sin(th)) * s).normalized())
    return out


def nodules(name, target, centre, d, count=5, r=0.08, spread=9.0, seed=0, m="M_Rust", segs=9, h=0.8, rings=2):
    """Botryoidal cluster: `count` overlapping rounded bumps on target's surface around direction d from centre."""
    rnd = random.Random(seed)
    out = []
    for k, dd in enumerate(cone_dirs(d, spread, count, seed)):
        p, n = S.hit_toward(target, centre, dd)
        if p is None:
            continue
        rr = r * (1.0 if k == 0 else rnd.uniform(0.55, 0.8))
        out.append(dome(name, rr, rr * h * rnd.uniform(0.85, 1.1), p, n, m, segs, rings, 0.4,
                        spin=rnd.uniform(0, 60), wall=False))
    return out


def octa(name, r, h, p, n, seed=0, m="M_DarkMetal", sink=0.35, tilt=25.0, bevel=0.0, squash=1.0):
    """Octahedral crystal (a 4-sided bipyramid, like magnetite) of half-width r and half-height h, set into
    surface point p (outward normal n), sunk by sink * h and tilted at random by up to `tilt` degrees."""
    rnd = random.Random(seed)
    o = E.bipyramid(name, r, h, h * squash, 4, (0, 0, 0), m, twist=rnd.uniform(0, 90))
    pl.xform(o, Matrix.Rotation(math.radians(rnd.uniform(-tilt, tilt)), 4, 'X') @
             Matrix.Rotation(math.radians(rnd.uniform(-tilt, tilt)), 4, 'Y'))
    nn = V(n).normalized()
    pl.align(o, nn, None)
    o.location = V(p) + nn * (h * (1.0 - 2 * sink))
    if bevel:
        rw.add_bevel(o, bevel, 1, 30, harden=True)
        rw.apply_modifiers(o)
    return o


# Mean sRGB colour of the library textures (assets/textures/<set>/<set>_albedo.png); the same values as
# art/blender/items/matlib.py, so a node and the item it yields (iron ore) share the same tinted material name.
TEX_MEAN = {"M_StoneRough": "888384", "M_Fabric": "dcdcdc"}
# Previews only (copy of matlib.PREVIEW_METALS): metallic stand-ins reflect the flat grey-blue preview world and turn
# muddy; a lower metallic keeps their hue readable. Godot swaps M_* materials by name, so the game is unaffected.
PREVIEW_METALS = {"M_Copper": ("d87a45", 0.32, 0.55), "M_Brass": ("e2b046", 0.32, 0.55),
                  "M_Steel": ("b4bcc8", 0.32, 0.4), "M_DarkMetal": ("4a515e", 0.4, 0.55)}


def _lin3(h):
    return rw.srgb_to_linear(rw.hex_to_srgb(h))


def _hex_from_lin(lin):
    out = []
    for x in lin:
        x = max(0.0, min(1.0, x))
        s = x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        out.append("%02x" % int(round(max(0.0, min(1.0, s)) * 255)))
    return "".join(out)


def tinted(lib_name, target):
    """Tinted library material "M_<Set>__<tint>" whose in-game colour (Godot multiplies the texture by the tint in
    linear space) comes out at `target` (sRGB hex); the Blender stand-in shows `target` so previews match the game.
    Same maths as matlib.tinted, so equal targets give the same material name. Returns the material name."""
    tex, tgt = _lin3(TEX_MEAN[lib_name]), _lin3(target)
    tint = _hex_from_lin([min(1.0, t / max(x, 1e-4)) for t, x in zip(tgt, tex)])
    name = "%s__%s" % (lib_name, tint)
    preview_color(name, target)
    return name


def preview_metals():
    """Previews only: soften the metallic library stand-ins (see PREVIEW_METALS). finish_env calls it after the
    export, right before the preview renders."""
    for m in bpy.data.materials:
        lib_name = m.name.split("__")[0]
        if lib_name not in PREVIEW_METALS or not m.node_tree:
            continue
        base, rough, metal = PREVIEW_METALS[lib_name]
        b = m.node_tree.nodes.get("Principled BSDF")
        if "__" not in m.name:
            b.inputs["Base Color"].default_value = rw._lin(base)
            m.diffuse_color = rw._lin(base)[:3] + (1.0,)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal


def preview_color(mat_name, hexcol):
    """Previews only: show a tinted textured library material (M_<Set>__rrggbb) at roughly its in-game value.
    Godot multiplies the set's texture by the tint, which rwlib's 25/75 preview mix doesn't darken."""
    m = rw._resolve_mat(mat_name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rw._lin(hexcol)
    m.diffuse_color = rw._lin(hexcol)[:3] + (m.diffuse_color[3],)
    return m


def stub(name, base, r, h, cut_dir=(1, 0), cut=0.6, m="ReedStub", segs=6):
    """Short cut stalk standing at `base` with a slanted cut top (cut = rise of the slant per unit radius)."""
    o = rw.cylinder(name, r, h, segs, (0, 0, 0), (0, 0, 0), S.mat(m))
    cx, cy = cut_dir
    L = math.hypot(cx, cy) or 1.0
    cx, cy = cx / L, cy / L
    for v in o.data.vertices:
        v.co.z += h / 2
        if v.co.z > h * 0.5:
            v.co.z += cut * (v.co.x * cx + v.co.y * cy) - cut * r
    o.data.update()
    o.location = V(base)
    rw.smooth(o, 40)
    return o


def mushroom(base, az, lean, stem_len, cap_r, cap_h=None, stem_r=None, upright=0.6, spots=5, seed=0, segs=12,
             spot_r=0.2, stem_segs=8, stem_res=2, kick=0.12, dome_rings=(16, 40, 62, 82), name="cap",
             cap_m="GlowcapCap", gill_m="GlowcapGill", stem_m="GlowcapStem", spot_m="GlowcapSpot"):
    """Cartoon toadstool. The stem rises from world point `base` and curves toward azimuth `az` (degrees,
    0 = +X) so its tip ends lean * stem_len out from the vertical; the cap sits on the tip, its axis between the
    stem's end tangent and straight up (upright 0..1). kick (0..1) is how early the stem bends outward (high for
    mushrooms growing out of a vertical surface). Returns the parts (stem, cap with gills, white spots)."""
    rnd = random.Random(seed)
    L = stem_len
    H = cap_h if cap_h is not None else cap_r * 0.62
    sr = stem_r if stem_r is not None else cap_r * 0.3
    pts = [V((0.0, 0.0, -0.05)), V((lean * L * kick, 0.0, L * 0.32)), V((lean * L * (0.38 + kick), 0.0, L * 0.7)),
           V((lean * L, 0.0, L))]
    parts = [pl.sausage(name + "_stem", pts, [sr * 1.3, sr * 1.08, sr * 0.95, sr * 0.9], stem_segs, stem_res,
                        S.mat(stem_m), (False, False), 1, True, 70)]
    T = (pts[-1] - pts[-2]).normalized()
    axis = (T * (1.0 - upright) + UP * upright).normalized()
    tip = pts[-1] - axis * (H * 0.06)
    # cap: underside (gills) from the stem out to the rim lip, then an elliptical dome
    prof = [(0.0, -0.02 * H), (sr * 1.05, -0.03 * H), (cap_r * 0.8, -0.11 * H), (cap_r * 1.0, -0.02 * H)]
    for deg_ in dome_rings:
        ph = math.radians(deg_)
        prof.append((cap_r * math.cos(ph), H * math.sin(ph)))
    prof.append((0.0, H))
    cap = S.lathe(name, prof, segs, (0, 0, 0), cap_m, 55, spin=rnd.uniform(0, 30))
    bpy.context.view_layer.update()
    rw.set_mat_where(cap, S.mat(gill_m), lambda c, nn: nn.z < -0.35)
    R = pl.frame_matrix(axis).to_4x4()
    parts.append(cap)
    sp = []
    for k in range(spots):
        th = 2 * math.pi * (k + rnd.uniform(-0.2, 0.2)) / max(spots, 1) + rnd.uniform(0, 1)
        ph = math.radians(rnd.uniform(28, 64) if k else 80)
        if k == 0:
            th = rnd.uniform(0, 2 * math.pi)
        p = V((cap_r * math.cos(ph) * math.cos(th), cap_r * math.cos(ph) * math.sin(th), H * math.sin(ph)))
        nn = V((math.cos(ph) * math.cos(th) / cap_r, math.cos(ph) * math.sin(th) / cap_r,
                math.sin(ph) / H)).normalized()
        s = cap_r * spot_r * rnd.uniform(0.75, 1.15)
        sp.append(dome(name + "_spot", s, s * 0.3, p, nn, spot_m, 6, 0, 0.5, wall=False))
    xform([cap] + sp, Matrix.Translation(tip) @ R)
    parts += sp
    turn(parts, az, base)
    return parts


def clip_below(o, z=0.0):
    """Cut away everything below world height z and close the cut (roots and lumps that dip into the ground), so
    the visible bounding box, and therefore S.ground_centre, starts at the real ground line."""
    rw.apply_modifiers(o)
    bpy.context.view_layer.update()
    co = o.matrix_world.inverted() @ V((0.0, 0.0, z))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=co,
                               plane_no=(0.0, 0.0, 1.0), clear_inner=True)
    edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid]
    if edges:
        try:
            bmesh.ops.holes_fill(bm, edges=edges)
        except Exception:
            pass
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


def flower_head(centre, facing, R, rc, n_petals=9, seed=0, cup=0.22, petal_w=None, spin=0.0, sepals=True,
                petal_m="SunBloom", eye_m="SunBloomEye", sepal_m="SunSepal", eye_segs=10, ribbon_res=1):
    """Cartoon daisy / sunflower head: a domed centre disc (radius rc, eye_m), a ring of n_petals cupped petals
    reaching out to radius R (petal_m) and a green sepal cup behind (sepal_m). Built facing +Z, then turned to face
    `facing` and moved to `centre` (the middle of the disc's base). Returns (parts, back point for the stem)."""
    rnd = random.Random(seed)
    w = petal_w if petal_w is not None else 2 * math.pi * R / n_petals * 0.62
    parts = [S.lathe("eye", [(0.0, -0.012), (rc * 1.02, -0.012), (rc * 1.06, 0.006), (rc * 0.84, rc * 0.3),
                             (rc * 0.45, rc * 0.44), (0.0, rc * 0.48)], eye_segs, (0, 0, 0), eye_m, 50)]
    for k in range(n_petals):
        a = math.radians(spin) + 2 * math.pi * (k + rnd.uniform(-0.08, 0.08)) / n_petals
        L = R * rnd.uniform(0.92, 1.06)
        d = V((math.cos(a), math.sin(a), 0.0))
        side = V((-math.sin(a), math.cos(a), 0.0))
        # an oval petal, cupped upward toward its rounded tip
        pts = [d * (rc * 0.55), d * (rc + (L - rc) * 0.3) + V((0, 0, L * cup * 0.12)),
               d * (rc + (L - rc) * 0.62) + V((0, 0, L * cup * 0.45)), d * (rc + (L - rc) * 0.88) + V((0, 0, L * cup * 0.8)),
               d * L + V((0, 0, L * cup))]
        parts.append(ribbon("petal", pts, [w * 0.4, w * 0.85, w, w * 0.8, w * 0.35], side, petal_m, keel=0.1,
                            thick=0.012, res=ribbon_res, tri=True))
    if sepals:
        parts.append(S.lathe("sepal", [(0.0, -0.06), (rc * 0.45, -0.055), (rc * 0.95, -0.018), (rc * 0.5, 0.0)], 7,
                             (0, 0, 0), sepal_m, 50))
    R3 = pl.frame_matrix(facing).to_4x4()
    xform(parts, Matrix.Translation(V(centre)) @ R3)
    back = V(centre) - V(facing).normalized() * 0.07
    return parts, back


def rosette_leaf(az, r0, r1, z0, zpeak, ztip, width, m="Leaf", seed=0, droop=0.6, res=1, keel=0.1):
    """Big broad leaf for a leafy clump: rises from radius r0 / height z0 at azimuth az (degrees), arches up to
    zpeak and droops to its pointed tip at radius r1 / height ztip. The blade lies flat-ish (its width across the
    azimuth) with a raised midrib."""
    rnd = random.Random(seed)
    a = math.radians(az + rnd.uniform(-4, 4))
    d = V((math.cos(a), math.sin(a), 0.0))
    side = V((-math.sin(a), math.cos(a), 0.0))
    pts = [d * r0 + V((0, 0, z0)), d * (r0 + (r1 - r0) * 0.3) + V((0, 0, zpeak * 0.92)),
           d * (r0 + (r1 - r0) * 0.58) + V((0, 0, zpeak)),
           d * (r0 + (r1 - r0) * 0.84) + V((0, 0, zpeak - (zpeak - ztip) * droop)),
           d * (r0 + (r1 - r0) * 0.96) + V((0, 0, ztip + (zpeak - ztip) * 0.05)), d * r1 + V((0, 0, ztip))]
    ws = [width * 0.3, width * 0.85, width, width * 0.82, width * 0.42, 0.0]   # broad, with a rounded point
    return ribbon("leaf", pts, ws, side, m, keel=keel, thick=0.014, res=res)


def join_harvest(parts, origin, base_obj, name="Harvest", smooth=None):
    """Join the gathered parts into ONE object named `name` with its origin at `origin` (world), parented to
    the base object (keeping its world transform)."""
    h = rw.join([p for p in parts if p is not None], name, origin=tuple(origin))
    if smooth:
        rw.smooth(h, smooth)
    pl.parent_keep(h, base_obj)
    return h


# --------------------------------------------------------------------------------------
# Finishing and QA
# --------------------------------------------------------------------------------------

def ground_centre_on(ref, mains=()):
    """Like stationlib.ground_centre, but centres X/Y on the bounding box of `ref` (e.g. a plant's mud base) instead
    of the whole model, so lopsided foliage doesn't pull the origin off the plant's axis; with ref=None X/Y stay as
    built (for models built around their axis at the world origin). Z: the lowest visible point goes to 0."""
    bpy.context.view_layer.update()
    mn, _ = rw.bounds()
    if ref is None:
        shift = V((0.0, 0.0, mn.z))
    else:
        rmn, rmx = rw.bounds([ref])
        shift = V(((rmn.x + rmx.x) / 2, (rmn.y + rmx.y) / 2, mn.z))
    for o in pl.roots():
        o.location -= shift
    bpy.context.view_layer.update()
    for o in mains:
        rw.set_origin(o, (0, 0, 0))
    bpy.context.view_layer.update()
    return shift


def report_harvest(asset, base_obj, harvest, origin_note):
    """RWREPORT lines for the gathering-node contract: Harvest name, parent, origin, clean transform."""
    bpy.context.view_layer.update()
    p = harvest.matrix_world.translation
    clean = all(abs(a) < 1e-6 for a in harvest.rotation_euler) and all(abs(s - 1) < 1e-6 for s in harvest.scale)
    print("RWREPORT   Harvest: name=%s parent=%s origin=(%.3f, %.3f, %.3f) [%s] clean_transform=%s tris=%d" % (
        harvest.name, harvest.parent.name if harvest.parent else "-", p.x, p.y, p.z, origin_note, clean,
        rw.tri_count([harvest])))
    print("RWREPORT   Base: name=%s origin=(%.3f, %.3f, %.3f) tris=%d" % (
        base_obj.name, *base_obj.matrix_world.translation, rw.tri_count([base_obj])))


def qa_closeup(asset, tag, direction, target=None, radius=None, size=640, fov=35.0):
    """QA only: render from a custom direction (looking at `target` from far out along `direction`, framing a sphere
    of `radius`) to /tmp/rwqa/<asset>_<tag>.png, with the same lights and outline as the previews."""
    os.makedirs(S.QA_DIR, exist_ok=True)
    mn, mx = rw.bounds()
    target = V(target) if target is not None else (mn + mx) / 2
    radius = radius if radius is not None else (mx - mn).length / 2
    rw._setup_render(size, False, True)
    cd = bpy.data.cameras.new("QA_Cam")
    cd.lens_unit = 'FOV'
    cd.angle = math.radians(fov)
    cam = bpy.data.objects.new("QA_Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = target + V(direction).normalized() * (radius / math.sin(math.radians(fov) / 2) * 1.08)
    cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    temp = [cam]
    for nm, energy, col, rot in (("QA_Key", 3.2, (1, 1, 1), (50, -10, -35)), ("QA_Fill", 0.8, (0.75, 0.82, 1.0), (70, 0, 150))):
        lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        lo.data.energy = energy
        lo.data.color = col
        lo.rotation_euler = tuple(math.radians(a) for a in rot)
        bpy.context.scene.collection.objects.link(lo)
        temp.append(lo)
    path = os.path.join(S.QA_DIR, "%s_%s.png" % (asset, tag))
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in temp:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(d, bpy.types.Camera):
            bpy.data.cameras.remove(d)
        else:
            bpy.data.lights.remove(d)
    print("RWREPORT   QA rendered", path)
    return path


def finish_env(asset, size, budget, nodes=(), height_tol=0.12, preview_glows=None):
    """Like stationlib.finish (E.check + node report + rw.finish steps: world-scale UVs, .blend, .glb, report,
    previews), but `preview_glows` {material: (base_hex, emission_hex, strength)} is applied AFTER the .blend and
    .glb are written, for the preview renders only. AgX washes bright flat glows toward white, while the game
    (Filmic, white 6, bloom) keeps their hue; flat accent glows are converted by Godot from the .glb values, so they
    must not be changed before the export (library M_* materials are swapped by name and can be tweaked any time)."""
    E.check(asset, size, budget, height_tol=height_tol)
    S.node_report(asset, nodes)
    rw.uv_all(2.0)
    blend_dir = os.path.join(rw.ART, "blender", S.CAT)
    os.makedirs(blend_dir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, asset + ".blend"))
    rw.export_glb(os.path.join(rw.ASSETS, "models", S.CAT, asset + ".glb"))
    rw.report(asset)
    preview_metals()
    for name, (base_hex, emit_hex, strength) in (preview_glows or {}).items():
        if bpy.data.materials.get(name) is not None or name.startswith("M_"):
            S.preview_glow(name, base_hex, emit_hex, strength)
    for v in E.previews():
        rw.render_view(os.path.join(rw.ART, "previews", S.CAT, "%s_%s.png" % (asset, v)), v)


def finish_node(asset, size, budget, base_obj, harvest, origin_note, height_tol=0.12, qa_views=("front34",),
                preview_glows=None):
    """Report, then finish_env (check + node report + .blend, .glb, previews). With RW_QA=1 it also renders the
    node with Harvest shrunk to 0.05 (/tmp/rwqa/<asset>_harvested_<view>.png)."""
    report_harvest(asset, base_obj, harvest, origin_note)
    finish_env(asset, size, budget, (base_obj.name, "Harvest"), height_tol, preview_glows)
    if S.qa_on():
        S.qa_harvested(asset, harvest, 0.05, qa_views)
        extra = os.environ.get("RW_QA_VIEWS")
        if extra:
            for v in extra.split(","):
                S.qa_render(asset, "full", v)
        qa_env_closeups(asset)


def qa_env_closeups(asset):
    """RW_QA_CLOSE="tag:dx,dy,dz:tx,ty,tz:radius|..." renders close-ups with qa_closeup (QA only)."""
    spec = os.environ.get("RW_QA_CLOSE")
    if not spec:
        return
    for item in spec.split("|"):
        f = item.split(":")
        d = tuple(float(x) for x in f[1].split(","))
        t = tuple(float(x) for x in f[2].split(",")) if len(f) > 2 and f[2] else None
        r = float(f[3]) if len(f) > 3 and f[3] else None
        qa_closeup(asset, f[0], d, t, r)
