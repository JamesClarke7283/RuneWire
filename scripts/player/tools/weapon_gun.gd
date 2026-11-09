class_name WeaponGun
extends EquipBase
## Tech guns. Each one fires by its "fire" mode:
##   hitscan    Arc Pistol (shock bolt), Brass Longshot (rifle; hold RMB to zoom, scoped shots +25%)
##   projectile Rivet Repeater (full-auto rivets)
##   gatling    Steamroller Gatling (spins up while LMB is held, slows you down)
##   lob        Boom Mortar (bouncing bombs)
##   pellets    Cogburst Scattergun
##   flame      Bellows Flamethrower (a short cone of fire that sets foes ablaze)
##   bolt       Clockwork Crossbow (heavy piercing bolts with a little drop)
## Stats come from the weapon instance, so rarity, level and perks (magazine, reload, spread...) all
## apply. The Tesla Lance (charge) extends this class.

const ZOOM_FOV := 0.42

var mag: int = -1
var reloading: bool = false
var reload_t: float = 0.0
var fire_t: float = 0.0
var trigger: bool = false
var zoomed: bool = false
var spin: float = 0.0           # gatling barrel speed, 0..1
var _spin_snd: bool = false
var _loop_snd_t: float = 0.0


func fire_mode() -> String:
	return str(data.get("fire", "hitscan"))


func mag_size() -> int:
	return maxi(1, int(data.get("mag", 1)))


func reload_time() -> float:
	return float(data.get("reload", 1.5)) * Game.reload_mult() * (0.8 if player and player.has_buff("oiled") else 1.0)


func on_equip() -> void:
	super.on_equip()
	if mag < 0:
		mag = mag_size()
	mag = mini(mag, mag_size())
	if fire_mode() == "bolt":
		player.viewmodel.show_part("Bolt", mag > 0)


func on_unequip() -> void:
	trigger = false
	_set_zoom(false)
	spin = 0.0
	_spin_snd = false
	if player:
		player.weapon_slow = 0.0
	super.on_unequip()


func hint() -> String:
	match fire_mode():
		"hitscan":
			if bool(data.get("scope", false)):
				return "LMB fire · hold RMB to zoom (scoped shots fly true, +25% damage) · R reload"
		"gatling":
			return "Hold LMB to spin up and fire · you walk slower while it roars · R reload"
		"flame":
			return "Hold LMB to spray fire: sets foes ablaze (wisps are immune) · R refuel"
		"bolt":
			return "LMB loose a bolt: pierces a foe, crits often · R reload"
		"lob":
			return "LMB lob a bouncing bomb · R reload"
	return "LMB fire · R reload · %s damage" % str(data.get("damage_type", "")).capitalize()


func status() -> String:
	if reloading:
		return "Refuelling..." if fire_mode() == "flame" else "Reloading..."
	if fire_mode() == "flame":
		return "Fuel %d%%" % int(100.0 * float(maxi(mag, 0)) / float(mag_size()))
	if fire_mode() == "gatling" and spin > 0.05:
		return "%d / %d  ·  %d%% spin" % [maxi(mag, 0), mag_size(), int(spin * 100.0)]
	return "%d / %d" % [maxi(mag, 0), mag_size()]


func meter() -> float:
	if reloading:
		return 1.0 - reload_t / maxf(reload_time(), 0.01)
	return float(maxi(mag, 0)) / float(mag_size())


func primary(pressed: bool) -> void:
	trigger = pressed
	if pressed and mag == 0:
		reload()
	if not pressed:
		_spin_snd = false


func secondary(pressed: bool) -> void:
	if bool(data.get("scope", false)):
		_set_zoom(pressed and not reloading)


func _set_zoom(on: bool) -> void:
	if zoomed == on or player == null:
		return
	zoomed = on
	player.set_zoom(ZOOM_FOV if on else 1.0)
	if on:
		AudioManager.play_2d("scope_zoom", -8.0)


