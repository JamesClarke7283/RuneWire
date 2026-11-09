#!/bin/sh
# Full asset import: import new files, fix 3D texture settings, re-import what changed.
cd "$(dirname "$0")/.." || exit 1
env -u LD_LIBRARY_PATH godot --headless --path . --import >/dev/null 2>&1
env -u LD_LIBRARY_PATH python3 tools/fix_imports.py | tail -3
env -u LD_LIBRARY_PATH godot --headless --path . --import 2>&1 | grep -E "ERROR|SCRIPT ERROR" | head -20
echo "import done"
