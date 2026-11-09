class_name Contraption
extends RigidBody3D
## A compound rigid body made of welded Parts. Handles mass properties, devices, piloting,
## flight assist (hover stones / rotors), quest tracking (drive distance, altitude) and impacts.

signal parts_changed

const G := 9.8

var parts: Array[Part] = []
var devices: Array[Device] = []
var pilot: Player = null
var pilot_seat: Part = null
var pilot_input: Dictionary = {}
var held: bool = false
var lights_on: bool = true
var hover_height: float = 2.5
var tags: Dictionary = {}

var _owner_part: Dictionary = {}
var _drive_last: Vector3 = Vector3.ZERO
var _drive_accum: float = 0.0
var _alt_timer: float = 0.0
var _impact_cd: float = 0.0
var _hover_cap: float = 0.0
var _rotor_cap: float = 0.0
var _has_lift: bool = false
var _wheel_count: int = 0
var _terrain: Terrain = null


func _init() -> void:
	collision_layer = 4
	collision_mask = 1 | 2 | 4 | 8 | 128
	continuous_cd = true
	contact_monitor = true
	max_contacts_reported = 4
	can_sleep = true
	linear_damp = 0.04
	angular_damp = 0.35
	freeze_mode = RigidBody3D.FREEZE_MODE_STATIC
	add_to_group("contraptions")


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	var w := get_tree().get_first_node_in_group("world")
	if w:
		_terrain = w.terrain


# ------------------------------------------------------------------ parts
func add_part(part: Part, world_xform: Transform3D, recompute_now: bool = true) -> void:
	if part.get_parent():
		part.get_parent().remove_child(part)
	add_child(part)
	part.global_transform = world_xform
	part.contraption = self
	parts.append(part)
	part.owner_ids.clear()
	for s in part.shapes:
		var oid := create_shape_owner(part)
		shape_owner_add_shape(oid, s["shape"])
		shape_owner_set_transform(oid, part.transform * (s["xform"] as Transform3D))
		part.owner_ids.append(oid)
		_owner_part[oid] = part
	if part.device:
		devices.append(part.device)
		part.device.on_attached(self)
	if recompute_now:
		recompute()


## Remove a part. keep_alive: the node is detached (caller re-parents it); otherwise it's being destroyed.
func remove_part(part: Part, keep_alive: bool = true) -> void:
	if not parts.has(part):
		return
	for oid in part.owner_ids:
		remove_shape_owner(oid)
		_owner_part.erase(oid)
	part.owner_ids.clear()
	parts.erase(part)
	if part.device:
		devices.erase(part.device)
		part.device.on_detached()
	if pilot_seat == part and pilot:
		pilot.exit_seat()
	if keep_alive:
		var xf := part.global_transform
		remove_child(part)
		part.transform = xf
	part.contraption = null
	if parts.is_empty():
		queue_free()
	else:
		recompute()


func part_from_shape(shape_idx: int) -> Part:
	if shape_idx < 0:
		return null
	var oid := shape_find_owner(shape_idx)
	return _owner_part.get(oid, null)


## Absorb every part of another contraption (keeping world transforms).
func merge_from(other: Contraption) -> void:
	if other == self or not is_instance_valid(other):
		return
	var total := mass + other.mass
	var lv := (linear_velocity * mass + other.linear_velocity * other.mass) / maxf(total, 0.01)
	var moved: Array[Part] = other.parts.duplicate()
	for p in moved:
		var xf := p.global_transform
		other.remove_part(p, true)
		add_part(p, xf, false)
	if other.freeze:
		freeze = true
	if is_instance_valid(other):
		other.queue_free()
	recompute()
	linear_velocity = lv


