class_name SpellCaster
extends EquipBase
## Magic weapons that cast from a crystal: wands, staves, the grimoire, the orb and the scepter.
## Each one casts by its "cast" mode:
##   bolt      Arcane Bolt, Emberwick Wand (quick bolts; hold to repeat; embers set foes ablaze)
##   spray     Rimefang Wand (a fan of frost shards that chill)
##   fireball  Fireball (exploding fireballs)
##   chain     Chain Lightning (leaps between foes)
##   ward      Mending Ward (heal over time + halve damage taken)
##   seeker    Wispcaller Grimoire (homing wisps)
##   orb       Gloom Orb (a slow orb that drags foes in, grinds them, then implodes)
##   beam      Sunlance Scepter (hold for a continuous beam that ramps up; costs mana per second)

const REPEAT := ["bolt", "spray", "fireball", "seeker"]

var cooldown: float = 0.0
var holding: bool = false
var beam_t: float = 0.0          # how long the beam has been held (ramps its damage)
var _tick_t: float = 0.0
var _snd_t: float = 0.0


func cast_mode() -> String:
	return str(data.get("cast", "bolt"))


func mana_cost() -> float:
	return float(data.get("mana", 0.0)) * (0.8 if player and player.has_buff("attuned") else 1.0)


func hint() -> String:
	var m := int(round(mana_cost()))
	match cast_mode():
		"bolt":
			return "LMB cast %s (hold to repeat) · %d mana%s" % [data.get("name", "Bolt"), m, " · sets foes ablaze" if data.has("burn") else ""]
		"spray":
			return "LMB fling %d frost shards (chills foes) · %d mana" % [int(data.get("shards", 3)), m]
		"fireball":
			return "LMB hurl a Fireball · %d mana" % m
		"chain":
			return "LMB Chain Lightning (aim at a foe) · %d mana" % m
		"ward":
			return "LMB cast Mending Ward: heal + halve damage · %d mana" % m
		"seeker":
			return "LMB release %d homing wisps · %d mana" % [int(data.get("seekers", 3)), m]
		"orb":
			return "LMB launch a Gloom Orb: drags foes in, then implodes · %d mana" % m
		"beam":
			return "Hold LMB to channel a sun beam (ramps up) · %d mana / s" % m
	return ""


func status() -> String:
	if cast_mode() == "beam":
		return "Channelling %d%%" % int(_ramp() * 100.0) if holding and beam_t > 0.0 else "Ready"
	return "Ready" if cooldown <= 0.0 else "%.1fs" % cooldown


func meter() -> float:
	if cast_mode() == "beam":
		return clampf(player.mana / maxf(Game.max_mana(), 1.0), 0.0, 1.0) if player else 1.0
	return clampf(1.0 - cooldown / maxf(float(data.get("cooldown", 1.0)), 0.01), 0.0, 1.0)


func on_unequip() -> void:
	holding = false
	beam_t = 0.0
	if player and player.viewmodel:
		player.viewmodel.set_channel(0.0)
	super.on_unequip()


func primary(pressed: bool) -> void:
	holding = pressed
	if pressed:
		if cast_mode() == "beam":
			beam_t = 0.0
			_tick_t = 0.0
		else:
			_try_cast()
	elif cast_mode() == "beam":
		beam_t = 0.0
		player.viewmodel.set_channel(0.0)


func tick(delta: float) -> void:
	cooldown -= delta
	if cast_mode() == "beam":
		if holding and not player.dead:
			_tick_beam(delta)
		return
	if holding and cooldown <= 0.0 and cast_mode() in REPEAT:
		_try_cast()


func _ramp() -> float:
	return clampf(beam_t / 1.5, 0.0, 1.0)


