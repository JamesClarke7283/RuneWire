extends Node
## Tracks quest state and objective progress by listening to gameplay events.
## Status per quest: "active" -> "ready" (all objectives met) -> "done" (rewarded).

signal quest_accepted(id: String)
signal quest_updated(id: String)
signal quest_ready(id: String)
signal quest_completed(id: String)
signal tracked_changed(id: String)

var state: Dictionary = {}        # id -> {status, progress: Array[float], times}
var tracked: String = ""


func _ready() -> void:
	Events.enemy_killed.connect(_on_enemy_killed)
	Events.location_reached.connect(func(loc): _advance("reach", loc, 1.0))
	Events.npc_talked.connect(func(npc): _advance("talk", npc, 1.0))
	Events.part_purchased.connect(func(pid, n): _advance("buy_part", pid, float(n)))
	Events.item_purchased.connect(func(iid): _advance("buy", iid, 1.0))
	Events.part_spawned.connect(func(pid, _p): _advance("spawn", pid, 1.0))
	Events.parts_welded.connect(func(_c): _advance("weld", "", 1.0))
	Events.contraption_built.connect(_on_built)
	Events.contraption_driven.connect(func(_c, m): _advance("drive", "", m))
	Events.contraption_altitude.connect(_on_altitude)
	Events.cargo_delivered.connect(func(_cid, zone): _advance("deliver", zone, 1.0))
	Events.challenge_finished.connect(_on_challenge)
	Events.enemy_killed_with.connect(_on_killed_with)
	Events.chest_opened.connect(_on_chest)
	Events.resource_harvested.connect(_on_harvest)
	Events.scavenged.connect(func(n): _advance("scavenge", "", float(n)))
	Events.item_crafted.connect(_on_crafted)
	Events.weapon_upgraded.connect(func(_uid, _lvl): _advance("upgrade", "", 1.0))
	Events.weapon_enchanted.connect(func(_uid): _advance("enchant", "", 1.0))
	Game.loadout_changed.connect(_refresh_equip)
	Game.inventory_changed.connect(_refresh_collect)
	Game.pouches_changed.connect(_refresh_absolute)
	Game.talents_changed.connect(_refresh_absolute)
	Game.artisan_changed.connect(func(_x, _r): _refresh_absolute())
	Game.schematic_learned.connect(func(_r): _refresh_absolute())
	Game.xp_changed.connect(func(_x, _l): _refresh_absolute())


func reset() -> void:
	state = {}
	tracked = ""


func def(id: String) -> Dictionary:
	return QuestDB.QUESTS.get(id, {})


func status(id: String) -> String:
	if not state.has(id):
		return "available" if prereqs_met(id) else "locked"
	return state[id]["status"]


func is_done(id: String) -> bool:
	return state.has(id) and (state[id]["status"] == "done" or int(state[id].get("times", 0)) > 0)


func is_active(id: String) -> bool:
	return state.has(id) and state[id]["status"] in ["active", "ready"]


func prereqs_met(id: String) -> bool:
	for p in def(id).get("prereq", []):
		if not is_done(p):
			return false
	return true


func offered_by(npc: String) -> Array:
	var out := []
	for id in QuestDB.QUESTS:
		var d: Dictionary = QuestDB.QUESTS[id]
		if d["giver"] != npc or not prereqs_met(id):
			continue
		if not state.has(id):
			out.append(id)
		elif d.get("repeatable", false) and state[id]["status"] == "done":
			out.append(id)
	return out


func ready_for(npc: String) -> Array:
	var out := []
	for id in state:
		if state[id]["status"] == "ready" and def(id).get("turn_in", "") == npc:
			out.append(id)
	return out


func active_for(npc: String) -> Array:
	var out := []
	for id in state:
		if state[id]["status"] == "active" and def(id).get("turn_in", "") == npc:
			out.append(id)
	return out


