extends Enemy
## Shade Wraith: floats low, blinks around the player and claws (draining mana).

var _blink_cd: float = 5.0
var _claw_phase: float = -1.0


func _setup() -> void:
	body_height = 2.0
	body_radius = 0.55
	hover_height = 1.6


func _on_aggro() -> void:
	AudioManager.play("wraith_shriek", global_position, 0.0)


func think(delta: float, dist: float) -> void:
	_blink_cd -= delta
	if _claw_phase >= 0.0:
		_claw_phase += delta
		desired_velocity = Vector3.ZERO
		if _claw_phase >= 0.3 and _claw_phase - delta < 0.3:
			if melee(2.8, 13.0, "arcane", 4.0) and target:
				target.mana = maxf(0.0, target.mana - 15.0)
				target.mana_changed.emit(target.mana, Game.max_mana())
				VFX.sparkle(self, target.global_position + Vector3.UP, Color(0.4, 0.5, 1.0), 8, 0.25)
		if _claw_phase > 0.7:
			_claw_phase = -1.0
		return
	if aggro and target:
		face_towards(target.global_position, delta, 7.0)
		if _blink_cd <= 0.0 and dist > 4.0:
			_blink_cd = randf_range(5.5, 8.0)
			_blink()
			return
		if dist < 2.4 and attack_cd <= 0.0:
			attack_cd = 1.4
			_claw_phase = 0.0
			return
		steer_to(target.global_position, move_speed)
	else:
		wander(move_speed)


func _blink() -> void:
	var from := global_position
	var a := randf() * TAU
	var to := target.global_position + Vector3(cos(a), 0, sin(a)) * randf_range(3.0, 5.5)
	if _world:
		to.y = _world.ground_y(to.x, to.z) + hover_height
	VFX.puffs(self, from, Color(0.3, 0.22, 0.4), 8, 0.7, 0.8, 1.0)
	VFX.sparkle(self, from, Color(0.4, 0.9, 0.9), 10, 0.3)
	global_position = to
	VFX.puffs(self, to, Color(0.3, 0.22, 0.4), 8, 0.7, 0.8, 1.0)
	AudioManager.play("wraith_shriek", to, -6.0, 1.3)


func animate(delta: float) -> void:
	if model:
		model.position.y = sin(_anim_t * 1.8) * 0.15
		model.rotation.x = clampf(velocity.length() * 0.05, 0.0, 0.3)
	var body := node("Body")
	if body:
		body.rotation.z = sin(_anim_t * 1.3) * 0.06
	var hl := node("HandL")
	var hr := node("HandR")
	var reach := 0.0
	if _claw_phase >= 0.0:
		reach = sin(clampf(_claw_phase / 0.6, 0.0, 1.0) * PI)
	if hl:
		hl.rotation.x = -1.2 * reach + sin(_anim_t * 2.2) * 0.15
	if hr:
		hr.rotation.x = -1.2 * reach + sin(_anim_t * 2.2 + 1.5) * 0.15
	var head := node("Head")
	if head:
		head.rotation.z = sin(_anim_t * 0.9) * 0.12
	var _u := delta
