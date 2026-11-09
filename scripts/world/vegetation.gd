class_name Vegetation
extends Node3D
## Deterministic scatter of trees, rocks, bushes, flowers and mushrooms using chunked MultiMeshes
## (with visibility ranges) plus static trunk/rock collision.

const CHUNK := 80.0
const TYPES := {
	# model: {vis: visibility range, col: collision {type, r/size}, shadow}
	"tree_oak": {"vis": 300.0, "col": "trunk", "r": 0.55, "shadow": true},
	"tree_oak_small": {"vis": 260.0, "col": "trunk", "r": 0.4, "shadow": true},
	"tree_pine": {"vis": 320.0, "col": "trunk", "r": 0.5, "shadow": true},
	"tree_crystal": {"vis": 260.0, "col": "trunk", "r": 0.45, "shadow": true},
	"tree_dead": {"vis": 240.0, "col": "trunk", "r": 0.4, "shadow": true},
	# collision fits the models: spheres for the boulders, a box for the cliff butte, a capsule along the log
	"rock_a": {"vis": 200.0, "col": "rock", "r": 0.8, "shadow": false},
	"rock_b": {"vis": 220.0, "col": "rock", "r": 1.2, "shadow": true},
	"rock_c": {"vis": 240.0, "col": "rock", "r": 1.35, "shadow": true},
	"cliff_a": {"vis": 420.0, "col": "box", "size": Vector3(9.0, 7.5, 5.0), "off": Vector3(0, 3.5, 0), "shadow": true},
	"bush_round": {"vis": 120.0, "col": "", "shadow": false},
	"bush_flower": {"vis": 110.0, "col": "", "shadow": false},
	"flower_patch": {"vis": 60.0, "col": "", "shadow": false},
	"mushroom_cluster": {"vis": 70.0, "col": "", "shadow": false},
	"log_fallen": {"vis": 140.0, "col": "capsule", "r": 0.45, "h": 4.1, "off": Vector3(0, 0.42, 0), "shadow": true},
	"stump": {"vis": 110.0, "col": "rock", "r": 0.45, "shadow": false},
}

var world: World
var instances: Dictionary = {}   # model -> Array[Transform3D]
var _rng := RandomNumberGenerator.new()
var _bodies: Dictionary = {}     # chunk key -> StaticBody3D
var _keep_clear: Array = []       # Vector3(x, z, radius) spots with no trees


func build(w: World) -> void:
	world = w
	_rng.seed = 90210
	# keep trees and rocks off the treasure chests and crystal clusters (placed earlier by the POIs,
	# snapped to flat ground, so use their real positions)
	_keep_clear = []
	for n in get_tree().get_nodes_in_group("chests") + get_tree().get_nodes_in_group("harvest_nodes"):
		var p3: Vector3 = (n as Node3D).global_position
		if p3.y > w.ground_y(p3.x, p3.z) + 4.0:
			continue  # sky islands
		_keep_clear.append(Vector3(p3.x, p3.z, 5.0 if n is TreasureChest else 4.0))
	var pier: Vector2 = WorldLayout.LAKE_PIER["pos"]
	_keep_clear.append(Vector3(pier.x, pier.y, float(WorldLayout.LAKE_PIER["clear"])))
	for k in TYPES:
		instances[k] = []
	_scatter()
	for model in instances:
		if (instances[model] as Array).is_empty():
			continue
		_emit_model(model, instances[model])


func _blocked(x: float, z: float, margin: float = 4.0) -> bool:
	var p := Vector2(x, z)
	for k in WorldLayout.POIS:
		var poi: Dictionary = WorldLayout.POIS[k]
		if p.distance_to(poi["pos"]) < float(poi["radius"]) + margin:
			return true
	var t := world.terrain
	var s: Color = t.splat_at(x, z)
	if s.r > 0.25 or s.a > 0.2:
		return true
	if t.height_at(x, z) < 0.9:
		return true
	if Terrain._dist_to_segment(p, WorldLayout.GORGE["a"], WorldLayout.GORGE["b"]) < float(WorldLayout.GORGE["width"]) + 3.0:
		return true
	for ring in WorldLayout.RACE_RINGS:
		if p.distance_to(Vector2(ring.x, ring.y)) < 7.0:   # (x, z, height)
			return true
	for k in _keep_clear:
		if p.distance_to(Vector2(k.x, k.y)) < k.z:
			return true
	return false


