extends Node
## Player progression and economy: gold, XP and levels (cap 30) with talents, owned parts, the pack
## (weapon instances, consumables, materials, pouches, key items) and its capacity (base slots plus
## five pouch slots), the hotbar loadout (two weapon slots + four quick-item slots), crafting at the
## stations (Artisan rank, schematics), weapon upgrades / enchanting / salvage, selling, vendor stock,
## treasure found and lifetime stats.

signal gold_changed(gold: int, delta: int)
signal xp_changed(xp: int, level: int)
signal leveled_up(level: int)
signal milestone_reached(level: int, rewards: Array)
signal inventory_changed
signal equipment_changed      # loadout or weapon stats changed (player refreshes its handlers)
signal loadout_changed        # weapon slots or quick slots changed
signal upgrades_changed
signal pouches_changed
signal talents_changed
signal artisan_changed(xp: int, rank: int)
signal schematic_learned(recipe_id: String)
## Something did not fit in the pack: kind "item" (payload {id, count}) or "weapon" (payload instance).
## The player drops it at their feet so nothing is ever lost.
signal pack_overflow(kind: String, payload: Variant)
signal area_discovered(area_id: String)        # a named region entered for the first time
signal waypoint_attuned(waypoint_id: String)   # a ley stone touched: it becomes a fast-travel point

const START_GOLD := 120
const BASE_PART_LIMIT := 40
const BASE_PACK := 24
const WEAPON_SLOTS := 2
const QUICK_SLOTS := 4
const POUCH_SLOTS := 5
const STARTER_POUCH := "pouch_cloth"
const SAVE_VERSION := 3

var gold: int = START_GOLD
var xp: int = 0
var level: int = 1
var parts: Dictionary = {}
var items: Dictionary = {}          # consumables, materials, pouches and key items: id -> count
var weapons: Array = []             # weapon instances (see Catalog.make_weapon)
var loadout: Array = [0, 0]         # weapon uid per hotbar weapon slot (0 = empty)
var quick: Array = ["", "", "", ""] # consumable id per quick slot (hotbar 5-8)
var pouches: Array = ["", "", "", "", ""]   # equipped pouch id per pouch slot
var next_uid: int = 1
var upgrades: Dictionary = {}
var unlocked_parts: Dictionary = {}
var opened_chests: Dictionary = {}  # chest id -> true
var shop_stock: Dictionary = {}     # vendor -> {"day": int, "items": [weapon instances]}
var talents: Dictionary = {}        # talent id -> rank
var artisan_xp: int = 0
var schematics: Dictionary = {}     # learned schematic recipe id -> true
var milestones: Dictionary = {}     # milestone level -> true (cache claimed)
var tracked_recipe: String = ""     # crafting goal shown by the objective tracker
var discovered: Dictionary = {}     # WorldLayout.AREAS id -> true (named on the map)
var waypoints: Dictionary = {}      # WorldLayout.WAYPOINTS id -> true (fast travel unlocked)
var stats: Dictionary = {}
var time_of_day: float = 0.32
var day: int = 0
var player_health: float = -1.0
var player_mana: float = -1.0
var player_transform: Transform3D = Transform3D()
var has_player_transform: bool = false
var started: bool = false
var difficulty: float = 1.0


func _ready() -> void:
	reset()
	Events.location_reached.connect(func(loc: String): attune_waypoint(loc))


func reset() -> void:
	gold = START_GOLD
	xp = 0
	level = 1
	parts = {"crate": 4, "plank": 6}
	items = {"health_tonic": 2, "mana_draught": 1, "spark_bomb": 2}
	weapons = []
	loadout = [0, 0]
	quick = Catalog.DEFAULT_QUICK.duplicate()
	pouches = [STARTER_POUCH, "", "", "", ""]
	next_uid = 1
	for base in Catalog.STARTER_WEAPONS:
		var w := Catalog.make_weapon(base, 0)
		w["new"] = false
		add_weapon(w, false)
	upgrades = {}
	unlocked_parts = {}
	opened_chests = {}
	shop_stock = {}
	talents = {}
	artisan_xp = 0
	schematics = {}
	milestones = {}
	tracked_recipe = ""
	discovered = {"town": true}
	waypoints = {"town": true}
	stats = {"kills": 0, "kills_magic": 0, "kills_tech": 0, "gold_earned": 0, "gold_spent": 0,
		"parts_spawned": 0, "welds": 0, "quests_done": 0, "deaths": 0, "playtime": 0.0, "bosses": 0,
		"elites": 0, "chests": 0, "vaults": 0, "harvested": 0, "scavenged": 0, "mined": 0, "gathered": 0,
		"crafted": 0, "upgraded": 0, "salvaged": 0, "enchanted": 0, "sold": 0, "best_drop": 0,
		"discovered": 0, "travels": 0}
	time_of_day = 0.32
	day = 0
	player_health = -1.0
	player_mana = -1.0
	has_player_transform = false
	started = false


func _process(delta: float) -> void:
	if started and not get_tree().paused:
		stats["playtime"] = float(stats.get("playtime", 0.0)) + delta


# ---------------------------------------------------------------- gold
func add_gold(amount: int, reason: String = "") -> void:
	if amount == 0:
		return
	gold += amount
	if amount > 0:
		stats["gold_earned"] = int(stats.get("gold_earned", 0)) + amount
	gold_changed.emit(gold, amount)
	if amount > 0 and reason != "":
		Events.toast("+%d gold  ·  %s" % [amount, reason], "gold")


func can_afford(amount: int) -> bool:
	return gold >= amount


func spend_gold(amount: int) -> bool:
	if amount < 0 or gold < amount:
		return false
	gold -= amount
	stats["gold_spent"] = int(stats.get("gold_spent", 0)) + amount
	gold_changed.emit(gold, -amount)
	return true


# ---------------------------------------------------------------- xp, levels & milestones
func xp_to_next(lvl: int = -1) -> int:
	if lvl < 0:
		lvl = level
	return int(round(90.0 * pow(float(lvl), 1.42)))


func is_max_level() -> bool:
	return level >= Catalog.MAX_LEVEL


