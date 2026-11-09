extends Node
## Visual check of the inventory-era UI and world content. Saves /tmp/rw_inv_*.png.
## Run windowed: godot --path . -- --autostart --no-intro --test=shots [-- --vm-only]

var main: Node


func wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, true, true).timeout


func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "/tmp/rw_inv_%s.png" % name
	img.save_png(path)
	printerr("SHOT ", path)


func run(m: Node) -> void:
	main = m
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func(): get_tree().quit(2))
	var p: Player = m.player
	var ui: GameUI = m.ui
	Game.time_of_day = 0.4
	await wait(1.5)
	# let the loading screen finish fading before the first shot
	for i in 40:
		if ui.loading == null or not is_instance_valid(ui.loading) or not ui.loading.visible:
			break
		await wait(0.1)
	# a pack full of loot (worn pouches make room for it all)
	Game.pouches = ["pouch_void", "pouch_ley", "pouch_rune", "pouch_brass", "pouch_alchemist"]
	Game.pouches_changed.emit()
	var picks := [["rivet_repeater", 2, ["deep", "brutal"]], ["tesla_lance", 4, []], ["scattergun", 1, []],
		["thunder_wrench", 3, []], ["fireball", 2, []], ["chain_lightning", 1, []], ["boom_mortar", 0, []], ["mending_ward", 0, []]]
	var first := 0
	for pk in picks:
		var uid := Game.add_weapon(Catalog.make_weapon(pk[0], pk[1], pk[2]), false)
		if first == 0:
			first = uid
	for id in Catalog.MATERIALS + ["ley_key"]:
		Game.add_item(id, randi_range(2, 9))
	for id in Catalog.CONSUMABLES:
		Game.add_item(id, 3)
	Game.equip_weapon(first, 0)
	Game.add_gold(1500)
	await wait(0.5)
	if Dev.has("vm-only"):
		await _viewmodels(p)
		get_tree().quit(0)
		return
	# ---------------------------------------------------------------- HUD
	p.teleport(m.world.ground_point(6, 26, 0.2), 200.0, -4.0)
	p.add_buff("swift", 30.0)
	await wait(1.0)
	await shot("hud")
	# ---------------------------------------------------------------- inventory
	ui.open_inventory()
	await wait(0.6)
	await shot("inventory")
	var inv: InventoryMenu = ui.current_menu
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "weapon" and Game.get_weapon(int(s.payload["uid"]))["base"] == "tesla_lance":
			inv._on_slot_clicked(s, MOUSE_BUTTON_LEFT, false)
	await wait(0.4)
	await shot("inventory_legendary")
	inv._set_tab("materials")
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "item":
			inv._on_slot_clicked(s, MOUSE_BUTTON_LEFT, false)
			break
	await wait(0.4)
	await shot("inventory_materials")
	ui.close_menu()
	# ---------------------------------------------------------------- workbench & shop
	ui.open_workbench()
	await wait(0.5)
	await shot("workbench_craft")
	(ui.current_menu as WorkbenchMenu)._set_tab("upgrade")
	await wait(0.3)
	await shot("workbench_upgrade")
	ui.close_menu()
	ui.open_shop("gus")
	await wait(0.3)
	var shop: ShopMenu = ui.current_menu
	shop.tab = 1
	shop._fill()
	await wait(0.4)
	await shot("shop_featured")
	shop.tab = shop._tabs.find("sell")
	shop._fill()
	await wait(0.4)
	await shot("shop_sell")
	ui.close_menu()
	# ---------------------------------------------------------------- the workbench in town
	var wb: Node3D = get_tree().get_first_node_in_group("workbench")
	var wbp := wb.global_position + wb.global_transform.basis.z * 3.6 + Vector3.UP * 0.3
	p.teleport(wbp, 0.0)
	await wait(0.2)
	_look_at(p, wb.global_position + Vector3.UP * 0.9)
	await wait(0.6)
	await shot("workbench_world")
	# ---------------------------------------------------------------- a chest, then its loot
	var chest: TreasureChest = null
	for c in get_tree().get_nodes_in_group("chests"):
		if c.chest_id == "woods_hollow":
			chest = c
	var cp := chest.global_position + chest.global_transform.basis.z * 3.2 + Vector3.UP * 0.3
	p.teleport(cp, 0.0)
	await wait(0.3)
	_look_at(p, chest.global_position + Vector3.UP * 0.5)
	await wait(0.8)
	await shot("chest_closed")
	chest.interact(p)
	await wait(0.9)
	await shot("chest_open")
	# weapon drops in their beams
	for i in 4:
		var a := i * 1.4 - 2.0
		Pickup.drop_weapon(p, chest.global_position + Vector3(cos(a) * 4.0, 1.5, sin(a) * 4.0), Catalog.roll_weapon(0.0, i + 1))
	await wait(1.6)
	_look_at(p, chest.global_position + Vector3.UP * 0.6)
	await shot("loot_beams")
	# ---------------------------------------------------------------- a Champion
	var e := Enemy.spawn("golem", m.world, chest.global_position + chest.global_transform.basis.x * 6.0 + Vector3.UP * 0.3, true)
	e.set_physics_process(false)
	await wait(0.5)
	_look_at(p, e.aim_point())
	await wait(0.4)
	await shot("champion")
	# ---------------------------------------------------------------- a crystal cluster
	var node: HarvestNode = null
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		if h.kind == "crystal" and h.global_position.y < 15.0 and (node == null or h.global_position.distance_to(p.global_position) < node.global_position.distance_to(p.global_position)):
			node = h
	var np := node.global_position + Vector3(2.6, 1.0, 2.6)
	p.teleport(np, 0.0)
	await wait(0.3)
	_look_at(p, node.global_position + Vector3.UP * 0.6)
	await wait(0.8)
	await shot("crystal_node")
	# ---------------------------------------------------------------- sky island
	var top: Vector3 = m.world.pois.sky_tops["flats"]
	p.teleport(top + Vector3(9, 4, 9), 45.0, -15.0)
	await wait(0.3)
	_look_at(p, top + Vector3.UP * 0.5)
	await wait(1.0)
	await shot("sky_island")
	# ---------------------------------------------------------------- crafting update: stations, nodes, menus
	await _crafting_shots(p, ui)
	printerr("SHOTS done")
	get_tree().quit(0)


