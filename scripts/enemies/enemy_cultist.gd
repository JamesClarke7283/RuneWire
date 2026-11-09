extends Enemy
## Choir Cultist: keeps its distance, casts homing arcane orbs and summons wisps.

var _cast_phase: float = -1.0
var _summon_cd: float = 10.0
var _staff_light: OmniLight3D


func _setup() -> void:
	body_height = 1.9
	body_radius = 0.42


func _on_model_ready() -> void:
	var cp := node("CastPoint")
	_staff_light = OmniLight3D.new()
	_staff_light.light_color = Color(0.7, 0.4, 1.0)
	_staff_light.light_energy = 0.8
	_staff_light.omni_range = 4.0
	if cp:
		cp.add_child(_staff_light)
	else:
		add_child(_staff_light)
		_staff_light.position = Vector3(0.4, 2.0, 0.3)


func cast_point() -> Vector3:
	var cp := node("CastPoint")
	if cp:
		return cp.global_position
	return global_position + Vector3.UP * 2.0 * scale_factor + facing_dir() * 0.5


func think(delta: float, dist: float) -> void:
	_summon_cd -= delta
	if _cast_phase >= 0.0:
		_cast_phase += delta
		desired_velocity = Vector3.ZERO
		if target:
			face_towards(target.global_position, delta, 8.0)
		if _cast_phase >= 0.45 and _cast_phase - delta < 0.45:
			_release_cast()
		if _cast_phase > 0.8:
			_cast_phase = -1.0
		return
	if aggro and target:
		face_towards(target.global_position, delta, 6.0)
		if _summon_cd <= 0.0 and _alive_summons() < 3:
			_summon_cd = 18.0
			_summon("wisp", 2)
			return
		if attack_cd <= 0.0 and can_attack() and dist < 30.0:
			attack_cd = randf_range(2.2, 3.0)
			_cast_phase = 0.0
			AudioManager.play("cultist_cast", global_position, -2.0)
			return
		strafe_around(target.global_position, 13.0, move_speed)
	else:
		wander(move_speed)


func _release_cast() -> void:
	if target == null:
		return
	shoot(cast_point(), target_pos(), 15.0, 12.0, "arcane", Color(0.75, 0.4, 1.0), {"size": 0.24, "homing_target": target, "homing_strength": 1.2})
	VFX.sparkle(self, cast_point(), Color(0.75, 0.4, 1.0), 8, 0.3)


func _alive_summons() -> int:
	var n := 0
	for s in summons:
		if is_instance_valid(s) and not s.dead:
			n += 1
	return n


func _summon(k: String, count: int) -> void:
	for i in count:
		var a := randf() * TAU
		var p := global_position + Vector3(cos(a), 0, sin(a)) * 3.0 + Vector3.UP * 1.5
		var e := Enemy.spawn(k, _world, p)
		if e:
			e.aggro = true
			e.home = global_position
			summons.append(e)
			VFX.ring(self, p, Color(0.75, 0.4, 1.0), 2.0, 0.5)
			VFX.sparkle(self, p, Color(1.0, 0.6, 0.3), 10, 0.3)
	AudioManager.play("cultist_cast", global_position, 2.0, 0.7)


func animate(delta: float) -> void:
	var moving := Vector2(velocity.x, velocity.z).length() > 0.3
	var body := node("Body")
	if body:
		body.position.y = body.position.y
		body.rotation.z = sin(_anim_t * (6.0 if moving else 1.5)) * (0.05 if moving else 0.015)
	var arml := node("ArmL")
	var armr := node("ArmR")
	var cast_amt := 0.0
	if _cast_phase >= 0.0:
		cast_amt = sin(clampf(_cast_phase / 0.8, 0.0, 1.0) * PI)
	if armr:
		armr.rotation.x = lerpf(armr.rotation.x, -1.5 * cast_amt - 0.2, 1.0 - exp(-12.0 * delta))
	if arml:
		arml.rotation.x = lerpf(arml.rotation.x, -0.6 * cast_amt + sin(_anim_t * 2.0) * 0.05, 1.0 - exp(-10.0 * delta))
	if _staff_light:
		_staff_light.light_energy = 0.8 + cast_amt * 3.0