func add_xp(amount: int) -> void:
	if amount <= 0 or is_max_level():
		return
	xp += amount
	var gained := false
	while not is_max_level() and xp >= xp_to_next():
		xp -= xp_to_next()
		level += 1
		gained = true
		leveled_up.emit(level)
		Events.toast("Level up! You are now level %d  ·  +1 talent point [K]" % level, "levelup")
		if level in Catalog.LEVEL_MILESTONES:
			_milestone(level)
	if is_max_level():
		xp = 0
	xp_changed.emit(xp, level)
	if gained:
		equipment_changed.emit()


## Every five levels: a cache of gold, a Rare+ weapon and an unknown schematic.
func _milestone(lvl: int) -> void:
	if milestones.has(lvl):
		return
	milestones[lvl] = true
	var rewards := []
	var g := 60 * lvl
	add_gold(g)
	rewards.append("%d gold" % g)
	var w := Catalog.roll_weapon(1.2 + lvl * 0.05, 2, "", "", Catalog.drop_level(lvl))
	give_weapon(w)
	rewards.append(Catalog.weapon_name(w))
	var sch := random_unknown_schematic()
	if sch != "":
		learn_schematic(sch, false)
		rewards.append("Schematic: " + Catalog.recipe_name(sch))
	Events.toast("Level %d milestone cache: %s" % [lvl, ", ".join(rewards)], "quest_done")
	milestone_reached.emit(lvl, rewards)


# ---------------------------------------------------------------- talents
func talent_rank(id: String) -> int:
	return int(talents.get(id, 0))


func talent_points_total() -> int:
	return level - 1


func talent_points_spent() -> int:
	var n := 0
	for t in talents:
		n += int(talents[t])
	return n


func talent_points() -> int:
	return maxi(0, talent_points_total() - talent_points_spent())


func can_learn_talent(id: String) -> bool:
	var t: Dictionary = Catalog.TALENTS.get(id, {})
	return not t.is_empty() and talent_points() > 0 and talent_rank(id) < int(t["ranks"]) and level >= int(t["level"])


func learn_talent(id: String) -> bool:
	if not can_learn_talent(id):
		return false
	talents[id] = talent_rank(id) + 1
	talents_changed.emit()
	equipment_changed.emit()
	inventory_changed.emit()
	Events.talent_learned.emit(id, talent_rank(id))
	return true


func respec_cost() -> int:
	return 50 * level


## Refund every talent point for gold (not while Deep Pockets is holding pack slots you are using).
func reset_talents() -> bool:
	if talents.is_empty():
		return false
	if pack_used() > pack_capacity() - 2 * talent_rank("deep_pockets"):
		Events.toast("Make room in your pack first: Deep Pockets is holding %d slots" % (2 * talent_rank("deep_pockets")), "warn")
		return false
	if not spend_gold(respec_cost()):
		return false
	talents = {}
	talents_changed.emit()
	equipment_changed.emit()
	inventory_changed.emit()
	return true


# ---------------------------------------------------------------- derived stats
func upgrade_tier(id: String) -> int:
	return int(upgrades.get(id, 0))


func max_health() -> float:
	return 100.0 + (level - 1) * 10.0 + upgrade_tier("vitality") * 30.0 + talent_rank("toughness") * 15.0


func max_mana() -> float:
	return 100.0 + (level - 1) * 8.0 + talent_rank("mana_well") * 20.0


func mana_regen() -> float:
	return 9.0 * (1.0 + 0.5 * upgrade_tier("mana_regen") + 0.15 * talent_rank("flow"))


## Damage multiplier for a weapon school from upgrades, level and talents (buffs are the player's).
func school_mult(school: String) -> float:
	if school == "magic":
		return 1.0 + 0.15 * upgrade_tier("arcana") + 0.03 * (level - 1) + 0.06 * talent_rank("spellweaver")
	return 1.0 + 0.15 * upgrade_tier("engineering") + 0.03 * (level - 1) + 0.06 * talent_rank("gunsmith")


func spell_damage_mult() -> float:
	return school_mult("magic")


func weapon_damage_mult() -> float:
	return school_mult("tech")


func reload_mult() -> float:
	return 1.0 - 0.1 * talent_rank("quick_hands")


func move_mult() -> float:
	return 1.0 + 0.04 * talent_rank("fleet_foot")


func status_mult() -> float:
	return 1.0 + 0.15 * talent_rank("elementalist")


func siphon() -> float:
	return 0.02 * talent_rank("siphon")


func gold_mult() -> float:
	return 1.0 + 0.1 * talent_rank("treasure_hunter")


func loot_luck() -> float:
	return 0.15 * talent_rank("treasure_hunter")


func forage_chance() -> float:
	return 0.3 * talent_rank("forager")


func scrap_chance() -> float:
	return 0.25 * talent_rank("scrapper")


func regen_mult() -> float:
	return 1.0 + 0.5 * talent_rank("second_wind")


func part_limit() -> int:
	return BASE_PART_LIMIT + 15 * upgrade_tier("capacity")


# ---------------------------------------------------------------- the pack & pouches
func pack_capacity() -> int:
	var n := BASE_PACK + 2 * talent_rank("deep_pockets")
	for p in pouches:
		if p != "":
			n += int(Catalog.pouch_def(p).get("slots", 0))
	return n


func has_pouch_perk(perk: String) -> bool:
	for p in pouches:
		if p != "" and str(Catalog.pouch_def(p).get("perk", "")) == perk:
			return true
	return false


func pouch_count() -> int:
	var n := 0
	for p in pouches:
		if p != "":
			n += 1
	return n


func item_stack_size(id: String) -> int:
	var s := Catalog.stack_size(id)
	if Catalog.is_consumable(id) and has_pouch_perk("alchemist"):
		s *= 2
	return maxi(s, 1)


## Pack slots `n` of an item fill.
func slots_for(id: String, n: int) -> int:
	if n <= 0 or not Catalog.takes_space(id):
		return 0
	return int(ceil(float(n) / float(item_stack_size(id))))


