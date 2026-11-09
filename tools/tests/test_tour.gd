extends Node
## A complete in-game tour of the crafting / progression update, driven through the game itself:
## every named region (the "now entering" banner, charted on the map), ley travel between every
## attuned stone, every crafting station (walk up, E, pick a recipe,
## click Craft), every kind of gathering node (aim + E), every weapon (wield it and fire at a target),
## levels 1 -> 30 (talent points, milestone caches, a talent in each tree) and all five pouch slots.
## Run: godot --headless --path . -- --autostart --no-intro --test=tour   (windowed: also /tmp/rw_tour_*.png)

var main: Node
var p: Player
var ui: GameUI
var fails := 0
var passes := 0


func check(cond: bool, what: String) -> void:
	if cond:
		passes += 1
		printerr("TEST PASS ", what)
	else:
		fails += 1
		printerr("TEST FAIL ", what)


func wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, true).timeout


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func press(action: String) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	Input.parse_input_event(ev)
	await frames(2)
	await get_tree().physics_frame
	var up := InputEventAction.new()
	up.action = action
	up.pressed = false
	Input.parse_input_event(up)
	await frames(2)
	await get_tree().physics_frame


func shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/rw_tour_%s.png" % name)
	printerr("SHOT ", name)


func aim_at(target: Vector3) -> void:
	var d := target - p.camera.global_position
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	p._apply_look()


func find_button(root: Node, text: String) -> Button:
	for c in root.find_children("*", "Button", true, false):
		var b := c as Button
		if b.is_visible_in_tree() and not b.disabled and b.text.contains(text):
			return b
	return null


## Teleport next to something, look at it and press E (the real interaction raycast).
func use(stand: Vector3, look: Vector3) -> String:
	p.teleport(main.world.ground_point(stand.x, stand.z, 0.15), NAN)
	await get_tree().physics_frame
	aim_at(look)
	await get_tree().physics_frame
	await get_tree().physics_frame
	p._update_interaction()
	var prompt := p.interact_text
	await press("interact")
	await frames(3)
	return prompt


