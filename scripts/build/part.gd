class_name Part
extends Node3D
## One build part (crate, wheel, thruster...). Parts always live inside a Contraption (a compound
## rigid body); their collision shapes are registered on that body through shape owners.

signal destroyed(part: Part)

const SPECIAL := {
	"cargo": {"name": "Ley Crystal Cargo", "category": "special", "price": 0, "mass": 380.0, "hp": 99999.0,
		"shape": {"type": "box", "size": Vector3(1.2, 1.2, 1.2)}, "model": "res://assets/models/items/item_ley_cargo.glb",
		"material": "wood", "indestructible": true, "desc": "Fragile? No. Heavy? Extremely."},
	"haul_crate": {"name": "Gorge Haul Crate", "category": "special", "price": 0, "mass": 220.0, "hp": 99999.0,
		"shape": {"type": "box", "size": Vector3(1.4, 1.4, 1.4)}, "model": "res://assets/models/parts/part_crate.glb",
		"model_scale": 1.4, "material": "wood", "indestructible": true, "desc": "Get it across the gorge!"},
}

var part_id: String = ""
var def: Dictionary = {}
var hp: float = 100.0
var max_hp: float = 100.0
var contraption: Contraption = null
var owner_ids: Array[int] = []
var shapes: Array = []          # [{shape: Shape3D, xform: Transform3D}] in part space
var device: Device = null
var model: Node3D = null
var paint: Color = Color.WHITE
var special: bool = false
var indestructible: bool = false
var placed: bool = true         # counts towards the part limit


static func create(id: String) -> Part:
	var p := Part.new()
	p.part_id = id
	p.name = "Part_" + id
	if SPECIAL.has(id):
		p.def = SPECIAL[id]
		p.special = true
		p.placed = false
		p.indestructible = bool(p.def.get("indestructible", false))
	else:
		p.def = Catalog.part(id)
	p.max_hp = float(p.def.get("hp", 100.0))
	p.hp = p.max_hp
	p._build()
	return p


func _build() -> void:
	var path: String = def.get("model", Catalog.part_model_path(part_id))
	model = MaterialLib.instance_model(path)
	if model == null:
		model = _placeholder()
	elif def.has("model_scale"):
		model.scale = Vector3.ONE * float(def["model_scale"])
	model.name = "Model"
	add_child(model)
	_build_shapes()
	var dev: String = def.get("device", "")
	if dev != "":
		device = Device.create(dev)
		if device:
			device.part = self
			add_child(device)


func _build_shapes() -> void:
	var sd: Dictionary = def.get("shape", {"type": "box", "size": Vector3.ONE})
	var shape: Shape3D
	var xf := Transform3D()
	match sd.get("type", "box"):
		"cylinder":
			var cs := CylinderShape3D.new()
			cs.radius = float(sd["radius"])
			cs.height = float(sd["height"])
			shape = cs
			match sd.get("axis", "y"):
				"x":
					xf.basis = Basis(Vector3.FORWARD, PI / 2)
				"z":
					xf.basis = Basis(Vector3.RIGHT, PI / 2)
		_:
			var bs := BoxShape3D.new()
			bs.size = sd.get("size", Vector3.ONE)
			shape = bs
	if sd.has("offset"):
		xf.origin = sd["offset"]
	shapes = [{"shape": shape, "xform": xf}]


func _placeholder() -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var sd: Dictionary = def.get("shape", {"type": "box", "size": Vector3.ONE})
	if sd.get("type", "box") == "cylinder":
		var cm := CylinderMesh.new()
		cm.top_radius = float(sd["radius"])
		cm.bottom_radius = float(sd["radius"])
		cm.height = float(sd["height"])
		mi.mesh = cm
		match sd.get("axis", "y"):
			"x":
				mi.rotation = Vector3(0, 0, PI / 2)
			"z":
				mi.rotation = Vector3(PI / 2, 0, 0)
	else:
		var bm := BoxMesh.new()
		bm.size = sd.get("size", Vector3.ONE)
		mi.mesh = bm
	var lib := {"wood": "M_WoodPlanks", "metal": "M_Brass", "stone": "M_Stone", "glass": "M_Glass", "rubber": "M_Rubber", "leather": "M_Leather"}
	mi.material_override = MaterialLib.get_named(lib.get(def.get("material", "wood"), "M_WoodPlanks"))
	root.add_child(mi)
	match def.get("device", ""):
		"wheel":
			mi.name = "Wheel"
		"seat":
			var sp := Node3D.new()
			sp.name = "SitPoint"
			sp.position = Vector3(0, 0.1, 0)
			root.add_child(sp)
		"lamp":
			var lp := Node3D.new()
			lp.name = "LightPoint"
			root.add_child(lp)
	return root


