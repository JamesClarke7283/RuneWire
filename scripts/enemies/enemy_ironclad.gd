extends Enemy
## Ironclad Warwalker (tech boss): stomps, fires explosive cannon shells and homing rocket
## barrages, calls drones in phase two. Its glowing cockpit eye takes double damage.

var _rocket_cd: float = 8.0
var _stomp_cd: float = 3.0
var _drone_cd: float = 0.0
var _phase2: bool = false
var _step_t: float = 0.0
var _rocket_left: int = 0
var _rocket_t: float = 0.0
var _smoke_t: float = 0.0


func _setup() -> void:
	body_height = 5.0
	body_radius = 1.6
	weak_point = "Head"
	move_speed = 2.4


func _build_collision() -> void:
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 1.7
	cap.height = 5.0
	cs.shape = cap
	cs.position.y = 2.6
	add_child(cs)


func aim_point() -> Vector3:
	return global_position + Vector3.UP * 3.6


func _muzzle(n: String, fallback: Vector3) -> Vector3:
	var m := node(n)
	return m.global_position if m else global_transform * fallback


func think(delta: float, dist: float) -> void:
	_rocket_cd -= delta
	_stomp_cd -= delta
	_drone_cd -= delta
	if not _phase2 and hp < max_hp * 0.5:
		_phase2 = true
		Events.toast("The Ironclad vents steam and calls for reinforcements!", "warn")
		_drone_cd = 0.0
	if _rocket_left > 0:
		_rocket_t -= delta
		if _rocket_t <= 0.0 and target:
			_rocket_t = 0.18
			_rocket_left -= 1
			var from := _muzzle("MuzzleR", Vector3(-1.6, 4.4, 0.8))
			var dir := (Vector3.UP * 1.2 + facing_dir() * 0.6 + Vector3(randf_range(-0.6, 0.6), 0, randf_range(-0.6, 0.6))).normalized()
			Projectile.spawn(self, from, dir * 16.0, {"damage": 12.0 * power(), "damage_type": "fire", "color": Color(1.0, 0.55, 0.2),
				"kind": "rocket", "size": 0.16, "from_player": false, "source": self, "homing_target": target, "homing_strength": 2.2,
				"lifetime": 6.0, "splash_radius": 2.2, "splash_damage": 8.0 * power()})
			AudioManager.play("ironclad_rocket", from, -2.0)
	if not (aggro and target):
		wander(move_speed)
		return
	face_towards(target.global_position, delta, 1.6)
	if _phase2 and _drone_cd <= 0.0:
		_drone_cd = 20.0
		for i in 2:
			var p := global_position + Vector3(randf_range(-6, 6), 7.0, randf_range(-6, 6))
			var e := Enemy.spawn("drone", _world, p)
			if e:
				e.aggro = true
				summons.append(e)
	if dist < 6.5 and _stomp_cd <= 0.0:
		_stomp_cd = 3.5
		_stomp()
		desired_velocity = Vector3.ZERO
		return
	if _rocket_cd <= 0.0 and can_attack():
		_rocket_cd = 10.0 if not _phase2 else 7.0
		_rocket_left = 6
		return
	if attack_cd <= 0.0 and can_attack() and dist < 45.0:
		attack_cd = 3.0 if not _phase2 else 2.2
		var from2 := _muzzle("MuzzleL", Vector3(1.6, 3.6, 1.6))
		var tp := target.global_position + target.velocity * 0.5
		shoot(from2, tp, 34.0, 18.0, "fire", Color(1.0, 0.6, 0.2), {"kind": "bomb", "size": 0.28, "splash_radius": 4.0, "splash_damage": 24.0 * power(), "gravity": 3.0})
		AudioManager.play("gun_mortar", from2, 4.0, 0.7)
		VFX.muzzle(self, from2, Color(1.0, 0.6, 0.2), 0.5)
	if dist > 12.0:
		steer_to(target.global_position, move_speed)
	else:
		desired_velocity = Vector3.ZERO


func _stomp() -> void:
	var p := global_position + facing_dir() * 2.0
	VFX.ring(self, p + Vector3.UP * 0.2, Color(1.0, 0.7, 0.3), 9.0, 0.5)
	VFX.puffs(self, p, Color(0.5, 0.48, 0.5), 12, 1.2, 1.2, 1.0)
	AudioManager.play("ironclad_step", p, 6.0, 0.7)
	if target and target.global_position.distance_to(p) < 7.0:
		var dir := (target.global_position - p).normalized()
		target.apply_damage(DamageInfo.make(25.0 * power(), "kinetic", self, p, dir + Vector3.UP * 0.7, 14.0))
	var pl := get_tree().get_first_node_in_group("player") as Player
	if pl and pl.global_position.distance_to(p) < 30.0:
		pl.shake(0.8, 0.4)


func animate(delta: float) -> void:
	var walking := Vector2(velocity.x, velocity.z).length() > 0.3
	if walking:
		var prev := _step_t
		_step_t += delta * 2.2
		if int(prev / PI) != int(_step_t / PI):
			AudioManager.play("ironclad_step", global_position, 0.0, 0.9)
			var pl := get_tree().get_first_node_in_group("player") as Player
			if pl and pl.global_position.distance_to(global_position) < 25.0:
				pl.shake(0.25, 0.2)
	var swing := sin(_step_t) * (0.4 if walking else 0.0)
	var tl := node("ThighL")
	var tr := node("ThighR")
	var sl := node("ShinL")
	var sr := node("ShinR")
	if tl:
		tl.rotation.x = swing
	if tr:
		tr.rotation.x = -swing
	if sl:
		sl.rotation.x = maxf(0.0, -sin(_step_t)) * 0.6
	if sr:
		sr.rotation.x = maxf(0.0, sin(_step_t)) * 0.6
	var pelvis := node("Pelvis")
	if pelvis:
		pelvis.rotation.z = sin(_step_t) * 0.04
	var torso := node("Torso")
	if torso and target:
		torso.rotation.y = lerp_angle(torso.rotation.y, 0.0, 1.0 - exp(-3.0 * delta))
	var arml := node("ArmL")
	if arml and target and aggro:
		var to := global_transform.basis.inverse() * (target_pos() - arml.global_position)
		arml.rotation.x = lerpf(arml.rotation.x, -atan2(to.y, Vector2(to.x, to.z).length()), 1.0 - exp(-4.0 * delta))
	_smoke_t -= delta
	if _smoke_t <= 0.0:
		_smoke_t = 0.35 if not _phase2 else 0.15
		for s in ["Smoke_0", "Smoke_1"]:
			var sn := node(s)
			if sn:
				VFX.puffs(self, sn.global_position, Color(0.35, 0.33, 0.36), 1, 0.7, 1.6, 3.0)
