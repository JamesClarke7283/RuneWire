class_name Viewmodel
extends Node3D
## First-person item presentation: loads the Blender viewmodel (or a procedural placeholder),
## tints it for the weapon instance (spell crystal colour, rarity glow accent) and animates equip,
## sway, bob, recoil, casting, melee swings, the Rivet Repeater's drum, the Scattergun's pump, the
## Tesla Lance's charge core, the Gatling's barrels, the Crossbow's bolt, the Piston Maul's piston,
## the Grimoire's pages, the Gloom Orb's orb and the Sunlance Scepter's halo.

const BASE_POS := Vector3(0.25, -0.24, -0.44)
const PLACEMENT := {
	"vm_gauntlet": {"pos": Vector3(0.24, -0.25, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_toolkit": {"pos": Vector3(0.24, -0.24, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_staff": {"pos": Vector3(0.25, -0.27, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_arc_pistol": {"pos": Vector3(0.22, -0.22, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_rivet_repeater": {"pos": Vector3(0.225, -0.25, -0.43), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_boom_mortar": {"pos": Vector3(0.24, -0.25, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_scattergun": {"pos": Vector3(0.22, -0.25, -0.38), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_tesla_lance": {"pos": Vector3(0.21, -0.25, -0.34), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_thunder_wrench": {"pos": Vector3(0.26, -0.29, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_longshot": {"pos": Vector3(0.21, -0.25, -0.36), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_gatling": {"pos": Vector3(0.27, -0.29, -0.44), "rot": Vector3(0, 180, 0), "scale": 0.92},
	"vm_flamer": {"pos": Vector3(0.23, -0.26, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_crossbow": {"pos": Vector3(0.22, -0.25, -0.40), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_steam_hammer": {"pos": Vector3(0.31, -0.40, -0.46), "rot": Vector3(0, 180, 0), "scale": 0.95},
	"vm_wand": {"pos": Vector3(0.25, -0.26, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_tome": {"pos": Vector3(0.30, -0.30, -0.56), "rot": Vector3(0, 180, 0), "scale": 0.74},
	"vm_orb": {"pos": Vector3(0.25, -0.27, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_scepter": {"pos": Vector3(0.25, -0.27, -0.42), "rot": Vector3(0, 180, 0), "scale": 1.0},
	"vm_runeblade": {"pos": Vector3(0.33, -0.36, -0.44), "rot": Vector3(0, 180, 0), "scale": 1.0},
}
## The Wispcaller Grimoire's spine direction in the model's own space (its "Pages" turn about it).
const SPINE_AXIS := Vector3(0.0, 0.6428, 0.766)
const GUN_MODELS := ["vm_arc_pistol", "vm_rivet_repeater", "vm_boom_mortar", "vm_scattergun", "vm_tesla_lance",
	"vm_longshot", "vm_gatling", "vm_flamer", "vm_crossbow"]
const MELEE_MODELS := ["vm_thunder_wrench", "vm_steam_hammer", "vm_runeblade"]

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
var _swing_len: float = 0.0
var _swing_left: float = 0.0
var _swing_heavy: bool = false
var _drum_spin: float = 0.0
var _pump: float = 0.0
var _pump_t: float = 0.0
var _charge: float = 0.0
var _barrel_spin: float = 0.0
var _channel: float = 0.0
var _piston: float = 0.0
var _pages: float = 0.0
var _glow_cache: Dictionary = {}


func _ready() -> void:
	holder = Node3D.new()
	holder.name = "Holder"
	add_child(holder)


func show_model(model_name: String, equip_id: String, weapon: Dictionary = {}) -> void:
	if current:
		current.visible = false
	current_model = model_name
	if not models.has(model_name):
		var n: Node3D = null
		var path := "res://assets/models/weapons/%s.glb" % model_name
		if model_name != "" and ResourceLoader.exists(path):
			n = (load(path) as PackedScene).instantiate()
			_record_tint_slots(n)
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
	_apply_tints(current, equip_id, weapon)
	_swing_left = 0.0
	_charge = 0.0
	_pump = 0.0
	_barrel_spin = 0.0
	_channel = 0.0
	_piston = 0.0
	var bolt := _sub("Bolt")
	if bolt:
		bolt.visible = true
	var core := _sub("ChargeCore")
	if core:
		core.scale = Vector3.ONE * 0.3
	_equip_t = 0.0


## Remember which surfaces carry the spell crystal and the rarity accent, before toon conversion.
func _record_tint_slots(root: Node) -> void:
	var slots := []
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat == null:
				continue
			var nm := mat.resource_name
			if nm.begins_with("M_Crystal") or nm.begins_with("RarityGlow"):
				slots.append([m, i, "crystal" if nm.begins_with("M_Crystal") else "rarity"])
	root.set_meta("tint_slots", slots)


func _apply_tints(root: Node, equip_id: String, weapon: Dictionary) -> void:
	if not root.has_meta("tint_slots"):
		return
	var spell := Catalog.weapon_base(equip_id)
	var rarity := int(weapon.get("rarity", 0)) if not weapon.is_empty() else -1
	for s in root.get_meta("tint_slots"):
		var m: MeshInstance3D = s[0]
		if not is_instance_valid(m):
			continue
		if s[2] == "crystal" and spell.has("crystal"):
			var c: Color = spell["crystal"]
			m.set_surface_override_material(s[1], MaterialLib.get_named("M_Crystal__" + c.to_html(false), "viewmodel"))
		elif s[2] == "rarity":
			var col := Catalog.rarity_color(rarity) if rarity >= 0 else Color(0.4, 0.95, 0.9)
			m.set_surface_override_material(s[1], rarity_glow(col, "viewmodel"))


## Emissive accent material of a colour (cached), for the viewmodel or for world pickups.
func rarity_glow(col: Color, variant: String) -> Material:
	var key := col.to_html() + variant
	if _glow_cache.has(key):
		return _glow_cache[key]
	var m := MaterialLib.get_flat(col, variant, "glow").duplicate() as ShaderMaterial
	m.set_shader_parameter("emission_color", col)
	m.set_shader_parameter("emission_energy", 3.2)
	m.set_shader_parameter("emission_pulse", 0.2)
	_glow_cache[key] = m
	return m


func _sub(node_name: String) -> Node3D:
	if current == null:
		return null
	return current.find_child(node_name, true, false) as Node3D


func set_motion(speed: float, grounded: bool, bob_t: float) -> void:
	_speed = speed
	_grounded = grounded
	_bob_t = bob_t


func add_sway(rel: Vector2) -> void:
	_sway_target += rel * 0.0009
	_sway_target = _sway_target.limit_length(0.06)


func kick(amount: float = 0.04, rot: float = 6.0) -> void:
	_kick = minf(_kick + amount, 0.14)
	_kick_rot = clampf(_kick_rot + rot, -30.0, 22.0)


func cast_push(amount: float = 1.0) -> void:
	_cast = amount
	_pages = 1.0


func set_tilt(t: float) -> void:
	_tilt = t


## Melee swing animation (wind up, strike down and across, recover).
func swing(duration: float, heavy: bool = false) -> void:
	_swing_len = maxf(duration, 0.05)
	_swing_left = _swing_len
	_swing_heavy = heavy


func spin_drum(amount: float = 1.0) -> void:
	_drum_spin = minf(_drum_spin + amount * 6.0, 26.0)


## Scattergun pump: slide the fore-grip back and forward after `delay` seconds.
func pump(delay: float = 0.3) -> void:
	_pump_t = delay


func set_charge(f: float) -> void:
	_charge = clampf(f, 0.0, 1.0)


## Show or hide a named sub-part of the current model (the Crossbow's loaded "Bolt").
func show_part(node_name: String, on: bool) -> void:
	var n := _sub(node_name)
	if n:
		n.visible = on


## Gatling barrel speed 0..1 (spins the "Barrels" sub-object).
func spin_barrels(f: float) -> void:
	_barrel_spin = clampf(f, 0.0, 1.0)


## Channelling strength 0..1 (the Sunlance Scepter's halo spins and the model trembles).
func set_channel(f: float) -> void:
	_channel = clampf(f, 0.0, 1.0)


## Piston Maul: punch the "Piston" out toward the striking face and let it settle back.
func punch_piston() -> void:
	_piston = 1.0


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
	var swing_rot := Vector3.ZERO
	var swing_pos := Vector3.ZERO
	if _swing_left > 0.0:
		_swing_left = maxf(0.0, _swing_left - delta)
		var t := 1.0 - _swing_left / _swing_len
		# 0-0.35 wind up (raise and cock right), 0.35-0.6 strike (down and to the left), then recover
		var up := 0.0
		var across := 0.0
		if t < 0.35:
			var k := t / 0.35
			up = ease(k, 0.6)
			across = ease(k, 0.6) * 0.5
		elif t < 0.6:
			var k2 := (t - 0.35) / 0.25
			up = lerpf(1.0, -1.1, ease(k2, 1.8))
			across = lerpf(0.5, -1.0, ease(k2, 1.8))
		else:
			var k3 := (t - 0.6) / 0.4
			up = lerpf(-1.1, 0.0, ease(k3, 0.5))
			across = lerpf(-1.0, 0.0, ease(k3, 0.5))
		var amp := 1.35 if _swing_heavy else 1.0
		swing_rot = Vector3(up * 0.75, across * 0.5, -across * 0.45) * amp
		swing_pos = Vector3(-across * 0.08, up * 0.06, -maxf(-up, 0.0) * 0.08) * amp
	holder.position = bob + equip_off + Vector3(-_sway.x, _sway.y, _kick - _cast * 0.08) + swing_pos
	holder.rotation = Vector3(deg_to_rad(_kick_rot) + _sway.y * 2.0, -_sway.x * 2.0, -_sway.x * 1.2 + _tilt * 0.4) + swing_rot
	current.position = base
	# animated sub-parts
	if _drum_spin > 0.01:
		var drum := _sub("Drum")
		if drum:
			drum.rotate_object_local(Vector3.RIGHT, _drum_spin * delta)
		_drum_spin = lerpf(_drum_spin, 0.0, 1.0 - exp(-5.0 * delta))
	if _pump_t > 0.0:
		_pump_t -= delta
		if _pump_t <= 0.0:
			_pump = 1.0
	if _pump > 0.0:
		_pump = maxf(0.0, _pump - delta * 3.2)
		var p := _sub("Pump")
		if p:
			if not p.has_meta("rest"):
				p.set_meta("rest", p.position)
			var rest: Vector3 = p.get_meta("rest")
			p.position = rest + _pump_offset()
	_animate_extras(delta)
	var core := _sub("ChargeCore")
	if core:
		var want := 0.3 + 0.7 * _charge
		var s := lerpf(core.scale.x, want, 1.0 - exp(-14.0 * delta))
		if _charge >= 1.0:
			s = want * (1.0 + sin(Time.get_ticks_msec() / 40.0) * 0.06)
		core.scale = Vector3.ONE * s


## Gatling barrels, scepter halo, orb, grimoire pages and the maul's piston.
func _animate_extras(delta: float) -> void:
	if _barrel_spin > 0.01:
		var barrels := _sub("Barrels")
		if barrels:
			barrels.rotate_object_local(Vector3.BACK, _barrel_spin * 32.0 * delta)
	var halo := _sub("Halo")
	if halo:
		halo.rotate_object_local(Vector3.BACK, (0.6 + 9.0 * _channel) * delta)
	if _channel > 0.01:
		holder.position += Vector3(randf_range(-1, 1), randf_range(-1, 1), 0) * 0.0025 * _channel
	var orb := _sub("Orb")
	if orb:
		orb.rotate_object_local(Vector3.UP, 1.4 * delta)
		orb.scale = Vector3.ONE * (1.0 + sin(Time.get_ticks_msec() / 260.0) * 0.04 + _cast * 0.12)
	if _pages > 0.0:
		_pages = maxf(0.0, _pages - delta * 2.4)
		var pages := _sub("Pages")
		if pages:
			if not pages.has_meta("rest_basis"):
				pages.set_meta("rest_basis", pages.basis)
			var b0: Basis = pages.get_meta("rest_basis")
			pages.basis = Basis(SPINE_AXIS, sin(_pages * PI * 3.0) * 0.45 * _pages) * b0
	if _piston > 0.0:
		_piston = maxf(0.0, _piston - delta * 3.0)
		var piston := _sub("Piston")
		if piston:
			if not piston.has_meta("rest"):
				piston.set_meta("rest", piston.position)
				var tip := _sub("Tip")
				var dir := Vector3(0, 0, 1)
				if tip and piston.get_parent() is Node3D:
					var par := piston.get_parent() as Node3D
					var d := par.to_local(tip.global_position) - piston.position
					if d.length() > 0.001:
						dir = d.normalized()
				piston.set_meta("dir", dir)
			var rest: Vector3 = piston.get_meta("rest")
			var pdir: Vector3 = piston.get_meta("dir")
			piston.position = rest + pdir * 0.07 * sin(minf(_piston * 1.6, 1.0) * PI * 0.5) * (1.0 if _piston > 0.4 else _piston / 0.4)


## The pump slides toward the player: Blender +Y is glTF -Z in the model's own space.
func _pump_offset() -> Vector3:
	return Vector3(0, 0, -0.06) * sin(_pump * PI)


## World position of the item's muzzle / emitter (for projectiles and effects).
func muzzle_position() -> Vector3:
	if current:
		for nm in ["Muzzle", "Emitter", "Tip", "MuzzleL"]:
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
		"vm_staff", "vm_wand", "vm_tome", "vm_orb", "vm_scepter", "vm_runeblade":
			glow_color = Catalog.weapon_base(equip_id).get("crystal", Color(0.66, 0.42, 1.0))
		"vm_arc_pistol", "vm_tesla_lance", "vm_thunder_wrench":
			glow_color = Color(0.4, 0.9, 1.0)
		"vm_rivet_repeater", "vm_boom_mortar", "vm_scattergun":
			glow_color = Color(1.0, 0.6, 0.25)
	var glow := MaterialLib.get_flat(glow_color, "viewmodel").duplicate() as ShaderMaterial
	glow.set_shader_parameter("emission_color", glow_color)
	glow.set_shader_parameter("emission_energy", 3.0)
	# glove
	var glove := MeshInstance3D.new()
	glove.name = "Glove"
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
	tip.name = "Emitter"
	if model_name in GUN_MODELS:
		tip.name = "Muzzle"
	elif model_name in MELEE_MODELS:
		tip.name = "Tip"
	match model_name:
		"vm_staff", "vm_wand", "vm_tome", "vm_orb", "vm_scepter":
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
		"vm_thunder_wrench", "vm_steam_hammer", "vm_runeblade":
			var hm := CylinderMesh.new()
			hm.top_radius = 0.02
			hm.bottom_radius = 0.026
			hm.height = 0.55
			body.mesh = hm
			body.material_override = MaterialLib.get_named("M_Steel", "viewmodel")
			body.rotation_degrees = Vector3(-55, 0, 0)
			body.position = Vector3(0, 0.12, -0.16)
			var head := MeshInstance3D.new()
			var hb := BoxMesh.new()
			hb.size = Vector3(0.16, 0.08, 0.12)
			head.mesh = hb
			head.material_override = brass
			head.position = Vector3(0, 0.34, -0.33)
			root.add_child(head)
			var cell := MeshInstance3D.new()
			var cs := SphereMesh.new()
			cs.radius = 0.035
			cs.height = 0.07
			cell.mesh = cs
			cell.material_override = glow
			cell.position = Vector3(0, 0.27, -0.27)
			root.add_child(cell)
			tip.position = Vector3(0, 0.36, -0.38)
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
			var long := model_name == "vm_tesla_lance"
			var bm2 := BoxMesh.new()
			bm2.size = Vector3(0.07, 0.09, 0.32)
			body.mesh = bm2
			body.material_override = brass
			body.position = Vector3(0, 0.05, -0.12)
			var barrel := MeshInstance3D.new()
			var cm2 := CylinderMesh.new()
			var r := 0.06 if model_name == "vm_boom_mortar" else (0.045 if model_name == "vm_scattergun" else 0.025)
			cm2.top_radius = r
			cm2.bottom_radius = r
			cm2.height = 0.4 if long else 0.22
			barrel.mesh = cm2
			barrel.material_override = glow if model_name in ["vm_arc_pistol", "vm_toolkit", "vm_tesla_lance"] else MaterialLib.get_named("M_Steel", "viewmodel")
			barrel.rotation_degrees = Vector3(90, 0, 0)
			barrel.position = Vector3(0, 0.06, -0.42 if long else -0.33)
			root.add_child(barrel)
			tip.position = Vector3(0, 0.06, -0.64 if long else -0.46)
			if model_name == "vm_tesla_lance":
				var core := MeshInstance3D.new()
				core.name = "ChargeCore"
				var ccm := SphereMesh.new()
				ccm.radius = 0.03
				ccm.height = 0.06
				core.mesh = ccm
				core.material_override = glow
				core.position = Vector3(0, 0.12, -0.12)
				root.add_child(core)
	root.add_child(body)
	root.add_child(tip)
	# placeholders are built facing -Z already; compensate the 180 degree yaw applied by PLACEMENT
	var wrapper := Node3D.new()
	wrapper.rotation_degrees = Vector3(0, 180, 0)
	wrapper.add_child(root)
	var outer := Node3D.new()
	outer.add_child(wrapper)
	return outer