func _used_with(item_counts: Dictionary, weapon_count: int) -> int:
	var n := weapon_count
	for id in item_counts:
		n += slots_for(str(id), int(item_counts[id]))
	return n


func pack_weapons() -> int:
	var n := 0
	for w in weapons:
		if equipped_slot(int(w["uid"])) < 0:
			n += 1
	return n


func pack_used() -> int:
	return _used_with(items, pack_weapons())


func pack_free() -> int:
	return pack_capacity() - pack_used()


## Pack slots in use after adding `add` and removing `remove` (item counts) and `weapon_delta` weapons.
func pack_used_after(add: Dictionary, remove: Dictionary = {}, weapon_delta: int = 0) -> int:
	var c := items.duplicate()
	for id in remove:
		c[id] = maxi(0, int(c.get(id, 0)) - int(remove[id]))
	for id in add:
		c[id] = int(c.get(id, 0)) + int(add[id])
	return _used_with(c, pack_weapons() + weapon_delta)


## How many of `n` items of `id` still fit in the pack.
func room_for(id: String, n: int = 1) -> int:
	if not Catalog.takes_space(id) or Catalog.is_schematic(id):
		return n
	var have := item_count(id)
	var stack := item_stack_size(id)
	var free := maxi(pack_free(), 0)
	var max_total := (slots_for(id, have) + free) * stack
	return clampi(max_total - have, 0, n)


## The pack has no free slot (weapons need one unless a hotbar weapon slot is empty).
func inventory_full() -> bool:
	return pack_free() <= 0


func has_weapon_room() -> bool:
	return pack_free() > 0 or int(loadout[0]) == 0 or int(loadout[1]) == 0


## Legacy name: the pack's size.
func weapon_cap() -> int:
	return pack_capacity()


## Put a pouch from the pack into pouch slot 0-4 (-1: the first empty one). A pouch already in that
## slot swaps back into the pack, if everything still fits.
func equip_pouch(id: String, slot: int = -1) -> bool:
	if not Catalog.is_pouch(id) or item_count(id) <= 0:
		return false
	if slot < 0:
		slot = pouches.find("")
		if slot < 0:
			Events.toast("All five pouch slots are full. Drag a pouch onto one to swap it.", "warn")
			return false
	if slot >= POUCH_SLOTS:
		return false
	var old: String = pouches[slot]
	if old != "":
		var cap_after := pack_capacity() - int(Catalog.pouch_def(old)["slots"]) + int(Catalog.pouch_def(id)["slots"])
		if pack_used_after({old: 1}, {id: 1}) > cap_after:
			Events.toast("Not enough room to swap pouches. Make some space first.", "warn")
			return false
	items[id] = item_count(id) - 1
	if int(items[id]) <= 0:
		items.erase(id)
	if old != "":
		items[old] = item_count(old) + 1
	pouches[slot] = id
	pouches_changed.emit()
	inventory_changed.emit()
	Events.pouch_equipped.emit(id)
	return true


## Take the pouch out of a pouch slot (it goes back into the pack, which must still hold everything).
func unequip_pouch(slot: int) -> bool:
	if slot < 0 or slot >= POUCH_SLOTS or str(pouches[slot]) == "":
		return false
	var p: String = pouches[slot]
	var cap_after := pack_capacity() - int(Catalog.pouch_def(p)["slots"])
	if pack_used_after({p: 1}) > cap_after:
		Events.toast("Your pack would overflow without that pouch. Make room first.", "warn")
		return false
	pouches[slot] = ""
	items[p] = item_count(p) + 1
	pouches_changed.emit()
	inventory_changed.emit()
	return true


func swap_pouch_slots(a: int, b: int) -> void:
	if a < 0 or b < 0 or a >= POUCH_SLOTS or b >= POUCH_SLOTS or a == b:
		return
	var t = pouches[a]
	pouches[a] = pouches[b]
	pouches[b] = t
	pouches_changed.emit()
	inventory_changed.emit()


# ---------------------------------------------------------------- parts
func is_part_unlocked(id: String) -> bool:
	var p := Catalog.part(id)
	if p.is_empty():
		return false
	if not p.has("unlock"):
		return true
	return unlocked_parts.has(id)


func unlock_part(id: String, announce: bool = true) -> void:
	if unlocked_parts.has(id):
		return
	unlocked_parts[id] = true
	inventory_changed.emit()
	if announce:
		Events.toast("New blueprint: %s" % Catalog.display_name(id), "unlock")


func part_count(id: String) -> int:
	return int(parts.get(id, 0))


func add_parts(id: String, n: int = 1) -> void:
	parts[id] = part_count(id) + n
	inventory_changed.emit()


func take_part(id: String) -> bool:
	if part_count(id) <= 0:
		return false
	parts[id] = part_count(id) - 1
	inventory_changed.emit()
	return true


func buy_part(id: String, n: int = 1) -> bool:
	var p := Catalog.part(id)
	if p.is_empty() or not is_part_unlocked(id):
		return false
	var cost: int = int(p["price"]) * n
	if not spend_gold(cost):
		return false
	add_parts(id, n)
	Events.part_purchased.emit(id, n)
	return true


# ---------------------------------------------------------------- weapons (inventory)
func get_weapon(uid: int) -> Dictionary:
	if uid <= 0:
		return {}
	for w in weapons:
		if int(w["uid"]) == uid:
			return w
	return {}


func has_weapon_base(base: String) -> bool:
	for w in weapons:
		if w["base"] == base:
			return true
	return false


func weapon_count(base: String) -> int:
	var n := 0
	for w in weapons:
		if w["base"] == base:
			n += 1
	return n


