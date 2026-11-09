class_name MapMenu
extends MenuPanel
## The map of Emberwick Vale [M]. The valley is painted from the terrain itself: hills, water, forests,
## roads and buildings. On top are the regions you have discovered (unknown ones stay "???"),
## Emberwick's crafting stations and townsfolk, the challenge terminals, the ley stones, you, and your
## current objective. Attuned ley stones and the plaza are fast-travel points: pick one, then Travel.

const VIEW := 660.0                        # on-screen size of the map square (px)
const LEY := Color("39d5c4")
const OBJ := Color("ffc93c")
const TREE_STAMPS := {                     # model -> [canopy colour, radius in metres]
	"tree_oak": [Color("3f7d36"), 2.8], "tree_oak_small": [Color("4f8f3c"), 2.0], "tree_pine": [Color("2b5f43"), 2.3],
	"tree_crystal": [Color("5fd8cc"), 2.2], "tree_dead": [Color("6b5a4a"), 1.7],
}
const ROOFS := {                           # building -> roof colour on the map
	"bld_house_a": Color("b5523b"), "bld_house_b": Color("9a4a3a"), "bld_workshop": Color("c47a3a"),
	"bld_magic_shop": Color("7a5cc4"), "bld_tinker_shop": Color("d94a3a"), "bld_watchtower": Color("8c877d"),
	"bld_arena_wall": Color("b3ab98"), "bld_arena_gate": Color("c9a24a"), "bld_factory_shed": Color("6d7480"),
}

static var _texture: ImageTexture = null   # painted once per session
static var _image: Image = null
static var _task: int = -1

var ui: GameUI
var _world: World
var _static: Control                       # trees, roads, buildings and region names (drawn once)
var _live: Control                         # markers, you, the objective and the hover card (every frame)
var _markers: Array = []                   # {at: Vector2 map px, name, sub, kind, id, color}
var _hover: Dictionary = {}
var _selected: String = ""
var _wp_buttons: Dictionary = {}
var _travel: Button
var _note: Label
var _objective: Dictionary = {}
var _t: float = 0.0
var _note_t: float = 0.0


func _init() -> void:
	panel_size = Vector2(1210, 830)
	title_text = "Map of Emberwick Vale"


## World (x, z) to a point on the map square. North (-Z) is up.
static func to_map(x: float, z: float) -> Vector2:
	return Vector2((x + WorldLayout.HALF) / WorldLayout.SIZE, (z + WorldLayout.HALF) / WorldLayout.SIZE) * VIEW


