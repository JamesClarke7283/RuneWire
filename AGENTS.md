# AGENTS.md

Guidance for AI agents working on **RuneWire**, a Godot 4.7 RPG where magic meets technology. The art pipeline uses three tools: Blender for 3D models, GIMP for textures and Godot for the game itself. This file explains how to drive each of them on this machine.

## Machine quirks (read first)

The machine runs Guix. Apps live in `/gnu/store` and are launched through wrapper scripts in `~/.guix-profile/bin`.

- **Strip `LD_LIBRARY_PATH` before launching any app from the agent shell.** The agent shell inherits an `LD_LIBRARY_PATH` from the T3 Code desktop environment. It includes libjpeg-turbo 2.1.4, which makes `godot` die with `libturbojpeg.so.0: version 'TURBOJPEG_3' not found`. Use `env -u LD_LIBRARY_PATH godot …`, and do the same for `blender`, `gimp-console-3` and `python3`.
- **`grep` and `find` are broken in the agent shell.** They are Claude Code wrapper functions that fail on Guix with loader errors such as `-G: cannot open shared object file` (exit 127). Use `command grep`, `command find` or awk instead. A loader error from these says nothing about the files being searched.
- **The system `python3` (3.12) has no numpy or Pillow.** Blender's bundled Python 3.13 does have numpy, so run array or image work through `blender --background --python`. ImageMagick, ffmpeg and sox aren't installed.

## MCP servers

All three apps are user-scope MCP servers in `~/.claude.json`, and Godot is also registered in this project's `.mcp.json`. Each MCP server is only a bridge: it dials a plugin that runs inside the app. A refused connection therefore means the in-app plugin isn't running, not that the MCP server is broken.

| App | MCP server command | Plugin inside the app | Listens on |
|---|---|---|---|
| Godot 4.7.2 | `npx -y @npgamedev/godot-mcp-server@latest` | editor plugin `res://addons/godot_mcp_toolkit` (v1.1.2) | 127.0.0.1:6550 (can bind 6550–6560; the MCP dock shows the live port) |
| Blender 5.2.3 LTS | `uv --directory ~/blender_mcp/mcp run blender-mcp` | Blender MCP add-on | 127.0.0.1:9876 |
| GIMP 3.2.8 | `~/.guix-profile/bin/gimp-mcp-server` | `~/.guix-profile/lib/gimp/3.0/plug-ins/gimp-mcp-plugin` | localhost:9877 |

To check which plugins are up, run:

```sh
ss -ltnp | awk '/:65[5-8][0-9]|:9876|:9877/'
```

A server can show as failed (for example `CONNECTION_CLOSED` at session start) even though its port is listening now. In that case, reconnect it with `/mcp` in an interactive session. Until it's back, use the CLI routes described below.

## Godot 4.7.2

The project uses the Forward+ renderer and Jolt Physics for 3D. Keep the addon's `MCPRuntimeServer` autoload in `project.godot`: while the game runs, it listens on 127.0.0.1:6570–6585 so the MCP can inspect the live game.

- **Editor plugin:** `godot_mcp_toolkit` must be enabled under Project Settings → Plugins; it is listed in the `[editor_plugins]` section of `project.godot`. Keep the npm server version matched to the addon version in `addons/godot_mcp_toolkit/plugin.cfg`. If `scene_get_tree` returns `NO_SCENE`, that only means no scene is open in the editor.
- **Working without the MCP:** write `.tscn`, `.tres` and `.gd` files directly. The open editor rescans the filesystem when its window regains focus.
  - Leave `uid=` off hand-written `ext_resource` lines; Godot adds UIDs when it re-saves the file.
  - Never hand-edit anything under `.godot/`.

CLI commands, run from the project root:

```sh
# Parse-check a script: prints SCRIPT ERROR lines and exits 1 on failure
env -u LD_LIBRARY_PATH godot --headless --path . --check-only --script res://scripts/foo.gd

# Run a SceneTree script headless (tests, generators)
env -u LD_LIBRARY_PATH godot --headless --path . --script res://tools/some_tool.gd

# Import new or changed assets, then quit
env -u LD_LIBRARY_PATH godot --headless --path . --import

# Smoke-test a scene for N frames; watch stderr for errors
env -u LD_LIBRARY_PATH godot --headless --path . --quit-after 600 res://scenes/main.tscn

# Render frames to PNGs for a visual check (needs a real GPU driver, so no --headless)
env -u LD_LIBRARY_PATH godot --path . --write-movie /tmp/shot.png --fixed-fps 30 --quit-after 90 res://scenes/main.tscn
```

`--import` starts a second editor instance. If the GUI editor is open on this project, both write to `.godot/`. In that case trigger imports from the open editor (focus its window, or use the MCP) instead.

## Blender 5.2.3 LTS

