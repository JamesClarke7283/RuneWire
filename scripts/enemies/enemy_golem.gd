extends Enemy
## Rune Golem: slow, heavy, slams the ground (telegraphed) and hurls boulders.

var _slam_phase: float = -1.0
var _throw_cd: float = 4.0
var _step_t: float = 0.0


func _setup() -> void:
	body_height = 2.8
	body_radius = 0.95


func _on_aggro() -> void:
	AudioManager.play("golem_step", global_position, 2.0, 0.6)


func think(delta: float, dist: float) -> void:
	_throw_cd -= delta
	if _slam_phase >= 0.0:
		desired_velocity = Vector3.ZERO
		_slam_phase += delta
		if _slam_phase >= 0.75 and _slam_phase - delta < 0.75:
			_do_slam()
		if _slam_phase > 1.4:
			_slam_phase = -1.0
		return
	if aggro and target:
		face_towards(target.global_position, delta, 3.0)
		if dist < 4.6 and attack_cd <= 0.0:
			_slam_phase = 0.0
			attack_cd = 2.6
			AudioManager.play("golem_slam", global_position, -2.0, 0.8)
			return
		if dist > 9.0 and dist < 28.0 and _throw_cd <= 0.0 and can_attack():
			_throw_cd = randf_range(5.0, 7.5)
			var from := global_position + Vector3.UP * 3.0
			var tp := target.global_position + target.velocity * 0.6
			var flat := Vector3(tp.x - from.x, 0, tp.z - from.z)
			var t := clampf(flat.length() / 18.0, 0.6, 2.0)
			var vel := flat / t + Vector3.UP * (tp.y - from.y + 0.5 * 12.0 * t * t) / t
			Projectile.spawn(self, from, vel, {"damage": 20.0 * Game.difficulty, "damage_type": "kinetic", "color": Color(0.6, 0.55, 0.5),
				"kind": "bomb", "size": 0.45, "from_player": false, "source": self, "gravity": 12.0, "splash_radius": 2.5, "splash_damage": 14.0 * Game.difficulty})
			return
		steer_to(target.global_position, move_speed)
	else:
		wander(move_speed)


func _do_slam() -> void:
	var p := global_position + facing_dir() * 2.2
	VFX.ring(self, p + Vector3.UP * 0.2, Color(0.75, 0.5, 1.0), 6.0, 0.5)
	VFX.puffs(self, p, Color(0.62, 0.58, 0.55), 10, 0.9, 1.0, 1.0)
	VFX.burst(self, p, Color(0.8, 0.6, 1.0), 14, 6.0, 0.2, 0.6, -10.0, "spark")
	AudioManager.play("golem_slam", p, 4.0)
	if target and target.global_position.distance_to(p) < 5.0:
		var dir := (target.global_position - p).normalized()
		target.apply_damage(DamageInfo.make(28.0 * Game.difficulty, "kinetic", self, p, dir + Vector3.UP * 0.6, 11.0))
	var pl := get_tree().get_first_node_in_group("player") as Player
	if pl and pl.global_position.distance_to(p) < 18.0:
		pl.shake(0.7, 0.35)


func animate(delta: float) -> void:
	var walking := Vector2(velocity.x, velocity.z).length() > 0.3
	if walking:
		_step_t += delta * move_speed * 1.1
		if fmod(_step_t, PI) < delta * move_speed * 1.1:
			AudioManager.play("golem_step", global_position, -4.0, 0.9)
	var swing := sin(_step_t) * (0.45 if walking else 0.0)
	var legl := node("LegL")
	var legr := node("LegR")
	if legl:
		legl.rotation.x = swing
	if legr:
		legr.rotation.x = -swing
	var hips := node("Hips")
	if hips:
		hips.position.y = hips.position.y
	var torso := node("Torso")
	var arml := node("ArmL")
	var armr := node("ArmR")
	var fl := node("ForearmL")
	var fr := node("ForearmR")
	if _slam_phase >= 0.0:
		var t := _slam_phase
		var raise := clampf(t / 0.6, 0.0, 1.0)
		var smash := clampf((t - 0.6) / 0.15, 0.0, 1.0)
		var ang := lerpf(0.0, -2.4, raise) + smash * 2.9
		if arml:
			arml.rotation.x = ang
		if armr:
			armr.rotation.x = ang
		if fl:
			fl.rotation.x = -0.6 * raise * (1.0 - smash)
		if fr:
			fr.rotation.x = -0.6 * raise * (1.0 - smash)
		if torso:
			torso.rotation.x = lerpf(-0.15 * raise, 0.35, smash)
	else:
		if arml:
			arml.rotation.x = lerpf(arml.rotation.x, -swing * 0.6, 1.0 - exp(-8.0 * delta))
		if armr:
			armr.rotation.x = lerpf(armr.rotation.x, swing * 0.6, 1.0 - exp(-8.0 * delta))
		if fl:
			fl.rotation.x = lerpf(fl.rotation.x, -0.25, 1.0 - exp(-6.0 * delta))
		if fr:
			fr.rotation.x = lerpf(fr.rotation.x, -0.25, 1.0 - exp(-6.0 * delta))
		if torso:
			torso.rotation.x = lerpf(torso.rotation.x, 0.06 + sin(_anim_t * 1.2) * 0.03, 1.0 - exp(-6.0 * delta))
			torso.rotation.z = sin(_step_t) * 0.06
	var head := node("Head")
	if head and target and aggro:
		var local: Vector3 = (head.get_parent() as Node3D).to_local(target.camera.global_position) if head.get_parent() is Node3D else Vector3.ZERO
		head.rotation.y = clampf(atan2(local.x, local.z), -0.8, 0.8)