## Adds a weapon instance (gives it a uid). Fills an empty weapon slot automatically (which needs no
## pack space). Returns the uid, or 0 when there is no room.
func add_weapon(w: Dictionary, announce: bool = true) -> int:
	var empty_slot := -1
	for i in WEAPON_SLOTS:
		if int(loadout[i]) == 0:
			empty_slot = i
			break
	if empty_slot < 0 and inventory_full():
		if announce:
			Events.toast("Pack full! Sell, salvage or stash things, or equip bigger pouches (%d/%d)" % [pack_used(), pack_capacity()], "warn")
		return 0
	var inst := w.duplicate(true)
	inst["uid"] = next_uid
	next_uid += 1
	weapons.append(inst)
	var uid: int = inst["uid"]
	if empty_slot >= 0:
		loadout[empty_slot] = uid
		loadout_changed.emit()
		equipment_changed.emit()
	stats["best_drop"] = maxi(int(stats.get("best_drop", 0)), int(inst["rarity"]))
	inventory_changed.emit()
	if announce:
		var r := int(inst["rarity"])
		var head: String = "New weapon" if r < 2 else "★ %s weapon" % Catalog.RARITY_NAMES[r]
		Events.toast("%s: %s  [I]" % [head, Catalog.weapon_name(inst)], "rarity_%d" % r)
	Events.weapon_acquired.emit(inst)
	return uid


## add_weapon, but a weapon that does not fit is dropped at the player's feet instead of lost.
func give_weapon(w: Dictionary, announce: bool = true) -> int:
	var uid := add_weapon(w, announce)
	if uid == 0:
		pack_overflow.emit("weapon", w)
	return uid


func remove_weapon(uid: int) -> bool:
	for i in weapons.size():
		if int(weapons[i]["uid"]) == uid:
			weapons.remove_at(i)
			var was_equipped := false
			for s in WEAPON_SLOTS:
				if int(loadout[s]) == uid:
					loadout[s] = 0
					was_equipped = true
			if was_equipped:
				loadout_changed.emit()
				equipment_changed.emit()
			inventory_changed.emit()
			return true
	return false


func loadout_weapon(slot: int) -> Dictionary:
	if slot < 0 or slot >= WEAPON_SLOTS:
		return {}
	return get_weapon(int(loadout[slot]))


func equipped_slot(uid: int) -> int:
	for s in WEAPON_SLOTS:
		if int(loadout[s]) == uid and uid > 0:
			return s
	return -1


## Put a weapon in hotbar weapon slot 0 or 1. If it already sits in the other slot, the two swap; a
## weapon already in the target slot goes back into the pack.
func equip_weapon(uid: int, slot: int) -> bool:
	if slot < 0 or slot >= WEAPON_SLOTS or get_weapon(uid).is_empty():
		return false
	var other := equipped_slot(uid)
	if other == slot:
		return true
	if other >= 0:
		loadout[other] = loadout[slot]
	loadout[slot] = uid
	get_weapon(uid)["new"] = false
	loadout_changed.emit()
	equipment_changed.emit()
	inventory_changed.emit()
	Events.loadout_changed.emit()
	return true


## Empties a weapon slot; the weapon goes into the pack (which needs a free slot).
func unequip_slot(slot: int) -> bool:
	if slot < 0 or slot >= WEAPON_SLOTS or int(loadout[slot]) == 0:
		return false
	if pack_free() <= 0:
		Events.toast("No room in your pack for that weapon. Make space first.", "warn")
		return false
	loadout[slot] = 0
	loadout_changed.emit()
	equipment_changed.emit()
	inventory_changed.emit()
	Events.loadout_changed.emit()
	return true


func swap_weapon_slots() -> void:
	var a = loadout[0]
	loadout[0] = loadout[1]
	loadout[1] = a
	loadout_changed.emit()
	equipment_changed.emit()
	Events.loadout_changed.emit()


func toggle_favorite(uid: int) -> void:
	var w := get_weapon(uid)
	if not w.is_empty():
		w["fav"] = not bool(w.get("fav", false))
		inventory_changed.emit()


func mark_seen(uid: int) -> void:
	var w := get_weapon(uid)
	if not w.is_empty() and bool(w.get("new", false)):
		w["new"] = false
		inventory_changed.emit()


# ---------------------------------------------------------------- legacy equipment API (tools + weapon bases)
func has_equipment(id: String) -> bool:
	return Catalog.TOOLS.has(id) or has_weapon_base(id)


## Grants a Common copy of a weapon base unless one is already owned (quests, dev tools, old saves).
func unlock_equipment(id: String) -> void:
	if Catalog.TOOLS.has(id) or not Catalog.WEAPONS.has(id) or has_weapon_base(id):
		return
	give_weapon(Catalog.make_weapon(id, 0), false)


func buy_equipment(id: String) -> bool:
	return buy_weapon(id)


## Buys a Common copy of a weapon base at its list price.
func buy_weapon(base: String) -> bool:
	var e := Catalog.weapon_base(base)
	if e.is_empty():
		return false
	if not has_weapon_room():
		Events.toast("Pack full!", "warn")
		return false
	if not spend_gold(int(e["price"])):
		return false
	add_weapon(Catalog.make_weapon(base, 0), false)
	Events.item_purchased.emit(base)
	Events.toast("Bought %s!" % e["name"], "unlock")
	return true


# ---------------------------------------------------------------- vendor stock
## Featured (rolled Uncommon+) weapons a vendor sells today. kind: "gun" (tech) or "spell" (magic).
func featured_stock(vendor: String, kind: String) -> Array:
	var s: Dictionary = shop_stock.get(vendor, {})
	if s.is_empty() or int(s.get("day", -1)) != day:
		var list := []
		var school := "school:magic" if kind == "spell" else "school:tech"
		for i in 3:
			var w := Catalog.roll_weapon(0.6 + 0.08 * level, 1, "", school, 1 + level / 6)
			w["new"] = false
			list.append(w)
		s = {"day": day, "items": list}
		shop_stock[vendor] = s
	return s["items"]


func featured_price(w: Dictionary) -> int:
	return Catalog.weapon_value(w) * 3


func buy_featured(vendor: String, index: int) -> bool:
	var s: Dictionary = shop_stock.get(vendor, {})
	var list: Array = s.get("items", [])
	if index < 0 or index >= list.size():
		return false
	if not has_weapon_room():
		Events.toast("Pack full!", "warn")
		return false
	var w: Dictionary = list[index]
	if not spend_gold(featured_price(w)):
		return false
	list.remove_at(index)
	add_weapon(w, true)
	Events.item_purchased.emit(str(w["base"]))
	return true