func reload() -> void:
	if reloading or mag >= mag_size():
		return
	reloading = true
	reload_t = reload_time()
	_set_zoom(false)
	AudioManager.play_2d("crossbow_reload" if fire_mode() == "bolt" else "reload", -4.0)
	player.viewmodel.kick(0.0, -25.0)


func tick(delta: float) -> void:
	fire_t -= delta
	if fire_mode() == "gatling":
		_tick_spin(delta)
	if reloading:
		reload_t -= delta
		if reload_t <= 0.0:
			reloading = false
			mag = mag_size()
			if fire_mode() == "bolt":
				player.viewmodel.show_part("Bolt", true)
		return
	if trigger and fire_t <= 0.0:
		if mag > 0:
			if fire_mode() == "gatling" and spin < 0.25:
				return
			_fire()
			var rate := float(data.get("fire_rate", 2.0))
			if fire_mode() == "gatling":
				rate *= lerpf(0.25, 1.0, spin)
			if player.has_buff("oiled"):
				rate *= 1.1
			fire_t = 1.0 / maxf(rate, 0.1)
		else:
			reload()


## Gatling: the barrels spin up while LMB is held and wind down when released.
func _tick_spin(delta: float) -> void:
	var want := 1.0 if trigger and not reloading and mag > 0 else 0.0
	var spinup := maxf(float(data.get("spinup", 1.0)), 0.1)
	spin = move_toward(spin, want, delta / (spinup if want > spin else spinup * 0.7))
	player.viewmodel.spin_barrels(spin)
	player.weapon_slow = float(data.get("move_slow", 0.3)) * spin if trigger else 0.0
	if trigger and want > 0.0 and not _spin_snd and spin < 0.6:
		_spin_snd = true
		AudioManager.play_2d("gatling_spin", -5.0)


func _aim_dir(spread_deg: float) -> Vector3:
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	if spread_deg > 0.0:
		var s := deg_to_rad(spread_deg)
		fwd = fwd.rotated(cam.global_transform.basis.x, randf_range(-s, s)).rotated(cam.global_transform.basis.y, randf_range(-s, s))
	return fwd.normalized()


