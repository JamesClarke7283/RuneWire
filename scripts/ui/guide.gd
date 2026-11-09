class_name Guide
## The objective tracker's brain: works out the single most useful next step for the player and where
## it is. In order: the tracked quest (or one ready to hand in), a tracked crafting recipe, a new job
## from a quest giver, then gentle suggestions (talent points, pouches, keys, an uncharted region, treasure).
## Returns {text, sub, target: Vector3 | null, kind} (empty = nothing to show), plus "hint": an optional
## short side-note shown under the objective.

const AREA_NAMES := {
	"woods": "the Whispering Woods, west of town", "foundry": "the Gearworks Foundry, north-east",
	"shrine": "the Sunken Shrine, north-west", "flats": "the southern flats", "watchtower": "the Old Watchtower, south-west",
	"town": "Emberwick", "arena": "the Arena, east", "ley_north": "the northern hills", "ley_east": "the eastern hills",
	"ley_lake": "the lake island, west", "lake": "the lake shore, west",
}
const ITEM_AREAS := {
	"ember_essence": "woods", "scrap_gear": "foundry", "rune_shard": "shrine", "shade_silk": "woods",
	"clockwork_core": "foundry", "ley_crystal": "woods", "copper_ore": "ley_north", "iron_ore": "foundry",
	"glowcap": "woods", "sunpetal": "flats", "reed_fiber": "lake",
}


static func next_objective(tree: SceneTree) -> Dictionary:
	var player := tree.get_first_node_in_group("player") as Player
	if player == null or player.dead:
		return {}
	var out := _quest_step(tree)
	if out.is_empty():
		out = _recipe_step(tree)
	if out.is_empty():
		out = _new_job(tree)
	if out.is_empty():
		out = _suggestion(tree, player)
	if not out.is_empty():
		out["hint"] = _side_hint(tree, out)
	return out


# ------------------------------------------------------------------ quests
static func _quest_step(tree: SceneTree) -> Dictionary:
	var q := Quests.tracked
	if q == "" or not Quests.is_active(q):
		# a finished quest waiting to be handed in beats a fresh one
		for id in Quests.active_quests():
			if Quests.status(id) == "ready":
				q = id
				break
	if q == "" or not Quests.is_active(q):
		return {}
	var d := Quests.def(q)
	var npc := str(QuestDB.NPC_NAMES.get(d["turn_in"], "the quest giver"))
	if Quests.status(q) == "ready":
		return {"text": "Return to %s for your reward" % npc, "sub": "“%s” is complete" % d["title"],
			"target": QuestNav.npc_pos(tree, d["turn_in"]), "kind": "turn_in"}
	for i in d["objectives"].size():
		if Quests.objective_done(q, i):
			continue
		var o: Dictionary = d["objectives"][i]
		var where := _objective_area(o)
		var sub := "“%s”" % d["title"]
		if where != "":
			sub += "  ·  " + where
		return {"text": Quests.objective_text(q, i), "sub": sub, "target": QuestNav.target_for(q, tree), "kind": "quest"}
	return {}


static func _objective_area(o: Dictionary) -> String:
	var t := str(o.get("target", ""))
	match str(o.get("type", "")):
		"kill", "kill_with":
			var area := str(QuestNav.KILL_AREAS.get(t, ""))
			return "in " + AREA_NAMES[area] if AREA_NAMES.has(area) else ""
		"collect", "harvest":
			var a2 := str(ITEM_AREAS.get(t, ""))
			if t == "ore":
				a2 = "ley_north"
			elif t == "herb":
				a2 = "woods"
			return "found in " + AREA_NAMES[a2] if AREA_NAMES.has(a2) else ""
		"reach":
			return "at " + str(QuestDB.LOCATION_NAMES.get(t, t.capitalize()))
		"talk":
			return "in Emberwick"
		"craft", "upgrade", "enchant":
			var st := _station_of(o)
			return "at the " + str(Catalog.STATIONS[st]["name"]) if st != "" else ""
		"open_chest":
			return "your compass shows the nearest one"
		"pouches":
			return "open your Inventory [I]"
		"talent":
			return "press K"
		"artisan":
			return "craft anything at the stations in Emberwick"
	return ""


static func _station_of(o: Dictionary) -> String:
	var t := str(o.get("target", ""))
	if t.begins_with("station:"):
		return t.substr(8)
	if Catalog.RECIPES.has(t):
		return str(Catalog.recipe(t)["station"])
	match str(o.get("type", "")):
		"upgrade":
			return "workbench"
		"enchant":
			return "altar"
	return ""