## Buys n of a material, pouch, consumable or schematic at its vendor price.
func buy_item(id: String, n: int = 1) -> bool:
	if n <= 0:
		return false
	if Catalog.is_schematic(id):
		var rid := Catalog.schematic_recipe(id)
		if knows_recipe(rid) or not spend_gold(Catalog.buy_price(id)):
			return false
		learn_schematic(rid)
		Events.item_purchased.emit(id)
		return true
	if room_for(id, n) < n:
		Events.toast("Not enough room in your pack!", "warn")
		return false
	if not spend_gold(Catalog.buy_price(id) * n):
		return false
	add_item(id, n)
	Events.item_purchased.emit(id)
	return true


func sell_weapon(uid: int) -> bool:
	var w := get_weapon(uid)
	if w.is_empty() or bool(w.get("fav", false)) or equipped_slot(uid) >= 0:
		return false
	var v := Catalog.weapon_value(w)
	remove_weapon(uid)
	add_gold(v)
	add_stat("sold")
	Events.item_sold.emit(str(w["base"]), v)
	return true


func sell_item(id: String, n: int = 1) -> bool:
	if item_count(id) < n or n <= 0:
		return false
	var v := Catalog.stack_value(id) * n
	remove_item(id, n)
	add_gold(v)
	add_stat("sold", n)
	Events.item_sold.emit(id, v)
	return true


# ---------------------------------------------------------------- consumables, materials & key items
func item_count(id: String) -> int:
	return int(items.get(id, 0))


## Adds up to n of an item - as many as fit in the pack - and returns how many were added. Schematics
## are learned on the spot instead.
func add_item(id: String, n: int = 1) -> int:
	if n <= 0:
		return 0
	if Catalog.is_schematic(id):
		learn_schematic(Catalog.schematic_recipe(id))
		return n
	var fit := room_for(id, n)
	if fit <= 0:
		return 0
	items[id] = item_count(id) + fit
	inventory_changed.emit()
	Events.item_collected.emit(id, fit)
	return fit


## add_item, but whatever does not fit is dropped at the player's feet instead of lost.
func give_item(id: String, n: int = 1) -> int:
	var got := add_item(id, n)
	if got < n:
		pack_overflow.emit("item", {"id": id, "count": n - got})
		Events.toast("Pack full: %d %s dropped at your feet" % [n - got, Catalog.display_name(id)], "warn")
	return got


func remove_item(id: String, n: int = 1) -> bool:
	if item_count(id) < n:
		return false
	items[id] = item_count(id) - n
	if items[id] <= 0:
		items.erase(id)
	inventory_changed.emit()
	return true


func has_items(cost: Dictionary) -> bool:
	for id in cost:
		if item_count(id) < int(cost[id]):
			return false
	return true


func take_items(cost: Dictionary) -> bool:
	if not has_items(cost):
		return false
	for id in cost:
		items[id] = item_count(id) - int(cost[id])
		if items[id] <= 0:
			items.erase(id)
	inventory_changed.emit()
	return true


func buy_consumable(id: String, n: int = 1) -> bool:
	var c: Dictionary = Catalog.CONSUMABLES.get(id, {})
	if c.is_empty():
		return false
	if room_for(id, n) < n:
		Events.toast("Not enough room in your pack!", "warn")
		return false
	if not spend_gold(int(c["price"]) * n):
		return false
	items[id] = item_count(id) + n
	inventory_changed.emit()
	Events.item_purchased.emit(id)
	return true


## Assign a consumable to quick slot 0-3 (hotbar keys 5-8). "" clears it. A consumable already in
## another quick slot moves (the two slots swap).
func set_quick(slot: int, id: String) -> void:
	if slot < 0 or slot >= QUICK_SLOTS:
		return
	if id != "" and not Catalog.is_consumable(id):
		return
	var other := quick.find(id) if id != "" else -1
	if other >= 0 and other != slot:
		quick[other] = quick[slot]
	quick[slot] = id
	loadout_changed.emit()


# ---------------------------------------------------------------- crafting: Artisan rank & schematics
func artisan_rank() -> int:
	return Catalog.artisan_rank_for(artisan_xp)


func artisan_progress() -> Vector2i:
	var r := artisan_rank()
	if r >= Catalog.ARTISAN_XP.size():
		return Vector2i(1, 1)
	var lo := int(Catalog.ARTISAN_XP[r - 1])
	var hi := int(Catalog.ARTISAN_XP[r])
	return Vector2i(artisan_xp - lo, hi - lo)


func add_artisan_xp(n: int) -> void:
	if n <= 0:
		return
	var before := artisan_rank()
	artisan_xp += int(round(n * (1.0 + 0.15 * talent_rank("master_artisan"))))
	var after := artisan_rank()
	if after > before:
		Events.toast("Artisan rank %d: %s! New recipes unlocked." % [after, Catalog.artisan_title(after)], "levelup")
	artisan_changed.emit(artisan_xp, after)


## Rarity luck for crafted weapons: grows with Artisan rank and the Master Artisan talent.
func craft_luck() -> float:
	return 0.8 + 0.12 * (artisan_rank() - 1) + 0.25 * talent_rank("master_artisan")


func knows_recipe(rid: String) -> bool:
	var r := Catalog.recipe(rid)
	return not r.is_empty() and (not bool(r.get("schematic", false)) or schematics.has(rid))


func learn_schematic(rid: String, announce: bool = true) -> bool:
	if not Catalog.RECIPES.has(rid) or schematics.has(rid):
		return false
	schematics[rid] = true
	schematic_learned.emit(rid)
	Events.schematic_learned.emit(rid)
	inventory_changed.emit()
	if announce:
		var r: Dictionary = Catalog.RECIPES[rid]
		Events.toast("Schematic learned: %s  ·  craft it at the %s" % [Catalog.recipe_name(rid), Catalog.STATIONS[r["station"]]["name"]], "unlock")
	return true


