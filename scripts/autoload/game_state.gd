extends Node
## Player progression and economy: gold, XP/levels, owned parts, equipment, consumables,
## quest items, upgrades and lifetime stats.

signal gold_changed(gold: int, delta: int)
signal xp_changed(xp: int, level: int)
signal leveled_up(level: int)
signal inventory_changed
signal equipment_changed
signal upgrades_changed

const START_GOLD := 120
const BASE_PART_LIMIT := 40
const MAX_HOTBAR := 8

var gold: int = START_GOLD
var xp: int = 0
var level: int = 1
var parts: Dictionary = {}
var items: Dictionary = {}
var equipment: Array = []
var hotbar: Array = []
var upgrades: Dictionary = {}
var unlocked_parts: Dictionary = {}
var stats: Dictionary = {}
var time_of_day: float = 0.32
var player_health: float = -1.0
var player_mana: float = -1.0
var player_transform: Transform3D = Transform3D()
var has_player_transform: bool = false
var started: bool = false
var difficulty: float = 1.0


func _ready() -> void:
	reset()


func reset() -> void:
	gold = START_GOLD
	xp = 0
	level = 1
	parts = {"crate": 4, "plank": 6}
	items = {"health_tonic": 2, "mana_draught": 1}
	equipment = Catalog.STARTER_EQUIPMENT.duplicate()
	hotbar = equipment.duplicate()
	upgrades = {}
	unlocked_parts = {}
	stats = {"kills": 0, "kills_magic": 0, "kills_tech": 0, "gold_earned": 0, "gold_spent": 0,
		"parts_spawned": 0, "welds": 0, "quests_done": 0, "deaths": 0, "playtime": 0.0, "bosses": 0}
	time_of_day = 0.32
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


# ---------------------------------------------------------------- xp
func xp_to_next(lvl: int = -1) -> int:
	if lvl < 0:
		lvl = level
	return int(round(90.0 * pow(float(lvl), 1.42)))


func add_xp(amount: int) -> void:
	if amount <= 0:
		return
	xp += amount
	var gained := false
	while xp >= xp_to_next():
		xp -= xp_to_next()
		level += 1
		gained = true
		leveled_up.emit(level)
		Events.toast("Level up! You are now level %d" % level, "levelup")
	xp_changed.emit(xp, level)
	if gained:
		equipment_changed.emit()


# ---------------------------------------------------------------- derived stats
func upgrade_tier(id: String) -> int:
	return int(upgrades.get(id, 0))


func max_health() -> float:
	return 100.0 + (level - 1) * 10.0 + upgrade_tier("vitality") * 30.0


func max_mana() -> float:
	return 100.0 + (level - 1) * 8.0


func mana_regen() -> float:
	return 9.0 * (1.0 + 0.5 * upgrade_tier("mana_regen"))


func spell_damage_mult() -> float:
	return 1.0 + 0.15 * upgrade_tier("arcana") + 0.03 * (level - 1)


func weapon_damage_mult() -> float:
	return 1.0 + 0.15 * upgrade_tier("engineering") + 0.03 * (level - 1)


func part_limit() -> int:
	return BASE_PART_LIMIT + 15 * upgrade_tier("capacity")


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


# ---------------------------------------------------------------- equipment
func has_equipment(id: String) -> bool:
	return id in equipment


func unlock_equipment(id: String) -> void:
	if has_equipment(id):
		return
	equipment.append(id)
	if hotbar.size() < MAX_HOTBAR:
		hotbar.append(id)
	equipment_changed.emit()


func buy_equipment(id: String) -> bool:
	var e := Catalog.equipment(id)
	if e.is_empty() or has_equipment(id):
		return false
	if not spend_gold(int(e["price"])):
		return false
	unlock_equipment(id)
	Events.item_purchased.emit(id)
	Events.toast("Learned %s!" % e["name"], "unlock")
	return true


# ---------------------------------------------------------------- consumables & items
func item_count(id: String) -> int:
	return int(items.get(id, 0))


func add_item(id: String, n: int = 1) -> void:
	items[id] = item_count(id) + n
	inventory_changed.emit()
	Events.item_collected.emit(id, n)


func remove_item(id: String, n: int = 1) -> bool:
	if item_count(id) < n:
		return false
	items[id] = item_count(id) - n
	if items[id] <= 0:
		items.erase(id)
	inventory_changed.emit()
	return true


func buy_consumable(id: String, n: int = 1) -> bool:
	var c: Dictionary = Catalog.CONSUMABLES.get(id, {})
	if c.is_empty():
		return false
	if not spend_gold(int(c["price"]) * n):
		return false
	items[id] = item_count(id) + n
	inventory_changed.emit()
	Events.item_purchased.emit(id)
	return true


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
	Events.item_purchased.emit(id)
	Events.toast("%s upgraded to tier %d" % [Catalog.UPGRADES[id]["name"], upgrade_tier(id)], "unlock")
	return true


func add_stat(key: String, n: float = 1.0) -> void:
	stats[key] = float(stats.get(key, 0)) + n


# ---------------------------------------------------------------- save / load
func to_dict() -> Dictionary:
	var t := player_transform
	return {
		"gold": gold, "xp": xp, "level": level, "parts": parts, "items": items,
		"equipment": equipment, "hotbar": hotbar, "upgrades": upgrades,
		"unlocked_parts": unlocked_parts.keys(), "stats": stats, "time_of_day": time_of_day,
		"player_health": player_health, "player_mana": player_mana,
		"player_pos": [t.origin.x, t.origin.y, t.origin.z], "player_yaw": t.basis.get_euler().y,
		"has_player_transform": has_player_transform,
	}


func from_dict(d: Dictionary) -> void:
	reset()
	gold = int(d.get("gold", START_GOLD))
	xp = int(d.get("xp", 0))
	level = int(d.get("level", 1))
	parts = _int_dict(d.get("parts", {}))
	items = _int_dict(d.get("items", {}))
	equipment = Array(d.get("equipment", equipment))
	hotbar = Array(d.get("hotbar", equipment))
	upgrades = _int_dict(d.get("upgrades", {}))
	unlocked_parts = {}
	for p in d.get("unlocked_parts", []):
		unlocked_parts[str(p)] = true
	stats.merge(d.get("stats", {}), true)
	time_of_day = float(d.get("time_of_day", 0.32))
	player_health = float(d.get("player_health", -1.0))
	player_mana = float(d.get("player_mana", -1.0))
	var pp: Array = d.get("player_pos", [0, 0, 0])
	has_player_transform = bool(d.get("has_player_transform", false))
	player_transform = Transform3D(Basis(Vector3.UP, float(d.get("player_yaw", 0.0))), Vector3(pp[0], pp[1], pp[2]))
	gold_changed.emit(gold, 0)
	xp_changed.emit(xp, level)
	inventory_changed.emit()
	equipment_changed.emit()
	upgrades_changed.emit()


func _int_dict(src: Dictionary) -> Dictionary:
	var out := {}
	for k in src:
		out[str(k)] = int(src[k])
	return out
