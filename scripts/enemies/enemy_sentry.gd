extends Enemy
## Sentry Turret: static gun with a limited turn rate. Flank it!

var _yaw: float = 0.0
var _pitch: float = 0.0
var _burst_left: int = 0
var _burst_t: float = 0.0
var _spin: float = 0.0
var _lamp_t: float = 0.0


func _setup() -> void:
	body_height = 1.8
	body_radius = 0.75


func aim_point() -> Vector3:
	return global_position + Vector3.UP * 1.3


func think(delta: float, dist: float) -> void:
	desired_velocity = Vector3.ZERO
	if not (aggro and target and dist < 38.0):
		_yaw += delta * 0.4
		return
	var yaw_node := node("Yaw")
	var pivot := yaw_node.global_position if yaw_node else aim_point()
	var d := global_transform.basis.inverse() * (target_pos() - pivot)
	var want_yaw := atan2(d.x, d.z)
	var want_pitch := -atan2(d.y, Vector2(d.x, d.z).length())
	var turn := 1.3 * delta
	_yaw += clampf(angle_difference(_yaw, want_yaw), -turn, turn)
	_pitch = move_toward(_pitch, clampf(want_pitch, -0.8, 0.6), turn)
	var aligned := absf(angle_difference(_yaw, want_yaw)) < 0.12
	if _burst_left > 0:
		_burst_t -= delta
		if _burst_t <= 0.0:
			_burst_t = 0.1
			_burst_left -= 1
			_spin += 1.0
			var m := node("Muzzle")
			var from := m.global_position if m else aim_point() + Vector3(sin(_yaw), 0, cos(_yaw)) * 1.0
			var dir := Vector3(sin(_yaw), -sin(_pitch), cos(_yaw)).normalized()
			dir = global_transform.basis * dir
			var tp := from + dir * 30.0 + Vector3(randf_range(-0.8, 0.8), randf_range(-0.5, 0.5), randf_range(-0.8, 0.8))
			shoot(from, tp, 55.0, 5.0, "kinetic", Color(1.0, 0.65, 0.25), {"kind": "rivet", "size": 0.07, "trail": false})
			AudioManager.play("sentry_shoot", from, -3.0)
			VFX.muzzle(self, from, Color(1.0, 0.65, 0.25), 0.2)
	elif aligned and attack_cd <= 0.0 and can_attack():
		attack_cd = 2.2
		_burst_left = 6


func animate(delta: float) -> void:
	var y := node("Yaw")
	var p := node("Pitch")
	var b := node("Barrels")
	if y:
		y.rotation.y = _yaw
	if p:
		p.rotation.x = _pitch
	if b:
		b.rotation.z += delta * _spin * 20.0
	_spin = maxf(0.0, _spin - delta * 2.0)
	_lamp_t += delta
	var lamp := node("Lamp")
	if lamp:
		lamp.visible = aggro and fmod(_lamp_t, 0.6) < 0.35 or not aggro