# ------------------------------------------------------------------ crafting goal
static func _recipe_step(tree: SceneTree) -> Dictionary:
	var rid := Game.tracked_recipe
	if rid == "" or not Catalog.RECIPES.has(rid):
		return {}
	var r := Catalog.recipe(rid)
	var name := Catalog.recipe_name(rid)
	if not Game.knows_recipe(rid):
		return {"text": "Find the schematic for %s" % name, "sub": "Chests, Ley Vaults, Champions and vendors carry schematics",
			"target": null, "kind": "craft"}
	if Game.artisan_rank() < int(r.get("rank", 1)):
		return {"text": "Reach Artisan rank %d to craft %s" % [int(r.get("rank", 1)), name],
			"sub": "Craft anything at the stations to gain crafting experience", "target": station_pos(tree, "workbench"), "kind": "craft"}
	var missing := first_missing(rid)
	if missing.is_empty():
		var st := str(r["station"])
		return {"text": "Craft %s at the %s" % [name, Catalog.STATIONS[st]["name"]], "sub": "Everything is ready",
			"target": station_pos(tree, st), "kind": "craft"}
	var id := str(missing["id"])
	var need := int(missing["need"])
	# an intermediate you could make right now?
	if Catalog.RECIPES.has(id) and Game.knows_recipe(id) and Game.has_items(Catalog.recipe(id).get("cost", {})):
		var st2 := str(Catalog.recipe(id)["station"])
		return {"text": "Craft %s at the %s" % [Catalog.display_name(id), Catalog.STATIONS[st2]["name"]],
			"sub": "needed for %s (%d/%d)" % [name, Game.item_count(id), need], "target": station_pos(tree, st2), "kind": "craft"}
	var src := str(Catalog.ITEMS.get(id, {}).get("src", ""))
	return {"text": "Get %d more %s" % [need - Game.item_count(id), Catalog.display_name(id)],
		"sub": "for %s  ·  %s" % [name, src] if src != "" else "for %s" % name, "target": source_pos(tree, id), "kind": "gather"}


## The first ingredient a recipe still lacks (following the chain one level down): {id, need}.
static func first_missing(rid: String) -> Dictionary:
	var cost: Dictionary = Catalog.recipe(rid).get("cost", {})
	for id in cost:
		if Game.item_count(id) < int(cost[id]):
			# a refined ingredient whose own inputs are missing: point at the raw material instead
			if Catalog.RECIPES.has(id) and Game.knows_recipe(id) and not Game.has_items(Catalog.recipe(id).get("cost", {})):
				var deeper := first_missing(id)
				if not deeper.is_empty() and not Catalog.RECIPES.has(str(deeper["id"])):
					return deeper
			return {"id": id, "need": int(cost[id])}
	return {}


## Where to get a material: the nearest gathering node that yields it, or its usual area.
static func source_pos(tree: SceneTree, item: String) -> Variant:
	var kind := ""
	for k in Catalog.HARVEST:
		if str(Catalog.HARVEST[k].get("item", "")) == item:
			kind = k
	if kind != "":
		var p: Variant = QuestNav.nearest_in_group(tree, "harvest_nodes", func(h): return h.kind == kind and h.available())
		if p != null:
			return p
	if ITEM_AREAS.has(item):
		var a := str(ITEM_AREAS[item])
		return QuestNav.area_pos("woods" if a == "lake" else a) if a != "lake" else Vector3(-150, 0, 40)
	return null


static func station_pos(tree: SceneTree, station: String) -> Variant:
	return QuestNav.nearest_in_group(tree, "stations", func(s): return s.station == station)


# ------------------------------------------------------------------ new jobs & suggestions
static func _new_job(tree: SceneTree) -> Dictionary:
	var best := ""
	var best_npc := ""
	var best_main := false
	for npc in QuestDB.NPC_NAMES:
		for q in Quests.offered_by(npc):
			var main := bool(Quests.def(q).get("main", false))
			if best == "" or (main and not best_main):
				best = q
				best_npc = npc
				best_main = main
	if best == "":
		return {}
	var who := str(QuestDB.NPC_NAMES[best_npc])
	var text := "Read the Bounty Board by the fountain" if best_npc == "board" else "Talk to %s" % who
	return {"text": text, "sub": "New %s: “%s”" % ["story quest" if best_main else "job", Quests.def(best)["title"]],
		"target": QuestNav.npc_pos(tree, best_npc), "kind": "talk"}


