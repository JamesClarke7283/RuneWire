"""prop_arcane_altar: "Enchanter's Altar", a crafting station for the town plaza, about 1.6 x 1.6 x 2.2 m.
Origin at the ground centre; the front faces -Y.

Two octagonal masonry steps (M_Stone) with a glowing violet inlay ring on the upper step. On them stands an
octagonal pedestal of lavender-tinted rough stone: a moulded base, a shaft with a big glowing violet rune on
each of its eight faces (rw.glow a066ff), a flared capital with a riveted brass band, and a shallow top dish
holding a glowing rune circle. Four curved brass arms rise from the capital's diagonal faces, each with a
brass collar and knuckle ring, and end in a little glowing orb that points at the crystal. Candle clusters
(cream wax, warm flames) stand on the steps, and a few loose violet shards lie at the back.

Nodes:
  Altar       static body (steps, pedestal, runes, arms, candles).
  Crystal     child of Altar (rw.set_parent). A big faceted violet crystal (M_Crystal__a066ff) with three
              little orbiting shards and a tilted glowing violet halo ring with brass studs, all in one object. Its origin
              is at the crystal's own centre, 1.6 m up. The game bobs it and spins it about its vertical axis,
              and every part of it clears the brass arms at any spin angle.
  LightPoint  empty at the crystal centre (root level, so the light doesn't bob).

Collision: Col_Steps_0-convcolonly (a frustum ramp over the two steps) and Col_Pedestal_0-convcolonly (a
cylinder of radius 0.5 m, 1.95 m tall, around the pedestal, the arms and the crystal).
"""
import math
import os
import random
import sys

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stationlib as S  # noqa: E402

E, rw, pl, V, M = S.E, S.rw, S.pl, S.V, S.M
ASSET = "prop_arcane_altar"
S.reset()
rnd = random.Random(5)
CRYSTAL_MAT = "M_Crystal__a066ff"
S.preview_glow(CRYSTAL_MAT, "7d4fe0", "a066ff", 0.9)   # preview only: violet glow (Godot tints M_Crystal__ itself)
STONE = "M_StoneRough__b0a8d0"
C8 = math.cos(math.radians(22.5))
P = []


def oct_lathe(name, prof_apothem, m, smooth=30):
    """Octagonal lathe with flats facing +-X / +-Y; the profile gives APOTHEMS (face distances), not radii."""
    prof = [(a / C8, z) for (a, z) in prof_apothem]
    return S.lathe(name, prof, 8, (0, 0, 0), m, smooth, spin=22.5)


# --- steps -----------------------------------------------------------------------------------------------------
P.append(oct_lathe("steps", [(0.0, 0.0), (0.8, 0.0), (0.8, 0.13), (0.77, 0.16), (0.61, 0.16), (0.61, 0.28),
                             (0.58, 0.31), (0.0, 0.31)], "M_Stone"))
# glowing inlay ring on the upper step, and a rune on each diagonal riser of the lower step
for k in range(8):
    th = math.radians(45 * k)
    a = 0.53
    n = V((math.cos(th), math.sin(th), 0.0))
    t = V((-n.y, n.x, 0.0))
    half = a * math.tan(math.radians(22.5))
    p0 = n * a - t * half + V((0, 0, 0.312))
    p1 = n * a + t * half + V((0, 0, 0.312))
    P.append(E.beam("inlay", tuple(p0), tuple(p1), 0.03, 0.01, M("RuneVioletSoft"), 0.0, extend=0.012))
for k, key in enumerate(("algiz", "sowilo", "ingwaz", "tiwaz")):
    th = math.radians(45 + 90 * k)
    n = V((math.cos(th), math.sin(th), 0.0))
    P += pl.glyph(key, n * 0.8 + V((0, 0, 0.075)), (-n.y, n.x, 0.0), (0, 0, 1), 0.1, 0.022, 0.012, M("RuneViolet"),
                  "steprune")

# --- pedestal: moulded base, rune shaft, flared capital, top dish -----------------------------------------------------
TOP = 0.92
PED = [(0.0, 0.31), (0.44, 0.31), (0.44, 0.36), (0.39, 0.4), (0.3, 0.45), (0.3, 0.8), (0.34, 0.84), (0.43, 0.88),
       (0.47, 0.9), (0.47, TOP - 0.02), (0.45, TOP), (0.33, TOP), (0.31, TOP - 0.025), (0.0, TOP - 0.025)]
