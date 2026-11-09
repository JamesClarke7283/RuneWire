class_name Player
extends CharacterBody3D
## First-person Runewright: movement, camera, health/mana/stamina, interaction, equipment
## hotbar, consumables and piloting contraptions (with a third-person chase camera).

signal health_changed(hp: float, max_hp: float)
signal mana_changed(mp: float, max_mp: float)
signal stamina_changed(st: float, max_st: float)
signal equipment_switched(id: String)
signal interact_hint_changed(text: String)
signal aim_info_changed(text: String)
signal died
signal respawned

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
var current_id: String = ""
var handlers: Dictionary = {}

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
	Events.screen_shake.connect(shake)
	_world = get_tree().get_first_node_in_group("world")
	select_slot(0, true)
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
			select_slot(slot + 1)
	elif event.is_action_pressed("prev_slot"):
		if not (current and current.scroll(-1)):
			select_slot(slot - 1)
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
				select_slot(i)
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
func select_slot(i: int, force: bool = false) -> void:
	var bar: Array = Game.hotbar
	if bar.is_empty():
		return
	i = wrapi(i, 0, bar.size())
	if i == slot and not force and current:
		return
	slot = i
	var id: String = bar[i]
	if current:
		current.on_unequip()
	current = _handler_for(id)
	current_id = id
	if current:
		current.on_equip()
	viewmodel.show_model(Catalog.equipment(id).get("model", ""), id)
	equipment_switched.emit(id)
	AudioManager.play_2d("ui_click", -10.0, 1.4)


func _handler_for(id: String) -> EquipBase:
	if handlers.has(id):
		return handlers[id]
	var e := Catalog.equipment(id)
	var h: EquipBase
	match id:
		"gauntlet":
			h = GauntletTool.new()
		"toolkit":
			h = ToolkitTool.new()
		_:
			if e.get("kind", "") == "spell":
				h = SpellCaster.new()
			else:
				h = WeaponGun.new()
	h.player = self
	h.id = id
	h.data = e
	h.name = "Equip_" + id
	add_child(h)
	handlers[id] = h
	return h


func _on_equipment_changed() -> void:
	if slot >= Game.hotbar.size():
		slot = 0
	health_changed.emit(health, Game.max_health())
	mana_changed.emit(mana, Game.max_mana())


func use_consumable(id: String) -> void:
	var c: Dictionary = Catalog.CONSUMABLES[id]
	if Game.item_count(id) <= 0:
		Events.toast("No %s left. Buy more from a vendor." % c["name"], "warn")
		AudioManager.play_ui("ui_error")
		return
	if id == "health_tonic" and health >= Game.max_health() - 0.5:
		Events.toast("Already at full health", "info")
		return
	if id == "mana_draught" and mana >= Game.max_mana() - 0.5:
		Events.toast("Mana already full", "info")
		return
	Game.items[id] = Game.item_count(id) - 1
	Game.inventory_changed.emit()
	if c.has("heal"):
		heal(float(c["heal"]))
	if c.has("mana"):
		mana = minf(Game.max_mana(), mana + float(c["mana"]))
		mana_changed.emit(mana, Game.max_mana())
	AudioManager.play_2d("spell_heal", -6.0, 1.2)


# ------------------------------------------------------------------ damage / healing
func apply_damage(info: DamageInfo) -> void:
	if dead or god_mode:
		return
	var amount := info.amount
	if ward_timer > 0.0:
		amount *= 0.5
	if piloting:
		amount *= 0.6
	health -= amount
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
	if current:
		current.on_equip()
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
	if sprinting and on_floor:
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
		if _jump_buffer > 0.0 and _coyote > 0.0:
			velocity.y = JUMP
			_jump_buffer = 0.0
			_coyote = 0.0
			AudioManager.play_2d("jump", -9.0)
		velocity.y -= GRAVITY * delta
	_prev_vy = velocity.y
	move_and_slide()
	# landing
	if is_on_floor() and not _was_on_floor:
		var impact := -_prev_vy
		if impact > 4.0:
			_land_dip = clampf(impact * 0.012, 0.0, 0.18)
			AudioManager.play_2d("land", -8.0)
		if impact > 17.0 and not _swimming:
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
		health = minf(hmax, health + 2.5 * delta)
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
	camera.fov = Settings.fov + _fov_kick
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
	if current:
		current.on_equip()


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