func _look_at(p: Player, target: Vector3) -> void:
	var d := target - p.camera.global_position
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	p._apply_look()


## First-person look at every weapon model (for tuning viewmodel placement).
func _viewmodels(p: Player) -> void:
	p.teleport(main.world.ground_point(-10, 170, 0.2), 30.0, 0.0)
	await wait(1.0)
	for base in Catalog.WEAPONS:
		var uid := 0
		for w in Game.weapons:
			if w["base"] == base:
				uid = int(w["uid"])
		if uid == 0:
			uid = Game.add_weapon(Catalog.make_weapon(base, 2), false)
		Game.equip_weapon(uid, 0)
		p.select_slot(0, true)
		await wait(0.7)
		await shot("vm_" + base)



## The crafting update: each station in town and its screen, the gathering nodes, the talents, a
## burning and a chilled foe with level tags, and the objective tracker.
func _crafting_shots(p: Player, ui: GameUI) -> void:
	for st in get_tree().get_nodes_in_group("stations"):
		var prop: Node3D = st.get_parent()
		p.teleport(prop.global_position + prop.global_transform.basis.z * 4.2 + Vector3.UP * 0.3, 0.0)
		await wait(0.3)
		_look_at(p, prop.global_position + Vector3.UP * 1.1)
		await wait(0.6)
		await shot("station_" + st.station)
		ui.open_station(st.station)
		await wait(0.5)
		await shot("menu_" + st.station)
		if st.station == "altar":
			(ui.current_menu as CraftingMenu)._set_tab("enchant")
			await wait(0.3)
			await shot("menu_altar_enchant")
		ui.close_menu()
	ui.open_crafting_book()
	await wait(0.5)
	await shot("menu_book")
	ui.close_menu()
	Game.level = 9
	ui.open_talents()
	await wait(0.4)
	await shot("menu_talents")
	ui.close_menu()
	for kind in ["ore_copper", "ore_iron", "glowcap", "sunpetal", "reeds"]:
		var node: HarvestNode = get_tree().get_nodes_in_group("harvest_nodes").filter(func(h): return h.kind == kind)[0]
		var off := Vector3(2.4, 0.0, 2.4)
		p.teleport(node.global_position + off + Vector3.UP * 0.6, 0.0)
		await wait(0.3)
		_look_at(p, node.global_position + Vector3.UP * 0.5)
		await wait(0.7)
		await shot("node_" + kind)
		# what the screenshot just showed: the banner must name the region the node is in
		var want := Hud.area_at(p.global_position)
		var got: String = ui.hud._area_id
		printerr("AREA %s at %s: banner=%s (%s) expected=%s %s" % [kind, str(p.global_position), got, ui.hud._area_name.text, want,
			"OK" if got == want else "MISMATCH"])
	# statuses and level tags
	var spot: Vector3 = main.world.ground_point(-10, 170, 0.2)
	p.teleport(spot, 0.0, 0.0)
	await wait(0.4)
	var fwd := -p.global_transform.basis.z
	var side := Vector3(-fwd.z, 0, fwd.x)
	var a := Enemy.spawn("crawler", main.world, spot + fwd * 7.0 - side * 2.0, false, 9)
	var b := Enemy.spawn("crawler", main.world, spot + fwd * 7.0 + side * 2.0, false, 2)
	for e in [a, b]:
		e.set_physics_process(false)
		e.max_hp = 9999.0
		e.hp = 9999.0
	await wait(0.3)
	a.apply_burn(10.0, 30.0, {})
	b.apply_chill(0.5, 30.0)
	for e in [a, b]:
		e._hb_timer = 30.0
		e._hb.set_instance_shader_parameter("show", 1.0)
		e._lvl_label.visible = true
	a.set_physics_process(true)
	b.set_physics_process(true)
	_look_at(p, (a.aim_point() + b.aim_point()) * 0.5)
	await wait(1.2)
	await shot("statuses")
	a.queue_free()
	b.queue_free()
	# Odda's new shop tabs and the wield-it prompt on a dropped weapon
	ui.open_shop("odda")
	await wait(0.3)
	var odda: ShopMenu = ui.current_menu
	for tname in ["pouches", "materials", "schematics"]:
		for i in odda._tabs.size():
			if str(odda._tabs[i]).begins_with(tname):
				odda.tab = i
		odda._fill()
		await wait(0.4)
		await shot("shop_" + tname)
	ui.close_menu()
	var wpos: Vector3 = main.world.ground_point(-10, 170, 0.2)
	p.teleport(wpos, 0.0, 0.0)
	await wait(0.3)
	var f2 := -p.global_transform.basis.z
	var dropped := Pickup.drop_weapon(p, wpos + f2 * 3.0 + Vector3.UP * 0.9, Catalog.make_weapon("sun_scepter", 3))
	dropped.velocity = Vector3.ZERO
	await wait(1.5)
	_look_at(p, dropped.global_position)
	await wait(0.4)
	await shot("pickup_prompt")
	# the level-up banner
	Game.add_xp(Game.xp_to_next() - Game.xp)
	await wait(0.7)
	await shot("level_up")
	# the map, with a few regions charted and a ley stone attuned
	for aid in ["woods", "lake", "flats"]:
		Game.discover_area(aid, true)
	Game.attune_waypoint("ley_lake")
	ui.open_map()
	await wait(0.6)
	await shot("map")
	ui.close_menu()