func recompute() -> void:
	var m := 0.0
	var com := Vector3.ZERO
	_hover_cap = 0.0
	_rotor_cap = 0.0
	_wheel_count = 0
	var seats := 0
	var turrets := 0
	var thrusters := 0
	for p in parts:
		var pm := p.part_mass()
		m += pm
		com += p.position * pm
		var dev: String = p.def.get("device", "")
		match dev:
			"wheel":
				_wheel_count += 1
			"hover":
				_hover_cap += float(p.def.get("lift_mass", 400.0))
			"rotor":
				_rotor_cap += float(p.def.get("force", 3000.0))
			"seat":
				seats += 1
			"turret_arcane", "turret_rivet":
				turrets += 1
			"thruster":
				thrusters += 1
	m = maxf(m, 1.0)
	mass = m
	center_of_mass_mode = RigidBody3D.CENTER_OF_MASS_MODE_CUSTOM
	center_of_mass = com / m
	_has_lift = _hover_cap > 0.0 or _rotor_cap > 0.0
	# Loose wheels roll on their own cylinder; welded wheels use raycast suspension instead.
	for p in parts:
		if p.def.get("device", "") == "wheel":
			for oid in p.owner_ids:
				shape_owner_set_disabled(oid, parts.size() > 1)
	for d in devices:
		d.on_recomputed()
	var new_tags := []
	if seats > 0 and _wheel_count >= 3:
		new_tags.append("vehicle")
	if seats > 0 and (_has_lift):
		new_tags.append("flyer")
	if _hover_cap > 0.0:
		new_tags.append("hover")
	if turrets > 0:
		new_tags.append("armed")
	if thrusters > 0:
		new_tags.append("rocket")
	var fresh := []
	for t in new_tags:
		if not tags.has(t):
			tags[t] = true
			fresh.append(t)
	if not fresh.is_empty():
		Events.contraption_built.emit(self, fresh)
	parts_changed.emit()


func radius() -> float:
	var r := 0.5
	for p in parts:
		r = maxf(r, p.position.distance_to(center_of_mass) + p.half_extents().length())
	return r


func wheel_count() -> int:
	return _wheel_count


func describe() -> String:
	return "%d parts · %d kg%s" % [parts.size(), int(mass), "  ·  FROZEN" if freeze else ""]


func seat_part() -> Part:
	if pilot_seat:
		return pilot_seat
	for p in parts:
		if p.def.get("device", "") == "seat":
			return p
	return null


## Forward / right / up axes of the pilot frame (the seat if there is one).
func pilot_basis() -> Basis:
	var s := seat_part()
	if s and is_instance_valid(s):
		return s.global_transform.basis.orthonormalized()
	return global_transform.basis.orthonormalized()


# ------------------------------------------------------------------ piloting
func set_pilot(p: Player, seat: Part) -> void:
	pilot = p
	pilot_seat = seat
	pilot_input = {}
	if p:
		freeze = false
		sleeping = false
		_drive_last = global_position
		if _hover_cap > 0.0 and _terrain:
			hover_height = clampf(_height_above_ground(), 1.5, 10.0)


func toggle_lights() -> void:
	lights_on = not lights_on
	for d in devices:
		if d is LampDevice:
			(d as LampDevice).set_on(lights_on)
	AudioManager.play("tool_configure", global_position, -6.0)


func _physics_process(delta: float) -> void:
	_impact_cd = maxf(0.0, _impact_cd - delta)
	if freeze:
		return
	var piloted := pilot != null and is_instance_valid(pilot)
	var ctl: Dictionary = pilot_input if piloted else {}
	for d in devices:
		if d.enabled:
			d.physics_step(delta, ctl, piloted)
	if _has_lift:
		_flight(delta, ctl, piloted)
	if piloted:
		_track(delta)


func _height_above_ground() -> float:
	var com := global_transform * center_of_mass
	var q := PhysicsRayQueryParameters3D.create(com, com - Vector3.UP * 60.0, 1 | 4)
	q.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit:
		return com.y - (hit["position"] as Vector3).y
	if _terrain:
		return com.y - _terrain.height_at(com.x, com.z)
	return 60.0


