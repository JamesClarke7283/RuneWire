extends Node
## End-to-end test of the inventory and everything around it: the I key, drag & drop onto the two
## weapon slots and the quick slots, consumables and buffs, weapon instances (rarity / perks / levels),
## the three new weapons, loot pickups, Champions, chests and Ley Vaults, crystal and scrap gathering,
## crafting / upgrading / salvaging, selling and vendor stock, the new quests, and save/load + migration.
## Run: godot --headless --path . -- --autostart --no-intro --test=inventory

var main: Node
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


func press(action: String) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	Input.parse_input_event(ev)
	await get_tree().process_frame
	var up := InputEventAction.new()
	up.action = action
	up.pressed = false
	Input.parse_input_event(up)
	await get_tree().process_frame


## Point the player's camera at a world position.
func aim_at(p: Player, target: Vector3) -> void:
	var d := target - p.camera.global_position
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	p._apply_look()


func spawn_still(kind: String, pos: Vector3, elite: bool = false) -> Enemy:
	var e := Enemy.spawn(kind, main.world, pos, elite)
	e.set_physics_process(false)
	return e


func run(m: Node) -> void:
	main = m
	get_tree().create_timer(240.0, true, false, true).timeout.connect(func():
		printerr("TEST TIMEOUT passes=%d fails=%d" % [passes, fails])
		get_tree().quit(2))
	printerr("TEST start")
	await wait(1.0)
	var p: Player = m.player
	var ui: GameUI = m.ui
	# ---------------------------------------------------------------- starting loadout
	check(Game.weapons.size() == 2, "starts with two weapons (%d)" % Game.weapons.size())
	check(Game.loadout_weapon(0).get("base", "") == "arc_pistol" and Game.loadout_weapon(1).get("base", "") == "arcane_bolt",
		"loadout is Arc Pistol + Arcane Bolt")
	check(p.slot == 0 and p.current_id == "arc_pistol" and p.current is WeaponGun, "player holds the weapon in slot 1")
	check(Game.quick == ["health_tonic", "mana_draught", "spark_bomb", "swift_elixir"], "default quick slots")
	check(ui.hud._slots.size() == 8, "HUD hotbar shows 8 slots (%d)" % ui.hud._slots.size())
	p.select_slot(2)
	check(p.current_id == "gauntlet" and p.current is GauntletTool, "slot 3 is the Grav Gauntlet")
	p.select_slot(3)
	check(p.current_id == "toolkit", "slot 4 is the Rune Toolkit")
	p.quick_swap()
	check(p.slot == 0, "X returns to the last weapon (slot %d)" % p.slot)
	p.quick_swap()
	check(p.slot == 1 and p.current is SpellCaster, "X swaps to the other weapon")
	# ---------------------------------------------------------------- I opens / closes the inventory
	await press("inventory")
	check(ui.current_menu is InventoryMenu and get_tree().paused, "I opens the inventory (and pauses)")
	var inv: InventoryMenu = ui.current_menu
	await wait(0.2)
	check(inv._grid.get_child_count() >= InventoryMenu.COLS * 5, "inventory grid built (%d slots)" % inv._grid.get_child_count())
	var n_locked := inv._grid.get_children().filter(func(c): return c.payload.get("type", "") == "locked").size()
	var n_open := inv._grid.get_children().filter(func(c): return c.payload.get("type", "") != "locked").size()
	check(n_locked >= InventoryMenu.COLS and n_open == Game.pack_capacity(), "pack shows %d open slots and %d locked ones" % [n_open, n_locked])
	check(inv._pouch_row.get_child_count() == Game.POUCH_SLOTS, "five pouch slots")
	check(inv._loadout_row.get_child_count() == 10, "inventory hotbar row: 8 slots + 2 separators")
	# a new Rare weapon with known perks
	var rare := Catalog.make_weapon("rivet_repeater", 2, ["deep", "brutal"])
	var uid := Game.add_weapon(rare, true)
	check(uid > 0 and Game.weapons.size() == 3, "picked up a Rare Rivet Repeater")
	var st := Catalog.weapon_stats(Game.get_weapon(uid))
	check(int(st["mag"]) == 68 and absf(float(st["damage"]) - 8.0 * 1.26 * 1.18) < 0.01, "rarity + perks change stats (mag %d, dmg %.2f)" % [int(st["mag"]), float(st["damage"])])
	check(Catalog.weapon_name(Game.get_weapon(uid)) == "Deep-Drum Rivet Repeater of Ruin", "perk name: %s" % Catalog.weapon_name(Game.get_weapon(uid)))
	await wait(0.1)
	# drag it from the grid onto hotbar slot 2
	var grid_slot: InvSlot = null
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "weapon" and int(s.payload["uid"]) == uid:
			grid_slot = s
	check(grid_slot != null, "new weapon appears in the grid")
	var data: Variant = inv.drag_data_for(grid_slot)
	var lo_slots: Array = inv._loadout_row.get_children().filter(func(c): return c is InvSlot)
	var slot2: InvSlot = lo_slots[1]
	check(inv.can_drop_on(slot2, data), "a weapon can be dropped on weapon slot 2")
	check(not inv.can_drop_on(lo_slots[2], data), "a weapon can't be dropped on a tool slot")
	check(not inv.can_drop_on(lo_slots[4], data), "a weapon can't be dropped on a quick slot")
	inv.drop_on(slot2, data)
	check(int(Game.loadout[1]) == uid, "dropped weapon is now in slot 2")
	await wait(0.1)
	# hover-key: hover the arcane bolt and press 1
	var bolt_uid := -1
	for w in Game.weapons:
		if w["base"] == "arcane_bolt":
			bolt_uid = int(w["uid"])
	inv._hover = {"type": "weapon", "uid": bolt_uid}
	await press("slot_1")
	check(int(Game.loadout[0]) == bolt_uid, "hover + 1 equips into slot 1")
	# equipping a weapon already in the other slot swaps them
	Game.equip_weapon(uid, 0)
	check(int(Game.loadout[0]) == uid and int(Game.loadout[1]) == bolt_uid, "equipping into the other slot swaps")
	# drag from a loadout slot back to the grid unequips
	await wait(0.1)
	lo_slots = inv._loadout_row.get_children().filter(func(c): return c is InvSlot)
	var from_lo: Variant = inv.drag_data_for(lo_slots[1])
	var empty_cell: InvSlot = inv._grid.get_children().filter(func(c): return c.payload.get("type", "") == "empty")[0]
	check(inv.can_drop_on(empty_cell, from_lo), "a loadout weapon can be dragged back to the pack")
	inv.drop_on(empty_cell, from_lo)
	check(int(Game.loadout[1]) == 0, "dragging out of slot 2 unequips it")
	Game.equip_weapon(bolt_uid, 1)
	# quick slot: drop the iron tonic on slot 8
	Game.add_item("iron_tonic", 2)
	await wait(0.1)
	lo_slots = inv._loadout_row.get_children().filter(func(c): return c is InvSlot)
	inv.drop_on(lo_slots[7], {"kind": "item", "id": "iron_tonic"})
	check(Game.quick[3] == "iron_tonic", "iron tonic assigned to quick slot 8")
	inv.drop_on(lo_slots[4], {"kind": "item", "id": "iron_tonic"})
	check(Game.quick[0] == "iron_tonic" and Game.quick[3] == "health_tonic", "moving a quick item swaps the slots")
	Game.set_quick(0, "health_tonic")
	Game.set_quick(3, "iron_tonic")
	await press("inventory")
	check(not ui.is_menu_open() and not get_tree().paused, "I closes the inventory")
	await wait(0.2)
	check(p.slot == 0 and p.current_uid == uid and p.current is WeaponGun, "player now wields the Rare repeater")
	check(int((p.current as WeaponGun).data["mag"]) == 68, "handler uses the instance's stats")
	# ---------------------------------------------------------------- quick slots & consumables
	var iron0 := Game.item_count("iron_tonic")
	p.use_quick(3)
	check(Game.item_count("iron_tonic") == iron0 - 1 and p.has_buff("iron"), "quick slot 8 drinks the Ironhide Tonic")
	var hp0 := p.health
	p.apply_damage(DamageInfo.make(20.0, "kinetic"))
	check(absf((hp0 - p.health) - 13.0) < 0.01, "Ironhide cuts damage by 35%% (took %.1f)" % (hp0 - p.health))
	var swift0 := Game.item_count("swift_elixir")
	p.use_quick(3 - 0)  # still the iron tonic: second one
	Game.add_item("swift_elixir", 1)
	p.use_consumable("swift_elixir")
	check(p.has_buff("swift") and Game.item_count("swift_elixir") == swift0, "Swiftfoot Elixir gives the swift buff")
	var bombs := Game.item_count("spark_bomb")
	var proj0 := get_tree().get_nodes_in_group("vfx_root")[0].get_children().filter(func(c): return c is Projectile).size()
	p.use_quick(2)
	await get_tree().process_frame
	var proj1 := get_tree().get_nodes_in_group("vfx_root")[0].get_children().filter(func(c): return c is Projectile).size()
	check(Game.item_count("spark_bomb") == bombs - 1 and proj1 > proj0, "quick slot 7 throws a Spark Bomb")
	# ---------------------------------------------------------------- weapons: scattergun, tesla lance, wrench
	var arena: Vector3 = m.world.ground_point(-10, 170, 0.1)
	p.teleport(arena, 0.0, 0.0)
	await wait(0.4)
	var fwd := -p.global_transform.basis.z
	var golem := spawn_still("golem", m.world.ground_point(arena.x + fwd.x * 7.0, arena.z + fwd.z * 7.0, 0.1))
	await wait(0.3)
	aim_at(p, golem.aim_point())
	var sg_uid := Game.add_weapon(Catalog.make_weapon("scattergun", 0), false)
	Game.equip_weapon(sg_uid, 0)
	await get_tree().process_frame
	check(p.current_id == "scattergun", "scattergun selected after equipping into the held slot")
	var g_hp := golem.hp
	p.current.primary(true)
	await wait(0.15)
	p.current.primary(false)
	check(golem.hp < g_hp and (p.current as WeaponGun).mag == 5, "scattergun blast hit (%.0f dmg)" % (g_hp - golem.hp))
	var tl_uid := Game.add_weapon(Catalog.make_weapon("tesla_lance", 0), false)
	Game.equip_weapon(tl_uid, 0)
	await get_tree().process_frame
	aim_at(p, golem.aim_point())
	check(p.current is TeslaLance, "Tesla Lance handler")
	g_hp = golem.hp
	p.current.primary(true)
	await wait(1.15)
	check((p.current as TeslaLance).charge >= 0.99, "lance charges to full")
	p.current.primary(false)
	await get_tree().process_frame
	check(golem.hp < g_hp - 40.0 and (p.current as WeaponGun).mag == 4, "full-charge lance bolt hit hard (%.0f dmg)" % (g_hp - golem.hp))
	var wr_uid := Game.add_weapon(Catalog.make_weapon("thunder_wrench", 0), false)
	Game.equip_weapon(wr_uid, 0)
	await get_tree().process_frame
	check(p.current is MeleeWeapon, "Thunder Wrench handler")
	var crawler := spawn_still("crawler", m.world.ground_point(arena.x + fwd.x * 2.0 - fwd.z * 0.3, arena.z + fwd.z * 2.0 + fwd.x * 0.3, 0.1))
	await wait(0.2)
	aim_at(p, crawler.aim_point())
	var c_hp := crawler.hp
	p.current.primary(true)
	p.current.primary(false)
	await wait(0.7)
	check(crawler.dead or crawler.hp < c_hp, "wrench swing hit the crawler")
	if is_instance_valid(golem):
		golem.queue_free()
	if is_instance_valid(crawler) and not crawler.dead:
		crawler.queue_free()
	# ---------------------------------------------------------------- Champions, kill tracking and quests
	Quests.accept("q_loadout")
	check(Game.has_weapon_base("thunder_wrench") and Game.weapon_count("thunder_wrench") >= 2, "q_loadout hands over a Thunder Wrench")
	check(Quests.objective_done("q_loadout", 0), "equip objective done (wrench already equipped)")
	var champ := spawn_still("crawler", m.world.ground_point(arena.x + 6, arena.z + 6, 0.1), true)
	await wait(0.2)
	var champ_hp := 55.0 * (1.0 + Catalog.ENEMY_HP_PER_LEVEL * float(champ.level - 1)) * 2.6
	check(champ.elite and absf(champ.max_hp - champ_hp) < 0.1, "Champion has 2.6x health at its level %d (%.0f)" % [champ.level, champ.max_hp])
	var elites0 := int(Game.stats.get("elites", 0))
	var melee_stats := Catalog.weapon_stats(Game.get_weapon(wr_uid))
	for i in 3:
		var foe: Enemy = champ if i == 0 else spawn_still("wisp", m.world.ground_point(arena.x + 6 + i, arena.z - 6, 2.0))
		await get_tree().process_frame
		foe.apply_damage(DamageInfo.make(9999.0, "kinetic", p, foe.aim_point(), Vector3.FORWARD, 0.0, true).with_weapon(melee_stats))
	check(int(Game.stats.get("elites", 0)) == elites0 + 1, "Champion kill counted")
	check(Quests.status("q_loadout") == "ready", "q_loadout complete after 3 melee kills (%s)" % Quests.status("q_loadout"))
	check(Quests.turn_in("q_loadout"), "q_loadout turned in")
	# ---------------------------------------------------------------- weapon pickups
	var n_w := Game.weapons.size()
	var mortar_drop := Pickup.drop_weapon(p, p.global_position + Vector3(0.5, 1.5, 0.0), Catalog.make_weapon("boom_mortar", 3))
	mortar_drop.velocity = Vector3.ZERO
	await wait(2.5)
	check(Game.weapons.size() == n_w + 1, "walking over a weapon drop picks it up")
	# ---------------------------------------------------------------- workbench: craft, upgrade, salvage
	Quests.accept("q_workbench")
	check(Game.item_count("scrap_gear") >= 5, "q_workbench hands over scrap")
	Game.add_gold(2000)
	# room for the materials below: three Bottomless Pouches
	for i in 3:
		Game.add_item("pouch_void", 1)
		Game.equip_pouch("pouch_void")
	check(Game.pouch_count() == 4 and Game.pack_capacity() >= 16 + 3 + 39, "equipped three Bottomless Pouches (pack %d)" % Game.pack_capacity())
	var sb0 := Game.item_count("spark_bomb")
	var out := Game.craft("spark_bomb")
	check(out.has("items") and Game.item_count("spark_bomb") == sb0 + 2, "crafted 2 Spark Bombs")
	for id in Catalog.MATERIALS:
		Game.add_item(id, 12)
	var n_w2 := Game.weapons.size()
	var made := Game.craft("w_tesla_lance")
	check(made.has("weapon") and Game.weapons.size() == n_w2 + 1 and int(made["weapon"]["rarity"]) >= 1, "crafted a weapon rolls Uncommon+")
	var lvl_w := Game.get_weapon(uid)
	var dmg_before := float(Catalog.weapon_stats(lvl_w)["damage"])
	check(Game.upgrade_weapon(uid) and int(Game.get_weapon(uid)["level"]) == 2, "weapon upgraded to +1")
	check(absf(float(Catalog.weapon_stats(Game.get_weapon(uid))["damage"]) / dmg_before - 1.1) < 0.001, "upgrade adds 10% damage")
	check(Quests.status("q_workbench") == "ready", "q_workbench complete (%s)" % Quests.status("q_workbench"))
	Quests.turn_in("q_workbench")
	check(Game.salvage_weapon(int(Game.loadout[0])).is_empty(), "equipped weapons can't be salvaged")
	var mortar_uid := 0
	for w in Game.weapons:
		if w["base"] == "boom_mortar":
			mortar_uid = int(w["uid"])
	Game.toggle_favorite(mortar_uid)
	check(Game.salvage_weapon(mortar_uid).is_empty() and not Game.sell_weapon(mortar_uid), "favourites are protected")
	Game.toggle_favorite(mortar_uid)
	var cores0 := Game.item_count("clockwork_core")
	var got := Game.salvage_weapon(mortar_uid)
	check(not got.is_empty() and Game.get_weapon(mortar_uid).is_empty() and Game.item_count("clockwork_core") > cores0, "salvaging an Epic gives materials incl. a core")
	# ---------------------------------------------------------------- vendors: sell and featured stock
	var g0 := Game.gold
	var sell_uid := sg_uid if Game.equipped_slot(sg_uid) < 0 else tl_uid
	var val := Catalog.weapon_value(Game.get_weapon(sell_uid))
	check(Game.sell_weapon(sell_uid) and Game.gold == g0 + val, "sold a weapon for %d gold" % val)
	g0 = Game.gold
	check(Game.sell_item("ley_crystal", 3) and Game.gold == g0 + 27, "sold 3 ley crystals")
	var stock := Game.featured_stock("gus", "gun")
	var all_up := stock.size() == 3
	for w in stock:
		all_up = all_up and int(w["rarity"]) >= 1 and Catalog.weapon_base(str(w["base"]))["kind"] != "spell"
	check(all_up, "Gus's featured stock: 3 Uncommon+ guns")
	check(Game.featured_stock("gus", "gun") == stock, "featured stock stays the same within a day")
	check(Game.buy_featured("gus", 0) and Game.featured_stock("gus", "gun").size() == 2, "bought a featured weapon")
	Game.day += 1
	check(Game.featured_stock("gus", "gun").size() == 3, "stock restocks the next day")
	ui.open_shop("gus")
	await wait(0.3)
	var shop: ShopMenu = ui.current_menu
	shop.tab = shop._tabs.find("sell")
	shop._fill()
	await wait(0.2)
	check(shop._grid.get_child_count() > 0, "Gus's Sell tab lists items")
	ui.close_menu()
	ui.open_workbench()
	await wait(0.3)
	check(ui.current_menu is WorkbenchMenu, "workbench menu opens")
	for t in ["upgrade", "salvage", "craft"]:
		(ui.current_menu as WorkbenchMenu)._set_tab(t)
		await wait(0.1)
	ui.close_menu()
	# ---------------------------------------------------------------- treasure chests and Ley Vaults
	var chests := get_tree().get_nodes_in_group("chests")
	check(chests.size() == WorldLayout.CHESTS.size(), "all %d treasure spots placed" % chests.size())
	Quests.accept("q_treasure")
	var plain: Array = chests.filter(func(c): return not c.vault and not c.opened)
	var opened := 0
	var gold_before := Game.gold
	for c in plain.slice(0, 3):
		p.teleport(c.global_position + c.global_transform.basis.z * 1.8 + Vector3.UP * 0.5, NAN)
		await wait(0.2)
		c.interact(p)
		opened += 1 if c.opened else 0
		await wait(1.6)
	check(opened == 3 and Game.is_chest_opened(plain[0].chest_id), "opened 3 chests")
	check(Game.gold > gold_before, "chest gold collected (%d -> %d)" % [gold_before, Game.gold])
	check(Quests.status("q_treasure") == "ready", "q_treasure complete")
	Quests.turn_in("q_treasure")
	var vault: TreasureChest = chests.filter(func(c): return c.vault and not c.opened)[0]
	while Game.item_count("ley_key") > 0:
		Game.remove_item("ley_key", 1)
	vault.interact(p)
	check(not vault.opened, "a Ley Vault stays shut without a key")
	Game.add_item("ley_key", 1)
	Quests.accept("q_vault")
	vault.interact(p)
	check(vault.opened and Game.item_count("ley_key") == 0, "a Ley Key opens the vault (and is used up)")
	check(Quests.status("q_vault") == "ready", "q_vault complete")
	check(chests.filter(func(c): return c.vault and c.global_position.y > 15.0).size() == 2, "two vaults float on sky islands")
	# nothing grows on top of the treasure or the crystals
	var crowded := []
	for n in chests + get_tree().get_nodes_in_group("harvest_nodes"):
		var np: Vector3 = (n as Node3D).global_position
		for model in m.world.vegetation.instances:
			if not (str(model).begins_with("tree_") or str(model).begins_with("rock_")):
				continue
			for xf in m.world.vegetation.instances[model]:
				if Vector2(xf.origin.x - np.x, xf.origin.z - np.z).length() < 3.0 and absf(xf.origin.y - np.y) < 4.0:
					crowded.append("%s near %s" % [model, n.name])
	check(crowded.is_empty(), "no trees or rocks crowd the chests and crystals %s" % str(crowded.slice(0, 3)))
	# ---------------------------------------------------------------- gathering
	var crystal: HarvestNode = null
	var scrap: HarvestNode = null
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		if h.kind == "crystal" and crystal == null:
			crystal = h
		if h.kind == "scrap" and scrap == null:
			scrap = h
	check(crystal != null and scrap != null, "crystal clusters and scrap heaps exist")
	var lc := Game.item_count("ley_crystal")
	crystal.interact(p)
	check(Game.item_count("ley_crystal") >= lc + 2 and not crystal.available(), "harvested ley crystals; the cluster regrows later")
	crystal.interact(p)
	check(Game.item_count("ley_crystal") <= lc + 4, "an empty cluster gives nothing")
	var sgears := Game.item_count("scrap_gear")
	scrap.interact(p)
	check(Game.item_count("scrap_gear") > sgears, "scavenged a scrap heap")
	# ---------------------------------------------------------------- treasure map
	var maps := Game.item_count("treasure_map")
	check(Game.craft("treasure_map").has("items") and Game.item_count("treasure_map") == maps + 1, "crafted a Treasure Map")
	check(p.use_consumable("treasure_map") and p.has_buff("map"), "reading the map starts the Treasure Map buff")
	await wait(0.7)
	check(ui.hud._compass.treasure is Vector3, "the compass marks the nearest treasure")
	# ---------------------------------------------------------------- satchel capacity
	var added := []
	while not Game.inventory_full():
		added.append(Game.add_weapon(Catalog.make_weapon("arc_pistol", 0), false))
	check(Game.add_weapon(Catalog.make_weapon("arc_pistol", 0), false) == 0, "a full pack refuses more weapons (%d/%d)" % [Game.pack_used(), Game.pack_capacity()])
	for a in added:
		Game.remove_weapon(a)
	# ---------------------------------------------------------------- save / load round trip
	Game.toggle_favorite(uid)
	Game.set_quick(1, "repair_kit")
	var snap_w := JSON.stringify(Game.weapons)
	var snap_lo := Game.loadout.duplicate()
	var snap_q := Game.quick.duplicate()
	var snap_chests := Game.opened_chests.size()
	main.save_now()
	Game.weapons = []
	Game.loadout = [0, 0]
	check(SaveSystem.load_game(), "save loaded")
	check(JSON.stringify(Game.weapons) == snap_w, "weapons (rarity, level, perks, favourite) survive a save")
	check(Game.loadout == snap_lo and Game.quick == snap_q, "loadout and quick slots survive a save")
	check(Game.opened_chests.size() == snap_chests, "opened chests survive a save")
	var reopened: TreasureChest = plain[0]
	reopened.opened = false
	m.world.pois.on_game_started()
	check(reopened.opened, "chest nodes re-sync to the save on game start")
	check(typeof(Game.weapons[0]["uid"]) == TYPE_INT and typeof(Game.weapons[0]["level"]) == TYPE_INT, "weapon numbers come back as ints")
	# old (pre-inventory) save format
	Game.from_dict({"gold": 500, "equipment": ["gauntlet", "toolkit", "arcane_bolt", "arc_pistol", "fireball"],
		"hotbar": ["gauntlet", "toolkit", "arcane_bolt", "arc_pistol", "fireball"], "items": {"health_tonic": 1}})
	var bases := Game.weapons.map(func(w): return w["base"])
	check(bases.size() == 3 and "fireball" in bases and Game.loadout_weapon(0).get("base", "") == "arcane_bolt", "old saves migrate to weapon instances (%s)" % str(bases))
	SaveSystem.load_game()
	await wait(0.3)
	check(p.current != null and p.slot_entry(p.slot).get("key", "") == p._current_key(), "player hand matches the loadout after loading")
	printerr("TEST SUMMARY passes=%d fails=%d" % [passes, fails])
	get_tree().quit(0 if fails == 0 else 1)
