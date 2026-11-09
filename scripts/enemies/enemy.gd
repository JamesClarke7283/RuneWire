class_name Enemy
extends CharacterBody3D
## Base class for all enemies: stats from Catalog.ENEMIES, damage & resistances, aggro, steering
## (ground or flying), health bar, loot (gold coins, quest items) and death effects.

const KINDS := {
	"wisp": "res://scripts/enemies/enemy_wisp.gd",
	"golem": "res://scripts/enemies/enemy_golem.gd",
	"wraith": "res://scripts/enemies/enemy_wraith.gd",
	"cultist": "res://scripts/enemies/enemy_cultist.gd",
	"archon": "res://scripts/enemies/enemy_archon.gd",
	"drone": "res://scripts/enemies/enemy_drone.gd",
	"sentry": "res://scripts/enemies/enemy_sentry.gd",
	"crawler": "res://scripts/enemies/enemy_crawler.gd",
	"ironclad": "res://scripts/enemies/enemy_ironclad.gd",
}

const HB_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_test_disabled, shadows_disabled;
instance uniform float fill = 1.0;
instance uniform float show = 0.0;
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
}
void fragment() {
	vec2 uv = UV;
	float border = step(uv.x, 0.03) + step(0.97, uv.x) + step(uv.y, 0.12) + step(0.88, uv.y);
	vec3 bg = vec3(0.1, 0.07, 0.12);
	vec3 col = mix(vec3(0.95, 0.25, 0.25), vec3(1.0, 0.75, 0.2), step(0.5, fill));
	col = mix(col, vec3(0.45, 0.95, 0.4), step(0.75, fill));
	vec3 c = uv.x < fill ? col : bg;
	ALBEDO = mix(c, vec3(0.05), clamp(border, 0.0, 1.0));
	ALPHA = show;
}
"""

var kind: String = ""
var def: Dictionary = {}
var hp: float = 50.0
var max_hp: float = 50.0
var dead: bool = false
var faction: String = "magic"
var flying: bool = false
var is_static: bool = false
var boss: bool = false
var move_speed: float = 4.0
var resist: Dictionary = {}
var model: Node3D
var target: Player = null
var home: Vector3 = Vector3.ZERO
var leash: float = 55.0
var aggro: bool = false
var state: String = "idle"
var state_t: float = 0.0
var attack_cd: float = 1.0
var spawner: Node = null
var body_height: float = 1.6
var body_radius: float = 0.5
var hover_height: float = 3.0
var weak_point: String = ""
var scale_factor: float = 1.0
var summons: Array = []

var _nodes: Dictionary = {}
var _hb: MeshInstance3D
var _hb_timer: float = 0.0
var _los_timer: float = 0.0
var _has_los: bool = false
var _wander_target: Vector3 = Vector3.ZERO
var _stuck_t: float = 0.0
var _last_pos: Vector3 = Vector3.ZERO
var _side: float = 1.0
var _anim_t: float = 0.0
var _flash_t: float = 0.0
var _world: World
static var _hb_shader: Shader


static func spawn(k: String, w: World, pos: Vector3) -> Enemy:
	if not KINDS.has(k):
		return null
	var e: Enemy = load(KINDS[k]).new()
	e.kind = k
	e._world = w
	w.enemies_root.add_child(e)
	e.global_position = pos
	e.home = pos
	return e


func _ready() -> void:
	add_to_group("enemies")
	def = Catalog.enemy(kind)
	max_hp = float(def.get("hp", 50.0)) * Game.difficulty
	hp = max_hp
	faction = def.get("faction", "magic")
	flying = bool(def.get("flying", false))
	is_static = bool(def.get("static", false))
	boss = bool(def.get("boss", false))
	move_speed = float(def.get("speed", 4.0))
	resist = def.get("resist", {})
	collision_layer = 8
	collision_mask = 1 | 4 | 8
	if _world == null:
		_world = get_tree().get_first_node_in_group("world")
	_setup()
	_build_collision()
	_build_model()
	_build_health_bar()
	_wander_target = global_position
	_last_pos = global_position
	_side = 1.0 if randf() > 0.5 else -1.0
	if boss:
		Events.boss_started.emit(self, str(def.get("name", kind)))


## Subclasses set body_height, body_radius, hover_height, scale_factor, weak_point here.
func _setup() -> void:
	pass


func _build_collision() -> void:
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = body_radius
	cap.height = maxf(body_height, body_radius * 2.0)
	cs.shape = cap
	cs.position.y = 0.0 if flying else body_height * 0.5
	add_child(cs)


func _build_model() -> void:
	var model_name: String = def.get("model", "")
	var path := "res://assets/models/enemies/%s.glb" % model_name
	if ResourceLoader.exists(path):
		model = (load(path) as PackedScene).instantiate()
		MaterialLib.apply(model)
	else:
		model = _placeholder_model()
	model.name = "Model"
	if scale_factor != 1.0:
		model.scale = Vector3.ONE * scale_factor
	add_child(model)
	for n in model.find_children("*", "Node3D", true, false):
		_nodes[String(n.name)] = n
	_on_model_ready()


func _on_model_ready() -> void:
	pass


func node(n: String) -> Node3D:
	return _nodes.get(n, null)


func _placeholder_model() -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var col := Color(0.6, 0.4, 1.0) if faction == "magic" else Color(0.85, 0.5, 0.2)
	if flying:
		var sm := SphereMesh.new()
		sm.radius = body_radius
		sm.height = body_radius * 2.0
		mi.mesh = sm
	else:
		var cm := CapsuleMesh.new()
		cm.radius = body_radius
		cm.height = body_height
		mi.mesh = cm
		mi.position.y = body_height * 0.5
	mi.name = "Body"
	mi.material_override = MaterialLib.get_flat(col)
	root.add_child(mi)
	var eye := MeshInstance3D.new()
	var em := SphereMesh.new()
	em.radius = body_radius * 0.25
	em.height = body_radius * 0.5
	eye.mesh = em
	eye.material_override = MaterialLib.get_glow(Color(1.0, 0.5, 0.2) if faction == "tech" else Color(0.4, 1.0, 0.9), 4.0)
	eye.position = Vector3(0, (0.0 if flying else body_height * 0.8), body_radius * 0.85)
	eye.name = "Eye"
	root.add_child(eye)
	return root


func _build_health_bar() -> void:
	if boss:
		return
	if _hb_shader == null:
		_hb_shader = Shader.new()
		_hb_shader.code = HB_SHADER
	_hb = MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1.1, 0.13)
	_hb.mesh = q
	var m := ShaderMaterial.new()
	m.shader = _hb_shader
	m.render_priority = 5
	_hb.material_override = m
	_hb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_hb.position = Vector3(0, (body_height * 0.5 + 0.5) if flying else body_height * scale_factor + 0.45, 0)
	add_child(_hb)
	_hb.set_instance_shader_parameter("show", 0.0)


## Point to aim at (centre of mass).
func aim_point() -> Vector3:
	if flying:
		return global_position
	return global_position + Vector3.UP * body_height * 0.55 * scale_factor


# ------------------------------------------------------------------ damage
func apply_damage(info: DamageInfo) -> void:
	if dead:
		return
	var mult := float(resist.get(info.damage_type, 1.0))
	var amount := info.amount * mult
	var crit := false
	if weak_point != "":
		var wp := node(weak_point)
		if wp and info.position.distance_to(wp.global_position) < 0.9 * scale_factor:
			amount *= 2.0
			crit = true
	hp -= amount
	aggro = true
	_hb_timer = 4.0
	_flash_t = 0.12
	MaterialLib.flash(model, 1.0)
	var col := Color(1, 1, 1)
	if mult >= 1.4:
		col = Color(1.0, 0.85, 0.25)
	elif mult <= 0.6:
		col = Color(0.65, 0.65, 0.7)
	if crit:
		col = Color(1.0, 0.45, 0.3)
	if amount >= 0.5:
		VFX.damage_number(self, aim_point() + Vector3.UP * 0.4 * scale_factor, amount, col, crit or mult >= 1.4)
	var snd := "hit_magic" if faction == "magic" else "hit_metal"
	AudioManager.play(snd, aim_point(), -4.0, 1.0, 0.12)
	Events.enemy_damaged.emit(self, amount, info.position, info.damage_type)
	if info.knockback > 0.0 and not is_static and not boss:
		velocity += info.direction.normalized() * info.knockback * (0.5 if flying else 0.8)
	if target == null:
		target = get_tree().get_first_node_in_group("player") as Player
	_on_damaged(info, amount)
	if hp <= 0.0:
		die(info)


func _on_damaged(_info: DamageInfo, _amount: float) -> void:
	pass


func die(info: DamageInfo = null) -> void:
	if dead:
		return
	dead = true
	hp = 0.0
	remove_from_group("enemies")
	collision_layer = 0
	collision_mask = 0
	if _hb:
		_hb.visible = false
	Events.enemy_killed.emit(kind, faction, global_position)
	Game.add_xp(int(def.get("xp", 10)))
	Game.add_stat("kills")
	Game.add_stat("kills_" + faction)
	if boss:
		Game.add_stat("bosses")
		Events.boss_ended.emit(self)
		Events.toast("%s defeated!" % def.get("name", kind), "quest_done")
	_drop_loot()
	if spawner and spawner.has_method("on_enemy_died"):
		spawner.on_enemy_died(self)
	for s in summons:
		if is_instance_valid(s) and not s.dead:
			s.die()
	_death_fx(info)


func _drop_loot() -> void:
	var g: Array = def.get("gold", [3, 6])
	var gold := randi_range(int(g[0]), int(g[1]))
	Pickup.drop_coins(self, aim_point(), gold)
	var loot: Dictionary = def.get("loot", {})
	for item in loot:
		if randf() < float(loot[item]):
			Pickup.drop_item(self, aim_point(), item)


func _death_fx(_info: DamageInfo) -> void:
	var pos := aim_point()
	if faction == "tech":
		AudioManager.play("death_tech", pos, 2.0)
		Combat.explode(self, pos, 2.5 * scale_factor, 0.0, "fire", self, false, false, 0.8)
		_break_apart()
		queue_free()
	else:
		AudioManager.play("death_magic", pos, 2.0)
		VFX.sparkle(self, pos, Color(0.7, 0.5, 1.0), 26, 0.5 * scale_factor)
		VFX.puffs(self, pos, Color(0.55, 0.45, 0.75), 8, 0.7 * scale_factor, 1.0, 1.5)
		MaterialLib.apply(model, "dissolve")
		var tw := create_tween()
		tw.tween_method(func(v): MaterialLib._set_instance_param(model, "dissolve", v), 0.0, 1.0, 0.9)
		tw.tween_callback(queue_free)


## Tech enemies burst into physics debris made from their own model pieces.
func _break_apart() -> void:
	var count := 0
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		if count >= 8:
			break
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		var aabb := m.get_aabb()
		if aabb.size.length() < 0.1:
			continue
		var rb := RigidBody3D.new()
		rb.collision_layer = 128
		rb.collision_mask = 1 | 4 | 128
		rb.mass = clampf(aabb.size.length() * 8.0, 2.0, 60.0)
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = (aabb.size * m.global_transform.basis.get_scale()).clamp(Vector3.ONE * 0.08, Vector3.ONE * 3.0)
		cs.shape = bs
		cs.position = aabb.get_center() * m.global_transform.basis.get_scale()
		rb.add_child(cs)
		var copy := MeshInstance3D.new()
		copy.mesh = m.mesh
		for i in m.mesh.get_surface_count():
			copy.set_surface_override_material(i, m.get_surface_override_material(i))
		copy.scale = m.global_transform.basis.get_scale()
		rb.add_child(copy)
		VFX.root(self).add_child(rb)
		rb.global_transform = Transform3D(m.global_transform.basis.orthonormalized(), m.global_position)
		rb.linear_velocity = (Vector3(randf_range(-1, 1), randf_range(0.6, 1.6), randf_range(-1, 1))).normalized() * randf_range(4, 9)
		rb.angular_velocity = Vector3(randf_range(-8, 8), randf_range(-8, 8), randf_range(-8, 8))
		var tw := rb.create_tween()
		tw.tween_interval(5.0)
		tw.tween_property(copy, "scale", Vector3.ZERO, 0.6)
		tw.tween_callback(rb.queue_free)
		count += 1


# ------------------------------------------------------------------ AI loop
func _physics_process(delta: float) -> void:
	if dead:
		return
	_anim_t += delta
	state_t += delta
	attack_cd -= delta
	if _flash_t > 0.0:
		_flash_t -= delta
		if _flash_t <= 0.0:
			MaterialLib.flash(model, 0.0)
	if _hb:
		_hb_timer -= delta
		_hb.set_instance_shader_parameter("show", 1.0 if _hb_timer > 0.0 else 0.0)
		_hb.set_instance_shader_parameter("fill", clampf(hp / max_hp, 0.0, 1.0))
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Player
	_los_timer -= delta
	if _los_timer <= 0.0 and target:
		_los_timer = 0.3
		_has_los = Combat.has_los(self, aim_point(), target.camera.global_position, [self])
	var dist := INF
	if target and not target.dead:
		dist = global_position.distance_to(target.global_position)
		var detect := 26.0 if not boss else 45.0
		if not aggro and dist < detect and _has_los:
			aggro = true
			_on_aggro()
		if aggro and (dist > 70.0 or global_position.distance_to(home) > leash + 30.0):
			aggro = false
	else:
		aggro = false
	think(delta, dist)
	if not is_static:
		_move(delta)
	animate(delta)


func _on_aggro() -> void:
	pass


## Subclass AI: decide desired movement (set `desired_velocity`) and trigger attacks.
var desired_velocity: Vector3 = Vector3.ZERO


func think(_delta: float, _dist: float) -> void:
	pass


func animate(_delta: float) -> void:
	pass


func can_attack() -> bool:
	return aggro and target != null and not target.dead and _has_los


func target_pos() -> Vector3:
	if target == null:
		return home
	return target.global_position + Vector3.UP * 1.0


func face_towards(p: Vector3, delta: float, speed: float = 6.0) -> void:
	var d := p - global_position
	d.y = 0
	if d.length_squared() < 0.01:
		return
	var want := atan2(d.x, d.z)
	rotation.y = lerp_angle(rotation.y, want, 1.0 - exp(-speed * delta))


func facing_dir() -> Vector3:
	return Vector3(sin(rotation.y), 0, cos(rotation.y))


## Chase / keep distance helpers.
func steer_to(p: Vector3, speed: float) -> void:
	var d := p - global_position
	if not flying:
		d.y = 0
	if d.length() < 0.3:
		desired_velocity = Vector3.ZERO
		return
	desired_velocity = d.normalized() * speed


func strafe_around(center: Vector3, want_dist: float, speed: float) -> void:
	var to := global_position - center
	to.y = 0
	var dist := to.length()
	if dist < 0.01:
		to = Vector3.RIGHT
		dist = 1.0
	var radial := to / dist
	var tangent := Vector3(-radial.z, 0, radial.x) * _side
	var radial_term := clampf((want_dist - dist) * 0.6, -1.0, 1.0)
	desired_velocity = (tangent + radial * radial_term).normalized() * speed


func wander(speed: float) -> void:
	if global_position.distance_to(_wander_target) < 2.0 or state_t > 8.0:
		var a := randf() * TAU
		var r := randf_range(4.0, 14.0)
		_wander_target = home + Vector3(cos(a) * r, 0, sin(a) * r)
		state_t = 0.0
	steer_to(_wander_target, speed * 0.45)


func _move(delta: float) -> void:
	if flying:
		var ground := _world.ground_y(global_position.x, global_position.z) if _world else 0.0
		var want_y := maxf(ground, WorldLayout.WATER_LEVEL) + hover_height
		if target and aggro:
			want_y = maxf(want_y, target.global_position.y + hover_height * 0.6)
		var vy := (want_y - global_position.y) * 2.5
		var v := desired_velocity
		v.y = vy + sin(_anim_t * 2.0) * 0.4
		velocity = velocity.lerp(v, 1.0 - exp(-3.5 * delta))
		move_and_slide()
		return
	var hv := Vector3(desired_velocity.x, 0, desired_velocity.z)
	velocity.x = lerpf(velocity.x, hv.x, 1.0 - exp(-8.0 * delta))
	velocity.z = lerpf(velocity.z, hv.z, 1.0 - exp(-8.0 * delta))
	if is_on_floor():
		velocity.y = -0.5
	else:
		velocity.y -= 22.0 * delta
	move_and_slide()
	# unstick: if we want to move but don't, sidestep for a moment
	if hv.length() > 0.5:
		var moved := global_position.distance_to(_last_pos)
		if moved < hv.length() * delta * 0.25:
			_stuck_t += delta
		else:
			_stuck_t = maxf(0.0, _stuck_t - delta)
		if _stuck_t > 0.8:
			_stuck_t = 0.0
			_side = -_side
			velocity += Vector3(-hv.z, 0, hv.x).normalized() * move_speed * _side + Vector3.UP * (5.0 if is_on_floor() else 0.0)
	_last_pos = global_position
	if global_position.y < -40.0:
		global_position = home + Vector3.UP


# ------------------------------------------------------------------ attack helpers
func shoot(from: Vector3, to: Vector3, speed: float, dmg: float, dmg_type: String, color: Color, opts: Dictionary = {}) -> Projectile:
	var o := {"damage": dmg * Game.difficulty, "damage_type": dmg_type, "color": color, "from_player": false, "source": self,
		"size": 0.18, "lifetime": 4.0}
	o.merge(opts, true)
	return Projectile.spawn(self, from, (to - from).normalized() * speed, o)


func melee(radius: float, dmg: float, dmg_type: String, knock: float = 6.0) -> bool:
	if target and not target.dead and target.global_position.distance_to(global_position) < radius:
		var dir := (target.global_position - global_position).normalized()
		target.apply_damage(DamageInfo.make(dmg * Game.difficulty, dmg_type, self, aim_point(), dir + Vector3.UP * 0.3, knock))
		return true
	return false