func random_unknown_schematic() -> String:
	var opts := []
	for rid in Catalog.schematic_recipes():
		if not schematics.has(rid):
			opts.append(rid)
	return opts[randi() % opts.size()] if not opts.is_empty() else ""


## Why a recipe can't be crafted right now ("" when it can). station "" skips the station check.
func craft_block(rid: String, station: String = "") -> String:
	var r := Catalog.recipe(rid)
	if r.is_empty():
		return "unknown"
	if not knows_recipe(rid):
		return "schematic"
	if station != "" and r["station"] != station and not (station == "field" and bool(r.get("field", false))):
		return "station"
	if artisan_rank() < int(r.get("rank", 1)):
		return "rank"
	if not has_items(r.get("cost", {})):
		return "materials"
	if gold < int(r.get("gold", 0)):
		return "gold"
	if r.has("weapon"):
		if not has_weapon_room() and pack_used_after({}, r.get("cost", {}), 1) > pack_capacity():
			return "room"
	elif pack_used_after(r.get("gives", {}), r.get("cost", {})) > pack_capacity():
		return "room"
	return ""


func can_craft(rid: String, station: String = "") -> bool:
	return craft_block(rid, station) == ""


## How many times in a row a recipe could be crafted (materials, gold and room permitting; max 99).
func craft_max(rid: String, station: String = "") -> int:
	if not can_craft(rid, station):
		return 0
	var r := Catalog.recipe(rid)
	var n := 99
	var cost: Dictionary = r.get("cost", {})
	for id in cost:
		n = mini(n, item_count(id) / maxi(int(cost[id]), 1))
	if int(r.get("gold", 0)) > 0:
		n = mini(n, gold / int(r["gold"]))
	if r.has("weapon"):
		n = mini(n, maxi(pack_free(), 1))
	else:
		while n > 1:
			var add := {}
			var rem := {}
			for id in r.get("gives", {}):
				add[id] = int(r["gives"][id]) * n
			for id in cost:
				rem[id] = int(cost[id]) * n
			if pack_used_after(add, rem) <= pack_capacity():
				break
			n -= 1
	return maxi(n, 1)


## Crafts a recipe. Returns what was made: {"items": {...}} or {"weapon": instance}, or {} on failure.
func craft(rid: String, station: String = "") -> Dictionary:
	if not can_craft(rid, station):
		return {}
	var r: Dictionary = Catalog.RECIPES[rid]
	if not spend_gold(int(r.get("gold", 0))):
		return {}
	take_items(r.get("cost", {}))
	var out := {}
	if r.has("weapon"):
		var lvl := 1 + (artisan_rank() - 1) / 3
		var w := Catalog.make_weapon(str(r["weapon"]), Catalog.roll_rarity(craft_luck(), 1), [], lvl)
		var uid := give_weapon(w, true)
		out["weapon"] = get_weapon(uid) if uid > 0 else w
	else:
		var gives: Dictionary = r.get("gives", {})
		for id in gives:
			give_item(id, int(gives[id]))
		out["items"] = gives
	add_stat("crafted")
	add_artisan_xp(Catalog.recipe_xp(rid))
	add_xp(Catalog.recipe_xp(rid) / 2)
	if tracked_recipe == rid and not has_items(r.get("cost", {})):
		tracked_recipe = ""
	Events.item_crafted.emit(rid)
	return out


func set_tracked_recipe(rid: String) -> void:
	tracked_recipe = rid if Catalog.RECIPES.has(rid) else ""
	inventory_changed.emit()


# ---------------------------------------------------------------- upgrade, salvage & enchant
## Why a weapon can't be upgraded ("" when it can).
func upgrade_block(uid: int) -> String:
	var w := get_weapon(uid)
	if w.is_empty():
		return "unknown"
	var cost := Catalog.upgrade_cost(w)
	if cost.is_empty():
		return "max"
	if artisan_rank() < int(cost.get("rank", 1)):
		return "rank"
	if not has_items(cost["items"]):
		return "materials"
	if gold < int(cost["gold"]):
		return "gold"
	return ""


func can_upgrade_weapon(uid: int) -> bool:
	return upgrade_block(uid) == ""


func upgrade_weapon(uid: int) -> bool:
	if not can_upgrade_weapon(uid):
		return false
	var w := get_weapon(uid)
	var cost := Catalog.upgrade_cost(w)
	spend_gold(int(cost["gold"]))
	take_items(cost["items"])
	w["level"] = int(w["level"]) + 1
	add_stat("upgraded")
	add_artisan_xp(10 + 4 * int(w["level"]))
	add_xp(8 + 3 * int(w["level"]))
	inventory_changed.emit()
	equipment_changed.emit()
	Events.weapon_upgraded.emit(uid, int(w["level"]))
	return true


func salvage_weapon(uid: int) -> Dictionary:
	var w := get_weapon(uid)
	if w.is_empty() or bool(w.get("fav", false)) or equipped_slot(uid) >= 0:
		return {}
	var got := Catalog.salvage_yield(w)
	if randf() < scrap_chance() and not got.is_empty():
		var k: String = got.keys()[randi() % got.size()]
		got[k] = int(got[k]) + 1
	remove_weapon(uid)
	for id in got:
		give_item(id, int(got[id]))
	add_stat("salvaged")
	add_artisan_xp(4)
	Events.weapon_salvaged.emit(str(w["base"]))
	return got


func _enchant_block(uid: int, cost: Dictionary) -> String:
	if get_weapon(uid).is_empty():
		return "unknown"
	if cost.is_empty():
		return "max"
	if artisan_rank() < int(cost.get("rank", 1)):
		return "rank"
	if not has_items(cost["items"]):
		return "materials"
	if gold < int(cost["gold"]):
		return "gold"
	return ""


func reroll_block(uid: int) -> String:
	return _enchant_block(uid, Catalog.reroll_cost(get_weapon(uid)))


func infuse_block(uid: int) -> String:
	return _enchant_block(uid, Catalog.infuse_cost(get_weapon(uid)))