func _try_add(model: String, x: float, z: float, scale_min: float = 0.85, scale_max: float = 1.2, max_slope: float = 0.3, sink: float = 0.15) -> bool:
	if _blocked(x, z):
		return false
	var t := world.terrain
	if t.slope_at(x, z) > max_slope:
		return false
	var y := t.height_at(x, z) - sink
	var s := _rng.randf_range(scale_min, scale_max)
	var b := Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3.ONE * s)
	if model.begins_with("rock_") or model == "cliff_a":
		b = Basis.from_euler(Vector3(_rng.randf_range(-0.2, 0.2), _rng.randf() * TAU, _rng.randf_range(-0.2, 0.2))).scaled(Vector3.ONE * s)
	(instances[model] as Array).append(Transform3D(b, Vector3(x, y, z)))
	return true


func _scatter() -> void:
	var woods: Vector2 = WorldLayout.WOODS["pos"]
	var woods_r: float = WorldLayout.WOODS["radius"]
	var shrine: Vector2 = WorldLayout.POIS["shrine"]["pos"]
	# Whispering Woods: dense oaks and pines, crystal trees towards the shrine
	for i in 520:
		var a := _rng.randf() * TAU
		var r := sqrt(_rng.randf()) * woods_r
		var x := woods.x + cos(a) * r
		var z := woods.y + sin(a) * r
		var near_shrine := Vector2(x, z).distance_to(shrine) < 95.0
		var roll := _rng.randf()
		var model := "tree_oak" if roll < 0.45 else ("tree_pine" if roll < 0.78 else "tree_oak_small")
		if near_shrine and _rng.randf() < 0.35:
			model = "tree_crystal"
		_try_add(model, x, z)
	for i in 120:
		var a2 := _rng.randf() * TAU
		var r2 := sqrt(_rng.randf()) * woods_r * 0.9
		var x2 := woods.x + cos(a2) * r2
		var z2 := woods.y + sin(a2) * r2
		var roll2 := _rng.randf()
		_try_add("mushroom_cluster" if roll2 < 0.5 else ("bush_round" if roll2 < 0.8 else "log_fallen"), x2, z2, 0.8, 1.3, 0.4)
	# shrine surroundings: dead and crystal trees
	for i in 90:
		var a3 := _rng.randf() * TAU
		var r3 := _rng.randf_range(50.0, 95.0)
		_try_add("tree_dead" if _rng.randf() < 0.6 else "tree_crystal", shrine.x + cos(a3) * r3, shrine.y + sin(a3) * r3)
	# northern pine forest on the foothills
	for i in 420:
		var x4 := _rng.randf_range(-260.0, 260.0)
		var z4 := _rng.randf_range(-290.0, -150.0)
		if Vector2(x4, z4).length() > 300.0:
			continue
		_try_add("tree_pine", x4, z4, 0.9, 1.35, 0.45)
	# pines around the rim everywhere (scenery)
	for i in 520:
		var a5 := _rng.randf() * TAU
		var r5 := _rng.randf_range(225.0, 305.0)
		_try_add("tree_pine", cos(a5) * r5, sin(a5) * r5, 0.9, 1.5, 0.55, 0.3)
	# meadows: scattered oaks, bushes, flowers and stumps
	for i in 700:
		var x6 := _rng.randf_range(-230.0, 230.0)
		var z6 := _rng.randf_range(-200.0, 230.0)
		if Vector2(x6, z6).distance_to(woods) < woods_r:
			continue
		var roll6 := _rng.randf()
		var model6 := "flower_patch"
		if roll6 < 0.12:
			model6 = "tree_oak"
		elif roll6 < 0.2:
			model6 = "tree_oak_small"
		elif roll6 < 0.38:
			model6 = "bush_round"
		elif roll6 < 0.5:
			model6 = "bush_flower"
		elif roll6 < 0.53:
			model6 = "stump"
		_try_add(model6, x6, z6, 0.8, 1.25, 0.35)
	# rocks everywhere, bigger on the slopes
	for i in 340:
		var x7 := _rng.randf_range(-290.0, 290.0)
		var z7 := _rng.randf_range(-290.0, 290.0)
		if Vector2(x7, z7).length() > 305.0:
			continue
		var roll7 := _rng.randf()
		var model7 := "rock_a" if roll7 < 0.45 else ("rock_b" if roll7 < 0.8 else "rock_c")
		_try_add(model7, x7, z7, 0.7, 1.6, 0.8, 0.35)
	# cliffs along the rim
	for i in 60:
		var a8 := _rng.randf() * TAU
		var r8 := _rng.randf_range(240.0, 300.0)
		_try_add("cliff_a", cos(a8) * r8, sin(a8) * r8, 1.0, 2.2, 1.0, 1.5)


