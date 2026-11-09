class_name Player
extends CharacterBody3D
## First-person Runewright: movement, camera, health/mana/stamina, interaction, the hotbar
## (slots 1-2 weapons from the inventory, 3-4 tools, 5-8 quick-use items), consumables and buffs,
## and piloting contraptions (with a third-person chase camera).

signal health_changed(hp: float, max_hp: float)
signal mana_changed(mp: float, max_mp: float)
signal stamina_changed(st: float, max_st: float)
signal equipment_switched(id: String)
signal interact_hint_changed(text: String)
signal aim_info_changed(text: String)
signal buffs_changed
signal died
signal respawned

## Selectable hotbar slots: 0-1 weapon slots, 2-3 tools. Slots 4-7 are quick-use items.
const SELECT_SLOTS := 4

const WALK := 5.4
const SPRINT := 8.9
const CROUCH_SPEED := 2.7
const SWIM := 3.6
const ACCEL := 13.0
const AIR_ACCEL := 3.2
const JUMP := 7.0
const GRAVITY := 19.5
const EYE := 1.62
const CROUCH_EYE := 1.05
const MAX_STAMINA := 100.0
const INTERACT_RANGE := 3.4

var head: Node3D
var camera: Camera3D
var viewmodel: Viewmodel
var chase_pivot: Node3D
var collision: CollisionShape3D
var capsule: CapsuleShape3D

var health: float = 100.0
var mana: float = 100.0
var stamina: float = MAX_STAMINA
var god_mode: bool = false
var dead: bool = false
var input_enabled: bool = true
var yaw: float = 0.0
var pitch: float = 0.0
var slot: int = 0
var current: EquipBase = null
var current_id: String = ""      # weapon base or tool id of the selected slot
var current_uid: int = 0         # weapon instance uid of the selected slot (0 for tools / empty)
var handlers: Dictionary = {}    # "w<uid>" or tool id -> EquipBase
var buffs: Dictionary = {}       # buff id -> seconds left
var weapon_slow: float = 0.0     # 0..1 movement penalty set by the weapon in hand (Steamroller Gatling)
var zoom: float = 1.0            # FOV multiplier target (Brass Longshot scope)
var _zoom_cur: float = 1.0
var _last_weapon_slot: int = 0

var piloting: Contraption = null
var seat_part: Part = null
var third_person: bool = true
var chase_yaw: float = 0.0
var chase_pitch: float = -0.25
var chase_dist: float = 9.0

var ward_timer: float = 0.0
var heal_pool: float = 0.0
var heal_rate: float = 0.0
var last_damage_time: float = -100.0
var interact_target: Object = null
var interact_text: String = ""
var aim_text: String = ""

var _coyote: float = 0.0
var _jump_buffer: float = 0.0
var _crouching: bool = false
var _eye_height: float = EYE
var _bob_t: float = 0.0
var _step_dist: float = 0.0
var _land_dip: float = 0.0
var _prev_vy: float = 0.0
var _shake: float = 0.0
var _shake_time: float = 0.0
var _fov_kick: float = 0.0
var _swimming: bool = false
var _was_on_floor: bool = true
var _world: Node = null


func _ready() -> void:
	add_to_group("player")
	collision_layer = 2
	collision_mask = 1 | 4 | 8
	floor_max_angle = deg_to_rad(50.0)
	floor_snap_length = 0.4
	safe_margin = 0.02
	capsule = CapsuleShape3D.new()
	capsule.radius = 0.36
	capsule.height = 1.78
	collision = CollisionShape3D.new()
	collision.shape = capsule
	collision.position.y = 0.89
	add_child(collision)
	head = Node3D.new()
	head.name = "Head"
	head.position.y = EYE
	add_child(head)
	camera = Camera3D.new()
	camera.name = "Camera"
	camera.near = 0.05
	camera.far = 900.0
	camera.fov = Settings.fov
	head.add_child(camera)
	camera.add_child(OutlineOverlay.new())
	viewmodel = Viewmodel.new()
	viewmodel.name = "Viewmodel"
	camera.add_child(viewmodel)
	chase_pivot = Node3D.new()
	chase_pivot.name = "ChasePivot"
	add_child(chase_pivot)
	chase_pivot.top_level = true
	health = Game.max_health() if Game.player_health <= 0.0 else minf(Game.player_health, Game.max_health())
	mana = Game.max_mana() if Game.player_mana < 0.0 else minf(Game.player_mana, Game.max_mana())
	Settings.changed.connect(func(): camera.fov = Settings.fov)
	Game.equipment_changed.connect(_on_equipment_changed)
	Game.pack_overflow.connect(_on_pack_overflow)
	Events.screen_shake.connect(shake)
	_world = get_tree().get_first_node_in_group("world")
	select_slot(_first_filled_slot(), true)
	_emit_stats()


