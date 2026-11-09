class_name MeleeWeapon
extends EquipBase
## Melee weapons: LMB quick swing (hold to keep swinging), RMB heavy attack.
##   Thunder Wrench  kinetic whack + a capacitor zap of shock; repairs your contraption parts on hit.
##   Piston Maul     slow crushing swings; heavy = a ground-slam shockwave that flings foes ("quake").
##   Runeblade       quick arcane slashes; heavy = a piercing crescent wave for mana ("wave").

var swing_t: float = 0.0        # time left in the current swing
var swing_len: float = 0.5
var heavy: bool = false
var _struck: bool = false
var _held: bool = false


func school() -> String:
	return str(data.get("school", "tech"))


func hint() -> String:
	if data.has("quake"):
		return "LMB swing · RMB ground slam: a shockwave that flings foes away"
	if data.has("wave"):
		return "LMB slash · RMB loose a piercing rune wave (%d mana)" % int(round(_wave_mana()))
	return "LMB swing · RMB heavy slam · whack your contraption parts to repair them"


func status() -> String:
	return "Ready" if swing_t <= 0.0 else ("Slam!" if heavy else "Swing!")


func meter() -> float:
	return 1.0 if swing_t <= 0.0 else 1.0 - swing_t / maxf(swing_len, 0.01)


func _wave_mana() -> float:
	return float(data.get("wave_mana", 15.0)) * (0.8 if player and player.has_buff("attuned") else 1.0)


func on_unequip() -> void:
	_held = false
	super.on_unequip()


func primary(pressed: bool) -> void:
	_held = pressed
	if pressed:
		_start(false)


func secondary(pressed: bool) -> void:
	if pressed:
		_start(true)


func _start(is_heavy: bool) -> void:
	if swing_t > 0.0 or player.dead:
		return
	if is_heavy and data.has("wave") and not player.spend_mana(_wave_mana()):
		Events.toast("Not enough mana for a rune wave", "warn")
		AudioManager.play_2d("mana_empty", -4.0)
		is_heavy = false
	heavy = is_heavy
	swing_len = float(data.get("swing_time", 0.55)) * (1.7 if heavy else 1.0)
	swing_t = swing_len
	_struck = false
	player.viewmodel.swing(swing_len, heavy)
	AudioManager.play_2d(str(data.get("sfx_swing", "wrench_swing")), -4.0, 0.85 if heavy else 1.0, 0.08)


func tick(delta: float) -> void:
	if swing_t <= 0.0:
		if _held:
			_start(false)   # keep swinging while LMB is held
		return
	swing_t -= delta
	# the blow lands a little past the middle of the swing
	if not _struck and swing_t <= swing_len * (0.45 if heavy else 0.55):
		_struck = true
		_strike()