func _try_cast() -> void:
	if cooldown > 0.0 or player.dead:
		return
	if not player.spend_mana(mana_cost()):
		Events.toast("Not enough mana", "warn")
		AudioManager.play_2d("mana_empty", -4.0)
		cooldown = 0.35
		return
	cooldown = float(data["cooldown"])
	var col: Color = data["color"]
	var from := player.viewmodel.muzzle_position()
	var mult := player.damage_mult("magic")
	player.viewmodel.cast_push(1.0)
	var sfx := str(data.get("sfx", ""))
	match cast_mode():
		"bolt":
			var dir := (player.aim_point(120.0) - from).normalized()
			var fire := str(data.get("damage_type", "arcane")) == "fire"
			Projectile.spawn(player, from, dir * float(data["speed"]), {"damage": float(data["damage"]) * mult,
				"damage_type": str(data.get("damage_type", "arcane")), "color": col, "size": 0.13 if fire else 0.16,
				"from_player": true, "source": player, "lifetime": 2.5, "weapon": data})
			AudioManager.play_2d(sfx if sfx != "" else "spell_arcane_cast", -3.0 if not fire else -4.0, randf_range(0.95, 1.08))
			VFX.sparkle(player, from, col, 5, 0.18)
		"spray":
			var n := int(data.get("shards", 3))
			var aim := (player.aim_point(100.0) - from).normalized()
			var side := aim.cross(Vector3.UP).normalized()
			if side.length_squared() < 0.01:
				side = Vector3.RIGHT
			var spread := deg_to_rad(float(data.get("spread", 5.0)))
			for i in n:
				var a := (float(i) - float(n - 1) * 0.5) * spread
				var d := aim.rotated(Vector3.UP, -a).normalized()
				Projectile.spawn(player, from, d * float(data.get("speed", 60.0)), {"damage": float(data["damage"]) * mult,
					"damage_type": "frost", "color": col, "size": 0.11, "from_player": true, "source": player,
					"lifetime": float(data.get("range", 70.0)) / float(data.get("speed", 60.0)), "weapon": data})
			AudioManager.play_2d(sfx if sfx != "" else "spell_arcane_cast", -3.0, randf_range(0.95, 1.05))
			VFX.burst(player, from, col, 8, 3.0, 0.1, 0.35, 0.0, "star", 40.0, aim)
		"fireball":
			var dir2 := (player.aim_point(120.0) - from).normalized()
			Projectile.spawn(player, from, dir2 * float(data["speed"]), {"damage": float(data["damage"]) * mult, "damage_type": "fire",
				"splash_damage": float(data["splash"]) * mult, "splash_radius": float(data["radius"]), "color": col, "size": 0.32,
				"from_player": true, "source": player, "lifetime": 3.0, "gravity": 2.0, "weapon": data})
			AudioManager.play_2d("spell_fireball_cast", -2.0)
			VFX.burst(player, from, col, 8, 2.0, 0.12, 0.3, 0.0, "spark")
		"chain":
			_chain(from, col, mult)
		"ward":
			player.add_heal_over_time(float(data["heal"]), float(data["duration"]))
			player.ward_timer = float(data["duration"]) + 1.0
			AudioManager.play_2d("spell_heal", -2.0)
			var feet := player.global_position + Vector3.UP * 0.1
			VFX.ring(player, feet, col, 3.0, 0.7)
			VFX.sparkle(player, player.global_position + Vector3.UP * 1.0, col, 20, 0.35)
			_rune_circle(feet, col)
		"seeker":
			_seekers(from, col, mult)
			AudioManager.play_2d(sfx if sfx != "" else "spell_arcane_cast", -2.0)
		"orb":
			var dir3 := (player.aim_point(float(data.get("range", 40.0))) - from).normalized()
			VoidOrb.spawn(player, from, dir3, data, mult)
			AudioManager.play_2d(sfx if sfx != "" else "spell_arcane_cast", -1.0)
			player.viewmodel.kick(0.04, 6.0)


## Grimoire: wisps that home in on the foes closest to the crosshair (or fly straight on).
func _seekers(from: Vector3, col: Color, mult: float) -> void:
	var n := int(data.get("seekers", 3))
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	var targets: Array = []
	var scored: Array = []
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.get("dead"):
			continue
		var ap: Vector3 = e.aim_point()
		var to := ap - cam.global_position
		if to.length() > float(data.get("range", 60.0)):
			continue
		var dot := to.normalized().dot(fwd)
		if dot < 0.55:
			continue
		scored.append([dot, e])
	scored.sort_custom(func(a, b): return a[0] > b[0])
	for s in scored:
		targets.append(s[1])
	var side := fwd.cross(Vector3.UP).normalized()
	for i in n:
		var t: Node3D = targets[i % targets.size()] if not targets.is_empty() else null
		var off := side * (float(i) - float(n - 1) * 0.5) * 0.6 + Vector3.UP * randf_range(0.2, 0.6)
		var v := (fwd + off * 0.6).normalized() * float(data.get("speed", 24.0))
		Projectile.spawn(player, from + off * 0.15, v, {"damage": float(data["damage"]) * mult, "damage_type": "arcane",
			"color": col, "size": 0.15, "from_player": true, "source": player, "lifetime": 3.2, "weapon": data,
			"homing_target": t, "homing_strength": 5.0 if t else 0.0})
	VFX.sparkle(player, from, col, 10, 0.25)


