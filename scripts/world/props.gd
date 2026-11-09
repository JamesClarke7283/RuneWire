class_name Props
## Places environment models (with toon materials, night lights) and falls back to simple
## placeholder blocks with collision when a model has not been exported yet.

# Footprints from art/ASSET_SPEC.md in Godot axes (x width, y height, z depth).
const FALLBACK := {
	"bld_house_a": Vector3(6, 8, 5), "bld_house_b": Vector3(5, 9, 5), "bld_workshop": Vector3(12, 10, 10),
	"bld_magic_shop": Vector3(7, 14, 7), "bld_tinker_shop": Vector3(8, 6, 6), "bld_watchtower": Vector3(5, 16, 5),
	"bld_arena_wall": Vector3(8, 8, 2.5), "bld_arena_gate": Vector3(8, 8, 2.5), "bld_factory_shed": Vector3(20, 9, 14),
	"prop_smokestack": Vector3(3, 20, 3), "prop_tank": Vector3(4, 6, 4), "prop_pipes": Vector3(6, 3, 2),
	"prop_scrap_pile": Vector3(4, 1.8, 4), "prop_conveyor": Vector3(8, 1.2, 1.5), "ruin_pillar": Vector3(1.2, 5, 1.2),
	"ruin_arch": Vector3(6, 6, 1.2), "ruin_wall": Vector3(6, 3, 1), "ruin_altar": Vector3(6, 1.2, 6),
	"ley_stone": Vector3(1.2, 3.5, 0.8), "prop_fountain": Vector3(6, 4, 6), "prop_street_lamp": Vector3(0.6, 4, 0.6),
	"prop_market_stall": Vector3(3, 3, 2), "prop_quest_board": Vector3(2.5, 2.6, 0.6), "prop_signpost": Vector3(1, 3, 1),
	"prop_fence": Vector3(2, 1.1, 0.2), "prop_bench": Vector3(2, 0.9, 0.6), "prop_well": Vector3(2, 3, 2),
	"prop_crate_stack": Vector3(2, 2, 2), "prop_barrels": Vector3(2, 1.2, 2), "prop_cart": Vector3(3, 1.6, 1.6),
	"prop_bridge": Vector3(12, 2, 4), "prop_banner": Vector3(1, 5, 0.2), "prop_race_ring": Vector3(9, 9, 1),
	"prop_target": Vector3(1.6, 2.2, 0.4), "prop_beacon": Vector3(2, 3, 2), "prop_goal_pad": Vector3(8, 0.3, 8),
	"prop_challenge_terminal": Vector3(1.2, 1.6, 1.2),
	"tree_oak": Vector3(5, 8, 5), "tree_oak_small": Vector3(3.5, 5, 3.5), "tree_pine": Vector3(4, 9, 4),
	"tree_crystal": Vector3(4, 6, 4), "tree_dead": Vector3(3, 6, 3), "bush_round": Vector3(1.4, 1.2, 1.4),
	"bush_flower": Vector3(1.4, 1.2, 1.4), "rock_a": Vector3(1.5, 1.2, 1.5), "rock_b": Vector3(2.2, 1.6, 2),
	"rock_c": Vector3(2.5, 2.0, 2.4), "cliff_a": Vector3(10, 8, 6), "log_fallen": Vector3(4, 0.8, 0.8), "stump": Vector3(1, 0.7, 1),
}

const FALLBACK_COLORS := {
	"bld_": Color("d8c7a0"), "prop_": Color("b0875a"), "ruin_": Color("a8a397"), "ley_": Color("7ec8c0"),
	"tree_": Color("5fae3e"), "bush_": Color("5fae3e"), "rock_": Color("8c877d"), "cliff_": Color("8c877d"),
	"log_": Color("6a4a35"), "stump": Color("6a4a35"),
}

static var _scene_cache: Dictionary = {}


static func model_path(model: String, category: String = "") -> String:
	if category == "":
		category = category_for(model)
	return "res://assets/models/%s/%s.glb" % [category, model]


static func category_for(model: String) -> String:
	if model.begins_with("tree_") or model.begins_with("bush_") or model.begins_with("rock_") or model.begins_with("cliff_") \
			or model in ["grass_clump", "flower_patch", "mushroom_cluster", "log_fallen", "stump"]:
		return "nature"
	if model.begins_with("item_"):
		return "items"
	if model.begins_with("enemy_"):
		return "enemies"
	if model.begins_with("npc_"):
		return "npcs"
	if model.begins_with("part_"):
		return "parts"
	if model.begins_with("vm_"):
		return "weapons"
	return "env"


static func exists(model: String) -> bool:
	return ResourceLoader.exists(model_path(model))


static func instance(model: String) -> Node3D:
	var path := model_path(model)
	if ResourceLoader.exists(path):
		var ps: PackedScene = _scene_cache.get(path)
		if ps == null:
			ps = load(path)
			_scene_cache[path] = ps
		var n := ps.instantiate() as Node3D
		MaterialLib.apply(n)
		n.name = model
		return n
	return fallback(model)


## Place a model on the ground at (x, z) (y from terrain unless `y` given).
static func place(parent: Node, model: String, pos: Vector3, yaw_deg: float = 0.0, scl: float = 1.0, with_lights: bool = true) -> Node3D:
	var n := instance(model)
	n.position = pos
	n.rotation.y = deg_to_rad(yaw_deg)
	if not is_equal_approx(scl, 1.0):
		n.scale = Vector3.ONE * scl
	parent.add_child(n)
	if with_lights:
		add_lights(n)
	return n


static func add_lights(n: Node3D, color: Color = Color(1.0, 0.78, 0.45), energy: float = 1.6, light_range: float = 9.0) -> void:
	for lp in n.find_children("LightPoint*", "", true, false):
		var l := NightLight.new()
		l.light_color = color
		l.light_energy = energy
		l.omni_range = light_range
		lp.add_child(l)


static func fallback(model: String) -> Node3D:
	var size: Vector3 = FALLBACK.get(model, Vector3(1.5, 1.5, 1.5))
	var root := Node3D.new()
	root.name = model
	var mi := MeshInstance3D.new()
	var col := Color("c0b090")
	for prefix in FALLBACK_COLORS:
		if model.begins_with(prefix):
			col = FALLBACK_COLORS[prefix]
	if model.begins_with("tree_") or model.begins_with("bush_"):
		var sm := SphereMesh.new()
		sm.radius = size.x * 0.5
		sm.height = size.y * 0.65
		mi.mesh = sm
		mi.position.y = size.y * 0.62
		var trunk := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.25
		cm.bottom_radius = 0.35
		cm.height = size.y * 0.5
		trunk.mesh = cm
		trunk.position.y = size.y * 0.25
		trunk.material_override = MaterialLib.get_named("M_Bark")
		root.add_child(trunk)
		mi.material_override = MaterialLib.get_named("M_Leaves")
	else:
		var bm := BoxMesh.new()
		bm.size = size
		mi.mesh = bm
		mi.position.y = size.y * 0.5
		mi.material_override = MaterialLib.get_flat(col)
	root.add_child(mi)
	if not (model.begins_with("bush_") or model in ["prop_race_ring", "prop_beacon", "prop_goal_pad"]):
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = size if not model.begins_with("tree_") else Vector3(0.7, size.y, 0.7)
		cs.shape = bs
		cs.position.y = size.y * 0.5
		body.add_child(cs)
		root.add_child(body)
	return root