func active_quests() -> Array:
	var out := []
	for id in state:
		if state[id]["status"] in ["active", "ready"]:
			out.append(id)
	return out


func completed_quests() -> Array:
	var out := []
	for id in state:
		if state[id]["status"] == "done" or int(state[id].get("times", 0)) > 0:
			out.append(id)
	return out


func accept(id: String) -> void:
	var d := def(id)
	if d.is_empty():
		return
	var prog := []
	for _o in d["objectives"]:
		prog.append(0.0)
	var times := int(state[id].get("times", 0)) if state.has(id) else 0
	state[id] = {"status": "active", "progress": prog, "times": times}
	tracked = id
	quest_accepted.emit(id)
	tracked_changed.emit(id)
	Events.toast("Quest accepted: %s" % d["title"], "quest")
	if times == 0:
		_give(d.get("on_accept", {}), "Received")
	_refresh_collect()
	_refresh_equip()
	_refresh_absolute()
	_check_ready(id)


func abandon(id: String) -> void:
	if not is_active(id):
		return
	if int(state[id].get("times", 0)) > 0:
		state[id]["status"] = "done"
	else:
		state.erase(id)
	if tracked == id:
		tracked = _pick_tracked()
		tracked_changed.emit(tracked)
	quest_updated.emit(id)


func turn_in(id: String) -> bool:
	if not state.has(id) or state[id]["status"] != "ready":
		return false
	var d := def(id)
	# consume collected quest items
	for i in d["objectives"].size():
		var o: Dictionary = d["objectives"][i]
		if o["type"] == "collect":
			Game.remove_item(o["target"], int(o["count"]))
	var r: Dictionary = d.get("rewards", {})
	if r.has("gold"):
		Game.add_gold(int(r["gold"]), d["title"])
	if r.has("xp"):
		Game.add_xp(int(r["xp"]))
	for pid in r.get("parts", {}):
		Game.add_parts(pid, int(r["parts"][pid]))
		Events.toast("Received %d x %s" % [int(r["parts"][pid]), Catalog.display_name(pid)], "item")
	_give({"items": r.get("items", {}), "weapons": r.get("weapons", [])}, "Received")
	for pid in r.get("unlock_parts", []):
		Game.unlock_part(pid)
	for eid in r.get("unlock_equipment", []):
		Game.unlock_equipment(eid)
	state[id]["status"] = "done"
	state[id]["times"] = int(state[id].get("times", 0)) + 1
	Game.add_stat("quests_done")
	quest_completed.emit(id)
	Events.toast("Quest complete: %s" % d["title"], "quest_done")
	if tracked == id:
		tracked = _pick_tracked()
		tracked_changed.emit(tracked)
	SaveSystem.request_autosave()
	return true


## Hands over items / weapons ({"items": {id: n}, "weapons": [{base, rarity}]}). Schematic ids
## ("sch_<recipe>") teach the recipe; anything that does not fit in the pack lands at your feet.
func _give(g: Dictionary, verb: String) -> void:
	for iid in g.get("items", {}):
		var n := int(g["items"][iid])
		if Catalog.is_schematic(iid):
			Game.learn_schematic(Catalog.schematic_recipe(iid))
			continue
		Game.give_item(iid, n)
		Events.toast("%s %d x %s" % [verb, n, Catalog.display_name(iid)], "item")
	for wd in g.get("weapons", []):
		var base: String = wd.get("base", "random")
		var w := Catalog.make_weapon(base if Catalog.WEAPONS.has(base) else Catalog.random_weapon_base(), int(wd.get("rarity", 0)),
			[], int(wd.get("level", 1)))
		Game.give_weapon(w, true)


func objective_progress(id: String, index: int) -> float:
	if not state.has(id):
		return 0.0
	var p: Array = state[id]["progress"]
	return float(p[index]) if index < p.size() else 0.0


func objective_done(id: String, index: int) -> bool:
	var o: Dictionary = def(id)["objectives"][index]
	return objective_progress(id, index) >= float(o.get("count", 1))


