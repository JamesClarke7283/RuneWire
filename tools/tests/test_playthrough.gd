extends Node
## A scripted *played* session. Every step goes through what a player does: aim at things and press E
## (the real interaction raycast), I for the inventory, number keys, LMB, Esc, and clicks on the real
## menu buttons. The loop: Gus's quest -> equip the reward from the inventory -> fight -> turn in ->
## Brannoc's treasure quest -> open chests -> claim a Ley Key -> harvest crystals -> scavenge scrap ->
## craft and upgrade at the Workbench -> brew at the Alchemist's Table -> mine copper and smelt it at
## the Forge -> cut reeds, weave cloth and sew a pouch at the Loom -> wear it (pack grows) -> spend a
## talent point -> sell to Gus -> throw a bomb from a quick slot -> swap a weapon off the ground -> stand
## on a floating island, unlock its Ley Vault and collect the loot -> attune a ley stone -> M for the map,
## travel there and back. The objective tracker is checked along the way.
## Run: godot --headless --path . -- --autostart --no-intro --test=playthrough   (windowed: also /tmp/rw_play_*.png)

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
		await get_tree().physics_frame


## Press and release an input action. Waits on idle frames too: input is flushed once per idle frame,
## and a slow UI frame can run several physics steps, so physics frames alone may not deliver it.
func press(action: String) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	Input.parse_input_event(ev)
	await get_tree().process_frame
	await get_tree().process_frame
	await frames(2)
	var up := InputEventAction.new()
	up.action = action
	up.pressed = false
	Input.parse_input_event(up)
	await get_tree().process_frame
	await get_tree().process_frame
	await frames(2)


func shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/rw_play_%s.png" % name)
	printerr("SHOT ", name)


func aim_at(target: Vector3) -> void:
	var d := target - p.camera.global_position
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	p._apply_look()


## Walk up to something (teleport to `stand`), look at `look`, check the HUD prompt, press E.
func interact_at(stand: Vector3, look: Vector3, prompt: String) -> bool:
	p.teleport(main.world.ground_point(stand.x, stand.z, 0.15), NAN)
	await frames(3)
	aim_at(look)
	await frames(4)
	var ok := p.interact_text.contains(prompt)
	if not ok:
		printerr("TEST INFO prompt was '%s' (wanted '%s')" % [p.interact_text, prompt])
	await press("interact")
	await frames(3)
	return ok


func find_button(root: Node, text: String) -> Button:
	if root == null:
		return null
	for c in root.find_children("*", "Button", true, false):
		var b := c as Button
		if b.is_visible_in_tree() and not b.disabled and not b.is_queued_for_deletion() and b.text.contains(text):
			return b
	return null


func click(root: Node, text: String) -> bool:
	var b := find_button(root, text)
	if b == null:
		printerr("TEST INFO no button '%s'" % text)
		return false
	b.pressed.emit()
	await frames(3)
	return true


## The smallest card (PanelContainer) under `root` holding a label that reads exactly `title`.
func find_card(root: Node, title: String) -> Node:
	var best: Node = null
	var best_n := 1 << 30
	for card in root.find_children("*", "PanelContainer", true, false):
		for l in card.find_children("*", "Label", true, false):
			if (l as Label).text == title:
				var n := card.find_children("*", "", true, false).size()
				if n < best_n:
					best_n = n
					best = card
				break
	return best


## The station of that kind: walk up to it, look at it, press E.
func use_station(station: String) -> void:
	var st: Node3D = get_tree().get_nodes_in_group("stations").filter(func(s): return s.station == station)[0]
	var prop: Node3D = st.get_parent()
	await interact_at(prop.global_position + prop.global_transform.basis.z * 2.6, prop.global_position + Vector3.UP * 0.9,
		Catalog.STATIONS[station]["name"])
	await frames(2)


func nearest_node(kind: String) -> HarvestNode:
	var best: HarvestNode = null
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		if h.kind == kind and h.available() and (best == null or h.global_position.distance_to(p.global_position) < best.global_position.distance_to(p.global_position)):
			best = h
	return best


