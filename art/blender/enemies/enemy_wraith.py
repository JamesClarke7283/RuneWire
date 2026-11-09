"""enemy_wraith: Shade Wraith of the Hollow Choir (origin at the body centre; tatters -1.1 m .. hood top +1.1 m).

A floating hooded shade. A tall pointed hood (violet piping on the rim) whose deep void face shows only
two angry glowing teal eyes; a broad shoulder mantle with pointed drapes and a piped hem, closed by a
brass clasp with a teal soul gem; a dark purple cloak (M_Fabric__3b2357) that tears into broad flowing
tatters with serrated edges, a few of them forked, longest at the back and swept back as it drifts;
the faint violet glow of its lining shows inside the cuffs, on the twisted tatters and through two
rips sewn shut with dark thread; wide ragged bell sleeves reach forward and pale ghostly clawed hands
with glowing teal claws float out of teal wisps in the cuffs. The Choir eye sigil glows on the back.

Hierarchy (spec Batch B):
  Body     pivot at the body centre (0, 0, 0) = the model origin; cloak, mantle, sleeves, wisps
    Head   pivot at the neck; hood, void face, eyes
    HandL  pivot at the left wrist (+X) = centre of the left cuff; the hand floats free of the sleeve
    HandR  pivot at the right wrist (-X)

How the game moves it (scripts/enemies/enemy_wraith.gd): the whole model bobs and pitches forward
when moving, Body rolls +-0.06 rad and Head +-0.12 rad about their pivots, and each hand swings about X
from +0.15 rad (idle sway) to -1.35 rad (claw strike). The hands droop from the cuffs at rest, so the
strike flicks the claws forward at the target (see the RWCLAW lines). The hood base sits deep in the
mantle collar over a dark throat void, and each hand turns inside a glowing wisp whose round head is
centred on the wrist pivot, so turning or rolling a node never opens a see-through gap.

Extra previews: RW_QUICK=1 skips them, RW_EXTRAS=front,side,pose,night picks them (see VIEWS);
RW_QA_DIR=/tmp/x RW_QA_VIEWS=back,pose_roll,far_grass,... writes scratch QA renders there.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "parts"))
sys.path.insert(0, HERE)
import bmesh  # noqa: E402
import bpy  # noqa: E402
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import magiclib as ml  # noqa: E402
import partlib as pl  # noqa: E402
from mathutils import Matrix, Vector as V  # noqa: E402

ASSET = "enemy_wraith"
rw.reset()

# ---------------------------------------------------------------- materials
CLOAK = "M_Fabric__3b2357"
PIPING = "M_Fabric__7a52b0"          # lighter violet piping on the hood rim and the mantle hem
TRIM = "M_Brass"
RUNE = "M_RuneGlow"
GEM = "M_Crystal__3ff2dc"
pl.tint_emission(GEM, "3ff2dc", 2.4)
# Godot turns any emissive flat material into a glow with energy >= 1, so "faint" glows use a dark
# emission colour at strength 1.0 over a darker base.
lining = rw.material("WraithLining", "3a2163", 0.9, 0.0, "4f2a9e", 1.0)
ghost = rw.material("WraithGhost", "c9cff2", 0.5, 0.0, "1d3f55", 1.0)
void = rw.flat("WraithVoid", "0d0816", 0.95)
hood_in = rw.flat("WraithHoodInner", "1c1030", 0.9)
eye_glow = rw.glow("WraithEye", "3ff7e0", 6.0)
claw_glow = rw.glow("WraithClaw", "27e0cf", 1.8)
wisp_glow = rw.glow("WraithWisp", "45e6d6", 2.0)
thread = rw.flat("WraithThread", "17101f", 0.8)

# ---------------------------------------------------------------- pivots
P_BODY = V((0.0, 0.0, 0.0))
P_NECK = V((0.0, -0.03, 0.47))
FRONT = 1.5 * math.pi          # ring angle of the front (-Y); 0 = +X (left), pi/2 = +Y (back)


# ======================================================================== helpers
def strip_rows(base, ctr, L, start_dir, out, side, rows, sweep, flare, sway, curl, twist=0.0, width_pow=2.2,
               t_end=1.0, serr=0.22):
    """Rows of points for one tatter hanging from `base` (hem points, in order). The centreline leaves
    `ctr` along `start_dir`, drops `L` metres, flares `flare` outward, sweeps by the vector `sweep`,
    sways `sway` sideways and flicks its tip `curl` outward. The flap stays broad, then tears to a point
    (width 1 - t^width_pow), the curved cross-section flattens out (cloth, not a tube) and turns by up to
    `twist` degrees about the drop. Both torn edges are serrated (alternate rows pulled in by `serr`, the
    two edges out of step). With t_end < 1 only the upper part is built (for a forked tatter).
    Returns (rows, centreline): row 0 = base; when the tatter is complete the last row is [tip]."""
    tip = ctr + V((0, 0, -L)) + out * flare + sweep + side * sway
    p1 = ctr + start_dir * (L * 0.45)
    offs = []
    for b in base:
        o = b - ctr
        rad = out * o.dot(out)
        offs.append((o - rad, rad))
    out_rows, centres = [], []
    for r in range(rows + 1):
        t = t_end * r / rows
        c = ctr * (1 - t) ** 2 + p1 * (2 * (1 - t) * t) + tip * (t * t)
        c = c + out * (curl * max(0.0, (t - 0.55) / 0.45) ** 2)
        centres.append(c)
        if t > 1.0 - 1e-6:
            out_rows.append([c])
            continue
        s = 1.0 - t ** width_pow
        flat = (1.0 - t) ** 1.5
        rot = Matrix.Rotation(math.radians(twist) * t * t, 3, 'Z')
        row = []
        last = len(offs) - 1
        for i, (tg, rd) in enumerate(offs):
            k = 1.0
            if r > 0 and ((i == 0 and r % 2 == 1) or (i == last and r % 2 == 0)):
                k = 1.0 - serr
            row.append(c + rot @ ((tg * k + rd * flat) * s))
        out_rows.append(row)
    return out_rows, centres


def add_strip(bm, base_verts, rows):
    """Faces for a tatter whose row 0 reuses `base_verts` (shared with the cloth above).
    Returns the verts of its last row (open end of a fork stem, or [tip])."""
    prev = base_verts
    for row in rows[1:]:
        if len(row) == 1:
            tip = bm.verts.new(row[0])
            for i in range(len(prev) - 1):
                bm.faces.new((prev[i], prev[i + 1], tip))
            return [tip]
        cur = [bm.verts.new(p) for p in row]
        for i in range(len(prev) - 1):
            bm.faces.new((prev[i], prev[i + 1], cur[i + 1], cur[i]))
        prev = cur
    return prev


def add_tatter(bm, base_v, ctr, tip_z, start_dir, out, side, rows, sweep, flare, sway, curl, twist, fork=None):
    """One tatter (optionally forked into two points). fork = (t_fork, len_a, len_b): the stem splits at
    t_fork and the two halves hang on; the longer half (len 1.0) ends exactly at tip_z.
    Returns the tip points."""
    base = [v.co.copy() for v in base_v]
    L = ctr.z - tip_z
    if not fork:
        rws, _ = strip_rows(base, ctr, L, start_dir, out, side, rows, sweep, flare, sway, curl, twist)
        add_strip(bm, base_v, rws)
        return [rws[-1][0]]
    t_f, la, lb = fork
    rf = max(2, int(round(rows * t_f)))
    rws, cen = strip_rows(base, ctr, L, start_dir, out, side, rf, sweep, flare, sway, curl, twist, t_end=t_f)
    end_v = add_strip(bm, base_v, rws)
    mid = len(end_v) // 2
    sdir = (cen[-1] - cen[-2]).normalized()
    tips = []
    for hv, lam, sg in ((end_v[:mid + 1], la, -1.0), (end_v[mid:], lb, 1.0)):
        hb = [v.co.copy() for v in hv]
        hc = (hb[len(hb) // 2] + hb[(len(hb) - 1) // 2]) * 0.5
        Ls = (hc.z - tip_z) * lam
        sub, _ = strip_rows(hb, hc, Ls, sdir, out, side, max(2, rows - rf), sweep * (1 - t_f), flare * 0.6,
                            sg * 0.035, curl, twist * 0.5)
        add_strip(bm, hv, sub)
        tips.append(sub[-1][0])
    return tips


def finish_cloth(name, bm, mat, inner, thick):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cl._orient_outward(bm)
    o = cl._new_obj(name, bm, mat, smooth=True)
    if thick:
        cl.cloth_shell(o, thick, inner)
    return o


def tattered_cloak(name, levels, widths, amp, strips, rows=7, mat=CLOAK, inner=lining, thick=0.022, tears=None,
                   forks=None):
    """Folded cloak surface of revolution that splits at its last ring into tatters.
    levels: [(z, rx, ry, cy), ...] top to bottom (the last one is the split ring).
    widths: columns per tatter, going round from the front (+X side first); strip 0 is centred on the
    front. Folds peak mid-tatter and the tears run along the valleys between them.
    strips: per tatter (tip_z, sweep_y, flare, sway, curl, twist); the tip hangs at world height tip_z.
    tears: per tatter, how far (m) the tear on its start side runs up (+) or down (-) from the split
    ring, so the tears don't all start at one height.
    forks: {tatter index: (t_fork, len_a, len_b)} tatters torn into two points (see add_tatter)."""
    segs = sum(widths)
    a0 = FRONT - math.pi * widths[0] / segs
    cols = []
    for j, w in enumerate(widths):
        cols += [(j, i / w) for i in range(w)]
    tears = tears or [0.0] * len(widths)
    bm = bmesh.new()
    grid = []
    n = len(levels)
    for li, (z, rx, ry, cy) in enumerate(levels):
        am = amp[0] + (amp[1] - amp[0]) * li / (n - 1)
        ring = []
        for k in range(segs):
            a = a0 + 2 * math.pi * k / segs
            j, u = cols[k]
            m = 1.0 + am * math.cos(2 * math.pi * (u - 0.5))
            dz = 0.0
            if li == n - 1:
                # the split ring rises toward each tear: lerp between the tears at both ends of the strip
                t0, t1 = tears[j], tears[(j + 1) % len(widths)]
                dz = t0 + (t1 - t0) * u
            ring.append(bm.verts.new((rx * m * math.cos(a), cy + ry * m * math.sin(a), z + dz)))
        grid.append(ring)
    for li in range(n - 1):
        A, B = grid[li], grid[li + 1]
        for k in range(segs):
            kk = (k + 1) % segs
            bm.faces.new((A[k], A[kk], B[kk], B[k]))
    z, rx, ry, cy = levels[-1]
    zp, rxp, ryp, cyp = levels[-2]
    start = 0
    tips = []
    for j, w in enumerate(widths):
        tip_z, sweep, flare, sway, curl, twist = strips[j]
        a_mid = a0 + 2 * math.pi * (start + w / 2) / segs
        ca, sa = math.cos(a_mid), math.sin(a_mid)
        zc = z + 0.5 * (tears[j] + tears[(j + 1) % len(widths)])
        ctr = V((rx * (1 + amp[1]) * ca, cy + ry * (1 + amp[1]) * sa, zc))
        prev = V((rxp * (1 + amp[1]) * ca, cyp + ryp * (1 + amp[1]) * sa, zp))
        out = V((ca / rx, sa / ry, 0.0)).normalized()
        side = V((-sa * rx, ca * ry, 0.0)).normalized()
        idx = [(start + i) % segs for i in range(w + 1)]
        base_v = [grid[-1][i] for i in idx]
        tips += add_tatter(bm, base_v, ctr, tip_z, (ctr - prev).normalized(), out, side, rows, V((0, sweep, 0)),
                           flare, sway, curl, twist, (forks or {}).get(j))
        start += w
    return finish_cloth(name, bm, mat, inner, thick), tips


def ghost_sleeve(name, ctrl, r0, r1, segs=16, n=9, droop=0.08, droop_from=0.5, ragged=0.03, tails=(),
                 mat=CLOAK, inner=lining, thick=0.02, seed=1):
    """Bell sleeve along a cubic Bezier (shoulder -> cuff) growing from r0 to r1. The lower side of
    the cuff hangs down by up to `droop`, the cuff edge is ragged (alternate points pushed along the
    sleeve), and `tails` = [(centre_col, width, L, sweep, sway)] tatters hang from cuff columns
    (column 0 = top of the cuff, segs/2 = bottom). Returns (object, cuff centre, cuff axis)."""
    pts = cl.bezier(ctrl[0], ctrl[1], ctrl[2], n, ctrl[3])
    m = len(pts)
    fr = cl._frames(pts, (0, 0, 1))
    axis = (pts[-1] - pts[-2]).normalized()
    rnd = random.Random(seed)
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        t = i / (m - 1)
        r = r0 + (r1 - r0) * t ** 1.6
        N, B = fr[i]
        f = max(0.0, (t - droop_from) / (1 - droop_from)) ** 1.5
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            off = N * (r * math.cos(a)) + B * (r * math.sin(a))
            q = p + off
            if f > 0 and off.z < 0:
                q = q + V((0, 0, -droop * f * (-off.z / r)))
            if i == m - 1 and ragged:
                q = q + axis * (ragged * (rnd.random() if k % 2 == 0 else -0.35 * rnd.random()))
            ring.append(bm.verts.new(q))
        rings.append(ring)
    for i in range(m - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(segs):
            kk = (k + 1) % segs
            bm.faces.new((A[k], A[kk], B[kk], B[k]))
    cuff = rings[-1]
    cc = pts[-1]
    for (c, w, L, sweep, sway) in tails:
        idx = [(c - w // 2 + i) % segs for i in range(w + 1)]
        base_v = [cuff[i] for i in idx]
        base = [v.co.copy() for v in base_v]
        ctr = cuff[c % segs].co.copy()
        out = (ctr - cc).normalized()                 # radial from the cuff centre (down for the cuff bottom)
        side = axis.cross(out).normalized()          # along the cuff edge
        start_dir = (V((0, 0, -1)) + axis * 0.5).normalized()
        rws, _ = strip_rows(base, ctr, L, start_dir, out, side, 5, sweep, 0.02, sway, 0.02, width_pow=1.4)
        add_strip(bm, base_v, rws)
    return finish_cloth(name, bm, mat, inner, thick), cc, axis


def ghost_hand(name, W, down, palm, thumb, s=1.0, curl=0.55, spread=1.0):
    """Pale ghostly claw: a ball centred on the wrist pivot, a chunky palm, three long
    knobbly fingers and a thumb, each ending in a hooked glowing claw that curls toward the palm.
    down = wrist -> fingertips, palm = palm normal (the side the claws hook to), thumb = thumb side."""
    d, n, t = cl._hand_axes(down, palm, thumb)
    W = V(W)
    parts = [cl.sphere(name + "_wrist_ball", W, 0.042 * s, 12, 6, ghost)]
    parts.append(cl.capsule(name + "_wrist", W + d * (0.02 * s), W + d * (0.1 * s), 0.042 * s, 0.052 * s, 12, 3,
                            ghost))
    pc = W + d * (0.15 * s)
    parts.append(cl.ellipsoid(name + "_palm", pc, (0.09 * s, 0.052 * s, 0.088 * s), 14, 8, ghost,
                              cl.axes_matrix(t, n, d)))
    claws = []

    def digit(tag, base, fdir, L, r, cl_len):
        k1 = base + fdir * (L * 0.5)
        d2 = (fdir + n * (curl * 0.7)).normalized()
        k2 = k1 + d2 * (L * 0.5)
        d3 = (fdir + n * (curl * 1.7)).normalized()
        out = [cl.sweep(name + "_" + tag, [base - fdir * (0.02 * s), base, base.lerp(k1, 0.55), k1,
                                           k1.lerp(k2, 0.5), k2],
                        [r * 0.9, r, r * 0.86, r * 0.95, r * 0.8, r * 0.78], 8, ghost),
               cl.sphere(name + "_" + tag + "_kn", k1, r * 1.12, 8, 5, ghost)]
        hook = cl.bezier(k2 - d2 * (0.012 * s), k2 + d2 * (cl_len * 0.5), k2 + d3 * (cl_len * 0.75)
                         + n * (cl_len * 0.25), 6)
        out.append(cl.sweep(name + "_" + tag + "_claw", hook, [r * 0.95, r * 0.92, r * 0.72, r * 0.48, r * 0.24, 0.0],
                            8, claw_glow))
        claws.append(hook[-1])
        return out

    for k, u in enumerate((-1.0, 0.0, 1.0)):
        base = pc + d * (0.055 * s) + t * (u * 0.056 * s) - n * (0.006 * s)
        fdir = (d + t * (u * 0.2 * spread)).normalized()
        L = (0.18 - 0.022 * abs(u)) * s
        parts += digit("f%d" % k, base, fdir, L, 0.032 * s, 0.105 * s)
    tb = pc + t * (0.075 * s) - d * (0.01 * s) + n * (0.014 * s)
    tdir = (t * 0.75 + d * 0.65 + n * 0.25).normalized()
    parts += digit("thumb", tb, tdir, 0.11 * s, 0.031 * s, 0.085 * s)
    return parts, claws


def glow_eye(name, target, center, az, el, w, h, sgn, mat, depth=0.014, top=0.35, slope=0.45, tilt=12.0,
             n_out=20, K=3, sink=0.006):
    """Angry cartoon glowing eye lying on `target` (seen from `center` along (az, el) degrees): an
    ellipse of half size (w, h) tilted `tilt` deg (outer end up), its top cut by a line sloping down
    toward the nose (a heavy brow), domed `depth` off the surface. sgn = +1 left eye (+X), -1 right."""
    c0 = V(center)
    hit, nrm = ml.surface_hit(target, c0, ml._dir((az, el)))
    U = V((0, 0, 1)).cross(nrm).normalized()
    Vv = nrm.cross(U).normalized()
    ca, sa = math.cos(math.radians(tilt * sgn)), math.sin(math.radians(tilt * sgn))
    outline = []
    for i in range(n_out):
        th = 2 * math.pi * i / n_out
        x, y = w * math.cos(th), h * math.sin(th)
        x, y = x * ca - y * sa, x * sa + y * ca
        ytop = h * top + slope * h * (x / w) * sgn
        outline.append((x, min(y, ytop)))
    cx = sum(p[0] for p in outline) / n_out
    cy = sum(p[1] for p in outline) / n_out

    def on_surface(x, y, hgt):
        p, nm = ml.surface_hit(target, c0, hit + U * x + Vv * y - c0)
        return p + nm * (hgt - sink)

    rings = []
    for k in range(K):
        f = math.cos(0.5 * math.pi * k / K)
        hgt = depth * math.sin(0.5 * math.pi * k / K)
        rings.append([on_surface(cx + (x - cx) * f, cy + (y - cy) * f, hgt) for (x, y) in outline])
    rings.append(on_surface(cx, cy, depth))
    return cl.skin(name, rings, mat, cap_start=False, cap_end=False)


def stitched_rip(name, target, center, ctrl, width=0.024, stitches=3, seed=1):
    """A jagged rip in the cloak leaking the violet inner light (a glowing bead following `target`'s
    surface through the (azimuth, elevation) control directions seen from `center`), sewn shut with
    dark cross-stitches."""
    pts, nrms = ml.surface_path(target, center, ctrl, zig=0.06, kinks=1, step_deg=2.5, seed=seed)
    m = len(pts)
    wid = [width * (0.3 + 0.7 * math.sin(math.pi * i / (m - 1)) ** 0.7) for i in range(m)]
    out = [ml.ribbon(name, pts, nrms, wid, [w * 0.6 + 0.004 for w in wid], RUNE, 4, 0.3, arch=True)]
    for i in range(stitches):
        k = int(round((i + 1) * (m - 1) / (stitches + 1)))
        p, nm = pts[k], nrms[k]
        tang = (pts[min(k + 1, m - 1)] - pts[max(k - 1, 0)]).normalized()
        across = nm.cross(tang).normalized()
        for sg in (1, -1):        # a little X across the rip
            a = p + across * 0.04 + tang * (0.014 * sg)
            b = p - across * 0.04 - tang * (0.014 * sg)
            out.append(cl.sweep(name + "_stitch", [a - nm * 0.004, p + nm * 0.009, b - nm * 0.004], 0.0065, 6,
                                thread))
    return out


# ======================================================================== Body
body = []
rnd = random.Random(11)

# --- cloak: a rounded chest tapering into broad flowing tatters swept back like a tail
WIDTHS = [5, 6, 6, 5, 9, 5, 6, 6]                  # 48 columns; strip 0 centred on the front, 4 on the back
SEGS = sum(WIDTHS)
SPLIT_Z = -0.64
strips, tears, mids = [], [], []
acc = 0
for j, w in enumerate(WIDTHS):
    a_mid = FRONT - math.pi * WIDTHS[0] / SEGS + 2 * math.pi * (acc + w / 2) / SEGS
    acc += w
    back = 0.5 - 0.5 * math.cos(a_mid - FRONT)      # 0 at the front, 1 at the back
    mids.append(back)
    tip_z = -0.86 - 0.2 * back + rnd.uniform(-0.03, 0.03)
    strips.append([max(-1.07, tip_z), 0.03 + 0.14 * back, 0.05 + 0.025 * rnd.random(),
                   (1 if j % 2 else -1) * (0.01 + 0.01 * rnd.random()), 0.02 + 0.02 * rnd.random(),
                   (1 if j % 2 else -1) * (4 + 5 * rnd.random())])
    tears.append(rnd.uniform(-0.04, 0.06))
# the tatter nearest the back centre is the longest: it sets the bottom of the model at -1.1 m
strips[max(range(len(mids)), key=lambda i: mids[i])][0] = -1.1
cloak, tatter_tips = tattered_cloak(
    "cloak", [(0.34, 0.36, 0.26, 0.0), (0.15, 0.43, 0.32, 0.0), (-0.1, 0.42, 0.32, 0.03),
              (-0.3, 0.385, 0.3, 0.07), (-0.49, 0.34, 0.28, 0.12), (SPLIT_Z, 0.31, 0.265, 0.16)],
    WIDTHS, (0.01, 0.06), strips, rows=6, tears=tears,
    forks={2: (0.55, 0.8, 1.0), 4: (0.5, 1.0, 0.8), 6: (0.5, 1.0, 0.75)})
body.append(cloak)
# the Choir's eye sigil glowing on the back of the cloak
body += ml.surface_glyph("back_sigil", cloak, (0.0, 0.05, -0.02), "eye", (180, 2), 0.42, 0.026, mat=RUNE,
                         per_unit=40)
# rips leaking the inner light, stitched shut: front right of the belly and low on the back left
body += stitched_rip("rip_front", cloak, (0.0, 0.03, -0.12), [(-31, 13), (-24, 0), (-32, -14)], seed=4)
body += stitched_rip("rip_back", cloak, (0.0, 0.08, -0.3), [(127, 11), (137, -2), (130, -16)], stitches=2, seed=7)

# --- broad shoulder mantle with pointed drapes and a lighter piped hem
N_DRAPES = 8
mrnd = random.Random(5)
drape_depth = [0.12 + 0.08 * mrnd.random() for _ in range(N_DRAPES)]


def mantle_hem(a, k):
    ph = N_DRAPES * a + 0.5 * math.pi            # drape points under the fold ridges
    i = int(round((ph - 0.5 * math.pi) / (2 * math.pi))) % N_DRAPES
    return -drape_depth[i] * (0.5 + 0.5 * math.sin(ph)) ** 2.5


mantle, mrings = ml.robe_surface("mantle", [(0.6, 0.13, 0.12, 0.0), (0.54, 0.21, 0.18, 0.0), (0.46, 0.35, 0.27, 0.01),
                                            (0.37, 0.46, 0.32, 0.02), (0.28, 0.51, 0.35, 0.03),
                                            (0.21, 0.52, 0.36, 0.035)],
                                 segs=48, folds=N_DRAPES, amp=(0.0, 0.035), mat=CLOAK, inner=hood_in, thick=0.022,
                                 hem=mantle_hem)
body.append(mantle)
body.append(ml.loop_tube("mantle_piping", [p + V((0, 0, -0.004)) for p in mrings[-1]], 0.016, 6, PIPING,
                         max_pts=48))
# dark throat void inside the collar: any gap round the turning hood shows darkness, not sky
body.append(cl.ellipsoid("throat_void", (0.0, -0.02, 0.5), (0.17, 0.16, 0.13), 16, 8, void))
# brass clasp with a glowing teal soul gem holding the mantle closed under the hood
clasp_c = V((0.0, -0.31, 0.4))
body.append(pl.disc("clasp", 0.055, 0.024, (0, -1, 0.3), tuple(clasp_c), TRIM, 18, 0.4))
body.append(cl.ellipsoid("soul_gem", clasp_c + V((0, -0.016, 0.005)), (0.032, 0.02, 0.038), 10, 6, GEM))

# --- sleeves reaching forward, ragged cuffs with a short pointed drape hanging under each
P_WRIST = {}
for s in (1, -1):
    slv, cc, ax = ghost_sleeve("sleeve", [(0.32 * s, 0.02, 0.36), (0.54 * s, 0.0, 0.24), (0.58 * s, -0.2, 0.14),
                                         (0.55 * s, -0.4, 0.08)], 0.105, 0.17, segs=16, n=9, droop=0.1,
                               tails=[(8, 5, 0.2, V((0.02 * s, 0.08, 0.0)), 0.01 * s)], seed=3 + (s > 0))
    body.append(slv)
    # glowing teal wisp the hand floats out of: its round head is centred on the wrist pivot (so the
    # hand can turn inside it) and its tail streams back into the sleeve
    body.append(cl.teardrop("wisp", cc, cc - ax * 0.2 + V((0, 0, 0.02)), 0.06, segments=14, mat=wisp_glow, steps=6))
    P_WRIST[s] = cc
body_node = cl.node("Body", body, P_BODY)

# ======================================================================== Head
head = []
hood_path = [(0.0, -0.28, 0.685), (0.0, -0.17, 0.705), (0.0, -0.05, 0.715), (0.0, 0.06, 0.73), (0.0, 0.135, 0.775),
             (0.0, 0.18, 0.845), (0.0, 0.205, 0.925), (0.0, 0.225, 1.01), (0.0, 0.27, 1.1)]
hood_r = [(0.232, 0.25), (0.27, 0.268), (0.278, 0.262), (0.262, 0.245), (0.232, 0.208), (0.185, 0.16), (0.13, 0.11),
          (0.07, 0.06), (0.0, 0.0)]
hood, rim = ml.hood_surface("hood", hood_path, hood_r, segs=22, mat=CLOAK, inner=hood_in, thick=0.024, tilt=0.05)
head.append(hood)
head.append(ml.loop_tube("hood_piping", rim, 0.02, 6, PIPING, max_pts=22))
void_c = V((0.0, -0.05, 0.685))
face_void = cl.ellipsoid("face_void", void_c, (0.196, 0.165, 0.225), 18, 10, void)
head.append(face_void)
for s in (1, -1):
    head.append(glow_eye("eye", face_void, void_c, 25 * s, 4, 0.07, 0.05, s, eye_glow))
head_node = cl.node("Head", head, P_NECK, body_node)

# ======================================================================== Hands (pivot = cuff centre)
claw_tips = {}
for s, side in ((1, "L"), (-1, "R")):
    parts, claws = ghost_hand("hand", P_WRIST[s], (-0.06 * s, -0.32, -1.0), (-0.25 * s, 1.0, 0.1), (-s, 0, 0),
                              s=1.0)
    claw_tips[side] = claws
    cl.node("Hand" + side, parts, P_WRIST[s], body_node)

rw.finish(ASSET, "enemies", icon=True)
cl.report_nodes(["Body", "Head", "HandL", "HandR"])
cl.budget(15000)
cl.tri_breakdown()
print("RWHEM    %d tatter tips, lowest z=%.3f, highest z=%.3f" % (
    len(tatter_tips), min(p.z for p in tatter_tips), max(p.z for p in tatter_tips)))


def claw_world(side, rx_deg):
    """World positions of a hand's claw tips with the hand node rotated rx_deg about X."""
    o = bpy.data.objects["Hand" + side]
    local = [o.matrix_world.inverted() @ V(p) for p in claw_tips[side]]
    old = o.rotation_euler.copy()
    o.rotation_euler = (math.radians(rx_deg), 0, 0)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ p for p in local]
    o.rotation_euler = old
    bpy.context.view_layer.update()
    return pts