## Enchanter's Altar: fresh perks for an Uncommon+ weapon (different ones where possible).
func reroll_perks(uid: int) -> bool:
	if reroll_block(uid) != "":
		return false
	var w := get_weapon(uid)
	var cost := Catalog.reroll_cost(w)
	spend_gold(int(cost["gold"]))
	take_items(cost["items"])
	var count := int(Catalog.RARITY_PERKS[int(w["rarity"])])
	var old: Array = w.get("perks", [])
	var fresh := Catalog.roll_perks(str(w["base"]), count, old)
	if fresh.size() < count:
		fresh = Catalog.roll_perks(str(w["base"]), count)
	w["perks"] = fresh
	_after_enchant(uid, 25)
	return true


## Enchanter's Altar: raise a weapon one rarity tier (up to Epic), adding a perk if the tier has more.
func infuse_weapon(uid: int) -> bool:
	if infuse_block(uid) != "":
		return false
	var w := get_weapon(uid)
	var cost := Catalog.infuse_cost(w)
	spend_gold(int(cost["gold"]))
	take_items(cost["items"])
	var r := int(w["rarity"]) + 1
	w["rarity"] = r
	var perks: Array = w.get("perks", [])
	var want := int(Catalog.RARITY_PERKS[r])
	if perks.size() < want:
		perks.append_array(Catalog.roll_perks(str(w["base"]), want - perks.size(), perks))
	w["perks"] = perks
	stats["best_drop"] = maxi(int(stats.get("best_drop", 0)), r)
	_after_enchant(uid, 40)
	return true


func _after_enchant(uid: int, art_xp: int) -> void:
	add_stat("enchanted")
	add_artisan_xp(art_xp)
	add_xp(art_xp / 2)
	inventory_changed.emit()
	equipment_changed.emit()
	Events.weapon_enchanted.emit(uid)


# ---------------------------------------------------------------- treasure
func is_chest_opened(id: String) -> bool:
	return opened_chests.has(id)


func mark_chest_opened(id: String, vault: bool) -> void:
	opened_chests[id] = true
	add_stat("chests")
	add_xp(120 if vault else 40)
	if vault:
		add_stat("vaults")


# ---------------------------------------------------------------- upgrades
func upgrade_price(id: String) -> int:
	var u: Dictionary = Catalog.UPGRADES.get(id, {})
	var tier := upgrade_tier(id)
	if u.is_empty() or tier >= u["prices"].size():
		return -1
	return int(u["prices"][tier])


func buy_upgrade(id: String) -> bool:
	var price := upgrade_price(id)
	if price < 0 or not spend_gold(price):
		return false
	upgrades[id] = upgrade_tier(id) + 1
	upgrades_changed.emit()
	equipment_changed.emit()
	inventory_changed.emit()
	Events.item_purchased.emit(id)
	Events.toast("%s upgraded to tier %d" % [Catalog.UPGRADES[id]["name"], upgrade_tier(id)], "unlock")
	return true


func add_stat(key: String, n: float = 1.0) -> void:
	stats[key] = float(stats.get(key, 0)) + n


# ---------------------------------------------------------------- exploration
## XP for naming a region on the map: more for the dangerous ones.
static func discovery_xp(area_id: String) -> int:
	var lv: Array = WorldLayout.AREAS.get(area_id, {}).get("levels", [0, 0])
	return 20 + 12 * int(lv[1])


## First visit to a named region: it gets its name on the map and pays some XP (none when `quiet`,
## e.g. the region the player loads in). Returns true when it was new.
func discover_area(area_id: String, quiet: bool = false) -> bool:
	if not WorldLayout.AREAS.has(area_id) or discovered.has(area_id):
		return false
	discovered[area_id] = true
	add_stat("discovered")
	if not quiet:
		add_xp(discovery_xp(area_id))
	area_discovered.emit(area_id)
	return true


## Touching a ley stone attunes it: from then on the map can send the player there.
func attune_waypoint(waypoint_id: String) -> bool:
	if not WorldLayout.WAYPOINTS.has(waypoint_id) or waypoints.has(waypoint_id):
		return false
	waypoints[waypoint_id] = true
	waypoint_attuned.emit(waypoint_id)
	Events.toast("%s attuned: travel here from the map [M]" % WorldLayout.WAYPOINTS[waypoint_id]["name"], "unlock")
	AudioManager.play_2d("enchant", -4.0, 1.15)
	return true


# ---------------------------------------------------------------- save / load
func to_dict() -> Dictionary:
	var t := player_transform
	return {
		"version": SAVE_VERSION,
		"gold": gold, "xp": xp, "level": level, "parts": parts, "items": items,
		"weapons": weapons, "loadout": loadout, "quick": quick, "pouches": pouches, "next_uid": next_uid,
		"upgrades": upgrades, "unlocked_parts": unlocked_parts.keys(), "opened_chests": opened_chests.keys(),
		"shop_stock": shop_stock, "talents": talents, "artisan_xp": artisan_xp, "schematics": schematics.keys(),
		"milestones": milestones.keys(), "tracked_recipe": tracked_recipe,
		"discovered": discovered.keys(), "waypoints": waypoints.keys(),
		"stats": stats, "time_of_day": time_of_day, "day": day,
		"player_health": player_health, "player_mana": player_mana,
		"player_pos": [t.origin.x, t.origin.y, t.origin.z], "player_yaw": t.basis.get_euler().y,
		"has_player_transform": has_player_transform,
	}


