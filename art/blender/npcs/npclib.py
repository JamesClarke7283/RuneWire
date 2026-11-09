"""npclib: shared helpers for the Batch B NPC generators (art/blender/npcs/npc_*.py).

Builds on charlib (art/blender/enemies/charlib.py, read-only here) and rwlib (never edited).
Same conventions: metres, +Z up, the front faces -Y, a character's LEFT is +X, angles in degrees.

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import npclib as nl
    rw, cl, V = nl.rw, nl.cl, nl.V

Rig contract (ASSET_SPEC "NPCs"; animated by scripts/npcs/npc.gd):
    Body  (pivot at the hips; legs are part of it; the model origin is at the feet)
      Head  (pivot at the neck)      yaw up to +-63 deg, pitch +-23 deg
      ArmL  (pivot at the shoulder)  swings ~52 deg forward, ~23 deg back, ~11 deg outward
      ArmR
Joint rules used by every NPC here:
  * each arm owns a ball centred exactly on its pivot, sunk into the torso, so any rotation keeps
    the shoulder closed;
  * the neck is part of Body and its top sits inside the head volume; the Head pivot is on the
    neck axis inside the head, so yaw and pitch never open a gap;
  * things that hang onto the torso (long braids, capes) belong to Body and tuck under the head.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, ".."), os.path.join(HERE, "..", "enemies")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402

V = Vector
CAT = "npcs"

try:  # keep report lines even if a busy machine OOM-kills the job mid-render
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


# ======================================================================================
# Small helpers
# ======================================================================================

def rot_to(direction, spin=0.0):
    """3x3 rotation taking local +Z to `direction` (then spun about it by `spin` degrees)."""
    R = V((0, 0, 1)).rotation_difference(V(direction).normalized()).to_matrix()
    if spin:
        R = R @ Matrix.Rotation(math.radians(spin), 3, 'Z')
    return R


def mirror_x(p):
    return V((-p[0], p[1], p[2]))


def polyline_resample(pts, count):
    """`count` points evenly spaced by arc length along a polyline."""
    P = [V(p) for p in pts]
    seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]
    total = sum(seg)
    out = []
    for k in range(count):
        d = total * k / max(1, count - 1)
        i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]
            i += 1
        t = 0.0 if seg[i] < 1e-9 else min(1.0, d / seg[i])
        out.append(P[i].lerp(P[i + 1], t))
    return out


def smooth_path(ctrl, n=12):
    """Catmull-Rom path through control points (n samples)."""
    P = [V(p) for p in ctrl]
    if len(P) == 2:
        return [P[0].lerp(P[1], k / (n - 1)) for k in range(n)]
    out = []
    segs = len(P) - 1
    for k in range(n):
        u = k / (n - 1) * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0 = P[i - 1] if i > 0 else 2 * P[0] - P[1]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < len(P) else 2 * P[-1] - P[-2]
        out.append(_cr(p0, p1, p2, p3, t))
    return out


def _cr(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3)


# ======================================================================================
# Body profiles and lofted clothing
# ======================================================================================

class Profile:
    """A smooth stack of horizontal ellipses [(z, rx, ry, cy), ...] (Catmull-Rom between levels).
    Angles follow charlib.ring: 0 = +X (left), 90 = +Y (back), 270 = -Y (front)."""

    def __init__(self, levels, cx=0.0):
        self.L = sorted([tuple(l) for l in levels], key=lambda l: l[0])
        self.cx = cx

    def at(self, z):
        L = self.L
        if z <= L[0][0]:
            return tuple(L[0][1:])
        if z >= L[-1][0]:
            return tuple(L[-1][1:])
        i = 0
        while i < len(L) - 2 and z > L[i + 1][0]:
            i += 1
        t = (z - L[i][0]) / (L[i + 1][0] - L[i][0])
        p0, p1, p2, p3 = L[max(i - 1, 0)], L[i], L[i + 1], L[min(i + 2, len(L) - 1)]
        return tuple(_cr(p0[k], p1[k], p2[k], p3[k], t) for k in (1, 2, 3))

    def point(self, z, a, off=0.0, rm=1.0):
        rx, ry, cy = self.at(z)
        r = math.radians(a)
        return V((self.cx + (rx * rm + off) * math.cos(r), cy + (ry * rm + off) * math.sin(r), z))

    def front_y(self, z, x=0.0, off=0.0):
        """y of the front surface at height z and lateral position x."""
        rx, ry, cy = self.at(z)
        u = min(0.999, abs(x - self.cx) / (rx + off))
        return cy - (ry + off) * math.sqrt(1 - u * u)

    def surface(self, name, z0, z1, steps=8, n=24, off=0.0, mat=None, a0=0.0, a1=360.0, rmod=None, zmod=None,
                caps=(True, True), zs=None, smooth=True):
        """Loft of the profile between z0 and z1 (closed tube, or an open arc a0..a1).
        rmod(a_deg, z) -> radius multiplier (folds); zmod(a_deg, z) -> z offset (hems)."""
        zs = zs or [z0 + (z1 - z0) * k / steps for k in range(steps + 1)]
        full = (a1 - a0) >= 359.99
        cnt = n if full else n + 1
        rings = []
        for z in zs:
            rx, ry, cy = self.at(z)
            ring = []
            for k in range(cnt):
                a = a0 + (a1 - a0) * k / n
                m = rmod(a, z) if rmod else 1.0
                dz = zmod(a, z) if zmod else 0.0
                r = math.radians(a)
                ring.append(V((self.cx + (rx * m + off) * math.cos(r), cy + (ry * m + off) * math.sin(r), z + dz)))
            rings.append(ring)
        return cl.skin(name, rings, mat, caps[0] and full, caps[1] and full, smooth, None, closed=full)


def arc_panel(name, prof, zs, half_fn, center=270.0, n=12, off=0.02, mat=None, zmod=None, rm=1.0):
    """Open surface wrapped on a profile (aprons, bibs, tabards): at each height z in `zs` it spans
    center +- half_fn(z) degrees. zmod(a_deg, z, k) -> z offset (rounded hem corners)."""
    rings = []
    for z in zs:
        h = half_fn(z) if callable(half_fn) else half_fn
        ring = []
        for k in range(n + 1):
            a = center - h + 2 * h * k / n
            p = prof.point(z, a, off, rm)
            if zmod:
                p.z += zmod(a, z, k)
            ring.append(p)
        rings.append(ring)
    return cl.skin(name, rings, mat, False, False, True, None, closed=False)


def ring_loft(name, levels, n=24, mat=None, caps=(True, True), rmod=None, zmod=None, smooth=True):
    """Loft through explicit ellipses [(z, rx, ry, cx, cy), ...] (no interpolation)."""
    rings = []
    for (z, rx, ry, cx, cy) in levels:
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            m = rmod(math.degrees(a), z) if rmod else 1.0
            dz = zmod(math.degrees(a), z) if zmod else 0.0
            ring.append(V((cx + rx * m * math.cos(a), cy + ry * m * math.sin(a), z + dz)))
        rings.append(ring)
    return cl.skin(name, rings, mat, caps[0], caps[1], smooth, None)


def scale_parts(parts, pivot, k, shift=(0, 0, 0)):
    """Uniformly scale world-space part meshes about `pivot` by k, then move them by `shift`."""
    M = Matrix.Translation(V(pivot) + V(shift)) @ Matrix.Scale(k, 4) @ Matrix.Translation(-V(pivot))
    for o in cl.flatten(parts):
        o.data.transform(o.matrix_world.inverted() @ M @ o.matrix_world)
        o.data.update()
    return parts


def thicken(o, t=0.015, inner_mat=None, offset=-1.0):
    """Solidify an open cloth/leather surface (applied when the node is joined)."""
    return cl.cloth_shell(o, t, inner_mat, offset)


def lathe_z(name, profile, center=(0, 0, 0), segs=24, mat=None, rot=None, smooth_angle=50, caps=(True, True)):
    """Revolve [(r, h), ...] about local Z, then rotate (3x3) and move to `center` (world space)."""
    o = rw.lathe(name, profile, segs, mat=mat, cap_bottom=caps[0], cap_top=caps[1], smooth_angle=smooth_angle)
    M = Matrix.Translation(V(center)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    o.data.transform(M)
    o.data.update()
    return o


def disc(name, center, r, thick, axis=(0, 0, 1), mat=None, segs=24, bevel=0.35):
    b = min(r, thick) * bevel
    prof = [(0.0, -thick / 2), (r - b, -thick / 2), (r, -thick / 2 + b), (r, thick / 2 - b), (r - b, thick / 2),
            (0.0, thick / 2)]
    return lathe_z(name, prof, center, segs, mat, rot_to(axis), 50, (False, False))


def star(name, center, normal, up, r_out, r_in=None, depth=0.012, points=5, mat=None, bevel=0.0):
    """Five-point (cartoon) star lying on a surface with the given normal; `up` orients a point."""
    r_in = r_in if r_in is not None else r_out * 0.48
    pts = []
    for k in range(points * 2):
        a = math.pi / 2 + math.pi * k / points
        rr = r_out if k % 2 == 0 else r_in
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    o = rw.extrude_poly(name, pts, depth, mat=mat, bevel=bevel)
    n = V(normal).normalized()
    u = V(up)
    u = (u - n * u.dot(n)).normalized()
    x = u.cross(n)
    R = Matrix((x, u, n)).transposed()
    o.data.transform(Matrix.Translation(V(center)) @ R.to_4x4())
    o.data.update()
    rw.smooth(o, 30)
    return o


# ======================================================================================
# Faces
# ======================================================================================

def _smax(a, b, k):
    """Polynomial smooth maximum (C1; equals max(a, b) once |a - b| >= k)."""
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k * 0.25


def head_shape(name, C, R, C2=None, R2=None, segs=24, rings=12, mat="M_Skin", k=0.03):
    """One smooth head mesh: the skull ellipsoid (C, R) smoothly unioned with an optional jaw/jowl
    ellipsoid (C2, R2). Two separate intersecting ellipsoids draw a contour line across the cheeks in
    3/4 views (it reads like a moustache); this single surface has no crease. Face features can keep
    using cl.head_point() on either ellipsoid, because the union matches each of them away from the
    k-wide blend."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    C = V(C)
    for v in bm.verts:
        d = v.co.normalized()
        t = 1.0 / math.sqrt((d.x / R[0]) ** 2 + (d.y / R[1]) ** 2 + (d.z / R[2]) ** 2)
        if C2 is not None:
            o = V(((C.x - C2[0]) / R2[0], (C.y - C2[1]) / R2[1], (C.z - C2[2]) / R2[2]))
            w = V((d.x / R2[0], d.y / R2[1], d.z / R2[2]))
            A, B, Cq = w.dot(w), o.dot(w), o.dot(o) - 1.0
            D = B * B - A * Cq
            if D > 0:
                t2 = (-B + math.sqrt(D)) / A
                if t2 > 0:
                    t = _smax(t, t2, k)
        v.co = C + d * t
    return cl._new_obj(name, bm, mat, True)