for tag, ang in (("rest", 0.0), ("sway", 8.6), ("strike", -68.8), ("max", -77.3)):
    pts = claw_world("L", ang)
    c = sum(pts, V()) / len(pts)
    print("RWCLAW   %-6s HandL.x=%6.1f deg  claw tips centre=(%.3f, %.3f, %.3f)  lowest z=%.3f" % (
        tag, ang, c.x, c.y, c.z, min(p.z for p in pts)))


def render_dir(path, direction, size=640, pose=None, bg=None, key=None, fill=None, fov=35.0, objs=None):
    """QA render like rw.render_view, but from any camera direction, optionally posed (node -> XYZ euler
    degrees, restored afterwards) and under other light levels (bg = world RGBA, key/fill = sun energy)."""
    saved = {}
    for nm, r in (pose or {}).items():
        o = bpy.data.objects[nm]
        saved[nm] = o.rotation_euler.copy()
        o.rotation_euler = tuple(math.radians(a) for a in r)
    bpy.context.view_layer.update()
    mn, mx = rw.bounds(objs)
    rw._setup_render(size, False, True)
    if bg is not None:
        bgn = bpy.data.worlds["RW_World"].node_tree.nodes.get("Background")
        bgn.inputs[0].default_value = bg[:3] + (1.0,)
        bgn.inputs[1].default_value = bg[3]
    temp = rw._temp_rig(mn, mx, "front34", fov)
    cam = temp[0]
    center = (mn + mx) / 2
    radius = max((mx - mn).length / 2, 0.05)
    d = V(direction).normalized()
    cam.location = center + d * (radius / math.sin(math.radians(fov) / 2) * 1.08)
    cam.rotation_euler = (center - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    for o in temp[1:]:
        if key is not None and o.name.startswith("RW_Key"):
            o.data.energy = key
        if fill is not None and o.name.startswith("RW_Fill"):
            o.data.energy = fill
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in temp:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
    for nm, r in saved.items():
        bpy.data.objects[nm].rotation_euler = r
    bpy.context.view_layer.update()
    print("RWREPORT   rendered", path)


NIGHT = dict(bg=(0.015, 0.02, 0.05, 0.6), key=0.25, fill=0.08)
STRIKE = {"Head": (0, 0, 35), "HandL": (-77, 0, 0), "HandR": (-77, 0, 0)}   # head turned, claws at -1.35 rad
# name -> (camera direction, pose, extra render_dir arguments)
VIEWS = {
    "front": ((0, -1, 0.12), None, {}),
    "side": ((-1, 0, 0.12), None, {}),
    "back": ((0.05, 1, 0.12), None, {}),
    "below": ((-0.5, -0.7, -0.6), None, {}),
    "pose": ((-0.75, -1.0, 0.4), STRIKE, {}),
    "pose_side": ((-1, -0.05, 0.12), STRIKE, {}),
    # game roll extremes exaggerated (Head 0.12 rad -> 30 deg, Body 0.06 rad) plus the idle hand sway
    "pose_roll": ((0.8, 1.0, 0.5), {"Head": (0, -30, 0), "Body": (0, 3.5, 0), "HandL": (8.6, 0, 0),
                                    "HandR": (8.6, 0, 0)}, {}),
    "pose_turn_back": ((0.8, 1.0, 0.5), {"Head": (0, 0, -35)}, {}),
    "hand": ((-0.6, -1.0, 0.35), None, {"objs": "HandR"}),
    "night": ((-0.75, -1.0, 0.55), None, NIGHT),
    # what the player mostly sees: the wraith hovers about level with the camera
    "level": ((-0.75, -1.0, -0.05), None, {}),
    # ~30 m away (about 60-90 px tall on a 1080p screen), against grass and at night
    "far_grass": ((-0.75, -1.0, 0.1), None, dict(bg=(0.2, 0.42, 0.1, 1.0), size=96)),
    "far_night": ((-0.75, -1.0, 0.1), None, dict(NIGHT, size=96)),
}


def render_named(tag, path, size):
    dvec, pose, extra = VIEWS[tag]
    extra = dict(extra)
    size = extra.pop("size", size)
    if "objs" in extra:
        extra["objs"] = [bpy.data.objects[extra["objs"]]]
    render_dir(path, dvec, size, pose=pose, **extra)


# Extra previews (one Blender job renders them all; keep the list short on a busy machine).
if os.environ.get("RW_QUICK") != "1":
    for tag in os.environ.get("RW_EXTRAS", "front,side,pose,night").split(","):
        if tag:
            render_named(tag, cl.preview_path(ASSET, "enemies", tag), 640)
# QA scratch renders: RW_QA_DIR=/tmp/x RW_QA_VIEWS=back,pose_roll,...
QA = os.environ.get("RW_QA_DIR")
if QA:
    for tag in os.environ.get("RW_QA_VIEWS", "back").split(","):
        if tag:
            render_named(tag, os.path.join(QA, "wraith_%s.png" % tag), 512)