func from_dict(d: Dictionary) -> void:
	reset()
	gold = int(d.get("gold", START_GOLD))
	xp = int(d.get("xp", 0))
	level = clampi(int(d.get("level", 1)), 1, Catalog.MAX_LEVEL)
	parts = _int_dict(d.get("parts", {}))
	items = {}
	var raw_items := _int_dict(d.get("items", {}))
	for id in raw_items:
		if Catalog.is_schematic(id):
			schematics[Catalog.schematic_recipe(id)] = true
		elif Catalog.item_category(id) != "" and int(raw_items[id]) > 0:
			items[id] = int(raw_items[id])
	upgrades = _int_dict(d.get("upgrades", {}))
	unlocked_parts = {}
	for p in d.get("unlocked_parts", []):
		unlocked_parts[str(p)] = true
	opened_chests = {}
	for c in d.get("opened_chests", []):
		opened_chests[str(c)] = true
	if d.has("weapons"):
		weapons = []
		next_uid = 1
		for raw in d.get("weapons", []):
			var w := _clean_weapon(raw)
			if not w.is_empty():
				weapons.append(w)
				next_uid = maxi(next_uid, int(w["uid"]) + 1)
		next_uid = maxi(next_uid, int(d.get("next_uid", 1)))
		var lo: Array = d.get("loadout", [0, 0])
		loadout = [0, 0]
		for i in mini(lo.size(), WEAPON_SLOTS):
			var uid := int(lo[i])
			loadout[i] = uid if not get_weapon(uid).is_empty() else 0
		var qk: Array = d.get("quick", quick)
		quick = ["", "", "", ""]
		for i in mini(qk.size(), QUICK_SLOTS):
			quick[i] = str(qk[i]) if Catalog.is_consumable(str(qk[i])) else ""
	else:
		_migrate_v1(d)
	# pouches (saves before v3 had a "Bigger Satchel" upgrade instead: each tier becomes a pouch)
	pouches = ["", "", "", "", ""]
	if d.has("pouches"):
		var pp: Array = d.get("pouches", [])
		for i in mini(pp.size(), POUCH_SLOTS):
			pouches[i] = str(pp[i]) if Catalog.is_pouch(str(pp[i])) else ""
	else:
		pouches[0] = STARTER_POUCH
	if upgrades.has("satchel"):
		var tiers := int(upgrades["satchel"])
		upgrades.erase("satchel")
		for i in tiers:
			var slot := pouches.find("")
			if slot >= 0:
				pouches[slot] = "pouch_brass"
			else:
				items["pouch_brass"] = item_count("pouch_brass") + 1
	talents = {}
	var tl: Dictionary = d.get("talents", {})
	for id in tl:
		if Catalog.TALENTS.has(str(id)):
			talents[str(id)] = clampi(int(tl[id]), 0, int(Catalog.TALENTS[str(id)]["ranks"]))
	while talent_points_spent() > talent_points_total() and not talents.is_empty():
		talents.erase(talents.keys()[0])
	artisan_xp = maxi(0, int(d.get("artisan_xp", 0)))
	for rid in d.get("schematics", []):
		if Catalog.RECIPES.has(str(rid)):
			schematics[str(rid)] = true
	milestones = {}
	for m in d.get("milestones", []):
		milestones[int(m)] = true
	tracked_recipe = str(d.get("tracked_recipe", ""))
	if not Catalog.RECIPES.has(tracked_recipe):
		tracked_recipe = ""
	for a in d.get("discovered", []):
		if WorldLayout.AREAS.has(str(a)):
			discovered[str(a)] = true
	for w in d.get("waypoints", []):
		if WorldLayout.WAYPOINTS.has(str(w)):
			waypoints[str(w)] = true
	var ss: Dictionary = d.get("shop_stock", {})
	shop_stock = {}
	for v in ss:
		var list := []
		for raw in (ss[v] as Dictionary).get("items", []):
			var w2 := _clean_weapon(raw)
			if not w2.is_empty():
				list.append(w2)
		shop_stock[str(v)] = {"day": int((ss[v] as Dictionary).get("day", -1)), "items": list}
	stats.merge(d.get("stats", {}), true)
	time_of_day = float(d.get("time_of_day", 0.32))
	day = int(d.get("day", 0))
	player_health = float(d.get("player_health", -1.0))
	player_mana = float(d.get("player_mana", -1.0))
	var pp2: Array = d.get("player_pos", [0, 0, 0])
	has_player_transform = bool(d.get("has_player_transform", false))
	player_transform = Transform3D(Basis(Vector3.UP, float(d.get("player_yaw", 0.0))), Vector3(pp2[0], pp2[1], pp2[2]))
	gold_changed.emit(gold, 0)
	xp_changed.emit(xp, level)
	inventory_changed.emit()
	loadout_changed.emit()
	pouches_changed.emit()
	talents_changed.emit()
	artisan_changed.emit(artisan_xp, artisan_rank())
	equipment_changed.emit()
	upgrades_changed.emit()


## Saves from before the inventory: "equipment" listed owned tools/spells/weapons and "hotbar" the order.
func _migrate_v1(d: Dictionary) -> void:
	weapons = []
	loadout = [0, 0]
	next_uid = 1
	var order: Array = Array(d.get("hotbar", [])) + Array(d.get("equipment", []))
	for id in order:
		var base := str(id)
		if Catalog.WEAPONS.has(base) and not has_weapon_base(base):
			var w := Catalog.make_weapon(base, 0)
			w["new"] = false
			weapons.append(_with_uid(w))
	if weapons.is_empty():
		for base in Catalog.STARTER_WEAPONS:
			weapons.append(_with_uid(Catalog.make_weapon(base, 0)))
	for i in mini(weapons.size(), WEAPON_SLOTS):
		loadout[i] = int(weapons[i]["uid"])
	quick = Catalog.DEFAULT_QUICK.duplicate()


func _with_uid(w: Dictionary) -> Dictionary:
	w["uid"] = next_uid
	next_uid += 1
	return w


func _clean_weapon(raw: Variant) -> Dictionary:
	if typeof(raw) != TYPE_DICTIONARY:
		return {}
	var r: Dictionary = raw
	var base := str(r.get("base", ""))
	if not Catalog.WEAPONS.has(base):
		return {}
	var perks: Array = []
	for p in r.get("perks", []):
		if Catalog.PERKS.has(str(p)):
			perks.append(str(p))
	return {"uid": int(r.get("uid", 0)), "base": base, "rarity": clampi(int(r.get("rarity", 0)), 0, 4),
		"level": clampi(int(r.get("level", 1)), 1, Catalog.MAX_WEAPON_LEVEL), "perks": perks,
		"fav": bool(r.get("fav", false)), "new": bool(r.get("new", false))}


func _int_dict(src: Dictionary) -> Dictionary:
	var out := {}
	for k in src:
		out[str(k)] = int(src[k])
	return out