func build() -> void:
	_world = get_tree().get_first_node_in_group("world") as World
	_objective = Guide.next_objective(get_tree())
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 18)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(row)
	# ---------------------------------------------------------------- the map square
	var frame := PanelContainer.new()
	var fb := StyleBoxFlat.new()
	fb.bg_color = UIStyle.PARCHMENT_DARK
	fb.border_color = UIStyle.BRASS_DARK
	fb.set_border_width_all(3)
	fb.set_corner_radius_all(6)
	fb.set_content_margin_all(3)
	frame.add_theme_stylebox_override("panel", fb)
	frame.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(frame)
	var view := Control.new()
	view.name = "MapView"
	view.custom_minimum_size = Vector2(VIEW, VIEW)
	view.clip_contents = true
	frame.add_child(view)
	var tr := TextureRect.new()
	tr.texture = map_texture(_world)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	tr.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	view.add_child(tr)
	_static = Control.new()
	_static.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_static.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_static.draw.connect(_draw_static)
	view.add_child(_static)
	_live = Control.new()
	_live.name = "Markers"
	_live.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_live.mouse_filter = Control.MOUSE_FILTER_STOP
	_live.draw.connect(_draw_live)
	_live.gui_input.connect(_on_map_input)
	view.add_child(_live)
	# ---------------------------------------------------------------- the side panel
	var side := VBoxContainer.new()
	side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	side.add_theme_constant_override("separation", 6)
	row.add_child(side)
	side.add_child(UIStyle.label("Where to next", 24, Color("5a3f8a"), "display"))
	var obj_text := "Nothing pressing: explore, gather and craft" if _objective.is_empty() else str(_objective["text"])
	var ot := UIStyle.label(obj_text, 19, UIStyle.INK, "ui")
	ot.name = "Objective"
	ot.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ot.custom_minimum_size.x = 440
	side.add_child(ot)
	var sub := str(_objective.get("sub", ""))
	if _objective.get("target") is Vector3:
		sub = (sub + "  ·  " if sub != "" else "") + "the gold marker on the map"
	if sub != "":
		var sl := UIStyle.label(sub, 16, Color("5a4632"), "body")
		sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		sl.custom_minimum_size.x = 440
		side.add_child(sl)
	side.add_child(_divider())
	var found := 0
	for id in WorldLayout.AREAS:
		if Game.discovered.has(id):
			found += 1
	var rt := UIStyle.label("Exploration  ·  %d / %d regions" % [found, WorldLayout.AREAS.size()], 22, Color("5a3f8a"), "display")
	rt.name = "RegionsTitle"
	side.add_child(rt)
	var et := "Uncharted regions show as ??? on the map. Each one you discover pays XP." if found < WorldLayout.AREAS.size() \
		else "Every region charted. Well travelled!"
	var el := UIStyle.label(et, 16, Color("5a4632"), "body")
	el.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	el.custom_minimum_size.x = 440
	side.add_child(el)
	side.add_child(_divider())
	side.add_child(UIStyle.label("Fast travel", 22, Color("5a3f8a"), "display"))
	var hint := UIStyle.label("Touch a ley stone to attune it, then pick it here or on the map.", 16, Color("5a4632"), "body")
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size.x = 440
	side.add_child(hint)
	var group := ButtonGroup.new()
	for id in WorldLayout.WAYPOINTS:
		var on := Game.waypoints.has(id)
		var b := Button.new()
		b.name = "Waypoint_" + str(id)
		b.toggle_mode = true
		b.button_group = group
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.text = str(WorldLayout.WAYPOINTS[id]["name"]) + ("" if on else "   ·   not attuned yet")
		b.disabled = not on
		b.custom_minimum_size = Vector2(440, 42)
		CraftingMenu.list_row_style(b, UIStyle.INK if on else Color("8a7a62"), LEY if on else Color("b9ab8f"))
		b.add_theme_color_override("font_disabled_color", Color("8a7a62"))
		b.add_theme_font_size_override("font_size", 18)
		var wid := str(id)
		b.pressed.connect(func(): _select(wid))
		side.add_child(b)
		_wp_buttons[wid] = b
	var trow := HBoxContainer.new()
	trow.add_theme_constant_override("separation", 12)
	side.add_child(trow)
	_travel = MenuPanel.button("Travel", func(): _go(), 250)
	_travel.name = "Travel"
	_travel.custom_minimum_size.y = 50
	trow.add_child(_travel)
	_note = UIStyle.label("", 15, Color("8a3a2a"), "body")
	_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trow.add_child(_note)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	side.add_child(spacer)
	var legend := Control.new()
	legend.custom_minimum_size = Vector2(440, 50)
	legend.draw.connect(func(): _draw_legend(legend))
	side.add_child(legend)
	_collect_markers()
	# preselect the nearest attuned waypoint that isn't right here
	var best := ""
	var best_d := INF
	var p: Player = ui.player if ui else null
	for id in Game.waypoints:
		if p == null:
			break
		var d := Vector2(p.global_position.x, p.global_position.z).distance_to(WorldLayout.WAYPOINTS[id]["arrive"])
		if d > 12.0 and d < best_d:
			best_d = d
			best = str(id)
	_select(best if best != "" else "town")


func _divider() -> HSeparator:
	var sep := HSeparator.new()
	var line := StyleBoxLine.new()
	line.color = Color(UIStyle.BRASS_DARK, 0.45)
	line.thickness = 2
	sep.add_theme_stylebox_override("separator", line)
	return sep


static func _danger_color(lo: int) -> Color:
	var d := maxi(lo, Game.level - 2) - Game.level
	return Color("6a6a6a") if d <= -3 else (Color("4f7a3a") if d <= 1 else (Color("c46a1a") if d <= 4 else Color("c0392b")))


# ------------------------------------------------------------------ the painted terrain
## The valley as a picture: one pixel per terrain sample, coloured by the splat map (meadow, forest,
## sand, roads, cobbles), rock on steep slopes, water below the lake line, lit from the north-west and
## faded to parchment beyond the edge of the playable land. Built once and cached.
static func map_texture(world: World) -> ImageTexture:
	if _texture != null:
		return _texture
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1
	if _image == null:
		_image = paint(world)
	_texture = ImageTexture.create_from_image(_image)
	return _texture


## Drop the cached picture (World calls this when it leaves the tree, so nothing leaks at exit).
static func release() -> void:
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1
	_image = null
	_texture = null


