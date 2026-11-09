class_name CraftingStation
extends Node3D
## A crafting station in Emberwick (see Catalog.STATIONS): the Artificer's Workbench, the Emberwick
## Forge, the Alchemist's Table, the Enchanter's Altar or the Tailor's Loom. Press E to open its
## crafting screen. Attach it as a child of the station prop; it adds its own interaction collider and
## a light (at the prop's "LightPoint" if it has one), and bobs the altar's floating "Crystal".

var station: String = "workbench"
var _light: OmniLight3D
var _crystal: Node3D
var _crystal_y: float = 0.0
var _t: float = 0.0
var _ready_count: int = 0
var _count_t: float = 0.0


func _ready() -> void:
	add_to_group("stations")
	if station == "workbench":
		add_to_group("workbench")
	var d: Dictionary = Catalog.STATIONS.get(station, Catalog.STATIONS["workbench"])
	var size: Vector3 = d.get("size", Vector3(2.0, 1.2, 1.2))
	var body := StaticBody3D.new()
	body.collision_layer = 32
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	cs.position = Vector3(0, size.y * 0.5, 0)
	body.add_child(cs)
	add_child(body)
	_light = OmniLight3D.new()
	_light.light_color = d.get("light", Color(1.0, 0.8, 0.45))
	_light.light_energy = 1.2
	_light.omni_range = 5.0
	_light.distance_fade_enabled = true
	_light.distance_fade_begin = 60.0
	_light.distance_fade_length = 15.0
	add_child(_light)
	var parent := get_parent() as Node3D
	var lp := parent.find_child("LightPoint", true, false) as Node3D if parent else null
	if lp:
		_light.global_position = lp.global_position
	else:
		_light.position = Vector3(0, size.y + 0.8, 0.4)
	if parent:
		_crystal = parent.find_child("Crystal", true, false) as Node3D
		if _crystal:
			_crystal_y = _crystal.position.y


func get_interact_text() -> String:
	var d: Dictionary = Catalog.STATIONS.get(station, {})
	var extra := ""
	if _ready_count > 0:
		extra = "  ·  %d recipe%s ready" % [_ready_count, "" if _ready_count == 1 else "s"]
	return "[E] Use the %s%s\n%s" % [d.get("name", "station"), extra, d.get("desc", "")]


func interact(_player: Player) -> void:
	var ui := get_tree().get_first_node_in_group("game_ui")
	if ui:
		ui.open_station(station)


## Recipes here that could be crafted right now (refreshed twice a second while someone looks).
func ready_count() -> int:
	var n := 0
	for rid in Catalog.recipes_for(station):
		if Game.can_craft(rid, station):
			n += 1
	return n


func _process(delta: float) -> void:
	_t += delta
	_count_t -= delta
	if _count_t <= 0.0:
		_count_t = 0.5
		var p := get_tree().get_first_node_in_group("player") as Node3D
		if p and p.global_position.distance_to(global_position) < 8.0:
			_ready_count = ready_count()
	match station:
		"forge":
			_light.light_energy = 1.6 + sin(_t * 9.0) * 0.18 + sin(_t * 23.0) * 0.1
		"altar":
			_light.light_energy = 1.2 + sin(_t * 1.6) * 0.25
		_:
			_light.light_energy = 1.1 + sin(_t * 3.1) * 0.08 + sin(_t * 7.3) * 0.05
	if _crystal:
		_crystal.position.y = _crystal_y + sin(_t * 1.4) * 0.08
		_crystal.rotate_y(delta * 0.7)
