"""glove: the shared chunky cartoon right-hand glove for the first-person viewmodels.

Every vm_*.py script (except vm_gauntlet, which is the hand itself) calls glove.fist() to wrap a brown
leather glove around its handle, plus the blue coat-sleeve cuff behind the wrist. vm_gauntlet reuses
glove.sleeve() so all viewmodels share the same sleeve.

Frame conventions (world space, metres):
  G     grip centre; the viewmodel origin (put it at (0, 0, 0)).
  A     grip axis: runs through the fist from the pinky side to the index/thumb side.
  out   the side the back of the hand faces (for a right hand on a pistol grip: -X, the player's right).
  F     forearm direction from the wrist toward the elbow (+Y and slightly down).
The fingers wrap around A starting at the knuckles (front-right) through `front` = A x out and end on
the far side; the thumb lies along the far (left, +X) side above the fingers.
"""
import math
import os
import sys

from mathutils import Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "parts"))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V
bpy = pl.bpy

LEATHER = "M_Leather"
LEATHER_DARK = "M_Leather__4a2a17"
SLEEVE = "M_Fabric__2f62c9"


def frame(A, out):
    A = V(A).normalized()
    o = V(out)
    o = (o - o.dot(A) * A).normalized()
    fr = A.cross(o).normalized()
    return A, o, fr


def around(G, A, o, fr, h, r, theta_deg):
    """Point at height h along A and radius r around A; theta 0 = out side, 90 = front."""
    t = math.radians(theta_deg)
    return V(G) + A * h + o * (r * math.cos(t)) + fr * (r * math.sin(t))


def oriented_pillow(name, size, centre, x_dir, y_dir, z_dir, e_xy=0.55, e_z=0.55, segs=18, rings=10, mat=LEATHER):
    o = pl.superellipsoid(name, size, (0, 0, 0), e_xy, e_z, segs, rings, mat)
    M = Matrix((V(x_dir).normalized(), V(y_dir).normalized(), V(z_dir).normalized())).transposed()
    o.data.transform(M.to_4x4())
    o.data.update()
    o.location = centre
    return o