P.append(oct_lathe("pedestal", PED, STONE))
P.append(oct_lathe("capband", [(0.335, 0.795), (0.355, 0.8), (0.355, 0.85), (0.335, 0.855)], "M_Brass"))
RUNES = ("algiz", "fehu", "tiwaz", "ingwaz", "dagaz", "sowilo", "othala", "kenaz")
for k in range(8):
    th = math.radians(-90 + 45 * k)
    n = V((math.cos(th), math.sin(th), 0.0))
    P += pl.glyph(RUNES[k], n * 0.3 + V((0, 0, 0.625)), (-n.y, n.x, 0.0), (0, 0, 1), 0.24, 0.042, 0.018,
                  M("RuneViolet"), "rune")
    # rivets on the brass band
    P.append(E.rivet("rivet", tuple(n * 0.357 + V((0, 0, 0.825))), 0.016, "M_Copper", lo=True))
# rune circle in the top dish: an octagonal ring and a central eye glyph
for k in range(8):
    th = math.radians(45 * k)
    n = V((math.cos(th), math.sin(th), 0.0))
    t = V((-n.y, n.x, 0.0))
    half = 0.2 * math.tan(math.radians(22.5))
    P.append(E.beam("dishring", tuple(n * 0.2 - t * half + V((0, 0, TOP - 0.022))),
                    tuple(n * 0.2 + t * half + V((0, 0, TOP - 0.022))), 0.03, 0.008, M("RuneViolet"), 0.0, extend=0.014))
P += pl.glyph("eye", V((0, 0, TOP - 0.022)), (1, 0, 0), (0, 1, 0), 0.2, 0.026, 0.008, M("RuneViolet"), "dishrune")

# --- brass arms from the four diagonal faces of the capital ----------------------------------------------------------
ARM = [(0.37, TOP - 0.03), (0.52, 1.1), (0.585, 1.38), (0.53, 1.68), (0.39, 1.9)]
for k in range(4):
    th = math.radians(45 + 90 * k)
    d = V((math.cos(th), math.sin(th), 0.0))
    pts = [d * r + V((0, 0, z)) for (r, z) in ARM]
    P.append(pl.sausage("arm", pts, [0.042, 0.038, 0.034, 0.03, 0.026], 8, 3, S.mat("M_Brass"), (False, True), 2,
                        True, 60))
    P.append(S.lathe("armcollar", [(0.0, -0.04), (0.065, -0.04), (0.07, 0.0), (0.06, 0.035), (0.0, 0.04)], 8,
                     tuple(d * 0.45 + V((0, 0, TOP + 0.04))), "M_Brass", 40,
                     axis=tuple((pts[1] - pts[0]).normalized())))
    q = pts[2]
    P.append(S.lathe("knuckle", [(0.03, -0.03), (0.05, -0.022), (0.05, 0.022), (0.03, 0.03)], 8, tuple(q), "M_Copper",
                     40, axis=tuple((pts[3] - pts[1]).normalized())))
    tip = pts[-1]
    inward = (V((0, 0, 1.6)) - tip).normalized()
    P.append(S.lathe("tipcup", [(0.0, -0.02), (0.045, -0.02), (0.05, 0.02), (0.042, 0.035), (0.0, 0.03)], 8,
                     tuple(tip + inward * 0.01), "M_Brass", 40, axis=tuple(inward)))
    P.append(rw.ico("tiporb", 0.036, 1, tuple(tip + inward * 0.05), (0, 0, 0), (1, 1, 1), M("RuneViolet"), None, 0))

# --- candles on the steps ----------------------------------------------------------------------------------------------


def candle(x, y, z, r, h):
    out = [S.lathe("candle", [(0.0, 0.0), (r * 1.45, 0.0), (r * 1.35, 0.012), (r, 0.022), (r, h - 0.016),
                              (r * 0.78, h), (0.0, h - 0.006)], 8, (x, y, z), "Wax", 40)]
    out.append(rw.ico("drip", r * 0.42, 1, (x + r * 0.85, y - r * 0.4, z + h * 0.62), (0, 0, 0), (0.8, 0.8, 1.6),
                      M("Wax"), None, 0))
    out.append(rw.box("wick", (0.008, 0.008, 0.03), (x, y, z + h + 0.008), mat=M("Ink")))
    out.append(S.flame("cflame", (x, y, z + h + 0.012), 0.085, 0.026, "CandleFlame", 6))
    return out


