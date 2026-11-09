extends Node
## Visual showcase: builds a vehicle, stages a fight and opens the menus, saving screenshots to
## /tmp/rw_show_*.png. Run windowed: godot --path . -- --autostart --no-intro --test=showcase

var main: Node


func wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, true, true).timeout


func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "/tmp/rw_show_%s.png" % name
	img.save_png(path)
	printerr("SHOT ", path)


func run(m: Node) -> void:
	main = m
	get_tree().create_timer(240.0, true, false, true).timeout.connect(func(): get_tree().quit(2))
	var p: Player = m.player
	var bm: BuildManager = m.world.build_manager
	var ui: GameUI = m.ui
	await wait(1.5)
	# ---------------------------------------------------------------- vehicle
	for id in ["platform", "seat", "wheel", "thruster", "lamp", "rivet_turret", "hover_stone"]:
		Game.add_parts(id, 6)
		Game.unlock_part(id, false)
	var base: Vector3 = m.world.ground_point(-6, 36, 1.3)
	var deck := bm.spawn_part("platform", Transform3D(Basis(), base))
	var seat := bm.spawn_part("seat", Transform3D(Basis(), base + Vector3(0, 0.75, -0.8)))
	var parts: Array = [seat]
	for off in [Vector3(-2.25, -0.2, 1.4), Vector3(2.25, -0.2, 1.4), Vector3(-2.25, -0.2, -1.4), Vector3(2.25, -0.2, -1.4)]:
		parts.append(bm.spawn_part("wheel", Transform3D(Basis(), base + off)))
	parts.append(bm.spawn_part("rivet_turret", Transform3D(Basis(), base + Vector3(0, 0.6, 1.2))))
	parts.append(bm.spawn_part("lamp", Transform3D(Basis(), base + Vector3(1.6, 0.4, 1.8))))
	parts.append(bm.spawn_part("lamp", Transform3D(Basis(), base + Vector3(-1.6, 0.4, 1.8))))
	parts.append(bm.spawn_part("thruster", Transform3D(Basis(), base + Vector3(0, 0.4, -1.8))))
	for q in parts:
		if q:
			bm.weld(deck, q)
	await wait(1.0)
	p.sit(seat)
	p.chase_yaw = deck.contraption.global_rotation.y + PI + 0.6
	var t := 0.0
	while t < 2.5:
		deck.contraption.pilot_input = {"throttle": 1.0, "steer": 0.3, "lift": 0.0, "boost": false, "fire": false, "aim": Vector3.ZERO}
		p.input_enabled = false
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
	await shot("vehicle")
	p.input_enabled = true
	p.exit_seat()
	# ---------------------------------------------------------------- fight
	p.teleport(m.world.ground_point(40, -10, 0.2), 90.0, -4.0)
	await wait(0.6)
	var kinds := ["wisp", "golem", "drone", "crawler", "cultist"]
	var foes := []
	for i in kinds.size():
		var a := -0.6 + i * 0.3
		var fwd := -p.camera.global_transform.basis.z
		fwd.y = 0
		var pos := p.global_position + fwd.normalized().rotated(Vector3.UP, a) * (10.0 + i * 1.5)
		pos.y = m.world.ground_y(pos.x, pos.z) + (2.5 if kinds[i] in ["wisp", "drone"] else 0.2)
		var e := Enemy.spawn(kinds[i], m.world, pos)
		e.aggro = false
		foes.append(e)
	await wait(0.8)
	p.select_slot(Game.hotbar.find("arcane_bolt"))
	for i in 3:
		p.current.primary(true)
		p.current.primary(false)
		await wait(0.12)
	if foes[0]:
		foes[0].apply_damage(DamageInfo.make(12.0, "kinetic", p, foes[0].aim_point(), Vector3.FORWARD, 0.0, true))
	Combat.explode(p, foes[1].global_position + Vector3(1.5, 0, 0), 3.5, 0.0, "fire", p, true, false)
	await wait(0.15)
	await shot("fight")
	for f in foes:
		if is_instance_valid(f):
			f.queue_free()
	# ---------------------------------------------------------------- menus
	ui.open_catalog()
	await wait(0.5)
	await shot("catalog")
	ui.close_menu()
	var odda: Npc = m.world.pois.npcs["odda"]
	p.teleport(odda.global_position + odda.global_transform.basis.z * 3.0, 0.0)
	await wait(0.3)
	ui.open_dialogue(odda)
	await wait(1.6)
	await shot("dialogue")
	ui.close_menu()
	ui.open_shop("lirael")
	await wait(0.5)
	await shot("shop")
	ui.close_menu()
	Quests.accept("q_arrival")
	Quests.accept("q_wisps")
	ui.open_menu(QuestLogMenu.new())
	await wait(0.5)
	await shot("questlog")
	ui.close_menu()
	ui.open_menu(CharacterMenu.new())
	await wait(0.5)
	await shot("character")
	ui.close_menu()
	printerr("SHOWCASE done")
	get_tree().quit(0)