func objective_text(id: String, index: int) -> String:
	var o: Dictionary = def(id)["objectives"][index]
	var count := float(o.get("count", 1))
	var prog := minf(objective_progress(id, index), count)
	match o["type"]:
		"drive", "altitude":
			return "%s (%d/%d m)" % [o["text"], int(prog), int(count)]
		"challenge":
			return o["text"]
	if count > 1:
		return "%s (%d/%d)" % [o["text"], int(prog), int(count)]
	return o["text"]


func set_tracked(id: String) -> void:
	tracked = id
	tracked_changed.emit(id)


func _pick_tracked() -> String:
	var act := active_quests()
	for id in act:
		if def(id).get("main", false):
			return id
	return act[0] if act.size() > 0 else ""


# ---------------------------------------------------------------- progress
## Progress objectives of `type` whose target is "any", `target` or one of `alt` (counted once).
func _advance(type: String, target: String, amount: float, absolute: bool = false, alt: Array = []) -> void:
	for id in state.keys():
		if state[id]["status"] != "active":
			continue
		var objs: Array = def(id)["objectives"]
		var changed := false
		for i in objs.size():
			var o: Dictionary = objs[i]
			if o["type"] != type:
				continue
			var tgt: String = o.get("target", "any")
			if tgt != "any" and tgt != "" and target != tgt and not (target == "" and tgt == "") and not tgt in alt:
				continue
			var count := float(o.get("count", 1))
			var cur: float = state[id]["progress"][i]
			if cur >= count:
				continue
			var nv := maxf(cur, amount) if absolute else cur + amount
			state[id]["progress"][i] = minf(nv, count)
			changed = true
		if changed:
			quest_updated.emit(id)
			_check_ready(id)


func _on_enemy_killed(enemy_type: String, faction: String, _pos: Vector3) -> void:
	for id in state.keys():
		if state[id]["status"] != "active":
			continue
		var objs: Array = def(id)["objectives"]
		var changed := false
		for i in objs.size():
			var o: Dictionary = objs[i]
			if o["type"] != "kill":
				continue
			var tgt: String = o.get("target", "any")
			var ok: bool = tgt == "any" or tgt == enemy_type or tgt == "faction:" + faction
			if not ok:
				continue
			var count := float(o.get("count", 1))
			if state[id]["progress"][i] < count:
				state[id]["progress"][i] += 1.0
				changed = true
		if changed:
			quest_updated.emit(id)
			_check_ready(id)


## kill_with objectives match the killing weapon's kind ("gun", "spell", "melee") or its base id.
func _on_killed_with(enemy_type: String, _faction: String, weapon_kind: String, weapon_base: String, elite: bool) -> void:
	if elite:
		_advance("kill_elite", enemy_type, 1.0)
	if weapon_kind == "":
		return
	for id in state.keys():
		if state[id]["status"] != "active":
			continue
		var objs: Array = def(id)["objectives"]
		var changed := false
		for i in objs.size():
			var o: Dictionary = objs[i]
			if o["type"] != "kill_with":
				continue
			var tgt: String = o.get("target", "any")
			if tgt != "any" and tgt != weapon_kind and tgt != weapon_base and tgt != "school:" + Catalog.weapon_school(weapon_base):
				continue
			if state[id]["progress"][i] < float(o.get("count", 1)):
				state[id]["progress"][i] += 1.0
				changed = true
		if changed:
			quest_updated.emit(id)
			_check_ready(id)


## harvest objectives: target an item id, "ore" (copper / iron), "herb" (glowcap / sunpetal) or "any".
func _on_harvest(item: String, n: int) -> void:
	var groups := []
	if item in ["copper_ore", "iron_ore"]:
		groups.append("ore")
	if item in ["glowcap", "sunpetal"]:
		groups.append("herb")
	_advance("harvest", item, float(n), false, groups)