func _flight(delta: float, ctl: Dictionary, piloted: bool) -> void:
	var lift_in: float = ctl.get("lift", 0.0)
	var vy := linear_velocity.y
	var up_force := 0.0
	var cap_force := 0.0
	# Hover stones hold a height above the ground, piloted or not.
	if _hover_cap > 0.0:
		if piloted:
			hover_height = clampf(hover_height + lift_in * 4.0 * delta, 1.0, 14.0)
		var h := _height_above_ground()
		var a := (hover_height - h) * 6.0 - vy * 3.2
		var cap := _hover_cap * G * 1.4
		up_force += clampf(mass * (G + a), 0.0, cap)
		cap_force += cap
	# Rotors are motors: they only work with a pilot.
	if _rotor_cap > 0.0 and piloted:
		var want_vy := lift_in * 6.0
		var a2 := (want_vy - vy) * 3.0
		var need := mass * (G + a2)
		var rotor_force := clampf(need - up_force, 0.0, _rotor_cap)
		up_force += rotor_force
		cap_force += _rotor_cap
	if up_force <= 0.0:
		return
	# Apply lift at each lift device so lopsided builds tilt, then stabilise.
	var lifters: Array[Device] = []
	for d in devices:
		if (d is HoverDevice) or (d is RotorDevice and piloted):
			if d.enabled:
				lifters.append(d)
	if lifters.is_empty():
		return
	var per := up_force / lifters.size()
	for d in lifters:
		apply_force(Vector3.UP * per, d.part.global_position - global_position)
	# upright stabilisation (roll/pitch) and spin damping
	var up_now := global_transform.basis.y
	var s := seat_part()
	if s:
		up_now = s.global_transform.basis.y
	var tilt_axis := up_now.cross(Vector3.UP)
	var inertia_k := mass * maxf(radius(), 1.0) * 1.2
	apply_torque(tilt_axis * inertia_k * 9.0 - Vector3(angular_velocity.x, 0, angular_velocity.z) * inertia_k * 2.4)
	# pilot movement: thrust along the seat's flattened forward, yaw with A/D
	if piloted:
		var b := pilot_basis()
		var fwd := b.z
		fwd.y = 0
		fwd = fwd.normalized()
		var thr: float = ctl.get("throttle", 0.0)
		var steer: float = ctl.get("steer", 0.0)
		var boost := 1.6 if ctl.get("boost", false) else 1.0
		var hv := Vector3(linear_velocity.x, 0, linear_velocity.z)
		var max_speed := 18.0 * boost
		if absf(thr) > 0.05:
			if hv.dot(fwd) * signf(thr) < max_speed:
				apply_central_force(fwd * thr * mass * 7.0 * boost)
		else:
			apply_central_force(-hv * mass * 0.9)
		var side := hv - fwd * hv.dot(fwd)
		apply_central_force(-side * mass * 1.2)
		apply_torque(Vector3.UP * (-steer) * inertia_k * 4.5 - Vector3(0, angular_velocity.y, 0) * inertia_k * 2.0)


func _track(delta: float) -> void:
	var pos := global_position
	var step := Vector2(pos.x - _drive_last.x, pos.z - _drive_last.z).length()
	_drive_last = pos
	if step < 5.0 and _wheel_count >= 3:
		_drive_accum += step
		if _drive_accum >= 1.0:
			Events.contraption_driven.emit(self, floorf(_drive_accum))
			_drive_accum -= floorf(_drive_accum)
	_alt_timer += delta
	if _alt_timer > 0.5:
		_alt_timer = 0.0
		var alt := _height_above_ground()
		Events.contraption_altitude.emit(self, alt)


func _on_body_entered(body: Node) -> void:
	var speed := linear_velocity.length()
	if _impact_cd > 0.0 or speed < 5.0:
		return
	_impact_cd = 0.25
	var mat: String = parts[0].def.get("material", "wood") if not parts.is_empty() else "wood"
	var snd := "impact_wood" if mat == "wood" else ("impact_stone" if mat == "stone" else "impact_metal")
	AudioManager.play(snd, global_position, clampf(-14.0 + speed, -12.0, 4.0), 1.0)
	if body.is_in_group("enemies") and speed > 7.0:
		var dmg := speed * clampf(mass / 120.0, 0.4, 6.0) * 1.4
		Combat.damage_node(body, DamageInfo.make(dmg, "kinetic", pilot, global_position, linear_velocity.normalized(), 8.0, true))
