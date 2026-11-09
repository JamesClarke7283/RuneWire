"""enemy_golem: Rune Golem of the Hollow Choir (origin on the ground between the feet, ~2.8 m tall).

A hunched, gorilla-like boulder construct: a tapered chest leaning forward under a high back hump,
huge mossy shoulders, a small head sunk low and forward between them with one glowing eye slit under
an angry brow, club-like forearms ending in giant blocky fists, and short stubby legs.
Faceted cartoon boulders (M_StoneRough, darker tinted rocks at the joints) are held together by
glowing violet rune magic (M_RuneGlow): an energy core sits in every joint and glows through the
seams, a few pebbles float in the gaps, and jagged cracks and carved runes glow on the rocks.
Violet crystals grow out of the back.

Hierarchy (spec Batch B):
  Hips              pivot (0, 0.05, 1.10)
    Torso           pivot at the waist
      Head          pivot at the neck
      ArmL          pivot at the left shoulder (+X)
        ForearmL    pivot at the elbow; big rock fist
      ArmR          pivot at the right shoulder (-X)
        ForearmR
    LegL            pivot at the left hip; stubby rock leg
    LegR

Every joint has a glowing core sphere centred on its pivot and the rocks on both sides overlap it,
so rotating a node about its pivot never opens a hole (the seam just shows more glow).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "parts"))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import magiclib as ml  # noqa: E402
import partlib as pl  # noqa: E402
from mathutils import Vector as V  # noqa: E402

ASSET = "enemy_golem"
rw.reset()

# ---------------------------------------------------------------- materials
STONE = "M_StoneRough"
STONE_D = "M_StoneRough__7d7598"     # cooler, darker rocks: joints, pelvis, knuckles, toes
TUSK = "M_StoneRough__efe6d2"
GLOW = "M_RuneGlow"
CORE = "M_RuneGlow__8a4dff"          # joint energy cores: a deeper violet than the cracks
pl.tint_emission(CORE, "8a4dff", 3.0)
CRYSTAL = "M_Crystal__a066ff"
pl.tint_emission(CRYSTAL, "a066ff", 2.2)
eye_mat = rw.glow("GolemEye", "f6e8ff", 6.0)
socket = rw.flat("GolemSocket", "1f1530", 0.9)
rw.flat("GolemMoss", "4fa233", 0.95)
rw.flat("GolemMossLight", "93d24e", 0.95)

# ---------------------------------------------------------------- pivots
HIPS_P = V((0.0, 0.05, 1.10))
WAIST_P = V((0.0, 0.06, 1.36))
NECK_P = V((0.0, -0.40, 2.20))
LEG_P = {1: V((0.40, 0.08, 1.00)), -1: V((-0.40, 0.08, 1.00))}
SHO_P = {1: V((0.90, -0.10, 2.12)), -1: V((-0.90, -0.10, 2.12))}
ELB_P = {1: V((1.02, -0.18, 1.52)), -1: V((-1.02, -0.18, 1.52))}


def rock(name, c, r, rot=None, seed=1, n=16, boxy=3.8, mat=STONE, bevel=0.035, segs=1, clip=None, wobble=0.07,
         jitter=0.07, taper=0.0):
    return ml.rock(name, c, r, rot, seed, n, jitter, boxy, wobble, mat, bevel, segs, clip, taper=taper)


def core(name, c, r):
    """Glowing rune-energy core centred on a joint pivot (shows in the seams between rocks)."""
    return cl.sphere(name, c, r, 12, 6, CORE)


def pebble(name, c, r, seed):
    return rock(name, c, (r, r * 0.9, r * 0.8), seed=seed, n=10, boxy=2.6, mat=STONE_D, bevel=0.015)


def mir(s, pairs):
    """Mirror (azimuth, elevation) control pairs for the side s (+1 left, -1 right)."""
    return [(az * s, el) for (az, el) in pairs]


def crack(name, target, c, ctrl, w, seed, branches=()):
    return ml.crack(name, target, c, ctrl, w * 1.3, zig=0.07, kinks=1, seed=seed, branches=branches, step_deg=5.0)


def glyph(name, target, c, key, face, size, w, up=(0, 0, 1)):
    return ml.surface_glyph(name, target, c, key, face, size, w * 1.25, up=up, per_unit=20)


# ======================================================================== Hips (root)
hips = []
pelvis_c = V((0.0, 0.08, 1.06))
pelvis = rock("pelvis", pelvis_c, (0.56, 0.37, 0.25), seed=11, n=16, mat=STONE_D, boxy=3.4)
hips.append(pelvis)
hips += crack("pelvis_crack", pelvis, pelvis_c, [(-75, -5), (-25, 6), (25, -6), (75, 6)], 0.03, 3)
key_c = V((0.0, -0.27, 1.0))
keystone = rock("keystone", key_c, (0.17, 0.12, 0.17), seed=12, n=12, boxy=3.2, bevel=0.025, taper=0.2)
hips.append(keystone)
hips += glyph("key_rune", keystone, key_c, "tiwaz", (0, -5), 0.17, 0.016)
hips_node = cl.node("Hips", hips, HIPS_P)

# ======================================================================== Torso
torso = [core("waist_core", WAIST_P + V((0.0, -0.02, 0.02)), 0.24)]
torso.append(rock("waist", WAIST_P + V((0.0, 0.02, 0.03)), (0.47, 0.36, 0.25), seed=21, n=14, mat=STONE_D, boxy=3.0))
for k, (p, r) in enumerate(((V((0.52, -0.08, 1.4)), 0.085), (V((-0.51, -0.02, 1.43)), 0.08),
                            (V((0.0, 0.46, 1.45)), 0.09))):
    torso.append(pebble("waist_pebble", p, r, 100 + k))
# chest: a massive tapered slab leaning forward, a big carved rune with cracks bursting from it
chest_c = V((0.0, -0.13, 1.86))
chest = rock("chest", chest_c, (0.62, 0.44, 0.44), rot=(24, 0, 0), seed=22, n=16, boxy=4.2, bevel=0.04, taper=0.3)
torso.append(chest)
torso += glyph("chest_rune", chest, chest_c, "algiz", (0, -14), 0.34, 0.028, up=(0, 0.42, 1))
torso += crack("chest_crack_l", chest, chest_c, [(16, 26), (34, 36), (56, 30), (80, 40)], 0.034, 5,
               branches=[(0.55, [(52, 56)], 0.6)])
torso += crack("chest_crack_r", chest, chest_c, [(-14, -14), (-32, -26), (-56, -22), (-80, -34)], 0.034, 6,
               branches=[(0.5, [(-46, -2)], 0.55)])
belly_c = V((0.0, -0.42, 1.5))
belly = rock("belly", belly_c, (0.34, 0.18, 0.18), rot=(26, 0, 0), seed=23, n=12, boxy=3.4, taper=-0.15)
torso.append(belly)
# upper back hump: the highest point, crystals growing out of its back, a moss patch on top
hump_c = V((0.0, 0.24, 2.24))
hump = rock("hump", hump_c, (0.58, 0.42, 0.38), rot=(-10, 0, 0), seed=24, n=16, boxy=3.6)
torso.append(hump)
torso += crack("hump_crack_a", hump, hump_c, [(150, 45), (168, 18), (182, -8), (204, -32)], 0.036, 8,
               branches=[(0.45, [(222, 8)], 0.6)])
torso += crack("hump_crack_b", hump, hump_c, [(122, -18), (140, -38), (162, -52)], 0.03, 9)
torso += ml.moss_cap("hump_moss", hump, hump_c, up=(0, 0.1, 1), reach=34, thick=0.05, drips=[(90, 16), (260, 10)],
                     seed=4)
for k, (x, ang, L, rr) in enumerate(((0.2, 24, 0.5, 0.095), (-0.18, -20, 0.44, 0.085), (0.0, 2, 0.62, 0.11),
                                      (0.38, 44, 0.3, 0.065), (-0.37, -40, 0.3, 0.065))):
    base = V((x, 0.5 + 0.05 * abs(x), 2.3 - 0.3 * abs(x)))
    axis = V((math.sin(math.radians(ang)) * 0.7, 0.75, 0.75)).normalized()
    torso.append(pl.crystal("crystal", tuple(base - axis * 0.1), tuple(axis), L, rr, 6, 0.3, 0.1, CRYSTAL,
                            spin=17 * k))
# huge shoulders the head sinks between, blanketed with moss
for s in (1, -1):
    sc = V((0.6 * s, -0.04, 2.3))
    cap = rock("shoulder_cap", sc, (0.42, 0.44, 0.3), rot=(16, -14 * s, 0), seed=25 + (s > 0), n=16, boxy=3.8)
    torso.append(cap)
    torso += ml.moss_cap("shoulder_moss", cap, sc, up=(0.15 * s, -0.1, 1), reach=54, thick=0.06,
                         drips=[(0 if s > 0 else 180, 22), (120, 18), (250, 14)], seed=6 + (s > 0))
    torso += crack("shoulder_crack", cap, sc, mir(s, [(-20, -10), (10, -28), (45, -20), (70, -38)]), 0.03, 10 + (s > 0))
torso_node = cl.node("Torso", torso, WAIST_P, hips_node)

# ======================================================================== Head
head = [core("neck_core", NECK_P, 0.15)]
skull_c = V((0.0, -0.56, 2.3))
skull = rock("skull", skull_c, (0.26, 0.24, 0.22), seed=31, n=16, boxy=3.8, bevel=0.03, taper=0.12)
head.append(skull)
# eye slit: a dark recessed socket with a glowing V-shaped slit inside, under a heavy angry brow
eye_ctrl = [(-33, 25), (-16, 19), (0, 16), (16, 19), (33, 25)]
pts, nrms = ml.surface_path(skull, skull_c, eye_ctrl, 0.0, 0, 3.0)
head.append(ml.ribbon("eye_socket", pts, nrms, [0.05] * len(pts), 0.02, socket, 8, 0.2, taper=(True, True)))
pts2 = [p + n * 0.013 for p, n in zip(pts, nrms)]
wid = [0.03 * (0.4 + 0.6 * max(0.0, math.sin(math.pi * i / (len(pts2) - 1))) ** 0.5) for i in range(len(pts2))]
head.append(ml.ribbon("eye_slit", pts2, nrms, wid, 0.012, eye_mat, 8, 0.1))
for s in (1, -1):
    bc = V((0.14 * s, -0.75, 2.455))
    head.append(rock("brow", bc, (0.14, 0.1, 0.06), rot=(12, -26 * s, 0), seed=32 + (s > 0), n=12, boxy=3.2,
                     bevel=0.02))
# glowing grimace: rune light leaking between the skull and the jaw
head.append(cl.ellipsoid("mouth_glow", V((0.0, -0.765, 2.238)), (0.15, 0.045, 0.024), 14, 6, GLOW))
jaw_c = V((0.0, -0.66, 2.15))
jaw = rock("jaw", jaw_c, (0.23, 0.17, 0.09), rot=(-8, 0, 0), seed=34, n=12, boxy=3.4, mat=STONE_D, bevel=0.02)
head.append(jaw)
for s in (1, -1):
    b = V((0.135 * s, -0.78, 2.19))
    head.append(cl.sweep("tusk", [b, b + V((0.01 * s, -0.02, 0.05)), b + V((0.025 * s, -0.025, 0.1))],
                         [0.032, 0.023, 0.0], 8, TUSK))
head += crack("skull_crack", skull, skull_c, [(55, 55), (85, 35), (115, 20)], 0.022, 12)
head += ml.moss_cap("skull_moss", skull, skull_c, up=(0, 0.35, 1), reach=30, thick=0.035, seed=9, top=0.45)
head_node = cl.node("Head", head, NECK_P, torso_node)

# ======================================================================== Arms
for s, side in ((1, "L"), (-1, "R")):
    S = SHO_P[s]
    E = ELB_P[s]
    arm = [core("shoulder_core", S, 0.24)]
    delt_c = S + V((0.08 * s, 0.0, 0.02))
    delt = rock("deltoid", delt_c, (0.34, 0.36, 0.32), rot=(0, 10 * s, 0), seed=41 + (s > 0), n=16, boxy=3.6,
                bevel=0.035)
    arm.append(delt)
    arm += glyph("delt_rune", delt, delt_c, "kenaz" if s > 0 else "sowilo", (90 * s, -8), 0.22, 0.02)
    arm += ml.moss_cap("delt_moss", delt, delt_c, up=(0.3 * s, 0.0, 1), reach=36, thick=0.04, seed=12 + (s > 0),
                       top=0.45, drips=[(0, 12)])
    up_c = V((1.0 * s, -0.16, 1.79))
    upper = rock("upper_arm", up_c, (0.23, 0.24, 0.27), seed=43 + (s > 0), n=14, boxy=3.4, mat=STONE_D)
    arm.append(upper)
    arm.append(pebble("elbow_pebble", V((1.27 * s, -0.1, 1.58)), 0.075, 110 + (s > 0)))
    arm_node = cl.node("Arm" + side, arm, S, torso_node)

    fore = [core("elbow_core", E, 0.18)]
    fore.append(rock("elbow", E + V((0.0, 0.08, -0.01)), (0.18, 0.17, 0.16), seed=45 + (s > 0), n=12, mat=STONE_D))
    fa_c = V((1.06 * s, -0.24, 1.18))
    forearm = rock("forearm", fa_c, (0.27, 0.29, 0.31), seed=47 + (s > 0), n=16, boxy=3.8, bevel=0.035, taper=-0.24)
    fore.append(forearm)
    fore += crack("fore_crack", forearm, fa_c, mir(s, [(-30, 60), (-15, 25), (5, -5), (-10, -40)]), 0.032,
                  20 + (s > 0), branches=[(0.45, [(40, 10)], 0.6)])
    fore += glyph("fore_rune", forearm, fa_c, "ingwaz", (90 * s, 2), 0.22, 0.018)
    fore.append(core("wrist_core", V((1.07 * s, -0.27, 0.9)), 0.15))
    fist_c = V((1.1 * s, -0.3, 0.6))
    fist = rock("fist", fist_c, (0.42, 0.4, 0.33), seed=49 + (s > 0), n=16, boxy=4.2, bevel=0.04, taper=0.05)
    fore.append(fist)
    fore += crack("fist_crack", fist, fist_c, mir(s, [(150, 50), (105, 28), (80, 8), (70, -25)]), 0.03, 24 + (s > 0))
    # four curled fingers across the front of the fist, the thumb wrapped over them on the inside
    for k in range(4):
        fx = fist_c.x + (0.24 - 0.158 * k)
        fc = V((fx, fist_c.y - 0.32, fist_c.z + 0.03 - 0.012 * abs(k - 1.5)))
        fore.append(rock("finger", fc, (0.08, 0.1, 0.19), rot=(6, 0, 0), seed=60 + k + 7 * (s > 0), n=12, boxy=3.8,
                         mat=STONE_D, bevel=0.022))
    tc = V((fist_c.x - 0.13 * s, fist_c.y - 0.42, fist_c.z - 0.11))
    fore.append(rock("thumb", tc, (0.19, 0.08, 0.075), rot=(0, 12 * s, 0), seed=70 + (s > 0), n=12, boxy=3.4,
                     bevel=0.022))
    cl.node("Forearm" + side, fore, E, arm_node)

# ======================================================================== Legs
for s, side in ((1, "L"), (-1, "R")):
    P = LEG_P[s]
    leg = [core("hip_core", P, 0.21)]
    th_c = V((0.42 * s, 0.08, 0.86))
    leg.append(rock("thigh", th_c, (0.28, 0.3, 0.2), seed=81 + (s > 0), n=14, boxy=3.4, mat=STONE_D))
    leg.append(core("knee_core", V((0.43 * s, 0.05, 0.67)), 0.16))
    col_c = V((0.45 * s, 0.04, 0.46))
    col = rock("shin", col_c, (0.27, 0.29, 0.22), seed=83 + (s > 0), n=14, boxy=3.6, taper=0.1)
    leg.append(col)
    leg += crack("shin_crack", col, col_c, mir(s, [(-10, 60), (-5, 20), (10, -10), (30, -40)]), 0.028, 30 + (s > 0))
    leg.append(rock("kneecap", V((0.46 * s, -0.21, 0.65)), (0.14, 0.1, 0.12), seed=85 + (s > 0), n=12, boxy=3.2,
                    bevel=0.025))
    foot_c = V((0.48 * s, -0.12, 0.16))
    leg.append(rock("foot", foot_c, (0.34, 0.46, 0.2), seed=87 + (s > 0), n=16, boxy=4.0, clip=0.0, bevel=0.035))
    for k in range(3):
        tc = V((foot_c.x + (0.17 - 0.17 * k) * s, foot_c.y - 0.43, 0.085))
        leg.append(rock("toe", tc, (0.085, 0.09, 0.085), seed=90 + k + 5 * (s > 0), n=10, boxy=3.0, mat=STONE_D,
                        clip=0.0, bevel=0.018))
    cl.node("Leg" + side, leg, P, hips_node)

rw.finish(ASSET, "enemies", icon=True)
cl.report_nodes(["Hips", "Torso", "Head", "ArmL", "ForearmL", "ArmR", "ForearmR", "LegL", "LegR"])
cl.budget(15000)
cl.tri_breakdown()
if os.environ.get("RW_QUICK") != "1":
    cl.render_extra(ASSET, "enemies", ("front", "side"))
    # walk extreme + head turn (Godot: legs +-0.45 rad, arms -+0.27, forearms -0.25, torso roll 0.06)
    cl.render_pose(ASSET, "enemies", {"LegL": (26, 0, 0), "LegR": (-26, 0, 0), "ArmL": (-16, 0, 0),
                                      "ArmR": (16, 0, 0), "ForearmL": (-14, 0, 0), "ForearmR": (-14, 0, 0),
                                      "Torso": (4, -3.5, 0), "Head": (0, 0, 40)}, "pose")
    # slam wind-up (arms -2.4 rad, forearms -0.6, torso -0.15) and the smash (arms +0.5, torso +0.35)
    cl.render_pose(ASSET, "enemies", {"ArmL": (-137, 0, 0), "ArmR": (-137, 0, 0), "ForearmL": (-34, 0, 0),
                                      "ForearmR": (-34, 0, 0), "Torso": (-8.6, 0, 0)}, "pose_slam", view="side")
    cl.render_pose(ASSET, "enemies", {"ArmL": (28, 0, 0), "ArmR": (28, 0, 0), "Torso": (20, 0, 0),
                                      "Head": (0, 0, -45)}, "pose_smash")