func _emit_stats() -> void:
	health_changed.emit(health, Game.max_health())
	mana_changed.emit(mana, Game.max_mana())
	stamina_changed.emit(stamina, MAX_STAMINA)


func teleport(pos: Vector3, yaw_deg: float = NAN, pitch_deg: float = 0.0) -> void:
	if piloting:
		exit_seat()
	global_position = pos
	velocity = Vector3.ZERO
	if not is_nan(yaw_deg):
		yaw = deg_to_rad(yaw_deg)
		pitch = deg_to_rad(pitch_deg)
	_apply_look()


# ------------------------------------------------------------------ input
func _unhandled_input(event: InputEvent) -> void:
	if dead or not input_enabled:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var rel: Vector2 = event.relative * Settings.mouse_sensitivity * 0.01
		if Settings.invert_y:
			rel.y = -rel.y
		if piloting and third_person:
			chase_yaw -= rel.x
			chase_pitch = clampf(chase_pitch - rel.y, -1.2, 0.35)
			return
		if current and current.mouse_motion(event.relative):
			return
		yaw -= rel.x
		pitch = clampf(pitch - rel.y, deg_to_rad(-88), deg_to_rad(88))
		_apply_look()
		if viewmodel:
			viewmodel.add_sway(event.relative)
		return
	if piloting:
		_pilot_input(event)
		return
	if event.is_action_pressed("primary"):
		if current:
			current.primary(true)
	elif event.is_action_released("primary"):
		if current:
			current.primary(false)
	elif event.is_action_pressed("secondary"):
		if current:
			current.secondary(true)
	elif event.is_action_released("secondary"):
		if current:
			current.secondary(false)
	elif event.is_action_pressed("reload"):
		if current:
			current.reload()
	elif event.is_action_pressed("next_slot"):
		if not (current and current.scroll(1)):
			cycle_slot(1)
	elif event.is_action_pressed("prev_slot"):
		if not (current and current.scroll(-1)):
			cycle_slot(-1)
	elif event.is_action_pressed("quick_swap"):
		quick_swap()
	elif event.is_action_pressed("interact"):
		_do_interact()
	elif event.is_action_pressed("use_health"):
		use_consumable("health_tonic")
	elif event.is_action_pressed("use_mana"):
		use_consumable("mana_draught")
	elif event.is_action_pressed("undo"):
		var bm := _build_manager()
		if bm:
			bm.undo()
	else:
		for i in 8:
			if event.is_action_pressed("slot_%d" % (i + 1)):
				if i < SELECT_SLOTS:
					select_slot(i, false, true)
				else:
					use_quick(i - SELECT_SLOTS)
				break


func _pilot_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		exit_seat()
	elif event.is_action_pressed("toggle_view"):
		third_person = not third_person
		_update_camera_mode()
	elif event.is_action_pressed("lights"):
		piloting.toggle_lights()
	elif event.is_action_pressed("next_slot"):
		chase_dist = clampf(chase_dist + 1.0, 4.0, 22.0)
	elif event.is_action_pressed("prev_slot"):
		chase_dist = clampf(chase_dist - 1.0, 4.0, 22.0)


func _apply_look() -> void:
	rotation = Vector3(0, yaw, 0)
	head.rotation = Vector3(pitch, 0, 0)


# ------------------------------------------------------------------ equipment
## Handler key of a weapon instance (tools use their own id).
static func weapon_key(uid: int) -> String:
	return "w:%d" % uid


## What a selectable hotbar slot holds: {"key", "id", "uid", "weapon"} or {} when it is empty.
func slot_entry(i: int) -> Dictionary:
	if i < Game.WEAPON_SLOTS:
		var w := Game.loadout_weapon(i)
		if w.is_empty():
			return {}
		return {"key": weapon_key(int(w["uid"])), "id": str(w["base"]), "uid": int(w["uid"]), "weapon": w}
	var t := i - Game.WEAPON_SLOTS
	if t >= 0 and t < Catalog.TOOL_SLOTS.size():
		var tid: String = Catalog.TOOL_SLOTS[t]
		return {"key": tid, "id": tid, "uid": 0, "weapon": {}}
	return {}


func _first_filled_slot() -> int:
	for i in SELECT_SLOTS:
		if not slot_entry(i).is_empty():
			return i
	return Game.WEAPON_SLOTS