func display_name() -> String:
	return str(def.get("name", part_id))


func part_mass() -> float:
	return float(def.get("mass", 20.0))


func half_extents() -> Vector3:
	var sd: Dictionary = def.get("shape", {"type": "box", "size": Vector3.ONE})
	if sd.get("type", "box") == "cylinder":
		var r := float(sd["radius"])
		var h := float(sd["height"]) * 0.5
		match sd.get("axis", "y"):
			"x":
				return Vector3(h, r, r)
			"z":
				return Vector3(r, r, h)
		return Vector3(r, h, r)
	return (sd.get("size", Vector3.ONE) as Vector3) * 0.5


func sit_transform() -> Transform3D:
	var sp := model.find_child("SitPoint", true, false) as Node3D if model else null
	if sp:
		return Transform3D(global_transform.basis.orthonormalized(), sp.global_position)
	return Transform3D(global_transform.basis.orthonormalized(), global_position + global_transform.basis.y * 0.15)


func apply_damage(info: DamageInfo) -> void:
	if indestructible or hp <= 0.0:
		return
	var amt := info.amount
	if info.from_player:
		amt *= 0.5
	var mat: String = def.get("material", "")
	if info.damage_type == "fire" and mat == "wood":
		amt *= 1.5
	if info.damage_type == "kinetic" and mat == "glass":
		amt *= 2.0
	hp -= amt
	MaterialLib.flash(model, 0.8)
	get_tree().create_timer(0.08).timeout.connect(func():
		if is_instance_valid(model):
			MaterialLib.flash(model, 0.0))
	if hp <= 0.0:
		destroy()


func destroy() -> void:
	if not is_inside_tree():
		return
	var pos := global_position
	var mat: String = def.get("material", "wood")
	var col := {"wood": Color(0.7, 0.5, 0.3), "metal": Color(0.8, 0.75, 0.6), "stone": Color(0.6, 0.6, 0.6), "glass": Color(0.7, 0.9, 1.0)}.get(mat, Color(0.7, 0.6, 0.5))
	VFX.burst(self, pos, col, 16, 6.0, 0.18, 0.7, -14.0, "puff", 180.0)
	VFX.burst(self, pos, Color(1, 0.85, 0.5), 10, 6.0, 0.12, 0.5, -12.0, "spark")
	AudioManager.play("impact_%s" % ("wood" if mat == "wood" else ("stone" if mat == "stone" else "metal")), pos, 2.0, 0.7)
	if device:
		device.on_destroyed()
	destroyed.emit(self)
	var bm := get_tree().get_first_node_in_group("build_manager") as BuildManager
	if bm:
		bm.on_part_destroyed(self)
	if contraption:
		contraption.remove_part(self, false)
	queue_free()


func set_paint(c: Color) -> void:
	paint = c
	MaterialLib.set_paint(model, c)


func to_dict(body: Contraption) -> Dictionary:
	var xf := body.global_transform.affine_inverse() * global_transform
	var d := {"id": part_id, "hp": hp, "x": _xf_to_arr(xf)}
	if paint != Color.WHITE:
		d["paint"] = paint.to_html()
	if device:
		d["dev"] = device.save_data()
	return d


static func _xf_to_arr(xf: Transform3D) -> Array:
	var q := xf.basis.get_rotation_quaternion()
	return [xf.origin.x, xf.origin.y, xf.origin.z, q.x, q.y, q.z, q.w]


static func arr_to_xf(a: Array) -> Transform3D:
	return Transform3D(Basis(Quaternion(a[3], a[4], a[5], a[6])), Vector3(a[0], a[1], a[2]))
