"""part_wheel: diameter 0.9 m, width 0.3 m along X.

Chunky rubber tyre with big chevron treads on a dark steel rim, a brass hub with 5 spokes, lug nuts
and domed axle caps on both faces. A single mesh object named "Wheel" with its origin at the wheel
centre; in Godot it spins about X.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partlib as pl  # noqa: E402
import wheel_common  # noqa: E402

rw = pl.rw
rw.reset()
wheel = wheel_common.build_wheel(R=0.45, W=0.3, n_lugs=14)
pl.check("part_wheel", (0.3, 0.9, 0.9))
rw.finish("part_wheel", "parts", icon=True)