func _fire() -> void:
	mag -= 1
	var col: Color = data.get("color", Color(1, 0.8, 0.4))
	var from := player.viewmodel.muzzle_position()
	var dmg := float(data.get("damage", 10.0)) * player.damage_mult("tech")
	var spread_deg := float(data.get("spread", 0.0))
	if zoomed:
		spread_deg = 0.0
		dmg *= 1.25
	var rng := float(data.get("range", 100.0))
	var sfx := str(data.get("sfx", "gun_rivet"))
	match fire_mode():
		"hitscan":
			_fire_hitscan(from, dmg, spread_deg, rng, col)
			if bool(data.get("scope", false)):
				player.viewmodel.kick(0.06, 13.0)
				player.shake(0.12, 0.1)
				AudioManager.play_2d(sfx, -1.0, 1.0, 0.04)
			else:
				player.viewmodel.kick(0.035, 8.0)
				AudioManager.play_2d(sfx, -3.0)
		"projectile", "gatling":
			var fwd2 := _aim_dir(spread_deg * (1.0 if fire_mode() == "projectile" else lerpf(1.6, 1.0, spin)))
			var target := _aim_target(fwd2, 200.0)
			Projectile.spawn(player, from, (target - from).normalized() * float(data.get("speed", 90.0)), {"damage": dmg,
				"damage_type": str(data.get("damage_type", "kinetic")), "color": col, "size": 0.06, "kind": "rivet",
				"from_player": true, "source": player, "lifetime": 1.5, "trail": false, "weapon": data})
			player.viewmodel.kick(0.02 if fire_mode() == "projectile" else 0.012, 3.5 if fire_mode() == "projectile" else 2.0)
			if fire_mode() == "projectile":
				player.viewmodel.spin_drum(1.0)
				AudioManager.play_2d(sfx, -6.0, 1.0, 0.08)
			else:
				AudioManager.play_2d(sfx, -9.0, 1.0, 0.06)
		"lob":
			var dir := (_aim_dir(0.0) + Vector3.UP * 0.12).normalized()
			Projectile.spawn(player, from, dir * float(data.get("speed", 26.0)) + player.velocity * 0.5, {"damage": dmg,
				"damage_type": "fire", "splash_damage": float(data.get("splash", 50.0)) * player.damage_mult("tech"),
				"splash_radius": float(data.get("radius", 5.0)), "color": col, "size": 0.16, "kind": "bomb", "from_player": true,
				"source": player, "lifetime": 3.0, "gravity": float(data.get("gravity", 14.0)), "bounces": 1, "fuse": 2.2,
				"weapon": data})
			player.viewmodel.kick(0.07, 14.0)
			player.shake(0.2, 0.12)
			AudioManager.play_2d(sfx, -2.0)
		"pellets":
			_fire_pellets(from, dmg, spread_deg, rng, col)
			player.viewmodel.kick(0.09, 16.0)
			player.viewmodel.pump(0.35)
			player.shake(0.18, 0.12)
			AudioManager.play_2d(sfx, -2.0, 1.0, 0.05)
			if mag > 0:
				get_tree().create_timer(0.32).timeout.connect(func():
					if active:
						AudioManager.play_2d("scatter_pump", -6.0))
		"flame":
			_fire_flame(from, dmg, rng, col)
			return
		"bolt":
			var fwd3 := _aim_dir(spread_deg)
			var target3 := _aim_target(fwd3, rng)
			var v := (target3 - from).normalized() * float(data.get("speed", 70.0))
			Projectile.spawn(player, from, v + Vector3.UP * float(data.get("gravity", 5.0)) * 0.04 * from.distance_to(target3) / 10.0, {
				"damage": dmg, "damage_type": str(data.get("damage_type", "kinetic")), "color": col, "size": 0.09, "kind": "rivet",
				"from_player": true, "source": player, "lifetime": 2.5, "gravity": float(data.get("gravity", 5.0)), "trail": true,
				"pierce": int(data.get("pierce", 1)), "knockback": 4.0, "weapon": data})
			player.viewmodel.kick(0.05, 9.0)
			player.viewmodel.show_part("Bolt", false)
			if mag > 0:
				get_tree().create_timer(0.35).timeout.connect(func():
					if active and not reloading:
						player.viewmodel.show_part("Bolt", true))
			AudioManager.play_2d(sfx, -3.0, 1.0, 0.06)
	VFX.muzzle(player, from, col, 0.26 if fire_mode() == "pellets" else (0.08 if fire_mode() == "gatling" else 0.14))


## Where the crosshair ray (camera forward, given spread) meets the world, up to `dist`.
func _aim_target(fwd: Vector3, dist: float) -> Vector3:
	var cam := player.camera
	var target := cam.global_position + fwd * dist
	var q := PhysicsRayQueryParameters3D.create(cam.global_position, target, 1 | 4 | 8)
	q.exclude = [player.get_rid()]
	var h := player.get_world_3d().direct_space_state.intersect_ray(q)
	return h["position"] if h else target


func _fire_hitscan(from: Vector3, dmg: float, spread_deg: float, rng: float, col: Color) -> void:
	var cam := player.camera
	var fwd := _aim_dir(spread_deg)
	var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + fwd * rng, 1 | 4 | 8 | 128)
	q.exclude = [player.get_rid()]
	var hit_r := player.get_world_3d().direct_space_state.intersect_ray(q)
	var end := cam.global_position + fwd * rng
	var dtype := str(data.get("damage_type", "shock"))
	if hit_r:
		end = hit_r["position"]
		Combat.damage_hit(hit_r, hit(dmg, dtype, end, fwd, 1.5 if dtype == "shock" else 3.0))
		VFX.burst(player, end, col, 8, 4.0, 0.12, 0.3, -6.0, "spark", 70.0, hit_r["normal"])
	if str(data.get("tracer", "lightning")) == "lightning":
		VFX.lightning(player, from, end, col, 5, 0.12, 0.08)
	else:
		VFX.beam(player, from, end, col.lerp(Color.WHITE, 0.4), 0.025, 0.14)
		VFX.flash_light(player, from, col, 2.0, 5.0, 0.12)


