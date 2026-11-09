class_name TeslaLance
extends WeaponGun
## Tesla Lance: hold LMB to charge the capacitor, release to fire a hitscan lightning bolt that pierces
## several foes. Damage scales from 30% (tap) to 100% (full charge); a full charge also shocks harder.

var charging: bool = false
var charge: float = 0.0
var _charge_sound_t: float = 0.0


func hint() -> String:
	return "Hold LMB to charge, release to fire · pierces %d foes · R reload" % (int(data.get("pierce", 2)) + 1)


func status() -> String:
	if reloading:
		return "Reloading..."
	if charging:
		return "Charge %d%%  ·  %d / %d" % [int(charge * 100.0), mag, mag_size()]
	return "%d / %d" % [maxi(mag, 0), mag_size()]


func on_unequip() -> void:
	charging = false
	charge = 0.0
	if player and player.viewmodel:
		player.viewmodel.set_charge(0.0)
	super.on_unequip()


func primary(pressed: bool) -> void:
	if pressed:
		if reloading or fire_t > 0.0:
			return
		if mag <= 0:
			reload()
			return
		charging = true
		charge = 0.0
		_charge_sound_t = 0.0
		AudioManager.play_2d("lance_charge", -1.0)
	elif charging:
		charging = false
		if charge >= 0.12:
			_discharge()
		charge = 0.0
		player.viewmodel.set_charge(0.0)


func tick(delta: float) -> void:
	fire_t -= delta
	if reloading:
		reload_t -= delta
		if reload_t <= 0.0:
			reloading = false
			mag = mag_size()
		return
	if charging:
		charge = minf(1.0, charge + delta / maxf(float(data.get("charge", 1.0)), 0.1))
		player.viewmodel.set_charge(charge)
		player.viewmodel.set_tilt(sin(Time.get_ticks_msec() / 25.0) * 0.01 * charge)
		if charge >= 1.0:
			_charge_sound_t -= delta
			if _charge_sound_t <= 0.0:
				_charge_sound_t = 0.4
				VFX.burst(player, player.viewmodel.muzzle_position(), data.get("color", Color.CYAN), 3, 1.5, 0.06, 0.2, 0.0, "spark")


func _discharge() -> void:
	mag -= 1
	fire_t = 1.0 / maxf(float(data.get("fire_rate", 1.5)), 0.1)
	var col: Color = data.get("color", Color(0.45, 0.95, 1.0))
	var full := charge >= 0.98
	var dmg := float(data.get("damage", 60.0)) * player.damage_mult("tech") * (0.3 + 0.7 * charge) * (1.15 if full else 1.0)
	var cam := player.camera
	var fwd := -cam.global_transform.basis.z
	var from := player.viewmodel.muzzle_position()
	var rng := float(data.get("range", 150.0))
	var space := player.get_world_3d().direct_space_state
	var start := cam.global_position
	var ex: Array[RID] = [player.get_rid()]
	var end := start + fwd * rng
	var hits := 0
	var max_hits := int(data.get("pierce", 2)) + 1
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(start, cam.global_position + fwd * rng, 1 | 4 | 8 | 128)
		q.exclude = ex
		var h := space.intersect_ray(q)
		if h.is_empty():
			break
		Combat.damage_hit(h, hit(dmg * pow(0.85, hits), "shock", h["position"], fwd, 3.0 if full else 1.5))
		VFX.burst(player, h["position"], col, 10, 5.0, 0.14, 0.35, -6.0, "spark", 80.0, h["normal"])
		if Combat.is_enemy(h["collider"]) and hits + 1 < max_hits:
			hits += 1
			ex.append((h["collider"] as CollisionObject3D).get_rid())
			start = h["position"]
			continue
		end = h["position"]
		break
	VFX.lightning(player, from, end, col, 12, 0.35 if full else 0.2, 0.22)
	VFX.beam(player, from, end, col.lerp(Color.WHITE, 0.5), 0.05 if full else 0.03, 0.18)
	VFX.flash_light(player, from, col, 3.0, 6.0, 0.2)
	player.viewmodel.kick(0.08 if full else 0.05, 12.0 if full else 7.0)
	player.shake(0.25 if full else 0.12, 0.15)
	AudioManager.play_2d("lance_fire", -1.0 if full else -4.0, 1.0 if full else 1.15)
	VFX.muzzle(player, from, col, 0.3 if full else 0.18)
