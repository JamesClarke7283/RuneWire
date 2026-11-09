"""enemy_ironclad: Ironclad Warwalker, the Cogwork Legion boss (origin on the ground, ~5.2 m tall).

Hierarchy (spec Batch B):
  Pelvis            pivot (0, 0, 2.6): dark-iron hip block with a wide girdle over the hips, hip sockets, a
                    hazard-striped waist collar, rust side skirts and a hazard codpiece
    Torso           pivot at the waist (0, 0, 2.95); yaws. Barrel-chested dark-iron hull with a rust-orange
                    armour roof and brass trim bands, on a round waist drum (no gap at any yaw); rust-orange chest
                    plate with a glowing furnace-grille "mouth"; copper boiler and two rusty smokestacks on the
                    back; hazard-striped pauldron over the left shoulder
      Head          armoured cockpit dome with one big glowing orange eye under an angry lid and brow.
                    ORIGIN AT THE EYE CENTRE: the game crits hits within 0.9 m of the Head origin
                    (enemy_ironclad.gd: weak_point = "Head")
      ArmL          pivot at the left shoulder (1.42, 0.05, 4.0): shoulder ball, strut and a big cannon
                    pointing -Y; the game pitches it about X to aim
        MuzzleL     empty at the cannon mouth
      ArmR          pivot at the right shoulder (-1.42, 0.05, 4.0): shoulder ball and a six-tube rocket pod
                    tilted up 22 degrees (rockets launch upward, then home in)
        MuzzleR     empty in front of the centre of the tubes
      Smoke_0       empty at the top of the left (+X) smokestack
      Smoke_1       empty at the top of the right smokestack
    ThighL/R        pivot at the hip (+-0.82, 0, 2.45): hip ball + rust-orange thigh armour, knee clevis, piston
      ShinL/R       pivot at the knee (+-0.82, -0.12, 1.5): knee ball and cap, dark shin with a hazard plate
        FootL/R     pivot at the ankle (+-0.82, 0, 0.52): ankle ball + big flat three-toed foot on the ground
Each child node carries the ball at its own pivot (hip, knee, ankle, shoulder) and the waist is a round drum in a
round collar, so joints show no gaps when rotated.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import rwlib as rw  # noqa: E402
import charlib as cl  # noqa: E402
import techlib as tl  # noqa: E402
pl = tl.pl
from mathutils import Matrix, Vector as V  # noqa: E402

ASSET = "enemy_ironclad"
rw.reset()
tl.setup()

PAINT, GLOW, GRILLE = tl.PAINT, tl.GLOW, tl.GRILLE
P = V((0, 0, 2.6))                      # pelvis pivot
WAIST = V((0, 0, 2.95))                 # torso pivot
SHO = {1: V((1.42, 0.05, 4.0)), -1: V((-1.42, 0.05, 4.0))}
HIP = {s: V((0.82 * s, 0.0, 2.45)) for s in (1, -1)}
KNEE = {s: V((0.82 * s, -0.12, 1.5)) for s in (1, -1)}
ANK = {s: V((0.82 * s, 0.0, 0.52)) for s in (1, -1)}
E = V((0, -1.2, 4.22))                  # eye (lens) centre = Head origin
SIDE = {1: "L", -1: "R"}
rocket_red = rw.flat("RocketRed", "d8452e", 0.5)
iris_glow = rw.glow("IronIris", "ff5a14", 2.2)
core_glow = rw.glow("IronCore", "ffe08a", 4.0)
RIGHT = Matrix.Rotation(math.radians(-90), 3, 'Y')    # local +Z -> -X

# ======================================================================== Pelvis
pel = []
pel.append(tl.loft("pelvis_block", [(2.2, 0.34, 0.3), (2.27, 0.5, 0.42), (2.5, 0.56, 0.48), (2.7, 0.56, 0.48),
                                    (2.72, 1.26, 0.52), (2.86, 1.3, 0.54), (2.9, 1.12, 0.46)], n=24, e=0.4,
                   mat="M_DarkMetal"))
for s in (1, -1):
    h = HIP[s]
    pel.append(cl.cyl("hip_socket", (0.4 * s, 0, h.z), (0.6 * s, 0, h.z), 0.27, 16, "M_DarkMetal"))
    pel.append(cl.torus("hip_rim", (0.6 * s, 0, h.z), 0.27, 0.04, tl.RY90, 16, 3, "M_Brass"))
    # rust skirt plate hanging from the girdle edge over the outside of the hip, flared out at the bottom
    pel.append(cl.rbox("skirt", (0.09, 0.8, 0.66), V((1.28 * s, -0.02, 2.5)), 0.04, "M_Rust",
                       Matrix.Rotation(math.radians(-9 * s), 3, 'Y'), segments=1))
    for y in (-0.28, 0.24):
        pel.append(cl.rivet(V((1.295 * s, y, 2.7)), 0.026, (s, 0, 0.16), "M_Brass"))   # on the tilted face
pel.append(cl.hazard_panel("codpiece", 0.56, 0.42, 0.04, (0, -0.52, 2.42), (12, 0, 0), stripe=0.13, bevel=0))
pel.append(cl.rbox("rear_plate", (0.6, 0.08, 0.4), (0, 0.5, 2.45), 0.03, "M_Rust", segments=1))
# hazard-striped waist collar that the torso's drum turns in
pel.append(tl.hazard_ring("waist_collar", (0, 0), 0.75, 0.6, 2.86, 3.0, count=10, slant=45, cols=28))
pel.append(cl.torus("collar_rim", (0, 0, 3.0), 0.675, 0.04, None, 28, 3, "M_Brass"))
pelvis = tl.node("Pelvis", pel, P)

# ======================================================================== Torso
tor = []
tor.append(cl.cyl("waist", (0, 0, 2.86), (0, 0, 3.2), 0.6, 24, "M_DarkMetal"))
HULL = [(3.0, 0.62, 0.5), (3.1, 0.84, 0.62), (3.4, 0.98, 0.74), (3.85, 1.07, 0.8), (4.25, 1.07, 0.78),
        (4.48, 0.98, 0.7), (4.6, 0.8, 0.56), (4.64, 0.55, 0.38)]
ROOF_Z = 4.36
hull = tl.loft("hull", [(z, a, b, 0.0, 0.05) for (z, a, b) in HULL], n=28, e=0.55, mat="M_DarkMetal")
rw.set_mat_where(hull, PAINT, lambda c, n: c.z > ROOF_Z)          # rust-orange armour roof (Legion paint)
tor.append(hull)


def hull_ab(z):
    """Hull half sizes (a, b) at height z (linear between the loft sections)."""
    for (z0, a0, b0), (z1, a1, b1) in zip(HULL[:-1], HULL[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
    return HULL[-1][1], HULL[-1][2]


for (z0, z1) in ((ROOF_Z - 0.05, ROOF_Z + 0.05), (3.1, 3.18)):    # brass trim bands hugging the hull
    secs = []
    for z in (z0, z1):
        a, b = hull_ab(z)
        secs.append((z, a + 0.03, b + 0.03, 0.0, 0.05))
    tor.append(tl.loft("hull_band", secs, n=28, e=0.55, mat="M_Brass", smooth_angle=60))
for k in range(8):                                                  # rivets along the roof band
    t = 2 * math.pi * (k + 0.5) / 8
    a, b = hull_ab(ROOF_Z)
    c, s_ = math.cos(t), math.sin(t)
    q = V((math.copysign(abs(c) ** 0.55, c) * (a + 0.04), 0.05 + math.copysign(abs(s_) ** 0.55, s_) * (b + 0.04),
           ROOF_Z))
    tor.append(cl.rivet(q, 0.028, V((q.x, q.y - 0.05, 0)), "M_Steel"))
# chest plate with a glowing furnace grille "mouth" and rivets
CP_C, CP_R = V((0, -0.66, 3.62)), (0.78, 0.2, 0.5)
tor.append(cl.ellipsoid("chest_plate", CP_C, CP_R, 20, 8, PAINT))
tor.append(cl.rbox("grille_frame", (0.72, 0.08, 0.36), (0, -0.865, 3.5), 0.04, "M_Brass", segments=1))
tor.append(cl.rbox("grille", (0.6, 0.08, 0.26), (0, -0.885, 3.5), 0.02, GRILLE, segments=1))
for k in range(5):
    tor.append(rw.box("grille_slot", (0.065, 0.03, 0.19), ((k - 2) * 0.115, -0.915, 3.5), mat=GLOW))
for x in (-0.52, 0.52):
    for z in (3.4, 3.72):
        p = cl.head_point(CP_C, CP_R, x, z, 0.0)
        tor.append(cl.rivet(p, 0.028, cl.head_normal(CP_C, CP_R, p), "M_Brass"))
# brass pressure gauge on the right flank, fed by a copper pipe from the boiler
rw.flat("GaugeFace", "f4ecd4", 0.5)
rw.flat("Needle", "a8231a", 0.5)
hull.data.update()
GP = cl.surface_points(hull, (0, 0.05, 3.55), [(-62.0, 2.0)])[0]
GN = V((GP.x, GP.y - 0.05, 0)).normalized()
GN = (GN + V((-0.25, -0.1, 0))).normalized()          # face a little more toward the camera side
GU = V((0, 0, 1)).cross(GN).normalized()
GV = GN.cross(GU).normalized()
tor.append(cl.cyl("gauge_bezel", GP - GN * 0.04, GP + GN * 0.05, 0.15, 16, "M_Brass", bevel=0.012))
tor.append(cl.cyl("gauge_face", GP + GN * 0.045, GP + GN * 0.056, 0.118, 16, "GaugeFace"))
for k in range(5):                                    # tick marks around the upper arc
    a = math.radians(-70 + 35 * k)
    q = GP + GN * 0.058 + (GU * math.sin(a) + GV * math.cos(a)) * 0.092
    tor.append(cl.rbox("gauge_tick", (0.018, 0.012, 0.036), q, 0.004, "M_DarkMetal",
                       cl.axes_matrix(GU * math.cos(a) - GV * math.sin(a), -GN, GU * math.sin(a) + GV * math.cos(a)),
                       segments=1))
ND = (GU * math.sin(math.radians(48)) + GV * math.cos(math.radians(48))).normalized()
tor.append(cl.sweep("gauge_needle", [GP + GN * 0.064 - ND * 0.02, GP + GN * 0.064 + ND * 0.09], [0.016, 0.0], 6,
                    "Needle", scale=(0.4, 1.0), up=GN))
tor.append(cl.sphere("gauge_pin", GP + GN * 0.062, 0.02, 8, 4, "M_Brass"))
pipe = [GP - GN * 0.02 + GV * -0.06, V((-1.085, 0.0, 3.47)), V((-1.07, 0.45, 3.5)), V((-0.94, 0.74, 3.68)),
        V((-0.79, 0.8, 3.82))]
tor.append(cl.sweep("gauge_pipe", cl.bezier(pipe[0], pipe[1], pipe[2], 6, pipe[3]) + [pipe[4]], 0.035, 8,
                    "M_Copper"))
tor.append(cl.torus("pipe_clamp", V((-1.075, 0.22, 3.48)), 0.042, 0.014, tl.rot_z_to((0, 1, 0.05)), 10, 3,
                    "M_Brass"))
# shoulder sockets
for s in (1, -1):
    tor.append(cl.cyl("sho_socket", (0.9 * s, 0.05, 4.0), (1.13 * s, 0.05, 4.0), 0.3, 16, "M_DarkMetal"))
    tor.append(cl.torus("sho_rim", (1.12 * s, 0.05, 4.0), 0.3, 0.04, tl.RY90, 16, 3, "M_Brass"))
# hazard-striped pauldron over the left shoulder (the cannon arm swings beneath it)
PC = V((1.45, 0.05, 4.1))
tor.append(cl.dome("pauldron", PC, (0.52, 0.52, 0.42), None, 0.6, 24, 6, PAINT))
tor.append(tl.hazard_ring("paul_band", (PC.x, PC.y), 0.54, 0.46, PC.z - 0.16, PC.z - 0.06, count=6, slant=45,
                          cols=24))
tor.extend(cl.rivet_ring(PC + V((0, 0, 0.3)), 0.3, 4, 0.026, (0, 0, 1), "M_Brass", 45, outward=True))
# copper boiler across the back with brass bands and domed ends
BOIL = V((0, 0.8, 4.02))
tor.append(cl.cyl("boiler", (-0.7, BOIL.y, BOIL.z), (0.7, BOIL.y, BOIL.z), 0.42, 20, "M_Copper"))
tor.append(cl.dome("boiler_end", (0.7, BOIL.y, BOIL.z), (0.42, 0.42, 0.14), tl.RY90, 0.5, 20, 3, "M_Copper"))
tor.append(cl.dome("boiler_end", (-0.7, BOIL.y, BOIL.z), (0.42, 0.42, 0.14), RIGHT, 0.5, 20, 3, "M_Copper"))
for x in (-0.36, 0.36):
    tor.append(cl.torus("boiler_band", (x, BOIL.y, BOIL.z), 0.425, 0.035, tl.RY90, 20, 3, "M_Brass"))
# two rusty smokestacks rising from the boiler, splayed back a little
SMOKE = []
for s in (1, -1):
    base = V((0.46 * s, 0.86, 4.3))
    ax = V((0.07 * s, 0.16, 1.0)).normalized()
    prof = [(0.0, 0.0), (0.15, 0.0), (0.15, 0.6), (0.19, 0.67), (0.23, 0.8), (0.23, 0.9), (0.17, 0.9),
            (0.17, 0.82), (0.0, 0.82)]
    st = pl.lathe_axis("stack", prof, tuple(ax), tuple(base), 14, "M_Rust", False, False, 40)
    rw.set_mat_where(st, GRILLE, lambda c, n, b=base, a=ax: (c - b).dot(a) > 0.815 and
                     ((c - b) - a * (c - b).dot(a)).length < 0.175)
    tor.append(st)
    tor.append(cl.torus("stack_band", base + ax * 0.4, 0.155, 0.03, tl.rot_z_to(ax), 14, 3, "M_Brass"))
    tor.append(cl.torus("stack_lip", base + ax * 0.9, 0.2, 0.035, tl.rot_z_to(ax), 14, 3, "M_Brass"))
    SMOKE.append(base + ax * 0.93)
# a hatch on the back of the roof
tor.append(cl.cyl("hatch", (0, 0.32, 4.58), (0, 0.32, 4.67), 0.24, 16, "M_Brass"))
tor.append(cl.sweep("hatch_handle", [(-0.1, 0.32, 4.66), (-0.08, 0.32, 4.73), (0.08, 0.32, 4.73), (0.1, 0.32, 4.66)],
                    0.02, 6, "M_Steel"))
torso = tl.node("Torso", tor, WAIST, pelvis)

# ======================================================================== Head (origin at the eye)
head = []
HC, HR = V((0, -0.62, 4.22)), (0.6, 0.56, 0.5)
head.append(cl.ellipsoid("cockpit", HC, HR, 24, 12, "M_DarkMetal"))
ER = 0.3                                # lens radius (the eye is the weak point: keep it big)
head.append(cl.cyl("eye_barrel", (0, -0.95, E.z), (0, E.y - 0.005, E.z), ER + 0.045, 24, "M_DarkMetal"))
head.append(cl.torus("eye_bezel", (0, E.y - 0.012, E.z), ER + 0.045, 0.06, tl.RX90, 28, 5, "M_Brass"))
head.extend(tl.bolt_ring((0, E.y - 0.07, E.z), (0, -1, 0), ER + 0.045, 6, 0.034, "M_Steel", 0))
head.append(cl.dome("lens", E, (ER, ER, 0.065), tl.RX90, 0.5, 20, 3, GLOW))
head.append(cl.torus("iris", E + V((0, -0.056, -0.034)), 0.14, 0.027, tl.RX90, 16, 3, iris_glow))
head.append(cl.ellipsoid("pupil", E + V((0, -0.058, -0.034)), (0.09, 0.028, 0.09), 12, 5, core_glow))
head.append(tl.lid_plate("eye_lid", (0, E.y - 0.032, E.z), ER * 1.056, ER * 0.593, ER * 0.093, 0.12, "M_DarkMetal",
                         bevel=0.012))
for sd in (1, -1):                      # angry V brow ridge along the lid edge
    a = V((0.0, E.y - 0.095, E.z + 0.05))
    b = V((0.278 * sd, E.y - 0.048, E.z + 0.21))
    head.append(cl.sweep("brow", [a, a.lerp(b, 0.5) + V((0, -0.013, 0.013)), b], [0.064, 0.064, 0.05], 10, PAINT,
                         scale=(0.7, 1.0), up=(0, -0.4, 1)))
    head.append(cl.rivet(b + V((0.022 * sd, -0.032, 0.012)), 0.032, (0.3 * sd, -1, 0.3), "M_Brass"))
# crest along the top, brass "ear" vents with glowing slots on the sides, a periscope
crest = []
for y in (-1.0, -0.82, -0.6, -0.36, -0.18):
    t = 1 - ((y - HC.y) / HR[1]) ** 2
    crest.append(V((0, y, HC.z + HR[2] * math.sqrt(max(0.0, t)) + 0.02)))
head.append(cl.sweep("crest", crest, [0.05, 0.075, 0.08, 0.07, 0.04], 10, PAINT, scale=(1.0, 0.5), up=(0, 0, 1)))
for s in (1, -1):
    ec = V((0.585 * s, -0.6, 4.24))
    head.append(cl.cyl("ear", ec - V((0.06 * s, 0, 0)), ec + V((0.05 * s, 0, 0)), 0.17, 14, "M_Brass"))
    head.append(cl.cyl("ear_vent", ec + V((0.045 * s, 0, 0)), ec + V((0.06 * s, 0, 0)), 0.12, 12, GRILLE))
    for k in (-1, 0, 1):
        head.append(rw.box("ear_slot", (0.012, 0.17, 0.035), tuple(ec + V((0.062 * s, 0, 0.06 * k))), mat=GLOW))
head.append(cl.sweep("periscope", [(-0.3, -0.45, 4.6), (-0.32, -0.47, 4.82), (-0.32, -0.6, 4.86)], 0.045, 8,
                     "M_DarkMetal"))
head.append(cl.ellipsoid("periscope_lens", (-0.32, -0.64, 4.86), (0.04, 0.02, 0.04), 8, 4, GLOW))
head_node = tl.node("Head", head, E, torso)

# ======================================================================== ArmL: cannon
S = SHO[1]
arm = [cl.sphere("shoulder", S, 0.33, 16, 8, "M_Steel")]
BRE = V((1.6, 0.0, 3.38))               # breech block centre (low enough to clear the pauldron when aiming down)
arm.append(cl.cyl("arm_strut", S, BRE + V((0, 0.05, 0.2)), 0.19, 14, "M_DarkMetal"))
arm.append(cl.torus("strut_band", S.lerp(BRE, 0.55), 0.2, 0.035, tl.rot_z_to(BRE - S), 14, 3, "M_Brass"))
arm.append(cl.rbox("breech", (0.62, 0.7, 0.56), BRE, 0.1, "M_DarkMetal"))
arm.append(cl.hazard_panel("breech_haz", 0.52, 0.32, 0.02, BRE + V((0.316, 0, 0)), (0, 0, 90), stripe=0.1,
                           bevel=0))
BY0 = BRE.y - 0.35
prof = [(0.0, 0.0), (0.28, 0.0), (0.28, 0.1), (0.235, 0.17), (0.215, 1.22), (0.26, 1.28), (0.31, 1.34),
        (0.31, 1.62), (0.27, 1.66), (0.16, 1.66), (0.16, 1.5), (0.0, 1.5)]
barrel = pl.lathe_axis("barrel", prof, (0, -1, 0), (BRE.x, BY0, BRE.z), 18, "M_DarkMetal", False, False, 40)
rw.set_mat_where(barrel, GRILLE, lambda c, n: c.y < BY0 - 1.49 and V((c.x - BRE.x, 0, c.z - BRE.z)).length < 0.165)
arm.append(barrel)
for h in (0.45, 0.9):
    arm.append(cl.torus("barrel_band", (BRE.x, BY0 - h, BRE.z), 0.222, 0.04, tl.RX90, 18, 3, "M_Brass"))
for sx in (1, -1):
    arm.append(rw.box("brake_slot", (0.05, 0.17, 0.13), (BRE.x + sx * 0.29, BY0 - 1.48, BRE.z), mat=GRILLE))
arm.append(cl.cyl("recoil", (BRE.x, BY0 + 0.1, BRE.z + 0.3), (BRE.x, BY0 - 0.7, BRE.z + 0.3), 0.085, 12, "M_Brass"))
arm.append(cl.cyl("recoil_cap", (BRE.x, BY0 - 0.7, BRE.z + 0.3), (BRE.x, BY0 - 0.76, BRE.z + 0.3), 0.06, 12, "M_Steel"))
arm.append(cl.rbox("recoil_clamp", (0.1, 0.1, 0.12), (BRE.x, BY0 - 0.6, BRE.z + 0.24), 0.02, "M_DarkMetal",
                   segments=1))
arm.extend(tl.piston("arm_piston", S + V((0.24, -0.08, -0.12)), BRE + V((0.26, -0.18, 0.22)), 0.05))
arm_l = tl.node("ArmL", arm, S, torso)
tl.empty("MuzzleL", (BRE.x, BY0 - 1.7, BRE.z), arm_l, 0.2)

# ======================================================================== ArmR: rocket pod
S = SHO[-1]
arm = [cl.sphere("shoulder", S, 0.33, 16, 8, "M_Steel")]
PODC = V((-1.62, -0.06, 4.52))
RP = Matrix.Rotation(math.radians(-22), 3, 'X')       # launch face tilted up 22 degrees
FN = RP @ V((0, -1, 0))
arm.append(cl.rbox("pod_mount", (0.36, 0.5, 0.42), V((-1.55, 0.05, 4.2)), 0.05, "M_DarkMetal", segments=1))
arm.append(cl.rbox("pod", (0.9, 1.1, 0.8), PODC, 0.1, PAINT, RP))
for ly in (-0.36, 0.36):
    arm.append(cl.rbox("pod_trim", (0.93, 0.07, 0.83), PODC + RP @ V((0, ly, 0)), 0.03, "M_Brass", RP, segments=1))
FACE = PODC + RP @ V((0, -0.55, 0))
arm.append(cl.rbox("pod_face", (0.78, 0.05, 0.66), FACE + FN * 0.01, 0.03, GRILLE, RP, segments=1))
for lx in (-0.25, 0.0, 0.25):
    for lz in (-0.15, 0.15):
        c = PODC + RP @ V((lx, -0.575, lz))
        arm.append(cl.torus("tube_ring", c, 0.1, 0.028, tl.rot_z_to(FN), 12, 3, "M_Brass"))
        arm.append(cl.sweep("warhead", [c - FN * 0.04, c + FN * 0.03, c + FN * 0.1], [0.072, 0.06, 0.0], 10,
                            rocket_red))
arm.append(cl.hazard_panel("pod_haz", 0.7, 0.42, 0.02, PODC + RP @ V((-0.456, 0.02, 0)),
                           RP @ Matrix.Rotation(math.radians(-90), 3, 'Z'), stripe=0.12, bevel=0))
for lx in (-0.3, 0.3):
    for ly in (-0.18, 0.18):
        arm.append(cl.rivet(PODC + RP @ V((lx, ly, 0.405)), 0.026, RP @ V((0, 0, 1)), "M_Brass"))
arm_r = tl.node("ArmR", arm, S, torso)
tl.empty("MuzzleR", FACE + FN * 0.16, arm_r, 0.2)
for i, p in enumerate(SMOKE):
    tl.empty("Smoke_%d" % i, p, torso, 0.2)

# ======================================================================== Legs
for s in (1, -1):
    sd = SIDE[s]
    H, K, A = HIP[s], KNEE[s], ANK[s]
    # ---- thigh: hip ball, chunky rust-orange armour, knee clevis plates, front piston
    Mth = tl.limb_frame(H, K)
    th = [cl.sphere("hip_ball", H, 0.3, 16, 8, "M_Steel")]
    th.append(tl.loft("thigh", [(-0.08, 0.22, 0.24), (-0.16, 0.31, 0.35), (-0.42, 0.36, 0.4), (-0.64, 0.3, 0.33),
                                (-0.74, 0.25, 0.27), (-0.78, 0.17, 0.19)], n=18, e=0.55, mat=PAINT, M=Mth))
    for sx in (1, -1):
        th.append(cl.rbox("clevis", (0.07, 0.38, 0.46), Mth @ V((sx * 0.285, 0, -0.84)), 0.025, "M_DarkMetal",
                          Mth.to_3x3(), segments=1))
    th.extend(tl.piston("thigh_piston", Mth @ V((0, -0.36, -0.12)), Mth @ V((0, -0.3, -0.78)), 0.055))
    for lz in (-0.3, -0.55):
        th.append(cl.rivet(Mth @ V((0.28 * s, -0.28, lz)), 0.028, Mth.to_3x3() @ V((0.7 * s, -0.7, 0)), "M_Brass"))
    thigh = tl.node("Thigh" + sd, th, H, pelvis)
    # ---- shin: knee ball and cap, dark shin with a hazard plate, calf piston, ankle band
    Msh = tl.limb_frame(K, A)
    sh = [cl.sphere("knee_ball", K, 0.25, 14, 7, "M_Brass")]
    sh.append(tl.loft("shin", [(-0.1, 0.2, 0.22), (-0.2, 0.28, 0.31), (-0.45, 0.31, 0.34), (-0.74, 0.27, 0.29),
                               (-0.86, 0.23, 0.25), (-0.9, 0.17, 0.19)], n=18, e=0.55, mat="M_DarkMetal", M=Msh))
    sh.append(cl.ellipsoid("knee_cap", Msh @ V((0, -0.24, 0.03)), (0.23, 0.1, 0.24), 14, 6, PAINT, Msh.to_3x3()))
    sh.append(cl.rivet(Msh @ V((0, -0.34, 0.03)), 0.032, Msh.to_3x3() @ V((0, -1, 0)), "M_Brass"))
    sh.append(cl.hazard_panel("shin_haz", 0.38, 0.4, 0.03, Msh @ V((0, -0.34, -0.47)), Msh.to_3x3(), stripe=0.11,
                              bevel=0))
    sh.extend(tl.piston("calf_piston", Msh @ V((0, 0.3, -0.18)), Msh @ V((0, 0.25, -0.76)), 0.05))
    sh.append(cl.torus("ankle_band", Msh @ V((0, 0, -0.84)), 0.245, 0.042, Msh.to_3x3(), 16, 3, "M_Brass"))
    shin = tl.node("Shin" + sd, sh, K, thigh)
    # ---- foot: ankle ball, wide flat base, instep, three splayed toes with brass caps, heel spur
    FX = A.x
    ft = [cl.sphere("ankle_ball", A, 0.21, 14, 7, "M_Steel")]
    ft.append(cl.rbox("foot_base", (0.88, 1.16, 0.26), V((FX, -0.12, 0.13)), 0.08, "M_DarkMetal"))
    ft.append(cl.rbox("instep", (0.56, 0.6, 0.26), V((FX, -0.02, 0.36)), 0.09, "M_DarkMetal"))
    for dx in (-0.28, 0.0, 0.28):
        R = Matrix.Rotation(math.radians(-dx * 45), 3, 'Z')
        tc = V((FX + dx * 1.05, -0.78, 0.12))
        ft.append(cl.rbox("toe", (0.25, 0.36, 0.24), tc, 0.07, "M_DarkMetal", R, segments=1))
        tip = tc + R @ V((0, -0.17, 0.0))
        ft.append(cl.sweep("toe_cap", [tip + R @ V((0, 0.06, 0.05)), tip + R @ V((0, -0.05, 0.01)),
                                       tip + R @ V((0, -0.11, -0.1))], [0.105, 0.085, 0.0], 10, "M_Brass",
                           scale=(0.75, 1.0), up=(0, 0, 1)))
    ft.append(cl.rbox("heel", (0.42, 0.3, 0.22), V((FX, 0.52, 0.11)), 0.07, "M_DarkMetal", segments=1))
    ft.append(cl.sweep("spur", [V((FX, 0.6, 0.15)), V((FX, 0.72, 0.08)), V((FX, 0.78, 0.0))], [0.08, 0.06, 0.0], 8,
                       "M_Brass"))
    ft.append(cl.hazard_panel("foot_haz", 0.62, 0.24, 0.02, V((FX, -0.5, 0.262)), (-90, 0, 0), stripe=0.1, bevel=0))
    tl.node("Foot" + sd, ft, A, shin)

rw.finish(ASSET, "enemies", icon=True)
NAMES = ["Pelvis", "Torso", "Head", "ArmL", "MuzzleL", "ArmR", "MuzzleR", "Smoke_0", "Smoke_1",
         "ThighL", "ShinL", "FootL", "ThighR", "ShinR", "FootR"]
tl.summary(NAMES, 16000)
cl.render_extra(ASSET, "enemies", ("front", "side"))
POSE = {"Torso": (0, 0, 35), "ThighL": (-35, 0, 0), "ShinL": (35, 0, 0), "ThighR": (25, 0, 0), "ShinR": (20, 0, 0),
        "ArmL": (25, 0, 0)}
cl.render_pose(ASSET, "enemies", POSE, "pose")
cl.render_pose(ASSET, "enemies", POSE, "pose_side", "side")