## Start painting the map in the background (World calls this once the terrain exists).
static func prepare(world: World) -> void:
	if _texture != null or _image != null or _task >= 0:
		return
	_task = WorkerThreadPool.add_task(func(): _image = paint(world), false, "Paint the map")


static func paint(world: World) -> Image:
	var n := Terrain.RES
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	if world == null or world.terrain == null:
		img.fill(UIStyle.PARCHMENT_DARK)
		return img
	var t := world.terrain
	var light := Vector3(-0.55, 0.7, -0.45).normalized()
	var meadow := Color("9cc96a")
	var forest := Color("5f9147")
	var sand := Color("e6d39a")
	var dirt := Color("c09a66")
	var cobble := Color("cfc6b0")
	var rock := Color("a59c8c")
	var shallow := Color("86cbe0")
	var deep := Color("3d7fae")
	var paper := UIStyle.PARCHMENT_DARK
	var lake: Vector2 = WorldLayout.LAKE["pos"]
	var lake_r: float = float(WorldLayout.LAKE["radius"]) * 1.3   # the lake's water plane (see World.build)
	for zi in n:
		var wz := -WorldLayout.HALF + zi * Terrain.CELL
		for xi in n:
			var wx := -WorldLayout.HALF + xi * Terrain.CELL
			var h: float = t.heights[zi * n + xi]
			var nrm := Vector3(t.sample(xi - 1, zi) - t.sample(xi + 1, zi), 2.0 * Terrain.CELL,
				t.sample(xi, zi - 1) - t.sample(xi, zi + 1)).normalized()
			var col: Color
			if h < WorldLayout.WATER_LEVEL - 0.05 and Vector2(wx, wz).distance_to(lake) < lake_r:
				col = shallow.lerp(deep, clampf(-h / 6.0, 0.0, 1.0))
				var shore := clampf(1.0 + h / 0.8, 0.0, 1.0)
				col = col.lerp(Color("cdeef2"), shore * 0.5)
			elif h < WorldLayout.WATER_LEVEL - 0.05:
				# the dry gorge: dark rock, deeper = darker
				col = Color("8a7a66").lerp(Color("4a3f36"), clampf(-h / 14.0, 0.0, 1.0))
			else:
				var s := t.splat_image.get_pixel(xi, zi)   # r dirt/roads, g sand, b forest, a cobbles
				col = meadow.lerp(forest, s.b * 0.85)
				col = col.lerp(sand, s.g)
				col = col.lerp(dirt, s.r * 0.8)
				col = col.lerp(cobble, s.a * 0.9)
				col = col.lerp(rock, clampf((1.0 - nrm.y - 0.18) * 3.5, 0.0, 0.85))
				col = col.lerp(Color("efe9da"), clampf((h - 26.0) / 22.0, 0.0, 0.55))
				var lit := clampf(nrm.dot(light), 0.0, 1.0)
				col = Color(col.r * (0.7 + 0.45 * lit), col.g * (0.7 + 0.45 * lit), col.b * (0.72 + 0.4 * lit))
			var r := Vector2(wx, wz).length()
			col = col.lerp(paper, smoothstep(WorldLayout.PLAY_RADIUS - 18.0, WorldLayout.PLAY_RADIUS + 26.0, r) * 0.82)
			col = col.lerp(UIStyle.PARCHMENT, 0.1)
			img.set_pixel(xi, zi, col)
	return img