- **MCP tools:**
  - `execute_blender_code` runs bpy code for modeling.
  - `get_objects_summary` and `get_object_detail_summary` inspect the scene.
  - `render_viewport_to_path` and `get_screenshot_of_window_as_image` show you the result.
  - `search_api_docs` and `search_manual_docs` search the bundled API reference and manual.
- **Working rules from the MCP server:**
  - Inspect the scene before changing it, and keep its naming.
  - Don't destructively modify existing objects without confirmation.
  - Prefer `bpy.ops` for standard actions.
  - Set the active object and the selection explicitly, because operators change both as a side effect.
  - Update the depsgraph before reading computed values.
  - Flush bmesh edits back to the mesh, or they are silently lost.
- **Headless route (no MCP needed; Python 3.13 with numpy):**
  ```sh
  env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/blender/build_x.py -- <args>
  ```
  Keep the generator scripts in the repo so every asset can be rebuilt.
- **Export to Godot as glTF binary**, in metres (1 Blender unit = 1 m):
  ```python
  bpy.ops.export_scene.gltf(filepath="/abs/path/assets/models/name.glb", export_format='GLB',
                            use_selection=True, export_apply=True, export_yup=True, export_tangents=True)
  ```
  Apply scale and rotation before exporting. Model the front of an object facing Blender −Y, which is what the Front view shows. The exporter maps that to +Z in glTF and Godot, which is `Vector3.MODEL_FRONT`, so aim it in Godot with `look_at(target, Vector3.UP, true)`.

## GIMP 3.2.8

- **The MCP plug-in has no autostart.** After every GIMP launch, the user must run Tools → MCP → Start MCP Server; after that, `check_server` reports connected. Agents can't click that menu, so ask the user to do it.
- **MCP tools:** canvas and layer operations, fills and gradients, and filters such as noise, blur, emboss, curves and hue/saturation. `export_image` writes files. For anything without a dedicated tool, `call_api` gives raw PDB/GEGL access.
- **Headless route (no MCP needed):**
  ```sh
  env -u LD_LIBRARY_PATH gimp-console-3 -i --batch-interpreter python-fu-eval \
    -b 'import gi; gi.require_version("Gimp", "3.0"); from gi.repository import Gimp; ...' --quit
  ```
  To run a script file, pass `-b 'exec(open("art/gimp/make_x.py").read())'`.
- **Python API pattern (verified with GIMP 3.2.8):**
  ```python
  gi.require_version("Gimp", "3.0"); gi.require_version("Gegl", "0.4")
  from gi.repository import Gimp, Gegl, Gio
  img = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
  layer = Gimp.Layer.new(img, "base", W, H, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
  img.insert_layer(layer, None, 0)
  f = Gimp.DrawableFilter.new(layer, "gegl:perlin-noise", "")
  f.get_config().set_property("scale", 1.8)
  f.update(); layer.merge_filter(f)
  Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, img, Gio.File.new_for_path(path), None)
  ```
  To list a filter's properties, use `[p.name for p in f.get_config().list_properties()]`. To call `Gegl.list_operations()`, run `Gegl.init(None)` first, or the plug-in crashes.

## Art direction

The style is **cartoon**, not realistic. The user chose it, and it also fits the GPU here, an Intel UHD 620 iGPU.

- **Shapes:** chunky and rounded, with slightly exaggerated proportions, generous bevels and silhouettes that read at a distance.
- **Colour:** saturated.
  - Magic: arcane violet and teal glows, warm gold.
  - Technology: brass, copper, steel and signal orange.
  - Shadows are tinted cool, never pure black.
- **Textures:** a hand-painted look. Use flat base colours, soft large-scale variation, painted edge highlights and very little high-frequency noise.
- **Rendering:** a toon shader (banded light, tinted shadows, rim light), a screen-space outline pass, and glow for emissive runes and tech lights.

## Asset pipeline conventions

`art/ASSET_SPEC.md` is the full asset contract: names, sizes, pivots, node names, texture sets and the audio list. The game code depends on it.

Blender generator scripts use `art/blender/rwlib.py`, and `art/blender/parts/part_crate.py` is the reference example.

```
art/               source art; contains .gdignore so Godot doesn't import it
  blender/         .blend files and bpy generator scripts
  gimp/            .xcf files and GIMP batch scripts
assets/
  models/          .glb files exported from Blender
  textures/<set>/  .png files exported from GIMP
```

- **Texture names:**
  - `<set>_albedo.png` (sRGB).
  - `<set>_normal.png` in the OpenGL (Y+) convention, which Godot expects.
  - `<set>_roughness.png`, `<set>_metallic.png` and `<set>_ao.png`, or a packed `<set>_orm.png` (R = AO, G = roughness, B = metallic) for `ORMMaterial3D`.
- **Texture sizes:** use powers of two (1024 or 2048). Environment textures must tile seamlessly.
- **Units:** 1 Godot unit = 1 Blender unit = 1 m.
