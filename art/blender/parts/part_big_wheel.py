"""part_big_wheel: diameter 1.6 m, width 0.45 m along X.

The part_wheel design, bigger and more rugged: more and deeper chevron lugs, thicker brass spokes on
both faces and a ring of bolts around each rim face. A single mesh object named "Wheel" with its
origin at the wheel centre; spins about X in Godot.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402
import wheel_common  # noqa: E402

rw = pl.rw
rw.reset()
wheel = wheel_common.build_wheel(R=0.8, W=0.45, n_lugs=16, lug_h=0.1, chevron=30.0, rugged=True)
pl.check("part_big_wheel", (0.45, 1.6, 1.6))
rw.finish("part_big_wheel", "parts", icon=True)
