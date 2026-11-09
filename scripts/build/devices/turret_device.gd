class_name TurretDevice
extends Device
## Auto turret (arcane bolts or rivets). Targets the nearest enemy in range with line of sight.
## While piloting, holding LMB aims every turret at the crosshair.

var style: String = "arcane"
var fire_range: float = 30.0
var _cooldown: float = 0.0
var _scan: float = 0.0
var _target: Node3D = null
var _yaw: Node3D
var _pitch: Node3D
var _barrels: Node3D
var _muzzle: Node3D
var _barrel_spin: float = 0.0
var _cur_yaw: float = 0.0
var _cur_pitch: float = 0.0


func supports_binding() -> bool:
	return true


func _ready() -> void:
	fire_range = float(part.def.get("range", 30.0))
	_yaw = part.model.find_child("Yaw", true, false) as Node3D
	_pitch = part.model.find_child("Pitch", true, false) as Node3D
	_barrels = part.model.find_child("Barrels", true, false) as Node3D
	_muzzle = part.model.find_child("Muzzle", true, false) as Node3D


func describe() -> String:
	var mode := "auto-target" if binding in ["auto", "always"] else ("pilot fire" if binding == "fire" else binding_name())
	return "%s  ·  %s%s" % [part.display_name(), mode, "" if enabled else "  ·  OFF"]


func _muzzle_pos() -> Vector3:
	if _muzzle:
		return _muzzle.global_position
	return part.global_position + part.global_transform.basis.y * 0.35 + part.global_transform.basis.z * 0.4


func physics_step(delta: float, ctl: Dictionary, piloted: bool) -> void:
	_cooldown -= delta
	_scan -= delta
	if contraption == null:
		return
	var aim_at: Variant = null
	var manual: bool = piloted and bool(ctl.get("fire", false)) and binding in ["auto", "fire"]
	if manual:
		aim_at = ctl.get("aim", null)
	elif binding in ["auto", "always"]:
		if _scan <= 0.0:
			_scan = 0.35
			_target = Combat.nearest_enemy(self, _muzzle_pos(), fire_range, true)
		if _target and is_instance_valid(_target) and not _target.get("dead"):
			aim_at = _target.aim_point() if _target.has_method("aim_point") else _target.global_position
		else:
			_target = null
	if aim_at == null:
		return
	var aligned := _aim(aim_at, delta)
	if _barrels and style == "rivet":
		_barrel_spin += delta * 25.0
		_barrels.rotation.z = _barrel_spin
	if aligned and _cooldown <= 0.0:
		_fire(aim_at)


func _aim(p: Vector3, delta: float) -> bool:
	var pivot := _yaw.global_position if _yaw else part.global_position
	var d := part.global_transform.basis.orthonormalized().inverse() * (p - pivot)
	var want_yaw := atan2(d.x, d.z)
	var want_pitch := -atan2(d.y, Vector2(d.x, d.z).length())
	_cur_yaw = lerp_angle(_cur_yaw, want_yaw, 1.0 - exp(-9.0 * delta))
	_cur_pitch = lerpf(_cur_pitch, clampf(want_pitch, -1.2, 0.6), 1.0 - exp(-9.0 * delta))
	if _yaw:
		_yaw.rotation.y = _cur_yaw
	if _pitch:
		_pitch.rotation.x = _cur_pitch
	if not _yaw:
		return true
	return absf(angle_difference(_cur_yaw, want_yaw)) < 0.12


func _fire(p: Vector3) -> void:
	var from := _muzzle_pos()
	var dir := (p - from).normalized()
	var mult := Game.weapon_damage_mult()
	if style == "arcane":
		_cooldown = 0.6
		Projectile.spawn(self, from, dir * 42.0, {"damage": 12.0 * mult, "damage_type": "arcane", "color": Color(0.7, 0.45, 1.0),
			"size": 0.16, "from_player": true, "source": contraption, "lifetime": 2.0})
		AudioManager.play("turret_arcane", from, -3.0)
		VFX.muzzle(self, from, Color(0.7, 0.45, 1.0), 0.18)
	else:
		_cooldown = 0.11
		dir = (dir + Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * 0.025).normalized()
		Projectile.spawn(self, from, dir * 85.0, {"damage": 5.5 * mult, "damage_type": "kinetic", "color": Color(1.0, 0.8, 0.4),
			"size": 0.07, "kind": "rivet", "from_player": true, "source": contraption, "lifetime": 1.2, "trail": false})
		AudioManager.play("turret_rivet", from, -6.0, 1.0, 0.1)
		VFX.muzzle(self, from, Color(1.0, 0.75, 0.35), 0.12)
