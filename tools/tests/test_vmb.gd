extends Node
## Dev helper: prints each weapon viewmodel's on-screen bounds and muzzle position, to keep new or
## rebuilt models framed like the old ones (tune Viewmodel.PLACEMENT).
## Run: godot --headless --path . -- --autostart --no-intro --test=vmb

func measure(p: Player, label: String) -> void:
	var cam := p.camera
	var vm := p.viewmodel.current
	var wr := Rect2()
	var gr := Rect2()
	var wf := true
	var gf := true
	for mi in vm.find_children("*", "MeshInstance3D", true, false):
		if not mi.is_visible_in_tree():
			continue
		var is_glove := String(mi.name).begins_with("Glove")
		var aabb: AABB = mi.get_aabb()
		for i in 8:
			var sp := cam.unproject_position(mi.global_transform * aabb.get_endpoint(i))
			if is_glove:
				gr = Rect2(sp, Vector2.ZERO) if gf else gr.expand(sp)
				gf = false
			else:
				wr = Rect2(sp, Vector2.ZERO) if wf else wr.expand(sp)
				wf = false
	var mz := cam.unproject_position(p.viewmodel.muzzle_position())
	printerr("VMB %-16s weapon x%4d..%4d y%4d..%4d  glove x%4d..%4d y%4d..%4d  muzzle (%d,%d)" % [label,
		int(wr.position.x), int(wr.end.x), int(wr.position.y), int(wr.end.y),
		int(gr.position.x), int(gr.end.x), int(gr.position.y), int(gr.end.y), int(mz.x), int(mz.y)])

func run(m: Node) -> void:
	var p: Player = m.player
	p.teleport(m.world.ground_point(-10, 170, 0.2), 30.0, 0.0)
	await get_tree().create_timer(1.5, true, true, true).timeout
	for base in ["arc_pistol", "rivet_repeater", "boom_mortar", "arcane_bolt", "scattergun", "tesla_lance", "thunder_wrench"]:
		var uid := Game.add_weapon(Catalog.make_weapon(base, 1), false)
		Game.equip_weapon(uid, 0)
		p.select_slot(0, true)
		await get_tree().create_timer(0.6, true, true, true).timeout
		measure(p, base)
	get_tree().quit(0)