func talk_to(npc_id: String) -> bool:
	var npc: Npc = main.world.pois.npcs[npc_id]
	var stand: Vector3 = npc.global_position + npc.global_transform.basis.z * 2.3
	await interact_at(stand, npc.global_position + Vector3.UP * 1.1, "Talk to")
	return ui.current_menu is DialogueMenu


func run(m: Node) -> void:
	main = m
	p = m.player
	ui = m.ui
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func():
		printerr("TEST TIMEOUT passes=%d fails=%d" % [passes, fails])
		get_tree().quit(2))
	printerr("TEST start")
	await wait(1.0)
	# The building tutorial (covered by test_core) is taken as done: it unlocks the new quests.
	Quests.state["q_arrival"] = {"status": "done", "progress": [1.0, 2.0, 1.0], "times": 1}
	var gold0 := Game.gold
	# ---------------------------------------------------------------- 1. Gus's quest
	var opened_d := await talk_to("gus")
	check(opened_d, "E on Gus opens his dialogue")
	var q_off := await click(ui.current_menu, "Two-Fisted Tinkering")
	check(q_off, "Gus offers Two-Fisted Tinkering")
	var acc := await click(ui.current_menu, "Accept")
	check(acc, "clicked Accept")
	check(Quests.is_active("q_loadout") and Game.has_weapon_base("thunder_wrench"), "quest accepted, Thunder Wrench received")
	await click(ui.current_menu, "Goodbye")
	check(not ui.is_menu_open(), "Goodbye closes the dialogue")
	await wait(0.7)
	check(ui.hud._obj_panel.visible and ui.hud._obj_text.text.begins_with("Equip the Thunder Wrench"), "the objective tracker shows the next step (%s)" % ui.hud._obj_text.text)
	await shot("objective")
	# ---------------------------------------------------------------- 2. equip it from the inventory
	await press("inventory")
	check(ui.current_menu is InventoryMenu, "I opens the inventory")
	var inv: InventoryMenu = ui.current_menu
	await frames(2)
	var wslot: InvSlot = null
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "weapon" and Game.get_weapon(int(s.payload["uid"])).get("base", "") == "thunder_wrench":
			wslot = s
	check(wslot != null, "the wrench is in the pack grid")
	wslot.mouse_entered.emit()
	await press("slot_2")
	check(Game.loadout_weapon(1).get("base", "") == "thunder_wrench", "hover the wrench + press 2: it moves into weapon slot 2")
	await shot("inventory")
	await press("inventory")
	check(not ui.is_menu_open(), "I closes the inventory")
	await press("slot_2")
	check(p.current is MeleeWeapon, "pressing 2 in play draws the wrench (slot %d, %s)" % [p.slot, p.current_id])
	# ---------------------------------------------------------------- 3. fight with LMB
	p.teleport(m.world.ground_point(-10, 170, 0.15), 0.0, 0.0)
	await wait(0.4)
	var kills := 0
	for i in 3:
		var fwd := -p.global_transform.basis.z
		var foe := Enemy.spawn("crawler", m.world, m.world.ground_point(p.global_position.x + fwd.x * 2.2, p.global_position.z + fwd.z * 2.2, 0.1))
		foe.set_physics_process(false)
		await frames(3)
		aim_at(foe.aim_point())
		for swing in 4:
			if not is_instance_valid(foe) or foe.dead:
				break
			await press("primary")
			await wait(0.7)
		kills += 1 if not is_instance_valid(foe) or foe.dead else 0
	check(kills == 3, "LMB swings felled 3 crawlers (%d)" % kills)
	check(Quests.status("q_loadout") == "ready", "Gus's quest objectives done")
	var bombs := Game.item_count("spark_bomb")
	var talked := await talk_to("gus")
	var offered := await click(ui.current_menu, "Turn in: Two-Fisted Tinkering")
	check(talked and offered, "turn-in offered by Gus")
	var claimed := await click(ui.current_menu, "Claim reward")
	check(claimed and Game.item_count("spark_bomb") == bombs + 3, "claimed: 3 Spark Bombs")
	await click(ui.current_menu, "Goodbye")
	# ---------------------------------------------------------------- 4. treasure for Brannoc
	talked = await talk_to("brannoc")
	offered = await click(ui.current_menu, "X Marks the Spot")
	check(talked and offered, "Brannoc offers X Marks the Spot")
	await click(ui.current_menu, "Accept")
	await click(ui.current_menu, "Goodbye")
	var gold_c := Game.gold
	var opened := 0
	var plain := get_tree().get_nodes_in_group("chests").filter(func(c): return not c.vault and not c.opened)
	for c in plain.slice(0, 3):
		var ch: TreasureChest = c
		var ok := await interact_at(ch.global_position + ch.global_transform.basis.z * 1.9, ch.global_position + Vector3.UP * 0.45, "Open treasure chest")
		opened += 1 if ok and ch.opened else 0
		await wait(2.2)
	check(opened == 3, "E opened 3 treasure chests (%d)" % opened)
	check(Game.gold > gold_c, "walked up the chest gold (%d -> %d)" % [gold_c, Game.gold])
	talked = await talk_to("brannoc")
	offered = await click(ui.current_menu, "Turn in: X Marks the Spot")
	check(talked and offered, "treasure quest turned in")
	var keys := Game.item_count("ley_key")
	await click(ui.current_menu, "Claim reward")
	check(Game.item_count("ley_key") == keys + 1, "Brannoc's reward: a Ley Key")
	await click(ui.current_menu, "Goodbye")
	# ---------------------------------------------------------------- 5. gather
	var crystal: HarvestNode = null
	var scraps := []
	for h in get_tree().get_nodes_in_group("harvest_nodes"):
		var hp: Vector3 = h.global_position
		if h.kind == "crystal" and crystal == null and hp.y < m.world.ground_y(hp.x, hp.z) + 2.0:
			crystal = h   # a cluster on the ground, not on a floating island
		elif h.kind == "scrap":
			scraps.append(h)
	var lc := Game.item_count("ley_crystal")
	var cp := crystal.global_position
	await interact_at(cp + Vector3(1.7, 0, 1.7), cp + Vector3.UP * 0.7, "Harvest Ley Crystals")
	check(Game.item_count("ley_crystal") >= lc + 2, "E harvested ley crystals (%d -> %d)" % [lc, Game.item_count("ley_crystal")])
	var gears := Game.item_count("scrap_gear")
	for hn in scraps.slice(0, 2):
		var pile: Node3D = hn.get_parent()
		var away := (pile.global_position - Vector3(150, pile.global_position.y, -175)).normalized()
		await interact_at(pile.global_position - away * 3.0, pile.global_position + Vector3.UP * 0.6, "Scavenge")
	check(Game.item_count("scrap_gear") >= gears + 2, "E scavenged scrap heaps (%d -> %d gears)" % [gears, Game.item_count("scrap_gear")])
	# ---------------------------------------------------------------- 6. workbench
	var wb: Node3D = get_tree().get_first_node_in_group("workbench")
	var bench: Node3D = wb.get_parent()
	await interact_at(bench.global_position + bench.global_transform.basis.z * 2.0, bench.global_position + Vector3.UP * 0.8, "Workbench")
	check(ui.current_menu is WorkbenchMenu, "E on the Workbench opens it")
	var wm: WorkbenchMenu = ui.current_menu
	await frames(2)
	# a few more scraps and an ember, as if picked up on the way (the bomb and the upgrade both need gears)
	Game.add_item("ember_essence", 1)
	Game.add_item("scrap_gear", 4)
	var sbombs := Game.item_count("spark_bomb")
	var picked := await click(wm._body, "Spark Bomb")
	var crafted := await click(wm._body, "Craft")
	check(picked and crafted, "picked Spark Bomb in the recipe list and clicked Craft")
	check(Game.item_count("spark_bomb") == sbombs + 2, "crafted 2 Spark Bombs")
	await shot("workbench")
	await click(wm._tab_row, "Upgrade")
	var pistol := Game.loadout_weapon(0)
	var upgraded := await click(wm._body, "Upgrade to +1")
	check(upgraded and int(Game.get_weapon(int(pistol["uid"]))["level"]) == 2, "clicked Upgrade: %s is now +1" % Catalog.display_name(str(pistol["base"])))
	await press("pause")
	check(not ui.is_menu_open(), "Esc closes the Workbench")
	# ---------------------------------------------------------------- 6b. the other crafting stations
	await use_station("alchemy")
	check(ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).station == "alchemy", "E on the Alchemist's Table opens it")
	var draughts := Game.item_count("mana_draught")
	await click((ui.current_menu as CraftingMenu)._body, "Mana Draught")
	await click((ui.current_menu as CraftingMenu)._body, "Craft")
	check(Game.item_count("mana_draught") == draughts + 1, "brewed a Mana Draught at the Alchemist's Table (%s, pack %d/%d)" % [
		Game.craft_block("mana_draught", "alchemy"), Game.pack_used(), Game.pack_capacity()])
	await press("pause")
	# mine copper, smelt it at the Forge
	var vein: HarvestNode = nearest_node("ore_copper")
	var vp := vein.global_position
	var ore0 := Game.item_count("copper_ore")
	await interact_at(vp + (Vector3(0, vp.y, 0) - vp).normalized() * 2.4, vp + Vector3.UP * 0.6, "Mine the Copper Vein")
	check(Game.item_count("copper_ore") >= ore0 + 2, "E mined Copper Ore (%d)" % Game.item_count("copper_ore"))
	await use_station("forge")
	check(ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).station == "forge", "E on the Forge opens it")
	await click((ui.current_menu as CraftingMenu)._body, "Copper Ingot")
	await click((ui.current_menu as CraftingMenu)._body, "Craft")
	check(Game.item_count("copper_ingot") >= 1 and Game.artisan_xp > 0, "smelted a Copper Ingot (Artisan xp %d)" % Game.artisan_xp)
	await shot("forge")
	await press("pause")
	# reeds -> cloth -> a pouch, then wear it
	var fiber_spots := 0
	for i in 4:
		if Game.item_count("reed_fiber") >= 6:
			break
		var reed: HarvestNode = nearest_node("reeds")
		var rp := reed.global_position
		await interact_at(rp + (Vector3(-190, rp.y, 10) - rp).normalized() * -2.2, rp + Vector3.UP * 0.8, "Cut the Reed Clump")
		fiber_spots += 1
	check(Game.item_count("reed_fiber") >= 6, "cut %d Reed Fiber from %d clumps" % [Game.item_count("reed_fiber"), fiber_spots])
	await use_station("loom")
	check(ui.current_menu is CraftingMenu and (ui.current_menu as CraftingMenu).station == "loom", "E on the Loom opens it")
	await click((ui.current_menu as CraftingMenu)._body, "Spun Cloth")
	await click((ui.current_menu as CraftingMenu)._body, "Craft ×")    # "Craft ×2" or "×3": one per 3 reeds
	check(Game.item_count("spun_cloth") >= 2, "wove Spun Cloth (×%d)" % Game.item_count("spun_cloth"))
	var pouches0 := Game.item_count("pouch_cloth")
	await click((ui.current_menu as CraftingMenu)._body, "Patched Cloth Pouch")
	await click((ui.current_menu as CraftingMenu)._body, "Craft")
	check(Game.item_count("pouch_cloth") == pouches0 + 1, "sewed a Patched Cloth Pouch")
	await shot("loom")
	await press("pause")
	var cap0 := Game.pack_capacity()
	await press("inventory")
	inv = ui.current_menu
	await frames(3)
	var pouch_slot: InvSlot = null
	for s in inv._grid.get_children():
		if s.payload.get("type", "") == "item" and str(s.payload.get("id", "")) == "pouch_cloth":
			pouch_slot = s
	check(pouch_slot != null, "the new pouch is in the pack")
	var drag: Variant = inv.drag_data_for(pouch_slot)
	var target: InvSlot = inv._pouch_row.get_child(1)
	check(target._can_drop_data(Vector2.ZERO, drag), "it can be dragged onto pouch slot 2")
	target._drop_data(Vector2.ZERO, drag)
	await frames(3)
	check(Game.pouches[1] == "pouch_cloth" and Game.pack_capacity() == cap0 + 3, "wearing two pouches: the pack grew %d -> %d" % [cap0, Game.pack_capacity()])
	await shot("pouches")
	await press("inventory")
	# talents
	check(Game.level >= 2 and Game.talent_points() >= 1, "levelled up along the way (level %d, %d talent points)" % [Game.level, Game.talent_points()])
	await press("talents")
	check(ui.current_menu is TalentMenu, "K opens the Talents")
	var hp_max := Game.max_health()
	var learned := await click(ui.current_menu.find_child("Talent_toughness", true, false), "+")
	check(learned and Game.talent_rank("toughness") == 1 and Game.max_health() == hp_max + 15.0, "spent a point on Toughness (+15 health)")
	await shot("talents")
	await press("talents")
	# ---------------------------------------------------------------- 7. sell a spare to Gus
	var spare := Catalog.make_weapon("boom_mortar", 1)
	Pickup.drop_weapon(p, p.global_position + Vector3(0.6, 1.4, 0.0), spare)
	await wait(2.2)
	var spare_w := {}
	for w in Game.weapons:
		if w["base"] == "boom_mortar":
			spare_w = w
	check(not spare_w.is_empty(), "walked over a weapon drop and picked it up")
	talked = await talk_to("gus")
	var browsed := await click(ui.current_menu, "Browse")
	check(talked and browsed, "asked to browse Gus's Gizmos")
	await frames(4)
	check(ui.current_menu is ShopMenu, "Gus's shop is open")
	var shop: ShopMenu = ui.current_menu
	await click(shop._tab_row, "Sell")
	var gold_s := Game.gold
	var sell_card := find_card(shop._grid, Catalog.weapon_name(spare_w))
	var sold := false
	if sell_card:
		sold = await click(sell_card, "Sell")
	check(sold, "clicked Sell on the spare mortar")
	check(Game.gold == gold_s + Catalog.weapon_value(spare_w) and Game.get_weapon(int(spare_w["uid"])).is_empty(), "sold it for %d gold" % Catalog.weapon_value(spare_w))
	await shot("shop_sell")
	await press("pause")
	# ---------------------------------------------------------------- 8. quick slot 7
	var b0 := Game.item_count("spark_bomb")
	await press("slot_7")
	check(Game.item_count("spark_bomb") == b0 - 1, "key 7 throws a Spark Bomb")
	# ---------------------------------------------------------------- 8b. swap a weapon off the ground
	p.teleport(m.world.ground_point(0, 14, 0.2), 180.0, 0.0)
	await wait(0.3)
	await press("slot_1")
	var held: Dictionary = Game.loadout_weapon(0)
	var fwd2 := -p.global_transform.basis.z
	var ground_w := Catalog.make_weapon("ember_wand", 2)
	var gpk := Pickup.drop_weapon(p, p.global_position + fwd2 * 3.0 + Vector3.UP * 0.8, ground_w)
	gpk.velocity = Vector3.ZERO
	await wait(1.4)
	aim_at(gpk.global_position)
	await frames(4)
	check(p.interact_text.contains("Wield"), "looking at a dropped wand offers to wield it (%s)" % p.interact_text.split("\n")[0])
	await press("interact")
	await frames(3)
	check(Game.loadout_weapon(0).get("base", "") == "ember_wand" and p.current_id == "ember_wand", "E swapped the Emberwick Wand into my hands")
	check(not Game.get_weapon(int(held["uid"])).is_empty(), "the %s went into the pack" % Catalog.display_name(str(held["base"])))
	# ---------------------------------------------------------------- 9. the floating Ley Vault
	var top: Vector3 = m.world.pois.sky_tops["flats"]
	var vault: TreasureChest = null
	for c in get_tree().get_nodes_in_group("chests"):
		if c.chest_id == "vault_sky_flats":
			vault = c
	p.teleport(vault.global_position + vault.global_transform.basis.z * 1.9 + Vector3.UP * 0.6, NAN)
	await wait(1.2)
	check(p.is_on_floor() and absf(p.global_position.y - top.y) < 0.8, "standing on the floating island (y %.1f, top %.1f)" % [p.global_position.y, top.y])
	aim_at(vault.global_position + Vector3.UP * 0.5)
	await frames(4)
	check(p.interact_text.contains("Unlock the Ley Vault"), "the vault asks for a Ley Key (%s)" % p.interact_text)
	var gold_v := Game.gold
	var n_w := Game.weapons.size()
	await press("interact")
	check(vault.opened and Game.item_count("ley_key") == keys, "E unlocked the vault with the key")
	await wait(2.6)
	var stranded := 0
	for pk in get_tree().get_nodes_in_group("pickups"):
		if not is_instance_valid(pk):
			continue   # already walked up (collected) while fetching another piece
		var pp: Vector3 = (pk as Node3D).global_position
		if Vector2(pp.x - top.x, pp.z - top.z).length() < 6.0:
			if pp.y < top.y - 1.0:
				stranded += 1
			elif pk.kind == "weapon":
				p.teleport(Vector3(pp.x, top.y + 0.2, pp.z), NAN)   # walk over to it
				await wait(0.8)
	check(stranded == 0, "vault loot landed on the island, none fell through (%d)" % stranded)
	await wait(1.0)
	check(Game.gold > gold_v, "vault gold collected (%d -> %d)" % [gold_v, Game.gold])
	check(Game.weapons.size() > n_w, "picked up the vault's weapon (%d -> %d)" % [n_w, Game.weapons.size()])
	aim_at(vault.global_position + Vector3.UP * 0.5)
	await wait(0.3)
	await shot("vault_open")
	check(Game.gold > gold0, "net gold over the session: %d -> %d" % [gold0, Game.gold])
	# ---------------------------------------------------------------- 10. the map and ley travel
	var ls: Vector2 = WorldLayout.LEY_STONES["ley_north"]
	p.teleport(m.world.ground_point(ls.x, ls.y + 3.0, 0.3), NAN)   # walk up to the northern ley stone
	await wait(0.8)
	check(Game.waypoints.has("ley_north"), "touching the northern ley stone attunes it")
	check(Game.discovered.has("north_hills") and Game.discovered.has("woods"), "the hills and woods we visited are charted (%d regions)" % Game.discovered.size())
	p.teleport(m.world.ground_point(0, 14, 0.3), 0.0)   # and home again
	await wait(0.6)
	await press("map")
	check(ui.current_menu is MapMenu, "M opens the map")
	var mm := ui.current_menu
	var rt := mm.find_child("RegionsTitle", true, false) as Label if mm else null
	check(rt != null and rt.text.contains("%d / %d" % [Game.discovered.size(), WorldLayout.AREAS.size()]), "the map counts charted regions (%s)" % (rt.text if rt else "?"))
	await wait(0.4)
	await shot("map")
	check(await click(mm, "Northern Ley Stone") and await click(mm, "Travel to"), "picked the northern stone and clicked Travel")
	await wait(0.6)
	var arrive: Vector2 = WorldLayout.WAYPOINTS["ley_north"]["arrive"]
	check(ui.current_menu == null and Vector2(p.global_position.x, p.global_position.z).distance_to(arrive) < 2.0,
		"ley travel to the northern stone (%s)" % str(p.global_position))
	for e in get_tree().get_nodes_in_group("enemies"):   # the hills' crawlers would (rightly) block ley travel
		if (e as Node3D).global_position.distance_to(p.global_position) < 60.0:
			e.queue_free()
	await wait(0.2)
	await press("map")
	check(ui.current_menu is MapMenu and await click(ui.current_menu, "Emberwick Plaza") and await click(ui.current_menu, "Travel to"), "and back to the plaza")
	await wait(0.6)
	check(Vector2(p.global_position.x, p.global_position.z).distance_to(WorldLayout.WAYPOINTS["town"]["arrive"]) < 2.0 and Hud.area_at(p.global_position) == "town",
		"home in Emberwick (%s)" % str(p.global_position))
	printerr("TEST SUMMARY passes=%d fails=%d" % [passes, fails])
	get_tree().quit(0 if fails == 0 else 1)