func run(m: Node) -> void:
	main = m
	p = m.player
	ui = m.ui
	get_tree().create_timer(900.0, true, false, true).timeout.connect(func():
		printerr("TEST TIMEOUT passes=%d fails=%d" % [passes, fails])
		get_tree().quit(2))
	printerr("TEST start")
	await wait(1.0)
	p.god_mode = true
	Game.add_gold(20000)
	# ---------------------------------------------------------------- 1. every named region
	var hud: Hud = ui.hud
	for id in WorldLayout.AREAS:
		if id == "town":
			continue
		var a: Dictionary = WorldLayout.AREAS[id]
		var c: Vector2 = a["pos"]
		p.teleport(m.world.ground_point(c.x, c.y, 0.3), NAN)
		await frames(3)
		var expected := Hud.area_at(p.global_position)
		check(hud._area_id == expected and hud._area_name.text == str(WorldLayout.AREAS[expected]["name"]) and hud._area_panel.visible,
			"entering %s shows its banner (%s)" % [a["name"], hud._area_name.text])
		await wait(0.6)
		await shot("area_" + id)
	p.teleport(m.world.ground_point(0, 12, 0.3), NAN)
	await frames(3)
	check(hud._area_id == "town" and hud._area_name.text == "Emberwick", "back in Emberwick: %s" % hud._area_name.text)
	check(Game.discovered.size() == WorldLayout.AREAS.size(), "every region charted on the map (%d / %d)" % [Game.discovered.size(), WorldLayout.AREAS.size()])
	# ---------------------------------------------------------------- 1b. ley stones and fast travel
	for id in WorldLayout.LEY_STONES:
		var ls: Vector2 = WorldLayout.WAYPOINTS[id]["pos"]
		p.teleport(m.world.ground_point(ls.x + 2.5, ls.y + 2.0, 0.3), NAN)
		await wait(0.4)
	check(Game.waypoints.size() == WorldLayout.WAYPOINTS.size(), "touched every ley stone: %d waypoints" % Game.waypoints.size())
	for id in ["ley_lake", "ley_north", "ley_east", "town"]:   # (we stand at the eastern stone now)
		check(ui.fast_travel(id), "ley travel to %s" % WorldLayout.WAYPOINTS[id]["name"])
		await wait(0.5)
		var arr: Vector2 = WorldLayout.WAYPOINTS[id]["arrive"]
		check(Vector2(p.global_position.x, p.global_position.z).distance_to(arr) < 2.0 and p.global_position.y > m.world.ground_y(arr.x, arr.y) - 0.3,
			"arrived on dry ground at %s (%s)" % [WorldLayout.WAYPOINTS[id]["name"], str(p.global_position)])
		await shot("travel_" + id)
	# ---------------------------------------------------------------- 1c. the Valley Rally loops the valley
	var race: RaceChallenge = m.world.pois.challenges["race"]
	var placed := race.rings.size() == WorldLayout.RACE_RINGS.size()
	var longest := 0.0
	for i in race.rings.size():
		var rp: Vector3 = (race.rings[i] as Node3D).global_position
		var lift: float = rp.y - m.world.ground_y(rp.x, rp.z)
		placed = placed and lift > 4.0 and lift < 5.2 and Vector2(rp.x, rp.z).length() > 60.0
		longest = maxf(longest, rp.distance_to((race.rings[(i + 1) % race.rings.size()] as Node3D).global_position))
	check(placed and longest < 100.0, "the %d rally rings loop the valley at ground level (longest leg %.0f m)" % [race.rings.size(), longest])
	check(race.start(), "the Valley Rally starts")
	for i in race.rings.size():
		var rp2: Vector3 = (race.rings[i] as Node3D).global_position
		p.teleport(m.world.ground_point(rp2.x, rp2.z, 0.2), NAN)   # through each ring at ground level
		await frames(3)
		await get_tree().physics_frame
	check(not race.running and Challenges.best_medal("race") > 0, "drove the rally through all %d rings for a medal" % race.rings.size())
	await shot("rally_done")
	ui.close_menu()
	await frames(2)
	var foe := Enemy.spawn("crawler", m.world, p.global_position + Vector3(8, 0, 0), false, 1)
	foe.aggro = true
	foe.target = p
	await frames(2)
	check(ui.travel_block("ley_east").contains("Foes"), "no ley travel with a foe on your heels (%s)" % ui.travel_block("ley_east"))
	foe.queue_free()
	await frames(2)
	# ---------------------------------------------------------------- 2. every crafting station
	var station_recipe := {"workbench": ["spark_bomb", {"scrap_gear": 2, "ember_essence": 1}],
		"forge": ["copper_ingot", {"copper_ore": 2}], "alchemy": ["health_tonic_glowcap", {"glowcap": 3}],
		"altar": ["rune_ink", {"rune_shard": 1, "glowcap": 1}], "loom": ["spun_cloth", {"reed_fiber": 3}]}
	for sid in station_recipe:
		var rid: String = station_recipe[sid][0]
		var need: Dictionary = station_recipe[sid][1]
		for id in need:
			Game.add_item(id, int(need[id]))
		var st: CraftingStation = get_tree().get_nodes_in_group("stations").filter(func(s): return s.station == sid)[0]
		var prop: Node3D = st.get_parent()
		var prompt := await use(prop.global_position + prop.global_transform.basis.z * 2.6, prop.global_position + Vector3.UP * 0.9)
		var opened: bool = ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).station == str(sid)
		check(opened and prompt.contains(str(Catalog.STATIONS[sid]["name"])), "E on the %s opens it" % Catalog.STATIONS[sid]["name"])
		if not opened:
			continue
		var cm: CraftingMenu = ui.current_menu
		var out := Catalog.recipe_output(rid)
		var before := Game.item_count(str(out["id"]))
		var row := cm._body.find_child("Recipe_" + rid, true, false) as Button
		if row:
			row.pressed.emit()
			await frames(3)
		var b := find_button(cm._body, "Craft")
		if b and b.text == "Craft":
			b.pressed.emit()
			await frames(3)
		check(Game.item_count(str(out["id"])) == before + int(out["count"]), "crafted %s at the %s" % [Catalog.recipe_name(rid), Catalog.STATIONS[sid]["short"]])
		await shot("station_" + sid)
		ui.close_menu()
		await frames(2)
	# ---------------------------------------------------------------- 3. every kind of gathering node
	for kind in Catalog.HARVEST:
		var best: HarvestNode = null
		for h in get_tree().get_nodes_in_group("harvest_nodes"):
			if h.kind == kind and h.available() and (kind != "crystal" or h.global_position.y < m.world.ground_y(h.global_position.x, h.global_position.z) + 2.0):
				best = h
				break
		if best == null:
			check(false, "a %s node exists" % kind)
			continue
		var item := str(Catalog.HARVEST[kind]["item"])
		var have := Game.item_count(item)
		var np := best.global_position
		var look := np + Vector3.UP * (0.6 if kind != "scrap" else 0.5)
		var stand := np + (Vector3(0, np.y, 0) - np).normalized() * 2.3   # approach from the town side
		if kind == "scrap":
			var pile: Node3D = best.get_parent()
			var away := (pile.global_position - Vector3(150, pile.global_position.y, -175)).normalized()
			stand = pile.global_position - away * 3.0
			look = pile.global_position + Vector3.UP * 0.6
		var prompt := await use(stand, look)
		check(Game.item_count(item) > have and not best.available(), "aim + E gathered from a %s (%s -> +%d %s)" % [
			Catalog.HARVEST[kind]["name"], prompt.split("\n")[0], Game.item_count(item) - have, Catalog.display_name(item)])
		await wait(0.3)
		await shot("node_" + kind)
	# ---------------------------------------------------------------- 4. every weapon
	var spot: Vector3 = m.world.ground_point(-10, 170, 0.1)
	p.teleport(spot, 0.0, 0.0)
	await wait(0.4)
	var fwd := -p.global_transform.basis.z
	var target := Enemy.spawn("golem", m.world, spot + fwd * 7.0, false, 1)
	target.set_physics_process(false)
	target.max_hp = 999999.0
	target.hp = 999999.0
	await wait(0.3)
	for base in Catalog.WEAPONS:
		var d: Dictionary = Catalog.WEAPONS[base]
		for w in Game.weapons.duplicate():
			if Game.equipped_slot(int(w["uid"])) < 0:
				Game.remove_weapon(int(w["uid"]))
		var uid := Game.add_weapon(Catalog.make_weapon(base, 2, []), false)
		Game.equip_weapon(uid, 0)
		p.select_slot(0, true)
		await frames(2)
		var melee: bool = d["kind"] == "melee"
		var dist := 2.2 if melee else (5.0 if str(d.get("fire", "")) == "flame" else 8.0)
		p.teleport(spot, NAN)
		target.global_position = spot + fwd * dist
		await frames(2)
		aim_at(target.aim_point())
		p.mana = Game.max_mana()
		var hp0 := target.hp
		var h: EquipBase = p.current
		var hold := 0.05
		match str(d.get("fire", d.get("cast", ""))):
			"gatling":
				hold = 1.6
			"flame", "beam":
				hold = 0.8
			"charge":
				hold = 1.1
		h.primary(true)
		await wait(hold)
		await shot("weapon_" + base)
		h.primary(false)
		var settle := 0.8
		match str(d.get("fire", d.get("cast", ""))):
			"lob":
				settle = 2.6
			"orb":
				settle = 3.6
			"seeker":
				settle = 1.6
		if melee:
			settle = 1.2
		await wait(settle)
		if base == "mending_ward":
			check(p.ward_timer > 0.0, "%s: the ward glows on you" % Catalog.weapon_name(Game.get_weapon(uid)))
		else:
			check(target.hp < hp0, "%s (%s %s): hit the target for %.0f" % [d["name"], Catalog.SCHOOL_NAMES[Catalog.weapon_school(base)],
				Catalog.KIND_NAMES[d["kind"]], hp0 - target.hp])
	target.queue_free()
	check(Catalog.WEAPONS.size() == 21, "%d weapons in the game" % Catalog.WEAPONS.size())
	# ---------------------------------------------------------------- 5. levels 1 -> 30 and talents
	var counts := {"caches": 0, "ups": 0}   # a dictionary: lambdas capture plain locals by value
	Game.milestone_reached.connect(func(_l, _r): counts["caches"] += 1)
	Game.leveled_up.connect(func(_l): counts["ups"] += 1)
	var start_level := Game.level
	while not Game.is_max_level():
		Game.add_xp(Game.xp_to_next() - Game.xp)
	check(Game.level == Catalog.MAX_LEVEL and int(counts["ups"]) == Catalog.MAX_LEVEL - start_level, "levelled from %d to %d" % [start_level, Game.level])
	check(Game.talent_points_total() == Catalog.MAX_LEVEL - 1, "%d talent points at level 30" % Game.talent_points_total())
	check(int(counts["caches"]) == Catalog.LEVEL_MILESTONES.size() - Catalog.LEVEL_MILESTONES.filter(func(l): return l <= start_level).size(),
		"%d milestone caches on the way" % int(counts["caches"]))
	var learned := []
	for t in ["gunsmith", "spellweaver", "toughness", "deep_pockets", "siphon", "second_wind"]:
		if Game.learn_talent(t):
			learned.append(t)
	check(learned.size() == 6, "spent points across all three trees: %s" % str(learned))
	await press("talents")
	check(ui.current_menu is TalentMenu, "K opens the talents")
	await wait(0.3)
	await shot("talents")
	await press("talents")
	# ---------------------------------------------------------------- 6. all five pouch slots
	var pouch_ids := ["pouch_void", "pouch_ley", "pouch_alchemist", "pouch_prospector", "pouch_scavenger"]
	for i in Game.POUCH_SLOTS:
		if str(Game.pouches[i]) != "":
			Game.unequip_pouch(i)
	for i in pouch_ids.size():
		Game.add_item(pouch_ids[i], 1)
		Game.equip_pouch(pouch_ids[i], i)
	var cap := Game.BASE_PACK + 2 * Game.talent_rank("deep_pockets")
	for pid in pouch_ids:
		cap += int(Catalog.pouch_def(pid)["slots"])
	check(Game.pouch_count() == 5 and Game.pack_capacity() == cap, "five pouches worn: pack %d slots" % Game.pack_capacity())
	check(Game.has_pouch_perk("alchemist") and Game.has_pouch_perk("prospector") and Game.has_pouch_perk("scavenger") and p.magnet_mult() == 2.0,
		"pouch perks active (double potion stacks, extra gathering, loot magnet)")
	await press("inventory")
	await wait(0.4)
	await shot("pouches")
	await press("inventory")
	printerr("TEST SUMMARY passes=%d fails=%d" % [passes, fails])
	get_tree().quit(0 if fails == 0 else 1)