def eye(c, r, f, shape=(0.8, 0.55, 1.0), iris=None, iris_r=0.62, pupil_r=0.36, segs=12, lid=0.0, lid_mat=None,
        lid_tilt=0.0, lower=0.0, lower_mat=None, look=(0.0, 0.0), shine=(0.28, 0.34), name="eye"):
    """Economical cartoon eye (~300 tris): white ellipsoid, iris and pupil as shallow domed caps that
    follow the white's curvature, a highlight dot, optional upper/lower lids (cover fraction 0..1).
    f = look direction, look = (x, z) pupil offset as a fraction of the eye radius."""
    rw.flat("EyeWhite", "fbf8f0", 0.35)
    rw.flat("Pupil", "1b1622", 0.3)
    rw.glow("EyeShine", "ffffff", 1.2)
    F = cl.frame(f, (0, 0, 1))
    c = V(c)
    rx, ry, rz = r * shape[0], r * shape[1], r * shape[2]
    parts = [cl.ellipsoid(name + "_white", c, (rx, ry, rz), segs, max(6, segs // 2 + 1), "EyeWhite", F)]
    ax = math.asin(max(-0.9, min(0.9, look[0])))
    az = math.asin(max(-0.9, min(0.9, look[1])))
    Fz = F @ Matrix.Rotation(ax, 3, 'Z') @ Matrix.Rotation(-az, 3, 'X') @ Matrix.Rotation(math.radians(90), 3, 'X')
    if iris:
        cov = (1 - math.sqrt(1 - iris_r ** 2)) / 2
        parts.append(cl.dome(name + "_iris", c, (rx * 1.02, rz * 1.02, ry * 1.035), Fz, cov, segs, 2, iris))
    cov = (1 - math.sqrt(1 - pupil_r ** 2)) / 2
    parts.append(cl.dome(name + "_pupil", c, (rx * 1.035, rz * 1.035, ry * 1.065), Fz, cov, max(8, segs - 2), 1,
                         "Pupil"))
    sx, sz = shine
    loc = V((sx, -math.sqrt(max(0.05, 1 - sx * sx - sz * sz)), sz))
    Flook = F @ Matrix.Rotation(ax, 3, 'Z') @ Matrix.Rotation(-az, 3, 'X')
    sp = c + Flook @ V((loc.x * rx * 1.04, loc.y * ry * 1.1, loc.z * rz * 1.04))
    parts.append(cl.ellipsoid(name + "_shine", sp, (r * 0.14, r * 0.07, r * 0.14), 6, 3, "EyeShine", Flook))
    if lid:
        parts.append(cl.dome(name + "_lid", c, (rx * 1.1, ry * 1.2, rz * 1.08), F, lid, segs, 3, lid_mat,
                             tilt=lid_tilt))
    if lower:
        Fl = F @ Matrix.Rotation(math.pi, 3, 'Y')
        parts.append(cl.dome(name + "_llid", c, (rx * 1.08, ry * 1.14, rz * 1.06), Fl, lower, segs, 2,
                             lower_mat or lid_mat, tilt=-lid_tilt * 0.5))
    return parts


def eye_pair(C, R, dx, z, r, iris=None, fwd=0.35, embed=0.42, shape=(0.8, 0.5, 1.0), lid=0.0, lid_mat=None,
             lid_tilt=0.0, lower=0.0, segs=12, iris_r=0.62, pupil_r=0.36, look=(0.0, 0.0), toe=0.0,
             shine=(0.28, 0.34), lower_mat=None):
    """Two cartoon eyes on the front of an ellipsoid head (centre C, radii R). `fwd` blends the eye
    direction from the head normal (0) toward straight ahead (1). lid_tilt > 0 droops the outer corners;
    look = (x, z) pupil offset for both eyes, toe > 0 pulls both pupils toward the nose."""
    parts = []
    for s in (1, -1):
        p = cl.head_point(C, R, C[0] + s * dx, z, 0.0)
        n = cl.head_normal(C, R, p)
        f = (n * (1 - fwd) + V((0, -1, 0)) * fwd).normalized()
        p = p - f * (r * shape[1] * embed)
        parts += eye(p, r, f, shape, iris, iris_r, pupil_r, segs, lid, lid_mat, lid_tilt * s, lower, lower_mat,
                     (look[0] - toe * s, look[1]), (shine[0], shine[1]))
    return parts


def brow(name, p_in, p_out, r=0.018, lift=0.012, mat=None, flat=0.55, steps=6, segs=6):
    """Arched eyebrow, inner end fat, outer end tapered (cheaper than charlib.brow)."""
    p_in, p_out = V(p_in), V(p_out)
    mid = (p_in + p_out) / 2 + V((0, 0, lift))
    pts = cl.bezier(p_in, mid, p_out, steps)
    rad = [r * (0.8 + 0.3 * math.sin(math.pi * i / (steps - 1))) for i in range(steps)]
    rad[-1] *= 0.55
    return cl.sweep(name, pts, rad, segs, mat, scale=(1.0, flat), up=(0, 0, 1))


def brow_pair(C, R, dx_in, dx_out, z_in, z_out, r=0.016, lift=0.012, mat=None, out=0.006, flat=0.55):
    parts = []
    for s in (1, -1):
        a = cl.head_point(C, R, C[0] + s * dx_in, z_in, out)
        b = cl.head_point(C, R, C[0] + s * dx_out, z_out, out)
        parts.append(brow("brow", a, b, r, lift, mat, flat))
    return parts


def nose(C, R, z, size=(0.035, 0.03, 0.03), out=0.0, mat="M_Skin", x=0.0, segs=10):
    p = cl.head_point(C, R, C[0] + x, z, 0.0) + V((0, -size[1] * 0.35 - out, 0))
    return cl.ellipsoid("nose", p, size, segs, 6, mat)


def cheeks(C, R, dx, z, r=0.03, mat=None, sink=0.55):
    mat = mat or rw.flat("Blush", "f08a8a", 0.7)
    parts = []
    for s in (1, -1):
        p = cl.head_point(C, R, C[0] + s * dx, z, 0.0)
        n = cl.head_normal(C, R, p)
        parts.append(cl.ellipsoid("cheek", p - n * (r * 0.32 * sink), (r * 1.2, r * 0.45, r * 0.85), 8, 4, mat,
                                  cl.frame(n)))
    return parts


def ears(C, R, z, size=(0.03, 0.045, 0.06), mat="M_Skin", inset=0.25, back=0.0, tilt=12.0, segs=10):
    parts = []
    for s in (1, -1):
        p = V((C[0] + s * (R[0] - size[0] * inset), C[1] + back, z))
        Rm = Matrix.Rotation(math.radians(-tilt * s), 3, 'Z')
        parts.append(cl.ellipsoid("ear", p, size, segs, 6, mat, Rm))
    return parts


def smile(C, R, half_w, z, curve=0.02, r=0.011, steps=7, embed=0.3, segs=6, flat=0.6, mat="Mouth"):
    """Closed smile line along the face (curve > 0: corners up)."""
    rw.flat("Mouth", "5a2430", 0.6)
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        x = C[0] - half_w + 2 * half_w * t
        pts.append(cl.head_point(C, R, x, z + curve * (2 * t - 1) ** 2, -r * embed))
    rad = [r * (0.55 + 0.45 * math.sin(math.pi * i / (steps - 1))) for i in range(steps)]
    return cl.sweep("mouth", pts, rad, segs, mat, scale=(1.0, flat), up=(0, 0, 1))


def face_patch(name, C, R, u0, u1, v0, v1, half_w, z, depth, curve, off, mat, nu=8, nv=2):
    """Thin patch lying on an ellipsoid face (follows its curvature) inside a 'D' grin outline:
    u in -1..1 across the mouth, v from the lip line (0) to the bottom of the grin (1)."""
    bm = bmesh.new()
    rows = []
    for j in range(nv + 1):
        v = v0 + (v1 - v0) * j / nv
        row = []
        for i in range(nu + 1):
            u = u0 + (u1 - u0) * i / nu
            top = z + curve * u * u
            h = depth * math.sqrt(max(0.0, 1 - u * u))
            row.append(bm.verts.new(cl.head_point(C, R, C[0] + u * half_w, top - h * v, off)))
        rows.append(row)
    for j in range(nv):
        for i in range(nu):
            q = (rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i])
            if len(set(q)) >= 3:
                bm.faces.new(q)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    cen = V(C)
    if sum(f.normal.dot(f.calc_center_median() - cen) for f in bm.faces) < 0:
        for f in bm.faces:
            f.normal_flip()
    return cl._new_obj(name, bm, mat, True)


def open_smile(C, R, half_w, z, depth=0.045, curve=0.012, tongue=True, teeth=True, nu=8, inside=None):
    """Open 'D' grin drawn on the face as thin curved patches (dark mouth, tongue, upper teeth),
    so it follows the head's curvature and never pokes out of the cheeks. `inside` = (name, hex)
    overrides the mouth-interior colour."""
    mouth = rw.flat(*inside, 0.6) if inside else rw.flat("MouthDark", "6a1a30", 0.6)
    parts = [face_patch("grin", C, R, -1.0, 1.0, 0.0, 1.0, half_w, z, depth, curve, 0.003, mouth, nu, 3)]
    if tongue:
        parts.append(face_patch("tongue", C, R, -0.66, 0.66, 0.5, 0.96, half_w, z, depth, curve, 0.0042,
                                rw.flat("Tongue", "ec6f7c", 0.6), 6, 1))
    if teeth:
        parts.append(face_patch("teeth", C, R, -0.8, 0.8, 0.0, 0.3, half_w, z, depth, curve, 0.0045,
                                rw.flat("Teeth", "fbf6ea", 0.4), 6, 1))
    return parts


# ======================================================================================
# Hair
# ======================================================================================

def braid(name, ctrl, r0, r1, lumps, mat, segs=10, rings=6, tilt=24.0, squash=0.78, stretch=1.45):
    """Cartoon plait: overlapping tilted lumps along a smooth path (r0 at the start, r1 at the end)."""
    path = smooth_path(ctrl, 40)
    P = polyline_resample(path, lumps)
    parts = []
    for i, p in enumerate(P):
        t = i / max(1, lumps - 1)
        r = r0 + (r1 - r0) * t
        tan = (P[min(i + 1, lumps - 1)] - P[max(i - 1, 0)]).normalized()
        Rm = rot_to(tan) @ Matrix.Rotation(math.radians(tilt if i % 2 else -tilt), 3, 'Y')
        parts.append(cl.ellipsoid(name, p, (r, r * squash, r * stretch), segs, rings, mat, Rm))
    return parts


# ======================================================================================
# Hands, arms, legs, boots
# ======================================================================================

def hand(name, W, down, palm, thumb, s=0.11, mat="M_Skin", fingers=3, curl=0.45, spread=1.0, segs=7, chunky=1.0):
    """Chunky cartoon mitten hand (~350 tris): palm + sausage fingers + thumb.
    down = wrist->fingertip direction, palm = palm normal, thumb = side the thumb is on."""
    d, n, t = cl._hand_axes(down, palm, thumb)
    W = V(W)
    M = cl.axes_matrix(t, n, d)
    parts = [cl.ellipsoid(name + "_palm", W + d * (0.42 * s), (0.44 * s * chunky, 0.25 * s, 0.46 * s), 10, 6,
                          mat, M)]
    fr = 0.14 * s * chunky
    for k in range(fingers):
        off = (k - (fingers - 1) / 2) * (0.29 if fingers <= 3 else 0.24) * s * spread
        b = W + d * (0.68 * s) + t * off
        tip = b + d * (0.32 * s) + n * (0.2 * s * curl) - t * (off * 0.12)
        parts.append(cl.capsule(name + "_f%d" % k, b, tip, fr, fr * 0.92, segs, 2, mat))
    b = W + d * (0.3 * s) + t * (0.34 * s) + n * (0.08 * s)
    tip = b + t * (0.18 * s) + d * (0.24 * s) + n * (0.14 * s)
    parts.append(cl.capsule(name + "_thumb", b, tip, fr * 1.02, fr * 0.95, segs, 2, mat))
    return parts


class ArmInfo:
    def __init__(self, S, E, W, d1, d2, side):
        self.S, self.E, self.W, self.d1, self.d2, self.side = S, E, W, d1, d2, side


def arm_frame(side, S, L1, L2, spread=9.0, bend=15.0, swing=0.0):
    d1, d2 = cl.arm_dirs(side, spread, bend, swing)
    S = V(S)
    E = S + d1 * L1
    W = E + d2 * L2
    return ArmInfo(S, E, W, d1, d2, side)


def soft_arm(side, S, L1=0.26, L2=0.24, r=(0.07, 0.058, 0.047), spread=9.0, bend=15.0, sleeve="M_Fabric",
             skin="M_Skin", sleeve_end=1.0, cuff_mat=None, cuff=0.018, ball_r=None, hand_s=0.11, fingers=3,
             segs=10, sleeve_r=None, hand_mat=None, swing=0.0, ball_segs=14, rows=2):
    """Hanging fleshy arm as one node: shoulder ball (centred on the pivot), sleeve, elbow,
    forearm, cuff and a mitten hand. sleeve_end: 0 = sleeve stops at the elbow (bare forearm),
    1 = full sleeve to the wrist. sleeve_r = radii of the sleeve tube (defaults to r * ~1.1)."""
    A = arm_frame(side, S, L1, L2, spread, bend, swing)
    S, E, W, d1, d2 = A.S, A.E, A.W, A.d1, A.d2
    r0, r1, r2 = r
    sr = sleeve_r or (r0 * 1.06, r1 * 1.12, r2 * 1.18)
    parts = [cl.sphere("shoulder", S, ball_r or r0 * 1.12, ball_segs, ball_segs // 2, sleeve)]
    ts = [k / rows for k in range(rows + 1)]
    parts.append(cl.sweep("upper", [S.lerp(E + d1 * 0.01, t) for t in ts], [sr[0] + (sr[1] - sr[0]) * t for t in ts],
                          segs, sleeve, cap_start=False, cap_end=False))
    parts.append(cl.sphere("elbow", E, sr[1] * 0.98, segs, 5, sleeve))
    fore_end = E.lerp(W, max(0.0, min(1.0, sleeve_end)))
    if sleeve_end > 0.05:
        parts.append(cl.sweep("fore_sleeve", [E, fore_end], [sr[1], sr[2] if sleeve_end >= 0.999 else
                                                              sr[1] + (sr[2] - sr[1]) * sleeve_end],
                              segs, sleeve, cap_start=False))
        cuff_at = fore_end
        cuff_rad = sr[2] if sleeve_end >= 0.999 else (sr[1] + (sr[2] - sr[1]) * sleeve_end)
    else:
        cuff_at = E + d2 * 0.035
        cuff_rad = sr[1] * 1.02
    if sleeve_end < 0.999:
        parts.append(cl.sweep("forearm", [E, W + d2 * 0.01], [r1 * 0.95, r2], segs, skin, cap_start=False))
    if cuff and cuff_mat is not None:
        parts.append(cl.torus("cuff", cuff_at, cuff_rad * 0.98, cuff, rot_to(d2), segs + 4, 5, cuff_mat))
    hd = (d2 + V((0, -0.06, 0))).normalized()
    parts += hand("hand", W - d2 * 0.01, hd, V((-side, 0.0, 0.0)), V((0, -1, 0)), hand_s, hand_mat or skin, fingers)
    return parts, A


def leg(side, hip, ankle, r0, r1, mat, segs=12, knee=None, bulge=1.0):
    hip, ankle = V(hip), V(ankle)
    mid = hip.lerp(ankle, 0.5) + (V(knee) if knee else V())
    rm = (r0 + r1) / 2 * bulge
    return cl.sweep("leg", [hip, mid, ankle], [r0, rm, r1], segs, mat, cap_start=False)


def boot(x, y, mat="M_Leather", sole_mat="M_Rubber", h=0.2, r=0.085, toe=0.15, width=1.0, toe_cap=None,
         lip_mat=None, segs=14, lip=0.03):
    """Chunky cartoon boot standing on z = 0 with the ankle at (x, y): lathed shaft with a rolled
    lip, a round toe, a sole, and an optional toe cap (~450 tris)."""
    prof = [(r * 0.96, 0.035), (r * 1.0, h * 0.45), (r * 1.04, h - lip * 0.5)]
    parts = [lathe_z("boot_shaft", prof, (x, y + 0.01, 0), segs, mat, None, 50, (True, False))]
    parts.append(lathe_z("boot_lip", [(r * 1.02, h - lip * 0.6), (r * 1.13, h - lip * 0.2), (r * 1.1, h + lip * 0.45),
                                      (r * 0.8, h + lip * 0.5)],
                         (x, y + 0.01, 0), segs, lip_mat or mat, None, 50, (False, False)))
    parts.append(cl.ellipsoid("boot_foot", (x, y - toe * 0.42, 0.074), (r * 1.02 * width, toe, 0.074), segs, 6, mat))
    parts.append(cl.ellipsoid("boot_sole", (x, y - toe * 0.36, 0.026), (r * 1.1 * width, toe * 1.1, 0.026), segs, 4,
                              sole_mat))
    if toe_cap:
        M = cl.axes_matrix(V((1, 0, 0)), V((0, 0, 1)), V((0, -1, 0)))
        parts.append(cl.dome("toe_cap", (x, y - toe * 0.42, 0.075), (r * 1.08 * width, 0.074, toe * 1.04), M, 0.2,
                             12, 2, toe_cap))
    return parts


# ======================================================================================
# Assembly
# ======================================================================================

def assemble(body_parts, hip, head_parts, neck, arm_l_parts, sh_l, arm_r_parts, sh_r):
    """Create the four contract nodes; returns (body, head, arm_l, arm_r)."""
    body = cl.node("Body", body_parts, V(hip))
    head = cl.node("Head", head_parts, V(neck), body)
    arm_l = cl.node("ArmL", arm_l_parts, V(sh_l), body)
    arm_r = cl.node("ArmR", arm_r_parts, V(sh_r), body)
    bpy.context.view_layer.update()
    return body, head, arm_l, arm_r


# ======================================================================================
# QA
# ======================================================================================

DEFAULT_POSES = {
    # Blender eulers (deg). Head: X > 0 nods down, Z > 0 turns to its left. Arms: X < 0 swings forward;
    # ArmL Y < 0 / ArmR Y > 0 lifts outward (matches npc.gd's Godot rotations).
    "pose": {"Head": (-18, 0, 55), "ArmL": (-52, -11, 0), "ArmR": (25, 0, 0)},
    "pose2": {"Head": (16, 0, -62), "ArmL": (24, 0, 0), "ArmR": (-52, 11, 0)},
}


def contact_sheet(paths, out, cols=3, tile=420):
    """Paste renders into one PNG grid (QA: fewer, smaller images to inspect)."""
    import numpy as np
    paths = [p for p in paths if p and os.path.exists(p)]
    rows = (len(paths) + cols - 1) // cols
    W, H = cols * tile, rows * tile
    sheet = np.zeros((H, W, 4), dtype=np.float32)
    sheet[...] = (0.55, 0.57, 0.6, 1.0)
    for i, p in enumerate(paths):
        img = bpy.data.images.load(p, check_existing=False)
        img.scale(tile, tile)
        a = np.empty(tile * tile * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(tile, tile, 4)
        if a[..., 3].min() < 0.99:  # transparent icon: composite over grey
            al = a[..., 3:4]
            a = a * al + np.array([0.55, 0.57, 0.6, 1.0], dtype=np.float32) * (1 - al)
            a[..., 3] = 1.0
        bpy.data.images.remove(img)
        r, c = i // cols, i % cols
        y0 = H - (r + 1) * tile  # Blender images are bottom-up
        sheet[y0:y0 + tile, c * tile:(c + 1) * tile] = a
    im = bpy.data.images.new("rw_sheet", W, H, alpha=True)
    im.pixels.foreach_set(sheet.ravel())
    im.filepath_raw = out
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    print("RWREPORT   sheet", out)
    return out


def script_args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def report(asset, budget_limit=12000):
    cl.report_nodes(["Body", "Head", "ArmL", "ArmR"])
    mn, mx = rw.bounds()
    print("RWNPC %s height %.3f m (z %.3f .. %.3f), width %.3f, depth %.3f" % (
        asset, mx.z - mn.z, mn.z, mx.z, mx.x - mn.x, mx.y - mn.y))
    for o in sorted(bpy.context.scene.objects, key=lambda x: x.name):
        if o.type == 'MESH' and not o.get("rw_helper"):
            print("RWNPC   node %-6s parent %-5s children %s" % (
                o.name, o.parent.name if o.parent else "-", sorted(c.name for c in o.children)))
    cl.budget(budget_limit)
    cl.tri_breakdown()


def qa(asset, poses=None, face=True, sheet=True, views=("front", "side")):
    """Extra QA renders (front/side, test poses with the head and arms rotated ~35-60 deg, a face
    close-up) and a contact sheet. Run inside the build, or later on the saved .blend:
        blender --background art/blender/npcs/<asset>.blend --python art/blender/npcs/npclib.py -- qa <asset>"""
    paths = [cl.preview_path(asset, CAT, "front34"), cl.preview_path(asset, CAT, "back34")]
    if views:
        cl.render_extra(asset, CAT, views)
        paths += [cl.preview_path(asset, CAT, v) for v in views]
    for tag, pose in (poses or DEFAULT_POSES).items():
        cl.render_pose(asset, CAT, pose, tag)
        paths.append(cl.preview_path(asset, CAT, tag))
    if face:
        for tag, view in (("face", "front"), ("face34", "front34")):
            fp = cl.preview_path(asset, CAT, tag)
            rw.render_view(fp, view, 640, objs=[bpy.data.objects["Head"]])
            paths.append(fp)
    if sheet:
        contact_sheet(paths, cl.preview_path(asset, CAT, "sheet"), cols=4, tile=400)


def finish(asset, budget_limit=12000, poses=None, face=True, sheet=True):
    """rw.finish (blend, glb, front34/back34 previews, icon) + node report. The extra QA renders run
    here only when the script gets `-- qa` (memory is tight when other Blender jobs run)."""
    rw.finish(asset, CAT, icon=True)
    report(asset, budget_limit)
    if "qa" in script_args():
        qa(asset, poses, face, sheet)


if __name__ == "__main__":
    _a = script_args()
    if len(_a) >= 2 and _a[0] == "qa":
        report(_a[1])
        qa(_a[1])