## Select hotbar slot i (0-3). `from_key`: a key press on an empty weapon slot explains how to fill it.
func select_slot(i: int, force: bool = false, from_key: bool = false) -> void:
	i = clampi(i, 0, SELECT_SLOTS - 1)
	var e := slot_entry(i)
	if e.is_empty():
		if from_key:
			Events.toast("Weapon slot %d is empty. Open your Inventory [I] to equip a weapon." % (i + 1), "info")
			AudioManager.play_ui("ui_error", -10.0)
		if not force:
			return
		i = _first_filled_slot()
		e = slot_entry(i)
	if i == slot and not force and current and e.get("key", "") == _current_key():
		return
	slot = i
	if i < Game.WEAPON_SLOTS:
		_last_weapon_slot = i
	if current:
		current.on_unequip()
	current = _handler_for(e)
	current_id = str(e.get("id", ""))
	current_uid = int(e.get("uid", 0))
	if current:
		current.on_equip()
	var model: String = Catalog.equipment(current_id).get("model", "")
	viewmodel.show_model(model, current_id, e.get("weapon", {}))
	equipment_switched.emit(current_id)
	AudioManager.play_2d("ui_click", -10.0, 1.4)


func _current_key() -> String:
	return weapon_key(current_uid) if current_uid > 0 else current_id


## Mouse wheel: step through the filled selectable slots.
func cycle_slot(dir: int) -> void:
	for step in range(1, SELECT_SLOTS + 1):
		var j := wrapi(slot + dir * step, 0, SELECT_SLOTS)
		if not slot_entry(j).is_empty():
			select_slot(j)
			return


## X: jump between the two weapon slots (or back to the last weapon from a tool).
func quick_swap() -> void:
	var target := _last_weapon_slot
	if slot < Game.WEAPON_SLOTS:
		target = 1 - slot
	if slot_entry(target).is_empty():
		target = 1 - target
	if not slot_entry(target).is_empty() and target != slot:
		select_slot(target)


func _handler_for(e: Dictionary) -> EquipBase:
	if e.is_empty():
		return null
	var key: String = e["key"]
	var base: String = e["id"]
	var data: Dictionary
	if int(e.get("uid", 0)) > 0:
		data = Catalog.weapon_stats(e["weapon"])
	else:
		data = Catalog.equipment(base)
	if handlers.has(key):
		var existing: EquipBase = handlers[key]
		existing.data = data
		return existing
	var h: EquipBase
	match base:
		"gauntlet":
			h = GauntletTool.new()
		"toolkit":
			h = ToolkitTool.new()
		"tesla_lance":
			h = TeslaLance.new()
		_:
			match data.get("kind", ""):
				"spell":
					h = SpellCaster.new()
				"melee":
					h = MeleeWeapon.new()
				_:
					h = WeaponGun.new()
	h.player = self
	h.id = base
	h.uid = int(e.get("uid", 0))
	h.data = data
	h.name = "Equip_" + key
	add_child(h)
	handlers[key] = h
	return h


## Handler for a weapon instance (creates it if needed) - used by tests and the inventory.
func handler_for_weapon(uid: int) -> EquipBase:
	var w := Game.get_weapon(uid)
	if w.is_empty():
		return null
	return _handler_for({"key": weapon_key(uid), "id": str(w["base"]), "uid": uid, "weapon": w})


func _on_equipment_changed() -> void:
	# drop handlers of weapons that left the inventory, refresh stats (levels, upgrades) of the rest
	for key in handlers.keys():
		if not str(key).begins_with("w:"):
			continue
		var uid := int(str(key).substr(2))
		var w := Game.get_weapon(uid)
		var h: EquipBase = handlers[key]
		if w.is_empty():
			if h == current:
				current.on_unequip()
				current = null
			handlers.erase(key)
			h.queue_free()
		else:
			h.data = Catalog.weapon_stats(w)
	# the selected slot may now hold a different weapon (equip / swap / unequip from the inventory)
	if not dead and piloting == null:
		var e := slot_entry(slot)
		if e.is_empty() or e.get("key", "") != _current_key() or current == null:
			select_slot(slot if not e.is_empty() else _first_filled_slot(), true)
	health_changed.emit(health, Game.max_health())
	mana_changed.emit(mana, Game.max_mana())


## Hotbar keys 5-8 use whatever consumable sits in that quick slot.
func use_quick(i: int) -> void:
	if i < 0 or i >= Game.quick.size():
		return
	var id: String = Game.quick[i]
	if id == "":
		Events.toast("Quick slot %d is empty. Assign an item in your Inventory [I]." % (i + 5), "info")
		AudioManager.play_ui("ui_error", -10.0)
		return
	use_consumable(id)