# ------------------------------------------------------------------ static layer
func _draw_static() -> void:
	var c := _static
	var k := VIEW / WorldLayout.SIZE
	# roads
	for r in WorldLayout.ROADS:
		var pts := PackedVector2Array()
		for p in r["pts"]:
			pts.append(to_map((p as Vector2).x, (p as Vector2).y))
		c.draw_polyline(pts, Color(0.42, 0.27, 0.14, 0.45), 2.0, true)
	# forests: a stamp per tree (shadow, then canopy)
	if _world and _world.vegetation:
		for model in TREE_STAMPS:
			var list: Array = _world.vegetation.instances.get(model, [])
			var col: Color = TREE_STAMPS[model][0]
			var rad: float = float(TREE_STAMPS[model][1]) * k
			for xf in list:
				var o: Vector3 = (xf as Transform3D).origin
				var s: float = (xf as Transform3D).basis.get_scale().x
				var m := to_map(o.x, o.z)
				c.draw_circle(m + Vector2(0.7, 0.9), rad * s, Color(0.1, 0.16, 0.1, 0.28))
				c.draw_circle(m, rad * s, col)
	# buildings: footprints in roof colours
	if _world and _world.props_root:
		for node in _world.props_root.get_children():
			var n3 := node as Node3D
			if n3 == null:
				continue
			var b := str(n3.get_meta("model", ""))
			if not ROOFS.has(b):
				continue
			var size: Vector3 = Props.FALLBACK.get(b, Vector3(4, 4, 4))
			var hx := size.x * 0.5 * n3.scale.x
			var hz := size.z * 0.5 * n3.scale.x
			var th := n3.rotation.y
			var pts2 := PackedVector2Array()
			for corner in [Vector2(-hx, -hz), Vector2(hx, -hz), Vector2(hx, hz), Vector2(-hx, hz)]:
				var wx: float = n3.position.x + cos(th) * corner.x + sin(th) * corner.y
				var wz: float = n3.position.z - sin(th) * corner.x + cos(th) * corner.y
				pts2.append(to_map(wx, wz))
			c.draw_colored_polygon(pts2, ROOFS[b])
			pts2.append(pts2[0])
			c.draw_polyline(pts2, Color(0.2, 0.12, 0.08, 0.8), 1.0, true)
	# the plaza fountain
	var f := to_map(0, 0)
	c.draw_circle(f, 3.4, Color("cfc6b0"))
	c.draw_circle(f, 2.2, Color("4fb7d9"))
	# region names (unknown ones stay "???"), under the centre so they clear the markers, with foe levels
	var font := UIStyle.display_font()
	var small := UIStyle.ui_font()
	for id in WorldLayout.AREAS:
		var a: Dictionary = WorldLayout.AREAS[id]
		var known := Game.discovered.has(id)
		var at := to_map((a["pos"] as Vector2).x, (a["pos"] as Vector2).y)
		at.y += 50.0 if id == "town" else 28.0
		var text := str(a["name"]) if known else "???"
		var w := 260.0
		var base := at + Vector2(-w * 0.5, 0.0)
		var fs := 17 if known else 20
		c.draw_string_outline(font, base, text, HORIZONTAL_ALIGNMENT_CENTER, w, fs, 6, Color(0.98, 0.93, 0.8, 0.85))
		c.draw_string(font, base, text, HORIZONTAL_ALIGNMENT_CENTER, w, fs, Color("3a2a1e") if known else Color(0.36, 0.3, 0.22, 0.75))
		var lv: Array = a["levels"]
		if known and int(lv[1]) > 0:
			var lt := "foes Lv %d-%d" % [maxi(int(lv[0]), 1), int(lv[1])]
			c.draw_string_outline(small, base + Vector2(0, 16), lt, HORIZONTAL_ALIGNMENT_CENTER, w, 13, 5, Color(0.98, 0.93, 0.8, 0.85))
			c.draw_string(small, base + Vector2(0, 16), lt, HORIZONTAL_ALIGNMENT_CENTER, w, 13, _danger_color(int(lv[0])))
	# compass rose
	var cr := Vector2(VIEW - 44, 46)
	c.draw_circle(cr, 22.0, Color(0.98, 0.93, 0.8, 0.75))
	c.draw_arc(cr, 22.0, 0, TAU, 32, UIStyle.BRASS_DARK, 2.0, true)
	c.draw_colored_polygon(PackedVector2Array([cr + Vector2(0, -19), cr + Vector2(6, 0), cr + Vector2(-6, 0)]), Color("c0392b"))
	c.draw_colored_polygon(PackedVector2Array([cr + Vector2(0, 19), cr + Vector2(6, 0), cr + Vector2(-6, 0)]), Color("3a2a1e"))
	c.draw_string(UIStyle.ui_font(), cr + Vector2(-30, -26), "N", HORIZONTAL_ALIGNMENT_CENTER, 60, 16, Color("3a2a1e"))