## Scattergun: several hitscan pellets in a cone; hits on the same enemy add up into one number.
func _fire_pellets(from: Vector3, dmg: float, spread_deg: float, rng: float, col: Color) -> void:
	var cam := player.camera
	var space := player.get_world_3d().direct_space_state
	var per_target := {}
	for i in int(data.get("pellets", 8)):
		var fwd := _aim_dir(spread_deg)
		var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + fwd * rng, 1 | 4 | 8 | 128)
		q.exclude = [player.get_rid()]
		var h := space.intersect_ray(q)
		var end := cam.global_position + fwd * rng
		if h:
			end = h["position"]
			# damage falls off past a third of the range
			var d := cam.global_position.distance_to(end)
			var fall := clampf(1.25 - d / rng, 0.35, 1.0)
			var key := str(h["collider"].get_instance_id()) + ":" + str(h.get("shape", 0))
			if not per_target.has(key):
				per_target[key] = {"hit": h, "amount": 0.0, "pos": end, "dir": fwd}
			per_target[key]["amount"] += dmg * fall
			VFX.burst(player, end, col, 3, 3.0, 0.1, 0.25, -6.0, "spark", 70.0, h["normal"])
		if i % 3 == 0:
			VFX.beam(player, from, end, col.lerp(Color.WHITE, 0.3), 0.012, 0.06)
	for key in per_target:
		var t: Dictionary = per_target[key]
		Combat.damage_hit(t["hit"], hit(float(t["amount"]), "kinetic", t["pos"], t["dir"], 4.0))


## Flamethrower: every foe inside the cone (with line of sight) takes fire damage and catches fire.
func _fire_flame(from: Vector3, dmg: float, rng: float, col: Color) -> void:
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	var cone := cos(deg_to_rad(float(data.get("cone", 14.0)) + 6.0))
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.get("dead"):
			continue
		var ap: Vector3 = e.aim_point()
		var to := ap - cam.global_position
		var d := to.length()
		if d > rng + 0.8 or d < 0.01:
			continue
		if to.normalized().dot(fwd) < cone and d > 1.6:
			continue
		if not Combat.has_los(player, cam.global_position, ap, [e]):
			continue
		e.apply_damage(hit(dmg * clampf(1.2 - d / (rng * 1.6), 0.5, 1.0), "fire", ap, fwd, 0.6))
	# visible jet: a fan of embers plus soft smoke at the far end
	VFX.burst(player, from + fwd * 0.25, col, 7, rng * 1.9, 0.32, 0.45, 2.5, "spark", float(data.get("cone", 14.0)), fwd)
	if randf() < 0.35:
		VFX.burst(player, from + fwd * rng * 0.6, Color(1.0, 0.85, 0.4), 3, 3.0, 0.5, 0.35, 3.0, "spark", 60.0, fwd)
	if randf() < 0.2:
		VFX.puffs(player, from + fwd * rng * 0.8, Color(0.35, 0.32, 0.3), 2, 0.6, 0.9, 2.0)
	player.viewmodel.kick(0.004, 0.6)
	_loop_snd_t -= 1.0 / maxf(float(data.get("fire_rate", 10.0)), 0.1)
	if _loop_snd_t <= 0.0:
		_loop_snd_t = 0.3
		AudioManager.play_2d(str(data.get("sfx", "flamer_burst")), -6.0, 1.0, 0.0)
