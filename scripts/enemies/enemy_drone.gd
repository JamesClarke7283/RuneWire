extends Enemy
## Scout Drone: hovers, strafes at range and fires rivet bursts. Lightning eats it for breakfast.

var _rotors: Array = []
var _burst_left: int = 0
var _burst_t: float = 0.0


func _setup() -> void:
	body_height = 0.8
	body_radius = 0.55
	hover_height = 5.0


func _on_model_ready() -> void:
	for i in 4:
		var r := node("Rotor_%d" % i)
		if r:
			_rotors.append(r)
	AudioManager.attach_loop(self, "drone_loop", -10.0, 5.0)


func think(delta: float, dist: float) -> void:
	if aggro and target:
		strafe_around(target.global_position, 13.0, move_speed)
		face_towards(target.global_position, delta, 7.0)
		if _burst_left > 0:
			_burst_t -= delta
			if _burst_t <= 0.0:
				_burst_t = 0.12
				_burst_left -= 1
				var m := node("Muzzle")
				var from := m.global_position if m else aim_point() + facing_dir() * 0.6 + Vector3.DOWN * 0.3
				var tp := target_pos() + Vector3(randf_range(-0.6, 0.6), randf_range(-0.4, 0.4), randf_range(-0.6, 0.6))
				shoot(from, tp, 45.0, 5.0, "kinetic", Color(1.0, 0.7, 0.3), {"kind": "rivet", "size": 0.07, "trail": false})
				AudioManager.play("drone_shoot", from, -4.0)
		elif attack_cd <= 0.0 and can_attack() and dist < 30.0:
			attack_cd = randf_range(1.8, 2.6)
			_burst_left = 3
			_burst_t = 0.0
	else:
		wander(move_speed)


func animate(delta: float) -> void:
	for r in _rotors:
		(r as Node3D).rotate_object_local(Vector3.UP, delta * 40.0)
	if model:
		var lv := global_transform.basis.inverse() * velocity
		model.rotation.x = lerpf(model.rotation.x, clampf(lv.z * 0.06, -0.4, 0.4), 1.0 - exp(-5.0 * delta))
		model.rotation.z = lerpf(model.rotation.z, clampf(-lv.x * 0.06, -0.4, 0.4), 1.0 - exp(-5.0 * delta))
	var gun := node("Gun")
	if gun and target and aggro:
		var to := gun.global_position.direction_to(target_pos())
		var local := global_transform.basis.inverse() * to
		gun.rotation.x = -atan2(local.y, Vector2(local.x, local.z).length())