# ------------------------------------------------------------------ markers
func _collect_markers() -> void:
	_markers.clear()
	var tree := get_tree()
	for st in tree.get_nodes_in_group("stations"):
		var cs := st as CraftingStation
		if cs == null:
			continue
		var sd: Dictionary = Catalog.STATIONS.get(cs.station, {})
		var gp := cs.global_position
		_markers.append({"at": to_map(gp.x, gp.z), "name": str(sd.get("name", cs.station)), "sub": "Crafting station  ·  E to use",
			"kind": "station", "id": cs.station, "color": Color("e07b39")})
	if _world and _world.pois:
		for id in _world.pois.npcs:
			var npc := _world.pois.npcs[id] as Node3D
			if npc == null or not is_instance_valid(npc):
				continue
			_markers.append({"at": to_map(npc.global_position.x, npc.global_position.z), "name": str(QuestDB.NPC_NAMES.get(id, id)),
				"sub": "Talk to them  ·  E", "kind": "npc", "id": str(id), "color": Color("f3e3bf")})
		for cid in _world.pois.challenges:
			var runner := _world.pois.challenges[cid] as Node
			var term := runner.get_parent() as Node3D if runner else null
			if term == null:
				continue
			var cd := Challenges.def(str(cid))
			_markers.append({"at": to_map(term.global_position.x, term.global_position.z), "name": str(cd.get("name", cid)),
				"sub": "Challenge terminal  ·  medals and gold", "kind": "challenge", "id": str(cid), "color": Color("ffc93c")})
	for id in WorldLayout.WAYPOINTS:
		var wp: Dictionary = WorldLayout.WAYPOINTS[id]
		var on := Game.waypoints.has(id)
		var sub := "Fast travel: pick it, then Travel" if on else "Touch the stone to attune it for fast travel"
		if id == "town":
			sub = "Fast travel: always open"
		_markers.append({"at": to_map((wp["pos"] as Vector2).x, (wp["pos"] as Vector2).y), "name": str(wp["name"]), "sub": sub,
			"kind": "waypoint", "id": str(id), "color": LEY})
	if _objective.get("target") is Vector3:
		var tp: Vector3 = _objective["target"]
		_markers.append({"at": to_map(tp.x, tp.z), "name": str(_objective["text"]), "sub": "Your objective",
			"kind": "objective", "id": "", "color": OBJ})


func _process(delta: float) -> void:
	_t += delta
	_note_t -= delta
	if _note_t <= 0.0:
		_note_t = 0.4
		_refresh_travel()
	if is_instance_valid(_live):
		_live.queue_redraw()


func _draw_live() -> void:
	var c := _live
	var pulse := 0.5 + 0.5 * sin(_t * 4.0)
	for m in _markers:
		var at: Vector2 = m["at"]
		match str(m["kind"]):
			"station":
				c.draw_rect(Rect2(at - Vector2(3.5, 3.5), Vector2(7, 7)), Color("3a2a1e"))
				c.draw_rect(Rect2(at - Vector2(2.5, 2.5), Vector2(5, 5)), m["color"])
			"npc":
				c.draw_circle(at, 4.2, Color("3a2a1e"))
				c.draw_circle(at, 3.0, m["color"])
			"challenge":
				_star(c, at, 8.0, Color("3a2a1e"))
				_star(c, at, 6.0, m["color"])
			"waypoint":
				var on := Game.waypoints.has(str(m["id"]))
				if on:
					c.draw_circle(at, 9.0 + pulse * 3.0, Color(LEY, 0.22))
				_diamond(c, at, 8.5, Color("1d2333"))
				_diamond(c, at, 6.5, LEY if on else Color("8fa6a3"))
				if str(m["id"]) == _selected:
					c.draw_arc(at, 13.0, 0, TAU, 28, Color("fff3c4"), 2.5, true)
	# the objective: a pulsing gold ring
	for m in _markers:
		if str(m["kind"]) == "objective":
			var at2: Vector2 = m["at"]
			c.draw_arc(at2, 10.0 + pulse * 5.0, 0, TAU, 32, Color(OBJ, 0.9), 3.0, true)
			c.draw_circle(at2, 4.5, OBJ)
			c.draw_arc(at2, 4.5, 0, TAU, 16, Color("3a2a1e"), 1.5, true)
	# you: an arrow pointing the way you face
	var p: Player = ui.player if ui else null
	if p:
		var me := to_map(p.global_position.x, p.global_position.z)
		var yaw := p.chase_yaw if (p.piloting and p.third_person) else p.yaw
		var fwd := Vector2(-sin(yaw), -cos(yaw))
		var side := Vector2(-fwd.y, fwd.x)
		var tip := me + fwd * 11.0
		var pts := PackedVector2Array([tip, me - fwd * 6.0 + side * 7.0, me - fwd * 2.5, me - fwd * 6.0 - side * 7.0])
		var shadow := PackedVector2Array()
		for q in pts:
			shadow.append(q + Vector2(1.2, 1.5))
		c.draw_colored_polygon(shadow, Color(0, 0, 0, 0.35))
		c.draw_colored_polygon(pts, Color("ffd84a"))
		pts.append(pts[0])
		c.draw_polyline(pts, Color("3a2a1e"), 2.0, true)
	# hover card
	if not _hover.is_empty():
		var font := UIStyle.ui_font()
		var title := str(_hover["name"])
		var sub := str(_hover.get("sub", ""))
		var w := maxf(font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x, font.get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x) + 20.0
		var pos: Vector2 = _hover["at"] + Vector2(14, -50)
		pos.x = clampf(pos.x, 4.0, VIEW - w - 4.0)
		pos.y = clampf(pos.y, 4.0, VIEW - 52.0)
		var box := StyleBoxFlat.new()
		box.bg_color = Color(0.11, 0.09, 0.14, 0.92)
		box.border_color = Color(_hover["color"], 0.9)
		box.set_border_width_all(2)
		box.set_corner_radius_all(6)
		c.draw_style_box(box, Rect2(pos, Vector2(w, 46)))
		c.draw_string(font, pos + Vector2(10, 20), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, UIStyle.PARCHMENT)
		c.draw_string(font, pos + Vector2(10, 38), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.85, 0.8, 0.7))


