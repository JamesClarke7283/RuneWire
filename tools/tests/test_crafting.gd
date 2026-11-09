extends Node
## End-to-end test of the crafting / progression update: the pack and its five pouch slots, stacks and
## overflow, the five crafting stations and the Crafting Book, Artisan ranks, schematics, enchanting,
## weapon levels to +9, gathering (ore, herbs, reeds), talents, levels and milestone caches, enemy
## levels and burn / chill, every new weapon (tech and magic), swapping a weapon off the ground with E,
## the objective tracker, the new quests, and save/load (+ migrating the old satchel upgrade).
## Run: godot --headless --path . -- --autostart --no-intro --test=crafting

var main: Node
var fails := 0
var passes := 0
var arena: Vector3
var fwd: Vector3


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


func aim_at(p: Player, target: Vector3) -> void:
	var d := target - p.camera.global_position
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	p._apply_look()


func spawn_still(kind: String, pos: Vector3, lvl: int = 1, elite: bool = false) -> Enemy:
	var e := Enemy.spawn(kind, main.world, pos, elite, lvl)
	e.set_physics_process(false)
	return e


## A ground point `d` metres in front of the arena spot (and `side` metres to the right).
func ahead(d: float, side: float = 0.0) -> Vector3:
	return main.world.ground_point(arena.x + fwd.x * d - fwd.z * side, arena.z + fwd.z * d + fwd.x * side, 0.1)


## Equip a fresh weapon in slot 1 and make sure the player holds it.
func wield(p: Player, base: String, rarity: int = 0) -> int:
	# keep the pack roomy: drop spare weapons from earlier steps
	for w in Game.weapons.duplicate():
		if Game.equipped_slot(int(w["uid"])) < 0 and not bool(w.get("fav", false)):
			Game.remove_weapon(int(w["uid"]))
	var uid := Game.add_weapon(Catalog.make_weapon(base, rarity, []), false)
	Game.equip_weapon(uid, 0)
	p.select_slot(0, true)
	await get_tree().process_frame
	return uid


