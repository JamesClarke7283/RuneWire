extends Node
## Developer automation driven by command-line user args (after `--`):
##   --autostart            skip the title menu and start a new game
##   --continue             load the save and start
##   --shots=a.png@120,b.png@300   save screenshots at those frames
##   --quit-frame=N         quit after N frames
##   --pos=x,y,z --yaw=deg --pitch=deg   place the player
##   --time=0.5             time of day (0..1)
##   --god --gold=N --unlock-all (all parts, one of every weapon, materials, consumables, schematics,
##                          big pouches and the top Artisan rank)
##   --loot=N               scatter N rolled weapons around the player (loot testing)
##   --test=name            run res://tools/tests/test_<name>.gd (a Node with `func run(main)`)
##   --no-intro             skip the welcome popup

var args: Dictionary = {}
var main: Node = null
var frame: int = 0
var shots: Array = []
var quit_frame: int = -1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "true"
	if args.has("shots"):
		for s in str(args["shots"]).split(","):
			var pf := s.split("@")
			if pf.size() == 2:
				shots.append({"path": pf[0], "frame": int(pf[1])})
	if args.has("quit-frame"):
		quit_frame = int(args["quit-frame"])


func has(flag: String) -> bool:
	return args.has(flag)


func arg(flag: String, default: Variant = "") -> Variant:
	return args.get(flag, default)


func vec3_arg(flag: String) -> Variant:
	if not args.has(flag):
		return null
	var p := str(args[flag]).split(",")
	if p.size() < 3:
		return null
	return Vector3(float(p[0]), float(p[1]), float(p[2]))


var _bench_frames: int = 0
var _bench_time: float = 0.0


func _process(delta: float) -> void:
	frame += 1
	var b0 := int(arg("bench-start", 150))
	var b1 := b0 + 300
	if has("bench") and frame > b0 and frame <= b1:
		_bench_frames += 1
		_bench_time += delta
		if frame == b1:
			print("DEV bench avg fps %.1f (%.2f ms)" % [_bench_frames / _bench_time, _bench_time / _bench_frames * 1000.0])
			print("DEV perf draws=%d prims=%d objects=%d process=%.2fms physics=%.2fms nodes=%d" % [
				Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
				Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
				Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
				Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
				Performance.get_monitor(Performance.OBJECT_NODE_COUNT)])
	for s in shots:
		if frame == int(s["frame"]):
			var img := get_viewport().get_texture().get_image()
			img.save_png(s["path"])
			print("DEV screenshot ", s["path"], " frame ", frame, " fps ", Engine.get_frames_per_second())
	if quit_frame > 0 and frame >= quit_frame:
		print("DEV quit at frame ", frame, " fps ", Engine.get_frames_per_second())
		get_tree().quit()


## Called by main.gd once the player exists.
func on_game_started(m: Node) -> void:
	main = m
	if has("god"):
		Game.add_gold(5000)
		m.player.god_mode = true
	if has("gold"):
		Game.add_gold(int(arg("gold")))
	if has("unlock-all"):
		# five big pouches first so everything fits
		Game.pouches = ["pouch_void", "pouch_void", "pouch_void", "pouch_ley", "pouch_alchemist"]
		Game.pouches_changed.emit()
		for pid in Catalog.PARTS:
			Game.unlock_part(pid, false)
			Game.add_parts(pid, 10)
		for eid in Catalog.WEAPONS:
			Game.unlock_equipment(eid)
		for mid in Catalog.MATERIALS + ["ley_key"]:
			Game.add_item(mid, 10)
		for cid in Catalog.CONSUMABLES:
			Game.add_item(cid, 5)
		for rid in Catalog.schematic_recipes():
			Game.learn_schematic(rid, false)
		Game.add_artisan_xp(int(Catalog.ARTISAN_XP[Catalog.ARTISAN_XP.size() - 1]))
	if has("time"):
		Game.time_of_day = float(arg("time"))
	if has("q"):
		Settings.quality = int(arg("q"))
	if has("scale"):
		Settings.render_scale = float(arg("scale"))
	if has("no-grass"):
		Settings.grass_density = 0.0
	if has("no-outline"):
		Settings.outlines = false
	if has("no-vsync"):
		Settings.vsync = false
	Settings.apply()
	var w: Node = m.world
	if has("no-veg"):
		w.vegetation.visible = false
	if has("no-shadows"):
		w.env_rig.sun.shadow_enabled = false
	if has("no-ssao"):
		w.env_rig.env.ssao_enabled = false
	if has("no-glow"):
		w.env_rig.env.glow_enabled = false
	if has("no-fog"):
		w.env_rig.env.fog_enabled = false
	if has("no-adjust"):
		w.env_rig.env.adjustment_enabled = false
	if has("no-aa"):
		get_viewport().screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	if has("no-terrain"):
		for c in w.terrain.get_children():
			if c is MeshInstance3D:
				c.visible = false
	if has("no-props"):
		w.props_root.visible = false
	if has("no-npcs"):
		w.npcs_root.visible = false
	if has("no-water"):
		w.get_node("Lake").visible = false
	if has("no-vm"):
		m.player.viewmodel.visible = false
	if has("no-lights"):
		for l in get_tree().get_nodes_in_group("night_lights"):
			l.visible = false
		for l in m.find_children("*", "OmniLight3D", true, false):
			l.visible = false
	if has("outline-debug"):
		for ol in m.player.camera.get_children():
			if ol is OutlineOverlay:
				ol.material.set_shader_parameter("debug_mode", 1)
	if has("loot"):
		for i in int(arg("loot", 6)):
			var a := TAU * i / maxf(float(arg("loot", 6)), 1.0)
			Pickup.drop_weapon(m.player, m.player.global_position + Vector3(cos(a) * 3.0, 1.5, sin(a) * 3.0), Catalog.roll_weapon(1.5))
	var pos: Variant = vec3_arg("pos")
	if pos != null:
		m.player.teleport(pos, float(arg("yaw", 0.0)), float(arg("pitch", 0.0)))
	elif has("yaw"):
		m.player.teleport(m.player.global_position, float(arg("yaw", 0.0)), float(arg("pitch", 0.0)))
	if has("test"):
		var path := "res://tools/tests/test_%s.gd" % arg("test")
		var script: Script = load(path) if ResourceLoader.exists(path) else null
		if script == null or not script.can_instantiate():
			printerr("TEST FAIL could not load ", path)
			get_tree().quit(3)
			return
		var t: Node = script.new()
		add_child(t)
		t.call_deferred("run", m)