## craft objectives: target a recipe id, "station:<id>" (anything at that station), "weapon" (any
## weapon recipe), "pouch" (any pouch) or "any".
func _on_crafted(rid: String) -> void:
	var r := Catalog.recipe(rid)
	var alt := ["station:" + str(r.get("station", ""))]
	if r.has("weapon"):
		alt.append("weapon")
	var o := Catalog.recipe_output(rid)
	if not o.is_empty() and Catalog.is_pouch(str(o["id"])):
		alt.append("pouch")
	_advance("craft", rid, 1.0, false, alt)


## Objectives that track a current value: pouches equipped, Artisan rank, talent points spent,
## player level and schematics learned.
func _refresh_absolute() -> void:
	_advance("pouches", "", float(Game.pouch_count()), true)
	_advance("artisan", "", float(Game.artisan_rank()), true)
	_advance("talent", "", float(Game.talent_points_spent()), true)
	_advance("level", "", float(Game.level), true)
	_advance("learn", "", float(Game.schematics.size()), true)


## open_chest objectives: target "any" counts every chest, "vault" only Ley Vaults.
func _on_chest(_chest_id: String, vault: bool) -> void:
	_advance("open_chest", "vault" if vault else "chest", 1.0)


## "equip" objectives complete while that weapon base sits in a hotbar weapon slot.
func _refresh_equip() -> void:
	for i in Game.WEAPON_SLOTS:
		var w := Game.loadout_weapon(i)
		if not w.is_empty():
			_advance("equip", str(w["base"]), 1.0, true)


func _on_built(_c: Node, tags: Array) -> void:
	for t in tags:
		_advance("build", str(t), 1.0)


func _on_altitude(_c: Node, alt: float) -> void:
	_advance("altitude", "", alt, true)


func _on_challenge(cid: String, result: Dictionary) -> void:
	_advance("challenge", cid, float(result.get("medal", 0)), true)


func _refresh_collect() -> void:
	for id in state.keys():
		if state[id]["status"] not in ["active", "ready"]:
			continue
		var objs: Array = def(id)["objectives"]
		var changed := false
		for i in objs.size():
			var o: Dictionary = objs[i]
			if o["type"] != "collect":
				continue
			var have := float(mini(Game.item_count(o["target"]), int(o["count"])))
			if not is_equal_approx(have, float(state[id]["progress"][i])):
				state[id]["progress"][i] = have
				changed = true
		if changed:
			if state[id]["status"] == "ready" and not _all_done(id):
				state[id]["status"] = "active"
			quest_updated.emit(id)
			_check_ready(id)


func _all_done(id: String) -> bool:
	var objs: Array = def(id)["objectives"]
	for i in objs.size():
		if not objective_done(id, i):
			return false
	return true


func _check_ready(id: String) -> void:
	if state[id]["status"] != "active":
		return
	if _all_done(id):
		state[id]["status"] = "ready"
		quest_ready.emit(id)
		var who: String = QuestDB.NPC_NAMES.get(def(id).get("turn_in", ""), "the quest giver")
		Events.toast("%s: objectives complete! Return to %s." % [def(id)["title"], who], "quest")


# ---------------------------------------------------------------- save / load
func to_dict() -> Dictionary:
	return {"state": state, "tracked": tracked}


func from_dict(d: Dictionary) -> void:
	state = {}
	var s: Dictionary = d.get("state", {})
	for id in s:
		if not QuestDB.QUESTS.has(id):
			continue
		var e: Dictionary = s[id]
		var prog := []
		for v in e.get("progress", []):
			prog.append(float(v))
		while prog.size() < def(id)["objectives"].size():
			prog.append(0.0)
		state[id] = {"status": str(e.get("status", "active")), "progress": prog, "times": int(e.get("times", 0))}
	tracked = str(d.get("tracked", ""))
	tracked_changed.emit(tracked)
