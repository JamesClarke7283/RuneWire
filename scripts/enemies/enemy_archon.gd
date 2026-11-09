extends "res://scripts/enemies/enemy_cultist.gd"
## The Hollow Archon (magic boss): a towering cultist that fires orb volleys, unleashes an arcane
## nova when you get close, summons wisps and wraiths and teleports around the altar.

var _nova_cd: float = 6.0
var _tele_cd: float = 12.0
var _phase2: bool = false


func _setup() -> void:
	body_height = 1.9
	body_radius = 0.9
	scale_factor = 2.3
	weak_point = "Head"


func _build_collision() -> void:
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 1.0
	cap.height = 4.4
	cs.shape = cap
	cs.position.y = 2.2
	add_child(cs)


func aim_point() -> Vector3:
	return global_position + Vector3.UP * 2.6


func think(delta: float, dist: float) -> void:
	_nova_cd -= delta
	_tele_cd -= delta
	if not _phase2 and hp < max_hp * 0.5:
		_phase2 = true
		move_speed *= 1.3
		Events.toast("The Archon's song grows louder!", "warn")
		_summon("wraith", 2)
	if _cast_phase >= 0.0:
		super.think(delta, dist)
		return
	if aggro and target:
		if dist < 7.0 and _nova_cd <= 0.0:
			_nova_cd = 7.0 if not _phase2 else 4.5
			_nova()
			return
		if _tele_cd <= 0.0:
			_tele_cd = randf_range(10.0, 14.0)
			_teleport()
			return
		if _summon_cd <= 0.0 and _alive_summons() < 5:
			_summon_cd = 16.0 if not _phase2 else 11.0
			_summon("wisp" if randf() < 0.6 else "wraith", 2 if not _phase2 else 3)
			return
	super.think(delta, dist)


func _release_cast() -> void:
	if target == null:
		return
	var n := 5 if not _phase2 else 7
	var base_dir := (target_pos() - cast_point()).normalized()
	for i in n:
		var ang := (float(i) - (n - 1) / 2.0) * 0.16
		var dir := base_dir.rotated(Vector3.UP, ang)
		Projectile.spawn(self, cast_point(), dir * 15.0, {"damage": 11.0 * power(), "damage_type": "arcane", "color": Color(0.75, 0.4, 1.0),
			"size": 0.28, "from_player": false, "source": self, "homing_target": target, "homing_strength": 0.5, "lifetime": 5.0})
	VFX.sparkle(self, cast_point(), Color(0.75, 0.4, 1.0), 16, 0.4)


func _nova() -> void:
	var p := global_position + Vector3.UP * 0.5
	VFX.ring(self, p, Color(0.8, 0.5, 1.0), 9.0, 0.6)
	VFX.ring(self, p + Vector3.UP * 1.5, Color(0.5, 0.9, 1.0), 7.0, 0.5)
	VFX.sparkle(self, p + Vector3.UP, Color(0.8, 0.5, 1.0), 30, 0.5)
	AudioManager.play("spell_lightning", p, 4.0, 0.6)
	if target and target.global_position.distance_to(global_position) < 9.0:
		var dir := (target.global_position - global_position).normalized()
		target.apply_damage(DamageInfo.make(26.0 * power(), "arcane", self, p, dir + Vector3.UP * 0.5, 13.0))


func _teleport() -> void:
	var a := randf() * TAU
	var to := home + Vector3(cos(a), 0, sin(a)) * randf_range(4.0, 12.0)
	if _world:
		to.y = _world.ground_y(to.x, to.z) + 0.3
	VFX.puffs(self, global_position + Vector3.UP * 2.0, Color(0.35, 0.25, 0.5), 12, 1.2, 1.0, 1.0)
	global_position = to
	VFX.ring(self, to + Vector3.UP * 0.2, Color(0.8, 0.5, 1.0), 4.0, 0.5)
	AudioManager.play("wraith_shriek", to, 0.0, 0.6)
