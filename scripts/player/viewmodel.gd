class_name Viewmodel
extends Node3D
## First-person item presentation: loads the Blender viewmodel (or a procedural placeholder),
## and animates equip, sway, bob, recoil and casting.

const BASE_POS := Vector3(0.25, -0.24, -0.44)
const PLACEMENT := {
	"vm_gauntlet": {"pos": Vector3(0.24, -0.25, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_toolkit": {"pos": Vector3(0.24, -0.24, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_staff": {"pos": Vector3(0.25, -0.27, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_arc_pistol": {"pos": Vector3(0.22, -0.22, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_rivet_repeater": {"pos": Vector3(0.22, -0.24, -0.38), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_boom_mortar": {"pos": Vector3(0.24, -0.25, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
}

var holder: Node3D
var current: Node3D = null
var current_model: String = ""
var models: Dictionary = {}
var _sway := Vector2.ZERO
var _sway_target := Vector2.ZERO
var _kick: float = 0.0
var _kick_rot: float = 0.0
var _cast: float = 0.0
var _equip_t: float = 1.0
var _speed: float = 0.0
var _bob_t: float = 0.0
var _grounded: bool = true
var _tilt: float = 0.0


func _ready() -> void:
	holder = Node3D.new()
	holder.name = "Holder"
	add_child(holder)


func show_model(model_name: String, equip_id: String) -> void:
	if current:
		current.visible = false
	current_model = model_name
	if not models.has(model_name):
		var n: Node3D = null
		var path := "res://assets/models/weapons/%s.glb" % model_name
		if model_name != "" and ResourceLoader.exists(path):
			n = (load(path) as PackedScene).instantiate()
			MaterialLib.apply(n, "viewmodel")
		else:
			n = _placeholder(model_name, equip_id)
		var pl: Dictionary = PLACEMENT.get(model_name, {"pos": BASE_POS, "rot": Vector3(0, 180, 0), "scale": 1.0})
		n.rotation_degrees = pl["rot"]
		n.scale = Vector3.ONE * float(pl["scale"])
		n.set_meta("base_pos", pl["pos"])
		holder.add_child(n)
		models[model_name] = n
	current = models[model_name]
	current.visible = true
	current.position = current.get_meta("base_pos")
	_equip_t = 0.0


func set_motion(speed: float, grounded: bool, bob_t: float) -> void:
	_speed = speed
	_grounded = grounded
	_bob_t = bob_t


func add_sway(rel: Vector2) -> void:
	_sway_target += rel * 0.0009
	_sway_target = _sway_target.limit_length(0.06)


func kick(amount: float = 0.04, rot: float = 6.0) -> void:
	_kick = minf(_kick + amount, 0.14)
	_kick_rot = minf(_kick_rot + rot, 22.0)


func cast_push(amount: float = 1.0) -> void:
	_cast = amount


func set_tilt(t: float) -> void:
	_tilt = t


func _process(delta: float) -> void:
	if current == null:
		return
	_equip_t = minf(1.0, _equip_t + delta * 4.0)
	_sway_target = _sway_target.lerp(Vector2.ZERO, 1.0 - exp(-6.0 * delta))
	_sway = _sway.lerp(_sway_target, 1.0 - exp(-12.0 * delta))
	_kick = lerpf(_kick, 0.0, 1.0 - exp(-14.0 * delta))
	_kick_rot = lerpf(_kick_rot, 0.0, 1.0 - exp(-12.0 * delta))
	_cast = lerpf(_cast, 0.0, 1.0 - exp(-9.0 * delta))
	var base: Vector3 = current.get_meta("base_pos")
	var bob_amt := clampf(_speed / 5.4, 0.0, 1.5) * (1.0 if _grounded else 0.2)
	var bob := Vector3(cos(_bob_t) * 0.012, absf(sin(_bob_t)) * 0.016, 0) * bob_amt
	var equip_off := Vector3(0, -0.35, 0.05) * pow(1.0 - _equip_t, 2.0)
	holder.position = bob + equip_off + Vector3(-_sway.x, _sway.y, _kick - _cast * 0.08)
	holder.rotation = Vector3(deg_to_rad(_kick_rot) + _sway.y * 2.0, -_sway.x * 2.0, -_sway.x * 1.2 + _tilt * 0.4)
	current.position = base


## World position of the item's muzzle / emitter (for projectiles and effects).
func muzzle_position() -> Vector3:
	if current:
		for nm in ["Muzzle", "Emitter", "MuzzleL"]:
			var m := current.find_child(nm, true, false) as Node3D
			if m:
				return m.global_position
	return global_transform * Vector3(0.22, -0.16, -0.75)


# ------------------------------------------------------------------ placeholders
func _placeholder(model_name: String, equip_id: String) -> Node3D:
	var root := Node3D.new()
	root.name = model_name if model_name != "" else equip_id
	var brass := MaterialLib.get_named("M_Brass", "viewmodel")
	var wood := MaterialLib.get_named("M_WoodDark", "viewmodel")
	var leather := MaterialLib.get_named("M_Leather", "viewmodel")
	var glow_color := Color(0.4, 0.95, 0.9)
	match model_name:
		"vm_staff":
			glow_color = Color(0.66, 0.42, 1.0)
		"vm_arc_pistol":
			glow_color = Color(0.4, 0.9, 1.0)
		"vm_rivet_repeater", "vm_boom_mortar":
			glow_color = Color(1.0, 0.6, 0.25)
	var glow := MaterialLib.get_flat(glow_color, "viewmodel").duplicate() as ShaderMaterial
	glow.set_shader_parameter("emission_color", glow_color)
	glow.set_shader_parameter("emission_energy", 3.0)
	# glove
	var glove := MeshInstance3D.new()
	var gm := CapsuleMesh.new()
	gm.radius = 0.055
	gm.height = 0.2
	glove.mesh = gm
	glove.material_override = leather
	glove.position = Vector3(0, -0.02, 0.08)
	glove.rotation_degrees = Vector3(90, 0, 0)
	root.add_child(glove)
	var body := MeshInstance3D.new()
	var tip := Node3D.new()
	tip.name = "Muzzle" if model_name.begins_with("vm_arc") or model_name.begins_with("vm_rivet") or model_name.begins_with("vm_boom") else "Emitter"
	match model_name:
		"vm_staff":
			var cm := CylinderMesh.new()
			cm.top_radius = 0.018
			cm.bottom_radius = 0.024
			cm.height = 0.5
			body.mesh = cm
			body.material_override = wood
			body.rotation_degrees = Vector3(90, 0, 0)
			body.position = Vector3(0, 0, -0.12)
			var orb := MeshInstance3D.new()
			var om := SphereMesh.new()
			om.radius = 0.045
			om.height = 0.09
			orb.mesh = om
			orb.material_override = glow
			orb.position = Vector3(0, 0, -0.39)
			root.add_child(orb)
			tip.position = Vector3(0, 0, -0.44)
		"vm_gauntlet":
			var bm := BoxMesh.new()
			bm.size = Vector3(0.12, 0.08, 0.16)
			body.mesh = bm
			body.material_override = brass
			body.position = Vector3(0, 0.0, -0.02)
			var gem := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.035
			sm.height = 0.07
			gem.mesh = sm
			gem.material_override = glow
			gem.position = Vector3(0, 0.0, -0.11)
			root.add_child(gem)
			tip.position = Vector3(0, 0, -0.16)
		_:
			var bm2 := BoxMesh.new()
			bm2.size = Vector3(0.07, 0.09, 0.32)
			body.mesh = bm2
			body.material_override = brass
			body.position = Vector3(0, 0.05, -0.12)
			var barrel := MeshInstance3D.new()
			var cm2 := CylinderMesh.new()
			var r := 0.06 if model_name == "vm_boom_mortar" else 0.025
			cm2.top_radius = r
			cm2.bottom_radius = r
			cm2.height = 0.22
			barrel.mesh = cm2
			barrel.material_override = glow if model_name == "vm_arc_pistol" or model_name == "vm_toolkit" else MaterialLib.get_named("M_Steel", "viewmodel")
			barrel.rotation_degrees = Vector3(90, 0, 0)
			barrel.position = Vector3(0, 0.06, -0.33)
			root.add_child(barrel)
			tip.position = Vector3(0, 0.06, -0.46)
	root.add_child(body)
	root.add_child(tip)
	# placeholders are built facing -Z already; compensate the 180 degree yaw applied by PLACEMENT
	var wrapper := Node3D.new()
	wrapper.rotation_degrees = Vector3(0, 180, 0)
	wrapper.add_child(root)
	for c in wrapper.get_children():
		pass
	var outer := Node3D.new()
	outer.add_child(wrapper)
	return outer
