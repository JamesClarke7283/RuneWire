class_name WeaponGun
extends EquipBase
## Tech weapons: Arc Pistol (hitscan shock), Rivet Repeater (auto rivets), Boom Mortar (bouncing bombs).

var mag: int = -1
var reloading: bool = false
var reload_t: float = 0.0
var fire_t: float = 0.0
var trigger: bool = false


func on_equip() -> void:
	super.on_equip()
	if mag < 0:
		mag = int(data["mag"])


func on_unequip() -> void:
	trigger = false
	super.on_unequip()


func hint() -> String:
	return "LMB fire · R reload · %s damage" % str(data["damage_type"]).capitalize()


func status() -> String:
	if reloading:
		return "Reloading..."
	return "%d / %d" % [mag, int(data["mag"])]


func primary(pressed: bool) -> void:
	trigger = pressed
	if pressed and mag == 0:
		reload()


func reload() -> void:
	if reloading or mag == int(data["mag"]):
		return
	reloading = true
	reload_t = float(data["reload"])
	AudioManager.play_2d("reload", -4.0)
	player.viewmodel.kick(0.0, -25.0)


func tick(delta: float) -> void:
	fire_t -= delta
	if reloading:
		reload_t -= delta
		if reload_t <= 0.0:
			reloading = false
			mag = int(data["mag"])
		return
	if trigger and fire_t <= 0.0:
		if mag > 0:
			_fire()
			fire_t = 1.0 / float(data["fire_rate"])
			if id == "arc_pistol":
				trigger = trigger  # semi-auto feel comes from the fire rate
		else:
			reload()


func _fire() -> void:
	mag -= 1
	var col: Color = data["color"]
	var from := player.viewmodel.muzzle_position()
	var dmg := float(data["damage"]) * Game.weapon_damage_mult()
	var spread_deg := float(data.get("spread", 0.0))
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	if spread_deg > 0.0:
		var s := deg_to_rad(spread_deg)
		fwd = fwd.rotated(cam.global_transform.basis.x, randf_range(-s, s)).rotated(cam.global_transform.basis.y, randf_range(-s, s))
	match id:
		"arc_pistol":
			var rng := float(data["range"])
			var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + fwd * rng, 1 | 4 | 8 | 128)
			q.exclude = [player.get_rid()]
			var hit := player.get_world_3d().direct_space_state.intersect_ray(q)
			var end := cam.global_position + fwd * rng
			if hit:
				end = hit["position"]
				Combat.damage_hit(hit, DamageInfo.make(dmg, "shock", player, end, fwd, 1.5, true))
				VFX.burst(player, end, col, 8, 4.0, 0.12, 0.3, -6.0, "spark", 70.0, hit["normal"])
			VFX.lightning(player, from, end, col, 5, 0.12, 0.08)
			player.viewmodel.kick(0.035, 8.0)
			AudioManager.play_2d("gun_arc_pistol", -3.0)
		"rivet_repeater":
			var target := cam.global_position + fwd * 200.0
			var q2 := PhysicsRayQueryParameters3D.create(cam.global_position, target, 1 | 4 | 8)
			q2.exclude = [player.get_rid()]
			var hit2 := player.get_world_3d().direct_space_state.intersect_ray(q2)
			if hit2:
				target = hit2["position"]
			Projectile.spawn(player, from, (target - from).normalized() * float(data["speed"]), {"damage": dmg, "damage_type": "kinetic",
				"color": col, "size": 0.06, "kind": "rivet", "from_player": true, "source": player, "lifetime": 1.5, "trail": false})
			player.viewmodel.kick(0.02, 3.5)
			AudioManager.play_2d("gun_rivet", -6.0, 1.0, 0.08)
		"boom_mortar":
			var dir := (fwd + Vector3.UP * 0.12).normalized()
			Projectile.spawn(player, from, dir * float(data["speed"]) + player.velocity * 0.5, {"damage": dmg, "damage_type": "fire",
				"splash_damage": float(data["splash"]) * Game.weapon_damage_mult(), "splash_radius": float(data["radius"]),
				"color": col, "size": 0.16, "kind": "bomb", "from_player": true, "source": player, "lifetime": 3.0,
				"gravity": float(data["gravity"]), "bounces": 1, "fuse": 2.2})
			player.viewmodel.kick(0.07, 14.0)
			player.shake(0.2, 0.12)
			AudioManager.play_2d("gun_mortar", -2.0)
	VFX.muzzle(player, from, col, 0.14)