func use_consumable(id: String) -> bool:
	var c: Dictionary = Catalog.CONSUMABLES.get(id, {})
	if c.is_empty() or dead:
		return false
	if Game.item_count(id) <= 0:
		Events.toast("No %s left. Craft or buy more." % c["name"], "warn")
		AudioManager.play_ui("ui_error")
		return false
	match str(c.get("use", "")):
		"heal":
			if health >= Game.max_health() - 0.5:
				Events.toast("Already at full health", "info")
				return false
			heal(float(c["heal"]))
			AudioManager.play_2d("drink", -4.0)
			VFX.sparkle(self, global_position + Vector3.UP * 1.2, UIStyle.HEALTH, 10, 0.25)
		"mana":
			if mana >= Game.max_mana() - 0.5:
				Events.toast("Mana already full", "info")
				return false
			mana = minf(Game.max_mana(), mana + float(c["mana"]))
			mana_changed.emit(mana, Game.max_mana())
			AudioManager.play_2d("drink", -4.0, 1.1)
			VFX.sparkle(self, global_position + Vector3.UP * 1.2, UIStyle.MANA, 10, 0.25)
		"regen":
			if health >= Game.max_health() - 0.5 and heal_pool <= 0.0:
				Events.toast("Already at full health", "info")
				return false
			add_heal_over_time(float(c["heal"]), float(c.get("duration", 20.0)))
			AudioManager.play_2d("drink", -4.0, 0.85)
			VFX.sparkle(self, global_position + Vector3.UP * 1.2, Color(0.55, 1.0, 0.55), 14, 0.25)
		"throw":
			if piloting:
				return false
			_throw_bomb(c)
		"buff":
			if c["buff"] == "map" and nearest_treasure() == null:
				Events.toast("No treasure left that the map can find. Well done!", "info")
				return false
			add_buff(str(c["buff"]), float(c["duration"]))
			AudioManager.play_2d("drink", -4.0, 0.9)
			VFX.sparkle(self, global_position + Vector3.UP * 1.0, Catalog.BUFFS[c["buff"]]["color"], 16, 0.3)
		"repair":
			if not _repair_contraption(float(c["amount"])):
				Events.toast("Look at (or pilot) a contraption to patch it up", "info")
				return false
	Game.remove_item(id, 1)
	Events.item_used.emit(id)
	return true


func _throw_bomb(c: Dictionary) -> void:
	var from := camera.global_position - camera.global_transform.basis.z * 0.6 + Vector3.DOWN * 0.15
	var dir := (-camera.global_transform.basis.z + Vector3.UP * 0.22).normalized()
	var dmg := damage_mult("tech")
	var dtype := str(c.get("damage_type", "fire"))
	var col: Color = Combat.TYPE_COLORS.get(dtype, Color(1.0, 0.55, 0.2))
	# a pseudo-weapon so the blast can chill (Rime Bomb); it carries no perks
	var fx := {"chill": float(c["chill"]), "chill_chance": 1.0} if c.has("chill") else {}
	Projectile.spawn(self, from, dir * 19.0 + velocity * 0.6, {"damage": float(c["damage"]) * dmg, "damage_type": dtype,
		"splash_damage": float(c["splash"]) * dmg, "splash_radius": float(c["radius"]), "color": col,
		"size": 0.17, "kind": "bomb", "from_player": true, "source": self, "lifetime": 4.0, "gravity": 15.0,
		"bounces": 2, "fuse": 1.6, "weapon": fx})
	viewmodel.kick(0.0, -18.0)
	AudioManager.play_2d("bomb_throw", -3.0)


func _repair_contraption(fraction: float) -> bool:
	var c: Contraption = piloting
	if c == null:
		var hit := aim_ray(8.0, 4)
		if hit and hit["collider"] is Contraption:
			c = hit["collider"]
	if c == null or not is_instance_valid(c):
		return false
	var fixed := 0
	for p in c.parts:
		if is_instance_valid(p) and p.hp < p.max_hp:
			p.hp = minf(p.max_hp, p.hp + p.max_hp * fraction)
			fixed += 1
	VFX.weld_sparks(self, c.global_transform * c.center_of_mass)
	AudioManager.play_2d("tool_weld", -2.0, 1.1)
	Events.toast("Patched up %d part%s" % [fixed, "" if fixed == 1 else "s"], "tool")
	return true


func add_buff(id: String, duration: float) -> void:
	buffs[id] = maxf(float(buffs.get(id, 0.0)), duration)
	buffs_changed.emit()
	Events.toast("%s for %d s" % [Catalog.BUFFS[id]["name"], int(duration)], "item")


## Nearest unopened treasure chest (vaults count only while carrying a Ley Key), or null.
func nearest_treasure() -> Variant:
	var has_key := Game.item_count("ley_key") > 0
	var best: Variant = null
	var best_d := INF
	for c in get_tree().get_nodes_in_group("chests"):
		if c.opened or (c.vault and not has_key):
			continue
		var d: float = (c as Node3D).global_position.distance_to(global_position)
		if d < best_d:
			best_d = d
			best = (c as Node3D).global_position
	return best


func has_buff(id: String) -> bool:
	return float(buffs.get(id, 0.0)) > 0.0