static func _suggestion(tree: SceneTree, player: Player) -> Dictionary:
	if Game.talent_points() > 0:
		return {"text": "Spend your talent point%s: press K" % ("" if Game.talent_points() == 1 else "s"),
			"sub": "%d unspent" % Game.talent_points(), "target": null, "kind": "talent"}
	var spare := _spare_pouch()
	if spare != "" and Game.pouches.has(""):
		return {"text": "Equip your %s in a pouch slot [I]" % Catalog.display_name(spare),
			"sub": "+%d pack slots" % int(Catalog.pouch_def(spare)["slots"]), "target": null, "kind": "pouch"}
	if Game.item_count("ley_key") > 0:
		var v: Variant = QuestNav.nearest_in_group(tree, "chests", func(c): return c.vault and not c.opened)
		if v != null:
			return {"text": "Unlock a Ley Vault with your Ley Key", "sub": "Two of them float in the sky: build something that flies",
				"target": v, "kind": "treasure"}
	var ex := explore_step(player)
	if not ex.is_empty():
		return ex
	var t: Variant = QuestNav.nearest_in_group(tree, "chests", func(c): return not c.vault and not c.opened)
	if t != null:
		var total := 0
		for c in tree.get_nodes_in_group("chests"):
			total += 1
		return {"text": "Hunt for treasure", "sub": "%d / %d treasures found  ·  craft a Treasure Map to point the way" % [Game.opened_chests.size(), total],
			"target": t if player.has_buff("map") else null, "kind": "treasure"}
	return {"text": "Gather, craft and grow stronger", "sub": "Track a recipe in the Crafting Book [B] to be guided to its materials",
		"target": null, "kind": "free"}


## The nearest uncharted region the player is ready for (its foes at most a level above theirs).
static func explore_step(player: Player) -> Dictionary:
	var here := Vector2(player.global_position.x, player.global_position.z)
	var best := ""
	var best_d := INF
	for id in WorldLayout.AREAS:
		var a: Dictionary = WorldLayout.AREAS[id]
		if Game.discovered.has(id) or int(a["levels"][0]) > Game.level + 1:
			continue
		var d := here.distance_to(a["pos"])
		if d < best_d:
			best_d = d
			best = str(id)
	if best == "":
		return {}
	var at: Vector2 = WorldLayout.AREAS[best]["pos"]
	var gy := 0.0
	var tree := player.get_tree()
	var w: World = tree.get_first_node_in_group("world") as World if tree else null
	if w:
		gy = w.ground_y(at.x, at.y)
	return {"text": "Explore the uncharted land %s" % compass_word(here, at),
		"sub": "%d / %d regions discovered  ·  each new one pays XP  ·  map [M]" % [Game.discovered.size(), WorldLayout.AREAS.size()],
		"target": Vector3(at.x, gy, at.y), "kind": "explore"}


## "to the north-west" etc. from one map point to another (north = -Z).
static func compass_word(from: Vector2, to: Vector2) -> String:
	var d := to - from
	var deg := fposmod(rad_to_deg(atan2(d.x, -d.y)), 360.0)   # 0 = north, 90 = east
	var names := ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
	return "to the " + names[int(round(deg / 45.0)) % 8]


static func _spare_pouch() -> String:
	var best := ""
	for id in Catalog.POUCHES:
		if Game.item_count(id) > 0 and (best == "" or int(Catalog.pouch_def(id)["slots"]) > int(Catalog.pouch_def(best)["slots"])):
			best = id
	return best


## A short side-note under the main objective (talents, pouches, a full pack).
static func _side_hint(_tree: SceneTree, main: Dictionary) -> String:
	var k := str(main.get("kind", ""))
	if Game.talent_points() > 0 and k != "talent":
		return "%d talent point%s to spend [K]" % [Game.talent_points(), "" if Game.talent_points() == 1 else "s"]
	var spare := _spare_pouch()
	if spare != "" and Game.pouches.has("") and k != "pouch":
		return "Equip your %s for +%d pack slots [I]" % [Catalog.display_name(spare), int(Catalog.pouch_def(spare)["slots"])]
	if Game.pack_free() <= 2:
		return "Pack nearly full (%d/%d): sell, salvage, craft, or sew a bigger pouch" % [Game.pack_used(), Game.pack_capacity()]
	return ""
