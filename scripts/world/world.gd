class_name World
extends Node3D
## Builds and owns the valley: environment, terrain, water, points of interest, vegetation,
## grass, NPCs, enemy spawners, challenges and the build manager.

signal build_progress(step: String, fraction: float)
signal built

var terrain: Terrain
var env_rig: EnvironmentRig
var build_manager: BuildManager
var vfx_root: Node3D
var props_root: Node3D
var enemies_root: Node3D
var npcs_root: Node3D
var vegetation: Vegetation
var grass: GrassField
var pois: PoiBuilder
var is_built: bool = false


func _ready() -> void:
	add_to_group("world")


func build() -> void:
	var t0 := Time.get_ticks_msec()
	build_progress.emit("Painting the sky", 0.05)
	await get_tree().process_frame
	env_rig = EnvironmentRig.new()
	env_rig.name = "Environment"
	add_child(env_rig)
	build_progress.emit("Shaping the valley", 0.12)
	await get_tree().process_frame
	terrain = Terrain.new()
	terrain.name = "Terrain"
	add_child(terrain)
	terrain.build()
	print("World: terrain %d ms" % (Time.get_ticks_msec() - t0))
	var water := Water.new()
	water.name = "Lake"
	add_child(water)
	water.setup(WorldLayout.LAKE["pos"], float(WorldLayout.LAKE["radius"]) * 2.6)
	vfx_root = Node3D.new()
	vfx_root.name = "VFX"
	vfx_root.add_to_group("vfx_root")
	add_child(vfx_root)
	props_root = Node3D.new()
	props_root.name = "Props"
	add_child(props_root)
	enemies_root = Node3D.new()
	enemies_root.name = "Enemies"
	add_child(enemies_root)
	npcs_root = Node3D.new()
	npcs_root.name = "NPCs"
	add_child(npcs_root)
	build_manager = BuildManager.new()
	build_manager.name = "Builds"
	add_child(build_manager)
	build_progress.emit("Raising Emberwick", 0.35)
	await get_tree().process_frame
	pois = PoiBuilder.new()
	pois.name = "POIs"
	add_child(pois)
	pois.build(self)
	print("World: pois %d ms" % (Time.get_ticks_msec() - t0))
	build_progress.emit("Planting trees", 0.65)
	await get_tree().process_frame
	vegetation = Vegetation.new()
	vegetation.name = "Vegetation"
	add_child(vegetation)
	vegetation.build(self)
	grass = GrassField.new()
	grass.name = "Grass"
	add_child(grass)
	grass.setup(self)
	print("World: vegetation %d ms" % (Time.get_ticks_msec() - t0))
	build_progress.emit("Waking the locals", 0.9)
	await get_tree().process_frame
	is_built = true
	built.emit()
	print("World: built in %d ms" % (Time.get_ticks_msec() - t0))


func ground_y(x: float, z: float) -> float:
	return terrain.height_at(x, z)


func ground_point(x: float, z: float, lift: float = 0.0) -> Vector3:
	return Vector3(x, terrain.height_at(x, z) + lift, z)


func spawn_point() -> Vector3:
	var p := WorldLayout.TOWN_SPAWN
	return Vector3(p.x, terrain.height_at(p.x, p.z) + 0.3, p.z)


func on_game_started() -> void:
	build_manager.restore()
	pois.on_game_started()