func _tick_buffs(delta: float) -> void:
	if buffs.is_empty():
		return
	var ended := false
	for b in buffs.keys():
		buffs[b] = float(buffs[b]) - delta
		if float(buffs[b]) <= 0.0:
			buffs.erase(b)
			ended = true
	if ended:
		buffs_changed.emit()


## Called by Enemy when one of the player's weapons hits (leech perk, Siphon talent).
func on_weapon_hit(amount: float, w: Dictionary) -> void:
	var l := float(w.get("leech", 0.0))
	if str(w.get("school", "")) == "magic":
		l += Game.siphon()
	if l > 0.0 and amount > 0.0 and health < Game.max_health():
		heal(amount * l)


## Damage multiplier for a weapon school: upgrades, level and talents (Game.school_mult) plus buffs.
func damage_mult(school: String) -> float:
	var m := Game.school_mult(school)
	if has_buff("fury"):
		m *= 1.25
	if school == "tech" and has_buff("oiled"):
		m *= 1.2
	if school == "magic" and has_buff("attuned"):
		m *= 1.2
	return m


## Camera zoom (FOV multiplier, 1 = normal). The Brass Longshot's scope sets it while RMB is held.
func set_zoom(f: float) -> void:
	zoom = clampf(f, 0.2, 1.0)


## Things that did not fit in the pack land at the player's feet (they wait there until there is room).
func _on_pack_overflow(kind: String, payload: Variant) -> void:
	var pos := global_position + Vector3.UP * 1.0 - transform.basis.z * 0.8
	if kind == "weapon":
		Pickup.drop_weapon(self, pos, payload)
	else:
		Pickup.drop_item(self, pos, str(payload.get("id", "")), int(payload.get("count", 1)))


## Display name of what is in hand (weapon instance name with rarity, or the tool name).
func current_name() -> String:
	if current_uid > 0:
		var w := Game.get_weapon(current_uid)
		if not w.is_empty():
			return Catalog.weapon_name(w)
	return Catalog.display_name(current_id)


# ------------------------------------------------------------------ damage / healing
func apply_damage(info: DamageInfo) -> void:
	if dead or god_mode:
		return
	var amount := info.amount
	if ward_timer > 0.0:
		amount *= 0.5
	if has_buff("iron"):
		amount *= 0.65
	if piloting:
		amount *= 0.6
	health = maxf(0.0, health - amount)   # (the HUD showed "-99899 / 100" on a big hit)
	last_damage_time = Time.get_ticks_msec() / 1000.0
	health_changed.emit(health, Game.max_health())
	Events.player_damaged.emit(amount, info.damage_type)
	shake(clampf(amount / 30.0, 0.15, 0.8), 0.25)
	if not piloting and info.knockback > 0.0:
		velocity += info.direction.normalized() * info.knockback
	if health <= 0.0:
		_die()


func heal(amount: float) -> void:
	health = minf(Game.max_health(), health + amount)
	health_changed.emit(health, Game.max_health())


func add_heal_over_time(amount: float, duration: float) -> void:
	heal_pool += amount
	heal_rate = heal_pool / maxf(duration, 0.1)


func spend_mana(amount: float) -> bool:
	if god_mode:
		return true
	if mana < amount:
		return false
	mana -= amount
	mana_changed.emit(mana, Game.max_mana())
	return true


func _die() -> void:
	if dead:
		return
	dead = true
	health = 0.0
	if piloting:
		exit_seat()
	if current:
		current.on_unequip()
	Game.add_stat("deaths")
	var lost := mini(int(Game.gold * 0.1), 100)
	if lost > 0:
		Game.spend_gold(lost)
	Events.player_died.emit()
	died.emit()
	viewmodel.visible = false
	var tw := create_tween()
	tw.tween_property(head, "position:y", 0.35, 0.6).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	await get_tree().create_timer(3.5).timeout
	respawn()


func respawn() -> void:
	dead = false
	health = Game.max_health()
	mana = Game.max_mana()
	ward_timer = 0.0
	heal_pool = 0.0
	head.position.y = EYE
	viewmodel.visible = true
	var spawn := WorldLayout.TOWN_SPAWN
	var w := _world
	if w and w.has_method("spawn_point"):
		spawn = w.spawn_point()
	teleport(spawn, 0.0, 0.0)
	select_slot(slot, true)
	_emit_stats()
	Events.player_respawned.emit()
	respawned.emit()


