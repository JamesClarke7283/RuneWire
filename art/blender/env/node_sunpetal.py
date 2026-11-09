"""node_sunpetal: "Sunpetal Blooms", a gathering node (picked), about 1.0 x 1.0 x 1.0 m. Origin at the ground centre.

Nodes:
  Clump    static base: a low mound of dark soil with a leafy clump on it: a rosette of big, broad, round-tipped
           arching leaves (Leaf / LeafDark, two tiers), two closed buds on short stems and a pebble. Without the
           flowers it reads as a plain leafy plant waiting to bloom.
  Harvest  child of Clump, ONE object: six big golden sunpetal flowers on curving stems: cupped, softly glowing
           warm yellow petals (SunBloom, rw.glow ffc934 0.9), domed glowing orange centres (SunBloomEye), green
           sepal cups and a small leaf on each stem (SunStem / SunSepal). The heads face outward and up all
           round (the game spins the node to a random yaw). Its origin is the ground centre: scaled to 0.05 the
           flowers sink into the clump (picked), scaled back to 1.0 they regrow.

Material notes (stationlib): the petals are "SunBloom", not "...petal"/"...flower", because Godot gives such names
the wind-sway foliage shader, which drops emission. Nothing in Harvest uses a foliage name, so stems and heads stay
together; the clump's Leaf / LeafDark do sway, but only by a millimetre this close to the node origin.

Collision: Col_Clump_0-convcolonly, one cylinder (radius 0.45, height 0.9).
"""
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatherlib as G  # noqa: E402

S, E, rw, pl, V, M = G.S, G.E, G.rw, G.pl, G.V, G.M
ASSET = "node_sunpetal"
S.reset()
rnd = random.Random(23)

# --- the clump: soil mound, two tiers of broad leaves, buds, pebbles -------------------------------------------------
base = [G.dome("soil", 0.27, 0.08, (0, 0, 0.012), (0, 0, 1), "Soil", 10, 1, 0.0, wall=False)]
for k in range(7):          # outer tier: long, low, arching out and down to the ground
    az = 360.0 * k / 7 + 12
    base.append(G.rosette_leaf(az, 0.05, rnd.uniform(0.5, 0.53), 0.07, rnd.uniform(0.2, 0.22), 0.07,
                               rnd.uniform(0.2, 0.22), "LeafDark" if k % 2 else "Leaf", seed=k, droop=0.8))
for k in range(5):          # inner tier: shorter and higher, filling the middle of the mound
    az = 360.0 * k / 5 + 40
    base.append(G.rosette_leaf(az, 0.02, rnd.uniform(0.32, 0.35), 0.1, rnd.uniform(0.32, 0.35), 0.17,
                               rnd.uniform(0.18, 0.2), "Leaf" if k % 2 else "LeafDark", seed=10 + k, droop=0.75))
# two closed buds that stay behind after picking (the plant is still "going to bloom")
for k, (az, r, h) in enumerate(((100, 0.12, 0.52), (300, 0.1, 0.46))):
    top = G.radial(az, r, h)
    base.append(pl.sausage("budstem", [G.radial(az, 0.02, 0.1), G.radial(az, r * 0.6, h * 0.6), top],
                           [0.018, 0.016, 0.015], 6, 2, S.mat("SunStem"), (False, False), 1, True, 60))
    base.append(rw.ico("bud", 0.045, 1, tuple(top + V((0, 0, 0.035))), (0, 0, az), (1.0, 1.0, 1.45), S.mat("SunSepal"),
                       None, 50))
    base.append(rw.cone("budtip", 0.028, 0.0, 0.045, 6, tuple(top + V((0, 0, 0.09))), (0, 0, 0), S.mat("SunBloom")))
for k, (a, d, s) in enumerate(((30, 0.48, 0.1),)):
    p = S.hull_rock("pebble", (s * 1.4, s * 1.2, s), tuple(G.radial(a, d)), seed=50 + k, n_points=8, bevel=0.0,
                    flat_bottom=0.45)
    base.append(G.on_ground(p))
clump = rw.join(base, "Clump", origin=(0, 0, 0))

# --- the sunpetals (all one Harvest object) ------------------------------------------------------------------------
fl = []
FLOWERS = (   # azimuth, head radius from the axis, head height, petal radius, centre radius, tilt (0 up .. 1 out)
    (20, 0.15, 0.88, 0.19, 0.07, 0.45),
    (95, 0.3, 0.7, 0.17, 0.064, 0.7),
    (165, 0.22, 0.8, 0.18, 0.067, 0.55),
    (235, 0.31, 0.63, 0.165, 0.062, 0.72),
    (300, 0.24, 0.76, 0.175, 0.065, 0.6),
    (210, 0.06, 0.55, 0.15, 0.058, 0.3),
)
for k, (az, rh, h, R, rc, tilt) in enumerate(FLOWERS):
    head = G.radial(az, rh, h)
    out = G.radial(az, 1.0) if rh > 0 else G.radial(az + 180, 1.0)
    facing = (out * tilt + V((0, 0, 1)) * (1.0 - tilt * 0.5)).normalized()
    parts, back = G.flower_head(head, facing, R, rc, 8, seed=30 + k, spin=rnd.uniform(0, 40), cup=0.25, eye_segs=8)
    fl += parts
    b0 = G.radial(az, rh * 0.15, 0.08)
    pts = [b0, G.radial(az, rh * 0.35, h * 0.45), G.radial(az, rh * 0.75, h * 0.8) - facing * 0.04, back]
    fl.append(pl.sausage("stem", pts, [0.024, 0.021, 0.019, 0.018], 6, 1, S.mat("SunStem"), (False, False), 1,
                         True, 60))
    # a small leaf halfway up the stem, on the outside
    mid = G.radial(az, rh * 0.4, h * 0.5)
    la = az + (35 if k % 2 else -35)
    tip = mid + G.radial(la, 0.15, 0.06)
    fl.append(G.ribbon("stemleaf", [mid, (mid + tip) / 2 + V((0, 0, 0.03)), tip], [0.03, 0.065, 0.0],
                       V((0, 0, 1)).cross(tip - mid), "SunSepal", keel=0.15, thick=0.01, res=1))

harvest = G.join_harvest(fl, (0, 0, 0), clump)

E.col_cyl("Clump", 0.45, 0.9, (0, 0, 0.45))
S.ground_centre([clump])
G.finish_node(ASSET, (1.0, 1.0, 1.0), 3000, clump, harvest, "ground centre",
              preview_glows={"SunBloom": ("ffd000", "ffd84a", 0.22), "SunBloomEye": ("e05a10", "ff7f1e", 0.4)})