func _emit_model(model: String, xforms: Array) -> void:
	var cfg: Dictionary = TYPES[model]
	# Placeholder boxes look bad at cliff/rock scale: wait for the real models instead.
	if (model == "cliff_a" or model.begins_with("rock_") or model in ["log_fallen", "stump"]) and not ResourceLoader.exists(Props.model_path(model, "nature")):
		return
	var parts := _mesh_parts(model)
	# group instances by chunk
	var chunks := {}
	for xf in xforms:
		var o: Vector3 = (xf as Transform3D).origin
		var key := Vector2i(int(floor(o.x / CHUNK)), int(floor(o.z / CHUNK)))
		if not chunks.has(key):
			chunks[key] = []
		chunks[key].append(xf)
	for key in chunks:
		var list: Array = chunks[key]
		for mp in parts:
			var mmi := MultiMeshInstance3D.new()
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mp["mesh"]
			mm.instance_count = list.size()
			var local: Transform3D = mp["xform"]
			for i in list.size():
				mm.set_instance_transform(i, (list[i] as Transform3D) * local)
			mmi.multimesh = mm
			mmi.visibility_range_end = float(cfg["vis"])
			mmi.visibility_range_end_margin = 20.0
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cfg["shadow"] else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mmi)
		if cfg["col"] != "":
			_add_collision(key, list, cfg)


func _add_collision(key: Vector2i, list: Array, cfg: Dictionary) -> void:
	var body: StaticBody3D = _bodies.get(key)
	if body == null:
		body = StaticBody3D.new()
		body.name = "VegCol_%d_%d" % [key.x, key.y]
		body.collision_layer = 1
		body.collision_mask = 0
		add_child(body)
		_bodies[key] = body
	for xf in list:
		var t: Transform3D = xf
		if Vector2(t.origin.x, t.origin.z).length() > WorldLayout.PLAY_RADIUS + 10.0:
			continue
		var s := t.basis.get_scale().x
		var cs := CollisionShape3D.new()
		if cfg["col"] == "trunk":
			var cyl := CylinderShape3D.new()
			cyl.radius = float(cfg["r"]) * s
			cyl.height = 5.0 * s
			cs.shape = cyl
			cs.position = t.origin + Vector3.UP * 2.5 * s
		elif cfg["col"] == "box" or cfg["col"] == "capsule":
			# oriented with the instance (yaw and tilt); sized by its scale
			var rot := t.basis.orthonormalized()
			if cfg["col"] == "box":
				var bx := BoxShape3D.new()
				bx.size = (cfg["size"] as Vector3) * s
				cs.shape = bx
			else:
				var cap := CapsuleShape3D.new()
				cap.radius = float(cfg["r"]) * s
				cap.height = float(cfg["h"]) * s
				cs.shape = cap
				rot = rot * Basis(Vector3.FORWARD, PI / 2.0)   # the capsule's long axis along the log (local X)
			cs.transform = Transform3D(rot, t.origin + t.basis * (cfg["off"] as Vector3))
		else:
			var sph := SphereShape3D.new()
			sph.radius = float(cfg["r"]) * s
			cs.shape = sph
			cs.position = t.origin + Vector3.UP * float(cfg["r"]) * s * 0.4
		body.add_child(cs)