# ------------------------------------------------------------------ physics
func _physics_process(delta: float) -> void:
	if piloting:
		_physics_piloting(delta)
		return
	if dead:
		velocity.y -= GRAVITY * delta
		velocity.x = move_toward(velocity.x, 0, 20 * delta)
		velocity.z = move_toward(velocity.z, 0, 20 * delta)
		move_and_slide()
		return
	var input_dir := Vector2.ZERO
	var wants_jump := false
	var wants_sprint := false
	var wants_crouch := false
	if input_enabled:
		input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		wants_jump = Input.is_action_just_pressed("jump")
		wants_sprint = Input.is_action_pressed("sprint")
		wants_crouch = Input.is_action_pressed("crouch")
	var on_floor := is_on_floor()
	_swimming = global_position.y < WorldLayout.WATER_LEVEL - 1.05 and _over_water()
	# crouch
	_crouching = wants_crouch and on_floor
	var target_eye := CROUCH_EYE if _crouching else EYE
	_eye_height = lerpf(_eye_height, target_eye, 1.0 - exp(-12.0 * delta))
	# speed
	var moving := input_dir.length() > 0.1
	var sprinting := wants_sprint and moving and stamina > 1.0 and not _crouching and input_dir.y < 0.2
	var speed := WALK
	if _crouching:
		speed = CROUCH_SPEED
	elif sprinting:
		speed = SPRINT
	if _swimming:
		speed = SWIM
	var swift := has_buff("swift")
	if swift:
		speed *= 1.3
	speed *= Game.move_mult() * (1.0 - clampf(weapon_slow, 0.0, 0.8))
	if sprinting and on_floor and not swift:
		stamina = maxf(0.0, stamina - 20.0 * delta)
	else:
		stamina = minf(MAX_STAMINA, stamina + 24.0 * delta)
	stamina_changed.emit(stamina, MAX_STAMINA)
	var wish := (transform.basis * Vector3(input_dir.x, 0, input_dir.y))
	wish.y = 0
	wish = wish.normalized() * speed
	var accel := ACCEL if on_floor or _swimming else AIR_ACCEL
	velocity.x = lerpf(velocity.x, wish.x, 1.0 - exp(-accel * delta))
	velocity.z = lerpf(velocity.z, wish.z, 1.0 - exp(-accel * delta))
	# jumping with coyote time and buffering
	if on_floor:
		_coyote = 0.12
	else:
		_coyote -= delta
	if wants_jump:
		_jump_buffer = 0.14
	else:
		_jump_buffer -= delta
	if _swimming:
		var buoy := (WorldLayout.WATER_LEVEL - 0.55 - global_position.y) * 6.0
		velocity.y = lerpf(velocity.y, clampf(buoy, -2.0, 3.0), 1.0 - exp(-4.0 * delta))
		if input_enabled and Input.is_action_pressed("jump"):
			velocity.y = 3.2
	else:
		var leap := has_buff("leap")
		if _jump_buffer > 0.0 and _coyote > 0.0:
			velocity.y = JUMP * (1.27 if leap else 1.0)
			_jump_buffer = 0.0
			_coyote = 0.0
			AudioManager.play_2d("jump", -9.0)
		velocity.y -= GRAVITY * delta * (0.5 if leap and velocity.y < 0.0 else 1.0)
		if leap:
			velocity.y = maxf(velocity.y, -9.0)
	_prev_vy = velocity.y
	move_and_slide()
	# landing
	if is_on_floor() and not _was_on_floor:
		var impact := -_prev_vy
		if impact > 4.0:
			_land_dip = clampf(impact * 0.012, 0.0, 0.18)
			AudioManager.play_2d("land", -8.0)
		if impact > 17.0 and not _swimming and not has_buff("leap"):
			apply_damage(DamageInfo.make((impact - 17.0) * 5.0, "kinetic"))
	_was_on_floor = is_on_floor()
	# soft play-area boundary
	var flat := Vector2(global_position.x, global_position.z)
	if flat.length() > WorldLayout.PLAY_RADIUS:
		var back := -flat.normalized() * (flat.length() - WorldLayout.PLAY_RADIUS) * 4.0
		velocity.x += back.x * delta * 10.0
		velocity.z += back.y * delta * 10.0
	if global_position.y < -60.0:
		teleport(WorldLayout.TOWN_SPAWN)
	_update_camera_effects(delta, moving and is_on_floor(), sprinting)
	_regen(delta)
	_update_interaction()
	if current:
		current.tick(delta)


func _over_water() -> bool:
	var lp: Vector2 = WorldLayout.LAKE["pos"]
	return Vector2(global_position.x, global_position.z).distance_to(lp) < float(WorldLayout.LAKE["radius"]) + 25.0