## Sunlance Scepter: a continuous beam while LMB is held. Mana drains per second; damage ramps up.
func _tick_beam(delta: float) -> void:
	_tick_t -= delta
	beam_t += delta
	player.viewmodel.set_channel(0.4 + 0.6 * _ramp())
	if _tick_t > 0.0:
		return
	_tick_t = 0.1
	if not player.spend_mana(mana_cost() * 0.1):
		Events.toast("Not enough mana", "warn")
		AudioManager.play_2d("mana_empty", -4.0)
		holding = false
		beam_t = 0.0
		player.viewmodel.set_channel(0.0)
		return
	var col: Color = data["color"]
	var from := player.viewmodel.muzzle_position()
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	var rng := float(data.get("range", 40.0))
	var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + fwd * rng, 1 | 4 | 8 | 128)
	q.exclude = [player.get_rid()]
	var h := player.get_world_3d().direct_space_state.intersect_ray(q)
	var end := cam.global_position + fwd * rng
	if h:
		end = h["position"]
		var ramp := 1.0 + (float(data.get("ramp", 1.5)) - 1.0) * _ramp()
		var dmg := float(data["damage"]) * 0.1 * ramp * player.damage_mult("magic")
		Combat.damage_hit(h, hit(dmg, str(data.get("damage_type", "arcane")), end, fwd, 0.2))
		VFX.burst(player, end, col, 4, 3.0, 0.16, 0.3, 1.0, "spark", 80.0, h["normal"])
	var w := 0.035 + 0.04 * _ramp()
	VFX.beam(player, from, end, col.lerp(Color.WHITE, 0.35), w, 0.12)
	VFX.beam(player, from, end, col, w * 2.2, 0.09)
	_snd_t -= 0.1
	if _snd_t <= 0.0:
		_snd_t = 0.3
		AudioManager.play_2d(str(data.get("sfx", "beam_hum")), -6.0, 0.97 + 0.08 * _ramp(), 0.0)


func _chain(from: Vector3, col: Color, mult: float) -> void:
	var rng := float(data["range"])
	var first: Node3D = null
	var hit_r := player.aim_ray(rng, 1 | 4 | 8)
	if hit_r and Combat.is_enemy(hit_r["collider"]):
		first = hit_r["collider"]
	else:
		# pick the enemy closest to the crosshair inside a cone
		var fwd := -player.camera.global_transform.basis.z
		var best := 0.96
		for e in get_tree().get_nodes_in_group("enemies"):
			if e.get("dead"):
				continue
			var ap: Vector3 = e.aim_point()
			var to := ap - player.camera.global_position
			if to.length() > rng:
				continue
			var d := to.normalized().dot(fwd)
			if d > best and Combat.has_los(player, player.camera.global_position, ap, [e]):
				best = d
				first = e
	AudioManager.play_2d("spell_lightning", -2.0)
	if first == null:
		var miss := player.aim_point(rng)
		VFX.lightning(player, from, miss, col, 8, 0.6, 0.18)
		return
	var dmg := float(data["damage"]) * mult
	var chain: Array = [first]
	var cur := first
	for i in int(data["chains"]):
		var nxt := Combat.nearest_enemy(cur, cur.global_position, 9.0, true, chain)
		if nxt == null:
			break
		chain.append(nxt)
		cur = nxt
	var prev_pos := from
	for i in chain.size():
		var e: Node3D = chain[i]
		if not is_instance_valid(e):
			continue
		var ap: Vector3 = e.aim_point()
		VFX.lightning(player, prev_pos, ap, col, 8, 0.7, 0.22)
		var info := hit(dmg * pow(0.85, i), "shock", ap, (ap - prev_pos).normalized(), 1.0)
		e.apply_damage(info)
		prev_pos = ap


func _rune_circle(pos: Vector3, col: Color) -> void:
	var d := Decal.new()
	d.texture_albedo = VFX.fx_texture("vfx_rune_circle")
	d.texture_emission = d.texture_albedo
	d.emission_energy = 2.0
	d.modulate = col
	d.size = Vector3(4.5, 2.0, 4.5)
	VFX.root(player).add_child(d)
	d.global_position = pos
	var tw := d.create_tween()
	tw.tween_property(d, "rotation:y", TAU * 0.5, float(data["duration"]))
	tw.parallel().tween_property(d, "modulate:a", 0.0, 1.0).set_delay(float(data["duration"]) - 1.0)
	tw.tween_callback(d.queue_free)