## Extract the meshes of a nature model (with toon materials baked into the surfaces).
func _mesh_parts(model: String) -> Array:
	var out := []
	var path := Props.model_path(model, "nature")
	if ResourceLoader.exists(path):
		var scene: Node3D = (load(path) as PackedScene).instantiate()
		MaterialLib.apply(scene)
		for mi in scene.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			if m.mesh == null or String(m.name).contains("-col"):
				continue
			var mesh := m.mesh.duplicate() as Mesh
			for i in mesh.get_surface_count():
				var mat := m.get_surface_override_material(i)
				if mat:
					mesh.surface_set_material(i, mat)
			var xf := Transform3D()
			var n: Node = m
			while n and n != scene:
				xf = (n as Node3D).transform * xf
				n = n.get_parent()
			out.append({"mesh": mesh, "xform": xf})
		scene.free()
	if out.is_empty():
		out = _fallback_parts(model)
	return out


func _fallback_parts(model: String) -> Array:
	var out := []
	var size: Vector3 = Props.FALLBACK.get(model, Vector3(1, 1, 1))
	if model.begins_with("tree_"):
		var trunk := CylinderMesh.new()
		trunk.top_radius = 0.25
		trunk.bottom_radius = 0.4
		trunk.height = size.y * 0.55
		trunk.radial_segments = 8
		trunk.material = MaterialLib.get_named("M_Bark")
		out.append({"mesh": trunk, "xform": Transform3D(Basis(), Vector3(0, size.y * 0.27, 0))})
		var canopy: PrimitiveMesh
		if model == "tree_pine":
			var c := CylinderMesh.new()
			c.top_radius = 0.0
			c.bottom_radius = size.x * 0.5
			c.height = size.y * 0.75
			c.radial_segments = 10
			canopy = c
		else:
			var sm := SphereMesh.new()
			sm.radius = size.x * 0.5
			sm.height = size.y * 0.6
			sm.radial_segments = 12
			sm.rings = 8
			canopy = sm
		var leaf := "M_Leaves__3f8a4a" if model == "tree_pine" else ("M_Crystal" if model == "tree_crystal" else "M_Leaves")
		canopy.material = MaterialLib.get_named(leaf)
		if model != "tree_dead":
			out.append({"mesh": canopy, "xform": Transform3D(Basis(), Vector3(0, size.y * (0.55 if model == "tree_pine" else 0.68), 0))})
	elif model.begins_with("bush_") or model in ["flower_patch", "mushroom_cluster"]:
		var sm2 := SphereMesh.new()
		sm2.radius = size.x * 0.5 if model.begins_with("bush_") else 0.25
		sm2.height = sm2.radius * 1.5
		sm2.radial_segments = 10
		sm2.rings = 6
		sm2.material = MaterialLib.get_named("M_Leaves") if model.begins_with("bush_") else MaterialLib.get_flat(Color("ff7ad9") if model == "flower_patch" else Color("d9c7a0"))
		out.append({"mesh": sm2, "xform": Transform3D(Basis(), Vector3(0, sm2.radius * 0.6, 0))})
	else:
		var bm := BoxMesh.new()
		bm.size = size
		bm.material = MaterialLib.get_named("M_StoneRough") if not model in ["log_fallen", "stump"] else MaterialLib.get_named("M_Bark")
		out.append({"mesh": bm, "xform": Transform3D(Basis(), Vector3(0, size.y * 0.45, 0))})
	return out