func _regen(delta: float) -> void:
	_tick_buffs(delta)
	var now := Time.get_ticks_msec() / 1000.0
	var mmax := Game.max_mana()
	if mana < mmax:
		mana = minf(mmax, mana + Game.mana_regen() * delta)
		mana_changed.emit(mana, mmax)
	var hmax := Game.max_health()
	if heal_pool > 0.0:
		var h := minf(heal_pool, heal_rate * delta)
		heal_pool -= h
		heal(h)
	elif health < hmax and now - last_damage_time > 6.0:
		health = minf(hmax, health + 2.5 * Game.regen_mult() * delta)
		health_changed.emit(health, hmax)
	if ward_timer > 0.0:
		ward_timer -= delta


func _update_camera_effects(delta: float, walking: bool, sprinting: bool) -> void:
	var hspeed := Vector2(velocity.x, velocity.z).length()
	if walking:
		_bob_t += delta * hspeed * 1.35
		_step_dist += hspeed * delta
		if _step_dist > (2.6 if sprinting else 2.1):
			_step_dist = 0.0
			_footstep()
	else:
		_bob_t = lerpf(_bob_t, round(_bob_t / PI) * PI, 1.0 - exp(-6.0 * delta))
	var bob := sin(_bob_t * 2.0) * 0.045 * clampf(hspeed / WALK, 0.0, 1.4)
	_land_dip = lerpf(_land_dip, 0.0, 1.0 - exp(-8.0 * delta))
	head.position.y = _eye_height + bob - _land_dip
	head.position.x = cos(_bob_t) * 0.02 * clampf(hspeed / WALK, 0.0, 1.4)
	var shake_off := Vector3.ZERO
	if _shake_time > 0.0:
		_shake_time -= delta
		shake_off = Vector3(randf_range(-1, 1), randf_range(-1, 1), 0) * _shake * 0.05
	camera.position = shake_off
	_fov_kick = lerpf(_fov_kick, 7.0 if sprinting else 0.0, 1.0 - exp(-5.0 * delta))
	_zoom_cur = lerpf(_zoom_cur, zoom, 1.0 - exp(-14.0 * delta))
	camera.fov = (Settings.fov + _fov_kick) * _zoom_cur
	viewmodel.set_motion(hspeed, is_on_floor(), _bob_t)


func shake(strength: float, duration: float) -> void:
	_shake = maxf(_shake if _shake_time > 0 else 0.0, strength)
	_shake_time = maxf(_shake_time, duration)


func _footstep() -> void:
	var surface := "grass"
	var w := _world
	if w and w.terrain:
		var s: Color = w.terrain.splat_at(global_position.x, global_position.z)
		if s.a > 0.5 or s.r > 0.6:
			surface = "stone"
	var col := get_last_slide_collision()
	if col and not (col.get_collider() is StaticBody3D and (col.get_collider() as Node).get_meta("surface", "") == "terrain"):
		surface = "stone"
	AudioManager.play_2d("footstep_%s_%d" % [surface, randi_range(1, 4)], -14.0, 1.0, 0.08)


# ------------------------------------------------------------------ aiming / interaction
func aim_ray(dist: float = 200.0, mask: int = 1 | 4 | 8 | 32, exclude: Array = []) -> Dictionary:
	var from := camera.global_position
	var to := from - camera.global_transform.basis.z * dist
	var q := PhysicsRayQueryParameters3D.create(from, to, mask)
	var ex: Array[RID] = [get_rid()]
	for e in exclude:
		if e is CollisionObject3D:
			ex.append(e.get_rid())
	q.exclude = ex
	q.collide_with_areas = false
	return get_world_3d().direct_space_state.intersect_ray(q)


func aim_point(dist: float = 200.0) -> Vector3:
	var hit := aim_ray(dist)
	if hit:
		return hit["position"]
	return camera.global_position - camera.global_transform.basis.z * dist


static func find_interactable(n: Object) -> Object:
	# Walk up from the collider; at each level also look at direct children, because
	# interactables (quest board, terminals) are attached as children of their prop model.
	var node := n as Node
	var depth := 0
	while node and depth < 6:
		if node.has_method("interact") and node.has_method("get_interact_text"):
			return node
		for c in node.get_children():
			if c.has_method("interact") and c.has_method("get_interact_text"):
				return c
		node = node.get_parent()
		depth += 1
	return null


func _update_interaction() -> void:
	var target: Object = null
	var text := ""
	var hit := aim_ray(INTERACT_RANGE, 1 | 4 | 32)
	if hit:
		var col: Object = hit["collider"]
		if col is Contraption:
			var part: Part = (col as Contraption).part_from_shape(hit["shape"])
			if part and part.device and part.device.has_method("interact"):
				target = part.device
				text = part.device.get_interact_text()
		else:
			var it := find_interactable(col)
			if it:
				target = it
				text = it.get_interact_text()
	interact_target = target
	if text != interact_text:
		interact_text = text
		interact_hint_changed.emit(text)
	# aim info for building tools
	var info := ""
	if current and current.has_method("aim_info"):
		info = current.aim_info()
	if info != aim_text:
		aim_text = info
		aim_info_changed.emit(info)