func _strike() -> void:
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	var reach := float(data.get("reach", 3.0)) * (1.15 if heavy else 1.0)
	var mult := player.damage_mult(school()) * (1.8 if heavy else 1.0)
	var dmg := float(data.get("damage", 30.0)) * mult
	var zap := float(data.get("zap", 0.0)) * mult
	var dtype := str(data.get("damage_type", "kinetic"))
	var col: Color = data.get("color", Color(0.5, 0.9, 1.0))
	var knock := float(data.get("knock", 9.0 if heavy else 5.0)) * (1.0 if heavy else 0.55)
	if heavy and data.has("wave"):
		_rune_wave(fwd, dmg, col)
		return
	var space := player.get_world_3d().direct_space_state
	var shape := SphereShape3D.new()
	shape.radius = reach * (0.6 if heavy else 0.5)
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.transform = Transform3D(Basis(), cam.global_position + fwd * reach * 0.55)
	q.collision_mask = 4 | 8 | 128
	q.exclude = [player.get_rid()]
	var results := space.intersect_shape(q, 24)
	var done := {}
	var hit_any := false
	var repaired := 0
	for r in results:
		var c: Object = r["collider"]
		if c is Contraption:
			var part: Part = (c as Contraption).part_from_shape(int(r.get("shape", 0)))
			if part and not done.has(part.get_instance_id()):
				done[part.get_instance_id()] = true
				if data.has("repair") and part.hp < part.max_hp:
					part.hp = minf(part.max_hp, part.hp + float(data.get("repair", 30.0)) * (1.5 if heavy else 1.0))
					repaired += 1
					VFX.weld_sparks(player, part.global_position)
				hit_any = true
			continue
		var key := c.get_instance_id()
		if done.has(key):
			continue
		done[key] = true
		if Combat.is_enemy(c):
			var e := c as Node3D
			var ap: Vector3 = e.aim_point() if e.has_method("aim_point") else e.global_position
			if not Combat.has_los(player, cam.global_position, ap, [c]):
				continue
			var dir := (ap - cam.global_position).normalized()
			e.apply_damage(hit(dmg, dtype, ap, dir + Vector3.UP * 0.25, knock))
			if zap > 0.0 and is_instance_valid(e) and not e.get("dead"):
				var z := hit(zap, "shock", ap, dir, 0.0)
				z.proc = true
				e.apply_damage(z)
				VFX.lightning(player, player.viewmodel.muzzle_position(), ap, col, 5, 0.25, 0.12)
			VFX.burst(player, ap, col.lerp(Color(1.0, 0.9, 0.6), 0.5), 12, 6.0, 0.14, 0.4, -12.0, "spark")
			hit_any = true
		elif c is RigidBody3D:
			(c as RigidBody3D).apply_central_impulse(fwd * 8.0 * (c as RigidBody3D).mass * (1.6 if heavy else 1.0))
			hit_any = true
	if heavy:
		var feet := player.global_position + Vector3(fwd.x, 0, fwd.z).normalized() * 1.6 + Vector3.UP * 0.1
		if data.has("quake"):
			hit_any = _quake(feet, mult, col) or hit_any
		else:
			VFX.ring(player, feet, col, 3.2, 0.4)
			player.shake(0.35, 0.2)
	if hit_any:
		player.viewmodel.kick(0.05, -10.0)
		player.shake(0.2 if heavy else 0.1, 0.12)
		AudioManager.play_2d(str(data.get("sfx_hit", "wrench_hit")), -2.0 if heavy else -4.0, 0.9 if heavy else 1.0, 0.08)
	if repaired > 0:
		AudioManager.play_2d("tool_weld", -6.0, 1.2)


## Piston Maul heavy: a shockwave around the impact point that damages and flings every foe nearby.
func _quake(at: Vector3, mult: float, col: Color) -> bool:
	var r := float(data.get("quake", 4.5))
	var any := false
	player.viewmodel.punch_piston()
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.get("dead"):
			continue
		var n := e as Node3D
		var d := Vector2(n.global_position.x - at.x, n.global_position.z - at.z).length()
		if d > r or absf(n.global_position.y - at.y) > 3.5:
			continue
		var dir := (n.global_position - at)
		dir.y = 0.0
		dir = dir.normalized() if dir.length() > 0.01 else -player.camera.global_transform.basis.z
		var fall := clampf(1.2 - d / r, 0.4, 1.0)
		e.apply_damage(hit(float(data.get("damage", 50.0)) * 0.8 * mult * fall, "kinetic", n.global_position, dir + Vector3.UP * 0.8,
			float(data.get("knock", 14.0)) * fall))
		any = true
	VFX.ring(player, at, col, r, 0.5)
	VFX.puffs(player, at, Color(0.62, 0.55, 0.45), 10, 1.1, 1.0, 1.5)
	VFX.burst(player, at, Color(1.0, 0.85, 0.5), 18, 9.0, 0.16, 0.5, -14.0, "spark", 70.0)
	player.shake(0.5, 0.3)
	AudioManager.play_2d(str(data.get("sfx_hit", "hammer_slam")), -1.0, 0.95)
	return any


## Runeblade heavy: a crescent wave of arcane force that pierces several foes.
func _rune_wave(fwd: Vector3, dmg: float, col: Color) -> void:
	var from := player.camera.global_position + fwd * 0.9 + Vector3.DOWN * 0.15
	Projectile.spawn(player, from, fwd * 34.0, {"damage": float(data.get("wave", 40.0)) * player.damage_mult(school()),
		"damage_type": str(data.get("damage_type", "arcane")), "color": col, "size": 0.34, "from_player": true,
		"source": player, "lifetime": 0.85, "pierce": 3, "knockback": 6.0, "weapon": data})
	VFX.burst(player, from, col, 12, 6.0, 0.16, 0.35, 0.0, "star", 40.0, fwd)
	player.viewmodel.kick(0.05, -8.0)
	AudioManager.play_2d("blade_wave", -2.0)
