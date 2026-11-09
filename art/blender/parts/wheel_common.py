"""wheel_common: shared builder for part_wheel and part_big_wheel.

The wheel spins about the X axis. It is built symmetric (5 spokes, hub, nuts and axle cap on BOTH
faces) so it looks right on either side of a contraption. Everything is joined into ONE mesh object
named "Wheel" with its origin at the wheel centre (the world origin).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402

rw = pl.rw
V = pl.V


def _radial(theta):
    return V((0.0, math.cos(theta), math.sin(theta)))


def _tangent(theta):
    return V((0.0, -math.sin(theta), math.cos(theta)))


def build_wheel(R, W, n_lugs=14, lug_h=None, chevron=26.0, rugged=False):
    """R = outer radius (tread tops), W = overall width along X."""
    k = R / 0.45                      # radial scale vs. the 0.9 m reference wheel
    hw = W / 2
    lug_h = lug_h or 0.045 * k
    r_c = R - lug_h                   # tyre crown radius under the lugs
    r_rim = 0.6 * R                   # where the tyre bead meets the rim
    parts = []

    # --- tyre carcass (lathe around X): bead -> sidewall bulge -> rounded shoulder -> crown ------------
    bulge_r = (r_rim + r_c) / 2 - 0.01 * k
    prof = [(r_rim - 0.012 * k, -hw * 0.66), (r_rim + 0.02 * k, -hw * 0.9), (bulge_r, -hw),
            (r_c - 0.03 * k, -hw * 0.94), (r_c - 0.006 * k, -hw * 0.8), (r_c, -hw * 0.55),
            (r_c, hw * 0.55), (r_c - 0.006 * k, hw * 0.8), (r_c - 0.03 * k, hw * 0.94), (bulge_r, hw),
            (r_rim + 0.02 * k, hw * 0.9), (r_rim - 0.012 * k, hw * 0.66)]
    parts.append(pl.lathe_axis("tyre", prof, (1, 0, 0), (0, 0, 0), 36 if not rugged else 40, "M_Rubber",
                               False, False, 40))

    # --- chunky chevron tread lugs ---------------------------------------------------------------------
    a = math.radians(chevron)
    lug_w = (0.075 if not rugged else 0.068) * k
    ext_target = hw - 0.014 * k - 0.006        # x extent of each lug (one per side of the centre line)
    lug_l = (ext_target - lug_w * math.sin(a)) / math.cos(a)
    for i in range(n_lugs):
        th = 2 * math.pi * i / n_lugs
        rad = _radial(th)
        tan = _tangent(th)
        for s in (-1, 1):
            xdir = V((math.cos(a), 0, 0)) + tan * (math.sin(a) * s)
            xc = s * (0.006 + ext_target / 2)
            centre = V((xc, 0, 0)) + rad * (r_c + lug_h / 2 - 0.006 * k)
            parts.append(pl.obox("lug", (lug_l, lug_w, lug_h + 0.012 * k), centre, xdir, rad, "M_Rubber",
                                 rounded=0.012 * k, segments=1))

    # --- rim: dark steel drum with lips gripping the beads ------------------------------------------------
    rr = r_rim
    rx = hw * 0.68
    rim_prof = [(rr - 0.04 * k, -rx), (rr + 0.012 * k, -rx), (rr + 0.012 * k, -rx + 0.016 * k),
                (rr - 0.006 * k, -rx + 0.024 * k), (rr - 0.006 * k, rx - 0.024 * k), (rr + 0.012 * k, rx - 0.016 * k),
                (rr + 0.012 * k, rx), (rr - 0.04 * k, rx), (rr - 0.04 * k, -rx)]
    parts.append(pl.lathe_axis("rim", rim_prof, (1, 0, 0), (0, 0, 0), 36, "M_DarkMetal", False, False, 40))
    if rugged:
        for s in (-1, 1):
            for i in range(8):
                th = 2 * math.pi * (i + 0.5) / 8
                p = V((s * rx, 0, 0)) + _radial(th) * (rr - 0.014 * k)
                parts.append(pl.bolt(p, (s, 0, 0), 0.014 * k, 0.01 * k, "M_Steel", washer=False, bevel=False))

    # --- brass hub with 5 chunky spokes on each face -----------------------------------------------------
    hub_r = 0.08 * k
    hub_hw = hw * 0.72
    sx = hw * 0.5                      # spoke plane offset from the centre
    r0, r1 = (0.032 * k, 0.024 * k) if not rugged else (0.036 * k, 0.027 * k)
    for s in (-1, 1):
        for i in range(5):
            th = math.radians(90 + 72 * i)
            p0 = V((s * sx * 1.15, 0, 0)) + _radial(th) * (hub_r * 0.7)
            p1 = V((s * sx * 0.85, 0, 0)) + _radial(th) * (rr - 0.03 * k)
            parts.append(pl.sausage("spoke", [p0, p1], [r0, r1], 8, 1, "M_Brass", (True, True), 2, False, 60))
    parts.append(pl.lathe_axis("hub", [(0.0, -hub_hw), (hub_r * 0.85, -hub_hw), (hub_r, -hub_hw + 0.014 * k),
                                       (hub_r, hub_hw - 0.014 * k), (hub_r * 0.85, hub_hw), (0.0, hub_hw)],
                               (1, 0, 0), (0, 0, 0), 24, "M_Brass", False, False, 40))
    for s in (-1, 1):
        fx = s * (hub_hw - 0.012 * k)
        parts.append(pl.disc("flange", hub_r * 1.3, 0.026 * k, (1, 0, 0), (fx, 0, 0), "M_Brass", 20, 0.4))
        for i in range(5):
            th = math.radians(90 + 36 + 72 * i)
            p = V((fx + s * 0.013 * k, 0, 0)) + _radial(th) * (hub_r * 1.02)
            parts.append(pl.bolt(p, (s, 0, 0), 0.016 * k, 0.013 * k, "M_Steel", washer=False))
        # axle cap: steel dome with a brass ring
        x0 = s * (hub_hw + 0.004 * k)
        cap_len = hw - abs(x0) - 0.003
        parts.append(pl.lathe_axis("axlecap", [(0.052 * k, 0.0), (0.052 * k, cap_len * 0.3),
                                               (0.04 * k, cap_len * 0.75), (0.02 * k, cap_len * 0.97),
                                               (0.0, cap_len)], (s, 0, 0), (x0, 0, 0), 18, "M_Steel", True, False,
                                   50))
        parts.append(pl.band("cap_ring", 0.058 * k, 0.014 * k, 0.012 * k, (1, 0, 0),
                             (x0 + s * cap_len * 0.16, 0, 0), "M_Brass", 16))

    wheel = rw.join(parts, "Wheel", origin=(0, 0, 0))
    rw.smooth(wheel, 40)
    return wheel