func _do_interact() -> void:
	if interact_target and is_instance_valid(interact_target):
		interact_target.interact(self)


func _build_manager() -> BuildManager:
	var w := _world
	if w and "build_manager" in w:
		return w.build_manager
	return null


# ------------------------------------------------------------------ piloting
func sit(part: Part) -> void:
	if part == null or part.contraption == null:
		return
	if current:
		current.on_unequip()
	piloting = part.contraption
	seat_part = part
	piloting.set_pilot(self, part)
	collision.disabled = true
	velocity = Vector3.ZERO
	viewmodel.visible = false
	chase_yaw = part.global_rotation.y + PI
	chase_pitch = -0.28
	chase_dist = clampf(piloting.radius() * 2.2 + 4.0, 6.0, 18.0)
	_update_camera_mode()
	Events.toast("Piloting! WASD drive · Space/Ctrl lift · LMB fire turrets · F lights · V view · E exit", "info")


func exit_seat() -> void:
	if piloting == null:
		return
	var c := piloting
	var sp := seat_part
	piloting = null
	seat_part = null
	if is_instance_valid(c):
		c.set_pilot(null, null)
	collision.disabled = false
	var exit_pos := global_position + Vector3.UP * 0.6
	if is_instance_valid(sp):
		exit_pos = sp.global_position + sp.global_transform.basis.x * 1.3 + Vector3.UP * 0.7
	global_position = exit_pos
	velocity = Vector3.ZERO
	rotation = Vector3(0, yaw, 0)
	head.top_level = false
	head.position = Vector3(0, EYE, 0)
	head.rotation = Vector3(pitch, 0, 0)
	camera.position = Vector3.ZERO
	viewmodel.visible = true
	select_slot(slot, true)


func _update_camera_mode() -> void:
	head.top_level = true


func _physics_piloting(delta: float) -> void:
	if not is_instance_valid(piloting) or not is_instance_valid(seat_part):
		piloting = null
		exit_seat()
		return
	var sit_xf := seat_part.sit_transform()
	global_position = sit_xf.origin - Vector3.UP * 0.6
	var ctl := {
		"throttle": Input.get_axis("move_back", "move_forward") if input_enabled else 0.0,
		"steer": Input.get_axis("move_left", "move_right") if input_enabled else 0.0,
		"lift": (1.0 if Input.is_action_pressed("jump") else 0.0) - (1.0 if Input.is_action_pressed("crouch") else 0.0) if input_enabled else 0.0,
		"boost": input_enabled and Input.is_action_pressed("sprint"),
		"fire": input_enabled and Input.is_action_pressed("primary"),
		"aim": Vector3.ZERO,
	}
	if third_person:
		var target := piloting.global_transform * piloting.center_of_mass
		var dir := Vector3(sin(chase_yaw) * cos(chase_pitch), -sin(chase_pitch), cos(chase_yaw) * cos(chase_pitch))
		var want := target + dir * chase_dist + Vector3.UP * 1.2
		# keep the camera above terrain and out of walls
		var q := PhysicsRayQueryParameters3D.create(target, want, 1)
		var hit := get_world_3d().direct_space_state.intersect_ray(q)
		if hit:
			want = hit["position"] + (target - want).normalized() * 0.4
		head.global_position = head.global_position.lerp(want, 1.0 - exp(-10.0 * delta))
		head.look_at(target + Vector3.UP * 1.0, Vector3.UP)
		camera.rotation = Vector3.ZERO
	else:
		head.global_transform = Transform3D(sit_xf.basis, sit_xf.origin + sit_xf.basis.y * 0.15)
		head.rotate_object_local(Vector3.UP, PI)  # seat front is +Z; camera looks down -Z
	ctl["aim"] = _pilot_aim_point()
	piloting.pilot_input = ctl
	_regen(delta)


func _pilot_aim_point() -> Vector3:
	var from := camera.global_position
	var fwd := -camera.global_transform.basis.z
	var q := PhysicsRayQueryParameters3D.create(from + fwd * 2.0, from + fwd * 300.0, 1 | 8)
	q.exclude = [piloting.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	return hit["position"] if hit else from + fwd * 300.0


func save_state() -> void:
	Game.player_health = health
	Game.player_mana = mana
	Game.player_transform = Transform3D(Basis(Vector3.UP, yaw), global_position + Vector3.UP * 0.2)
	Game.has_player_transform = true


## The weapon slot (0 or 1) used most recently.
func last_weapon_slot() -> int:
	return _last_weapon_slot


## Pickup pull range multiplier (the Scavenger's Sack doubles it).
func magnet_mult() -> float:
	return 2.0 if Game.has_pouch_perk("scavenger") else 1.0
