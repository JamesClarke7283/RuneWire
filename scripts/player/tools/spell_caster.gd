class_name SpellCaster
extends EquipBase
## Casts the equipped spell from the staff's crystal.

var cooldown: float = 0.0
var holding: bool = false


func hint() -> String:
	match id:
		"arcane_bolt":
			return "LMB cast Arcane Bolt (hold to repeat) · %d mana" % int(data["mana"])
		"fireball":
			return "LMB hurl a Fireball · %d mana" % int(data["mana"])
		"chain_lightning":
			return "LMB Chain Lightning (aim at a foe) · %d mana" % int(data["mana"])
		"mending_ward":
			return "LMB cast Mending Ward: heal + halve damage · %d mana" % int(data["mana"])
	return ""


func status() -> String:
	return "Ready" if cooldown <= 0.0 else "%.1fs" % cooldown


func on_unequip() -> void:
	holding = false
	super.on_unequip()


func primary(pressed: bool) -> void:
	holding = pressed
	if pressed:
		_try_cast()


func tick(delta: float) -> void:
	cooldown -= delta
	if holding and cooldown <= 0.0 and id in ["arcane_bolt", "fireball"]:
		_try_cast()


func _try_cast() -> void:
	if cooldown > 0.0 or player.dead:
		return
	if not player.spend_mana(float(data["mana"])):
		Events.toast("Not enough mana", "warn")
		AudioManager.play_2d("mana_empty", -4.0)
		cooldown = 0.35
		return
	cooldown = float(data["cooldown"])
	var col: Color = data["color"]
	var from := player.viewmodel.muzzle_position()
	var mult := Game.spell_damage_mult()
	player.viewmodel.cast_push(1.0)
	match id:
		"arcane_bolt":
			var dir := (player.aim_point(120.0) - from).normalized()
			Projectile.spawn(player, from, dir * float(data["speed"]), {"damage": float(data["damage"]) * mult, "damage_type": "arcane",
				"color": col, "size": 0.16, "from_player": true, "source": player, "lifetime": 2.5})
			AudioManager.play_2d("spell_arcane_cast", -3.0)
			VFX.sparkle(player, from, col, 5, 0.18)
		"fireball":
			var dir2 := (player.aim_point(120.0) - from).normalized()
			Projectile.spawn(player, from, dir2 * float(data["speed"]), {"damage": float(data["damage"]) * mult, "damage_type": "fire",
				"splash_damage": float(data["splash"]) * mult, "splash_radius": float(data["radius"]), "color": col, "size": 0.32,
				"from_player": true, "source": player, "lifetime": 3.0, "gravity": 2.0})
			AudioManager.play_2d("spell_fireball_cast", -2.0)
			VFX.burst(player, from, col, 8, 2.0, 0.12, 0.3, 0.0, "spark")
		"chain_lightning":
			_chain(from, col, mult)
		"mending_ward":
			player.add_heal_over_time(float(data["heal"]), float(data["duration"]))
			player.ward_timer = float(data["duration"]) + 1.0
			AudioManager.play_2d("spell_heal", -2.0)
			var feet := player.global_position + Vector3.UP * 0.1
			VFX.ring(player, feet, col, 3.0, 0.7)
			VFX.sparkle(player, player.global_position + Vector3.UP * 1.0, col, 20, 0.35)
			_rune_circle(feet, col)


func _chain(from: Vector3, col: Color, mult: float) -> void:
	var rng := float(data["range"])
	var first: Node3D = null
	var hit := player.aim_ray(rng, 1 | 4 | 8)
	if hit and Combat.is_enemy(hit["collider"]):
		first = hit["collider"]
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
		var info := DamageInfo.make(dmg * pow(0.85, i), "shock", player, ap, (ap - prev_pos).normalized(), 1.0, true)
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