def surface_point(obj, start, direction, fallback):
    """First hit of a ray from `start` along `direction` on obj (world space)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(obj, dg)
    inv = obj.matrix_world.inverted()
    d = (inv.to_3x3() @ V(direction)).normalized()
    loc, nrm, idx, dist = bvh.ray_cast(inv @ V(start), d)
    if loc is None:
        return V(fallback), V(direction) * -1
    mw = obj.matrix_world
    return mw @ loc, (mw.to_3x3() @ nrm).normalized()


def sleeve(wrist_end, F, out=(-1, 0, 0), s=1.0, sleeve_len=0.07, buttons=True, flare=True):
    """Leather glove gauntlet flare + blue folded-back coat-sleeve cuff + a short sleeve, along F from
    wrist_end. Returns a list of objects. flare=False skips the leather flare (vm_gauntlet has a bracer)."""
    F = V(F).normalized()
    p0 = V(wrist_end)
    parts = []
    if not flare:
        p0 = p0 - F * (0.05 * s)       # the cuff starts right at wrist_end
    # leather glove flare with a rolled lip
    flare_prof = [(0.036 * s, -0.01 * s), (0.04 * s, 0.0), (0.05 * s, 0.026 * s), (0.058 * s, 0.04 * s),
                  (0.052 * s, 0.046 * s)]
    if flare:
        parts.append(pl.lathe_axis("glove_flare", flare_prof, F, p0, 16, LEATHER, False, False, 50))
        parts.append(rw.torus("glove_lip", 0.056 * s, 0.009 * s, 16, 5, (0, 0, 0), mat=LEATHER_DARK))
        pl.align(parts[-1], F, p0 + F * (0.042 * s))
    # blue sleeve: fat folded cuff then the sleeve tube, closed with a cap at the back
    c0 = p0 + F * (0.05 * s)
    L = sleeve_len * s
    cuff = [(0.05 * s, 0.0), (0.066 * s, 0.004 * s), (0.074 * s, 0.018 * s), (0.075 * s, 0.045 * s),
            (0.07 * s, 0.06 * s), (0.064 * s, 0.064 * s), (0.064 * s, 0.064 * s + L), (0.058 * s, 0.07 * s + L),
            (0.0, 0.07 * s + L)]
    cf = pl.lathe_axis("sleeve", cuff, F, c0, 18, SLEEVE, True, False, 45)
    parts.append(cf)
    if buttons:
        o = V(out)
        o = (o - o.dot(F) * F).normalized()
        up = F.cross(o).normalized()
        for k in (-1, 1):
            d = (o * 0.94 + up * (0.34 * k)).normalized()
            p = c0 + F * (0.032 * s) + d * (0.074 * s)
            parts.append(pl.lathe_axis("button", [(0.011 * s, -0.004 * s), (0.011 * s, 0.002 * s),
                                                  (0.007 * s, 0.006 * s), (0.0, 0.007 * s)], d, p, 8, "M_Brass",
                                       True, True, 60))
    return parts


def fist(A=(0, -0.259, 0.966), out=(-1, 0, 0), F=(0, 1, -0.4), G=(0, 0, 0), s=1.0, wrist_len=0.05,
         sleeve_len=0.035, name="Glove", finger_wrap=1.0, knuckle_bias=0.0, thumb_lift=0.0):
    """Chunky cartoon leather fist gripping a handle along A through G. Returns the joined object
    (origin at the world origin)."""
    A, o, fr = frame(A, out)
    F = V(F).normalized()
    G = V(G)
    parts = []

    # --- fist mass (palm + back of the hand) -----------------------------------------------------------
    mass_c = G + o * (0.016 * s) - fr * (0.012 * s) - A * (0.002 * s)
    mass = oriented_pillow("fist", (0.088 * s, 0.09 * s, 0.15 * s), mass_c, o, fr, A, 0.55, 0.6, 16, 10)
    parts.append(mass)
    # thenar (thumb base) bulge on the back-left
    parts.append(oriented_pillow("thenar", (0.05 * s, 0.06 * s, 0.09 * s),
                                 around(G, A, o, fr, 0.03 * s, 0.032 * s, 232), o, fr, A, 0.8, 0.8, 10, 6))

    # --- four fingers wrapped around the grip -------------------------------------------------------------
    gap = 0.0355 * s
    ends = (196, 206, 202, 190)
    for i in range(4):
        h = (1.5 - i) * gap
        rr = 0.0185 * s * (1.0, 1.03, 0.98, 0.88)[i]
        th0, th1 = 22 + knuckle_bias, 22 + knuckle_bias + (ends[i] - 22) * finger_wrap
        pts, rad = [], []
        n = 6
        for k in range(n):
            t = k / (n - 1)
            th = th0 + (th1 - th0) * t
            R = 0.046 * s + 0.004 * s * math.sin(math.pi * t) - (0.012 * s * ((t - 0.7) / 0.3) if t > 0.7 else 0.0)
            pts.append(around(G, A, o, fr, h, R, th))
            rad.append(rr * (1.0 - 0.1 * t))
        parts.append(pl.sausage("finger", pts, rad, 8, 2, LEATHER, (True, True), 2, True, 75))
        # knuckle bump
        parts.append(rw.sphere("knuckle", rr * 1.02, 8, 5, tuple(around(G, A, o, fr, h, 0.05 * s, 12 + knuckle_bias)),
                               mat=LEATHER))

    # --- thumb along the far side, above the fingers --------------------------------------------------------
    top = 1.5 * gap + thumb_lift * s
    tpts = [around(G, A, o, fr, top - 0.022 * s, 0.03 * s, 255), around(G, A, o, fr, top + 0.006 * s, 0.047 * s, 218),
            around(G, A, o, fr, top + 0.018 * s, 0.054 * s, 178), around(G, A, o, fr, top + 0.02 * s, 0.054 * s, 140)]
    parts.append(pl.sausage("thumb", tpts, [0.025 * s, 0.023 * s, 0.021 * s, 0.019 * s], 8, 3, LEATHER, (True, True),
                            2, True, 75))
    # stitched thumb seam: a dark leather band around the thumb's middle joint
    parts.append(rw.torus("thumbseam", 0.021 * s, 0.0045 * s, 10, 4, (0, 0, 0), mat=LEATHER_DARK))
    pl.align(parts[-1], (tpts[3] - tpts[1]).normalized(), tpts[2])

    # --- stitched seams on the back of the hand (three tendon ridges) ---------------------------------------
    for k in (-1, 0, 1):
        h = k * 0.036 * s
        a = around(G, A, o, fr, h, 0.0, 0) - fr * (0.03 * s)
        b = around(G, A, o, fr, h, 0.0, 0) + fr * (0.008 * s)
        pa, _ = surface_point(mass, a + o * 0.2, -o, a + o * 0.06 * s)
        pb, _ = surface_point(mass, b + o * 0.2, -o, b + o * 0.06 * s)
        parts.append(pl.capsule("seam", pa - o * 0.002 * s, pb - o * 0.002 * s, 0.0055 * s, 5, 2, LEATHER_DARK))

    # --- wrist, glove flare and sleeve ------------------------------------------------------------------------
    heel = G - A * (0.035 * s) - fr * (0.03 * s) + o * (0.012 * s)
    wrist_end = heel + F * (wrist_len * s)
    parts.append(pl.sausage("wrist", [heel, (heel + wrist_end) / 2, wrist_end + F * 0.01 * s],
                            [0.042 * s, 0.038 * s, 0.038 * s], 12, 2, LEATHER, (True, False), 2, True, 60))
    parts += sleeve(wrist_end, F, out, s, sleeve_len)

    g = rw.join(parts, name, origin=(0, 0, 0))
    rw.smooth(g, 60)
    return g