for (ang, rad, z, group) in ((-122, 0.72, 0.16, ((0.0, 0.0, 0.046, 0.25), (0.08, -0.05, 0.04, 0.16),
                                                  (-0.06, -0.07, 0.034, 0.11))),
                             (-57, 0.73, 0.16, ((0.0, 0.0, 0.042, 0.17), (0.06, -0.06, 0.034, 0.1))),
                             (32, 0.55, 0.31, ((0.0, 0.0, 0.044, 0.21), (-0.06, 0.06, 0.036, 0.13))),
                             (150, 0.72, 0.16, ((0.0, 0.0, 0.042, 0.15),))):
    a = math.radians(ang)
    cx, cy = math.cos(a) * rad, math.sin(a) * rad
    for (dx, dy, r, h) in group:
        P += candle(cx + dx, cy + dy, z, r, h)

# loose violet shards at the back of the lower step
for k, (ang, L, spin) in enumerate(((100, 0.16, 10), (112, 0.11, 40), (75, 0.12, 70))):
    a = math.radians(ang)
    base = V((math.cos(a) * 0.68, math.sin(a) * 0.68, 0.16))
    dirv = (V((math.cos(a), math.sin(a), 0.0)) * 0.5 + V((0, 0, 0.8))).normalized()
    P.append(pl.crystal("shard", base, dirv, L, 0.034, 6, 0.32, 0.1, S.mat(CRYSTAL_MAT), spin))

altar = E.join(P, "Altar", origin=(0, 0, 0))
rw.smooth(altar, 30)

# --- the floating crystal (separate object, origin at its own centre) ------------------------------------------------
CZ = 1.6
HT, HB, MID = 0.5, 0.24, 0.3          # main crystal: top / bottom pyramid heights, prism band
cr = [E.bipyramid("crystal", 0.205, HT, HB, 8, (0, 0, 0), CRYSTAL_MAT, twist=0.0, mid=MID)]
for k, (ang, z, L) in enumerate(((20, 0.08, 0.15), (140, -0.1, 0.12), (260, 0.18, 0.13))):
    a = math.radians(ang)
    dirv = V((math.cos(a), math.sin(a), 0.0))
    cr.append(E.bipyramid("orbit", 0.042, L * 0.55, L * 0.45, 6, tuple(dirv * 0.31 + V((0, 0, z))), CRYSTAL_MAT,
                          twist=ang))
gyro = E.ring("halo", 0.37, 0.026, (0, 0, 0), (0, 0, 1), M("RuneVioletSoft"), 28, 6)
E.place([gyro], (0, 0, 0), (18, 0, 0))
cr.append(gyro)
for k in range(4):
    a = math.radians(45 + 90 * k)
    y = math.sin(a) * 0.37
    p = V((math.cos(a) * 0.37, y * math.cos(math.radians(18)), y * math.sin(math.radians(18))))
    cr.append(rw.ico("halostud", 0.042, 1, tuple(p), (0, 0, 0), (1, 1, 1), S.mat("M_Brass"), None, 0))
# the main crystal's own centre (middle of its height, on its axis) goes to (0, 0, CZ): the spin axis
E.place(cr, (0, 0, CZ - (HT - HB) / 2), (0, 0, 0))
crystal = E.join(cr, "Crystal", origin=(0, 0, CZ))
bpy.context.view_layer.update()
rw.flat_shade(crystal)
rw.smooth(crystal, 30)
pl.parent_keep(crystal, altar)
rw.empty("LightPoint", (0, 0, CZ))

# --- collision -------------------------------------------------------------------------------------------------------
E.col_frustum("Steps", 0.84, 0.62, 0.31, (0, 0, 0.155), 16)
E.col_cyl("Pedestal", 0.5, 1.95, (0, 0, 0.975), verts=12)
S.finish(ASSET, (1.6, 1.6, 2.2), 5000, nodes=("Altar", "Crystal", "LightPoint"))
print("RWCHECK %s Crystal bbox %s .. %s" % (ASSET, tuple(round(v, 3) for v in rw.bounds([crystal])[0]),
                                           tuple(round(v, 3) for v in rw.bounds([crystal])[1])))