func run(m: Node) -> void:
	main = m
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func():
		printerr("TEST TIMEOUT passes=%d fails=%d" % [passes, fails])
		get_tree().quit(2))
	printerr("TEST start")
	await wait(1.0)
	var p: Player = m.player
	var ui: GameUI = m.ui
	p.god_mode = true
	# ---------------------------------------------------------------- objective tracker (fresh game)
	await wait(0.8)
	var obj := Guide.next_objective(get_tree())
	check(str(obj.get("text", "")).contains("Odda") and obj.get("target") is Vector3, "first objective: talk to Odda (%s)" % obj.get("text", ""))
	check(ui.hud._obj_panel.visible and ui.hud._obj_text.text == str(obj["text"]), "HUD shows the objective under the compass")
	check(ui.hud._compass.target is Vector3, "the compass points at the objective")
	check(ui.hud._obj_dist.text.ends_with(" m"), "objective shows distance and direction (%s)" % ui.hud._obj_dist.text)
	Quests.accept("q_arrival")
	await wait(0.7)
	check(ui.hud._obj_text.text.begins_with("Buy a part"), "tracked quest step becomes the objective (%s)" % ui.hud._obj_text.text)
	Quests.abandon("q_arrival")
	Game.set_tracked_recipe("copper_ingot")
	obj = Guide.next_objective(get_tree())
	check(str(obj.get("text", "")).contains("Copper Ore") and obj.get("target") is Vector3, "tracked recipe guides to copper ore (%s)" % obj.get("text", ""))
	var vein_d := INF
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		if h.kind == "ore_copper":
			vein_d = minf(vein_d, (h as Node3D).global_position.distance_to(obj["target"]))
	check(vein_d < 0.5, "...and the target is a copper vein")
	# ---------------------------------------------------------------- the pack and pouches
	var base_cap := Game.BASE_PACK + 3
	check(Game.pouches[0] == "pouch_cloth" and Game.pack_capacity() == base_cap, "start: a cloth pouch, %d pack slots" % Game.pack_capacity())
	check(Game.pack_used() == 3, "starting items fill 3 slots (%d)" % Game.pack_used())
	Game.add_item("scrap_gear", 45)
	check(Game.slots_for("scrap_gear", 45) == 2 and Game.pack_used() == 5, "45 gears = 2 stacks of 40")
	Game.add_item("pouch_alchemist", 1)
	var cons_stack := Game.item_stack_size("health_tonic")
	check(Game.equip_pouch("pouch_alchemist") and Game.item_stack_size("health_tonic") == cons_stack * 2, "Alchemist's Bandolier doubles potion stacks")
	check(Game.pack_capacity() == base_cap + 4, "a second pouch grows the pack to %d" % Game.pack_capacity())
	# fill the pack and overflow
	var fillers := []
	for id in Catalog.MATERIALS + Catalog.CONSUMABLES.keys():
		if Game.pack_free() <= 0:
			break
		if Game.item_count(id) == 0 and id != "ley_crystal" and id != "ember_essence":
			Game.add_item(id, 1)
			fillers.append(id)
	check(Game.pack_free() <= 0, "the pack fills up (%d/%d)" % [Game.pack_used(), Game.pack_capacity()])
	check(Game.add_item("ley_crystal", 3) == 0 and Game.room_for("ley_crystal", 3) == 0, "a full pack takes no new stack")
	check(Game.add_item("scrap_gear", 30) == 30 and Game.item_count("scrap_gear") == 75, "...but tops up stacks that have room")
	var pickups0 := get_tree().get_nodes_in_group("pickups").size()
	check(Game.give_item("ember_essence", 2) == 0, "give_item into a full pack adds nothing")
	await get_tree().process_frame
	check(get_tree().get_nodes_in_group("pickups").size() >= pickups0 + 2, "...and drops the overflow at the player's feet")
	check(Game.add_item("ley_key", 1) == 1, "keys ride on the key ring (no pack space)")
	check(not Game.unequip_pouch(1), "can't take off a pouch the pack still needs")
	check(Game.add_weapon(Catalog.make_weapon("crossbow", 0), false) == 0, "a full pack refuses a weapon")
	Game.remove_item(fillers[fillers.size() - 1], 1)
	Game.add_item("pouch_void", 1)
	check(Game.equip_pouch("pouch_void", 2) and Game.pack_capacity() == base_cap + 4 + 13, "a Bottomless Pouch adds 13 slots (%d)" % Game.pack_capacity())
	# swap pouch slots and drag a pouch in the inventory
	Game.swap_pouch_slots(1, 2)
	check(Game.pouches[1] == "pouch_void" and Game.pouches[2] == "pouch_alchemist", "pouch slots swap")
	Game.add_item("pouch_brass", 1)
	await press("inventory")
	var inv: InventoryMenu = ui.current_menu
	await wait(0.2)
	var brass_slot: InvSlot = null
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "item" and str(s.payload.get("id", "")) == "pouch_brass":
			brass_slot = s
	check(brass_slot != null, "a spare pouch shows in the pack grid")
	var pslots := inv._pouch_row.get_children()
	var drag: Variant = inv.drag_data_for(brass_slot)
	check(inv.can_drop_on(pslots[3], drag) and not inv.can_drop_on(inv._loadout_row.get_children().filter(func(c): return c is InvSlot)[0], drag),
		"pouches drop on pouch slots only")
	inv.drop_on(pslots[3], drag)
	check(Game.pouches[3] == "pouch_brass" and Game.item_count("pouch_brass") == 0, "dragged the Brass-Buckled Pouch onto pouch slot 4")
	await wait(0.1)
	inv._on_slot_clicked(inv._pouch_row.get_child(3), MOUSE_BUTTON_RIGHT, false)
	check(Game.pouches[3] == "" and Game.item_count("pouch_brass") == 1, "right-click takes a pouch off")
	Game.equip_pouch("pouch_brass", 3)
	await press("inventory")
	# clear the clutter for the rest of the test
	for id in fillers + ["ember_essence"]:
		Game.remove_item(id, Game.item_count(id))
	# ---------------------------------------------------------------- recipes, stations and the Crafting Book
	check(Catalog.RECIPES.size() >= 60, "%d crafting recipes" % Catalog.RECIPES.size())
	for st in Catalog.STATION_ORDER:
		check(Catalog.recipes_for(st).size() >= 9, "%s has %d recipes" % [st, Catalog.recipes_for(st).size()])
	var stations := get_tree().get_nodes_in_group("stations")
	var ids := stations.map(func(s): return s.station)
	check(stations.size() == 5 and ids.has("forge") and ids.has("loom") and ids.has("altar") and ids.has("alchemy") and ids.has("workbench"),
		"five crafting stations stand in Emberwick (%s)" % str(ids))
	Game.add_gold(5000)
	Game.add_item("copper_ore", 6)
	check(Game.craft_block("copper_ingot", "workbench") == "station", "ingots need the Forge, not the Workbench")
	check(Game.craft_block("copper_ingot", "field") == "station", "...and can't be made from the Crafting Book")
	check(Game.craft_block("copper_ingot", "forge") == "", "...but the Forge can smelt them")
	var xp0 := Game.artisan_xp
	var out := Game.craft("copper_ingot", "forge")
	check(out.has("items") and Game.item_count("copper_ingot") == 1 and Game.item_count("copper_ore") == 4, "smelted a Copper Ingot")
	check(Game.artisan_xp == xp0 + Catalog.recipe_xp("copper_ingot"), "crafting earns Artisan experience")
	check(Game.craft_max("copper_ingot", "forge") == 2, "craft_max counts the batches you can afford (%d)" % Game.craft_max("copper_ingot", "forge"))
	check(Game.craft_block("w_gatling", "forge") == "schematic", "the Gatling needs its schematic")
	check(Game.craft_block("brass_ingot", "forge") == "rank", "brass needs Artisan rank 2")
	# open the Forge with E and craft through the real menu
	var forge: CraftingStation = stations.filter(func(s): return s.station == "forge")[0]
	var fpos := forge.global_position
	p.teleport(fpos + (Vector3.ZERO - fpos).normalized() * 3.2 + Vector3.UP * 0.4, NAN)
	await wait(0.3)
	aim_at(p, fpos + Vector3.UP * 0.9)
	await get_tree().physics_frame
	p._update_interaction()
	check(p.interact_target == forge and p.interact_text.contains("Forge"), "looking at the Forge shows its prompt (%s)" % p.interact_text.split("\n")[0])
	await press("interact")
	await wait(0.2)
	check(ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).station == "forge", "E opens the Forge's crafting screen")
	var cm: CraftingMenu = ui.current_menu
	var row := cm._body.find_child("Recipe_copper_ingot", true, false) as Button
	check(row != null, "the Forge lists Copper Ingot")
	if row:
		row.pressed.emit()
		await wait(0.15)
	var craft_btn: Button = null
	for b in cm._body.find_children("*", "Button", true, false):
		if (b as Button).text == "Craft" and not (b as Button).disabled:
			craft_btn = b
	check(craft_btn != null, "the details card has an active Craft button")
	if craft_btn:
		craft_btn.pressed.emit()
		await wait(0.15)
	check(Game.item_count("copper_ingot") == 2, "clicking Craft smelted another ingot")
	cm._set_tab("upgrade")
	await wait(0.1)
	check(cm._body.get_child_count() > 0, "the Forge has an Upgrade tab")
	ui.close_menu()
	await press("crafting")
	check(ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).is_book(), "B opens the Crafting Book")
	await press("crafting")
	check(not ui.is_menu_open(), "B closes it")
	# field crafting: a cloth pouch anywhere
	Game.add_item("spun_cloth", 2)
	check(Game.can_craft("pouch_cloth", "field") and Game.craft("pouch_cloth", "field").has("items"), "a Patched Cloth Pouch can be sewn anywhere")
	# schematics: picked up from the ground
	Pickup.drop_item(p, p.global_position + Vector3.UP * 1.0, "sch_w_gatling")
	await wait(1.5)
	check(Game.knows_recipe("w_gatling"), "picking up a schematic teaches the recipe")
	check(Game.craft_block("w_gatling", "forge") == "rank", "...which still needs Artisan rank 6")
	# Artisan rank and crafted weapon levels
	Game.add_artisan_xp(int(Catalog.ARTISAN_XP[5]) - Game.artisan_xp)
	check(Game.artisan_rank() == 6, "Artisan rank 6 (%d)" % Game.artisan_rank())
	for id in ["steel_plate", "brass_ingot", "spring_coil", "clockwork_core"]:
		Game.add_item(id, 4)
	var made := Game.craft("w_gatling", "forge")
	check(made.has("weapon") and int(made["weapon"]["rarity"]) >= 1 and int(made["weapon"]["level"]) == 2, "crafted a Steamroller Gatling at level +1 (rank 6)")
	# enchanting
	var ench_uid := Game.add_weapon(Catalog.make_weapon("ember_wand", 1, ["brutal"]), false)
	for id in ["rune_ink", "focus_gem", "runesteel_ingot", "clockwork_core"]:
		Game.add_item(id, 6)
	check(Game.reroll_perks(ench_uid) and not "brutal" in Game.get_weapon(ench_uid)["perks"], "rerolled perks at the altar (%s)" % str(Game.get_weapon(ench_uid)["perks"]))
	check(Game.infuse_weapon(ench_uid) and int(Game.get_weapon(ench_uid)["rarity"]) == 2, "infused Uncommon -> Rare")
	check(Game.infuse_weapon(ench_uid) and int(Game.get_weapon(ench_uid)["rarity"]) == 3 and Game.get_weapon(ench_uid)["perks"].size() == 2,
		"infused Rare -> Epic with a second perk")
	check(Catalog.infuse_cost(Game.get_weapon(ench_uid)).is_empty(), "infusion stops at Epic")
	# upgrades to +9 with rank gates
	var up_w := Game.get_weapon(ench_uid)
	up_w["level"] = 9
	check(Game.upgrade_block(ench_uid) == "rank", "+9 -> +10 needs a higher Artisan rank")
	Game.add_artisan_xp(5000)
	for id in ["rune_shard", "ley_crystal", "rune_ink", "focus_gem", "runesteel_ingot"]:
		Game.add_item(id, 12)
	check(Game.upgrade_weapon(ench_uid) and int(Game.get_weapon(ench_uid)["level"]) == 10, "upgraded to the max level, +9")
	check(Catalog.upgrade_cost(Game.get_weapon(ench_uid)).is_empty(), "no upgrades past level 10")
	# ---------------------------------------------------------------- gathering nodes
	var kinds := {}
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		kinds[h.kind] = int(kinds.get(h.kind, 0)) + 1
	for k in ["ore_copper", "ore_iron", "glowcap", "sunpetal", "reeds"]:
		check(int(kinds.get(k, 0)) >= 8, "%d %s nodes in the valley" % [int(kinds.get(k, 0)), k])
	for k in ["ore_iron", "glowcap", "reeds"]:
		var node: HarvestNode = get_tree().get_nodes_in_group("harvest_nodes").filter(func(h): return h.kind == k)[0]
		var item := str(Catalog.HARVEST[k]["item"])
		var before := Game.item_count(item)
		node.interact(p)
		check(Game.item_count(item) >= before + int(Catalog.HARVEST[k]["count"][0]) and not node.available(), "gathered %s from a %s" % [item, k])
	Game.add_item("pouch_prospector", 1)
	Game.equip_pouch("pouch_prospector", 4)
	var sun: HarvestNode = get_tree().get_nodes_in_group("harvest_nodes").filter(func(h): return h.kind == "sunpetal")[0]
	var s0 := Game.item_count("sunpetal")
	sun.interact(p)
	check(Game.item_count("sunpetal") >= s0 + 2, "the Prospector's Satchel adds one more (%d)" % (Game.item_count("sunpetal") - s0))
	# ---------------------------------------------------------------- talents, levels and milestones
	await press("talents")
	check(ui.current_menu is TalentMenu, "K opens the Talents")
	ui.close_menu()
	var lvl0 := Game.level
	var hp_max0 := Game.max_health()
	while Game.level < 5:
		Game.add_xp(Game.xp_to_next() - Game.xp)
	check(Game.level == 5 and Game.talent_points() == 4, "level 5 with 4 talent points (%d)" % Game.talent_points())
	check(Game.milestones.has(5), "the level 5 milestone cache was handed out")
	check(Game.max_health() > hp_max0, "levels raise max health")
	var cap0 := Game.pack_capacity()
	check(Game.learn_talent("deep_pockets") and Game.pack_capacity() == cap0 + 2, "Deep Pockets: +2 pack slots")
	var tm0 := Game.school_mult("tech")
	check(Game.learn_talent("gunsmith") and absf(Game.school_mult("tech") - tm0 - 0.06) < 0.001, "Gunsmith: +6% tech damage")
	var mh := Game.max_health()
	check(Game.learn_talent("toughness") and Game.max_health() == mh + 15.0, "Toughness: +15 health")
	check(not Game.can_learn_talent("master_artisan"), "Master Artisan needs level 8")
	check(Game.reset_talents() and Game.talent_points() == 4 and Game.pack_capacity() == cap0, "talents refund for gold")
	Game.level = Catalog.MAX_LEVEL - 1
	Game.add_xp(999999)
	check(Game.level == Catalog.MAX_LEVEL and Game.is_max_level(), "levels cap at %d" % Catalog.MAX_LEVEL)
	Game.level = lvl0 + 4
	Game.xp = 0
	# ---------------------------------------------------------------- enemy levels and statuses
	arena = m.world.ground_point(-10, 170, 0.1)
	p.teleport(arena, 0.0, 0.0)
	await wait(0.4)
	fwd = -p.global_transform.basis.z
	var lv := spawn_still("crawler", ahead(9.0), 6)
	check(lv.level >= 6 and absf(lv.max_hp - 55.0 * (1.0 + Catalog.ENEMY_HP_PER_LEVEL * float(lv.level - 1))) < 0.5, "a level %d crawler has scaled health (%.0f)" % [lv.level, lv.max_hp])
	check(lv._lvl_label != null and lv._lvl_label.text == "Lv %d" % lv.level, "foes wear a level tag")
	lv.queue_free()
	# ---------------------------------------------------------------- the new weapons
	var golem := spawn_still("golem", ahead(8.0), 1)
	golem.max_hp = 99999.0
	golem.hp = 99999.0
	await wait(0.2)
	# Rimefang Wand: frost shards chill
	await wield(p, "frost_wand")
	aim_at(p, golem.aim_point())
	check(p.current is SpellCaster and (p.current as SpellCaster).cast_mode() == "spray", "Rimefang Wand handler")
	var hp0 := golem.hp
	p.mana = Game.max_mana()
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	await wait(0.4)
	check(golem.hp < hp0 and golem.is_chilled(), "frost shards hit and chill (%.0f dmg)" % (hp0 - golem.hp))
	# Emberwick Wand: burning
	await wield(p, "ember_wand")
	aim_at(p, golem.aim_point())
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	await wait(0.4)
	check(golem.is_burning(), "ember bolts set the golem ablaze")
	golem.set_physics_process(true)
	hp0 = golem.hp
	await wait(1.1)
	golem.set_physics_process(false)
	check(golem.hp < hp0, "burning ticks fire damage (%.1f)" % (hp0 - golem.hp))
	# Bellows Flamethrower (needs the foe close)
	golem.global_position = ahead(5.0)
	await wield(p, "flamer")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	var fuel0 := (p.current as WeaponGun).mag
	p.current.primary(true)
	await wait(0.6)
	p.current.primary(false)
	check(golem.hp < hp0 and (p.current as WeaponGun).mag < fuel0, "the flamethrower scorches in a cone (%.0f dmg)" % (hp0 - golem.hp))
	# Steamroller Gatling: spin-up, slow, then rivets
	golem.global_position = ahead(10.0)
	await wield(p, "gatling")
	aim_at(p, golem.aim_point())
	var gun := p.current as WeaponGun
	hp0 = golem.hp
	gun.primary(true)
	await wait(0.18)
	check(gun.mag == gun.mag_size() and p.weapon_slow > 0.0, "the gatling spins up before firing and slows you")
	await wait(1.5)
	check(gun.spin > 0.95 and gun.mag < gun.mag_size(), "...then fires a torrent (%d rivets)" % (gun.mag_size() - gun.mag))
	gun.primary(false)
	await wait(0.5)
	check(golem.hp < hp0 and p.weapon_slow == 0.0, "rivets hit and the slow ends on release")
	# Brass Longshot: zoom
	await wield(p, "longshot")
	aim_at(p, golem.aim_point())
	p.current.secondary(true)
	check(p.zoom < 0.5, "RMB zooms the Longshot's scope")
	hp0 = golem.hp
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	check(golem.hp < hp0 - 40.0, "a scoped Longshot shot hits hard (%.0f)" % (hp0 - golem.hp))
	p.current.secondary(false)
	await wait(0.4)
	check(p._zoom_cur > 0.9, "the zoom lets go")
	# Clockwork Crossbow
	await wield(p, "crossbow")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	await wait(0.5)
	check(golem.hp < hp0 and (p.current as WeaponGun).mag == 5, "a crossbow bolt hit (%.0f)" % (hp0 - golem.hp))
	# Wispcaller Grimoire: homing wisps
	await wield(p, "seeker_tome")
	aim_at(p, golem.aim_point() + Vector3.UP * 2.0)
	hp0 = golem.hp
	p.mana = Game.max_mana()
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	await wait(1.4)
	check(golem.hp < hp0, "homing wisps find the golem even aimed high (%.0f)" % (hp0 - golem.hp))
	# Sunlance Scepter: a held beam (god mode makes spells free, so turn it off for the mana checks)
	p.god_mode = false
	p.health = Game.max_health()
	await wield(p, "sun_scepter")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	p.mana = Game.max_mana()
	var mana0 := p.mana
	p.current.primary(true)
	await wait(1.0)
	p.current.primary(false)
	p.god_mode = true
	check(golem.hp < hp0 - 8.0 and p.mana < mana0 - 4.0, "the sun beam burns and drains mana (%.0f dmg, %.0f mana)" % [hp0 - golem.hp, mana0 - p.mana])
	# Gloom Orb: pull and implode
	var orb_crawler := spawn_still("crawler", ahead(9.5, 1.5), 1)
	orb_crawler.max_hp = 9999.0
	orb_crawler.hp = 9999.0
	await wield(p, "void_orb")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	p.mana = Game.max_mana()
	p.current.primary(true)
	await wait(0.05)
	p.current.primary(false)
	await wait(3.6)
	check(golem.hp < hp0 - 30.0, "the Gloom Orb grinds and implodes (%.0f)" % (hp0 - golem.hp))
	check(is_instance_valid(orb_crawler) and orb_crawler.hp < 9999.0, "...catching the crawler nearby too")
	if is_instance_valid(orb_crawler):
		orb_crawler.queue_free()
	# Piston Maul: ground slam
	p.teleport(arena, NAN)
	await wait(0.2)
	golem.global_position = ahead(2.2)
	await wield(p, "steam_hammer")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	p.current.secondary(true)
	await wait(1.7)
	check(golem.hp < hp0 - 40.0, "the Piston Maul's slam lands (%.0f)" % (hp0 - golem.hp))
	# Runeblade: rune wave for mana
	p.god_mode = false
	golem.global_position = ahead(8.0)
	await wield(p, "runeblade")
	aim_at(p, golem.aim_point())
	hp0 = golem.hp
	p.mana = Game.max_mana()
	mana0 = p.mana
	p.current.secondary(true)
	await wait(1.2)
	check(p.mana < mana0 - 3.0 and golem.hp < hp0, "the Runeblade's wave costs mana and hits at range (%.0f)" % (hp0 - golem.hp))
	p.god_mode = true
	golem.queue_free()
	# ---------------------------------------------------------------- take a weapon off the ground with E
	p.teleport(arena, NAN)
	await wait(0.2)
	await wield(p, "arc_pistol")
	var floor_w := Catalog.make_weapon("frost_wand", 2)
	var drop_at: Vector3 = ahead(3.0) + Vector3.UP * 0.8
	var pk := Pickup.drop_weapon(p, drop_at, floor_w)
	pk.velocity = Vector3.ZERO
	await wait(1.6)
	aim_at(p, pk.global_position)
	await get_tree().physics_frame
	p._update_interaction()
	var dbg_hit := p.aim_ray(Player.INTERACT_RANGE, 1 | 4 | 32)
	check(p.interact_target == pk and p.interact_text.contains("Wield"), "looking at a dropped weapon offers to wield it (%s | ray %s, pickup at %s, player at %s)" % [
		p.interact_text.split("\n")[0], str(dbg_hit.get("collider")), str(pk.global_position), str(p.global_position)])
	var held_uid := int(Game.loadout[0])
	await press("interact")
	await wait(0.2)
	check(Game.loadout_weapon(0).get("base", "") == "frost_wand" and p.current_id == "frost_wand", "E wields it in the active slot")
	check(not Game.get_weapon(held_uid).is_empty() and Game.equipped_slot(held_uid) < 0, "the old weapon went into the pack")
	# ---------------------------------------------------------------- quests: Hot Metal
	Quests.accept("q_forge")
	check(Game.item_count("copper_ore") >= 2, "Hot Metal hands over some ore")
	var vein: HarvestNode = get_tree().get_nodes_in_group("harvest_nodes").filter(func(h): return h.kind == "ore_copper")[0]
	vein.interact(p)
	if Quests.objective_progress("q_forge", 0) < 4.0:
		var vein2: HarvestNode = get_tree().get_nodes_in_group("harvest_nodes").filter(func(h): return h.kind == "ore_copper")[1]
		vein2.interact(p)
	check(Quests.objective_done("q_forge", 0), "mined 4 copper ore for the quest")
	await wait(0.7)
	check(ui.hud._obj_text.text.contains("Smelt"), "the objective moves on to smelting (%s)" % ui.hud._obj_text.text)
	Game.craft("copper_ingot", "forge")
	Game.craft("copper_ingot", "forge")
	check(Quests.status("q_forge") == "ready", "Hot Metal complete (%s)" % Quests.status("q_forge"))
	await wait(0.7)
	check(ui.hud._obj_text.text.contains("Return to"), "objective: return to Odda (%s)" % ui.hud._obj_text.text)
	check(Quests.turn_in("q_forge") and Game.item_count("pouch_leather") >= 1, "turned in; got a Leather Belt Pouch")
	Quests.accept("q_talents")
	await get_tree().process_frame
	check(Quests.objective_done("q_talents", 0), "Find Your Edge: level objective already met")
	Game.learn_talent("fleet_foot")
	check(Quests.status("q_talents") == "ready", "spending a talent point completes it")
	# ---------------------------------------------------------------- the "now entering" area banner
	var hud: Hud = ui.hud
	var banner_ok := 0
	var spots := {"north_hills": Vector2(30, -190), "woods": Vector2(-90, -40), "flats": Vector2(-10, 170),
		"lake": Vector2(-128, 12), "foundry": Vector2(150, -175), "town": Vector2(0, 12)}
	for want in spots:
		var sp: Vector2 = spots[want]
		p.teleport(m.world.ground_point(sp.x, sp.y, 0.3), NAN)
		await get_tree().process_frame
		await get_tree().process_frame
		var name_ok := hud._area_name.text == str(WorldLayout.AREAS[want]["name"])
		if hud._area_id == want and name_ok and hud._area_panel.visible:
			banner_ok += 1
		else:
			printerr("TEST INFO banner at %s: id=%s name=%s visible=%s" % [want, hud._area_id, hud._area_name.text, hud._area_panel.visible])
	check(banner_ok == spots.size(), "the area banner names each region right after a teleport (%d/%d)" % [banner_ok, spots.size()])
	check(hud._area_sub.text.contains("Crafting stations") or hud._area_sub.text.contains("vendors"), "Emberwick's banner lists what is there")
	# ---------------------------------------------------------------- save / load
	Game.set_tracked_recipe("pouch_rune")
	Game.discover_area("shrine", true)
	Game.attune_waypoint("ley_east")
	var snap := {"pouches": Game.pouches.duplicate(), "talents": Game.talents.duplicate(), "artisan": Game.artisan_xp,
		"sch": Game.schematics.size(), "mile": Game.milestones.size(), "found": Game.discovered.size()}
	main.save_now()
	Game.pouches = ["", "", "", "", ""]
	Game.talents = {}
	Game.artisan_xp = 0
	Game.schematics = {}
	Game.discovered = {}
	Game.waypoints = {}
	check(SaveSystem.load_game(), "save loaded")
	check(Game.discovered.size() == int(snap["found"]) and Game.discovered.has("shrine") and Game.waypoints.has("ley_east") and Game.waypoints.has("town"),
		"charted regions and attuned ley stones survive a save")
	check(Game.pouches == snap["pouches"] and Game.talents == snap["talents"], "pouches and talents survive a save")
	check(Game.artisan_xp == snap["artisan"] and Game.schematics.size() == snap["sch"] and Game.milestones.size() == snap["mile"],
		"Artisan rank, schematics and milestones survive a save")
	check(Game.tracked_recipe == "pouch_rune", "the tracked recipe survives a save")
	Game.from_dict({"gold": 10, "weapons": [], "loadout": [0, 0], "upgrades": {"satchel": 2, "vitality": 1}})
	check(Game.pouches[0] == "pouch_cloth" and Game.pouches[1] == "pouch_brass" and Game.pouches[2] == "pouch_brass"
		and not Game.upgrades.has("satchel") and Game.upgrade_tier("vitality") == 1, "old saves trade Bigger Satchel tiers for pouches")
	check(Game.discovered.has("town") and Game.waypoints.has("town"), "old saves start with Emberwick charted and the plaza open for travel")
	SaveSystem.load_game()
	await wait(0.2)
	printerr("TEST SUMMARY passes=%d fails=%d" % [passes, fails])
	get_tree().quit(0 if fails == 0 else 1)
