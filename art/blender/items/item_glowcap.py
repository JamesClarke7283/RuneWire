"""item_glowcap: a cluster of three chunky glowing mushrooms on a clump of moss and soil, about 0.3 x 0.2 x 0.27 m.

Three cartoon mushrooms (big, medium, small) with plump cream stems (flat) and fat domed caps that glow teal-blue
(emissive 4fd8ff over a deeper blue base), darker glowing gills underneath and white spots, leaning out of a
rounded clump of brown soil (flat) topped with soft moss cushions. One mesh object "Glowcap", origin at the centre.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as ml  # noqa: E402

il, rw, pl, V = ml.il, ml.rw, ml.pl, ml.V
ASSET = "item_glowcap"
rw.reset()

rnd = random.Random(3)
parts = []

# soil clump with moss on top
soil = il.blob("soil", (0.22, 0.18, 0.1), (0, 0, 0.02), ml.mat("Soil"), 2, 1.0, 4, 0.02)
il.purge_helpers()
parts.append(soil)
parts += il.moss_on(soil, [(-0.065, -0.035), (0.06, -0.04), (0.01, 0.055), (-0.075, 0.04), (0.075, 0.035)],
                    0.075, 2, ("Moss", "MossLight"), 0.42, 0.3)


def mushroom(base, axis, R, stem_h, spots, spin):
    """Stem from `base` along `axis`, cap of radius R on top; returns the parts."""
    ax = V(axis).normalized()
    out = []
    sr = R * 0.36
    stem = [(0.0, -0.01), (sr * 1.25, -0.01), (sr * 1.3, stem_h * 0.12), (sr * 1.05, stem_h * 0.45),
            (sr * 0.9, stem_h * 0.85), (sr * 0.95, stem_h + 0.004), (0.0, stem_h + 0.004)]
    out.append(il.lathe("stem", stem, ax, base, 12, ml.mat("MushStem"), 50))
    top = V(base) + ax * stem_h
    cap = il.curve_profile([(0.0, -R * 0.12), (R * 0.55, -R * 0.14), (R * 0.97, -R * 0.06), (R * 1.0, R * 0.08),
                            (R * 0.86, R * 0.42), (R * 0.5, R * 0.7), (0.0, R * 0.78)], 2)
    capo = il.lathe("cap", cap, ax, top, 15, ml.mat("CapGlow"), 55)
    # gills: the underside of the cap
    rw.set_mat_where(capo, ml.mat("CapGills"), lambda c, n: n.dot(ax) < -0.35)
    out.append(capo)
    # soft white spots: low round domes sitting on the cap
    u = ax.orthogonal().normalized()
    w = ax.cross(u).normalized()
    for k in range(spots + 1):
        if k == spots:
            d, r = ax, R * 0.2
        else:
            a = math.radians(spin + 360.0 * k / spots + rnd.uniform(-15, 15))
            el = math.radians(56 if k % 2 else 30)
            d = ax * math.cos(el) + (u * math.cos(a) + w * math.sin(a)) * math.sin(el)
            r = R * (0.2 if k % 2 else 0.24) * rnd.uniform(0.85, 1.1)
        hit = ml.on_surface(capo, top + ax * (R * 0.2), [d.normalized()])
        if hit:
            p, n = hit[0]
            dome = [(r, -0.003), (r * 0.92, 0.0018), (r * 0.52, 0.0042), (0.0, 0.005)]
            out.append(il.lathe("spot", dome, n, p, 8, ml.mat("CapSpot"), 80))
    return out


parts += mushroom((-0.015, 0.02, 0.05), (-0.12, 0.1, 1.0), 0.07, 0.13, 4, 10)
parts += mushroom((0.06, -0.03, 0.045), (0.45, -0.2, 1.0), 0.05, 0.085, 3, 40)
parts += mushroom((-0.075, -0.035, 0.04), (-0.75, 0.5, 1.0), 0.037, 0.075, 2, 70)

clump = rw.join(parts, "Glowcap")
il.finish_item(ASSET, (0.3, 0.2, 0.27))