static func _diamond(c: CanvasItem, at: Vector2, r: float, col: Color) -> void:
	c.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -r), at + Vector2(r * 0.75, 0), at + Vector2(0, r), at + Vector2(-r * 0.75, 0)]), col)


static func _star(c: CanvasItem, at: Vector2, r: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 10:
		var a := -PI / 2.0 + i * PI / 5.0
		pts.append(at + Vector2(cos(a), sin(a)) * (r if i % 2 == 0 else r * 0.45))
	c.draw_colored_polygon(pts, col)


func _draw_legend(c: Control) -> void:
	var font := UIStyle.body_font()
	var x := 4.0
	var y := 16.0
	var items := [["you", "you"], ["objective", "objective"], ["ley", "ley stone"], ["challenge", "challenge"],
		["station", "crafting station"], ["npc", "townsfolk"]]
	for i in items.size():
		if i == 3:
			x = 4.0
			y = 40.0
		var at := Vector2(x + 8, y - 5)
		match str(items[i][0]):
			"you":
				c.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -8), at + Vector2(6, 6), at + Vector2(0, 3), at + Vector2(-6, 6)]), Color("ffd84a"))
			"objective":
				c.draw_arc(at, 7.0, 0, TAU, 20, OBJ, 2.5, true)
				c.draw_circle(at, 3.0, OBJ)
			"ley":
				_diamond(c, at, 7.0, LEY)
			"challenge":
				_star(c, at, 7.0, Color("ffc93c"))
			"station":
				c.draw_rect(Rect2(at - Vector2(3.5, 3.5), Vector2(7, 7)), Color("e07b39"))
			"npc":
				c.draw_circle(at, 3.5, Color("3a2a1e"))
		c.draw_string(font, Vector2(x + 22, y), str(items[i][1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color("5a4632"))
		x += 150.0


# ------------------------------------------------------------------ input and travel
func _on_map_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var at: Vector2 = (event as InputEventMouseMotion).position
		var best: Dictionary = {}
		var best_d := 14.0
		for m in _markers:
			var d := at.distance_to(m["at"])
			if d < best_d:
				best_d = d
				best = m
		_hover = best
	elif event is InputEventMouseButton and (event as InputEventMouseButton).pressed \
			and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		if str(_hover.get("kind", "")) == "waypoint":
			var id := str(_hover["id"])
			if Game.waypoints.has(id):
				_select(id)
				AudioManager.play_ui("ui_click")
			else:
				AudioManager.play_ui("ui_error")
				_note.text = "Not attuned yet: touch that ley stone first"
				_note_t = 2.0


func _select(id: String) -> void:
	_selected = id
	var b: Button = _wp_buttons.get(id)
	if b and not b.button_pressed:
		b.set_pressed_no_signal(true)
	_refresh_travel()


func _refresh_travel() -> void:
	if not is_instance_valid(_travel):
		return
	var why := ui.travel_block(_selected) if ui else "No map"
	_travel.disabled = why != ""
	_travel.text = "Travel to %s" % WorldLayout.WAYPOINTS[_selected]["name"] if WorldLayout.WAYPOINTS.has(_selected) else "Travel"
	_note.text = why


func _go() -> void:
	if ui and ui.travel_block(_selected) == "":
		ui.fast_travel(_selected)
